"""
Re-score existing DC results with corrected null equivalence handling.

This script:
1. Loads existing DC result files
2. Applies corrected eval_score with null equivalence
3. Saves updated results with corrected metrics
4. NO API calls - just re-scoring existing predictions

Author: Sum Yee Chan
Date: November 6, 2025
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Import corrected evaluator
from src.evaluation_utils import eval_score_fixed


def rescore_result_file(input_file, output_dir):
    """Re-score a single result file with corrected evaluator."""

    print(f"\n{'='*70}")
    print(f"Re-scoring: {input_file.name}")
    print(f"{'='*70}")

    # Load original results
    with open(input_file) as f:
        data = json.load(f)

    predictions = data.get('predictions', [])

    if not predictions:
        print("  ⚠️  No predictions found, skipping...")
        return None

    print(f"  Total predictions: {len(predictions)}")

    # Re-score each prediction
    corrections_made = 0
    for pred in predictions:
        gt = pred.get('ground_truth', '')
        prediction = pred.get('prediction', '')
        answer_format = pred.get('answer_format')

        # Original score
        original_correct = pred.get('correct', False)

        # Corrected score
        corrected_score = eval_score_fixed(gt, prediction, answer_format)
        corrected_correct = (corrected_score >= 0.5)

        # Update if changed
        if original_correct != corrected_correct:
            corrections_made += 1

        # Update in place
        pred['anls_score'] = corrected_score
        pred['correct'] = corrected_correct

    # Recalculate overall metrics
    total = len(predictions)
    correct = sum(1 for p in predictions if p.get('correct', False))
    accuracy = correct / total if total > 0 else 0

    # Calculate by format
    format_breakdown = {}
    for pred in predictions:
        fmt = pred.get('answer_format')
        if fmt not in format_breakdown:
            format_breakdown[fmt] = {'correct': 0, 'total': 0}

        format_breakdown[fmt]['total'] += 1
        if pred.get('correct', False):
            format_breakdown[fmt]['correct'] += 1

    # Add accuracy to each format
    for fmt in format_breakdown:
        total_fmt = format_breakdown[fmt]['total']
        correct_fmt = format_breakdown[fmt]['correct']
        format_breakdown[fmt]['accuracy'] = correct_fmt / total_fmt if total_fmt > 0 else 0

    # Update metadata
    original_accuracy = data.get('overall_accuracy', 0)
    original_correct = data.get('correct', 0)

    data['overall_accuracy'] = accuracy
    data['correct'] = correct
    data['total'] = total
    data['format_breakdown'] = format_breakdown

    # Add re-scoring metadata
    data['rescore_metadata'] = {
        'original_accuracy': original_accuracy,
        'original_correct': original_correct,
        'corrected_accuracy': accuracy,
        'corrected_correct': correct,
        'corrections_made': corrections_made,
        'rescore_timestamp': datetime.now().strftime("%Y%m%d_%H%M%S"),
        'evaluator': 'eval_score_fixed with null equivalence'
    }

    # Print summary
    print(f"\n  Results:")
    print(f"    Original accuracy: {original_accuracy*100:.1f}% ({original_correct}/{total})")
    print(f"    Corrected accuracy: {accuracy*100:.1f}% ({correct}/{total})")
    print(f"    Improvement: {(accuracy - original_accuracy)*100:+.1f}%")
    print(f"    Corrections made: {corrections_made} predictions")

    # Save corrected results
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"rescored_{input_file.name}"

    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\n  ✅ Saved to: {output_file}")

    return {
        'filename': input_file.name,
        'dataset': data.get('metadata', {}).get('dataset', 'unknown'),
        'total_questions': total,
        'original_accuracy': original_accuracy * 100,
        'original_correct': original_correct,
        'corrected_accuracy': accuracy * 100,
        'corrected_correct': correct,
        'improvement': (accuracy - original_accuracy) * 100,
        'corrections_made': corrections_made
    }


def main():
    """Re-score all DC result files."""

    print("="*70)
    print("DC RESULTS RE-SCORING WITH CORRECTED EVALUATOR")
    print("="*70)
    print()
    print("This script re-scores existing predictions with null equivalence fix.")
    print("No API calls - just updating evaluation logic.")
    print()

    # Setup paths
    results_dir = Path("results/dc_experiments")
    output_dir = Path("results/dc_experiments/rescored")

    # Find all DC result files
    result_files = sorted(results_dir.glob("dc_cumulative_cold_*.json"))

    if not result_files:
        print("❌ No DC result files found in results/dc_experiments/")
        return

    print(f"Found {len(result_files)} DC result files to re-score\n")

    # Re-score each file
    all_summaries = []

    for result_file in result_files:
        summary = rescore_result_file(result_file, output_dir)
        if summary:
            all_summaries.append(summary)

    # Print overall summary
    print("\n" + "="*70)
    print("SUMMARY: ALL RUNS")
    print("="*70)
    print()

    # Group by dataset
    dev_runs = [s for s in all_summaries if s['dataset'] == 'dev']
    test_runs = [s for s in all_summaries if s['dataset'] == 'test']

    if dev_runs:
        print("Dev Set Runs (93 questions):")
        print(f"{'Run':<40} {'Original':>12} {'Corrected':>12} {'Change':>10}")
        print("-"*70)
        for s in dev_runs:
            print(f"{s['filename']:<40} "
                  f"{s['original_accuracy']:>10.1f}% "
                  f"{s['corrected_accuracy']:>10.1f}% "
                  f"{s['improvement']:>+9.1f}%")
        print()

    if test_runs:
        print("Test Set Runs (654 questions):")
        print(f"{'Run':<40} {'Original':>12} {'Corrected':>12} {'Change':>10}")
        print("-"*70)
        for s in test_runs:
            print(f"{s['filename']:<40} "
                  f"{s['original_accuracy']:>10.1f}% "
                  f"{s['corrected_accuracy']:>10.1f}% "
                  f"{s['improvement']:>+9.1f}%")
        print()

    # Calculate totals
    total_corrections = sum(s['corrections_made'] for s in all_summaries)
    affected_runs = sum(1 for s in all_summaries if s['corrections_made'] > 0)

    print("Overall Impact:")
    print(f"  Runs analyzed: {len(all_summaries)}")
    print(f"  Runs affected: {affected_runs}")
    print(f"  Total predictions corrected: {total_corrections}")
    print()

    print(f"✅ All re-scored results saved to: {output_dir}")
    print()
    print("Next steps:")
    print("  1. Review corrected metrics")
    print("  2. Share findings with Victor")
    print("  3. Decide whether to integrate fix into codebase")


if __name__ == "__main__":
    main()
