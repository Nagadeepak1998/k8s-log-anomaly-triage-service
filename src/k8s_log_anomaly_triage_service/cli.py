from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .models import DeploymentTrendManifest, LogEvent, ReplayManifest
from .replay import review_replay
from .reporting import render_deployment_trend_markdown, render_replay_markdown
from .rules import triage_logs
from .trends import review_deployment_trends


def load_logs(path: Path) -> list[LogEvent]:
    payload = json.loads(path.read_text())
    if isinstance(payload, dict) and "logs" in payload:
        payload = payload["logs"]
    if not isinstance(payload, list):
        raise ValueError("input must be a JSON list or an object with a logs array")
    return [LogEvent.model_validate(item) for item in payload]


def load_replay_manifest(path: Path) -> ReplayManifest:
    return ReplayManifest.model_validate_json(path.read_text())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Triage Kubernetes log anomalies from JSON input.")
    parser.add_argument("input", type=Path, help="Path to JSON log events.")
    parser.add_argument("--service", default="unknown-service")
    parser.add_argument("--environment", default="staging")
    parser.add_argument(
        "--fail-at",
        type=float,
        default=80.0,
        help="Exit non-zero when risk score is greater than or equal to this threshold.",
    )
    return parser


def build_replay_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Review a multi-window Kubernetes log replay manifest."
    )
    parser.add_argument("command", choices=["replay"])
    parser.add_argument("input", type=Path, help="Path to replay manifest JSON.")
    parser.add_argument("--page-at", type=float, default=90.0)
    parser.add_argument("--watch-at", type=float, default=50.0)
    parser.add_argument("--fail-at", choices=["watch", "page"], default="page")
    parser.add_argument("--markdown", type=Path, help="Optional Markdown report output path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "replay":
        return run_replay(argv)
    if argv and argv[0] == "trends":
        return run_trends(argv)

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        logs = load_logs(args.input)
        result = triage_logs(args.service, args.environment, logs)
    except Exception as exc:  # pragma: no cover - argparse-facing error path
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(result.model_dump_json(indent=2))
    return 1 if result.risk_score >= args.fail_at else 0


def run_replay(argv: list[str]) -> int:
    parser = build_replay_parser()
    args = parser.parse_args(argv)
    try:
        manifest = load_replay_manifest(args.input)
        result = review_replay(manifest, page_at=args.page_at, watch_at=args.watch_at)
        if args.markdown:
            args.markdown.parent.mkdir(parents=True, exist_ok=True)
            args.markdown.write_text(render_replay_markdown(result))
    except Exception as exc:  # pragma: no cover - argparse-facing error path
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(result.model_dump_json(indent=2))
    if args.fail_at == "watch" and result.status in {"watch", "page"}:
        return 1
    return 1 if result.status == "page" else 0


def run_trends(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Review anomaly trends across deployments.")
    parser.add_argument("command", choices=["trends"])
    parser.add_argument("input", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args(argv)
    try:
        manifest = DeploymentTrendManifest.model_validate_json(args.input.read_text())
        result = review_deployment_trends(manifest)
        if args.markdown:
            args.markdown.parent.mkdir(parents=True, exist_ok=True)
            args.markdown.write_text(render_deployment_trend_markdown(result))
    except Exception as exc:  # pragma: no cover - argparse-facing error path
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(result.model_dump_json(indent=2))
    return 1 if result.status == "page" else 0


if __name__ == "__main__":
    raise SystemExit(main())
