#!/usr/bin/env python3
"""
DSPy RAG Module for MMESGBench
Implements two-stage RAG: ColBERT Retrieval → Reasoning → Extraction
"""

import dspy
from dspy_implementation.dspy_retriever import DSPyColBERTRetriever
from dspy_implementation.dspy_signatures import ESGReasoning, AnswerExtraction


class MMESGBenchRAG(dspy.Module):
    """
    Main RAG module for MMESGBench evaluation.

    Architecture:
        1. ColBERT Retrieval: Top-5 semantic chunks (existing 41.3% baseline)
        2. Stage 1 - Reasoning: ChainOfThought over retrieved context
        3. Stage 2 - Extraction: Predict structured answer from analysis

    This matches MMESGBench paper's two-stage extraction approach.
    """

    def __init__(self):
        super().__init__()

        # Initialize ColBERT retriever (existing infrastructure)
        self.retriever = DSPyColBERTRetriever()

        # DSPy modules for two-stage generation
        # Stage 1: Generate detailed analysis with chain-of-thought
        self.reasoning = dspy.ChainOfThought(ESGReasoning)

        # Stage 2: Extract structured answer from analysis
        self.extraction = dspy.Predict(AnswerExtraction)

        print("✅ MMESGBenchRAG module initialized")
        print("   • Retriever: ColBERT (41.3% baseline)")
        print("   • Stage 1: ChainOfThought reasoning")
        print("   • Stage 2: Answer extraction")

    def forward(self, question: str, doc_id: str, answer_format: str):
        """
        Forward pass: Retrieve → Reason → Extract

        Args:
            question: ESG question text
            doc_id: Source document identifier
            answer_format: Expected format (Int, Float, Str, List)

        Returns:
            dspy.Prediction with:
                - answer: Extracted answer string
                - analysis: Stage 1 reasoning
                - context: Retrieved chunks
        """
        # Step 1: Retrieve top-5 chunks using ColBERT
        context = self.retriever.retrieve(doc_id, question, top_k=5)

        if not context:
            # Fallback if retrieval fails
            return dspy.Prediction(
                answer="Failed to retrieve context",
                analysis="Document indexing or retrieval failed",
                context=""
            )

        # Step 2: Generate analysis (Stage 1) with chain-of-thought
        reasoning_output = self.reasoning(
            question=question,
            context=context,
            doc_id=doc_id
        )

        # Step 3: Extract answer (Stage 2) from analysis
        extraction_output = self.extraction(
            question=question,
            analysis=reasoning_output.analysis,
            answer_format=answer_format
        )

        # Return complete prediction
        return dspy.Prediction(
            answer=extraction_output.extracted_answer,
            analysis=reasoning_output.analysis,
            context=context,
            rationale=getattr(reasoning_output, 'rationale', '')  # If using CoT
        )


class MMESGBenchRAGBasic(dspy.Module):
    """
    Basic RAG module without chain-of-thought (for baseline comparison).

    Uses Predict instead of ChainOfThought for Stage 1.
    """

    def __init__(self):
        super().__init__()
        self.retriever = DSPyColBERTRetriever()
        self.reasoning = dspy.Predict(ESGReasoning)  # Basic Predict, no CoT
        self.extraction = dspy.Predict(AnswerExtraction)

        print("✅ MMESGBenchRAGBasic module initialized (no CoT)")

    def forward(self, question: str, doc_id: str, answer_format: str):
        """Same forward pass as MMESGBenchRAG but without CoT"""
        context = self.retriever.retrieve(doc_id, question, top_k=5)

        if not context:
            return dspy.Prediction(
                answer="Failed to retrieve context",
                analysis="Document retrieval failed",
                context=""
            )

        reasoning_output = self.reasoning(
            question=question,
            context=context,
            doc_id=doc_id
        )

        extraction_output = self.extraction(
            question=question,
            analysis=reasoning_output.analysis,
            answer_format=answer_format
        )

        return dspy.Prediction(
            answer=extraction_output.extracted_answer,
            analysis=reasoning_output.analysis,
            context=context
        )


if __name__ == "__main__":
    print("=" * 60)
    print("DSPy RAG Module Test")
    print("=" * 60)

    # Initialize DSPy with Qwen
    from dspy_implementation.dspy_setup import setup_dspy_qwen
    setup_dspy_qwen()

    print("\n🧪 Testing RAG module...")

    # Create module
    rag = MMESGBenchRAG()

    # Test question
    question = "According to the IPCC, which region had the highest per capita GHG emissions in 2019?"
    doc_id = "AR6 Synthesis Report Climate Change 2023.pdf"
    answer_format = "Str"

    print(f"\n📝 Question: {question}")
    print(f"📄 Document: {doc_id}")
    print(f"📊 Format: {answer_format}")

    # Run forward pass
    print("\n🚀 Running two-stage RAG...")
    prediction = rag(question=question, doc_id=doc_id, answer_format=answer_format)

    print(f"\n✅ Results:")
    print(f"   Answer: {prediction.answer}")
    print(f"   Analysis (first 200 chars): {prediction.analysis[:200]}...")
    print(f"   Context length: {len(prediction.context)} chars")

    print("\n✅ RAG module working correctly!")
