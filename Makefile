.PHONY: setup test lint run smoke docker-build

setup:
	python3 -m venv .venv
	. .venv/bin/activate && python -m pip install --upgrade pip && pip install -e '.[dev]'

test:
	. .venv/bin/activate && pytest

lint:
	. .venv/bin/activate && ruff check .

run:
	. .venv/bin/activate && uvicorn k8s_log_anomaly_triage_service.app:app --host 0.0.0.0 --port 8000

smoke:
	. .venv/bin/activate && k8s-log-triage examples/crashloop_logs.json --service embedding-api --environment staging --fail-at 90

docker-build:
	docker build -t k8s-log-anomaly-triage-service:local .
