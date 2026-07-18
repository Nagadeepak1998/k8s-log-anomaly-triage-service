from __future__ import annotations

from dataclasses import dataclass
import re

from .models import Finding, LogEvent, Severity, TriageResponse


@dataclass(frozen=True)
class Rule:
    category: str
    severity: Severity
    weight: int
    patterns: tuple[str, ...]
    recommendation: str


RULES: tuple[Rule, ...] = (
    Rule(
        category="crash_loop",
        severity="critical",
        weight=28,
        patterns=(r"crashloopbackoff", r"back-off restarting failed container", r"exit code 1"),
        recommendation="Check recent deployment diff, container command, config mounts, and last terminated state.",
    ),
    Rule(
        category="memory_pressure",
        severity="high",
        weight=22,
        patterns=(r"oomkilled", r"out of memory", r"memory cgroup out of memory"),
        recommendation="Compare memory request/limit to working set and inspect heap or batch-size changes.",
    ),
    Rule(
        category="dependency_timeout",
        severity="high",
        weight=18,
        patterns=(
            r"timeout",
            r"context deadline exceeded",
            r"connection refused",
            r"upstream .* unavailable",
        ),
        recommendation="Validate dependency health, service discovery, network policy, and retry budget.",
    ),
    Rule(
        category="image_pull",
        severity="high",
        weight=18,
        patterns=(r"imagepullbackoff", r"errimagepull", r"unauthorized: authentication required"),
        recommendation="Verify image tag, registry credentials, pull secret, and rollout image digest.",
    ),
    Rule(
        category="auth_or_secret",
        severity="medium",
        weight=13,
        patterns=(r"permission denied", r"forbidden", r"invalid api key", r"secret .* not found"),
        recommendation="Check service account permissions, secret references, and rotated credentials.",
    ),
    Rule(
        category="data_or_schema",
        severity="medium",
        weight=11,
        patterns=(
            r"schema mismatch",
            r"missing column",
            r"deserialization error",
            r"invalid payload",
        ),
        recommendation="Compare producer and consumer versions and validate contract changes before rollback.",
    ),
)

RUNBOOK_BY_CATEGORY: dict[str, list[str]] = {
    "crash_loop": [
        "Freeze the rollout and compare the failing ReplicaSet with the previous stable ReplicaSet.",
        "Inspect `kubectl describe pod` events and the previous container logs for the first failing stack line.",
        "Roll back only after confirming the issue is tied to the new image, config, or startup command.",
    ],
    "memory_pressure": [
        "Check recent traffic and batch-size changes before raising limits.",
        "Compare memory usage to requests and limits in the current deployment manifest.",
        "Capture a heap or allocation profile if the service restarts repeatedly under steady load.",
    ],
    "dependency_timeout": [
        "Check dependency SLO dashboards and recent deploys for the upstream service.",
        "Confirm DNS, service endpoints, and network policy from inside a pod in the same namespace.",
        "Reduce retry amplification if downstream errors are causing queue or thread exhaustion.",
    ],
    "image_pull": [
        "Confirm the deployed image tag or digest exists in the registry.",
        "Validate imagePullSecrets and registry token expiry.",
        "Redeploy the last known-good image only after the registry or tag mismatch is confirmed.",
    ],
}


def normalize_message(message: str) -> str:
    return re.sub(r"\s+", " ", message.strip().lower())


def triage_logs(service: str, environment: str, logs: list[LogEvent]) -> TriageResponse:
    normalized = [(event, normalize_message(event.message)) for event in logs]
    findings: list[Finding] = []

    for rule in RULES:
        matches: list[LogEvent] = []
        for event, message in normalized:
            if any(re.search(pattern, message) for pattern in rule.patterns):
                matches.append(event)

        if matches:
            findings.append(
                Finding(
                    category=rule.category,
                    severity=rule.severity,
                    score=float(rule.weight * len(matches)),
                    evidence_count=len(matches),
                    example=matches[0].message,
                    recommendation=rule.recommendation,
                )
            )

    findings.sort(key=lambda item: item.score, reverse=True)
    raw_score = sum(item.score for item in findings)
    risk_score = min(100.0, round(raw_score / max(len(logs), 1) + raw_score * 0.35, 2))
    incident_class = findings[0].category if findings else "no_clear_anomaly"
    summary = build_summary(service, environment, risk_score, incident_class, findings)
    runbook_steps = build_runbook(incident_class, findings)

    return TriageResponse(
        service=service,
        environment=environment,
        risk_score=risk_score,
        incident_class=incident_class,
        summary=summary,
        findings=findings,
        runbook_steps=runbook_steps,
        metrics={
            "log_events": len(logs),
            "findings": len(findings),
            "namespaces": sorted({event.namespace for event in logs}),
            "pods": sorted({event.pod for event in logs}),
        },
    )


def build_summary(
    service: str,
    environment: str,
    risk_score: float,
    incident_class: str,
    findings: list[Finding],
) -> str:
    if not findings:
        return f"{service} in {environment} has no high-signal anomaly in the submitted logs."

    top = findings[0]
    return (
        f"{service} in {environment} is most consistent with {incident_class}; "
        f"risk score {risk_score:.2f}/100 from {top.evidence_count} matching log event(s)."
    )


def build_runbook(incident_class: str, findings: list[Finding]) -> list[str]:
    steps = RUNBOOK_BY_CATEGORY.get(
        incident_class,
        [
            "Group errors by pod and deployment revision.",
            "Compare current symptoms with the latest deploy, config, and dependency changes.",
            "Escalate with log examples, affected namespace, pod names, and first-seen timestamp.",
        ],
    )
    if findings:
        steps = [*steps, f"Attach evidence for `{findings[0].category}`: {findings[0].example}"]
    return steps
