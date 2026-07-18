from __future__ import annotations

from .models import DeploymentTrendResponse, ReplayReviewResponse


def render_replay_markdown(review: ReplayReviewResponse) -> str:
    lines = [
        f"# Kubernetes Log Replay Review: {review.incident_id}",
        "",
        f"- Owner: `{review.owner}`",
        f"- Status: `{review.status}`",
        f"- Reviewed windows: `{review.reviewed_windows}`",
        f"- Highest risk score: `{review.highest_risk_score:.2f}`",
        f"- Dominant incident class: `{review.dominant_incident_class}`",
        f"- Recurring classes: `{', '.join(review.recurring_incident_classes) or 'none'}`",
        "",
        "## Summary",
        "",
        review.summary,
        "",
        "## Window Results",
        "",
        "| Window | Service | Environment | Risk | Class | Findings |",
        "| --- | --- | --- | ---: | --- | ---: |",
    ]

    for window in review.windows:
        lines.append(
            "| "
            f"{window.window_id} | {window.service} | {window.environment} | "
            f"{window.risk_score:.2f} | {window.incident_class} | {window.findings} |"
        )

    lines.extend(["", "## Recommended Actions", ""])
    lines.extend(f"- {action}" for action in review.recommended_actions)
    lines.append("")
    return "\n".join(lines)


def render_deployment_trend_markdown(review: DeploymentTrendResponse) -> str:
    lines = [
        f"# Deployment Anomaly Trend Review: {review.review_id}",
        "",
        f"- Status: `{review.status}`",
        f"- Reviewed deployments: `{review.reviewed_deployments}`",
        f"- Anomalous deployments: `{review.anomalous_deployments}`",
        f"- Unowned deployments: `{review.unowned_deployments}`",
        f"- Recurring classes: `{', '.join(review.recurring_incident_classes) or 'none'}`",
        "",
        "## Deployment Results",
        "",
        "| Deployment | Service | Environment | Owner | Risk | Class |",
        "| --- | --- | --- | --- | ---: | --- |",
    ]
    for item in review.deployments:
        lines.append(
            f"| {item.deployment_id} | {item.service} | {item.environment} | "
            f"{item.owner} | {item.risk_score:.2f} | {item.incident_class} |"
        )
    lines.extend(["", "## Owner Routing", ""])
    for route in review.owner_routes:
        lines.append(
            f"- `{route.owner}`: {route.affected_deployments} deployment(s), "
            f"services {', '.join(route.services)}, classes {', '.join(route.incident_classes)}"
        )
    lines.extend(["", "## Recommended Actions", ""])
    lines.extend(f"- {action}" for action in review.recommended_actions)
    lines.append("")
    return "\n".join(lines)
