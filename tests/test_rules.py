from k8s_log_anomaly_triage_service.models import LogEvent
from k8s_log_anomaly_triage_service.rules import triage_logs


def test_triage_detects_crash_loop_as_top_incident():
    logs = [
        LogEvent(namespace="ml", pod="ranker-55d", message="Back-off restarting failed container"),
        LogEvent(namespace="ml", pod="ranker-55d", message="container exited with exit code 1"),
        LogEvent(namespace="ml", pod="ranker-55d", message="readiness probe failed"),
    ]

    result = triage_logs("ranker-api", "prod-like", logs)

    assert result.incident_class == "crash_loop"
    assert result.risk_score > 20
    assert result.findings[0].severity == "critical"
    assert "ReplicaSet" in result.runbook_steps[0]


def test_triage_returns_low_signal_when_no_rules_match():
    logs = [LogEvent(message="request completed successfully", pod="api-1")]

    result = triage_logs("api", "dev", logs)

    assert result.incident_class == "no_clear_anomaly"
    assert result.risk_score == 0
    assert result.findings == []


def test_dependency_timeout_groups_multiple_patterns():
    logs = [
        LogEvent(namespace="ops", pod="worker-1", message="context deadline exceeded calling redis"),
        LogEvent(namespace="ops", pod="worker-2", message="upstream model-service unavailable"),
    ]

    result = triage_logs("batch-worker", "staging", logs)

    assert result.incident_class == "dependency_timeout"
    assert result.metrics["pods"] == ["worker-1", "worker-2"]
    assert result.findings[0].evidence_count == 2
