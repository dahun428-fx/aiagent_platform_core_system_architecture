# tool Agent 템플릿

이 폴더를 복사해 자기 Agent를 만듭니다.

1. 폴더를 복사하고 `agent-manifest.json`의 `metadata.id`, `metadata.name`을 바꿉니다.
2. `agent.py`의 `handle()`에 업무 로직을 작성합니다.
3. 검증: `python scripts/agentctl.py validate <폴더>/agent-manifest.json`
4. 적합성: `python scripts/agentctl.py conformance <폴더>`
5. 실행: `python scripts/agentctl.py run --agents-dir <폴더의 상위 폴더>`

자세한 안내: docs/onboarding/14-connect-your-agent.md
