# Uses .venv/bin/python when `make setup` has created it, otherwise python3. Override with PYTHON=...
PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)

.PHONY: setup scenarios stack test-impl

# Create .venv and install the Python dependencies (jsonschema and friends).
# Uses uv when it is installed. Otherwise venv and ensurepip run as separate steps so a pip bootstrap
# failure shows its real error instead of venv's one-line summary.
setup:
	@if command -v uv >/dev/null 2>&1; then \
		uv venv --clear .venv && uv pip install --python .venv/bin/python -r requirements-dev.txt; \
	else \
		python3 -m venv --clear --without-pip .venv && \
		.venv/bin/python -m ensurepip --upgrade --default-pip && \
		.venv/bin/python -m pip install -r requirements-dev.txt; \
	fi

# Run every scenario against a fresh local stack and print the pass/fail table.
scenarios:
	$(PYTHON) impl/scenarios/run.py

# Keep the local stack up (fake model, Agent Gateway model route, Platform APIs).
stack:
	$(PYTHON) impl/stack.py

test-impl:
	$(PYTHON) -m unittest discover -s impl/tests -v
