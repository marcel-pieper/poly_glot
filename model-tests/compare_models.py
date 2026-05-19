#!/usr/bin/env python3
"""
Compare OpenAI models on Polyglot prompts with token usage and cost estimates.

Run from model-tests (dedicated venv — see README):

  cd model-tests
  .\\scripts\\setup.ps1
  .\\scripts\\run.ps1 --task correction
  python ../model-tests/compare_models.py --task turn --pair correction=gpt-4.1,chat=gpt-5.4-mini
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT.parent / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT))

from lib.report import write_run_outputs  # noqa: E402
from lib.runner import (  # noqa: E402
    TASK_DEFAULT_FIXTURES,
    TASK_RUNNERS,
    ModelRunner,
    RunResult,
)


def load_api_key() -> str:
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if key:
        return key
    env_file = BACKEND / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("OPENAI_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit(
        "OPENAI_API_KEY not set. Export it or add it to backend/.env"
    )


def load_yaml(path: Path) -> list[dict] | dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_fixtures(path: Path, limit: int | None) -> list[dict]:
    data = load_yaml(path)
    if not isinstance(data, list):
        raise SystemExit(f"Fixtures file must be a YAML list: {path}")
    fixtures = [f for f in data if isinstance(f, dict) and f.get("id")]
    if limit is not None:
        fixtures = fixtures[:limit]
    return fixtures


def parse_models_arg(models_str: str) -> list[str]:
    return [m.strip() for m in models_str.split(",") if m.strip()]


def parse_pair_arg(pair_str: str) -> dict[str, str]:
    pair: dict[str, str] = {}
    for part in pair_str.split(","):
        part = part.strip()
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        pair[key.strip()] = value.strip()
    if "correction" not in pair or "chat" not in pair:
        raise SystemExit("--pair must include correction=MODEL and chat=MODEL")
    return pair


def load_default_models(task: str, models_path: Path) -> list[str] | list[dict[str, str]]:
    data = load_yaml(models_path)
    if task == "turn":
        pairs = data.get("turn_pairs") if isinstance(data, dict) else None
        if not pairs:
            raise SystemExit("No turn_pairs in models.yaml")
        return pairs
    models = data.get(task) if isinstance(data, dict) else None
    if not models:
        raise SystemExit(f"No models listed for task '{task}' in {models_path}")
    return models


def dry_run_plan(
    task: str,
    fixtures: list[dict],
    model_specs: list[str] | list[dict[str, str]],
) -> None:
    print(f"Task: {task}")
    print(f"Fixtures: {len(fixtures)}")
    if task == "turn":
        print(f"Turn pairs: {len(model_specs)}")
        total_calls = len(fixtures) * len(model_specs) * 2
    else:
        print(f"Models: {len(model_specs)}")
        total_calls = len(fixtures) * len(model_specs)
    print(f"API calls: {total_calls}")
    for f in fixtures:
        print(f"  - {f['id']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare OpenAI models on Polyglot tasks.")
    parser.add_argument(
        "--task",
        required=True,
        choices=["correction", "chat_reply", "translation", "title", "turn"],
        help="Which production task to exercise",
    )
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=None,
        help="Fixture YAML path (default: model-tests/fixtures/<task>.yaml)",
    )
    parser.add_argument(
        "--models",
        type=str,
        default=None,
        help="Comma-separated model IDs (single-model tasks)",
    )
    parser.add_argument(
        "--pair",
        action="append",
        default=None,
        metavar="SPEC",
        help="For --task turn: correction=MODEL,chat=MODEL (repeat for multiple pairs)",
    )
    parser.add_argument(
        "--models-file",
        type=Path,
        default=ROOT / "models.yaml",
        help="Default models per task",
    )
    parser.add_argument(
        "--pricing",
        type=Path,
        default=ROOT / "pricing.yaml",
        help="Pricing table for cost estimates",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory (default: model-tests/output/<timestamp>)",
    )
    parser.add_argument("--limit", type=int, default=None, help="Run only first N fixtures")
    parser.add_argument("--delay-ms", type=int, default=0, help="Pause between API calls")
    parser.add_argument("--dry-run", action="store_true", help="Print plan without calling API")
    args = parser.parse_args()

    fixtures_path = args.fixtures or (ROOT / TASK_DEFAULT_FIXTURES[args.task])
    if not fixtures_path.is_absolute():
        fixtures_path = ROOT / fixtures_path
    fixtures = load_fixtures(fixtures_path, args.limit)

    if args.task == "turn":
        if args.pair:
            pairs = [parse_pair_arg(p) for p in args.pair]
        else:
            pairs = load_default_models("turn", args.models_file)
            if args.models:
                models = parse_models_arg(args.models)
                pairs = [{"correction": m, "chat": m} for m in models]
        model_specs: list[str] | list[dict[str, str]] = pairs
    else:
        if args.models:
            model_specs = parse_models_arg(args.models)
        else:
            model_specs = load_default_models(args.task, args.models_file)

    if args.dry_run:
        dry_run_plan(args.task, fixtures, model_specs)
        return

    api_key = load_api_key()
    runner = ModelRunner(api_key=api_key, pricing_path=args.pricing, delay_ms=args.delay_ms)

    results: list[RunResult] = []

    if args.task == "turn":
        for pair in model_specs:
            assert isinstance(pair, dict)
            for fixture in fixtures:
                results.append(
                    runner.run_turn(
                        correction_model=pair["correction"],
                        chat_model=pair["chat"],
                        fixture=fixture,
                    )
                )
                print(
                    f"[{fixture['id']}] turn corr={pair['correction']} chat={pair['chat']} "
                    f"cost={results[-1].total_cost_usd} status={results[-1].status}"
                )
    else:
        run_fn = TASK_RUNNERS[args.task]
        for model in model_specs:
            assert isinstance(model, str)
            for fixture in fixtures:
                results.append(run_fn(runner, model, fixture))
                print(
                    f"[{fixture['id']}] {args.task} model={model} "
                    f"cost={results[-1].total_cost_usd} status={results[-1].status}"
                )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = args.out or (ROOT / "output" / f"{args.task}_{timestamp}")
    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fixtures_path": str(fixtures_path),
        "models": model_specs,
        "pricing_path": str(args.pricing),
    }
    json_path = write_run_outputs(out_dir, args.task, results, meta)
    print(f"\nWrote {json_path}")
    print(f"Summary: {out_dir / 'summary.md'}")


if __name__ == "__main__":
    main()
