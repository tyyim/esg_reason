#!/usr/bin/env python3
"""
DSPy Baseline Evaluation for MMESGBench
Validates that DSPy implementation matches 41.3% accuracy baseline
"""

import sys
import json
import os
from pathlib import Path
from tqdm import tqdm

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Change to project root for document access
os.chdir(project_root)

from dspy_implementation.dspy_setup import setup_dspy_qwen
from dspy_implementation.dspy_dataset import MMESGBenchDataset
from dspy_implementation.dspy_rag_module import MMESGBenchRAG
from dspy_implementation.dspy_metrics import evaluate_predictions


def run_baseline_evaluation(use_dev_set=True, max_questions=None):
    """
    Run baseline evaluation on dev or test set.

    Args:
        use_dev_set: If True, use dev set (93 questions), else test set (94 questions)
        max_questions: Optional limit for quick testing

    Returns:
        dict: Evaluation results
    """
    print("=" * 80)
    print("DSPy Baseline Evaluation - MMESGBench")
    print("=" * 80)

    # Initialize DSPy with Qwen Max
    print("\n📋 Setting up DSPy environment...")
    setup_dspy_qwen()

    # Load dataset
    print("📊 Loading MMESGBench dataset with corrections...")
    dataset = MMESGBenchDataset()

    # Select evaluation set
    if use_dev_set:
        eval_set = dataset.dev_set
        set_name = "Dev Set"
        expected_count = 93
    else:
        eval_set = dataset.test_set
        set_name = "Test Set"
        expected_count = 94

    if max_questions:
        eval_set = eval_set[:max_questions]

    print(f"\n🎯 Evaluating on {set_name}")
    print(f"   Questions: {len(eval_set)}/{expected_count}")
    print(f"   Target accuracy: 41.3% (385/933 on full dataset)")

    # Initialize RAG module
    print("\n🚀 Initializing MMESGBenchRAG module...")
    rag = MMESGBenchRAG()

    # Check for checkpoint
    checkpoint_file = f"dspy_baseline_{'dev' if use_dev_set else 'test'}_checkpoint.json"
    if os.path.exists(checkpoint_file):
        print(f"\n📂 Found checkpoint: {checkpoint_file}")
        with open(checkpoint_file, 'r') as f:
            checkpoint = json.load(f)
        predictions = checkpoint.get('predictions', [])
        start_idx = len(predictions)
        print(f"   Resuming from question {start_idx + 1}/{len(eval_set)}")
    else:
        predictions = []
        start_idx = 0

    # Run evaluation
    print(f"\n🔄 Running evaluation on {len(eval_set)} questions...")
    print("   This may take several minutes...\n")

    examples = []

    for i, example in enumerate(tqdm(eval_set[start_idx:], desc="Evaluating", initial=start_idx, total=len(eval_set))):
        try:
            # Run RAG pipeline
            pred = rag(
                question=example.question,
                doc_id=example.doc_id,
                answer_format=example.answer_format
            )

            predictions.append(pred)
            examples.append(example)

            # Save checkpoint every 10 questions
            if (len(predictions)) % 10 == 0:
                with open(checkpoint_file, 'w') as f:
                    json.dump({'predictions': [vars(p) for p in predictions]}, f)
                tqdm.write(f"   ✓ Checkpoint saved: {len(predictions)}/{len(eval_set)} questions")

        except Exception as e:
            print(f"\n⚠️  Error on question {start_idx + i + 1}: {e}")
            # Create empty prediction for failed questions
            import dspy
            predictions.append(dspy.Prediction(answer="Failed to generate"))
            examples.append(example)

    # Ensure we have examples for all predictions
    if len(examples) < len(predictions):
        examples = eval_set[:len(predictions)]

    # Evaluate results
    print("\n📊 Computing evaluation metrics...")
    results = evaluate_predictions(predictions, examples)

    # Print detailed results
    print("\n" + "=" * 80)
    print("BASELINE EVALUATION RESULTS")
    print("=" * 80)

    print(f"\n🎯 Overall Performance:")
    print(f"   Accuracy: {results['accuracy']:.1%} ({results['correct']}/{results['total']})")
    print(f"   F1 Score: {results['f1_score']:.3f}")

    print(f"\n📋 Format Breakdown:")
    for fmt, stats in results['format_breakdown'].items():
        acc = stats['accuracy']
        correct = stats['correct']
        total = stats['total']
        print(f"   {fmt:6s}: {acc:6.1%} ({correct:3d}/{total:3d})")

    # Baseline comparison
    baseline_acc = 0.413  # 41.3% with corrections
    diff = results['accuracy'] - baseline_acc

    print(f"\n📈 Baseline Comparison:")
    print(f"   Expected: {baseline_acc:.1%}")
    print(f"   Achieved: {results['accuracy']:.1%}")
    print(f"   Difference: {diff:+.1%}")

    if abs(diff) <= 0.005:  # Within ±0.5%
        print(f"   ✅ PASS: Within ±0.5% tolerance")
    else:
        print(f"   ⚠️  WARNING: Outside ±0.5% tolerance")

    # Save detailed results
    output_file = f"dspy_baseline_{'dev' if use_dev_set else 'test'}_results.json"

    detailed_results = {
        "evaluation_set": set_name,
        "num_questions": len(eval_set),
        "overall_metrics": {
            "accuracy": results['accuracy'],
            "f1_score": results['f1_score'],
            "correct": results['correct'],
            "total": results['total']
        },
        "format_breakdown": results['format_breakdown'],
        "baseline_comparison": {
            "expected_accuracy": baseline_acc,
            "achieved_accuracy": results['accuracy'],
            "difference": diff,
            "within_tolerance": abs(diff) <= 0.005
        },
        "predictions": [
            {
                "question": ex.question,
                "doc_id": ex.doc_id,
                "answer_format": ex.answer_format,
                "ground_truth": ex.answer,
                "predicted_answer": pred.answer,
                "correct": pred.answer == ex.answer
            }
            for ex, pred in zip(examples, predictions)
        ]
    }

    with open(output_file, 'w') as f:
        json.dump(detailed_results, f, indent=2)

    print(f"\n💾 Detailed results saved to: {output_file}")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run DSPy baseline evaluation")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Use test set instead of dev set"
    )
    parser.add_argument(
        "--max-questions",
        type=int,
        default=None,
        help="Maximum number of questions to evaluate (for quick testing)"
    )

    args = parser.parse_args()

    # Run evaluation
    results = run_baseline_evaluation(
        use_dev_set=not args.test,
        max_questions=args.max_questions
    )

    print("\n✅ Baseline evaluation complete!")
    print("   Ready for Stage 7: MIPROv2 optimization")
