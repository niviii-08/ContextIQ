# LLM Architecture

## Responsibility boundary

| Layer | Responsibility |
|---|---|
| Upstream ML systems (external, not in this module) | Prediction, probability, association, metrics |
| `insight_engine.py` / `recommendations.py` / `daily_summary.py` | Deterministic interpretation of ML outputs into insights/recommendations |
| `llm/explanation_service.py` + `llm/provider.py` | **Only** phrasing/communication of already-computed facts into natural language |

The LLM is never given raw permission to compute a number, decide a risk
level, or invent a cause. It is given a small, already-validated JSON
payload and asked to phrase it.

## Provider abstraction (`llm/provider.py`)

```python
class LLMProvider(abc.ABC):
    @abc.abstractmethod
    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 300) -> str: ...
```

Implementations provided:
- `MockLLMProvider` — dependency-free, deterministic, used by default and in
  all tests. Requires no API key.
- `AnthropicLLMProvider` — thin adapter over the Anthropic Messages API.
  Import of the `anthropic` package is deferred so it's only required if
  this provider is actually selected.
- `OpenAILLMProvider` — same pattern for OpenAI, included to demonstrate
  provider replaceability (swap via `LLM_PROVIDER` env var only).

`get_provider(name, api_key)` is the single factory function the rest of the
app calls. Adding a new vendor means implementing `LLMProvider.complete()`
and registering it in this factory — no other file changes.

## Prompting

The system prompt (`SYSTEM_PROMPT` in `explanation_service.py`) instructs
the model to:
1. Use only facts/numbers/names present in the JSON payload.
2. Never invent numbers, probabilities, causes, dates, or user behaviour.
3. Never speculate about causes not explicitly present.
4. Stay to 1–2 sentences, no markdown.

The user prompt is the JSON-serialized `{type, data: payload}` — nothing
else is sent.

## Hallucination validation

After the provider returns text, `_validate_no_hallucination()`:

1. Collects every numeric value present anywhere in the payload (including
   percentage-equivalent forms, e.g. `0.82` also registers as `82`).
2. Extracts every number in the LLM's output text.
3. Rejects the output if any output number doesn't correspond (within a
   small tolerance for rounding/formatting) to an allowed payload number.
   Small numbers (0, 1, 2) are always allowed since they typically come from
   sentence structure, not fabricated statistics.

String/entity hallucination is constrained upstream: the payload passed to
the LLM only ever contains the task/context names already present in the
structured `Insight`/`Recommendation` being explained, and the system prompt
explicitly forbids introducing new facts.

## Fallback

If validation fails, or the provider raises an exception, or output is
otherwise unusable, `generate_explanation()`:

1. Retries once (`max_attempts`, default 2).
2. If still invalid, calls `deterministic_fallback()`, which builds a plain
   sentence by directly interpolating payload key/value pairs. This path
   uses no LLM call and therefore cannot hallucinate by construction.

The `LLMExplanationResult` returned always tells the caller whether a
fallback was used (`used_fallback`) and why validation failed
(`rejected_reason`), so this is auditable end-to-end.

## Testing without an API key

`tests/test_llm_explanation.py` exercises the validation/fallback pipeline
using hand-written `LLMProvider` test doubles (`FaithfulProvider`,
`HallucinatingProvider`, `ExplodingProvider`) — no network access or API key
is required. The default `LLM_PROVIDER=mock` setting means the full test
suite, including API integration tests, runs offline.
