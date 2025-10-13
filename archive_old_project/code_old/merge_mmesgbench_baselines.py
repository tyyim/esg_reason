#!/usr/bin/env python3
"""
Merge MMESGBench Baseline Results

Combines:
1. Original full dataset results (933 questions, old doc names)
2. Corrected evaluation results (47 questions, correct doc names)

Output: Combined MMESGBench baseline with 933 questions
"""

import json
from pathlib import Path
from collections import defaultdict

def load_json(filepath):
    """Load JSON file"""
    with open(filepath, 'r') as f:
        return json.load(f)

def merge_baselines():
    """Merge the two baseline results"""

    # Load files
    print("📂 Loading baseline files...")
    original = load_json("optimized_full_dataset_mmesgbench_with_f1.json")
    corrected = load_json("corrected_evaluation_results/colbert_corrected_evaluation.json")

    print(f"   Original: {original['total_questions']} questions")
    print(f"   Corrected: {corrected['total_questions']} questions")

    # Since the corrected file only has 47 questions (a subset validation),
    # and the original has all 933 questions, we'll use the original as the baseline
    # and note that it was validated on 47 corrected questions

    # Create combined baseline
    combined = {
        "metadata": {
            "description": "Combined MMESGBench baseline results",
            "source_files": [
                "optimized_full_dataset_mmesgbench_with_f1.json (933 questions)",
                "corrected_evaluation_results/colbert_corrected_evaluation.json (47 question validation)"
            ],
            "evaluation_date": "2025-09-28",
            "validation_date": "2025-10-01",
            "retrieval": "ColBERT with SentenceTransformer (all-MiniLM-L6-v2)",
            "llm": "Qwen Max",
            "notes": "Original baseline with subset validation on corrected documents"
        },
        "overall_accuracy": original['accuracy'],
        "total_questions": original['total_questions'],
        "total_correct": original['total_score'],
        "format_breakdown": {},
        "validation_subset": {
            "total_questions": corrected['total_questions'],
            "accuracy": corrected['accuracy'],
            "notes": "Validation on 47 questions with corrected document names"
        }
    }

    # Process format breakdown
    for format_name, stats in original['format_breakdown'].items():
        combined['format_breakdown'][format_name] = {
            "total": stats['total'],
            "correct": stats['correct'],
            "accuracy": stats['accuracy']
        }

    # Add document breakdown
    combined['document_breakdown'] = original.get('document_breakdown', {})

    # Calculate summary statistics
    print("\n📊 Combined MMESGBench Baseline:")
    print(f"   Total Questions: {combined['total_questions']}")
    print(f"   Overall Accuracy: {combined['overall_accuracy']:.2%}")
    print(f"\n   Format Breakdown:")
    for fmt, stats in combined['format_breakdown'].items():
        print(f"      {fmt}: {stats['correct']}/{stats['total']} ({stats['accuracy']:.1%})")

    # Save combined results
    output_path = "mmesgbench_baseline_combined.json"
    with open(output_path, 'w') as f:
        json.dump(combined, f, indent=2)

    print(f"\n✅ Combined baseline saved: {output_path}")
    print(f"\n📌 Key Metrics:")
    print(f"   • Overall: {combined['overall_accuracy']:.1%}")
    print(f"   • 'Not answerable' (None): {combined['format_breakdown']['None']['accuracy']:.1%}")
    print(f"   • Int Format: {combined['format_breakdown']['Int']['accuracy']:.1%}")
    print(f"   • Str Format: {combined['format_breakdown']['Str']['accuracy']:.1%}")
    print(f"   • Float Format: {combined['format_breakdown']['Float']['accuracy']:.1%}")
    print(f"   • List Format: {combined['format_breakdown']['List']['accuracy']:.1%}")

    return combined

if __name__ == "__main__":
    merge_baselines()
