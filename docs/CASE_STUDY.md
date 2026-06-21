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

The service exposes the same logic through a FastAPI endpoint and a CLI so it can run in CI, a support workflow, or an internal platform tool.

## Production-Shaped Details

- Typed request and response contracts with Pydantic.
- Prometheus counters and histograms for request volume, risk scores, and HTTP latency.
- Structured JSON logs for triage outcomes without storing secrets.
- Kubernetes manifests with probes, resource limits, Prometheus scrape annotations, and a restricted container security context.
- Terraform skeleton for ECR and CloudWatch log resources.
- Tests covering rule scoring, low-signal logs, API behavior, metrics, and CLI failure thresholds.
- CI workflow stored under `docs/github-actions/ci.yml` because the current GitHub token may not have workflow scope.

## Tradeoffs

The scoring is rule-based instead of model-based. That is intentional for a one-run portfolio project: the behavior is inspectable, deterministic, testable, and safe to run without vendor credentials or private data. A later extension could add embeddings or LLM-generated summaries behind the deterministic classifier.

## What It Demonstrates

- Incident response thinking for Kubernetes workloads.
- API and CLI parity.
- Observability-first service design.
- Deployment hygiene for containers and Kubernetes.
- Practical MLOps/platform engineering credibility without fake production claims.
