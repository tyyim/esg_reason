"""OpenAI-compatible LLM client for ACE roles.

Supports OpenAI API and OpenAI-compatible APIs (e.g., DashScope, DeepSeek).
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

try:
    from openai import OpenAI
except ImportError:
    raise ImportError(
        "openai package is required. Install it with: pip install openai"
    )

from .llm_base import LLMClient, LLMResponse


class OpenAILLMClient(LLMClient):
    """OpenAI-compatible client that conforms to ACE-open's LLMClient interface."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> None:
        """
        Initialize OpenAI-compatible LLM client.

        Args:
            model: Model name (e.g., "gpt-4o-mini", "deepseek-v3.1")
            api_key: API key (defaults to OPENAI_API_KEY env var)
            base_url: Base URL for API (defaults to None for OpenAI, or OPENAI_API_BASE env var)
            system_prompt: Custom system prompt (defaults to JSON-only prompt)
        """
        super().__init__(model=model)
        
        # Get API key from parameter or environment
        if api_key is None:
            api_key = os.getenv("API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY not provided and not found in environment variables. "
                "Please set OPENAI_API_KEY or pass api_key parameter."
            )
        
        # Get base_url from parameter or environment
        if base_url is None:
            base_url = os.getenv("API_BASE")
        
        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,  # None means use OpenAI's default
        )
        
        self._system_prompt = system_prompt or (
            "You are a JSON-only assistant that MUST reply with a single valid JSON object without extra text.\n"
            "Reasoning: low\n"
            "Do not expose analysis or chain-of-thought. Respond using the final JSON only."
        )

    def complete(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """
        Complete a prompt using OpenAI API.

        Args:
            prompt: The prompt text
            **kwargs: Additional parameters:
                - temperature: float (default: 0.0)
                - max_tokens: int (default: 1024)
                - max_new_tokens: int (alias for max_tokens)

        Returns:
            LLMResponse with text and raw response data
        """
        # Map ACE kwargs to OpenAI params
        temperature = float(kwargs.get("temperature", 0.0))
        max_tokens = int(
            kwargs.get("max_new_tokens", kwargs.get("max_tokens", 1024))
        )

        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": prompt},
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {type(e).__name__}: {e}") from e

        text = response.choices[0].message.content
        if text is None:
            raise RuntimeError("OpenAI API returned empty response")
        
        text = text.strip()
        
        # Return as ACE LLMResponse
        raw: Dict[str, Any] = {
            "id": response.id,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                "completion_tokens": response.usage.completion_tokens if response.usage else None,
                "total_tokens": response.usage.total_tokens if response.usage else None,
            },
        }
        return LLMResponse(text=text, raw=raw)

