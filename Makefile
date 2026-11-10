PYTHON ?= python3

.PHONY: scenarios stack test-impl

# Run every scenario against a fresh local stack and print the pass/fail table.
scenarios:
	$(PYTHON) impl/scenarios/run.py

# Keep the local stack up (fake model, Agent Gateway model route, Platform APIs).
stack:
	$(PYTHON) impl/stack.py

test-impl:
	$(PYTHON) -m unittest discover -s impl/tests -v
