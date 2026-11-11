# `make setup`으로 만든 .venv/bin/python 이 있으면 그것을, 없으면 python3 을 쓴다. PYTHON=... 으로 바꿀 수 있다.
PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)

.PHONY: setup scenarios demo stack test-impl db

# .venv 를 만들고 Python 의존성(jsonschema 등)을 설치한다.
# uv 가 있으면 uv 를 쓴다. 없으면 venv 와 ensurepip 를 따로 실행해서, pip 설치가 실패할 때 실제 오류가 보이게 한다.
setup:
	@if command -v uv >/dev/null 2>&1; then \
		uv venv --clear .venv && uv pip install --python .venv/bin/python -r requirements-dev.txt; \
	else \
		python3 -m venv --clear --without-pip .venv && \
		.venv/bin/python -m ensurepip --upgrade --default-pip && \
		.venv/bin/python -m pip install -r requirements-dev.txt; \
	fi

# 새 로컬 스택에 모든 시나리오를 실행하고 통과·실패 표를 출력한다.
scenarios:
	$(PYTHON) impl/scenarios/run.py

# 스택을 띄우고 브라우저에서 시나리오 화면(http://127.0.0.1:8700)을 연다.
demo:
	$(PYTHON) impl/demo/server.py

# 로컬 스택(가짜 모델·도구, Agent Gateway 모델·도구 경로, Platform APIs)을 띄운 채로 둔다.
stack:
	$(PYTHON) impl/stack.py

# impl/ 자동 테스트를 실행한다.
test-impl:
	$(PYTHON) -m unittest discover -s impl/tests -v

# Docker로 로컬 PostgreSQL을 띄운다(선택). 쓰려면 IMPL_DATABASE_URL=postgresql://impl:impl@127.0.0.1:55432/impl 을 함께 준다.
# 주지 않으면 stack.py가 설치된 PostgreSQL(initdb)로 실행마다 임시 DB를 만들고 끝나면 지운다.
db:
	docker compose -f impl/compose.yaml up -d
