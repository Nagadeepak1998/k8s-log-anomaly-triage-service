from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .models import LogEvent
from .rules import triage_logs


def load_logs(path: Path) -> list[LogEvent]:
    payload = json.loads(path.read_text())
    if isinstance(payload, dict) and "logs" in payload:
        payload = payload["logs"]
    if not isinstance(payload, list):
        raise ValueError("input must be a JSON list or an object with a logs array")
    return [LogEvent.model_validate(item) for item in payload]


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


def main(argv: list[str] | None = None) -> int:
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


if __name__ == "__main__":
    raise SystemExit(main())
