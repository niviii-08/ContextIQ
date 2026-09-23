from app.llm.explanation_service import (
    deterministic_fallback,
    generate_explanation,
)
from app.llm.provider import LLMProvider, MockLLMProvider
from app.schemas import LLMExplanationRequest


class FaithfulProvider(LLMProvider):
    """Returns text that only uses facts present in the prompt/payload."""

    def complete(self, system_prompt, user_prompt, max_tokens=300):
        return "Lab Record has an 82% forgetting risk based on prior history."


class HallucinatingProvider(LLMProvider):
    """Returns text with a fabricated number not present in the payload."""

    def complete(self, system_prompt, user_prompt, max_tokens=300):
        return "Lab Record has a 99% forgetting risk because you missed it 12 times last year."


class ExplodingProvider(LLMProvider):
    """Simulates a provider/network failure."""

    def complete(self, system_prompt, user_prompt, max_tokens=300):
        raise RuntimeError("network error")


def _sample_request():
    return LLMExplanationRequest(
        type="forgetting",
        payload={"task": "Lab Record", "probability": 0.82, "previous_forgetting_count": 4},
    )


def test_faithful_output_is_accepted():
    result = generate_explanation(_sample_request(), FaithfulProvider())
    assert result.validation_passed is True
    assert result.used_fallback is False
    assert "82" in result.text


def test_hallucinated_numbers_are_rejected_and_fallback_used():
    result = generate_explanation(_sample_request(), HallucinatingProvider())
    assert result.validation_passed is False
    assert result.used_fallback is True
    assert "99" not in result.text
    assert "12" not in result.text


def test_provider_failure_triggers_fallback():
    result = generate_explanation(_sample_request(), ExplodingProvider())
    assert result.used_fallback is True
    assert result.validation_passed is False


def test_deterministic_fallback_contains_only_payload_values():
    request = _sample_request()
    text = deterministic_fallback(request)
    assert "Lab Record" in text
    assert "0.82" in text
    assert "4" in text


def test_mock_provider_produces_structurally_valid_output_without_api_key():
    result = generate_explanation(_sample_request(), MockLLMProvider())
    assert isinstance(result.text, str)
    assert len(result.text) > 0


def test_fallback_never_raises_on_empty_payload():
    request = LLMExplanationRequest(type="empty_case", payload={})
    result = generate_explanation(request, ExplodingProvider())
    assert result.used_fallback is True
    assert result.text  # still produces something
