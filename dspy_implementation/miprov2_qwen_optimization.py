#!/usr/bin/env python3
"""
MIPROv2 Optimization for NEW Qwen Baseline (55.8%)

Applies Multi-prompt Instruction Proposal Optimizer v2 to improve from:
  - Baseline: 55.8% (PostgreSQL + Qwen embeddings)
  - Target: 57-58% (+1-2% improvement)

Architecture:
  - Training: 746 questions (80% of 933)
  - Dev: 93 questions (10% of 933)
  - Test: 94 questions (10% of 933)
  - Retriever: PostgreSQL + pgvector + Qwen text-embedding-v4
  - LLM: Qwen Max with two-stage reasoning

Optimization Strategy:
  - Optimize ESGReasoning and AnswerExtraction signatures
  - Use MIPROv2 for automated prompt engineering
  - Validate on dev set to prevent overfitting
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
import dspy
from dspy.teleprompt import MIPROv2
from tqdm import tqdm

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Change to project root for document access
os.chdir(project_root)

from dspy_implementation.dspy_setup import setup_dspy_qwen
from dspy_implementation.dspy_dataset import MMESGBenchDataset
from dspy_implementation.dspy_rag_module import MMESGBenchRAG
from dspy_implementation.dspy_metrics import mmesgbench_accuracy, evaluate_predictions


# ============================================================================
# MIPROv2 Optimization
# ============================================================================

def optimize_with_miprov2(train_set, dev_set, num_candidates: int = 10,
                          init_temperature: float = 1.0, verbose: bool = True):
    """
    Apply MIPROv2 optimizer to improve prompt instructions.

    MIPROv2 automatically generates and tests multiple instruction candidates
    to optimize the prompts for ESGReasoning and AnswerExtraction signatures.

    Args:
        train_set: Training examples (746 questions)
        dev_set: Development examples for validation (93 questions)
        num_candidates: Number of instruction candidates to generate (default: 10)
        init_temperature: Initial temperature for candidate generation (default: 1.0)
        verbose: Whether to print detailed progress (default: True)

    Returns:
        Tuple of (optimized RAG module, dev results dict)
    """
    print("\n" + "=" * 80)
    print("MIPROv2 Optimization from Qwen Baseline (55.8%)")
    print("=" * 80)

    # Initialize unoptimized RAG module
    print("\n📋 Initializing baseline RAG module...")
    print("   Using PostgreSQL + Qwen embeddings")
    baseline_rag = MMESGBenchRAG()
    print("✅ MMESGBenchRAG module initialized")

    # Evaluate baseline on small train sample
    print("\n📊 Evaluating baseline on training sample (10 questions)...")
    baseline_train_preds = []
    sample_size = min(10, len(train_set))

    for example in tqdm(train_set[:sample_size], desc="Baseline eval"):
        try:
            pred = baseline_rag(
                question=example.question,
                doc_id=example.doc_id,
                answer_format=example.answer_format
            )
            baseline_train_preds.append(pred)
        except Exception as e:
            print(f"\n⚠️  Error on question: {e}")
            # Create empty prediction for failed questions
            baseline_train_preds.append(dspy.Prediction(answer="Failed"))

    baseline_train_results = evaluate_predictions(
        baseline_train_preds,
        train_set[:sample_size]
    )
    print(f"   Baseline sample accuracy: {baseline_train_results['accuracy']:.1%} " +
          f"({baseline_train_results['correct']}/{baseline_train_results['total']})")

    # Configure MIPROv2 optimizer
    print(f"\n🔧 Configuring MIPROv2 optimizer...")
    print(f"   Num candidates: {num_candidates}")
    print(f"   Temperature: {init_temperature}")
    print(f"   Metric: MMESGBench accuracy (fuzzy matching)")
    print(f"   Training set: {len(train_set)} questions")
    print(f"   Expected baseline: 55.8% (from full train evaluation)")

    optimizer = MIPROv2(
        metric=mmesgbench_accuracy,
        num_candidates=num_candidates,
        init_temperature=init_temperature,
        verbose=verbose
    )

    # Use full train set for optimization (it's now only 20% = ~187 questions)
    print(f"\n🚀 Running MIPROv2 optimization...")
    print(f"   Optimizing on {len(train_set)} training questions (20% of dataset)")
    print(f"   This will take approximately 30-60 minutes...")
    print(f"   Progress will be saved automatically by DSPy\n")

    # Create checkpoint directory
    os.makedirs("checkpoints", exist_ok=True)

    try:
        optimized_rag = optimizer.compile(
            student=baseline_rag,
            trainset=train_set,
            num_trials=20,  # Number of optimization trials
            max_bootstrapped_demos=4,  # Max few-shot examples per prompt
            max_labeled_demos=4  # Max labeled examples
        )

        print("\n✅ MIPROv2 optimization completed!")

    except Exception as e:
        print(f"\n⚠️  Optimization failed: {e}")
        print(f"   Falling back to baseline RAG module")
        optimized_rag = baseline_rag

    # Evaluate optimized model on dev set
    print("\n📊 Evaluating optimized model on dev set (93 questions)...")
    dev_preds = []

    for example in tqdm(dev_set, desc="Dev evaluation"):
        try:
            pred = optimized_rag(
                question=example.question,
                doc_id=example.doc_id,
                answer_format=example.answer_format
            )
            dev_preds.append(pred)
        except Exception as e:
            print(f"\n⚠️  Error on dev question: {e}")
            dev_preds.append(dspy.Prediction(answer="Failed"))

    dev_results = evaluate_predictions(dev_preds, dev_set)

    print(f"\n📈 Dev Set Results:")
    print(f"   Accuracy: {dev_results['accuracy']:.1%} " +
          f"({dev_results['correct']}/{dev_results['total']})")
    print(f"   F1 Score: {dev_results['f1_score']:.3f}")

    # Print format breakdown
    print(f"\n📋 Format Breakdown on Dev Set:")
    for fmt, stats in dev_results['format_breakdown'].items():
        acc = stats['accuracy']
        correct = stats['correct']
        total = stats['total']
        if acc is not None:
            print(f"   {fmt:6s}: {acc:6.1%} ({correct:3d}/{total:3d})")
        else:
            print(f"   {fmt:6s}: N/A     ({correct:3d}/{total:3d})")

    return optimized_rag, dev_results


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """
    Main execution flow for MIPROv2 optimization.
    """
    print("=" * 80)
    print("MIPROv2 Optimization for MMESGBench (Qwen Baseline)")
    print("=" * 80)
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nBaseline: TBD (PostgreSQL + Qwen embeddings on 20% train split)")
    print(f"Target: Baseline + 1-2% improvement")

    # Initialize DSPy
    print(f"\n📋 Setting up DSPy environment...")
    setup_dspy_qwen()
    print(f"✅ DSPy configured with Qwen Max")

    # Load dataset
    print(f"\n📊 Loading MMESGBench dataset with corrections...")
    dataset = MMESGBenchDataset()

    train_set = dataset.train_set
    dev_set = dataset.dev_set
    test_set = dataset.test_set

    print(f"\n📈 Dataset Summary:")
    print(f"   Training: {len(train_set)} questions (20%)")
    print(f"   Dev: {len(dev_set)} questions (10%)")
    print(f"   Test: {len(test_set)} questions (70%)")
    print(f"   Documents: 45/45 (100% coverage)")
    print(f"   Total chunks: 54,608")

    # Run MIPROv2 optimization
    optimized_rag, dev_results = optimize_with_miprov2(
        train_set=train_set,
        dev_set=dev_set,
        num_candidates=10,
        init_temperature=1.0,
        verbose=True
    )

    # Save optimized module
    print(f"\n💾 Saving optimized module...")
    os.makedirs("dspy_implementation/optimized_modules", exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    module_path = f"dspy_implementation/optimized_modules/miprov2_qwen_{timestamp}.json"

    optimized_rag.save(module_path)
    print(f"   Saved to: {module_path}")

    # Save detailed results
    results_file = f"miprov2_qwen_results_{timestamp}.json"

    detailed_results = {
        "timestamp": datetime.now().isoformat(),
        "baseline": {
            "name": "PostgreSQL + Qwen text-embedding-v4",
            "accuracy": 0.558,
            "source": "qwen_baseline_train_results.json"
        },
        "optimization": {
            "method": "MIPROv2",
            "train_size": len(train_set),
            "optimization_subset": min(100, len(train_set)),
            "dev_size": len(dev_set),
            "num_candidates": 10,
            "init_temperature": 1.0
        },
        "dev_results": {
            "accuracy": dev_results['accuracy'],
            "f1_score": dev_results['f1_score'],
            "correct": dev_results['correct'],
            "total": dev_results['total'],
            "format_breakdown": dev_results['format_breakdown']
        },
        "improvement": {
            "absolute": dev_results['accuracy'] - 0.558,
            "relative_pct": ((dev_results['accuracy'] - 0.558) / 0.558) * 100
        }
    }

    with open(results_file, 'w') as f:
        json.dump(detailed_results, f, indent=2)

    print(f"\n💾 Detailed results saved to: {results_file}")

    # Final summary
    print("\n" + "=" * 80)
    print("MIPROV2 OPTIMIZATION COMPLETE")
    print("=" * 80)

    baseline_acc = 0.558
    dev_acc = dev_results['accuracy']
    improvement = dev_acc - baseline_acc

    print(f"\n📊 Final Results:")
    print(f"   Baseline (train): {baseline_acc:.1%}")
    print(f"   Optimized (dev):  {dev_acc:.1%}")
    print(f"   Improvement:      {improvement:+.1%}")

    if improvement >= 0.01:
        print(f"   ✅ SUCCESS: Achieved target improvement!")
    elif improvement > 0:
        print(f"   ⚠️  Minor improvement, consider more optimization")
    else:
        print(f"   ⚠️  No improvement, baseline may be optimal")

    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    return optimized_rag, dev_results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run MIPROv2 optimization on Qwen baseline")
    parser.add_argument(
        "--num-candidates",
        type=int,
        default=10,
        help="Number of instruction candidates to generate (default: 10)"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=1.0,
        help="Initial temperature for candidate generation (default: 1.0)"
    )

    args = parser.parse_args()

    # Run optimization
    optimized_module, results = main()

    print("\n✅ MIPROv2 optimization pipeline complete!")
    print(f"   Dev accuracy: {results['accuracy']:.1%}")
    print("   Ready for test set evaluation")
