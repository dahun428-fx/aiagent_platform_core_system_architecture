# Uses .venv/bin/python when `make setup` has created it, otherwise python3. Override with PYTHON=...
PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)

.PHONY: setup scenarios stack test-impl

# Create .venv and install the Python dependencies (jsonschema and friends).
setup:
	python3 -m venv .venv
	.venv/bin/python -m pip install -r requirements-dev.txt

# Run every scenario against a fresh local stack and print the pass/fail table.
scenarios:
	$(PYTHON) impl/scenarios/run.py

# Keep the local stack up (fake model, Agent Gateway model route, Platform APIs).
stack:
	$(PYTHON) impl/stack.py

test-impl:
	$(PYTHON) -m unittest discover -s impl/tests -v
