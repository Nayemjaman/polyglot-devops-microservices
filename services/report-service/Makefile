PYTHON ?= python3
VENV := .venv
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
UVICORN := $(VENV)/bin/uvicorn
ALEMBIC := $(VENV)/bin/alembic

ifneq (,$(wildcard .env))
include .env
export
endif

.PHONY: setup run test migrate clean

setup:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

run:
	$(UVICORN) app.main:app --host $${HOST:-0.0.0.0} --port $${PORT:-8003} --reload

migrate:
	$(ALEMBIC) upgrade head

test:
	$(PYTEST)

clean:
	rm -rf .pytest_cache
