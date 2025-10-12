#!/usr/bin/env python3
"""
Compare Baseline vs Optimized predictions with relaxed matching
Find root cause of performance difference
"""
import json
import re
import ast
from typing import Dict, List, Tuple
from collections import defaultdict

def normalize_for_comparison(text: str) -> str:
    """Normalize text for semantic comparison"""
    if text is None:
        return "not answerable"

    text = str(text).lower().strip()
    text = text.replace("the ", "").replace("a ", "").replace("an ", "")
    text = text.replace("organization", "org")
    return text

def extract_number(text: str) -> float:
    """Extract numeric value from text"""
    text = str(text).replace("%", "").replace(",", "").strip()
    match = re.search(r'-?\d+\.?\d*', text)
    if match:
        return float(match.group())
    return None

def check_semantic_match(gold: str, pred: str, format_type: str) -> Tuple[bool, str]:
    """
    Check if prediction is semantically correct
    Returns (is_match, reason)
    """
    if gold is None or pred is None:
        return False, "None value"

    gold_str = str(gold).strip()
    pred_str = str(pred).strip()

    # Exact match
    if gold_str.lower() == pred_str.lower():
        return True, "Exact match"

    # Number with % sign difference
    if format_type == "Float":
        gold_num = extract_number(gold_str)
        pred_num = extract_number(pred_str)

        if gold_num is not None and pred_num is not None:
            if abs(gold_num - pred_num) < 0.01:
                if "%" in gold_str and "%" not in pred_str:
                    return True, "Missing % sign (number correct)"
                elif gold_num == pred_num:
                    return True, "Number match (formatting differs)"

    # List with quote style difference
    if format_type == "List":
        try:
            gold_list = ast.literal_eval(gold_str)
            pred_list = ast.literal_eval(pred_str)
            if gold_list == pred_list:
                return True, "List match (quote style differs)"
        except:
            pass

    # String semantic similarity
    if format_type == "Str":
        gold_norm = normalize_for_comparison(gold_str)
        pred_norm = normalize_for_comparison(pred_str)

        gold_words = set(gold_norm.split())
        pred_words = set(pred_norm.split())

        overlap = len(gold_words & pred_words) / max(len(gold_words), 1)

        if overlap > 0.7:
            return True, f"Semantic match ({overlap*100:.0f}% overlap)"

        if all(word in pred_norm for word in gold_words if len(word) > 3):
            return True, "Contains all key information (verbose)"

    return False, "No match"

def evaluate_predictions(dev_set: List[Dict], predictions: List[Dict], label: str) -> Dict:
    """Evaluate predictions with both strict and relaxed matching"""

    results = {
        'label': label,
        'total': len(dev_set),
        'strict_correct': 0,
        'relaxed_correct': 0,
        'false_negatives': [],
        'by_format': defaultdict(lambda: {
            'total': 0,
            'strict_correct': 0,
            'relaxed_correct': 0,
            'false_negatives': []
        })
    }

    for idx, (question, pred) in enumerate(zip(dev_set, predictions)):
        gold_answer = question.get('answer')
        pred_answer = pred.get('predicted_answer') or pred.get('answer', '')
        format_type = question.get('answer_format', 'Unknown')

        # Update format stats
        results['by_format'][format_type]['total'] += 1

        # Strict matching
        gold_str = str(gold_answer).lower().strip()
        pred_str = str(pred_answer).lower().strip()
        strict_match = (gold_str == pred_str)

        if strict_match:
            results['strict_correct'] += 1
            results['relaxed_correct'] += 1
            results['by_format'][format_type]['strict_correct'] += 1
            results['by_format'][format_type]['relaxed_correct'] += 1
        else:
            # Check relaxed matching
            is_match, reason = check_semantic_match(gold_answer, pred_answer, format_type)

            if is_match:
                results['relaxed_correct'] += 1
                results['by_format'][format_type]['relaxed_correct'] += 1

                # This is a false negative
                fn_record = {
                    'idx': idx,
                    'question': question.get('question', '')[:80],
                    'format': format_type,
                    'gold': str(gold_answer),
                    'predicted': str(pred_answer),
                    'reason': reason
                }
                results['false_negatives'].append(fn_record)
                results['by_format'][format_type]['false_negatives'].append(fn_record)

    return results

def compare_models(baseline_results: Dict, optimized_results: Dict) -> Dict:
    """Compare baseline vs optimized performance"""

    comparison = {
        'baseline_strict': baseline_results['strict_correct'],
        'baseline_relaxed': baseline_results['relaxed_correct'],
        'optimized_strict': optimized_results['strict_correct'],
        'optimized_relaxed': optimized_results['relaxed_correct'],
        'total': baseline_results['total'],
        'degraded_questions': [],
        'improved_questions': [],
        'by_format': {}
    }

    # Calculate percentage changes
    total = comparison['total']
    comparison['baseline_strict_pct'] = baseline_results['strict_correct'] / total * 100
    comparison['baseline_relaxed_pct'] = baseline_results['relaxed_correct'] / total * 100
    comparison['optimized_strict_pct'] = optimized_results['strict_correct'] / total * 100
    comparison['optimized_relaxed_pct'] = optimized_results['relaxed_correct'] / total * 100

    comparison['strict_delta'] = comparison['optimized_strict_pct'] - comparison['baseline_strict_pct']
    comparison['relaxed_delta'] = comparison['optimized_relaxed_pct'] - comparison['baseline_relaxed_pct']

    return comparison

def generate_report(baseline_results: Dict, optimized_results: Dict, comparison: Dict) -> str:
    """Generate comprehensive comparison report"""

    report = []
    report.append("=" * 100)
    report.append("BASELINE vs OPTIMIZED COMPARISON WITH RELAXED MATCHING")
    report.append("=" * 100)
    report.append("")

    # Overall results
    report.append("📊 OVERALL RESULTS")
    report.append("-" * 100)
    report.append(f"Total questions (dev set): {comparison['total']}")
    report.append("")
    report.append("BASELINE PERFORMANCE:")
    report.append(f"  Strict matching:  {comparison['baseline_strict']}/{comparison['total']} ({comparison['baseline_strict_pct']:.1f}%)")
    report.append(f"  Relaxed matching: {comparison['baseline_relaxed']}/{comparison['total']} ({comparison['baseline_relaxed_pct']:.1f}%)")
    report.append(f"  False negatives:  {len(baseline_results['false_negatives'])} ({len(baseline_results['false_negatives'])/comparison['total']*100:.1f}%)")
    report.append("")
    report.append("OPTIMIZED PERFORMANCE:")
    report.append(f"  Strict matching:  {comparison['optimized_strict']}/{comparison['total']} ({comparison['optimized_strict_pct']:.1f}%)")
    report.append(f"  Relaxed matching: {comparison['optimized_relaxed']}/{comparison['total']} ({comparison['optimized_relaxed_pct']:.1f}%)")
    report.append(f"  False negatives:  {len(optimized_results['false_negatives'])} ({len(optimized_results['false_negatives'])/comparison['total']*100:.1f}%)")
    report.append("")
    report.append("PERFORMANCE CHANGE:")
    report.append(f"  Strict:  {comparison['strict_delta']:+.1f}% {'❌ DEGRADED' if comparison['strict_delta'] < 0 else '✅ IMPROVED'}")
    report.append(f"  Relaxed: {comparison['relaxed_delta']:+.1f}% {'❌ DEGRADED' if comparison['relaxed_delta'] < 0 else '✅ IMPROVED'}")
    report.append("")

    # By format comparison
    report.append("📋 PERFORMANCE BY FORMAT")
    report.append("-" * 100)
    for fmt in sorted(baseline_results['by_format'].keys(), key=lambda x: (x is None, x or '')):
        fmt_name = fmt if fmt else "null"
        baseline_fmt = baseline_results['by_format'][fmt]
        optimized_fmt = optimized_results['by_format'][fmt]

        total = baseline_fmt['total']
        baseline_strict_pct = baseline_fmt['strict_correct'] / total * 100
        baseline_relaxed_pct = baseline_fmt['relaxed_correct'] / total * 100
        optimized_strict_pct = optimized_fmt['strict_correct'] / total * 100
        optimized_relaxed_pct = optimized_fmt['relaxed_correct'] / total * 100

        report.append(f"\n{fmt_name} ({total} questions):")
        report.append(f"  Baseline:  {baseline_fmt['strict_correct']}/{total} strict ({baseline_strict_pct:.1f}%), "
                     f"{baseline_fmt['relaxed_correct']}/{total} relaxed ({baseline_relaxed_pct:.1f}%)")
        report.append(f"  Optimized: {optimized_fmt['strict_correct']}/{total} strict ({optimized_strict_pct:.1f}%), "
                     f"{optimized_fmt['relaxed_correct']}/{total} relaxed ({optimized_relaxed_pct:.1f}%)")
        report.append(f"  Delta:     Strict {optimized_strict_pct - baseline_strict_pct:+.1f}%, "
                     f"Relaxed {optimized_relaxed_pct - baseline_relaxed_pct:+.1f}%")

    report.append("")

    # False negatives breakdown
    report.append("\n🔍 FALSE NEGATIVES BREAKDOWN")
    report.append("-" * 100)
    report.append(f"\nBASELINE FALSE NEGATIVES: {len(baseline_results['false_negatives'])} cases")
    for fmt, cases in baseline_results['by_format'].items():
        if cases['false_negatives']:
            fmt_name = fmt if fmt else "null"
            report.append(f"  {fmt_name}: {len(cases['false_negatives'])} cases")

    report.append(f"\nOPTIMIZED FALSE NEGATIVES: {len(optimized_results['false_negatives'])} cases")
    for fmt, cases in optimized_results['by_format'].items():
        if cases['false_negatives']:
            fmt_name = fmt if fmt else "null"
            report.append(f"  {fmt_name}: {len(cases['false_negatives'])} cases")

    # Root cause analysis
    report.append("\n\n" + "=" * 100)
    report.append("ROOT CAUSE ANALYSIS")
    report.append("=" * 100)
    report.append("")

    if comparison['relaxed_delta'] < 0:
        report.append(f"⚠️ OPTIMIZATION DEGRADED PERFORMANCE")
        report.append(f"\nRelaxed accuracy: {comparison['baseline_relaxed_pct']:.1f}% → {comparison['optimized_relaxed_pct']:.1f}% ({comparison['relaxed_delta']:.1f}%)")
        report.append(f"\nPossible causes:")
        report.append(f"1. MIPROv2 optimization had dataset mismatch (valset != devset)")
        report.append(f"2. Optimized prompts may have overfitted to train set")
        report.append(f"3. Prompts became too specific, hurting generalization")
        report.append(f"4. Evaluation metric issues masked during optimization")
        report.append(f"\nRecommendation:")
        report.append(f"→ Re-run MIPROv2 with explicit valset=devset parameter")
        report.append(f"→ Use relaxed matching during optimization")
        report.append(f"→ Review optimized prompts for overfitting")
    else:
        report.append(f"✅ OPTIMIZATION IMPROVED PERFORMANCE")
        report.append(f"\nRelaxed accuracy: {comparison['baseline_relaxed_pct']:.1f}% → {comparison['optimized_relaxed_pct']:.1f}% ({comparison['relaxed_delta']:+.1f}%)")

    report.append("")
    report.append("=" * 100)

    return "\n".join(report)

def main():
    print("Loading data...")

    # Load dev set
    with open('dspy_implementation/data_splits/dev_93.json', 'r') as f:
        dev_set = json.load(f)

    # Load baseline predictions (extracted from full dataset)
    print("Loading baseline predictions...")
    with open('baseline_dev_predictions.json', 'r') as f:
        baseline_preds = json.load(f)

    # Load optimized predictions
    print("Loading optimized predictions...")
    with open('optimized_predictions.json', 'r') as f:
        optimized_preds = json.load(f)

    print(f"\nLoaded:")
    print(f"  Dev set: {len(dev_set)} questions")
    print(f"  Baseline predictions: {len(baseline_preds)}")
    print(f"  Optimized predictions: {len(optimized_preds)}")

    # Evaluate baseline
    print("\nEvaluating baseline predictions...")
    baseline_results = evaluate_predictions(dev_set, baseline_preds, "Baseline")

    # Evaluate optimized
    print("Evaluating optimized predictions...")
    optimized_results = evaluate_predictions(dev_set, optimized_preds, "Optimized")

    # Compare
    print("\nComparing results...")
    comparison = compare_models(baseline_results, optimized_results)

    # Generate report
    report = generate_report(baseline_results, optimized_results, comparison)

    # Save report
    with open('baseline_vs_optimized_comparison.txt', 'w') as f:
        f.write(report)

    # Save detailed results
    detailed_results = {
        'baseline': {
            'strict_correct': baseline_results['strict_correct'],
            'relaxed_correct': baseline_results['relaxed_correct'],
            'false_negatives': baseline_results['false_negatives'][:10],  # Top 10
            'by_format': {fmt: {
                'total': stats['total'],
                'strict_correct': stats['strict_correct'],
                'relaxed_correct': stats['relaxed_correct'],
                'fn_count': len(stats['false_negatives'])
            } for fmt, stats in baseline_results['by_format'].items()}
        },
        'optimized': {
            'strict_correct': optimized_results['strict_correct'],
            'relaxed_correct': optimized_results['relaxed_correct'],
            'false_negatives': optimized_results['false_negatives'][:10],  # Top 10
            'by_format': {fmt: {
                'total': stats['total'],
                'strict_correct': stats['strict_correct'],
                'relaxed_correct': stats['relaxed_correct'],
                'fn_count': len(stats['false_negatives'])
            } for fmt, stats in optimized_results['by_format'].items()}
        },
        'comparison': comparison
    }

    with open('baseline_vs_optimized_detailed.json', 'w') as f:
        json.dump(detailed_results, f, indent=2)

    print(f"\n✅ Comparison complete!")
    print(f"📄 Report saved to: baseline_vs_optimized_comparison.txt")
    print(f"📄 Detailed results: baseline_vs_optimized_detailed.json")
    print(f"\n{report}")

if __name__ == '__main__':
    main()
