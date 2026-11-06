import copy
import importlib.util
import json
import threading
import unittest
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("platform_ref", ROOT / "examples/python/platform_ref.py")
ref = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ref)
from test_contracts import validator


def fixture(name):
    return json.loads((ROOT / "examples/fixtures" / (name + ".json")).read_text(encoding="utf-8"))


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.platform = ref.Platform()
        self.request = fixture("invocation")
        self.identity = fixture("identity")
        self.policy = fixture("policy")
        self.trace = fixture("result")["traceparent"]

    def invoke(self, body=None, key="test-key", token="Bearer mock-user"):
        return self.platform.invoke("agent-demo", body or self.request, token, key, self.trace)

    def test_vertical_flow_and_output_contract(self):
        result = self.invoke()
        validator("result").validate(result)
        self.assertEqual(result["output"]["content"], "mock:hello")
        self.assertEqual([e["component"] for e in self.platform.audit], ["agent-gateway", "runtime", "model-gateway"])
        self.assertTrue(all(e["traceparent"] == self.trace for e in self.platform.audit))

    def test_missing_auth_and_tenant_spoof_denied(self):
        with self.assertRaises(ref.Fault) as e:
            self.invoke(token="")
        self.assertEqual(e.exception.status, 401)
        self.request["context"]["tenantId"] = "tenant-other"
        with self.assertRaises(ref.Fault) as e:
            self.invoke()
        self.assertEqual(e.exception.status, 403)

    def test_unknown_agent_and_unsupported_async(self):
        with self.assertRaises(ref.Fault) as e:
            self.platform.invoke("agent-unknown", self.request, "Bearer mock-user", "k", self.trace)
        self.assertEqual(e.exception.status, 404)
        self.request["execution"]["mode"] = "durable"
        with self.assertRaises(ref.Fault) as e:
            self.invoke()
        self.assertEqual(e.exception.status, 501)

    def test_input_validation_and_trace_validation(self):
        self.request["context"]["principalId"] = "forged-user"
        with self.assertRaises(ref.Fault) as e:
            self.invoke()
        self.assertEqual(e.exception.status, 422)
        with self.assertRaises(ref.Fault):
            self.platform.invoke("agent-demo", fixture("invocation"), "Bearer mock-user", "x", "00-" + "0" * 32 + "-" + "1" * 16 + "-01")

    def test_idempotency_replay_and_body_conflict(self):
        a = self.invoke()
        b = self.invoke()
        self.assertEqual(a, b)
        self.assertEqual(self.platform.model.calls, 1)
        self.request["input"]["content"] = "different"
        with self.assertRaises(ref.Fault) as e:
            self.invoke()
        self.assertEqual(e.exception.status, 409)

    def test_concurrent_idempotency(self):
        out = []
        threads = [threading.Thread(target=lambda: out.append(self.invoke())) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len(out), 8)
        self.assertTrue(all(x == out[0] for x in out))
        self.assertEqual(self.platform.model.calls, 1)

    def test_classification_routing_fail_closed(self):
        self.policy["classification"] = "confidential"
        out = self.platform.model.invoke("hello", self.identity, self.policy, self.trace)
        self.assertEqual(out["provider"], "self-hosted")
        self.platform.model.available = {"external"}
        with self.assertRaises(ref.Fault):
            self.platform.model.invoke("hello", self.identity, self.policy, self.trace)
        self.platform.model.available = set()
        with self.assertRaises(ref.Fault):
            self.platform.model.invoke("hello", self.identity, self.policy, self.trace)

    def test_caller_cannot_downgrade_classification(self):
        # Server-side classification is restricted and only an external model is available.
        self.platform.data_classification = "restricted"
        self.platform.model.available = {"external"}
        self.request["context"]["dataClassification"] = "public"
        with self.assertRaises(ref.Fault) as e:
            self.invoke()
        self.assertEqual(e.exception.status, 503)
        self.assertEqual(self.platform.model.calls, 0)
        self.assertEqual(ref.effective_classification("public", "restricted"), "restricted")
        self.assertEqual(ref.effective_classification("confidential", "internal"), "confidential")

    def test_tool_retry_with_new_trace_returns_cached_result(self):
        first = self.platform.tools.invoke(fixture("tool-invoke"))
        retry = fixture("tool-invoke")
        retry["traceparent"] = "00-" + "a" * 32 + "-" + "b" * 16 + "-01"
        self.assertEqual(self.platform.tools.invoke(retry), first)
        self.assertEqual(sum(e["component"] == "credential-broker" for e in self.platform.audit), 1)
        changed = fixture("tool-invoke")
        changed["arguments"]["query"] = "different"
        with self.assertRaises(ref.Fault) as e:
            self.platform.tools.invoke(changed)
        self.assertEqual(e.exception.status, 409)
        revoked = fixture("tool-invoke")
        revoked["identity"]["scopes"] = ["agents.invoke"]
        with self.assertRaises(ref.Fault):
            self.platform.tools.invoke(revoked)

    def test_policy_unavailable_and_expired(self):
        self.platform.policy_available = False
        with self.assertRaises(ref.Fault):
            self.invoke()
        self.policy["expiresAt"] = "2000-01-01T00:00:00Z"
        with self.assertRaises(ref.Fault):
            self.platform.model.invoke("hello", self.identity, self.policy, self.trace)

    def test_tool_broker_and_no_credential_leak(self):
        request = fixture("tool-invoke")
        result = self.platform.tools.invoke(request)
        validator("tool-result").validate(result)
        self.assertEqual(result["output"]["content"], "tool:hello")
        self.assertNotIn("credential", json.dumps(result).lower())
        self.assertEqual([e["component"] for e in self.platform.audit], ["credential-broker", "tool-gateway"])

    def test_tool_unknown_scope_tenant_and_write_denied(self):
        for mutate in [
            lambda r: r.update(toolId="tool-unknown"),
            lambda r: r["identity"].update(scopes=["agents.invoke"]),
            lambda r: r["identity"].update(tenantId="tenant-other"),
            lambda r: r.update(version="9.0.0"),
        ]:
            r = fixture("tool-invoke")
            mutate(r)
            with self.assertRaises(ref.Fault):
                self.platform.tools.invoke(r)
        self.platform.tools.descriptor["effect"] = "write"
        with self.assertRaises(ref.Fault):
            self.platform.tools.invoke(fixture("tool-invoke"))

    def test_lease_binding_expiry_audience_scope(self):
        request = fixture("credential-request")
        lease = self.platform.broker.issue(request, self.policy)
        validator("credential-lease").validate(lease)
        with self.assertRaises(ref.Fault):
            self.platform.broker.consume(lease["credentialRef"], "other-workload", "inv-demo", "tool-search")
        with self.assertRaises(ref.Fault):
            self.platform.broker.consume(lease["credentialRef"], "runtime-demo", "inv-other", "tool-search")
        with self.assertRaises(ref.Fault):
            self.platform.broker.consume(lease["credentialRef"], "runtime-demo", "inv-demo", "other-audience")
        self.platform.broker.now = lambda: datetime(2100, 1, 1, tzinfo=timezone.utc)
        with self.assertRaises(ref.Fault):
            self.platform.broker.consume(lease["credentialRef"], "runtime-demo", "inv-demo", "tool-search")
        for key, value in [("resource", "resource-unknown"), ("scopes", ["admin.all"]), ("policyDecisionId", "policy-forged")]:
            r = fixture("credential-request")
            r[key] = value
            with self.assertRaises(ref.Fault):
                self.platform.broker.issue(r, self.policy)

    def test_approval_replay_and_expiry(self):
        a = fixture("approval")
        ref.verify_approval(a, "tenant-demo", "inv-demo", a["subjectDigest"], "0.1.0")
        for args in [("tenant-other", "inv-demo", a["subjectDigest"], "0.1.0"), ("tenant-demo", "inv-other", a["subjectDigest"], "0.1.0"), ("tenant-demo", "inv-demo", "sha256:" + "b" * 64, "0.1.0"), ("tenant-demo", "inv-demo", a["subjectDigest"], "0.2.0")]:
            with self.assertRaises(ref.Fault):
                ref.verify_approval(a, *args)
        a["expiresAt"] = "2000-01-01T00:00:00Z"
        with self.assertRaises(ref.Fault):
            ref.verify_approval(a, "tenant-demo", "inv-demo", a["subjectDigest"], "0.1.0")

    def test_retrieval_acl_and_classification_before_context(self):
        documents = fixture("retrieval")["documents"]
        other = {**documents[0], "tenantId": "tenant-other"}
        forbidden = {**documents[0], "allowedPrincipals": ["someone-else"]}
        restricted = {**documents[0], "classification": "restricted"}
        out = ref.retrieve(documents + [other, forbidden, restricted], self.identity, self.policy)
        self.assertEqual(out, documents)

    def test_cross_agent_cycles_depth_scope_and_tenant(self):
        r = fixture("cross-agent")
        ref.validate_cross_agent(r, self.identity["scopes"])
        for mutate in [
            lambda x: x.update(targetAgentId="agent-demo"),
            lambda x: x.update(depth=100),
            lambda x: x["identity"].update(scopes=["admin.all"]),
            lambda x: x["identity"].update(tenantId="tenant-other"),
            lambda x: x.update(budgetRemaining=0),
        ]:
            x = copy.deepcopy(r)
            mutate(x)
            with self.assertRaises(ref.Fault):
                ref.validate_cross_agent(x, self.identity["scopes"])

    def test_evaluation_and_redaction(self):
        self.policy["classification"] = "internal"
        score = sum(self.platform.model.invoke(case, self.identity, self.policy, self.trace)["content"] == "mock:" + case for case in ["hello", "한글", ""]) / 3
        result = fixture("evaluation")
        result.update(score=score, passed=score >= result["threshold"])
        validator("evaluation").validate(result)
        self.assertTrue(result["passed"])
        self.platform.record("test", self.trace, {"access_token": "sensitive", "prompt": "PII", "tenantId": "tenant-demo"})
        self.assertNotIn("sensitive", json.dumps(self.platform.audit))
        self.assertNotIn("PII", json.dumps(self.platform.audit))

    def test_broker_trace_follows_tool_invocation(self):
        request = fixture("tool-invoke")
        request["traceparent"] = "00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-01"
        self.platform.tools.invoke(request)
        self.assertTrue(all(e["traceparent"] == request["traceparent"] for e in self.platform.audit))

    def test_http_contract_smoke(self):
        server = ref.make_server(port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            req = Request(base + "/v1/agents/agent-demo/invocations", json.dumps(self.request).encode(), {"Authorization": "Bearer mock-user", "Idempotency-Key": "http-key", "traceparent": self.trace, "Content-Type": "application/json"})
            with urlopen(req, timeout=5) as response:
                result = json.load(response)
                validator("result").validate(result)
                self.assertEqual(response.headers["traceparent"], self.trace)
            with self.assertRaises(HTTPError) as e:
                urlopen(Request(base + "/v1/agents/agent-demo/invocations", b"{}"), timeout=5)
            self.assertEqual(e.exception.code, 401)
            validator("problem").validate(json.load(e.exception))
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

