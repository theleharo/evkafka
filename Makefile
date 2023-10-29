
format:
		ruff evkafka tests --fix
		black evkafka tests

lint:
		ruff evkafka tests
		black evkafka tests --check
		mypy evkafka

test:
		coverage run -m pytest
		coverage report -m
		pytest --dead-fixtures

testcov: test
		coverage html


check: format lint test

docs:
		mkdocs build

.PHONY: format lint test check docs testcov
