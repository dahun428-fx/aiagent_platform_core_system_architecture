"""도구 실행 기록(effect ledger): 같은 멱등성 키의 도구 호출이 몇 번 들어와도 실제 실행은 한 번만 되게 한다.

PostgreSQL 표 하나에 키마다 한 줄을 둔다. 줄은 프로세스 밖에 있으므로 도구 경로를 재시작해도 남는다.
키 = tenant · principal(없으면 workload) · Agent · 도구 · 도구 버전 · 앱이 보낸 Idempotency-Key.
같은 키에 다른 요청(digest가 다름)이 오면 409, 처리 중이면 202, 끝났으면 저장된 결과를 그대로 돌려준다.
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
    status          text NOT NULL CHECK (status IN ('pending', 'succeeded')),
    result          jsonb,
    created_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, principal_id, agent_id, tool_id, tool_version, idempotency_key)
)
"""


class EffectLedger:
    """키 하나의 생애: claim(pending 줄을 만든 쪽만 실행) → succeed(결과 저장) 또는 release(실패하면 줄을 지워 다시 시도 가능).

    shortcut: 실행 중에 프로세스가 죽으면 pending 줄이 남아 그 키는 계속 202를 받는다.
              S6a에서 pending의 만료와 unknown_outcome 처리를 넣는다.
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
        return ("done", result) if status == "succeeded" else ("pending", None)

    # 실행이 끝났다: 결과를 저장해서, 같은 키로 다시 오면 실행하지 않고 이 결과를 돌려준다.
    def succeed(self, key, result):
        with self.connect() as conn:
            conn.execute("UPDATE tool_effects SET status = 'succeeded', result = %s WHERE tenant_id = %s"
                         " AND principal_id = %s AND agent_id = %s AND tool_id = %s AND tool_version = %s"
                         " AND idempotency_key = %s AND status = 'pending'", (Jsonb(result), *key))

    # 실행이 실패했다: 줄을 지워서 같은 키로 다시 시도할 수 있게 한다.
    # 읽기 도구라 다시 실행해도 외부에 남는 효과가 없으므로 안전하다. 쓰기 도구는 S6a에서 unknown_outcome으로 남기고 지우지 않는다.
    def release(self, key):
        with self.connect() as conn:
            conn.execute("DELETE FROM tool_effects WHERE tenant_id = %s AND principal_id = %s AND agent_id = %s"
                         " AND tool_id = %s AND tool_version = %s AND idempotency_key = %s AND status = 'pending'", key)
