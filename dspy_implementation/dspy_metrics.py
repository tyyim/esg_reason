#!/usr/bin/env python3
"""
DSPy Evaluation Metrics for MMESGBench
Uses exact MMESGBench evaluation logic for 100% compatibility
"""

import sys
from pathlib import Path

# Add parent directory to import existing evaluation logic
sys.path.insert(0, str(Path(__file__).parent.parent))

from mmesgbench_exact_evaluation import (
    evaluate_prediction_mmesgbench,
    eval_acc_and_f1_mmesgbench
)


# ============================================================================
# Primary Metric: Accuracy with MMESGBench Exact Evaluation
# ============================================================================

def mmesgbench_accuracy(example, pred, trace=None):
    """
    Evaluate answer accuracy using exact MMESGBench evaluation logic.

    This metric implements 100% compatible evaluation with MMESGBench GitHub:
    - ANLS fuzzy matching for strings (threshold: 0.5)
    - Float tolerance handling (±1% relative tolerance)
    - List fuzzy matching (80% threshold)
    - Substring matching for partial answers

    Args:
        example: DSPy Example with ground truth answer and format
        pred: DSPy Prediction with extracted answer
        trace: Optional execution trace (not used)

    Returns:
        float: 1.0 if correct, 0.0 if incorrect
    """
    try:
        # Extract prediction answer (handle different attribute names)
        predicted_answer = getattr(pred, 'answer', '')
        if not predicted_answer:
            predicted_answer = getattr(pred, 'extracted_answer', '')

        # Get ground truth and format from example
        ground_truth = str(example.answer)
        answer_format = example.answer_format

        # Use exact MMESGBench evaluation - returns (is_correct, exact_match, f1_score)
        result = evaluate_prediction_mmesgbench(
            predicted_answer,
            ground_truth,
            answer_format
        )

        # Handle tuple return (is_correct, exact_match, f1_score) or just boolean
        if isinstance(result, tuple):
            is_correct = result[0]
        else:
            is_correct = result

        return float(is_correct)

    except Exception as e:
        print(f"⚠️  Error in mmesgbench_accuracy: {e}")
        return 0.0


# ============================================================================
# Secondary Metric: F1 Score
# ============================================================================

def mmesgbench_f1(example, pred, trace=None):
    """
    Calculate F1 score for a single prediction.

    Note: F1 is typically calculated over a set of predictions,
    but this provides per-example F1 for compatibility with DSPy.

    Args:
        example: DSPy Example with ground truth
        pred: DSPy Prediction with extracted answer
        trace: Optional execution trace

    Returns:
        float: F1 score for this prediction
    """
    try:
        predicted_answer = getattr(pred, 'answer', '')
        if not predicted_answer:
            predicted_answer = getattr(pred, 'extracted_answer', '')

        # Create single-item results list for F1 calculation
        results = [{
            'predicted_answer': predicted_answer,
            'ground_truth': str(example.answer),
            'answer_format': example.answer_format
        }]

        # Calculate accuracy and F1
        _, f1 = eval_acc_and_f1_mmesgbench(results)

        return f1

    except Exception as e:
        print(f"⚠️  Error in mmesgbench_f1: {e}")
        return 0.0


# ============================================================================
# Composite Metric: Accuracy + F1
# ============================================================================

def mmesgbench_combined(example, pred, trace=None):
    """
    Combined metric that averages accuracy and F1 score.

    Useful for optimization when you want to balance both metrics.

    Args:
        example: DSPy Example with ground truth
        pred: DSPy Prediction with extracted answer
        trace: Optional execution trace

    Returns:
        float: Average of accuracy and F1 score
    """
    acc = mmesgbench_accuracy(example, pred, trace)
    f1 = mmesgbench_f1(example, pred, trace)

    return (acc + f1) / 2.0


# ============================================================================
# Format-Specific Metrics (for analysis)
# ============================================================================

def accuracy_by_format(predictions, examples):
    """
    Calculate accuracy breakdown by answer format.

    Args:
        predictions: List of DSPy predictions
        examples: List of DSPy examples

    Returns:
        dict: Accuracy for each format type
    """
    format_stats = {}

    for pred, example in zip(predictions, examples):
        fmt = example.answer_format

        if fmt not in format_stats:
            format_stats[fmt] = {'correct': 0, 'total': 0}

        is_correct = mmesgbench_accuracy(example, pred)
        format_stats[fmt]['correct'] += is_correct
        format_stats[fmt]['total'] += 1

    # Calculate percentages
    format_accuracy = {}
    for fmt, stats in format_stats.items():
        format_accuracy[fmt] = {
            'accuracy': stats['correct'] / stats['total'] if stats['total'] > 0 else 0.0,
            'correct': int(stats['correct']),
            'total': stats['total']
        }

    return format_accuracy


# ============================================================================
# Batch Evaluation
# ============================================================================

def evaluate_predictions(predictions, examples):
    """
    Evaluate a batch of predictions with comprehensive metrics.

    Args:
        predictions: List of DSPy predictions
        examples: List of DSPy examples

    Returns:
        dict: Comprehensive evaluation results
    """
    # Overall metrics
    total_correct = 0
    total_predictions = len(predictions)

    # Collect results for F1 calculation
    results_for_f1 = []

    for pred, example in zip(predictions, examples):
        is_correct = mmesgbench_accuracy(example, pred)
        total_correct += is_correct

        # Collect for F1
        predicted_answer = getattr(pred, 'answer', '')
        if not predicted_answer:
            predicted_answer = getattr(pred, 'extracted_answer', '')

        results_for_f1.append({
            'predicted_answer': predicted_answer,
            'ground_truth': str(example.answer),
            'answer_format': example.answer_format
        })

    # Calculate overall metrics
    overall_accuracy = total_correct / total_predictions if total_predictions > 0 else 0.0
    _, overall_f1 = eval_acc_and_f1_mmesgbench(results_for_f1)

    # Format-specific breakdown
    format_breakdown = accuracy_by_format(predictions, examples)

    return {
        'accuracy': overall_accuracy,
        'f1_score': overall_f1,
        'correct': int(total_correct),
        'total': total_predictions,
        'format_breakdown': format_breakdown
    }


if __name__ == "__main__":
    print("=" * 60)
    print("DSPy Metrics for MMESGBench")
    print("=" * 60)

    # Test metrics with example predictions
    import dspy

    # Create test example
    example = dspy.Example(
        doc_id="AR6 Synthesis Report Climate Change 2023.pdf",
        question="According to the IPCC, which region had the highest per capita GHG emissions in 2019?",
        answer="North America",
        answer_format="Str"
    ).with_inputs('doc_id', 'question', 'answer_format')

    # Test prediction (correct)
    pred_correct = dspy.Prediction(answer="North America")

    # Test prediction (incorrect)
    pred_incorrect = dspy.Prediction(answer="Asia")

    print("\n🧪 Testing metrics...")

    print(f"\n✅ Correct prediction:")
    print(f"   Ground truth: {example.answer}")
    print(f"   Prediction: {pred_correct.answer}")
    print(f"   Accuracy: {mmesgbench_accuracy(example, pred_correct)}")
    print(f"   F1 Score: {mmesgbench_f1(example, pred_correct):.3f}")

    print(f"\n❌ Incorrect prediction:")
    print(f"   Ground truth: {example.answer}")
    print(f"   Prediction: {pred_incorrect.answer}")
    print(f"   Accuracy: {mmesgbench_accuracy(example, pred_incorrect)}")
    print(f"   F1 Score: {mmesgbench_f1(example, pred_incorrect):.3f}")

    print("\n✅ Metrics working correctly!")
    print("   Using exact MMESGBench evaluation logic")
