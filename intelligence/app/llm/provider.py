"""
llm/provider.py
================
Provider-agnostic LLM abstraction. The rest of the module talks only to the
LLMProvider interface, never to a specific vendor SDK, so the backing model
can be swapped (Anthropic, OpenAI, local model, mock) without touching
insight/recommendation/explanation logic.
"""

from __future__ import annotations

import abc
from typing import Optional


class LLMProvider(abc.ABC):
    """Minimal interface every LLM backend must implement."""

    @abc.abstractmethod
    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 300) -> str:
        """Return raw text completion for the given prompts."""
        raise NotImplementedError


class MockLLMProvider(LLMProvider):
    """Deterministic, dependency-free provider used for tests and offline runs.

    It does not call any network API. It produces a plausible, structurally
    valid explanation directly from the payload it's given, so unit tests can
    run without an API key while still exercising the validation pipeline.
    """

    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 300) -> str:
        # Echo a simple, templated sentence built only from what appears in
        # the user_prompt (which itself is built only from validated
        # structured input by the caller). This keeps the mock provider
        # incapable of inventing facts.
        return f"[mock-explanation] {user_prompt.strip()[:280]}"


class AnthropicLLMProvider(LLMProvider):
    """Adapter around the Anthropic Messages API.

    Kept dependency-light: uses the `anthropic` package if installed. Import
    is deferred so the rest of the module works without the package present
    (e.g. in CI using MockLLMProvider).
    """

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            import anthropic  # deferred import

            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 300) -> str:
        client = self._get_client()
        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        parts = [block.text for block in response.content if getattr(block, "type", None) == "text"]
        return "".join(parts)


class OpenAILLMProvider(LLMProvider):
    """Adapter around the OpenAI Chat Completions API, provided as a second
    example implementation to demonstrate provider replaceability."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            import openai  # deferred import

            self._client = openai.OpenAI(api_key=self.api_key)
        return self._client

    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 300) -> str:
        client = self._get_client()
        response = client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content or ""


class OpenRouterLLMProvider(LLMProvider):
    """Adapter for OpenRouter (https://openrouter.ai).

    OpenRouter exposes an OpenAI-compatible API that routes requests to many
    different models (GPT-4o, Claude, Mistral, Llama, etc.) with a single
    API key. Set LLM_PROVIDER=openrouter and LLM_API_KEY=<provider-api-key> in .env.

    Example model strings for LLM_MODEL:
        openai/gpt-4o-mini        (fast, cheap)
        openai/gpt-4o
        anthropic/claude-sonnet-4-6
        google/gemini-flash-1.5
        meta-llama/llama-3.1-8b-instruct:free  (free tier)
    """

    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, api_key: str, model: str = "openai/gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            import openai  # deferred import — openai package required

            self._client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.OPENROUTER_BASE_URL,
                default_headers={
                    "HTTP-Referer": "https://github.com/contextiq",
                    "X-Title": "ContextIQ",
                },
            )
        return self._client

    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 300) -> str:
        client = self._get_client()
        response = client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content or ""


def get_provider(provider_name: str, api_key: Optional[str] = None) -> LLMProvider:
    """Factory used by the app to construct a provider from configuration."""
    provider_name = (provider_name or "mock").lower()
    if provider_name == "mock":
        return MockLLMProvider()
    if provider_name == "anthropic":
        if not api_key:
            raise ValueError("api_key is required for the anthropic provider")
        return AnthropicLLMProvider(api_key=api_key)
    if provider_name == "openai":
        if not api_key:
            raise ValueError("api_key is required for the openai provider")
        return OpenAILLMProvider(api_key=api_key)
    if provider_name == "openrouter":
        if not api_key:
            raise ValueError("api_key is required for the openrouter provider")
        return OpenRouterLLMProvider(api_key=api_key)
    raise ValueError(f"Unknown LLM provider: {provider_name!r}. "
                     f"Valid options: mock, anthropic, openai, openrouter")
