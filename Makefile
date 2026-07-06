PYTHON ?= python3.12
VENV := .venv
PIP := $(VENV)/bin/pip
PY := $(VENV)/bin/python

.PHONY: setup test lint typecheck fetch-data backtest validate paper report kill audit

setup:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "✔ Environnement prêt. Copier .env.example vers .env si besoin (testnet/alertes)."

test:
	$(PY) -m pytest tests/ -q

lint:
	$(VENV)/bin/ruff check src/ tests/ scripts/
	$(VENV)/bin/ruff format --check src/ tests/ scripts/

typecheck:
	$(VENV)/bin/mypy src/risk src/execution src/backtest

fetch-data:
	$(PY) scripts/fetch_data.py

backtest:
	$(PY) scripts/run_backtest.py

validate:
	$(PY) scripts/run_validation.py

paper:
	$(PY) scripts/run_paper.py

report:
	$(PY) scripts/make_report.py

kill:
	$(PY) scripts/kill.py

audit:
	$(VENV)/bin/pip-audit -r requirements.txt
