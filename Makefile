.PHONY: run-bot
run-bot:
	@python -m app.delivery.bot


.PHONY: run-local-server
run-local-server:
	@python -m uvicorn app.delivery.web.asgi:application


.PHONY: run-prod-server
run-prod-server:
	@python -m gunicorn app.delivery.web.asgi:application \
		--worker-class uvicorn.workers.UvicornWorker \
		--bind ${HOST}:${PORT} \
		--workers ${WORKERS} \
		--log-level ${LOG_LEVEL} \
		--access-logfile ${ACCESS_LOGFILE} \
		--error-logfile ${ERROR_LOGFILE} \


.PHONY: makemigrations
makemigrations:
	@python manage.py makemigrations


.PHONY: migrate
migrate:
	@python manage.py migrate


# Tests, linters & formatters
.PHONY: lint
lint:
	@make EXIT_ZERO=true black isort
	@make EXIT_ZERO=true FLAKEHEAVEN_CACHE_TIMEOUT=0 -j 3 flakeheaven mypy


.PHONY: test
test:
	@pytest


.PHONY: check
check:
	@make EXIT_ZERO=false FLAKEHEAVEN_CACHE_TIMEOUT=0 -j 6 black isort flakeheaven mypy test


.PHONY: black
black:
    ifeq ($(EXIT_ZERO), false)
		@black --check --diff .
    else
		@black .
    endif


.PHONY: isort
isort:
    ifeq ($(EXIT_ZERO), false)
		@isort --check .
    else
		@isort .
    endif


.PHONY: flakeheaven
flakeheaven:
    ifeq ($(EXIT_ZERO), false)
		@flakeheaven lint .
    else
		@flakeheaven lint . --exit-zero
    endif


.PHONY: mypy
mypy:
	@mypy .
