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


def test_api_replay_review_and_metrics():
    client = TestClient(app)
    response = client.post(
        "/replay",
        json={
            "incident_id": "incident-123",
            "owner": "platform-oncall",
            "windows": [
                {
                    "window_id": "crashloop",
                    "service": "ranker-api",
                    "environment": "staging",
                    "logs": [
                        {
                            "namespace": "ml",
                            "pod": "ranker-1",
                            "message": "CrashLoopBackOff: back-off restarting failed container",
                        },
                        {
                            "namespace": "ml",
                            "pod": "ranker-1",
                            "message": "container exited with exit code 1",
                        },
                        {
                            "namespace": "ml",
                            "pod": "ranker-1",
                            "message": "Back-off restarting failed container",
                        },
                    ],
                }
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "page"
    assert body["dominant_incident_class"] == "crash_loop"

    metrics = client.get("/metrics")
    assert "k8s_log_replay_reviews_total" in metrics.text


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


def test_cli_replay_writes_markdown_report(tmp_path, capsys):
    path = tmp_path / "replay.json"
    report = tmp_path / "report.md"
    path.write_text(
        json.dumps(
            {
                "incident_id": "incident-123",
                "owner": "platform-oncall",
                "windows": [
                    {
                        "window_id": "crashloop",
                        "service": "ranker-api",
                        "environment": "staging",
                        "logs": [
                            {
                                "namespace": "ml",
                                "pod": "ranker-1",
                                "message": "CrashLoopBackOff: back-off restarting failed container",
                            },
                            {
                                "namespace": "ml",
                                "pod": "ranker-1",
                                "message": "container exited with exit code 1",
                            },
                            {
                                "namespace": "ml",
                                "pod": "ranker-1",
                                "message": "Back-off restarting failed container",
                            },
                        ],
                    }
                ],
            }
        )
    )

    exit_code = main(["replay", str(path), "--markdown", str(report)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert '"status": "page"' in captured.out
    assert "Kubernetes Log Replay Review" in report.read_text()


def test_api_and_cli_deployment_trends(tmp_path, capsys):
    payload = {
        "review_id": "series",
        "default_owner": "platform-oncall",
        "deployments": [
            {
                "deployment_id": "api-1",
                "deployed_at": "2026-07-17T00:00:00Z",
                "service": "api",
                "environment": "staging",
                "logs": [{"message": "context deadline exceeded"}],
            },
            {
                "deployment_id": "api-2",
                "deployed_at": "2026-07-18T00:00:00Z",
                "service": "api",
                "environment": "staging",
                "logs": [{"message": "upstream model unavailable"}],
            },
        ],
    }
    client = TestClient(app)
    response = client.post("/deployments/trends", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "page"
    assert "k8s_log_deployment_trend_reviews_total" in client.get("/metrics").text
    source, report = tmp_path / "trends.json", tmp_path / "trends.md"
    source.write_text(json.dumps(payload))
    assert main(["trends", str(source), "--markdown", str(report)]) == 1
    assert '"status": "page"' in capsys.readouterr().out
    assert "Deployment Anomaly Trend Review" in report.read_text()
