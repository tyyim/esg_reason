#!/usr/bin/env python3
"""
DSPy Signatures for MMESGBench RAG
Implements two-stage architecture: Reasoning → Extraction
"""

import dspy

# ============================================================================
# Stage 1: ESG Reasoning with Retrieved Context
# ============================================================================

class ESGReasoning(dspy.Signature):
    """
    Answer ESG questions based on retrieved document context.

    This signature generates detailed analysis and reasoning about ESG questions
    using the top-5 retrieved document chunks from ColBERT retrieval.

    Aligned with MMESGBench paper's first stage of two-stage extraction.

    IMPORTANT: If the context does not contain sufficient information to answer
    the question, clearly state in your analysis that the question cannot be
    answered from the given context.
    """

    question: str = dspy.InputField(
        desc="ESG question requiring document analysis (e.g., emissions, climate targets, governance)"
    )
    context: str = dspy.InputField(
        desc="Retrieved document chunks (top-5 from ColBERT semantic search)"
    )
    doc_id: str = dspy.InputField(
        desc="Source document identifier (e.g., 'AR6 Synthesis Report Climate Change 2023.pdf')"
    )

    analysis: str = dspy.OutputField(
        desc="Detailed reasoning and analysis based on the provided context. "
             "Should explain the answer and reference specific information from the context. "
             "If context lacks sufficient information, clearly state the question cannot be answered."
    )


# ============================================================================
# Stage 2: Answer Extraction from Analysis
# ============================================================================

class AnswerExtraction(dspy.Signature):
    """
    Extract structured answer from free-form analysis following MMESGBench format.

    This signature implements the second stage of MMESGBench's two-stage extraction:
    - Takes the free-form analysis from Stage 1
    - Extracts the final answer in the required format (Int, Float, Str, List)
    - Follows exact MMESGBench extraction prompt guidelines

    Based on: MMESGBench/src/eval/prompt_for_answer_extraction.md
    """

    question: str = dspy.InputField(
        desc="Original ESG question"
    )
    analysis: str = dspy.InputField(
        desc="Free-form reasoning and analysis from Stage 1"
    )
    answer_format: str = dspy.InputField(
        desc="Expected answer format: one of [Int, Float, Str, List]"
    )

    extracted_answer: str = dspy.OutputField(
        desc="Extracted answer in the required format. "
             "For Int: just the number (e.g., '2050'). "
             "For Float: number with decimals (e.g., '19.62'). "
             "For Str: concise text (e.g., 'North America'). "
             "For List: JSON array format (e.g., '[\"Africa\", \"Asia\"]'). "
             "If cannot answer: 'Not answerable'. "
             "If analysis lacks info: 'Fail to answer'."
    )


# ============================================================================
# Alternative Signatures (for experimentation)
# ============================================================================

class ESGReasoningWithChainOfThought(dspy.Signature):
    """
    Extended reasoning signature with explicit chain-of-thought prompting.
    Can be used as alternative to basic ESGReasoning for optimization experiments.
    """

    question: str = dspy.InputField()
    context: str = dspy.InputField()
    doc_id: str = dspy.InputField()

    rationale: str = dspy.OutputField(
        desc="Step-by-step reasoning process"
    )
    analysis: str = dspy.OutputField(
        desc="Final analysis based on the rationale"
    )


# ============================================================================
# Utility Functions
# ============================================================================

def validate_answer_format(answer: str, expected_format: str) -> bool:
    """
    Validate that extracted answer matches expected format.

    Args:
        answer: Extracted answer string
        expected_format: One of ['Int', 'Float', 'Str', 'List']

    Returns:
        True if format matches, False otherwise
    """
    if expected_format == "Int":
        try:
            int(float(answer))
            return True
        except (ValueError, TypeError):
            return answer in ["Not answerable", "Fail to answer"]

    elif expected_format == "Float":
        try:
            float(answer)
            return True
        except (ValueError, TypeError):
            return answer in ["Not answerable", "Fail to answer"]

    elif expected_format == "List":
        # Check if it looks like a list (starts with [)
        return answer.startswith('[') or answer in ["Not answerable", "Fail to answer"]

    elif expected_format == "Str":
        return isinstance(answer, str)

    return False


if __name__ == "__main__":
    print("=" * 60)
    print("DSPy Signatures for MMESGBench RAG")
    print("=" * 60)

    print("\n✅ Signatures defined:")
    print("   1. ESGReasoning - Stage 1: Generate analysis from context")
    print("   2. AnswerExtraction - Stage 2: Extract structured answer")
    print("   3. ESGReasoningWithChainOfThought - Alternative with explicit CoT")

    print("\n📋 Signature details:")
    print("\nESGReasoning:")
    print(f"   Inputs: question, context, doc_id")
    print(f"   Output: analysis")

    print("\nAnswerExtraction:")
    print(f"   Inputs: question, analysis, answer_format")
    print(f"   Output: extracted_answer")

    print("\n✅ Ready for RAG module implementation!")
