import json

from k8s_log_anomaly_triage_service.models import ReplayManifest
from k8s_log_anomaly_triage_service.replay import review_replay
from k8s_log_anomaly_triage_service.reporting import render_replay_markdown


def test_replay_review_pages_on_high_risk_window():
    manifest = ReplayManifest.model_validate(
        {
            "incident_id": "incident-123",
            "owner": "platform-oncall",
            "windows": [
                {
                    "window_id": "baseline",
                    "service": "api",
                    "environment": "staging",
                    "logs": [{"pod": "api-1", "message": "request completed successfully"}],
                },
                {
                    "window_id": "crashloop",
                    "service": "api",
                    "environment": "staging",
                    "logs": [
                        {"pod": "api-1", "message": "CrashLoopBackOff"},
                        {"pod": "api-1", "message": "Back-off restarting failed container"},
                        {"pod": "api-1", "message": "exit code 1"},
                    ],
                },
            ],
        }
    )

    review = review_replay(manifest)

    assert review.status == "page"
    assert review.reviewed_windows == 2
    assert review.highest_risk_score >= 45
    assert review.dominant_incident_class == "crash_loop"
    assert "Page the platform owner" in review.recommended_actions[0]


def test_replay_markdown_renders_window_table():
    manifest = ReplayManifest.model_validate_json(
        json.dumps(
            {
                "incident_id": "incident-123",
                "owner": "platform-oncall",
                "windows": [
                    {
                        "window_id": "baseline",
                        "service": "api",
                        "environment": "staging",
                        "logs": [{"pod": "api-1", "message": "request completed successfully"}],
                    }
                ],
            }
        )
    )

    markdown = render_replay_markdown(review_replay(manifest))

    assert "# Kubernetes Log Replay Review: incident-123" in markdown
    assert "| baseline | api | staging | 0.00 | no_clear_anomaly | 0 |" in markdown
