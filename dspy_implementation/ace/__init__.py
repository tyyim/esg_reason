"""
ACE integration for MMESGBench.

This package wires the ACE-open modules to the project's RAG and evaluation pipeline.
"""

from .ace_module import ACERAGModule  # noqa: F401
from .ace_llm import DashscopeLLMClient  # noqa: F401
from .openai_llm import OpenAILLMClient  # noqa: F401


