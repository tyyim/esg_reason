"""
Re-score DC predictions with ANLS string bug fix
Uses existing prediction files, only re-computes scores
"""
import json
import sys
from pathlib import Path
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.evaluation import eval_score

def rescore_predictions(input_file):
    """Re-score predictions with fixed evaluator"""
    print(f"\n{'='*60}")
    print(f"Re-scoring: {input_file}")
    print(f"{'='*60}\n")
    
    # Load predictions
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    predictions = data.get('predictions', [])
    
    # Re-score each prediction
    correct = 0
    format_breakdown = defaultdict(lambda: {'correct': 0, 'total': 0, 'changed': 0})
    
    for pred in predictions:
        gt = pred['ground_truth']
        predicted = pred.get('prediction', pred.get('predicted', ''))
        answer_type = pred.get('answer_format', pred.get('answer_type', pred.get('format', 'Unknown')))
        
        # Store original correctness
        original_correct = pred.get('correct', False)
        
        # Re-compute score with fixed evaluator
        score = eval_score(gt, predicted, answer_type)
        is_correct = (score >= 0.5)
        
        # Track if this changed
        if original_correct != is_correct:
            format_breakdown[answer_type]['changed'] += 1
            # Debug: print first few changes
            if format_breakdown[answer_type]['changed'] <= 3:
                print(f"\n  [DEBUG] {answer_type} score changed:")
                print(f"    Q: {pred['question'][:80]}...")
                print(f"    GT: {gt}")
                print(f"    Pred: {predicted}")
                print(f"    Original: {original_correct} -> New: {is_correct}")
                print(f"    Score: {score}")
        
        # Update prediction
        pred['score'] = score
        pred['correct'] = is_correct
        
        if is_correct:
            correct += 1
        
        # Update format breakdown
        format_breakdown[answer_type]['correct'] += (1 if is_correct else 0)
        format_breakdown[answer_type]['total'] += 1
    
    # Compute metrics
    total = len(predictions)
    accuracy = correct / total if total > 0 else 0
    
    # Print results
    print(f"\n{'='*60}")
    print(f"Results with ANLS String Fix:")
    print(f"{'='*60}")
    print(f"Overall Accuracy: {accuracy:.1%} ({correct}/{total})")
    
    # Original results
    original_accuracy = data.get('overall_accuracy', data.get('accuracy', 0))
    original_correct = data.get('correct', 0)
    print(f"Original Accuracy: {original_accuracy:.1%} ({original_correct}/{total})")
    print(f"Improvement: {(accuracy - original_accuracy)*100:+.1f}% ({correct - original_correct:+d} questions)")
    
    print(f"\n{'='*60}")
    print(f"Format-Specific Breakdown:")
    print(f"{'='*60}")
    
    # Filter out None keys
    valid_formats = [k for k in format_breakdown.keys() if k is not None]
    for fmt in sorted(valid_formats):
        stats = format_breakdown[fmt]
        fmt_acc = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
        print(f"{fmt:8s}: {fmt_acc:6.1%} ({stats['correct']:3d}/{stats['total']:3d})")
    
    # Save rescored results
    output_file = str(input_file).replace('.json', '_anls_fixed.json')
    output_data = {
        'original_file': str(input_file),
        'rescore_date': '2025-11-09',
        'fixes_applied': ['null_equivalence', 'anls_string_bug'],
        'accuracy': accuracy,
        'correct': correct,
        'total': total,
        'format_breakdown': dict(format_breakdown),
        'predictions': predictions,
        'final_cheatsheet': data.get('final_cheatsheet', '')
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✅ Rescored results saved to: {output_file}\n")
    
    return {
        'file': input_file.name,
        'original_accuracy': original_accuracy,
        'new_accuracy': accuracy,
        'improvement': accuracy - original_accuracy,
        'original_correct': original_correct,
        'new_correct': correct,
        'total': total
    }


def main():
    """Rescore all DC prediction files"""
    results_dir = project_root / "results" / "dc_experiments"
    
    # Files to rescore (from original Nov 1st runs - no fixes applied yet)
    files_to_rescore = [
        "dc_cumulative_cold_dev_20251101_153119.json",  # Dev set (no fixes)
        "dc_cumulative_cold_test_20251101_171723.json",  # Test set cold (no fixes)
        "dc_cumulative_cold_test_20251101_172109.json",  # Test set bootstrap (no fixes)
    ]
    
    # Check what files exist
    print("\n" + "="*60)
    print("Checking for DC prediction files...")
    print("="*60)
    
    available_files = []
    for filename in files_to_rescore:
        filepath = results_dir / filename
        if filepath.exists():
            available_files.append(filepath)
            print(f"✅ Found: {filename}")
        else:
            print(f"❌ Not found: {filename}")
    
    if not available_files:
        print("\n⚠️  No prediction files found. Looking for any dc_*.json files...\n")
        available_files = sorted(results_dir.glob("dc_*.json"))
        for f in available_files:
            if not f.name.endswith('_anls_fixed.json'):  # Skip already rescored
                print(f"Found: {f.name}")
    
    if not available_files:
        print("❌ No DC prediction files found in results/dc_experiments/")
        return
    
    # Rescore all files
    summary = []
    for filepath in available_files:
        if filepath.name.endswith('_anls_fixed.json'):
            print(f"\n⏭️  Skipping already rescored file: {filepath.name}")
            continue
        
        result = rescore_predictions(filepath)
        summary.append(result)
    
    # Print summary
    if summary:
        print("\n" + "="*60)
        print("SUMMARY - Impact of ANLS String Bug Fix")
        print("="*60)
        for result in summary:
            print(f"\n{result['file']}:")
            print(f"  Original: {result['original_accuracy']:.1%} ({result['original_correct']}/{result['total']})")
            print(f"  Fixed:    {result['new_accuracy']:.1%} ({result['new_correct']}/{result['total']})")
            print(f"  Impact:   {result['improvement']*100:+.1f}% ({result['new_correct'] - result['original_correct']:+d} questions)")


if __name__ == "__main__":
    main()

