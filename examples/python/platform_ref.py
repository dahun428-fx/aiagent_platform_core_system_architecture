"""Local-only reference, not a production identity provider or durable engine."""
from __future__ import annotations
import copy
import hashlib
import json
import re
import threading
import uuid
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Protocol

from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[2]
TRACE = re.compile(r"^00-(?!0{32})[0-9a-f]{32}-(?!0{16})[0-9a-f]{16}-[0-9a-f]{2}$")
RANK = {"public": 0, "internal": 1, "confidential": 2, "restricted": 3}


def load(name):
    return json.loads((ROOT / "examples/fixtures" / (name + ".json")).read_text())


@lru_cache
def validators():
    schemas = [json.loads(p.read_text()) for p in (ROOT / "contracts").glob("*.schema.json")]
    registry = Registry().with_resources((s["$id"], Resource.from_contents(s)) for s in schemas)
    return {s["title"]: Draft202012Validator(s, registry=registry, format_checker=FormatChecker()) for s in schemas}


def validate(name, value):
    try:
        validators()[name].validate(value)
    except ValidationError as exc:
        raise Fault(422, "VALIDATION_ERROR", "Request does not match contract") from exc


class Fault(Exception):
    def __init__(self, status, code, detail):
        self.status, self.code, self.detail = status, code, detail
        super().__init__(detail)

    def problem(self, traceparent=None):
        trace_id = traceparent.split("-")[1] if traceparent and TRACE.fullmatch(traceparent) else uuid.uuid4().hex
        return {"type": "about:blank", "title": self.code, "status": self.status,
                "detail": self.detail, "code": self.code, "traceId": trace_id}


def utcnow():
    return datetime.now(timezone.utc)


def expiration(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def authorize(identity, policy, scope, now=None):
    validate("identity", identity)
    validate("policy", policy)
    now = now or utcnow()
    if (identity["tenantId"] != policy["tenantId"] or not policy["allowed"]
            or expiration(policy["expiresAt"]) <= now
            or scope not in set(identity["scopes"]) & set(policy["allowedScopes"])):
        raise Fault(403, "FORBIDDEN", "Policy denied")
    if identity["mode"] == "delegated":
        for hop in identity["delegation"]:
            if scope not in hop["scopes"]:
                raise Fault(403, "FORBIDDEN", "Delegation scope denied")


def canonical_digest(value):
    return "sha256:" + hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def verify_approval(approval, tenant, invocation, digest, policy_version):
    validate("approval", approval)
    expected = (tenant, invocation, digest, policy_version, "approved")
    actual = tuple(approval[k] for k in ("tenantId", "invocationId", "subjectDigest", "policyVersion", "decision"))
    if expected != actual or expiration(approval["expiresAt"]) <= utcnow():
        raise Fault(403, "FORBIDDEN", "Approval is stale or not bound to this request")


def retrieve(documents, identity, policy):
    authorize(identity, policy, "agents.invoke")
    # Filter BEFORE content is assembled for the model. Knowledge backend must enforce this too.
    return [copy.deepcopy(d) for d in documents
            if d["tenantId"] == identity["tenantId"]
            and identity.get("principalId", identity["workloadId"]) in d["allowedPrincipals"]
            and RANK[d["classification"]] <= RANK[policy["classification"]]]


def validate_cross_agent(envelope, parent_scopes):
    validate("cross-agent", envelope)
    identity, policy = envelope["identity"], envelope["policy"]
    authorize(identity, policy, "agents.invoke")
    if (envelope["targetAgentId"] in envelope["visitedAgents"]
            or envelope["depth"] > envelope["maxDepth"]
            or not set(identity["scopes"]).issubset(parent_scopes)
            or envelope["request"]["context"]["tenantId"] != identity["tenantId"]):
        raise Fault(403, "FORBIDDEN", "Cross-Agent budget, cycle or delegation denied")
    # Actual remote workload/audience verification belongs to the transport adapter.


class ModelGateway:
    def __init__(self, record):
        self.record = record
        self.available = {"external", "self-hosted"}
        self.calls = 0

    def invoke(self, content, identity, policy, traceparent):
        authorize(identity, policy, "models.invoke")
        candidates = ["self-hosted"] if policy["classification"] in ("confidential", "restricted") else ["self-hosted", "external"]
        provider = next((p for p in candidates if p in self.available and "model-" + p in policy["allowedResources"]), None)
        if provider is None:
            raise Fault(503, "UPSTREAM_UNAVAILABLE", "No policy-approved model route")
        self.calls += 1
        self.record("model-gateway", traceparent, {"decisionId": policy["decisionId"], "provider": provider})
        return {"content": "mock:" + content, "provider": provider,
                "routeDecisionId": "route-" + provider,
                "usage": {"inputTokens": len(content.split()), "outputTokens": len(("mock:" + content).split())},
                "traceparent": traceparent}


class CredentialBroker:
    def __init__(self, record):
        self.record = record
        self.leases = {}
        self.now = utcnow
        self.lock = threading.Lock()

    def issue(self, request, policy, traceparent=None):
        validate("credential-request", request)
        identity = request["identity"]
        authorize(identity, policy, "tools.read", self.now())
        if (request["policyDecisionId"] != policy["decisionId"]
                or request["resource"] not in policy["allowedResources"]
                or request["resource"] != request["toolId"]
                or request["toolId"] != "tool-search"
                or request["toolVersion"] != "0.1.0"
                or not set(request["scopes"]).issubset(set(identity["scopes"]) & set(policy["allowedScopes"]) & {"tools.read"})):
            raise Fault(403, "FORBIDDEN", "Credential audience or scope denied")
        # Synthetic lease only. No real downstream credential is created.
        ref = "lease-" + uuid.uuid4().hex
        deadline = min(self.now() + timedelta(seconds=60), expiration(policy["expiresAt"]))
        lease = {"credentialRef": ref, "audience": request["resource"], "scopes": request["scopes"],
                 "expiresAt": deadline.isoformat(), "nonExportable": True}
        with self.lock:
            self.leases[ref] = {"lease": lease, "workload": identity["workloadId"],
                                "invocation": request["invocationId"], "consumed": False}
        traceparent = traceparent or "00-" + uuid.uuid4().hex + "-" + uuid.uuid4().hex[:16] + "-01"
        self.record("credential-broker", traceparent, {"decisionId": policy["decisionId"]})
        return copy.deepcopy(lease)

    def consume(self, ref, workload, invocation, audience):
        with self.lock:
            item = self.leases.get(ref)
            if (not item or item["consumed"] or item["workload"] != workload or item["invocation"] != invocation
                    or item["lease"]["audience"] != audience or expiration(item["lease"]["expiresAt"]) <= self.now()):
                raise Fault(403, "FORBIDDEN", "Credential lease binding or expiry denied")
            item["consumed"] = True
        # In a real broker the adapter injects credentials inside the trusted boundary.


class ToolGateway:
    def __init__(self, broker, record):
        self.broker, self.record = broker, record
        self.descriptor = load("tool-descriptor")
        self.memo = {}
        self.lock = threading.Lock()

    def invoke(self, request):
        validate("tool-invoke", request)
        identity, policy = request["identity"], request["policy"]
        authorize(identity, policy, "tools.read")
        if (request["toolId"] != self.descriptor["toolId"] or request["version"] != self.descriptor["version"]
                or self.descriptor["resource"] not in policy["allowedResources"]):
            raise Fault(403, "FORBIDDEN", "Tool not approved")
        if self.descriptor["effect"] == "write":
            raise Fault(403, "FORBIDDEN", "Write tools require an external approval service; not implemented in mock")
        key = (identity["tenantId"], identity.get("principalId", identity["workloadId"]),
               identity["agentId"], request["toolId"], request["version"], request["idempotencyKey"])
        digest = canonical_digest(request)
        with self.lock:
            if key in self.memo:
                old_digest, old_result = self.memo[key]
                if digest != old_digest:
                    raise Fault(409, "CONFLICT", "Idempotency key reused for different request")
                return copy.deepcopy(old_result)
            validate("tool-input", request["arguments"])
            credential_request = {"identity": identity, "toolId": request["toolId"], "toolVersion": request["version"],
                                  "resource": self.descriptor["resource"], "scopes": ["tools.read"],
                                  "policyDecisionId": policy["decisionId"], "invocationId": request["invocationId"]}
            lease = self.broker.issue(credential_request, policy, request["traceparent"])
            self.broker.consume(lease["credentialRef"], identity["workloadId"], request["invocationId"], self.descriptor["resource"])
            output = {"content": "tool:" + request["arguments"]["query"]}
            validate("tool-output", output)
            result = {"invocationId": request["invocationId"], "toolId": request["toolId"],
                      "status": "succeeded", "output": output, "traceparent": request["traceparent"]}
            self.record("tool-gateway", request["traceparent"], {"toolId": request["toolId"], "tenantId": identity["tenantId"]})
            self.memo[key] = (digest, result)
            return copy.deepcopy(result)


class RuntimeAdapter(Protocol):
    def execute(self, envelope: dict) -> dict: ...


class Runtime:
    def __init__(self, model, record):
        self.model, self.record = model, record

    def execute(self, envelope):
        validate("runtime", envelope)
        self.record("runtime", envelope["traceparent"], {"invocationId": envelope["invocationId"]})
        out = self.model.invoke(envelope["request"]["input"]["content"], envelope["identity"], envelope["policy"], envelope["traceparent"])
        return {"invocationId": envelope["invocationId"], "agentVersion": envelope["agentVersion"], "status": "succeeded",
                "output": {"type": "message", "content": out["content"]}, "traceparent": out["traceparent"],
                "routeDecisionId": out["routeDecisionId"], "usage": out["usage"]}


class Platform:
    def __init__(self):
        self.audit = []
        self.model = ModelGateway(self.record)
        self.runtime = Runtime(self.model, self.record)
        self.broker = CredentialBroker(self.record)
        self.tools = ToolGateway(self.broker, self.record)
        self.policy_available = True
        self.memo = {}
        self.lock = threading.Lock()

    def record(self, component, traceparent, fields):
        allowed = {"tenantId", "invocationId", "decisionId", "toolId", "provider"}
        self.audit.append({"component": component, "traceparent": traceparent,
                           **{k: v for k, v in fields.items() if k in allowed}})

    def invoke(self, agent_id, body, authorization, key, traceparent=None):
        # Fixed synthetic token lookup only. Production JWT/OIDC verification is not implemented.
        if authorization != "Bearer mock-user":
            raise Fault(401, "UNAUTHENTICATED", "A mock user token is required for this loopback demo")
        if not self.policy_available:
            raise Fault(503, "UPSTREAM_UNAVAILABLE", "Policy service unavailable")
        identity, policy = load("identity"), load("policy")
        validate("invocation", body)
        if agent_id != "agent-demo":
            raise Fault(404, "NOT_FOUND", "Unknown Agent")
        if body["context"]["tenantId"] != identity["tenantId"]:
            raise Fault(403, "FORBIDDEN", "Tenant assertion does not match authenticated identity")
        if body["execution"]["mode"] != "sync":
            raise Fault(501, "NOT_IMPLEMENTED", "Durable/async is contract-only in this reference")
        if not key or not key.strip():
            raise Fault(422, "VALIDATION_ERROR", "Idempotency-Key is required")
        if traceparent is None:
            traceparent = "00-" + uuid.uuid4().hex + "-" + uuid.uuid4().hex[:16] + "-01"
        if not TRACE.fullmatch(traceparent):
            raise Fault(422, "VALIDATION_ERROR", "Invalid traceparent")
        policy["classification"] = body["context"]["dataClassification"]
        authorize(identity, policy, "agents.invoke")
        # Memory-only, single-process idempotency. Real deployments need a persistent atomic effect ledger.
        cache_key = (identity["tenantId"], identity["principalId"], agent_id, "0.1.0", key)
        digest = canonical_digest(body)
        with self.lock:
            if cache_key in self.memo:
                old_digest, old_result = self.memo[cache_key]
                if digest != old_digest:
                    raise Fault(409, "CONFLICT", "Idempotency key reused for different request")
                return copy.deepcopy(old_result)
            invocation_id = "inv-" + uuid.uuid4().hex
            self.record("agent-gateway", traceparent, {"tenantId": identity["tenantId"], "invocationId": invocation_id})
            result = self.runtime.execute({"invocationId": invocation_id, "agentId": agent_id, "agentVersion": "0.1.0",
                                           "request": body, "identity": identity, "policy": policy, "traceparent": traceparent})
            validate("result", result)
            self.memo[cache_key] = (digest, result)
            return copy.deepcopy(result)


def make_server(port=8765):
    platform = Platform()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def send_json(self, status, payload, content_type="application/json"):
            raw = json.dumps(payload, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("X-Content-Type-Options", "nosniff")
            if isinstance(payload, dict) and "traceparent" in payload:
                self.send_header("traceparent", payload["traceparent"])
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            if self.path in ("/health/live", "/health/ready"):
                self.send_json(200, {"status": "ok"})
            else:
                self.send_json(501, Fault(501, "NOT_IMPLEMENTED", "This target API is contract-only").problem(), "application/problem+json")

        def do_POST(self):
            try:
                if self.headers.get("Authorization") != "Bearer mock-user":
                    raise Fault(401, "UNAUTHENTICATED", "Mock token required")
                match = re.fullmatch(r"/v1/agents/([a-z][a-z0-9.-]{1,63})/invocations", self.path)
                if not match:
                    raise Fault(501, "NOT_IMPLEMENTED", "This target API is contract-only")
                size = int(self.headers.get("Content-Length", "0"))
                if size <= 0 or size > 65536:
                    raise Fault(422, "VALIDATION_ERROR", "Invalid demo request size")
                body = json.loads(self.rfile.read(size))
                out = platform.invoke(match[1], body, self.headers.get("Authorization"), self.headers.get("Idempotency-Key"), self.headers.get("traceparent"))
                self.send_json(200, out)
            except Fault as exc:
                self.send_json(exc.status, exc.problem(self.headers.get("traceparent")), "application/problem+json")
            except (ValueError, TypeError):
                self.send_json(400, Fault(400, "VALIDATION_ERROR", "Malformed request").problem(), "application/problem+json")
            except Exception:
                self.send_json(500, Fault(500, "UPSTREAM_UNAVAILABLE", "Internal reference error").problem(), "application/problem+json")

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


if __name__ == "__main__":
    server = make_server()
    print("Local synthetic Agent Gateway: http://127.0.0.1:8765 ; Ctrl-C to stop", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

