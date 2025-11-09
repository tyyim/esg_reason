"""
Universal re-scoring script for BOTH DC and DSPy predictions
Handles different prediction formats and re-computes scores with fixed evaluator
"""
import json
import sys
from pathlib import Path
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.evaluation import eval_score


def load_dataset_lookup():
    """Load dataset splits and create lookup by question index"""
    # Load dev and test sets from saved split files
    dev_file = project_root / "dspy_implementation" / "data_splits" / "dev_93.json"
    test_file = project_root / "dspy_implementation" / "data_splits" / "test_654.json"
    
    lookups = {}
    
    # Load dev set
    with open(dev_file, 'r') as f:
        dev_data = json.load(f)
    lookups['dev'] = {f"q{i}": {
        'question': item['question'],
        'ground_truth': item['answer'],
        'answer_format': item['answer_format']
    } for i, item in enumerate(dev_data)}
    
    # Load test set
    with open(test_file, 'r') as f:
        test_data = json.load(f)
    lookups['test'] = {f"q{i}": {
        'question': item['question'],
        'ground_truth': item['answer'],
        'answer_format': item['answer_format']
    } for i, item in enumerate(test_data)}
    
    return lookups


def rescore_predictions(input_file: Path, dataset_lookups: dict):
    """Re-score predictions with fixed evaluator (handles DC and DSPy formats)"""
    print(f"\n{'='*60}")
    print(f"Re-scoring: {input_file}")
    print(f"{'='*60}\n")
    
    # Load predictions
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    predictions_data = data.get('predictions', [])
    
    # Detect format: DSPy uses dict, DC uses list
    is_dspy_format = isinstance(predictions_data, dict)
    
    # Determine dataset (dev or test)
    if 'dev' in input_file.name:
        dataset_type = 'dev'
    elif 'test' in input_file.name:
        dataset_type = 'test'
    else:
        print(f"⚠️  Cannot determine dataset type from filename: {input_file.name}")
        return None
    
    if is_dspy_format:
        print(f"  Format: DSPy (dict) | Dataset: {dataset_type}")
        # Convert dict to list for processing
        prediction_keys = list(predictions_data.keys())
        predictions = [predictions_data[k] for k in prediction_keys]
    else:
        print(f"  Format: DC (list) | Dataset: {dataset_type}")
        predictions = predictions_data
        prediction_keys = None
    
    # Get dataset lookup
    dataset_lookup = dataset_lookups.get(dataset_type, {})
    
    # Re-score each prediction
    correct = 0
    format_breakdown = defaultdict(lambda: {'correct': 0, 'total': 0, 'changed': 0})
    
    for idx, pred in enumerate(predictions):
        # Extract fields based on format
        if is_dspy_format:
            # DSPy format: need to get ground truth from dataset
            q_id = prediction_keys[idx]
            gt_data = dataset_lookup.get(q_id, {})
            gt = gt_data.get('ground_truth', '')
            answer_type = gt_data.get('answer_format', 'Unknown')
            question = gt_data.get('question', '')
            predicted = pred.get('answer', '')
        else:
            # DC format: has ground truth embedded
            gt = pred.get('ground_truth', '')
            predicted = pred.get('prediction', pred.get('predicted', ''))
            answer_type = pred.get('answer_format', pred.get('answer_type', pred.get('format', 'Unknown')))
            question = pred.get('question', '')
        
        # Store original correctness
        original_correct = pred.get('correct', False)
        
        # Re-compute score with fixed evaluator
        score = eval_score(gt, predicted, answer_type)
        is_correct = (score >= 0.5)
        
        # Track if this changed
        if original_correct != is_correct:
            format_breakdown[answer_type]['changed'] += 1
            # Debug: print first few changes per format
            if format_breakdown[answer_type]['changed'] <= 2:
                print(f"\n  [DEBUG] {answer_type} score changed:")
                print(f"    Q: {question[:80] if question else 'N/A'}...")
                print(f"    GT: {gt}")
                print(f"    Pred: {predicted[:100]}...")
                print(f"    Original: {original_correct} -> New: {is_correct}")
                print(f"    Score: {score:.3f}")
        
        # Update prediction with ground truth info (for DSPy)
        if is_dspy_format:
            pred['ground_truth'] = gt
            pred['answer_format'] = answer_type
            pred['question'] = question
        
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
    
    # Filter out None keys and sort
    valid_formats = sorted([k for k in format_breakdown.keys() if k is not None])
    for fmt in valid_formats:
        stats = format_breakdown[fmt]
        fmt_acc = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
        changed_str = f" ({stats['changed']} changed)" if stats['changed'] > 0 else ""
        print(f"{fmt:8s}: {fmt_acc:6.1%} ({stats['correct']:3d}/{stats['total']:3d}){changed_str}")
    
    # Save rescored results
    output_file = str(input_file).replace('.json', '_anls_fixed.json')
    
    if is_dspy_format:
        # Convert back to DSPy dict format
        rescored_predictions = {prediction_keys[i]: predictions[i] for i in range(len(predictions))}
    else:
        # Keep as list for DC format
        rescored_predictions = predictions
    
    output_data = {
        'original_file': str(input_file),
        'rescore_date': '2025-11-09',
        'fixes_applied': ['null_equivalence', 'anls_string_bug'],
        'format': 'DSPy' if is_dspy_format else 'DC',
        'dataset': dataset_type,
        'accuracy': accuracy,
        'overall_accuracy': accuracy,  # For compatibility
        'correct': correct,
        'total': total,
        'format_breakdown': {k: dict(v) for k, v in format_breakdown.items() if k is not None},
        'predictions': rescored_predictions
    }
    
    # Preserve additional metadata from original
    if 'final_cheatsheet' in data:
        output_data['final_cheatsheet'] = data['final_cheatsheet']
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✅ Rescored results saved to: {output_file}\n")
    
    return {
        'filepath': output_file,
        'filename': input_file.name,
        'format': 'DSPy' if is_dspy_format else 'DC',
        'dataset': dataset_type,
        'original_accuracy': original_accuracy,
        'new_accuracy': accuracy,
        'improvement': accuracy - original_accuracy,
        'original_correct': original_correct,
        'new_correct': correct,
        'total': total
    }


def main():
    """Rescore all DC and DSPy prediction files"""
    
    # Load dataset lookups first
    print("\n" + "="*60)
    print("Loading MMESGBench dataset...")
    print("="*60)
    dataset_lookups = load_dataset_lookup()
    print(f"✅ Loaded {len(dataset_lookups['dev'])} dev questions")
    print(f"✅ Loaded {len(dataset_lookups['test'])} test questions")
    
    # Define all files to rescore
    files_to_check = [
        # DC experiments (Nov 1, 2025 - no fixes applied)
        ("results/dc_experiments", [
            "dc_cumulative_cold_dev_20251101_153119.json",
            "dc_cumulative_cold_test_20251101_171723.json",
            "dc_cumulative_cold_test_20251101_172109.json",
        ]),
        # DSPy dev set (Oct 19, 2025 - no fixes applied)
        ("results/dev_set", [
            "baseline_dev_predictions_20251019_130401.json",
            "gepa_dev_predictions_20251019_130401.json",
            "miprov2_dev_predictions_20251019_130401.json",
        ]),
        # DSPy test set (Oct 21, 2025 - no fixes applied)
        ("results/test_set", [
            "baseline_test_predictions_20251021_225632.json",
            "gepa_test_predictions_20251021_225632.json",
            "miprov2_test_predictions_20251021_225632.json",
        ]),
    ]
    
    print("\n" + "="*60)
    print("Checking for prediction files (DC + DSPy)...")
    print("="*60)
    
    available_files = []
    for results_dir, filenames in files_to_check:
        dir_path = project_root / results_dir
        print(f"\n📁 {results_dir}/")
        for filename in filenames:
            filepath = dir_path / filename
            if filepath.exists():
                available_files.append(filepath)
                print(f"  ✅ {filename}")
            else:
                print(f"  ❌ {filename} (not found)")
    
    if not available_files:
        print("\n❌ No prediction files found to rescore!")
        return
    
    print(f"\n{'='*60}")
    print(f"Re-scoring {len(available_files)} prediction files...")
    print(f"{'='*60}")
    
    # Rescore all files
    summary = []
    for filepath in available_files:
        # Skip already rescored files
        if filepath.name.endswith('_anls_fixed.json'):
            print(f"\n⏭️  Skipping already rescored file: {filepath.name}")
            continue
        
        result = rescore_predictions(filepath, dataset_lookups)
        if result:
            summary.append(result)
    
    # Print summary
    if summary:
        print("\n" + "="*60)
        print("SUMMARY - Impact of Evaluation Bug Fixes")
        print("(Null Equivalence + ANLS String)")
        print("="*60)
        
        # Group by format and dataset
        dc_results = [r for r in summary if r['format'] == 'DC']
        dspy_dev_results = [r for r in summary if r['format'] == 'DSPy' and r['dataset'] == 'dev']
        dspy_test_results = [r for r in summary if r['format'] == 'DSPy' and r['dataset'] == 'test']
        
        if dc_results:
            print("\n🔹 Dynamic Cheatsheet (DC):")
            for result in dc_results:
                dataset_label = "(Dev)" if result['dataset'] == 'dev' else "(Test)"
                print(f"\n  {result['filename'].replace('_20251101_', ' ')} {dataset_label}:")
                print(f"    Original: {result['original_accuracy']:.1%} ({result['original_correct']}/{result['total']})")
                print(f"    Fixed:    {result['new_accuracy']:.1%} ({result['new_correct']}/{result['total']})")
                print(f"    Impact:   {result['improvement']*100:+.1f}% ({result['new_correct'] - result['original_correct']:+d} questions)")
        
        if dspy_dev_results:
            print("\n🔹 DSPy Dev Set (93 questions):")
            for result in dspy_dev_results:
                approach = "Baseline" if "baseline" in result['filename'] else \
                          "GEPA" if "gepa" in result['filename'] else \
                          "MIPROv2" if "miprov2" in result['filename'] else "Unknown"
                
                print(f"\n  {approach}:")
                print(f"    Original: {result['original_accuracy']:.1%} ({result['original_correct']}/{result['total']})")
                print(f"    Fixed:    {result['new_accuracy']:.1%} ({result['new_correct']}/{result['total']})")
                print(f"    Impact:   {result['improvement']*100:+.1f}% ({result['new_correct'] - result['original_correct']:+d} questions)")
        
        if dspy_test_results:
            print("\n🔹 DSPy Test Set (654 questions):")
            for result in dspy_test_results:
                approach = "Baseline" if "baseline" in result['filename'] else \
                          "GEPA" if "gepa" in result['filename'] else \
                          "MIPROv2" if "miprov2" in result['filename'] else "Unknown"
                
                print(f"\n  {approach}:")
                print(f"    Original: {result['original_accuracy']:.1%} ({result['original_correct']}/{result['total']})")
                print(f"    Fixed:    {result['new_accuracy']:.1%} ({result['new_correct']}/{result['total']})")
                print(f"    Impact:   {result['improvement']*100:+.1f}% ({result['new_correct'] - result['original_correct']:+d} questions)")


if __name__ == "__main__":
    main()
