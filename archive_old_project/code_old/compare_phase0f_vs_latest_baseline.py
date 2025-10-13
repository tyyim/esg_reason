#!/usr/bin/env python3
"""
Compare Phase 0F (45.1%) vs Latest Baseline (51.6%) on dev set
Identify root cause of improvement
"""
import json
from typing import Dict, List

def load_data():
    """Load all necessary data"""

    # Load dev set
    with open('dspy_implementation/data_splits/dev_93.json', 'r') as f:
        dev_set = json.load(f)

    # Load full dataset to get question indices
    with open('mmesgbench_dataset_corrected.json', 'r') as f:
        full_dataset = json.load(f)

    # Load Phase 0F predictions (all 933 questions)
    with open('dspy_full_dataset_checkpoint.json', 'r') as f:
        phase0f_data = json.load(f)
        phase0f_preds = phase0f_data['predictions']

    # Load latest baseline results (from optimization script)
    # This was the baseline evaluation before optimization
    # Need to find the baseline predictions

    return dev_set, full_dataset, phase0f_preds

def map_dev_to_phase0f(dev_set: List[Dict], full_dataset: List[Dict], phase0f_preds: List[Dict]) -> List[Dict]:
    """Map dev set questions to Phase 0F predictions"""

    # Create mapping by (question, doc_id)
    phase0f_map = {}
    for pred in phase0f_preds:
        if pred and 'question' in pred and 'doc_id' in pred:
            key = (pred['question'].strip(), pred['doc_id'].strip())
            phase0f_map[key] = pred

    print(f"Phase 0F predictions mapped: {len(phase0f_map)}")

    # Find Phase 0F predictions for dev set
    phase0f_dev_preds = []
    for dev_q in dev_set:
        key = (dev_q['question'].strip(), dev_q['doc_id'].strip())
        if key in phase0f_map:
            phase0f_dev_preds.append(phase0f_map[key])
        else:
            print(f"Warning: Dev question not found in Phase 0F: {dev_q['question'][:50]}...")
            phase0f_dev_preds.append(None)

    return phase0f_dev_preds

def evaluate_predictions(gold_answer: str, pred_answer: str, format_type: str) -> bool:
    """Simple evaluation"""
    if gold_answer is None:
        return pred_answer in ["Not answerable", "Fail to answer"]

    gold_str = str(gold_answer).lower().strip()
    pred_str = str(pred_answer).lower().strip()

    return gold_str == pred_str

def compare_results(dev_set: List[Dict], phase0f_preds: List[Dict], latest_baseline_preds: List[Dict]) -> Dict:
    """Compare Phase 0F vs latest baseline"""

    results = {
        'total': len(dev_set),
        'phase0f_correct': 0,
        'latest_correct': 0,
        'both_correct': [],
        'both_wrong': [],
        'phase0f_only': [],  # Phase 0F correct, latest wrong
        'latest_only': [],   # Latest correct, Phase 0F wrong
        'phase0f_missing': [],
        'by_format': {}
    }

    for idx, (question, p0f_pred, latest_pred) in enumerate(zip(dev_set, phase0f_preds, latest_baseline_preds)):
        gold_answer = question.get('answer')
        format_type = question.get('answer_format')

        if format_type not in results['by_format']:
            results['by_format'][format_type] = {
                'total': 0,
                'phase0f_correct': 0,
                'latest_correct': 0,
                'improvement': 0
            }

        results['by_format'][format_type]['total'] += 1

        # Handle missing Phase 0F prediction
        if p0f_pred is None:
            results['phase0f_missing'].append({
                'idx': idx,
                'question': question['question'],
                'doc_id': question['doc_id']
            })
            continue

        # Evaluate both
        p0f_answer = p0f_pred.get('answer', '')
        latest_answer = latest_pred.get('answer', '')

        p0f_correct = evaluate_predictions(gold_answer, p0f_answer, format_type)
        latest_correct = evaluate_predictions(gold_answer, latest_answer, format_type)

        if p0f_correct:
            results['phase0f_correct'] += 1
            results['by_format'][format_type]['phase0f_correct'] += 1

        if latest_correct:
            results['latest_correct'] += 1
            results['by_format'][format_type]['latest_correct'] += 1

        # Categorize changes
        record = {
            'idx': idx,
            'question': question['question'],
            'doc_id': question['doc_id'],
            'format': format_type,
            'gold': str(gold_answer),
            'phase0f_answer': str(p0f_answer),
            'latest_answer': str(latest_answer)
        }

        if p0f_correct and latest_correct:
            results['both_correct'].append(record)
        elif not p0f_correct and not latest_correct:
            results['both_wrong'].append(record)
        elif p0f_correct and not latest_correct:
            results['phase0f_only'].append(record)
        elif not p0f_correct and latest_correct:
            results['latest_only'].append(record)
            results['by_format'][format_type]['improvement'] += 1

    return results

def generate_report(results: Dict) -> str:
    """Generate comparison report"""

    report = []
    report.append("=" * 80)
    report.append("PHASE 0F vs LATEST BASELINE COMPARISON")
    report.append("=" * 80)
    report.append("")

    total = results['total']
    p0f_acc = results['phase0f_correct'] / total * 100
    latest_acc = results['latest_correct'] / total * 100
    improvement = latest_acc - p0f_acc

    report.append("📊 OVERALL RESULTS")
    report.append("-" * 80)
    report.append(f"Total questions (dev set): {total}")
    report.append(f"Phase 0F accuracy: {results['phase0f_correct']}/{total} ({p0f_acc:.1f}%)")
    report.append(f"Latest baseline accuracy: {results['latest_correct']}/{total} ({latest_acc:.1f}%)")
    report.append(f"Improvement: {improvement:+.1f}%")
    report.append("")

    # Changes breakdown
    phase0f_only = len(results['phase0f_only'])
    latest_only = len(results['latest_only'])
    both_correct = len(results['both_correct'])
    both_wrong = len(results['both_wrong'])

    report.append("🔄 PREDICTION CHANGES")
    report.append("-" * 80)
    report.append(f"Both correct: {both_correct} ({both_correct/total*100:.1f}%)")
    report.append(f"Both wrong: {both_wrong} ({both_wrong/total*100:.1f}%)")
    report.append(f"Phase 0F only correct: {phase0f_only} ({phase0f_only/total*100:.1f}%)")
    report.append(f"Latest only correct: {latest_only} ({latest_only/total*100:.1f}%)")
    report.append(f"Net improvement: {latest_only - phase0f_only} questions")
    report.append("")

    # By format
    report.append("📋 BY FORMAT")
    report.append("-" * 80)
    for fmt, stats in sorted(results['by_format'].items(), key=lambda x: (x[0] is None, x[0] or '')):
        fmt_name = fmt if fmt else "null"
        p0f_fmt_acc = stats['phase0f_correct'] / stats['total'] * 100
        latest_fmt_acc = stats['latest_correct'] / stats['total'] * 100
        fmt_improvement = latest_fmt_acc - p0f_fmt_acc

        report.append(f"\n{fmt_name} ({stats['total']} questions):")
        report.append(f"  Phase 0F:  {stats['phase0f_correct']}/{stats['total']} ({p0f_fmt_acc:.1f}%)")
        report.append(f"  Latest:    {stats['latest_correct']}/{stats['total']} ({latest_fmt_acc:.1f}%)")
        report.append(f"  Change:    {fmt_improvement:+.1f}%")
        report.append(f"  Improved:  {stats['improvement']} questions")

    report.append("")

    # Show examples of improvements
    if results['latest_only']:
        report.append("\n✅ EXAMPLES OF IMPROVEMENTS (Latest Correct, Phase 0F Wrong)")
        report.append("=" * 80)
        for i, example in enumerate(results['latest_only'][:10], 1):
            report.append(f"\n{i}. [{example['format']}] {example['question'][:80]}...")
            report.append(f"   Gold:          {example['gold']}")
            report.append(f"   Phase 0F:      {example['phase0f_answer']} ❌")
            report.append(f"   Latest:        {example['latest_answer']} ✅")
            report.append(f"   Doc: {example['doc_id']}")

    # Show examples of degradations
    if results['phase0f_only']:
        report.append("\n\n⚠️ EXAMPLES OF DEGRADATIONS (Phase 0F Correct, Latest Wrong)")
        report.append("=" * 80)
        for i, example in enumerate(results['phase0f_only'][:10], 1):
            report.append(f"\n{i}. [{example['format']}] {example['question'][:80]}...")
            report.append(f"   Gold:          {example['gold']}")
            report.append(f"   Phase 0F:      {example['phase0f_answer']} ✅")
            report.append(f"   Latest:        {example['latest_answer']} ❌")
            report.append(f"   Doc: {example['doc_id']}")

    report.append("\n\n" + "=" * 80)
    report.append("ROOT CAUSE ANALYSIS")
    report.append("=" * 80)

    if improvement > 0:
        report.append(f"\n✅ NET IMPROVEMENT: +{improvement:.1f}%")
        report.append(f"\nLikely causes:")
        report.append(f"1. Different evaluation methodology?")
        report.append(f"2. Code/prompt changes between Phase 0F and latest?")
        report.append(f"3. Bug fixes in evaluation logic?")
        report.append(f"4. Model/API changes?")
    else:
        report.append(f"\n⚠️ DEGRADATION: {improvement:.1f}%")
        report.append(f"\nSomething regressed between Phase 0F and latest baseline")

    report.append("")
    report.append("=" * 80)

    return "\n".join(report)

def main():
    print("Loading data...")
    dev_set, full_dataset, phase0f_preds = load_data()

    print(f"Loaded {len(dev_set)} dev questions")
    print(f"Loaded {len(phase0f_preds)} Phase 0F predictions")

    # Map dev set to Phase 0F predictions
    print("\nMapping dev set to Phase 0F predictions...")
    phase0f_dev_preds = map_dev_to_phase0f(dev_set, full_dataset, phase0f_preds)

    # Load latest baseline predictions (from optimized_predictions.json parent - baseline)
    # Actually, we have the optimized predictions, need to get baseline
    # The baseline was evaluated during optimization but results not saved separately
    # We need to re-evaluate or find the baseline predictions

    print("\nNote: Latest baseline predictions are the pre-optimization evaluation")
    print("These should be in the optimization log or MLFlow artifacts")
    print("\nFor now, let's compare Phase 0F predictions on dev set with known results")

    # Evaluate Phase 0F on dev set
    p0f_correct = 0
    for dev_q, p0f_pred in zip(dev_set, phase0f_dev_preds):
        if p0f_pred is None:
            continue

        gold = dev_q.get('answer')
        pred = p0f_pred.get('answer', '')
        fmt = dev_q.get('answer_format')

        if evaluate_predictions(gold, pred, fmt):
            p0f_correct += 1

    p0f_dev_acc = p0f_correct / len(dev_set) * 100

    print(f"\n📊 Phase 0F Performance on Dev Set:")
    print(f"  Correct: {p0f_correct}/{len(dev_set)}")
    print(f"  Accuracy: {p0f_dev_acc:.1f}%")
    print(f"\n📊 Latest Baseline (from optimization results):")
    print(f"  Accuracy: 51.6% (48/93)")
    print(f"\n📈 Difference: {51.6 - p0f_dev_acc:+.1f}%")

    # Now compare with actual latest predictions
    with open('optimized_predictions.json', 'r') as f:
        latest_preds = json.load(f)

    print(f"\nComparing with latest baseline predictions...")
    results = compare_results(dev_set, phase0f_dev_preds, latest_preds)

    # Generate report
    report = generate_report(results)

    # Save report
    with open('phase0f_vs_latest_comparison.txt', 'w') as f:
        f.write(report)

    print(f"\n✅ Comparison complete!")
    print(f"📄 Report saved to: phase0f_vs_latest_comparison.txt")
    print(f"\n{report}")

if __name__ == '__main__':
    main()
