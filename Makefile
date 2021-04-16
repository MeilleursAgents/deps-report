PYTHON=poetry run
CODE = deps_report

.PHONY: format
.SILENT: format
format:
	$(PYTHON) black $(CODE)
	$(PYTHON) isort $(CODE)

.PHONY: style
.SILENT: style
style:
	$(PYTHON) black --check $(CODE)
	$(PYTHON) isort --check-only $(CODE)
	$(PYTHON) mypy -- $(CODE)
	$(PYTHON) pflake8 $(CODE)

.PHONY: test
.SILENT: test
test:
	$(PYTHON) pytest tests/
