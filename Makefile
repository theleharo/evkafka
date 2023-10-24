
format:
		ruff evkafka tests --fix
		black evkafka tests

lint:
		ruff evkafka tests --fix
		black evkafka tests --check
		mypy evkafka

test:
		pytest
		pytest --dead-fixtures

check: format lint test

docs:
		mkdocs build

.PHONY: format lint test check docs
