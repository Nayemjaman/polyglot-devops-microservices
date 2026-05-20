PYTHON ?= python3
VENV := .venv
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
UVICORN := $(VENV)/bin/uvicorn

ifneq (,$(wildcard .env))
include .env
export
endif

.PHONY: setup run test clean

setup:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

run:
	$(UVICORN) app.main:app --host $${HOST:-0.0.0.0} --port $${PORT:-8002} --reload

test:
	$(PYTEST)

clean:
	rm -rf .pytest_cache
