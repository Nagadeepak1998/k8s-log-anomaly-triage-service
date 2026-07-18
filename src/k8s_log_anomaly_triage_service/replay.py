from __future__ import annotations

from collections import Counter

from .models import ReplayManifest, ReplayReviewResponse, ReplayWindowResult
from .rules import triage_logs


PAGE_THRESHOLD = 80.0
WATCH_THRESHOLD = 50.0
PAGE_INCIDENT_CLASSES = {"crash_loop", "image_pull"}


def review_replay(
    manifest: ReplayManifest,
    page_at: float = PAGE_THRESHOLD,
    watch_at: float = WATCH_THRESHOLD,
) -> ReplayReviewResponse:
    windows: list[ReplayWindowResult] = []

    for window in manifest.windows:
        triage = triage_logs(window.service, window.environment, window.logs)
        windows.append(
            ReplayWindowResult(
                window_id=window.window_id,
                service=window.service,
                environment=window.environment,
                risk_score=triage.risk_score,
                incident_class=triage.incident_class,
                findings=len(triage.findings),
                summary=triage.summary,
            )
        )

    class_counts = Counter(
        window.incident_class for window in windows if window.incident_class != "no_clear_anomaly"
    )
    highest_risk = max((window.risk_score for window in windows), default=0.0)
    page_windows = sum(1 for window in windows if is_page_window(window, page_at))
    recurring_classes = sorted(
        incident_class for incident_class, count in class_counts.items() if count > 1
    )
    dominant_class = dominant_incident_class(windows)

    if page_windows or recurring_classes:
        status = "page"
    elif highest_risk >= watch_at:
        status = "watch"
    else:
        status = "pass"

    return ReplayReviewResponse(
        incident_id=manifest.incident_id,
        owner=manifest.owner,
        status=status,
        summary=build_replay_summary(
            manifest.incident_id,
            status,
            len(windows),
            page_windows,
            highest_risk,
            dominant_class,
            recurring_classes,
        ),
        reviewed_windows=len(windows),
        page_windows=page_windows,
        highest_risk_score=highest_risk,
        dominant_incident_class=dominant_class,
        recurring_incident_classes=recurring_classes,
        windows=windows,
        recommended_actions=build_recommended_actions(status, dominant_class, recurring_classes),
    )


def build_replay_summary(
    incident_id: str,
    status: str,
    reviewed_windows: int,
    page_windows: int,
    highest_risk: float,
    dominant_class: str,
    recurring_classes: list[str],
) -> str:
    recurrence = (
        f" recurring classes: {', '.join(recurring_classes)}."
        if recurring_classes
        else " no recurring class detected."
    )
    return (
        f"{incident_id} replay status={status}: reviewed {reviewed_windows} window(s), "
        f"{page_windows} page-worthy window(s), highest risk {highest_risk:.2f}/100, "
        f"dominant class {dominant_class};{recurrence}"
    )


def is_page_window(window: ReplayWindowResult, page_at: float) -> bool:
    if window.risk_score >= page_at:
        return True
    return window.incident_class in PAGE_INCIDENT_CLASSES and window.risk_score >= 45


def dominant_incident_class(windows: list[ReplayWindowResult]) -> str:
    if not windows:
        return "no_clear_anomaly"
    return max(windows, key=lambda window: window.risk_score).incident_class


def build_recommended_actions(
    status: str,
    dominant_class: str,
    recurring_classes: list[str],
) -> list[str]:
    if status == "pass":
        return [
            "Keep the incident in observation and attach the replay summary to the ticket.",
            "Re-run replay if a new deploy, config change, or dependency incident lands.",
        ]

    actions = [
        "Page the platform owner with the highest-risk window, affected pods, and first-seen timestamp.",
        "Compare the replay windows against deploy, config, and dependency timelines.",
    ]
    if recurring_classes:
        actions.append(
            f"Treat repeated {', '.join(recurring_classes)} evidence as a pattern, not a single noisy log."
        )
    elif dominant_class != "no_clear_anomaly":
        actions.append(
            f"Start with the `{dominant_class}` runbook and confirm the newest failure window."
        )
    actions.append(
        "Document the decision, mitigations, and rollback criteria in the incident record."
    )
    return actions
