.PHONY: setup test lint run smoke replay-report trends-report docker-build

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
	. .venv/bin/activate && PYTHONPATH=src python -m k8s_log_anomaly_triage_service.cli examples/crashloop_logs.json --service embedding-api --environment staging --fail-at 90

replay-report:
	. .venv/bin/activate && PYTHONPATH=src python -m k8s_log_anomaly_triage_service.cli replay examples/replay_manifest.json --markdown reports/replay_review.md; rc=$$?; if [ $$rc -eq 1 ]; then echo "expected page decision"; exit 0; fi; exit $$rc

trends-report:
	. .venv/bin/activate && PYTHONPATH=src python -m k8s_log_anomaly_triage_service.cli trends examples/deployment_trends.json --markdown reports/deployment_trends.md; rc=$$?; if [ $$rc -eq 1 ]; then echo "expected page decision"; exit 0; fi; exit $$rc

docker-build:
	docker build -t k8s-log-anomaly-triage-service:local .
