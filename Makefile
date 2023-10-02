
format:
		ruff evkafka --fix
		black evkafka

check:
		ruff evkafka --fix
		black evkafka --check
		mypy evkafka

docs:
		mkdocs build

.PHONY: format check docs
