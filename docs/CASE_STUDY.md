# Case Study: Kubernetes Log Anomaly Triage Service

## Problem

Platform and MLOps teams often receive noisy Kubernetes logs during an incident. The first useful question is not whether an LLM can summarize the text, but whether the service can quickly group symptoms into an actionable incident class with evidence and safe next steps.

## Approach

This project implements a deterministic triage layer for common Kubernetes failure modes:

- crash loops
- memory pressure
- dependency timeouts
- image pull failures
- authorization or secret issues
- data and schema mismatches

The service exposes the same logic through a FastAPI endpoint and a CLI so it can run in CI, a support workflow, or an internal platform tool. It includes a replay reviewer for incident windows and a deployment-trend reviewer that detects repeated failure classes across releases, then groups evidence by accountable workload owner.

## Production-Shaped Details

- Typed request and response contracts with Pydantic.
- Prometheus counters and histograms for request volume, risk scores, and HTTP latency.
- Replay review metrics for incident windows and page/watch/pass outcomes.
- Deployment-trend metrics and owner-routed Markdown review evidence.
- Structured JSON logs for triage outcomes without storing secrets.
- Kubernetes manifests with probes, resource limits, Prometheus scrape annotations, and a restricted container security context.
- Terraform skeleton for ECR and CloudWatch log resources.
- Tests covering rule scoring, low-signal logs, API behavior, replay review behavior, metrics, Markdown reports, and CLI failure thresholds.
- CI workflow stored under `docs/github-actions/ci.yml` because the current GitHub token may not have workflow scope.

## Recruiter-Readable Upgrade

The July 8 upgrade added a deterministic incident replay gate:

- `examples/replay_manifest.json` models a clean baseline, dependency warnings, and a final crash-loop page window.
- `k8s-log-triage replay ...` returns `pass`, `watch`, or `page` and can write `reports/replay_review.md`.
- `POST /replay` provides API parity for the same review.
- `k8s_log_replay_reviews_total{status,dominant_incident_class}` makes replay outcomes observable.

This turns the repo from a single-batch classifier into a small production-support workflow: responders can review whether symptoms are recurring, identify the dominant failure class, and hand off a concise report.

The July 18 upgrade adds `k8s-log-triage trends` and `POST /deployments/trends`. A deterministic deployment history distinguishes a clean baseline from recurring dependency timeouts and a separate memory-pressure event, then routes affected services to declared on-call owners. Missing ownership or a recurring incident class creates a page decision, making accountability part of release readiness.

## Tradeoffs

The scoring is rule-based instead of model-based. That is intentional for a one-run portfolio project: the behavior is inspectable, deterministic, testable, and safe to run without vendor credentials or private data. A later extension could add embeddings or LLM-generated summaries behind the deterministic classifier.

## What It Demonstrates

- Incident response thinking for Kubernetes workloads.
- API and CLI parity.
- Observability-first service design.
- Deployment hygiene for containers and Kubernetes.
- Practical MLOps/platform engineering credibility without fake production claims.
