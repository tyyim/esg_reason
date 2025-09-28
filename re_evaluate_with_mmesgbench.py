#!/usr/bin/env python3
"""
Re-evaluate existing results with exact MMESGBench evaluation logic
"""

import json
from mmesgbench_exact_evaluation import evaluate_prediction_mmesgbench

def re_evaluate_results(results_file: str, output_file: str):
    """Re-evaluate existing results with MMESGBench logic"""
    print(f"📊 Re-evaluating results from: {results_file}")

    # Load existing results
    with open(results_file, 'r') as f:
        old_results = json.load(f)

    detailed_results = old_results['detailed_results']
    print(f"Found {len(detailed_results)} questions to re-evaluate")

    # Re-evaluate each result
    new_results = []
    old_correct = 0
    new_correct = 0

    for i, result in enumerate(detailed_results):
        # Use exact MMESGBench evaluation
        is_correct, exact_match, f1_score = evaluate_prediction_mmesgbench(
            result['predicted_answer'],
            result['ground_truth'],
            result['answer_format']
        )

        # Create new result with MMESGBench evaluation
        new_result = {
            'question': result['question'],
            'predicted_answer': result['predicted_answer'],
            'ground_truth': result['ground_truth'],
            'score': 1.0 if is_correct else 0.0,
            'answer_format': result['answer_format'],
            'doc_id': result['doc_id'],
            'exact_match': exact_match,
            'f1_score': f1_score,
            'old_score': result['score']  # Keep track of old score
        }

        new_results.append(new_result)

        # Track changes
        old_correct += result['score']
        new_correct += new_result['score']

        # Show differences
        if result['score'] != new_result['score']:
            status = "✅ NEW CORRECT" if new_result['score'] > result['score'] else "❌ NOW WRONG"
            print(f"  {status}: Q{i+1} ({result['answer_format']})")
            print(f"    Predicted: {result['predicted_answer']}")
            print(f"    Ground Truth: {result['ground_truth']}")
            print(f"    Old: {result['score']} → New: {new_result['score']}")
            print()

    # Calculate new statistics
    total_questions = len(new_results)
    new_accuracy = new_correct / total_questions if total_questions > 0 else 0
    old_accuracy = old_correct / total_questions if total_questions > 0 else 0

    # Group by format
    format_stats = {}
    for result in new_results:
        fmt = result['answer_format']
        if fmt not in format_stats:
            format_stats[fmt] = {'total': 0, 'correct': 0}
        format_stats[fmt]['total'] += 1
        format_stats[fmt]['correct'] += result['score']

    # Calculate format accuracies
    for fmt, stats in format_stats.items():
        stats['accuracy'] = stats['correct'] / stats['total'] if stats['total'] > 0 else 0

    # Group by document
    doc_stats = {}
    for result in new_results:
        doc = result['doc_id']
        if doc not in doc_stats:
            doc_stats[doc] = {'total': 0, 'correct': 0}
        doc_stats[doc]['total'] += 1
        doc_stats[doc]['correct'] += result['score']

    # Calculate doc accuracies
    for doc, stats in doc_stats.items():
        stats['accuracy'] = stats['correct'] / stats['total'] if stats['total'] > 0 else 0

    # Create new results object
    new_results_obj = {
        'accuracy': new_accuracy,
        'total_questions': total_questions,
        'total_score': new_correct,
        'total_time': old_results.get('total_time', 0),
        'avg_processing_time': old_results.get('avg_processing_time', 0),
        'format_breakdown': format_stats,
        'document_breakdown': doc_stats,
        'detailed_results': new_results,
        'evaluation_method': 'Re-evaluated with exact MMESGBench evaluation logic',
        'original_method': old_results.get('evaluation_method', 'Unknown'),
        'original_accuracy': old_accuracy,
        'evaluation_changes': {
            'questions_changed': sum(1 for r in new_results if r['score'] != r['old_score']),
            'newly_correct': sum(1 for r in new_results if r['score'] > r['old_score']),
            'newly_incorrect': sum(1 for r in new_results if r['score'] < r['old_score']),
            'accuracy_change': new_accuracy - old_accuracy
        }
    }

    # Save new results
    with open(output_file, 'w') as f:
        json.dump(new_results_obj, f, indent=2)

    # Print summary
    print(f"\n📊 Re-evaluation Summary:")
    print(f"Original Accuracy: {old_accuracy:.1%} ({old_correct:.0f}/{total_questions})")
    print(f"MMESGBench Accuracy: {new_accuracy:.1%} ({new_correct:.0f}/{total_questions})")
    print(f"Improvement: {new_accuracy - old_accuracy:.1%} ({new_correct - old_correct:.0f} questions)")
    print(f"Questions Changed: {new_results_obj['evaluation_changes']['questions_changed']}")
    print(f"Newly Correct: {new_results_obj['evaluation_changes']['newly_correct']}")
    print(f"Newly Incorrect: {new_results_obj['evaluation_changes']['newly_incorrect']}")

    print(f"\n📊 Format Breakdown (MMESGBench):")
    for fmt, stats in format_stats.items():
        print(f"  {fmt}: {stats['accuracy']:.1%} ({stats['correct']:.0f}/{stats['total']})")

    print(f"\n✅ Re-evaluation completed! Results saved to: {output_file}")

    return new_results_obj

if __name__ == "__main__":
    # Re-evaluate the latest full dataset results
    re_evaluate_results(
        'optimized_full_dataset_fixed_results.json',
        'optimized_full_dataset_mmesgbench_rescored.json'
    )