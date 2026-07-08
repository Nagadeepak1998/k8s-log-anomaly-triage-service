# k8s-log-anomaly-triage-service

Production-shaped Kubernetes log anomaly triage service for platform, SRE, DevOps, and MLOps workflows.

The project scores Kubernetes log batches, identifies a likely incident class, replays multi-window incidents into Markdown triage reports, exposes Prometheus metrics, and ships with tests, Docker, Kubernetes manifests, a Terraform skeleton, and CI documentation.

## Business Problem

During an incident, platform teams need to turn noisy pod logs into a short, reliable first diagnosis. This service gives responders a deterministic triage result they can use before escalating, rolling back, or opening a deeper investigation.

## Architecture

```mermaid
flowchart LR
    A[Kubernetes pod logs JSON] --> B[CLI: k8s-log-triage]
    A --> C[FastAPI /triage]
    B --> D[Deterministic anomaly rules]
    C --> D
    D --> E[Incident class + risk score]
    D --> F[Runbook steps]
    A --> L[Replay manifest]
    L --> M[CLI/API replay review]
    M --> N[Markdown incident report]
    C --> G[/metrics Prometheus]
    C --> H[Structured JSON logs]
    C --> I[Docker image]
    I --> J[Kubernetes manifests]
    I --> K[Terraform ECR/CloudWatch skeleton]
```

## What It Detects

- `crash_loop`
- `memory_pressure`
- `dependency_timeout`
- `image_pull`
- `auth_or_secret`
- `data_or_schema`
- `no_clear_anomaly`

## Local Setup

```bash
make setup
```

## Run Tests and Lint

```bash
make test
make lint
```

## CLI Usage

```bash
k8s-log-triage examples/crashloop_logs.json \
  --service embedding-api \
  --environment staging \
  --fail-at 90
```

The CLI returns non-zero when the risk score is greater than or equal to `--fail-at`, which makes it useful as a CI or release-gate check.

## Replay Review

The replay mode reviews multiple dated log windows and writes an incident-ready Markdown report:

```bash
make replay-report
```

Direct CLI usage:

```bash
k8s-log-triage replay examples/replay_manifest.json \
  --markdown reports/replay_review.md
```

The sample replay intentionally returns `page` because the final window reproduces a crash loop. `make replay-report` treats that non-zero CLI result as expected and leaves the report at `reports/replay_review.md`.

## Run the API Locally

```bash
make run
```

Health check:

```bash
curl http://localhost:8000/health
```

Triage request:

```bash
curl -X POST http://localhost:8000/triage \
  -H "Content-Type: application/json" \
  -d @<(jq -n --slurpfile logs examples/crashloop_logs.json '{service:"embedding-api", environment:"staging", logs:$logs[0]}')
```

Replay request:

```bash
curl -X POST http://localhost:8000/replay \
  -H "Content-Type: application/json" \
  -d @examples/replay_manifest.json
```

Prometheus metrics:

```bash
curl http://localhost:8000/metrics
```

## Docker Usage

```bash
docker build -t k8s-log-anomaly-triage-service:local .
docker run --rm -p 8000:8000 k8s-log-anomaly-triage-service:local
```

Docker Compose:

```bash
docker compose up --build
```

## Kubernetes Deployment

Update the image in `infra/k8s/deployment.yaml`, then apply:

```bash
kubectl apply -k infra/k8s
kubectl rollout status deployment/k8s-log-anomaly-triage
kubectl port-forward service/k8s-log-anomaly-triage 8000:80
```

The manifest includes readiness and liveness probes, resource requests and limits, Prometheus scrape annotations, and a restrictive security context.

## Terraform Notes

`infra/terraform` is a small cloud skeleton for an ECR repository and CloudWatch log group:

```bash
cd infra/terraform
terraform init
terraform plan
```

Local development does not require AWS credentials.

## CI/CD

The CI workflow is stored at `docs/github-actions/ci.yml`.

It runs install, lint, tests, a CLI smoke check, and Docker build. It is not placed under `.github/workflows` in this repo because the current GitHub token may not have `workflow` scope.

If you want to activate it as a live GitHub Actions workflow, run:

```bash
gh auth refresh -h github.com -s workflow
mkdir -p .github/workflows
cp docs/github-actions/ci.yml .github/workflows/ci.yml
git add .github/workflows/ci.yml
git commit -m "Add GitHub Actions CI workflow"
git push origin main
```

## Observability

- `/metrics` exposes Prometheus-compatible counters and histograms.
- Replay reviews emit `k8s_log_replay_reviews_total{status,dominant_incident_class}`.
- Structured JSON logs include service, environment, incident class, risk score, and log event count.
- Raw credentials are not required and no secrets are stored in the repository.

## Security Basics

- No hardcoded secrets.
- Non-root Docker runtime user.
- Kubernetes container security context drops Linux capabilities and disables privilege escalation.
- Read-only Docker Compose runtime.
- Deterministic local examples only; no private employer data.

## What This Demonstrates

**DevOps and SRE**

- Kubernetes incident triage thinking.
- Multi-window replay review for recurring failure patterns.
- Docker and Docker Compose runtime.
- Kubernetes manifests with health probes, resources, metrics annotations, and security context.
- Terraform skeleton for cloud deployment support.

**MLOps and AI Platform**

- Production support workflow for model-serving and platform services.
- Deterministic anomaly classification suitable for guardrails before adding LLM summarization.
- CLI/API parity for CI and internal tooling.

**Software Engineering**

- Typed FastAPI contracts.
- Unit and API tests.
- Prometheus metrics and structured logs.
- Recruiter-readable documentation and case study.

## Limitations

- The analyzer is deterministic and rule-based, not a trained anomaly model.
- It expects structured JSON log events rather than directly tailing cluster logs.
- It is a portfolio project, not a claim of live production deployment.

See [docs/CASE_STUDY.md](docs/CASE_STUDY.md) for the portfolio case study.
