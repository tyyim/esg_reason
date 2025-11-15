"""Minimal LLM base types compatible with ACE roles."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class LLMResponse:
    text: str
    raw: Optional[Dict[str, Any]] = None


class LLMClient(ABC):
    def __init__(self, model: Optional[str] = None) -> None:
        self.model = model

    @abstractmethod
    def complete(self, prompt: str, **kwargs: Any) -> LLMResponse:  # pragma: no cover
        ...


