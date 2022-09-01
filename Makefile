PYTHON=poetry run
CODE_DIR = deps_report
TESTS_DIR = tests

.PHONY: format
.SILENT: format
format:
	$(PYTHON) black $(CODE_DIR) $(TESTS_DIR)
	$(PYTHON) isort $(CODE_DIR) $(TESTS_DIR)

.PHONY: style
.SILENT: style
style:
	$(PYTHON) black --check $(CODE_DIR) $(TESTS_DIR)
	$(PYTHON) isort --check-only $(CODE_DIR) $(TESTS_DIR)
	$(PYTHON) mypy -- $(CODE_DIR)
	$(PYTHON) flake8 $(CODE_DIR)

.PHONY: test
.SILENT: test
test:
	$(PYTHON) pytest


.PHONY: build
.SILENT: build
build:
	poetry build
