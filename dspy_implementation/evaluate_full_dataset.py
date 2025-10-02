#!/usr/bin/env python3
"""
DSPy Full Dataset Evaluation (933 Questions)
Validates DSPy implementation against complete MMESGBench dataset
"""

import sys
import json
import os
from pathlib import Path
from tqdm import tqdm
import dspy

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Change to project root for document access
os.chdir(project_root)

from dspy_implementation.dspy_setup import setup_dspy_qwen
from dspy_implementation.dspy_rag_module import MMESGBenchRAG
from dspy_implementation.dspy_metrics import evaluate_predictions

def load_full_dataset():
    """Load full MMESGBench dataset with corrections"""
    import json

    # Load samples
    with open('MMESGBench/dataset/samples.json', 'r') as f:
        data = json.load(f)

    # Load corrections
    with open('dspy_implementation/document_corrections_mapping.json', 'r') as f:
        corrections = json.load(f)

    # Apply corrections
    correction_map = {}
    for corr in corrections['corrections']:
        if corr['type'] in ['document_replacement', 'filename_validated']:
            correction_map[corr['original']] = corr['corrected']

    # Apply corrections to data
    for item in data:
        if item['doc_id'] in correction_map:
            item['doc_id'] = correction_map[item['doc_id']]

    # Convert to DSPy examples
    examples = []
    for item in data:
        example = dspy.Example(
            doc_id=item['doc_id'],
            question=item['question'],
            answer=str(item['answer']),
            answer_format=item['answer_format']
        ).with_inputs('doc_id', 'question', 'answer_format')
        examples.append(example)

    return examples

def run_full_evaluation():
    """Run evaluation on all 933 questions"""
    print("=" * 80)
    print("DSPy Full Dataset Evaluation - 933 Questions")
    print("=" * 80)

    # Initialize DSPy
    print("\n📋 Setting up DSPy environment...")
    setup_dspy_qwen()

    # Load full dataset
    print("📊 Loading full MMESGBench dataset (933 questions)...")
    eval_set = load_full_dataset()
    print(f"✅ Loaded {len(eval_set)} questions with document corrections")
    print(f"   Target accuracy: 41.3% (385/933)")

    # Initialize RAG module
    print("\n🚀 Initializing MMESGBenchRAG module...")
    rag = MMESGBenchRAG()

    # Check for checkpoint
    checkpoint_file = "dspy_full_dataset_checkpoint.json"
    if os.path.exists(checkpoint_file):
        print(f"\n📂 Found checkpoint: {checkpoint_file}")
        with open(checkpoint_file, 'r') as f:
            checkpoint = json.load(f)
        predictions = [dspy.Prediction(**p) for p in checkpoint.get('predictions', [])]
        start_idx = len(predictions)
        print(f"   Resuming from question {start_idx + 1}/{len(eval_set)}")
    else:
        predictions = []
        start_idx = 0

    # Run evaluation
    print(f"\n🔄 Running evaluation on {len(eval_set)} questions...")
    print(f"   Starting from question {start_idx + 1}")
    print("   This will take approximately 30-45 minutes...\n")

    for i, example in enumerate(tqdm(eval_set[start_idx:], desc="Evaluating", initial=start_idx, total=len(eval_set))):
        try:
            # Run RAG pipeline
            pred = rag(
                question=example.question,
                doc_id=example.doc_id,
                answer_format=example.answer_format
            )

            predictions.append(pred)

            # Save checkpoint every 50 questions
            if len(predictions) % 50 == 0:
                with open(checkpoint_file, 'w') as f:
                    json.dump({
                        'predictions': [vars(p) for p in predictions],
                        'completed': len(predictions),
                        'total': len(eval_set)
                    }, f, indent=2)
                tqdm.write(f"   ✓ Checkpoint saved: {len(predictions)}/{len(eval_set)} questions")

        except Exception as e:
            tqdm.write(f"\n⚠️  Error on question {start_idx + i + 1}: {e}")
            predictions.append(dspy.Prediction(answer="Failed to generate"))

    # Evaluate results
    print("\n📊 Computing evaluation metrics...")
    examples = eval_set[:len(predictions)]
    results = evaluate_predictions(predictions, examples)

    # Print results
    print("\n" + "=" * 80)
    print("FULL DATASET EVALUATION RESULTS (933 Questions)")
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

    if abs(diff) <= 0.02:  # Within ±2%
        print(f"   ✅ PASS: Within ±2% tolerance")
    else:
        print(f"   ⚠️  Note: Outside ±2% tolerance")

    # Save detailed results
    output_file = "dspy_full_dataset_results.json"
    detailed_results = {
        "evaluation_set": "Full Dataset (933 questions)",
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
            "within_tolerance": abs(diff) <= 0.02
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

    # Clean up checkpoint
    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)
        print(f"🧹 Checkpoint removed: {checkpoint_file}")

    return results


if __name__ == "__main__":
    results = run_full_evaluation()

    print("\n✅ Full dataset evaluation complete!")
    print(f"   Final accuracy: {results['accuracy']:.1%}")
    print("   Ready for Stage 7: MIPROv2 optimization")
