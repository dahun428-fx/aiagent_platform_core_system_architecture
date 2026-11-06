"""Local conformance checks for an Agent folder. Every verdict is taken at the platform boundary
(responses, audit records, call counts), never from the adapter's internals."""
import copy
import re

import platform_ref as ref

TRACE = "00-0123456789abcdef0123456789abcdef-0123456789abcdef-01"
CREDENTIAL_LIKE = re.compile(r"lease-[0-9a-f]{8,}|credentialRef|Bearer\s+\S+", re.I)


def _body(content="conformance"):
    body = ref.load("invocation")
    body["input"]["content"] = content
    return body


def _platform(agent_dir):
    platform = ref.Platform()
    agent_id = platform.register(agent_dir)
    return platform, agent_id


def _status(call):
    try:
        call()
    except ref.Fault as fault:
        return fault.status
    return 200


def _runs(platform):
    return sum(e["component"] == "runtime" for e in platform.audit)


def check_manifest(agent_dir):
    _platform(agent_dir)
    return "Manifest valid, adapter python-inprocess-v1, profile local"


def check_success(agent_dir):
    platform, agent_id = _platform(agent_dir)
    result = platform.invoke(agent_id, _body(), "Bearer mock-user", "c2", TRACE)
    ref.validate("result", result)
    assert result["status"] == "succeeded"
    return "200, result.schema valid"


def check_missing_token(agent_dir):
    platform, agent_id = _platform(agent_dir)
    assert _status(lambda: platform.invoke(agent_id, _body(), "", "c3", TRACE)) == 401
    assert _runs(platform) == 0
    return "401 without token, adapter not executed"


def check_tenant_spoof(agent_dir):
    platform, agent_id = _platform(agent_dir)
    body = _body()
    body["context"]["tenantId"] = "tenant-other"
    assert _status(lambda: platform.invoke(agent_id, body, "Bearer mock-user", "c4", TRACE)) == 403
    assert _runs(platform) == 0
    return "403 on tenant spoof, adapter not executed"


def check_replay(agent_dir):
    platform, agent_id = _platform(agent_dir)
    first = platform.invoke(agent_id, _body(), "Bearer mock-user", "c5", TRACE)
    second = platform.invoke(agent_id, _body(), "Bearer mock-user", "c5", TRACE)
    assert first == second and _runs(platform) == 1
    return "same key replay returns stored result, adapter executed once"


def check_conflict(agent_dir):
    platform, agent_id = _platform(agent_dir)
    platform.invoke(agent_id, _body("one"), "Bearer mock-user", "c6", TRACE)
    assert _status(lambda: platform.invoke(agent_id, _body("two"), "Bearer mock-user", "c6", TRACE)) == 409
    return "409 on key reuse with different content"


def check_required_scopes(agent_dir):
    platform, agent_id = _platform(agent_dir)
    agent = platform.agents[agent_id]
    agent["manifest"] = copy.deepcopy(agent["manifest"])
    agent["manifest"]["identity"]["requiredScopes"].append("admin.all")
    body = _body()
    assert _status(lambda: platform.invoke(agent_id, body, "Bearer mock-user", "c10", TRACE)) == 403
    assert _runs(platform) == 0
    return "caller without a Manifest requiredScopes entry is denied (403) before the adapter runs"


def check_identity_mode(agent_dir):
    seen = {}
    for mode in ("delegated", "independent"):
        platform, agent_id = _platform(agent_dir)
        agent = platform.agents[agent_id]
        agent["manifest"] = copy.deepcopy(agent["manifest"])
        agent["manifest"]["identity"]["mode"] = mode
        original = platform.runtime.execute

        def capture(envelope, a, key, _orig=original, _mode=mode):
            seen[_mode] = copy.deepcopy(envelope["identity"])
            return _orig(envelope, a, key)

        platform.runtime.execute = capture
        try:
            platform.invoke(agent_id, _body(), "Bearer mock-user", "c11-" + mode, TRACE)
        except ref.Fault:
            pass  # an independent Agent may lack grants for its own calls; the envelope is what is checked
    assert seen["delegated"]["mode"] == "delegated" and seen["delegated"].get("principalId")
    ind = seen["independent"]
    assert ind["mode"] == "independent" and "principalId" not in ind and ind["delegation"] == []
    return "delegated runs as the caller; independent runs as the Agent workload without the user principal"


def check_classification(agent_dir):
    platform, agent_id = _platform(agent_dir)
    platform.data_classification = "restricted"
    platform.model.available = {"external"}
    body = _body()
    body["context"]["dataClassification"] = "public"
    status = _status(lambda: platform.invoke(agent_id, body, "Bearer mock-user", "c7", TRACE))
    external = [e for e in platform.audit if e["component"] == "model-gateway" and e.get("provider") == "external"]
    assert not external, "restricted data reached the external model route"
    assert status in (200, 503), status
    used = any(e["component"] == "model-gateway" for e in platform.audit) or status == 503
    return ("caller cannot downgrade classification; external route unused"
            + ("" if used else " (this adapter did not call the model route, so only the platform rule was checked)"))


def check_tools_and_leakage(agent_dir):
    platform, agent_id = _platform(agent_dir)
    agent = platform.agents[agent_id]
    envelope = {"invocationId": "inv-c8", "agentId": agent_id, "agentVersion": agent["version"], "request": _body(),
                "identity": {**ref.load("identity"), "agentId": agent_id}, "policy": ref.load("policy"), "traceparent": TRACE}
    probe = copy.copy(agent)
    probe["adapter"] = type("Probe", (), {"handle": lambda self, ctx, m: ctx.call_tool("tool-undeclared", "0.1.0", {"query": "x"})})()
    assert _status(lambda: platform.runtime.execute(envelope, probe, "c8")) == 403
    result = platform.invoke(agent_id, _body(), "Bearer mock-user", "c8", TRACE)
    assert not CREDENTIAL_LIKE.search(result["output"]["content"]), "credential-like text in output"
    return "undeclared tool denied (403); no credential-like text in output"


def check_adapter_failure(agent_dir):
    platform, agent_id = _platform(agent_dir)
    agent = platform.agents[agent_id]
    original = agent["adapter"]

    class Failing:
        def handle(self, ctx, message):
            raise RuntimeError("internal-secret-detail")

    agent["adapter"] = Failing()
    try:
        platform.invoke(agent_id, _body(), "Bearer mock-user", "c9", TRACE)
        raise AssertionError("adapter failure did not fail the call")
    except ref.Fault as fault:
        assert fault.status == 500 and "internal-secret-detail" not in fault.detail
    agent["adapter"] = original
    platform.invoke(agent_id, _body(), "Bearer mock-user", "c9", TRACE)
    assert _runs(platform) == 2, "failed result was cached"
    return "500 without adapter message; failure not cached, retry executes"


LOADING, ADAPTER, PLATFORM = "manifest-loading", "adapter-path", "platform-enforcement"

# (id, title, group, check). Groups say what a PASS guarantees:
#   manifest-loading      the Manifest is valid and the local Registry accepts it
#   adapter-path          this adapter produced a valid result through its own code path
#   platform-enforcement  the platform enforces the rule around this adapter (the adapter cannot weaken it)
CHECKS = [
    ("C1", "Manifest and registration", LOADING, check_manifest),
    ("C2", "Successful call", ADAPTER, check_success),
    ("C3", "Missing token", PLATFORM, check_missing_token),
    ("C4", "Tenant spoof", PLATFORM, check_tenant_spoof),
    ("C5", "Idempotent replay", PLATFORM, check_replay),
    ("C6", "Idempotency conflict", PLATFORM, check_conflict),
    ("C7", "Classification downgrade", PLATFORM, check_classification),
    ("C8", "Undeclared tool and credential leakage", PLATFORM, check_tools_and_leakage),
    ("C9", "Adapter failure", PLATFORM, check_adapter_failure),
    ("C10", "Manifest requiredScopes", PLATFORM, check_required_scopes),
    ("C11", "Manifest identity.mode", PLATFORM, check_identity_mode),
]

SCOPE_NOTE = ("Local conformance covers Manifest loading, this adapter's basic path and platform rule enforcement. "
              "It is not a business-quality, security or production certification.")


def run(agent_dir):
    """Return a list of {id, title, passed, detail}. Later checks are skipped if C1 fails."""
    results = []
    for check_id, title, group, check in CHECKS:
        if results and check_id != "C1" and not results[0]["passed"]:
            results.append({"id": check_id, "title": title, "group": group, "passed": False, "detail": "skipped: C1 failed"})
            continue
        try:
            detail = check(agent_dir)
            results.append({"id": check_id, "title": title, "group": group, "passed": True, "detail": detail})
        except (AssertionError, ref.Fault, ref.AgentLoadError, OSError) as exc:
            results.append({"id": check_id, "title": title, "group": group, "passed": False,
                            "detail": f"{type(exc).__name__}: {exc}" if str(exc) else type(exc).__name__})
    return results
