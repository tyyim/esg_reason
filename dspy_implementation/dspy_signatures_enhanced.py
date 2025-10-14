#!/usr/bin/env python3
"""
Enhanced DSPy Signatures for MMESGBench RAG
Includes query generation for retrieval optimization
"""

import dspy


class QueryGeneration(dspy.Signature):
    """
    Generate optimized search query for ESG document retrieval.

    This signature is optimizable - MIPROv2 will learn better instructions
    for reformulating questions to maximize retrieval accuracy.
    """
    question = dspy.InputField(
        desc="Original user question about ESG or climate data"
    )
    doc_type = dspy.InputField(
        desc="Document type: ESG report, climate assessment, sustainability report"
    )

    search_query = dspy.OutputField(
        desc="Optimized retrieval query with key ESG terms, metrics, and context"
    )
    reasoning = dspy.OutputField(
        desc="Explanation of why this query will retrieve relevant evidence"
    )


class ESGReasoning(dspy.Signature):
    """
    Analyze ESG document context and provide detailed reasoning.

    Stage 1 of two-stage extraction: Generate chain-of-thought analysis
    over retrieved context to answer ESG questions.

    IMPORTANT: If the context does not contain sufficient information to answer
    the question, clearly state in your analysis that the question cannot be
    answered from the given context.
    """
    context = dspy.InputField(
        desc="Retrieved chunks from ESG documents"
    )
    question = dspy.InputField(
        desc="ESG question to answer"
    )
    doc_id = dspy.InputField(
        desc="Source document identifier"
    )

    analysis = dspy.OutputField(
        desc="Detailed chain-of-thought reasoning analyzing the context to answer the question. If context lacks sufficient information, clearly state the question cannot be answered."
    )


class AnswerExtraction(dspy.Signature):
    """
    Extract structured answer from analysis.

    Stage 2 of two-stage extraction: Extract final answer in specified format
    (Int, Float, Str, List) from the chain-of-thought analysis.

    CRITICAL INSTRUCTIONS:
    - Extract answer in the specified format: Int, Float, Str, or List
    - If the analysis indicates the question cannot be answered from the context,
      respond with exactly: "Not answerable"
    - If the analysis indicates it cannot read/understand images or documents,
      respond with exactly: "Fail to answer"
    - Otherwise, provide only the answer value without explanation
    """
    question = dspy.InputField(
        desc="Original ESG question"
    )
    analysis = dspy.InputField(
        desc="Chain-of-thought reasoning from Stage 1"
    )
    answer_format = dspy.InputField(
        desc="Required answer format: Int, Float, Str, or List"
    )

    extracted_answer = dspy.OutputField(
        desc='Final answer in specified format, or "Not answerable" if context lacks information, or "Fail to answer" if documents cannot be read'
    )


# Keep original signatures for backward compatibility
class ESGReasoningOriginal(dspy.Signature):
    """Original reasoning signature without query optimization."""
    context = dspy.InputField(desc="Retrieved ESG document chunks")
    question = dspy.InputField(desc="ESG question")
    doc_id = dspy.InputField(desc="Document ID")

    analysis = dspy.OutputField(desc="Detailed reasoning")


class AnswerExtractionOriginal(dspy.Signature):
    """Original extraction signature."""
    question = dspy.InputField(desc="ESG question")
    analysis = dspy.InputField(desc="Reasoning from Stage 1")
    answer_format = dspy.InputField(desc="Expected format")

    extracted_answer = dspy.OutputField(desc="Final answer")


if __name__ == "__main__":
    print("=" * 60)
    print("Enhanced DSPy Signatures with Query Generation")
    print("=" * 60)

    print("\n✅ Signatures defined:")
    print("   1. QueryGeneration - Optimize retrieval queries")
    print("   2. ESGReasoning - Chain-of-thought analysis")
    print("   3. AnswerExtraction - Structured answer extraction")

    print("\n📝 Signature details:")
    print("\nQueryGeneration:")
    print(f"   Inputs: {[f.name for f in QueryGeneration.input_fields]}")
    print(f"   Outputs: {[f.name for f in QueryGeneration.output_fields]}")

    print("\nESGReasoning:")
    print(f"   Inputs: {[f.name for f in ESGReasoning.input_fields]}")
    print(f"   Outputs: {[f.name for f in ESGReasoning.output_fields]}")

    print("\nAnswerExtraction:")
    print(f"   Inputs: {[f.name for f in AnswerExtraction.input_fields]}")
    print(f"   Outputs: {[f.name for f in AnswerExtraction.output_fields]}")

    print("\n✅ All signatures ready for optimization!")
