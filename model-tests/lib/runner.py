from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable

from openai import OpenAI

from lib.messages import (
    chat_reply_messages,
    correction_messages,
    title_messages,
    translation_messages,
)
from lib.pricing import estimate_cost_usd, load_pricing, usage_dict


@dataclass
class CallResult:
    subtask: str
    model: str
    output: dict[str, Any]
    usage: dict[str, int]
    cost_usd: float | None
    latency_ms: int
    status: str
    error: str | None = None


@dataclass
class RunResult:
    fixture_id: str
    task: str
    model: str | None
    models: dict[str, str] | None
    notes: str | None
    calls: list[CallResult] = field(default_factory=list)
    status: str = "ok"
    error: str | None = None

    @property
    def total_cost_usd(self) -> float | None:
        if not self.calls:
            return None
        costs = [c.cost_usd for c in self.calls]
        if any(c is None for c in costs):
            return None
        return sum(costs)

    @property
    def total_latency_ms(self) -> int:
        return sum(c.latency_ms for c in self.calls)

    @property
    def usage_totals(self) -> dict[str, int]:
        totals = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "reasoning_tokens": 0}
        for call in self.calls:
            for key in totals:
                totals[key] += call.usage.get(key, 0)
        return totals


class ModelRunner:
    def __init__(self, api_key: str, pricing_path: Any = None, delay_ms: int = 0) -> None:
        self.client = OpenAI(api_key=api_key)
        self.pricing = load_pricing(pricing_path)
        self.delay_ms = delay_ms

    def _sleep(self) -> None:
        if self.delay_ms > 0:
            time.sleep(self.delay_ms / 1000.0)

    def _call_json(self, model: str, messages: list[dict], subtask: str) -> CallResult:
        self._sleep()
        started = time.perf_counter()
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
            )
            latency_ms = int((time.perf_counter() - started) * 1000)
            raw = response.choices[0].message.content or "{}"
            usage = usage_dict(response.usage)
            cost = estimate_cost_usd(model, usage, self.pricing)
            return CallResult(
                subtask=subtask,
                model=model,
                output=json.loads(raw),
                usage=usage,
                cost_usd=cost,
                latency_ms=latency_ms,
                status="ok",
            )
        except Exception as exc:
            latency_ms = int((time.perf_counter() - started) * 1000)
            return CallResult(
                subtask=subtask,
                model=model,
                output={},
                usage=usage_dict(None),
                cost_usd=None,
                latency_ms=latency_ms,
                status="error",
                error=str(exc),
            )

    def run_correction(self, model: str, fixture: dict) -> RunResult:
        messages = correction_messages(
            fixture["message_to_correct"],
            fixture.get("prior_exchange") or [],
            fixture.get("target_language"),
            fixture.get("native_language"),
        )
        call = self._call_json(model, messages, "correction")
        return RunResult(
            fixture_id=fixture["id"],
            task="correction",
            model=model,
            models=None,
            notes=fixture.get("notes"),
            calls=[call],
            status=call.status,
            error=call.error,
        )

    def run_chat_reply(self, model: str, fixture: dict) -> RunResult:
        messages = chat_reply_messages(
            fixture.get("history") or [],
            fixture.get("target_language"),
            fixture.get("native_language"),
        )
        call = self._call_json(model, messages, "chat_reply")
        return RunResult(
            fixture_id=fixture["id"],
            task="chat_reply",
            model=model,
            models=None,
            notes=fixture.get("notes"),
            calls=[call],
            status=call.status,
            error=call.error,
        )

    def run_translation(self, model: str, fixture: dict) -> RunResult:
        messages = translation_messages(fixture["text"], fixture.get("to_language"))
        call = self._call_json(model, messages, "translation")
        return RunResult(
            fixture_id=fixture["id"],
            task="translation",
            model=model,
            models=None,
            notes=fixture.get("notes"),
            calls=[call],
            status=call.status,
            error=call.error,
        )

    def run_title(self, model: str, fixture: dict) -> RunResult:
        messages = title_messages(fixture.get("conversation_lines") or [])
        call = self._call_json(model, messages, "title")
        return RunResult(
            fixture_id=fixture["id"],
            task="title",
            model=model,
            models=None,
            notes=fixture.get("notes"),
            calls=[call],
            status=call.status,
            error=call.error,
        )

    def run_turn(self, correction_model: str, chat_model: str, fixture: dict) -> RunResult:
        corr_messages = correction_messages(
            fixture["message_to_correct"],
            fixture.get("prior_exchange") or [],
            fixture.get("target_language"),
            fixture.get("native_language"),
        )
        chat_messages = chat_reply_messages(
            fixture.get("history") or [],
            fixture.get("target_language"),
            fixture.get("native_language"),
        )

        with ThreadPoolExecutor(max_workers=2) as pool:
            corr_future = pool.submit(self._call_json, correction_model, corr_messages, "correction")
            chat_future = pool.submit(self._call_json, chat_model, chat_messages, "chat_reply")
            calls = [corr_future.result(), chat_future.result()]

        status = "ok" if all(c.status == "ok" for c in calls) else "error"
        errors = "; ".join(c.error for c in calls if c.error) or None
        return RunResult(
            fixture_id=fixture["id"],
            task="turn",
            model=None,
            models={"correction": correction_model, "chat": chat_model},
            notes=fixture.get("notes"),
            calls=calls,
            status=status,
            error=errors,
        )


TASK_DEFAULT_FIXTURES: dict[str, str] = {
    "correction": "fixtures/corrections.yaml",
    "chat_reply": "fixtures/chat_reply.yaml",
    "translation": "fixtures/translations.yaml",
    "title": "fixtures/titles.yaml",
    "turn": "fixtures/turns.yaml",
}

TASK_RUNNERS: dict[str, Callable[[ModelRunner, str, dict], RunResult]] = {
    "correction": lambda r, m, f: r.run_correction(m, f),
    "chat_reply": lambda r, m, f: r.run_chat_reply(m, f),
    "translation": lambda r, m, f: r.run_translation(m, f),
    "title": lambda r, m, f: r.run_title(m, f),
}
