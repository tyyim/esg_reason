"""
ACE + RAG Integration for MMESGBench

This module composes ACE-open components with the project's retriever
and evaluation utilities. It maintains a persistent Playbook that evolves
online across questions, matching ACE's online adaptation mode.
"""
from __future__ import annotations

import sys
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Project imports
_project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_project_root))
from dspy_implementation.dspy_postgres_retriever import DSPyPostgresRetriever  # type: ignore
from MMESGBench.src.eval.eval_score import eval_score  # type: ignore

from .playbook import Playbook
from .roles import Generator, Reflector, Curator
from .adaptation import OnlineAdapter, TaskEnvironment, EnvironmentResult, Sample
from .prompts import GENERATOR_PROMPT, REFLECTOR_PROMPT, CURATOR_PROMPT

from .ace_llm import DashscopeLLMClient

logger = logging.getLogger(__name__)


@dataclass
class _ESGSample(Sample):
    """Alias to carry MMESGBench-specific metadata if needed."""
    pass


class _ESGEnvironment(TaskEnvironment):
    """Task environment producing feedback based on MMESGBench ANLS scoring."""

    def evaluate(self, sample: Sample, generator_output) -> EnvironmentResult:  # type: ignore[override]
        prediction = generator_output.final_answer
        gt = sample.ground_truth
        # Compute ANLS if GT available; else neutral feedback
        if gt is not None:
            try:
                score = float(eval_score(str(gt), str(prediction), sample.metadata.get("answer_format", "Str")))
            except Exception:
                score = 0.0
            is_correct = score >= 0.5
            feedback = f"ANLS={score:.3f}; correct={is_correct}; expected={gt}"
            return EnvironmentResult(feedback=feedback, ground_truth=str(gt), metrics={"anls": score})
        return EnvironmentResult(feedback="no_ground_truth", ground_truth=None, metrics={})


class ACERAGModule:
    """
    ACE online adaptation with ESG RAG context.

    Flow:
        question -> retrieval -> ACE generator -> answer
                                      |  ^
                                      v  |
                                 reflection + curation -> playbook updates
    """

    def __init__(
        self,
        model_name: str = "qwen2.5-7b-instruct",
        *,
        max_refinement_rounds: int = 1,
        reflection_window: int = 3,
    ) -> None:
        self.retriever = DSPyPostgresRetriever()
        self.playbook = Playbook()
        self.llm = DashscopeLLMClient(model=model_name)
        self.generator = Generator(self.llm, prompt_template=GENERATOR_PROMPT)
        self.reflector = Reflector(self.llm, prompt_template=REFLECTOR_PROMPT)
        self.curator = Curator(self.llm, prompt_template=CURATOR_PROMPT)
        self.adapter = OnlineAdapter(
            playbook=self.playbook,
            generator=self.generator,
            reflector=self.reflector,
            curator=self.curator,
            max_refinement_rounds=max_refinement_rounds,
            reflection_window=reflection_window,
        )
        self.environment = _ESGEnvironment()
        self.model_name = model_name

    def forward(self, question: str, doc_id: str, answer_format: str, *, context_top_k: int = 5, context_override: str | None = None, ground_truth: str | None = None) -> str:
        context = context_override if context_override is not None else self.retriever.retrieve(doc_id, question, top_k=context_top_k)
        if not context:
            return "ERROR: Retrieval failed"

        try:
            details = self.forward_with_details(question, doc_id, answer_format, context=context, ground_truth=ground_truth)
            return details.get("final_answer", "") or ""
        except Exception as e:
            raise RuntimeError(f"ACE forward error: {type(e).__name__}: {e}") from e

    def __call__(self, question: str, doc_id: str, answer_format: str) -> str:
        return self.forward(question, doc_id, answer_format)

    def playbook_stats(self) -> dict:
        return self.playbook.stats()

    def forward_with_details(
        self,
        question: str,
        doc_id: str,
        answer_format: str,
        *,
        context_top_k: int = 5,
        context: str | None = None,
        ground_truth: str | None = None,
        adapt: bool = True,
    ) -> dict:
        # Retriever
        logger.info("[Retriever] Starting retrieval...")
        if context is None:
            context = self.retriever.retrieve(doc_id, question, top_k=context_top_k)
        if not context:
            raise RuntimeError("Retrieval failed: empty context")
        logger.info(f"[Retriever] Completed. Retrieved context length: {len(context)} chars")

        sample = _ESGSample(
            question=question,
            context=context,
            ground_truth=ground_truth,  # Pass ground_truth to enable reflection
            metadata={"doc_id": doc_id, "answer_format": answer_format},
        )
        
        if adapt:
            logger.info("[ACE] Starting adapter run (Generator -> Reflector -> Curator)...")
            results = self.adapter.run([sample], self.environment)
            if not results:
                raise RuntimeError("ACE produced no result")
            last = results[-1]
            logger.info("[ACE] Adapter run completed successfully")
            return {
                "final_answer": last.generator_output.final_answer,
                "reasoning": last.generator_output.reasoning,
                "bullet_ids": last.generator_output.bullet_ids,
                "context": context,
            }
        else:
            logger.info("[ACE] Adaptation disabled. Generating with fixed playbook...")
            gen = self.generator.generate(
                question=question,
                context=context,
                playbook=self.playbook,
                reflection=None,
                answer_format=answer_format,
            )
            return {
                "final_answer": gen.final_answer,
                "reasoning": gen.reasoning,
                "bullet_ids": gen.bullet_ids,
                "context": context,
            }


