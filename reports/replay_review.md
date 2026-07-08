# Kubernetes Log Replay Review: embedding-api-2026-07-08-replay

- Owner: `ml-platform-oncall`
- Status: `page`
- Reviewed windows: `3`
- Highest risk score: `57.40`
- Dominant incident class: `crash_loop`
- Recurring classes: `none`

## Summary

embedding-api-2026-07-08-replay replay status=page: reviewed 3 window(s), 1 page-worthy window(s), highest risk 57.40/100, dominant class crash_loop; no recurring class detected.

## Window Results

| Window | Service | Environment | Risk | Class | Findings |
| --- | --- | --- | ---: | --- | ---: |
| 00-baseline | embedding-api | staging | 0.00 | no_clear_anomaly | 0 |
| 01-dependency-warnings | embedding-api | staging | 30.60 | dependency_timeout | 1 |
| 02-crashloop-page | embedding-api | staging | 57.40 | crash_loop | 1 |

## Recommended Actions

- Page the platform owner with the highest-risk window, affected pods, and first-seen timestamp.
- Compare the replay windows against deploy, config, and dependency timelines.
- Start with the `crash_loop` runbook and confirm the newest failure window.
- Document the decision, mitigations, and rollback criteria in the incident record.
