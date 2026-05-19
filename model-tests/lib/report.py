from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lib.runner import RunResult


def result_to_dict(result: RunResult) -> dict[str, Any]:
    return {
        "fixture_id": result.fixture_id,
        "task": result.task,
        "model": result.model,
        "models": result.models,
        "notes": result.notes,
        "status": result.status,
        "error": result.error,
        "total_latency_ms": result.total_latency_ms,
        "usage": result.usage_totals,
        "cost_usd": result.total_cost_usd,
        "calls": [
            {
                "subtask": c.subtask,
                "model": c.model,
                "output": c.output,
                "usage": c.usage,
                "cost_usd": c.cost_usd,
                "latency_ms": c.latency_ms,
                "status": c.status,
                "error": c.error,
            }
            for c in result.calls
        ],
    }


def write_run_outputs(out_dir: Path, task: str, results: list[RunResult], meta: dict[str, Any]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    run_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task": task,
        "meta": meta,
        "results": [result_to_dict(r) for r in results],
    }
    json_path = out_dir / "run.json"
    json_path.write_text(json.dumps(run_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    _write_summary_md(out_dir / "summary.md", task, results, meta)
    _write_summary_csv(out_dir / "summary.csv", results)
    return json_path


def _model_label(result: RunResult) -> str:
    if result.models:
        return f"corr={result.models.get('correction')} chat={result.models.get('chat')}"
    return result.model or "?"


def _write_summary_md(out_path: Path, task: str, results: list[RunResult], meta: dict[str, Any]) -> None:
    lines: list[str] = [
        "# Model comparison summary",
        "",
        f"- **Task:** `{task}`",
        f"- **Generated:** {meta.get('generated_at', '')}",
        f"- **Fixtures:** {meta.get('fixtures_path', '')}",
        "",
        "## Cost by model configuration",
        "",
        "| Model(s) | Calls | Total cost (USD) | Avg latency (ms) | Errors |",
        "|----------|-------|------------------|------------------|--------|",
    ]

    by_model: dict[str, list[RunResult]] = defaultdict(list)
    for r in results:
        by_model[_model_label(r)].append(r)

    for label, group in sorted(by_model.items()):
        costs = [r.total_cost_usd for r in group if r.total_cost_usd is not None]
        total_cost = sum(costs) if costs else None
        avg_lat = sum(r.total_latency_ms for r in group) / len(group) if group else 0
        errors = sum(1 for r in group if r.status != "ok")
        cost_str = f"{total_cost:.6f}" if total_cost is not None else "n/a"
        lines.append(f"| `{label}` | {len(group)} | {cost_str} | {avg_lat:.0f} | {errors} |")

    if results:
        avg_turn_costs = [
            r.total_cost_usd for r in results if r.total_cost_usd is not None and r.task == "turn"
        ]
        if not avg_turn_costs:
            avg_turn_costs = [r.total_cost_usd for r in results if r.total_cost_usd is not None]
        if avg_turn_costs:
            per_1k = (sum(avg_turn_costs) / len(avg_turn_costs)) * 1000
            lines.extend(
                [
                    "",
                    f"**Estimated cost per 1,000 runs (this fixture set):** ${per_1k:.4f}",
                ]
            )

    lines.extend(["", "## Results by fixture", ""])

    by_fixture: dict[str, list[RunResult]] = defaultdict(list)
    for r in results:
        by_fixture[r.fixture_id].append(r)

    for fixture_id, group in sorted(by_fixture.items()):
        notes = next((g.notes for g in group if g.notes), None)
        lines.append(f"### `{fixture_id}`")
        if notes:
            lines.append(f"*{notes}*")
        lines.append("")
        for r in group:
            lines.append(f"#### `{_model_label(r)}`")
            if r.error:
                lines.append(f"- **Error:** {r.error}")
            lines.append(f"- **Cost:** {r.total_cost_usd}")
            lines.append(f"- **Latency:** {r.total_latency_ms} ms")
            for call in r.calls:
                lines.append(f"- **{call.subtask}** (`{call.model}`): `{json.dumps(call.output, ensure_ascii=False)}`")
            lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def _write_summary_csv(out_path: Path, results: list[RunResult]) -> None:
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "fixture_id",
                "task",
                "model",
                "correction_model",
                "chat_model",
                "status",
                "cost_usd",
                "latency_ms",
                "prompt_tokens",
                "completion_tokens",
                "reasoning_tokens",
                "output_json",
            ]
        )
        for r in results:
            output = {c.subtask: c.output for c in r.calls}
            writer.writerow(
                [
                    r.fixture_id,
                    r.task,
                    r.model or "",
                    (r.models or {}).get("correction", ""),
                    (r.models or {}).get("chat", ""),
                    r.status,
                    r.total_cost_usd if r.total_cost_usd is not None else "",
                    r.total_latency_ms,
                    r.usage_totals.get("prompt_tokens", 0),
                    r.usage_totals.get("completion_tokens", 0),
                    r.usage_totals.get("reasoning_tokens", 0),
                    json.dumps(output, ensure_ascii=False),
                ]
            )
