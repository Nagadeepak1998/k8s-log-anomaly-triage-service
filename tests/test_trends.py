from k8s_log_anomaly_triage_service.models import DeploymentTrendManifest
from k8s_log_anomaly_triage_service.reporting import render_deployment_trend_markdown
from k8s_log_anomaly_triage_service.trends import review_deployment_trends


def test_trends_page_and_route_recurring_anomalies():
    manifest = DeploymentTrendManifest.model_validate(
        {
            "review_id": "review-1",
            "default_owner": "platform-oncall",
            "deployments": [
                {
                    "deployment_id": "api-1",
                    "deployed_at": "2026-07-01T00:00:00Z",
                    "service": "api",
                    "environment": "staging",
                    "logs": [{"message": "context deadline exceeded"}],
                },
                {
                    "deployment_id": "api-2",
                    "deployed_at": "2026-07-02T00:00:00Z",
                    "service": "api",
                    "environment": "staging",
                    "logs": [{"message": "upstream model unavailable"}],
                },
            ],
        }
    )
    result = review_deployment_trends(manifest)
    assert result.status == "page"
    assert result.recurring_incident_classes == ["dependency_timeout"]
    assert result.owner_routes[0].owner == "platform-oncall"
    assert result.owner_routes[0].affected_deployments == 2
    assert "platform-oncall" in render_deployment_trend_markdown(result)


def test_trends_page_when_anomalous_deployment_has_no_owner():
    manifest = DeploymentTrendManifest.model_validate(
        {
            "review_id": "review-2",
            "deployments": [
                {
                    "deployment_id": "worker-1",
                    "deployed_at": "2026-07-03T00:00:00Z",
                    "service": "worker",
                    "environment": "staging",
                    "logs": [{"message": "OOMKilled"}],
                }
            ],
        }
    )
    result = review_deployment_trends(manifest)
    assert result.status == "page"
    assert result.unowned_deployments == 1
    assert result.owner_routes[0].owner == "unowned"
    assert "Assign workload ownership" in result.recommended_actions[-1]
