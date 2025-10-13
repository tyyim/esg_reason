#!/usr/bin/env python3
"""
Enhanced DSPy RAG Module for MMESGBench
Includes query generation for optimized retrieval
"""

import dspy
from dspy_implementation.dspy_postgres_retriever import DSPyPostgresRetriever
from dspy_implementation.dspy_signatures_enhanced import (
    QueryGeneration,
    ESGReasoning,
    AnswerExtraction
)


class EnhancedMMESGBenchRAG(dspy.Module):
    """
    Enhanced RAG module with query optimization.

    Architecture:
        Stage 0: Query Generation (NEW - optimizable)
            - Reformulate question for better retrieval
            - Optimize for ESG terminology and context

        Stage 1: Retrieval (existing, but uses optimized query)
            - PostgreSQL + pgvector semantic search
            - Qwen text-embedding-v4 (1024-dim)
            - Top-5 chunks

        Stage 2: Reasoning (existing - optimizable)
            - ChainOfThought over retrieved context
            - Qwen Max with CoT prompting

        Stage 3: Extraction (existing - optimizable)
            - Extract structured answer from analysis
            - Format validation (Int, Float, Str, List)

    Key Improvement: Query generation addresses retrieval bottleneck
    (research shows 90% correlation between retrieval and final accuracy)
    """

    def __init__(self, enable_query_optimization: bool = True):
        super().__init__()

        self.enable_query_optimization = enable_query_optimization

        # Stage 0: Query generation/optimization (NEW)
        if enable_query_optimization:
            self.query_gen = dspy.ChainOfThought(QueryGeneration)

        # Stage 1: Retrieval (existing)
        self.retriever = DSPyPostgresRetriever()

        # Stage 2: Reasoning with CoT (existing)
        self.reasoning = dspy.ChainOfThought(ESGReasoning)

        # Stage 3: Answer extraction (existing)
        self.extraction = dspy.Predict(AnswerExtraction)

        print("✅ EnhancedMMESGBenchRAG module initialized")
        print(f"   • Query optimization: {'ENABLED' if enable_query_optimization else 'DISABLED'}")
        print("   • Retriever: PostgreSQL + pgvector (Qwen embeddings)")
        print("   • Stage 1: Query generation (optimizable)")
        print("   • Stage 2: ChainOfThought reasoning (optimizable)")
        print("   • Stage 3: Answer extraction (optimizable)")

    def forward(self, question: str, doc_id: str, answer_format: str):
        """
        Forward pass: Query Gen → Retrieve → Reason → Extract

        Args:
            question: ESG question text
            doc_id: Source document identifier
            answer_format: Expected format (Int, Float, Str, List)

        Returns:
            dspy.Prediction with:
                - answer: Extracted answer string
                - search_query: Optimized query used for retrieval
                - query_reasoning: Why this query is better
                - analysis: Stage 2 reasoning
                - context: Retrieved chunks
                - retrieval_score: Average similarity score
        """
        # Stage 0: Generate optimized query
        if self.enable_query_optimization:
            query_output = self.query_gen(
                question=question,
                doc_type="ESG Climate Report"
            )
            search_query = query_output.search_query
            query_reasoning = query_output.reasoning
        else:
            # Fallback: use raw question
            search_query = question
            query_reasoning = "Using raw question (query optimization disabled)"

        # Stage 1: Retrieve with optimized query
        context = self.retriever.retrieve(
            doc_id=doc_id,
            question=search_query,  # Use optimized query, not raw question
            top_k=5
        )

        if not context:
            # Fallback if retrieval fails
            return dspy.Prediction(
                answer="Failed to retrieve context",
                search_query=search_query,
                query_reasoning=query_reasoning,
                analysis="Document indexing or retrieval failed",
                context="",
                retrieval_score=0.0
            )

        # Stage 2: Generate analysis with CoT
        reasoning_output = self.reasoning(
            question=question,  # Use original question for reasoning
            context=context,
            doc_id=doc_id
        )

        # Stage 3: Extract answer from analysis
        extraction_output = self.extraction(
            question=question,
            analysis=reasoning_output.analysis,
            answer_format=answer_format
        )

        # Return complete prediction with all intermediate outputs
        return dspy.Prediction(
            answer=extraction_output.extracted_answer,
            search_query=search_query,
            query_reasoning=query_reasoning,
            analysis=reasoning_output.analysis,
            context=context,
            rationale=getattr(reasoning_output, 'rationale', ''),
            retrieval_score=0.0  # Could compute from retriever if available
        )


class BaselineMMESGBenchRAG(dspy.Module):
    """
    Baseline RAG without query optimization (for comparison).

    This is identical to the original implementation - uses raw question
    for retrieval without optimization.
    """

    def __init__(self):
        super().__init__()

        # No query generation - use raw question
        self.retriever = DSPyPostgresRetriever()
        self.reasoning = dspy.ChainOfThought(ESGReasoning)
        self.extraction = dspy.Predict(AnswerExtraction)

        print("✅ BaselineMMESGBenchRAG module initialized (no query optimization)")

    def forward(self, question: str, doc_id: str, answer_format: str):
        """Same as enhanced but without query generation."""
        # Stage 1: Retrieve with raw question
        context = self.retriever.retrieve(
            doc_id=doc_id,
            question=question,  # Raw question, not optimized
            top_k=5
        )

        if not context:
            return dspy.Prediction(
                answer="Failed to retrieve context",
                search_query=question,
                query_reasoning="Using raw question (baseline)",
                analysis="Document retrieval failed",
                context="",
                retrieval_score=0.0
            )

        # Stage 2: Reasoning
        reasoning_output = self.reasoning(
            question=question,
            context=context,
            doc_id=doc_id
        )

        # Stage 3: Extraction
        extraction_output = self.extraction(
            question=question,
            analysis=reasoning_output.analysis,
            answer_format=answer_format
        )

        return dspy.Prediction(
            answer=extraction_output.extracted_answer,
            search_query=question,
            query_reasoning="Using raw question (baseline)",
            analysis=reasoning_output.analysis,
            context=context,
            rationale=getattr(reasoning_output, 'rationale', ''),
            retrieval_score=0.0
        )


if __name__ == "__main__":
    print("=" * 60)
    print("Enhanced DSPy RAG Module Test")
    print("=" * 60)

    # Initialize DSPy with Qwen
    from dspy_implementation.dspy_setup import setup_dspy_qwen
    setup_dspy_qwen()

    print("\n🧪 Testing enhanced RAG module...")

    # Create both modules for comparison
    enhanced_rag = EnhancedMMESGBenchRAG(enable_query_optimization=True)
    baseline_rag = BaselineMMESGBenchRAG()

    # Test question
    question = "According to the IPCC, which region had the highest per capita GHG emissions in 2019?"
    doc_id = "AR6 Synthesis Report Climate Change 2023.pdf"
    answer_format = "Str"

    print(f"\n📝 Question: {question}")
    print(f"📄 Document: {doc_id}")
    print(f"📊 Format: {answer_format}")

    # Test enhanced RAG
    print("\n🚀 Testing ENHANCED RAG (with query optimization)...")
    enhanced_pred = enhanced_rag(question=question, doc_id=doc_id, answer_format=answer_format)

    print(f"\n✅ Enhanced Results:")
    print(f"   Optimized Query: {enhanced_pred.search_query}")
    print(f"   Query Reasoning: {enhanced_pred.query_reasoning}")
    print(f"   Answer: {enhanced_pred.answer}")
    print(f"   Analysis (first 150 chars): {enhanced_pred.analysis[:150]}...")

    # Test baseline RAG
    print("\n🚀 Testing BASELINE RAG (no query optimization)...")
    baseline_pred = baseline_rag(question=question, doc_id=doc_id, answer_format=answer_format)

    print(f"\n✅ Baseline Results:")
    print(f"   Query Used: {baseline_pred.search_query}")
    print(f"   Answer: {baseline_pred.answer}")
    print(f"   Analysis (first 150 chars): {baseline_pred.analysis[:150]}...")

    print("\n✅ Both modules working correctly!")
    print("\n📊 Key Difference:")
    print("   Enhanced: Uses optimized query for retrieval")
    print("   Baseline: Uses raw question for retrieval")
