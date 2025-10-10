#!/usr/bin/env python3
"""
Full Dataset Evaluation - Phase 1a Validation

Evaluates 3 approaches on full 933-question dataset:
1. Baseline RAG (no query optimization)
2. Enhanced RAG (with query gen, default prompts)
3. Optimized RAG (MIPROv2 light mode)

Expected runtime: ~3-4 hours total (933 questions)
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import dspy

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from dspy_implementation.dspy_setup import setup_dspy_qwen
from dspy_implementation.dspy_dataset import MMESGBenchDataset
from dspy_implementation.dspy_rag_enhanced import EnhancedMMESGBenchRAG, BaselineMMESGBenchRAG
from dspy_implementation.dspy_metrics_enhanced import evaluate_predictions_enhanced


def load_optimized_module(checkpoint_path: str):
    """Load optimized RAG module from checkpoint."""
    print(f"\n📦 Loading optimized module from: {checkpoint_path}")

    # Load the optimized RAG
    optimized_rag = EnhancedMMESGBenchRAG(enable_query_optimization=True)

    try:
        # Try to load compiled module if available
        optimized_rag.load(checkpoint_path)
        print("   ✅ Loaded compiled module successfully")
    except Exception as e:
        print(f"   ⚠️  Could not load compiled module: {e}")
        print("   Using default enhanced RAG instead")

    return optimized_rag


def evaluate_approach(rag_module, dataset, approach_name: str, output_file: str):
    """Evaluate a RAG approach on full dataset."""

    print(f"\n{'='*80}")
    print(f"EVALUATING: {approach_name}")
    print(f"{'='*80}")
    print(f"Dataset size: {len(dataset)} questions")
    print(f"Output file: {output_file}")

    # Run predictions
    predictions = []
    for example in tqdm(dataset, desc=f"{approach_name}"):
        try:
            pred = rag_module(
                question=example.question,
                doc_id=example.doc_id,
                answer_format=example.answer_format
            )
            predictions.append(pred)
        except Exception as e:
            print(f"\n⚠️  Error on question {example.question[:50]}: {e}")
            predictions.append(dspy.Prediction(answer="ERROR"))

    # Evaluate
    results = evaluate_predictions_enhanced(predictions, dataset)

    # Save results
    detailed_results = {
        'approach': approach_name,
        'timestamp': datetime.now().isoformat(),
        'dataset_size': len(dataset),
        'overall_metrics': results,
        'predictions': [
            {
                'question': ex.question,
                'predicted_answer': pred.answer if hasattr(pred, 'answer') else None,
                'ground_truth': ex.answer,
                'doc_id': ex.doc_id,
                'answer_format': ex.answer_format,
                'evidence_pages': ex.evidence_pages
            }
            for ex, pred in zip(dataset, predictions)
        ]
    }

    with open(output_file, 'w') as f:
        json.dump(detailed_results, f, indent=2)

    print(f"\n✅ {approach_name} Evaluation Complete!")
    print(f"\n📊 Overall Results:")
    print(f"   Retrieval: {results['retrieval_accuracy']:.1%} ({results['retrieval_correct']}/{results['total']})")
    print(f"   Answer:    {results['answer_accuracy']:.1%} ({results['answer_correct']}/{results['total']})")
    print(f"   E2E:       {results['end_to_end_accuracy']:.1%} ({results['end_to_end_correct']}/{results['total']})")

    print(f"\n📋 Format Breakdown:")
    for fmt, stats in results['by_format'].items():
        fmt_str = str(fmt) if fmt is not None else "None"
        print(f"   {fmt_str:6s}: Retrieval={stats['retrieval_accuracy']:5.1%}, Answer={stats['answer_accuracy']:5.1%}, E2E={stats['end_to_end_accuracy']:5.1%}")

    return results


def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("="*80)
    print("FULL DATASET EVALUATION - Phase 1a Validation")
    print("="*80)
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Setup
    print("\n📋 Setting up DSPy environment...")
    setup_dspy_qwen()

    print("\n📊 Loading full dataset...")
    dataset = MMESGBenchDataset()
    full_dataset = dataset.train_set + dataset.dev_set + dataset.test_set  # All 933 questions
    print(f"✅ Loaded {len(full_dataset)} questions")

    # Create output directory
    results_dir = Path("dspy_implementation/full_dataset_results")
    results_dir.mkdir(exist_ok=True)

    # Approach 1: Baseline RAG (no query optimization)
    print("\n" + "="*80)
    print("APPROACH 1: Baseline RAG (No Query Optimization)")
    print("="*80)

    baseline_rag = BaselineMMESGBenchRAG()
    baseline_results = evaluate_approach(
        baseline_rag,
        full_dataset,
        "Baseline RAG (No Query Opt)",
        results_dir / f"baseline_results_{timestamp}.json"
    )

    # Approach 2: Enhanced RAG (default prompts)
    print("\n" + "="*80)
    print("APPROACH 2: Enhanced RAG (Query Gen, Default Prompts)")
    print("="*80)

    enhanced_rag = EnhancedMMESGBenchRAG(enable_query_optimization=True)
    enhanced_results = evaluate_approach(
        enhanced_rag,
        full_dataset,
        "Enhanced RAG (Default Prompts)",
        results_dir / f"enhanced_results_{timestamp}.json"
    )

    # Approach 3: Optimized RAG (light mode)
    print("\n" + "="*80)
    print("APPROACH 3: Optimized RAG (MIPROv2 Light Mode)")
    print("="*80)

    # Find latest optimized module
    optimized_modules = list(Path("dspy_implementation/optimized_modules").glob("enhanced_rag_*.json"))
    if optimized_modules:
        latest_module = max(optimized_modules, key=lambda p: p.stat().st_mtime)
        optimized_rag = load_optimized_module(str(latest_module))
    else:
        print("\n⚠️  No optimized module found, using enhanced RAG instead")
        optimized_rag = enhanced_rag

    optimized_results = evaluate_approach(
        optimized_rag,
        full_dataset,
        "Optimized RAG (Light Mode)",
        results_dir / f"optimized_results_{timestamp}.json"
    )

    # Final Comparison
    print("\n" + "="*80)
    print("FINAL COMPARISON - Full Dataset (933 questions)")
    print("="*80)

    comparison = {
        'baseline': baseline_results,
        'enhanced': enhanced_results,
        'optimized': optimized_results
    }

    print("\n📊 End-to-End Accuracy:")
    print(f"   Baseline:  {baseline_results['end_to_end_accuracy']:.1%} ({baseline_results['end_to_end_correct']}/933)")
    print(f"   Enhanced:  {enhanced_results['end_to_end_accuracy']:.1%} ({enhanced_results['end_to_end_correct']}/933)")
    print(f"   Optimized: {optimized_results['end_to_end_accuracy']:.1%} ({optimized_results['end_to_end_correct']}/933)")

    improvement_enhanced = enhanced_results['end_to_end_accuracy'] - baseline_results['end_to_end_accuracy']
    improvement_optimized = optimized_results['end_to_end_accuracy'] - baseline_results['end_to_end_accuracy']

    print(f"\n📈 Improvements:")
    print(f"   Enhanced vs Baseline:  {improvement_enhanced:+.1%}")
    print(f"   Optimized vs Baseline: {improvement_optimized:+.1%}")

    # Save comparison
    comparison_file = results_dir / f"comparison_{timestamp}.json"
    with open(comparison_file, 'w') as f:
        json.dump(comparison, f, indent=2)

    print(f"\n💾 All results saved to: {results_dir}/")
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)


if __name__ == "__main__":
    main()
