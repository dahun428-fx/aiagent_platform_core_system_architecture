"""Run after platform_ref.py. Uses only Python standard library."""
import json
from urllib.request import Request, urlopen

body = {"input": {"type": "message", "content": "hello"},
        "context": {"tenantId": "tenant-demo", "dataClassification": "internal"},
        "execution": {"mode": "sync", "timeoutMs": 5000}}
req = Request("http://127.0.0.1:8765/v1/agents/agent-demo/invocations",
              json.dumps(body).encode(), {"Content-Type": "application/json",
              "Authorization": "Bearer mock-user", "Idempotency-Key": "python-demo"})
with urlopen(req, timeout=5) as response:
    print(json.dumps(json.load(response), ensure_ascii=False, indent=2))

