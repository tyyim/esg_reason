"""DashScope-backed LLM client compatible with ACE-open's LLMClient.

Uses Qwen via dashscope Generation API and returns JSON-only text for ACE roles.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

import dashscope
from dashscope import Generation
from .llm_base import LLMClient, LLMResponse


class DashscopeLLMClient(LLMClient):
    """DashScope client that conforms to ACE-open's LLMClient interface."""

    def __init__(self, model: str = "qwen2.5-7b-instruct", system_prompt: Optional[str] = None) -> None:
        super().__init__(model=model)
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("DASHSCOPE_API_KEY environment variable not set")
        dashscope.api_key = api_key
        self._system_prompt = system_prompt or (
            "You are a JSON-only assistant that MUST reply with a single valid JSON object without extra text.\n"
            "Reasoning: low\n"
            "Do not expose analysis or chain-of-thought. Respond using the final JSON only."
        )

    def complete(self, prompt: str, **kwargs: Any) -> LLMResponse:
        # Map ACE kwargs to dashscope params if needed; keep conservative defaults
        temperature = float(kwargs.get("temperature", 0.0))
        max_tokens = int(kwargs.get("max_new_tokens", kwargs.get("max_tokens", 1024)))

        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": prompt},
        ]

        response = Generation.call(
            model=self.model,
            messages=messages,
            result_format='message',
            temperature=temperature,
            max_tokens=max_tokens,
        )

        if response.status_code != 200:
            raise RuntimeError(f"DashScope API error: {response.code} - {response.message}")

        text = response.output.choices[0].message.content.strip()
        # Return as ACE LLMResponse
        raw: Dict[str, Any] = {
            "status_code": response.status_code,
            "request_id": getattr(response, "request_id", None),
        }
        return LLMResponse(text=text, raw=raw)


