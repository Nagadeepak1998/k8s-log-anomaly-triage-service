from __future__ import annotations

from .models import ReplayReviewResponse


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
