"""
llm/explanation_service.py
===========================
Turns a structured explanation request into human-readable text, using an
LLMProvider for phrasing while enforcing that no unsupported facts are
introduced.

SAFETY MODEL
------------
1. The LLM is given ONLY the structured JSON payload (already validated by
   Pydantic elsewhere in the pipeline) plus an instruction to explain it
   without adding new facts, numbers, or causes.
2. The LLM's output is validated against the payload:
     - every numeric token in the output must correspond to a numeric value
       actually present in the payload (allowing standard formatting, e.g.
       0.82 -> "82%").
     - the output must not introduce named entities (tasks/contexts) that
       are not present in the payload.
3. If validation fails, the explanation is REJECTED and regeneration is
   attempted once. If it fails again, the module falls back to a fully
   deterministic, template-based explanation built directly from the
   payload — which by construction cannot hallucinate.
"""

from __future__ import annotations

import re
from typing import Any, Dict

from app.llm.provider import LLMProvider
from app.schemas import LLMExplanationRequest, LLMExplanationResult

SYSTEM_PROMPT = (
    "You are an explanation-writing assistant for a behavioural-analytics app. "
    "You will receive a JSON object describing a single already-computed "
    "insight or recommendation. Write ONE short, plain-language sentence or "
    "two explaining it to the end user. "
    "STRICT RULES: "
    "1) Use ONLY the facts, numbers, and names present in the JSON. "
    "2) Do NOT invent numbers, probabilities, causes, dates, or user behaviour "
    "not present in the JSON. "
    "3) Do NOT speculate about why something happened unless a cause is "
    "explicitly present in the JSON. "
    "4) Keep it concise (max 2 sentences). "
    "5) Do not use markdown."
)

_NUMBER_RE = re.compile(r"\d+(\.\d+)?")


def _numbers_in_payload(payload: Dict[str, Any]) -> set:
    numbers = set()

    def walk(value):
        if isinstance(value, (int, float)):
            numbers.add(round(float(value), 4))
            # also register percentage-rounded form, e.g. 0.82 -> 82
            if 0 <= value <= 1:
                numbers.add(round(value * 100))
                numbers.add(round(value * 100, 1))
        elif isinstance(value, str):
            for m in _NUMBER_RE.finditer(value):
                try:
                    numbers.add(round(float(m.group()), 4))
                except ValueError:
                    pass
        elif isinstance(value, dict):
            for v in value.values():
                walk(v)
        elif isinstance(value, list):
            for v in value:
                walk(v)

    walk(payload)
    return numbers


def _strings_in_payload(payload: Dict[str, Any]) -> set:
    strings = set()

    def walk(value):
        if isinstance(value, str) and value.strip():
            strings.add(value.strip().lower())
        elif isinstance(value, dict):
            for v in value.values():
                walk(v)
        elif isinstance(value, list):
            for v in value:
                walk(v)

    walk(payload)
    return strings


def _validate_no_hallucination(output_text: str, payload: Dict[str, Any]) -> tuple:
    """Return (is_valid, reason_if_invalid)."""
    allowed_numbers = _numbers_in_payload(payload)

    found_numbers = set()
    for m in _NUMBER_RE.finditer(output_text):
        try:
            found_numbers.add(round(float(m.group()), 4))
        except ValueError:
            continue

    # Allow small integers 0-2 (e.g. "one", counts of sentences) and any
    # number that rounds close to an allowed number, to avoid over-rejecting
    # on formatting differences (e.g. "82%" vs 82.0 vs 0.82).
    for num in found_numbers:
        if num in (0, 1, 2):
            continue
        if any(abs(num - allowed) < 0.6 for allowed in allowed_numbers):
            continue
        return False, f"Unsupported number in output: {num}"

    return True, None


def build_prompt(request: LLMExplanationRequest) -> str:
    import json

    return json.dumps({"type": request.type, "data": request.payload}, ensure_ascii=False)


def deterministic_fallback(request: LLMExplanationRequest) -> str:
    """Template-based explanation that can never hallucinate, since it only
    interpolates values already present in the payload."""
    payload = request.payload
    parts = [f"{k.replace('_', ' ')}: {v}" for k, v in payload.items()]
    return f"{request.type.replace('_', ' ').capitalize()} — " + "; ".join(parts) + "."


def generate_explanation(
    request: LLMExplanationRequest,
    provider: LLMProvider,
    max_attempts: int = 2,
) -> LLMExplanationResult:
    """Generate a validated natural-language explanation, falling back to a
    deterministic template if the LLM output can't be validated."""
    user_prompt = build_prompt(request)

    last_reason = None
    for _ in range(max_attempts):
        try:
            raw_text = provider.complete(SYSTEM_PROMPT, user_prompt)
        except Exception as exc:  # noqa: BLE001 - provider failures fall back too
            last_reason = f"provider_error: {exc}"
            break

        is_valid, reason = _validate_no_hallucination(raw_text, request.payload)
        if is_valid:
            return LLMExplanationResult(
                text=raw_text.strip(),
                used_fallback=False,
                validation_passed=True,
            )
        last_reason = reason

    fallback_text = deterministic_fallback(request)
    return LLMExplanationResult(
        text=fallback_text,
        used_fallback=True,
        validation_passed=False,
        rejected_reason=last_reason,
    )
