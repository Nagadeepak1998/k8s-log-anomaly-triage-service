import json

from fastapi.testclient import TestClient

from k8s_log_anomaly_triage_service.app import app
from k8s_log_anomaly_triage_service.cli import main


def test_api_triage_and_metrics():
    client = TestClient(app)
    response = client.post(
        "/triage",
        json={
            "service": "payments-api",
            "environment": "staging",
            "logs": [
                {
                    "namespace": "payments",
                    "pod": "payments-1",
                    "container": "api",
                    "message": "OOMKilled after processing batch",
                }
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["incident_class"] == "memory_pressure"
    assert body["findings"][0]["recommendation"]

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "k8s_log_triage_requests_total" in metrics.text


def test_cli_returns_nonzero_when_risk_exceeds_threshold(tmp_path, capsys):
    path = tmp_path / "logs.json"
    path.write_text(
        json.dumps(
            [
                {
                    "namespace": "ml",
                    "pod": "embedder-1",
                    "message": "CrashLoopBackOff: back-off restarting failed container",
                }
            ]
        )
    )

    exit_code = main([str(path), "--service", "embedder", "--fail-at", "1"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "crash_loop" in captured.out
