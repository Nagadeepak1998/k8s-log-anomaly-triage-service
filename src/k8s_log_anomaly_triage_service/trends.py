from __future__ import annotations

from collections import Counter, defaultdict

from .models import (
    DeploymentTrendManifest,
    DeploymentTrendResponse,
    DeploymentTrendResult,
    OwnerRoute,
)
from .rules import triage_logs


def review_deployment_trends(manifest: DeploymentTrendManifest) -> DeploymentTrendResponse:
    deployments = []
    for deployment in sorted(manifest.deployments, key=lambda item: item.deployed_at):
        triage = triage_logs(deployment.service, deployment.environment, deployment.logs)
        deployments.append(
            DeploymentTrendResult(
                deployment_id=deployment.deployment_id,
                deployed_at=deployment.deployed_at,
                service=deployment.service,
                environment=deployment.environment,
                owner=deployment.owner or manifest.default_owner or "unowned",
                risk_score=triage.risk_score,
                incident_class=triage.incident_class,
            )
        )

    anomalous = [item for item in deployments if item.incident_class != "no_clear_anomaly"]
    class_counts = Counter(item.incident_class for item in anomalous)
    recurring = sorted(name for name, count in class_counts.items() if count > 1)
    grouped = defaultdict(list)
    for item in anomalous:
        grouped[item.owner].append(item)
    routes = [
        OwnerRoute(
            owner=owner,
            services=sorted({item.service for item in items}),
            affected_deployments=len(items),
            highest_risk_score=max(item.risk_score for item in items),
            incident_classes=sorted({item.incident_class for item in items}),
        )
        for owner, items in sorted(grouped.items())
    ]
    unowned = sum(item.owner == "unowned" for item in anomalous)
    status = "page" if recurring or unowned else "watch" if anomalous else "pass"
    actions = ["Route each anomaly group to its workload owner with deployment evidence."]
    if recurring:
        actions.append(
            f"Investigate recurring {', '.join(recurring)} across deployment boundaries."
        )
    if unowned:
        actions.append("Assign workload ownership before the next deployment proceeds.")
    return DeploymentTrendResponse(
        review_id=manifest.review_id,
        status=status,
        summary=(
            f"{manifest.review_id} status={status}: reviewed {len(deployments)} deployment(s), "
            f"found {len(anomalous)} anomalous and {unowned} unowned."
        ),
        reviewed_deployments=len(deployments),
        anomalous_deployments=len(anomalous),
        unowned_deployments=unowned,
        recurring_incident_classes=recurring,
        deployments=deployments,
        owner_routes=routes,
        recommended_actions=actions,
    )
