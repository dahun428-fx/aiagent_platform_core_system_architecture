"""도구 실행 기록(effect ledger): 같은 멱등성 키의 도구 호출이 몇 번 들어와도 실제 실행은 한 번만 되게 한다.

PostgreSQL 표 하나에 키마다 한 줄을 둔다. 줄은 프로세스 밖에 있으므로 도구 경로를 재시작해도 남는다.
키 = tenant · principal(없으면 workload) · Agent · 도구 · 도구 버전 · 앱이 보낸 Idempotency-Key.
같은 키에 다른 요청(digest가 다름)이 오면 409, 처리 중이면 202, 끝났으면 저장된 결과를 그대로 돌려준다.
끝난 결과에는 성공(succeeded)과, 쓰기 도구의 응답을 잃어 실행 여부를 모르는 unknown_outcome이 있다.
쓰기 도구의 승인 기록(tool_approvals)도 같은 DB에 둔다.
"""
from __future__ import annotations

import psycopg
from psycopg.types.json import Jsonb

SCHEMA = """
CREATE TABLE IF NOT EXISTS tool_effects (
    tenant_id       text NOT NULL,
    principal_id    text NOT NULL,
    agent_id        text NOT NULL,
    tool_id         text NOT NULL,
    tool_version    text NOT NULL,
    idempotency_key text NOT NULL,
    request_digest  text NOT NULL,
    status          text NOT NULL,
    result          jsonb,
    created_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, principal_id, agent_id, tool_id, tool_version, idempotency_key)
);
-- S5에서 만든 표는 status를 pending·succeeded로만 제한했다. unknown_outcome을 넣을 수 있게 제한을 바꾼다.
ALTER TABLE tool_effects DROP CONSTRAINT IF EXISTS tool_effects_status_check;
ALTER TABLE tool_effects ADD CONSTRAINT tool_effects_status_check CHECK (status IN ('pending', 'succeeded', 'unknown_outcome'));
CREATE TABLE IF NOT EXISTS tool_approvals (
    approval_id text PRIMARY KEY,
    approval    jsonb NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);
"""


class EffectLedger:
    """키 하나의 생애: claim(pending 줄을 만든 쪽만 실행) → finish(결과 저장) 또는 release(실패하면 줄을 지워 다시 시도 가능).

    shortcut: 실행 중에 프로세스가 죽으면 pending 줄이 남아 그 키는 계속 202를 받는다.
              pending 만료(읽기는 다시 실행, 쓰기는 unknown_outcome)는 worker가 여럿이 되는 S6b에서 넣는다.
    """

    def __init__(self, url):
        self.url = url
        with self.connect() as conn:
            conn.execute(SCHEMA)

    # 호출마다 새 연결을 연다. autocommit이라 문장 하나가 곧 트랜잭션 하나다.
    # shortcut: 연결 풀이 없다. 호출이 많아지면 psycopg_pool로 바꾼다.
    def connect(self):
        return psycopg.connect(self.url, autocommit=True, connect_timeout=5)

    # 이 키로 실행할 권리를 얻는다. 처음 온 요청이면 ("run", None).
    # 이미 줄이 있으면: digest가 다르면 ("conflict", None), 처리 중이면 ("pending", None), 끝났으면 ("done", 저장된 결과).
    # INSERT ... ON CONFLICT DO NOTHING 한 문장으로 "없으면 만들기"를 원자적으로 해서, 동시에 두 요청이 와도 하나만 실행한다.
    def claim(self, key, digest):
        with self.connect() as conn:
            inserted = conn.execute(
                "INSERT INTO tool_effects (tenant_id, principal_id, agent_id, tool_id, tool_version, idempotency_key,"
                " request_digest, status) VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending') ON CONFLICT DO NOTHING",
                (*key, digest)).rowcount
            if inserted:
                return "run", None
            row = conn.execute(
                "SELECT request_digest, status, result FROM tool_effects WHERE tenant_id = %s AND principal_id = %s"
                " AND agent_id = %s AND tool_id = %s AND tool_version = %s AND idempotency_key = %s", key).fetchone()
        if row is None:  # claim과 SELECT 사이에 release로 지워졌다. 다시 시도한다.
            return self.claim(key, digest)
        stored_digest, status, result = row
        if stored_digest != digest:
            return "conflict", None
        return ("pending", None) if status == "pending" else ("done", result)

    # 실행이 끝났다: 결과(tool-result)를 저장해서, 같은 키로 다시 오면 실행하지 않고 이 결과를 돌려준다.
    # 줄의 status는 결과의 status(succeeded 또는 unknown_outcome)를 그대로 쓴다.
    def finish(self, key, result):
        with self.connect() as conn:
            conn.execute("UPDATE tool_effects SET status = %s, result = %s WHERE tenant_id = %s"
                         " AND principal_id = %s AND agent_id = %s AND tool_id = %s AND tool_version = %s"
                         " AND idempotency_key = %s AND status = 'pending'", (result["status"], Jsonb(result), *key))

    # 실행이 실패했다: 줄을 지워서 같은 키로 다시 시도할 수 있게 한다.
    # upstream이 요청을 받지 못한 것이 확실할 때(읽기 도구의 실패, 쓰기 도구의 연결 실패)만 부른다.
    def release(self, key):
        with self.connect() as conn:
            conn.execute("DELETE FROM tool_effects WHERE tenant_id = %s AND principal_id = %s AND agent_id = %s"
                         " AND tool_id = %s AND tool_version = %s AND idempotency_key = %s AND status = 'pending'", key)

    # 승인 기록을 저장한다(같은 approvalId면 새 내용으로 바꾼다). 승인이 맞는지는 쓰기 도구를 부를 때 검사한다.
    def save_approval(self, approval):
        with self.connect() as conn:
            conn.execute("INSERT INTO tool_approvals (approval_id, approval) VALUES (%s, %s)"
                         " ON CONFLICT (approval_id) DO UPDATE SET approval = EXCLUDED.approval",
                         (approval["approvalId"], Jsonb(approval)))

    # 승인 기록을 읽는다. 없으면 None.
    def load_approval(self, approval_id):
        with self.connect() as conn:
            row = conn.execute("SELECT approval FROM tool_approvals WHERE approval_id = %s", (approval_id,)).fetchone()
        return row[0] if row else None
