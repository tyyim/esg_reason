#!/usr/bin/env python3
"""
NEW Qwen Baseline Evaluation on Training Set
PostgreSQL + Qwen text-embedding-v4 (replacing SentenceTransformer baseline)
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


def run_qwen_baseline_train(max_questions=None):
    """
    Run NEW baseline evaluation on training set with Qwen embeddings.

    Args:
        max_questions: Optional limit for quick testing

    Returns:
        dict: Evaluation results
    """
    print("=" * 80)
    print("NEW Qwen Baseline Evaluation - Training Set")
    print("PostgreSQL + Qwen text-embedding-v4")
    print("=" * 80)

    # Initialize DSPy with Qwen Max
    print("\n📋 Setting up DSPy environment...")
    setup_dspy_qwen()

    # Load dataset
    print("📊 Loading MMESGBench dataset with corrections...")
    dataset = MMESGBenchDataset()

    # Use training set
    eval_set = dataset.train_set
    set_name = "Train Set"
    expected_count = 178

    if max_questions:
        eval_set = eval_set[:max_questions]

    print(f"\n🎯 Evaluating on {set_name}")
    print(f"   Questions: {len(eval_set)}/{expected_count}")
    print(f"   Embeddings: Qwen text-embedding-v4 (1024-dim)")
    print(f"   Vector Store: PostgreSQL + pgvector")
    print(f"   Documents: 44/45 (95.5% coverage, IPCC indexing in progress)")
    print(f"   Previous baseline (SentenceTransformer): 45.1%")

    # Initialize RAG module
    print("\n🚀 Initializing MMESGBenchRAG module...")
    rag = MMESGBenchRAG()

    # Check for checkpoint
    checkpoint_file = "qwen_baseline_train_checkpoint.json"
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
                    json.dump({
                        'predictions': [
                            {
                                'answer': p.answer,
                                'analysis': getattr(p, 'analysis', ''),
                                'context': getattr(p, 'context', '')
                            } for p in predictions
                        ]
                    }, f)
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
    print("QWEN BASELINE EVALUATION RESULTS - TRAINING SET")
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
    previous_baseline = 0.451  # 45.1% with SentenceTransformer
    diff = results['accuracy'] - previous_baseline

    print(f"\n📈 Baseline Comparison:")
    print(f"   Previous (SentenceTransformer): {previous_baseline:.1%}")
    print(f"   NEW (Qwen embeddings):         {results['accuracy']:.1%}")
    print(f"   Difference:                     {diff:+.1%}")

    if diff >= 0:
        print(f"   ✅ IMPROVEMENT with Qwen embeddings")
    else:
        print(f"   ⚠️  Slight decrease (may improve with IPCC document)")

    # Save detailed results
    output_file = "qwen_baseline_train_results.json"

    detailed_results = {
        "evaluation_set": set_name,
        "num_questions": len(eval_set),
        "embeddings": "Qwen text-embedding-v4 (1024-dim)",
        "vector_store": "PostgreSQL + pgvector",
        "documents_indexed": "44/45 (95.5% coverage)",
        "overall_metrics": {
            "accuracy": results['accuracy'],
            "f1_score": results['f1_score'],
            "correct": results['correct'],
            "total": results['total']
        },
        "format_breakdown": results['format_breakdown'],
        "baseline_comparison": {
            "previous_baseline": previous_baseline,
            "new_baseline": results['accuracy'],
            "difference": diff,
            "improvement": diff >= 0
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

    parser = argparse.ArgumentParser(description="Run Qwen baseline evaluation on training set")
    parser.add_argument(
        "--max-questions",
        type=int,
        default=None,
        help="Maximum number of questions to evaluate (for quick testing)"
    )

    args = parser.parse_args()

    # Run evaluation
    results = run_qwen_baseline_train(max_questions=args.max_questions)

    print("\n✅ NEW Qwen baseline evaluation complete!")
    print(f"   Achieved: {results['accuracy']:.1%} accuracy")
    print("   Ready for MIPROv2 optimization")
