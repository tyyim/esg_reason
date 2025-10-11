#!/usr/bin/env python3
"""
Substitute Corrected Results into Original MMESGBench Baseline

Takes the 47 corrected evaluation results and substitutes them into the
original 933 results, then recalculates overall accuracy.
"""

import json
from collections import defaultdict

def load_json(filepath):
    """Load JSON file"""
    with open(filepath, 'r') as f:
        return json.load(f)

def create_question_key(result):
    """Create unique key for matching questions"""
    # Use question text and doc_id as unique identifier
    question = result['question'].strip().lower()
    doc_id = result['doc_id']
    return (question, doc_id)

def substitute_and_recalculate():
    """Substitute corrected results and recalculate accuracy"""

    # Load files
    print("📂 Loading files...")
    original = load_json("optimized_full_dataset_mmesgbench_with_f1.json")
    corrected = load_json("corrected_evaluation_results/colbert_corrected_evaluation.json")

    print(f"   Original: {len(original['detailed_results'])} questions")
    print(f"   Corrected: {len(corrected['detailed_results'])} questions")

    # Create map of corrected results
    corrected_map = {}
    for result in corrected['detailed_results']:
        key = create_question_key(result)
        corrected_map[key] = result

    print(f"   Created map with {len(corrected_map)} corrected results")

    # Substitute corrected results into original
    substituted_results = []
    substitution_count = 0

    for result in original['detailed_results']:
        key = create_question_key(result)

        if key in corrected_map:
            # Replace with corrected result
            substituted_results.append(corrected_map[key])
            substitution_count += 1
        else:
            # Keep original result
            substituted_results.append(result)

    print(f"\n✅ Substituted {substitution_count} questions with corrected results")

    # Recalculate overall statistics
    total_questions = len(substituted_results)
    total_correct = sum(1 for r in substituted_results if r['score'] == 1.0)
    overall_accuracy = total_correct / total_questions

    # Calculate format breakdown
    format_stats = defaultdict(lambda: {'total': 0, 'correct': 0})

    for result in substituted_results:
        fmt = result['answer_format']
        if fmt is None:
            fmt = 'None'

        format_stats[fmt]['total'] += 1
        if result['score'] == 1.0:
            format_stats[fmt]['correct'] += 1

    # Add accuracy to format breakdown
    format_breakdown = {}
    for fmt, stats in format_stats.items():
        format_breakdown[fmt] = {
            'total': stats['total'],
            'correct': stats['correct'],
            'accuracy': stats['correct'] / stats['total'] if stats['total'] > 0 else 0
        }

    # Create final result
    final_result = {
        "metadata": {
            "description": "MMESGBench baseline with corrected document names substituted",
            "original_file": "optimized_full_dataset_mmesgbench_with_f1.json",
            "corrected_file": "corrected_evaluation_results/colbert_corrected_evaluation.json",
            "total_questions": total_questions,
            "substituted_questions": substitution_count,
            "retrieval": "ColBERT with SentenceTransformer (all-MiniLM-L6-v2)",
            "llm": "Qwen Max",
            "evaluation_date": "2025-09-28 (original) + 2025-10-01 (corrected substitution)"
        },
        "overall_accuracy": overall_accuracy,
        "total_questions": total_questions,
        "total_correct": total_correct,
        "format_breakdown": format_breakdown,
        "detailed_results": substituted_results
    }

    # Display results
    print("\n" + "=" * 70)
    print("📊 CORRECTED MMESGBench BASELINE RESULTS")
    print("=" * 70)
    print(f"\nOverall Accuracy: {overall_accuracy:.2%} ({total_correct}/{total_questions})")
    print(f"\nFormat Breakdown:")
    for fmt in sorted(format_breakdown.keys()):
        stats = format_breakdown[fmt]
        print(f"  {fmt:12s}: {stats['correct']:3.0f}/{stats['total']:3d} ({stats['accuracy']:6.1%})")

    # Compare with original
    print(f"\n📈 Change from Original:")
    original_correct = original['total_score']
    original_accuracy = original['accuracy']
    accuracy_change = overall_accuracy - original_accuracy
    correct_change = total_correct - original_correct

    print(f"  Accuracy: {original_accuracy:.2%} → {overall_accuracy:.2%} ({accuracy_change:+.2%})")
    print(f"  Correct: {original_correct:.0f} → {total_correct} ({correct_change:+.0f})")

    # Save result
    output_file = "mmesgbench_baseline_corrected.json"
    with open(output_file, 'w') as f:
        json.dump(final_result, f, indent=2)

    print(f"\n✅ Saved corrected baseline: {output_file}")

    return final_result

if __name__ == "__main__":
    substitute_and_recalculate()
