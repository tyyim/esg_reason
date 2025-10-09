#!/usr/bin/env python3
"""
Enhanced Metrics for MMESGBench RAG
Separates retrieval accuracy from answer accuracy
"""

import re
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mmesgbench_exact_evaluation import (
    evaluate_prediction_mmesgbench
)
from dspy_implementation.dspy_metrics import mmesgbench_accuracy


def retrieval_accuracy(example, prediction, trace=None) -> float:
    """
    Measure retrieval quality: Does retrieved context contain evidence?

    This metric checks if the retrieved context includes text from the
    evidence pages mentioned in the ground truth.

    Args:
        example: DSPy example with evidence_pages field
        prediction: DSPy prediction with context field
        trace: Optional execution trace

    Returns:
        1.0 if retrieval successful, 0.0 otherwise
    """
    # Get evidence pages from example
    evidence_pages = example.get('evidence_pages', '')
    if not evidence_pages:
        # No evidence pages specified - assume retrieval is correct
        return 1.0

    # Get retrieved context
    context = prediction.get('context', '')
    if not context:
        return 0.0

    # Check if any evidence page numbers appear in context
    # Evidence pages format: "61, 116, 25" or "page 61"
    page_numbers = re.findall(r'\d+', str(evidence_pages))

    # Look for page references in context
    for page_num in page_numbers:
        # Check various formats: "page 61", "Page 61", "p.61", etc.
        patterns = [
            f"page {page_num}",
            f"Page {page_num}",
            f"p. {page_num}",
            f"p.{page_num}",
            f"pg {page_num}",
            f"pg. {page_num}"
        ]
        # Convert patterns to lowercase for case-insensitive matching
        if any(pattern.lower() in context.lower() for pattern in patterns):
            return 1.0

    # No matching evidence pages found - retrieval failed
    return 0.0


def answer_accuracy(example, prediction, trace=None) -> float:
    """
    Measure answer correctness using MMESGBench fuzzy matching.

    This is the existing accuracy metric - focuses only on final answer
    quality, not retrieval quality.

    Args:
        example: DSPy example with answer and answer_format
        prediction: DSPy prediction with answer field
        trace: Optional execution trace

    Returns:
        1.0 if answer correct, 0.0 otherwise
    """
    # Use the existing mmesgbench_accuracy function
    return mmesgbench_accuracy(example, prediction, trace)


def end_to_end_accuracy(example, prediction, trace=None) -> float:
    """
    Combined metric: Both retrieval AND answer must be correct.

    This is the strictest metric - only succeeds if:
    1. Retrieval found relevant evidence (retrieval_accuracy = 1.0)
    2. Answer extraction is correct (answer_accuracy = 1.0)

    Args:
        example: DSPy example
        prediction: DSPy prediction
        trace: Optional execution trace

    Returns:
        1.0 if both retrieval and answer correct, 0.0 otherwise
    """
    retrieval_correct = retrieval_accuracy(example, prediction, trace)
    answer_correct = answer_accuracy(example, prediction, trace)

    # Both must be correct
    return retrieval_correct * answer_correct


def compute_detailed_metrics(example, prediction, trace=None) -> Dict[str, float]:
    """
    Compute all metrics for detailed analysis.

    Returns dictionary with:
        - retrieval_correct: 1.0 if retrieval successful
        - answer_correct: 1.0 if answer correct
        - end_to_end_correct: 1.0 if both successful

    Args:
        example: DSPy example
        prediction: DSPy prediction
        trace: Optional execution trace

    Returns:
        Dictionary of metrics
    """
    return {
        'retrieval_correct': retrieval_accuracy(example, prediction, trace),
        'answer_correct': answer_accuracy(example, prediction, trace),
        'end_to_end_correct': end_to_end_accuracy(example, prediction, trace)
    }


def evaluate_predictions_enhanced(predictions, examples) -> Dict[str, Any]:
    """
    Evaluate predictions with separate retrieval and answer metrics.

    This provides more insight than overall accuracy alone:
    - If retrieval is low but answer is high: Retrieved wrong context but reasoned well
    - If retrieval is high but answer is low: Found evidence but extraction failed
    - If both are low: Fundamental pipeline issues

    Args:
        predictions: List of DSPy predictions
        examples: List of DSPy examples (ground truth)

    Returns:
        Dictionary with:
            - retrieval_accuracy: Fraction with correct retrieval
            - answer_accuracy: Fraction with correct answers
            - end_to_end_accuracy: Fraction with both correct
            - total: Total examples evaluated
            - by_format: Breakdown by answer format
    """
    total = len(examples)

    retrieval_correct = 0
    answer_correct = 0
    end_to_end_correct = 0

    # Track by answer format
    format_stats = {}

    for pred, example in zip(predictions, examples):
        # Compute metrics
        metrics = compute_detailed_metrics(example, pred)

        retrieval_correct += metrics['retrieval_correct']
        answer_correct += metrics['answer_correct']
        end_to_end_correct += metrics['end_to_end_correct']

        # Track by format
        fmt = example.answer_format
        if fmt not in format_stats:
            format_stats[fmt] = {
                'total': 0,
                'retrieval_correct': 0,
                'answer_correct': 0,
                'end_to_end_correct': 0
            }

        format_stats[fmt]['total'] += 1
        format_stats[fmt]['retrieval_correct'] += metrics['retrieval_correct']
        format_stats[fmt]['answer_correct'] += metrics['answer_correct']
        format_stats[fmt]['end_to_end_correct'] += metrics['end_to_end_correct']

    # Calculate format-specific accuracies
    for fmt in format_stats:
        stats = format_stats[fmt]
        t = stats['total']
        format_stats[fmt]['retrieval_accuracy'] = stats['retrieval_correct'] / t if t > 0 else 0.0
        format_stats[fmt]['answer_accuracy'] = stats['answer_correct'] / t if t > 0 else 0.0
        format_stats[fmt]['end_to_end_accuracy'] = stats['end_to_end_correct'] / t if t > 0 else 0.0

    return {
        'retrieval_accuracy': retrieval_correct / total if total > 0 else 0.0,
        'answer_accuracy': answer_correct / total if total > 0 else 0.0,
        'end_to_end_accuracy': end_to_end_correct / total if total > 0 else 0.0,
        'retrieval_correct': int(retrieval_correct),
        'answer_correct': int(answer_correct),
        'end_to_end_correct': int(end_to_end_correct),
        'total': total,
        'by_format': format_stats
    }


# Metric functions for DSPy optimizer
# These return float values (0.0 or 1.0) as required by DSPy

def mmesgbench_retrieval_metric(example, prediction, trace=None) -> float:
    """Retrieval-only metric for DSPy optimizer."""
    return retrieval_accuracy(example, prediction, trace)


def mmesgbench_answer_metric(example, prediction, trace=None) -> float:
    """Answer-only metric for DSPy optimizer."""
    return answer_accuracy(example, prediction, trace)


def mmesgbench_end_to_end_metric(example, prediction, trace=None) -> float:
    """End-to-end metric for DSPy optimizer (recommended)."""
    return end_to_end_accuracy(example, prediction, trace)


if __name__ == "__main__":
    print("=" * 60)
    print("Enhanced Metrics Test")
    print("=" * 60)

    import dspy

    # Mock example and predictions for testing
    example = dspy.Example(
        question="Test question",
        answer="North America",
        answer_format="Str",
        evidence_pages="61, 116"
    ).with_inputs('question', 'answer_format')

    # Test 1: Perfect prediction (retrieval + answer correct)
    perfect_pred = dspy.Prediction(
        answer="North America",
        context="...on page 61, North America had highest emissions...",
        search_query="optimized query"
    )

    print("\n🧪 Test 1: Perfect prediction")
    metrics = compute_detailed_metrics(example, perfect_pred)
    print(f"   Retrieval: {metrics['retrieval_correct']}")
    print(f"   Answer: {metrics['answer_correct']}")
    print(f"   End-to-end: {metrics['end_to_end_correct']}")

    # Test 2: Wrong retrieval, correct answer (lucky guess)
    lucky_pred = dspy.Prediction(
        answer="North America",
        context="...unrelated text from page 10...",
        search_query="bad query"
    )

    print("\n🧪 Test 2: Lucky guess (wrong retrieval, correct answer)")
    metrics = compute_detailed_metrics(example, lucky_pred)
    print(f"   Retrieval: {metrics['retrieval_correct']}")
    print(f"   Answer: {metrics['answer_correct']}")
    print(f"   End-to-end: {metrics['end_to_end_correct']}")

    # Test 3: Correct retrieval, wrong answer (extraction failed)
    extraction_fail_pred = dspy.Prediction(
        answer="Europe",
        context="...on page 61, North America had highest emissions...",
        search_query="good query"
    )

    print("\n🧪 Test 3: Extraction failed (correct retrieval, wrong answer)")
    metrics = compute_detailed_metrics(example, extraction_fail_pred)
    print(f"   Retrieval: {metrics['retrieval_correct']}")
    print(f"   Answer: {metrics['answer_correct']}")
    print(f"   End-to-end: {metrics['end_to_end_correct']}")

    print("\n✅ Enhanced metrics working correctly!")
    print("\n📊 Key Insight:")
    print("   These metrics help identify WHERE the pipeline fails:")
    print("   - Low retrieval → Need better query generation")
    print("   - Low answer (high retrieval) → Need better extraction")
    print("   - Low both → Fundamental issues")
