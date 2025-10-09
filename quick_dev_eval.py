#!/usr/bin/env python3
"""
Quick Dev Set Evaluation with Fixed Metrics
Evaluates baseline RAG on dev set to get true retrieval accuracy.
"""

import sys
from pathlib import Path
from tqdm import tqdm
import dspy

# Add parent directory
sys.path.insert(0, str(Path(__file__).parent))

from dspy_implementation.dspy_setup import setup_dspy_qwen
from dspy_implementation.dspy_dataset import MMESGBenchDataset
from dspy_implementation.dspy_rag_enhanced import BaselineMMESGBenchRAG
from dspy_implementation.dspy_metrics_enhanced import evaluate_predictions_enhanced

def main():
    print("=" * 80)
    print("QUICK DEV SET EVALUATION - Fixed Retrieval Metrics")
    print("=" * 80)

    # Setup
    print("\n📋 Setting up DSPy...")
    setup_dspy_qwen()

    # Load dataset
    print("\n📊 Loading dev set...")
    dataset = MMESGBenchDataset()
    dev_set = dataset.dev_set
    print(f"   Dev set: {len(dev_set)} questions")

    # Initialize baseline RAG (no query optimization)
    print("\n🔧 Initializing baseline RAG...")
    rag = BaselineMMESGBenchRAG()

    # Evaluate
    print("\n🎯 Evaluating with FIXED retrieval metric...")
    predictions = []

    for example in tqdm(dev_set, desc="Evaluating"):
        try:
            pred = rag(
                question=example.question,
                doc_id=example.doc_id,
                answer_format=example.answer_format
            )
            predictions.append(pred)
        except Exception as e:
            print(f"\n⚠️  Error: {e}")
            predictions.append(dspy.Prediction(answer="Failed"))

    # Compute metrics
    print("\n📊 Computing metrics...")
    results = evaluate_predictions_enhanced(predictions, dev_set)

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS - Baseline RAG (No Query Optimization)")
    print("=" * 80)

    print(f"\n📈 Overall Metrics (Dev Set - {len(dev_set)} questions):")
    print(f"   Retrieval accuracy: {results['retrieval_accuracy']:.1%} " +
          f"({results['retrieval_correct']}/{results['total']})")
    print(f"   Answer accuracy:    {results['answer_accuracy']:.1%} " +
          f"({results['answer_correct']}/{results['total']})")
    print(f"   End-to-end accuracy: {results['end_to_end_accuracy']:.1%} " +
          f"({results['end_to_end_correct']}/{results['total']})")

    print(f"\n📋 Format Breakdown:")
    for fmt, stats in results['by_format'].items():
        fmt_str = str(fmt) if fmt is not None else "None"
        print(f"\n   {fmt_str}:")
        print(f"      Retrieval: {stats['retrieval_accuracy']:6.1%} ({stats['retrieval_correct']}/{stats['total']})")
        print(f"      Answer:    {stats['answer_accuracy']:6.1%} ({stats['answer_correct']}/{stats['total']})")
        print(f"      E2E:       {stats['end_to_end_accuracy']:6.1%} ({stats['end_to_end_correct']}/{stats['total']})")

    print("\n" + "=" * 80)

    # Save results
    import json
    from datetime import datetime

    results_file = f"quick_dev_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'dev_size': len(dev_set),
            'results': results,
            'note': 'Baseline RAG with FIXED retrieval metric'
        }, f, indent=2)

    print(f"📁 Results saved to: {results_file}\n")

    return results

if __name__ == "__main__":
    main()
