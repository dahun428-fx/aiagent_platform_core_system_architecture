"""Local-only reference, not a production identity provider or durable engine."""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import os
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
    return json.loads((ROOT / "examples/fixtures" / (name + ".json")).read_text(encoding="utf-8"))


@lru_cache
def validators():
    schemas = [json.loads(p.read_text(encoding="utf-8")) for p in (ROOT / "contracts").glob("*.schema.json")]
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


def agent_identity(caller, agent, policy):
    """Identity the Agent runs with. delegated: the caller's identity. independent: the Agent's own workload
    identity, whose grant is the Manifest requiredScopes capped by policy. It never carries the user principal."""
    mode = agent["manifest"]["identity"]["mode"]
    if mode == "delegated":
        return copy.deepcopy(caller)
    if mode == "independent":
        grant = [s for s in agent["manifest"]["identity"]["requiredScopes"] if s in policy["allowedScopes"]]
        return {"tenantId": caller["tenantId"], "agentId": agent["id"], "workloadId": "workload-" + agent["id"],
                "mode": "independent", "scopes": grant, "delegation": []}
    raise Fault(501, "NOT_IMPLEMENTED", "Unsupported identity.mode")


def canonical_digest(value):
    return "sha256:" + hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def verify_approval(approval, tenant, invocation, digest, policy_version):
    validate("approval", approval)
    expected = (tenant, invocation, digest, policy_version, "approved")
    actual = tuple(approval[k] for k in ("tenantId", "invocationId", "subjectDigest", "policyVersion", "decision"))
    if expected != actual or expiration(approval["expiresAt"]) <= utcnow():
        raise Fault(403, "FORBIDDEN", "Approval is stale or not bound to this request")


def effective_classification(declared, authoritative):
    """The caller's declared classification is an assertion. It may raise, never lower, the server-side value."""
    return max(declared, authoritative, key=lambda c: RANK[c])


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

    def route(self, identity, policy):
        """Authorize and pick a policy-approved provider. Shared with the HTTP model route in impl/."""
        authorize(identity, policy, "models.invoke")
        candidates = ["self-hosted"] if policy["classification"] in ("confidential", "restricted") else ["self-hosted", "external"]
        provider = next((p for p in candidates if p in self.available and "model-" + p in policy["allowedResources"]), None)
        if provider is None:
            raise Fault(503, "UPSTREAM_UNAVAILABLE", "No policy-approved model route")
        return provider

    def invoke(self, content, identity, policy, traceparent):
        provider = self.route(identity, policy)
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
        # Same business effect = same arguments against the same approved resource. Trace and policy evidence are
        # re-validated on every attempt (authorize above) and must not turn a legitimate retry into a conflict.
        digest = canonical_digest({"arguments": request["arguments"], "resource": self.descriptor["resource"]})
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


ADAPTER_ID = "python-inprocess-v1"
IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
BUILTIN_AGENTS = ROOT / "examples/agents"


class AgentAdapter(Protocol):
    """What an Agent implements: business logic only. See docs/onboarding/14-connect-your-agent.md."""
    def handle(self, ctx: "AgentContext", message: dict) -> dict: ...


class ContextError(Exception):
    """A platform decision raised inside an AgentContext call. The Runtime re-raises the original Fault."""
    def __init__(self, fault):
        self.fault = fault
        super().__init__(fault.detail)


class AgentContext:
    """The only capabilities an adapter receives. Identity, policy, credentials and platform objects stay with
    the platform and are injected inside these calls. In-process loading is not an isolation boundary."""
    def __init__(self, generate, call_tool, log):
        self._generate, self._call_tool, self._log = generate, call_tool, log

    def generate(self, prompt: str) -> str:
        return self._generate(prompt)

    def call_tool(self, tool_id: str, version: str, arguments: dict) -> str:
        return self._call_tool(tool_id, version, arguments)

    def log(self, event: str, **fields) -> None:
        self._log(event, fields)


class AgentLoadError(ValueError):
    pass


def _inside(child, parent):
    child, parent = os.path.normcase(str(child)), os.path.normcase(str(parent))
    return os.path.dirname(child) == parent


def load_agent(agent_dir):
    """Load one local Agent folder: agent-manifest.json plus the module named by runtime.entrypoint."""
    base = Path(agent_dir).resolve(strict=True)
    try:
        manifest = json.loads((base / "agent-manifest.json").read_text(encoding="utf-8"))
        validate("agent-manifest", manifest)
    except (OSError, ValueError, Fault) as exc:
        raise AgentLoadError("Invalid or unreadable Agent Manifest") from exc
    runtime = manifest["runtime"]
    if runtime["adapter"] != ADAPTER_ID:
        raise AgentLoadError("Unsupported runtime.adapter; this kit supports " + ADAPTER_ID)
    if runtime["executionMode"] != "sync":
        raise AgentLoadError("Only sync execution is supported locally")
    if manifest["deployment"]["profile"] != "local":
        raise AgentLoadError("The local Registry only accepts deployment.profile = local")
    module_name, _, factory_name = runtime["entrypoint"].partition(":")
    if not (IDENTIFIER.fullmatch(module_name) and IDENTIFIER.fullmatch(factory_name)):
        raise AgentLoadError("runtime.entrypoint must be module:factory with plain identifiers")
    try:
        path = (base / (module_name + ".py")).resolve(strict=True)
    except OSError as exc:
        raise AgentLoadError("Entrypoint module not found in the Agent folder") from exc
    if not _inside(path, base):
        raise AgentLoadError("Entrypoint must be a file directly inside the Agent folder")
    agent_id = manifest["metadata"]["id"]
    unique = "agent_" + hashlib.sha256(str(base).encode()).hexdigest()[:12] + "_" + module_name
    spec = importlib.util.spec_from_file_location(unique, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    factory = getattr(module, factory_name, None)
    if not callable(factory):
        raise AgentLoadError("Entrypoint factory not found")
    adapter = factory()
    if not callable(getattr(adapter, "handle", None)):
        raise AgentLoadError("Adapter must implement handle(ctx, message)")
    return {"id": agent_id, "version": manifest["metadata"]["version"], "manifest": manifest, "adapter": adapter,
            "classification": manifest["governance"]["classification"],
            "tools": set(manifest["capabilities"]["tools"]), "dir": base}


class Runtime:
    def __init__(self, model, tools, record):
        self.model, self.tools, self.record = model, tools, record

    def execute(self, envelope, agent, request_key):
        validate("runtime", envelope)
        self.record("runtime", envelope["traceparent"], {"invocationId": envelope["invocationId"]})
        identity, policy, trace = envelope["identity"], envelope["policy"], envelope["traceparent"]
        routes, usage, tool_calls = [], {"inputTokens": 0, "outputTokens": 0}, [0]

        def generate(prompt):
            try:
                out = self.model.invoke(prompt, identity, policy, trace)
            except Fault as fault:
                raise ContextError(fault) from None
            routes.append(out["routeDecisionId"])
            for k in usage:
                usage[k] += out["usage"][k]
            return out["content"]

        def call_tool(tool_id, version, arguments):
            if tool_id not in agent["tools"]:
                raise ContextError(Fault(403, "FORBIDDEN", "Tool is not declared in the Agent Manifest"))
            tool_calls[0] += 1
            request = {"invocationId": envelope["invocationId"], "toolId": tool_id, "version": version,
                       "arguments": arguments, "identity": identity, "policy": policy,
                       "idempotencyKey": request_key + ":tool-" + str(tool_calls[0]), "traceparent": trace}
            try:
                return self.tools.invoke(request)["output"]["content"]
            except Fault as fault:
                raise ContextError(fault) from None

        def log(event, fields):
            self.record("agent-log", trace, {"invocationId": envelope["invocationId"], **fields})

        try:
            output = agent["adapter"].handle(AgentContext(generate, call_tool, log), copy.deepcopy(envelope["request"]["input"]))
        except ContextError as exc:
            raise exc.fault from None
        except Exception:
            # Any adapter failure, including a Fault the adapter raises itself, is reported without its message.
            raise Fault(500, "UPSTREAM_UNAVAILABLE", "Agent adapter failed") from None
        result = {"invocationId": envelope["invocationId"], "agentVersion": envelope["agentVersion"], "status": "succeeded",
                  "output": output, "traceparent": trace,
                  "routeDecisionId": routes[-1] if routes else "route-none", "usage": usage}
        try:
            validate("result", result)
        except Fault:
            raise Fault(500, "UPSTREAM_UNAVAILABLE", "Agent adapter returned an invalid result") from None
        return result


class Platform:
    def __init__(self, agents_dir=None):
        self.audit = []
        self.model = ModelGateway(self.record)
        self.broker = CredentialBroker(self.record)
        self.tools = ToolGateway(self.broker, self.record)
        self.runtime = Runtime(self.model, self.tools, self.record)
        self.agents = {}
        self.register(BUILTIN_AGENTS / "agent-demo")
        if agents_dir:
            for child in sorted(Path(agents_dir).iterdir(), key=lambda c: c.name):
                if (child / "agent-manifest.json").is_file():
                    self.register(child)
        self.policy_available = True
        # Classification of the data this Agent handles, decided server-side (policy/data source), not by the caller.
        self.data_classification = None
        self.memo = {}
        self.lock = threading.Lock()

    def register(self, agent_dir):
        agent = load_agent(agent_dir)
        existing = self.agents.get(agent["id"])
        if existing and existing["dir"] != agent["dir"]:
            raise AgentLoadError("Duplicate Agent id: " + agent["id"])
        self.agents[agent["id"]] = agent
        return agent["id"]

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
        agent = self.agents.get(agent_id)
        if agent is None:
            raise Fault(404, "NOT_FOUND", "Unknown Agent")
        identity["agentId"] = agent_id
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
        authoritative = effective_classification(self.data_classification or agent["classification"], policy["classification"])
        policy["classification"] = effective_classification(body["context"]["dataClassification"], authoritative)
        authorize(identity, policy, "agents.invoke")
        # The caller must hold every scope the Manifest declares as required, before the adapter runs.
        for scope in agent["manifest"]["identity"]["requiredScopes"]:
            try:
                authorize(identity, policy, scope)
            except Fault:
                raise Fault(403, "FORBIDDEN", "Caller lacks a scope required by the Agent Manifest") from None
        caller_principal = identity["principalId"]
        identity = agent_identity(identity, agent, policy)
        # Memory-only, single-process idempotency. Real deployments need a persistent atomic effect ledger.
        cache_key = (identity["tenantId"], caller_principal, agent_id, agent["version"], key)
        digest = canonical_digest(body)
        with self.lock:
            if cache_key in self.memo:
                old_digest, old_result = self.memo[cache_key]
                if digest != old_digest:
                    raise Fault(409, "CONFLICT", "Idempotency key reused for different request")
                return copy.deepcopy(old_result)
            invocation_id = "inv-" + uuid.uuid4().hex
            self.record("agent-gateway", traceparent, {"tenantId": identity["tenantId"], "invocationId": invocation_id})
            result = self.runtime.execute({"invocationId": invocation_id, "agentId": agent_id, "agentVersion": agent["version"],
                                           "request": body, "identity": identity, "policy": policy, "traceparent": traceparent},
                                          agent, key)
            validate("result", result)
            self.memo[cache_key] = (digest, result)
            return copy.deepcopy(result)


def make_server(port=8765, agents_dir=None):
    platform = Platform(agents_dir)

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

    Handler.platform = platform
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def serve(port=8765, agents_dir=None):
    server = make_server(port, agents_dir)
    print("Local synthetic Agent Gateway: http://127.0.0.1:%d ; agents: %s ; Ctrl-C to stop"
          % (server.server_address[1], ", ".join(sorted(platform_of(server).agents))), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def platform_of(server):
    return server.RequestHandlerClass.platform


if __name__ == "__main__":
    serve()

