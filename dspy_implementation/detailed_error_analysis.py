#!/usr/bin/env python3
"""
Detailed Question-Level Error Analysis

Investigates:
1. Evaluator issues (the SyntaxError we hit)
2. Question-by-question comparison: baseline vs GEPA
3. Right→wrong and wrong→right patterns
4. Answer format analysis
5. Actual prediction differences (not just scores)
"""

import os
import sys
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

import dspy
from tqdm import tqdm

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from dspy_implementation.dspy_dataset import MMESGBenchDataset
from dspy_implementation.dspy_rag_enhanced import BaselineMMESGBenchRAG


def safe_eval_score(gt, pred, answer_format):
    """
    Safely evaluate score using corrected evaluator with null equivalence.
    Falls back to simple ANLS if needed.
    """
    try:
        from src.evaluation import eval_score as corrected_eval
        try:
            score = corrected_eval(gt, pred, answer_format)
            return score, "corrected", None
        except Exception as e:
            # Corrected evaluator failed - use our own
            error_msg = str(e)
            score = simple_anls_score(gt, pred, answer_format)
            return score, "fallback", error_msg
    except ImportError:
        # No corrected evaluator available
        score = simple_anls_score(gt, pred, answer_format)
        return score, "simple", "No corrected evaluator"


def simple_anls_score(gt, pred, answer_format):
    """
    Simple ANLS 0.5 implementation as fallback.
    """
    # Normalize strings
    gt_str = str(gt).strip().lower()
    pred_str = str(pred).strip().lower()

    # Handle special cases
    if pred_str in ["not answerable", "fail to answer", ""]:
        if gt_str in ["not answerable", "fail to answer", "", "none", "null"]:
            return 1.0
        return 0.0

    if gt_str in ["not answerable", "fail to answer", "", "none", "null"]:
        return 0.0

    # Exact match
    if gt_str == pred_str:
        return 1.0

    # For lists (try to handle as JSON)
    if answer_format == "List":
        try:
            import ast
            gt_list = ast.literal_eval(gt) if isinstance(gt, str) else gt
            pred_list = ast.literal_eval(pred) if isinstance(pred, str) else pred

            if isinstance(gt_list, list) and isinstance(pred_list, list):
                # Normalize list elements
                gt_set = set(str(x).strip().lower() for x in gt_list)
                pred_set = set(str(x).strip().lower() for x in pred_list)

                if gt_set == pred_set:
                    return 1.0

                # Partial credit (ANLS-like)
                intersection = len(gt_set & pred_set)
                union = len(gt_set | pred_set)
                if union > 0:
                    return intersection / union
        except:
            pass

    # For numbers (Float/Int)
    if answer_format in ["Float", "Int"]:
        try:
            gt_num = float(gt)
            pred_num = float(pred)

            # ±1% tolerance for floats
            if answer_format == "Float":
                tolerance = abs(gt_num * 0.01)
                if abs(gt_num - pred_num) <= tolerance:
                    return 1.0
            else:
                # Exact match for integers
                if gt_num == pred_num:
                    return 1.0
        except:
            pass

    # String similarity (Levenshtein-based ANLS)
    try:
        import Levenshtein
        distance = Levenshtein.distance(gt_str, pred_str)
        max_len = max(len(gt_str), len(pred_str))
        if max_len == 0:
            return 1.0
        similarity = 1.0 - (distance / max_len)
        return similarity
    except ImportError:
        # Fallback: substring matching
        if gt_str in pred_str or pred_str in gt_str:
            return 0.7  # Partial credit
        return 0.0


def load_gepa_predictions():
    """Load GEPA optimized program and get predictions on dev set."""
    print("\n📦 Loading GEPA optimized program...")

    gepa_path = "dspy_implementation/optimized_programs/gepa_skip_baseline_20251018_150806.json"
    if not os.path.exists(gepa_path):
        print(f"   ❌ GEPA program not found: {gepa_path}")
        return None

    gepa_module = BaselineMMESGBenchRAG()
    gepa_module.load(gepa_path)
    print(f"   ✅ Loaded GEPA module")

    return gepa_module


def evaluate_and_compare(dataset, desc="Evaluation"):
    """
    Evaluate both baseline and GEPA, compare question-by-question.
    """
    print("\n" + "="*80)
    print(f"{desc.upper()}")
    print("="*80)

    # Load GEPA
    gepa_module = load_gepa_predictions()
    if gepa_module is None:
        print("❌ Cannot proceed without GEPA module")
        return None

    # Create baseline
    print("\n📦 Creating baseline module...")
    baseline_module = BaselineMMESGBenchRAG()

    # Evaluate both
    results = []
    eval_errors = []

    for i, example in enumerate(tqdm(dataset, desc="Comparing predictions")):
        try:
            # Baseline prediction
            baseline_pred = baseline_module(
                question=example.question,
                doc_id=example.doc_id,
                answer_format=example.answer_format
            )

            # GEPA prediction
            gepa_pred = gepa_module(
                question=example.question,
                doc_id=example.doc_id,
                answer_format=example.answer_format
            )

            # Evaluate both
            baseline_score, baseline_method, baseline_error = safe_eval_score(
                example.answer,
                baseline_pred.answer,
                example.answer_format
            )

            gepa_score, gepa_method, gepa_error = safe_eval_score(
                example.answer,
                gepa_pred.answer,
                example.answer_format
            )

            # Track evaluation errors
            if baseline_error:
                eval_errors.append({
                    'question_id': i,
                    'question': example.question[:100],
                    'format': example.answer_format,
                    'ground_truth': example.answer,
                    'error': baseline_error,
                    'approach': 'baseline'
                })

            if gepa_error:
                eval_errors.append({
                    'question_id': i,
                    'question': example.question[:100],
                    'format': example.answer_format,
                    'ground_truth': example.answer,
                    'error': gepa_error,
                    'approach': 'gepa'
                })

            # Store comparison
            results.append({
                'question_id': i,
                'question': example.question,
                'doc_id': example.doc_id,
                'format': example.answer_format,
                'ground_truth': example.answer,
                'baseline': {
                    'prediction': baseline_pred.answer,
                    'score': baseline_score,
                    'correct': baseline_score >= 0.5,
                    'eval_method': baseline_method,
                    'analysis': baseline_pred.analysis[:200] if hasattr(baseline_pred, 'analysis') else ""
                },
                'gepa': {
                    'prediction': gepa_pred.answer,
                    'score': gepa_score,
                    'correct': gepa_score >= 0.5,
                    'eval_method': gepa_method,
                    'analysis': gepa_pred.analysis[:200] if hasattr(gepa_pred, 'analysis') else ""
                }
            })

        except Exception as e:
            print(f"\n⚠️  Error on question {i}: {e}")
            eval_errors.append({
                'question_id': i,
                'question': example.question[:100],
                'error': str(e),
                'approach': 'both'
            })

    return results, eval_errors


def analyze_results(results, eval_errors):
    """Detailed analysis of question-level results."""
    print("\n" + "="*80)
    print("DETAILED ERROR ANALYSIS")
    print("="*80)

    # 1. Evaluation Method Analysis
    print("\n📊 Evaluation Method Distribution:")
    baseline_methods = defaultdict(int)
    gepa_methods = defaultdict(int)

    for r in results:
        baseline_methods[r['baseline']['eval_method']] += 1
        gepa_methods[r['gepa']['eval_method']] += 1

    print(f"\nBaseline:")
    for method, count in baseline_methods.items():
        print(f"   {method}: {count} questions")

    print(f"\nGEPA:")
    for method, count in gepa_methods.items():
        print(f"   {method}: {count} questions")

    # 2. Evaluation Errors
    if eval_errors:
        print(f"\n⚠️  Evaluation Errors Found: {len(eval_errors)}")
        print("\nSample Errors:")
        for error in eval_errors[:5]:
            print(f"\n   Question {error['question_id']}:")
            print(f"   Q: {error['question']}")
            print(f"   Format: {error.get('format', 'N/A')}")
            print(f"   GT: {error.get('ground_truth', 'N/A')}")
            print(f"   Error: {error['error'][:200]}")

    # 3. Performance Comparison
    baseline_correct = sum(1 for r in results if r['baseline']['correct'])
    gepa_correct = sum(1 for r in results if r['gepa']['correct'])

    print(f"\n📈 Overall Performance:")
    print(f"   Baseline: {baseline_correct}/{len(results)} = {baseline_correct/len(results)*100:.1f}%")
    print(f"   GEPA:     {gepa_correct}/{len(results)} = {gepa_correct/len(results)*100:.1f}%")
    print(f"   Difference: {gepa_correct - baseline_correct} questions ({(gepa_correct - baseline_correct)/len(results)*100:+.1f}%)")

    # 4. Transition Analysis
    right_to_wrong = [r for r in results if r['baseline']['correct'] and not r['gepa']['correct']]
    wrong_to_right = [r for r in results if not r['baseline']['correct'] and r['gepa']['correct']]
    both_right = [r for r in results if r['baseline']['correct'] and r['gepa']['correct']]
    both_wrong = [r for r in results if not r['baseline']['correct'] and not r['gepa']['correct']]

    print(f"\n🔄 Prediction Transitions:")
    print(f"   ✅→✅ Both Correct: {len(both_right)}")
    print(f"   ❌→❌ Both Wrong: {len(both_wrong)}")
    print(f"   ✅→❌ Right→Wrong (DEGRADATION): {len(right_to_wrong)}")
    print(f"   ❌→✅ Wrong→Right (IMPROVEMENT): {len(wrong_to_right)}")

    # 5. Detailed Degradation Analysis
    if right_to_wrong:
        print(f"\n" + "-"*80)
        print(f"DEGRADATION CASES (Baseline ✅ → GEPA ❌): {len(right_to_wrong)}")
        print("-"*80)

        # Group by format
        by_format = defaultdict(list)
        for r in right_to_wrong:
            by_format[r['format']].append(r)

        for fmt, cases in by_format.items():
            print(f"\n{fmt} format: {len(cases)} degradations")

            for i, case in enumerate(cases[:3], 1):  # Show first 3 per format
                print(f"\n{i}. Question {case['question_id']}:")
                print(f"   Q: {case['question'][:100]}...")
                print(f"   GT: {case['ground_truth']}")
                print(f"   Baseline (✅ score={case['baseline']['score']:.2f}): {case['baseline']['prediction']}")
                print(f"   GEPA (❌ score={case['gepa']['score']:.2f}): {case['gepa']['prediction']}")

    # 6. Improvement Analysis
    if wrong_to_right:
        print(f"\n" + "-"*80)
        print(f"IMPROVEMENT CASES (Baseline ❌ → GEPA ✅): {len(wrong_to_right)}")
        print("-"*80)

        # Group by format
        by_format = defaultdict(list)
        for r in wrong_to_right:
            by_format[r['format']].append(r)

        for fmt, cases in by_format.items():
            print(f"\n{fmt} format: {len(cases)} improvements")

            for i, case in enumerate(cases[:3], 1):  # Show first 3 per format
                print(f"\n{i}. Question {case['question_id']}:")
                print(f"   Q: {case['question'][:100]}...")
                print(f"   GT: {case['ground_truth']}")
                print(f"   Baseline (❌ score={case['baseline']['score']:.2f}): {case['baseline']['prediction']}")
                print(f"   GEPA (✅ score={case['gepa']['score']:.2f}): {case['gepa']['prediction']}")

    # 7. Format-Specific Analysis
    print(f"\n" + "-"*80)
    print("FORMAT-SPECIFIC PERFORMANCE")
    print("-"*80)

    by_format = defaultdict(lambda: {'baseline': [], 'gepa': []})
    for r in results:
        fmt = r['format']
        by_format[fmt]['baseline'].append(r['baseline']['correct'])
        by_format[fmt]['gepa'].append(r['gepa']['correct'])

    for fmt in sorted(by_format.keys()):
        baseline_acc = sum(by_format[fmt]['baseline']) / len(by_format[fmt]['baseline']) * 100
        gepa_acc = sum(by_format[fmt]['gepa']) / len(by_format[fmt]['gepa']) * 100
        delta = gepa_acc - baseline_acc

        print(f"\n{fmt}:")
        print(f"   Total: {len(by_format[fmt]['baseline'])} questions")
        print(f"   Baseline: {baseline_acc:.1f}%")
        print(f"   GEPA:     {gepa_acc:.1f}%")
        print(f"   Δ:        {delta:+.1f}%")

    return {
        'transitions': {
            'both_right': both_right,
            'both_wrong': both_wrong,
            'right_to_wrong': right_to_wrong,
            'wrong_to_right': wrong_to_right
        },
        'by_format': dict(by_format),
        'eval_errors': eval_errors
    }


def main():
    print("\n" + "="*80)
    print("DETAILED QUESTION-LEVEL ERROR ANALYSIS")
    print("="*80)
    print("\nInvestigating:")
    print("1. Evaluator issues (SyntaxError in eval_score)")
    print("2. Question-by-question baseline vs GEPA comparison")
    print("3. Right→wrong and wrong→right patterns")
    print("4. Answer format clustering")
    print("5. Actual prediction differences")

    # Load dataset
    print("\n📊 Loading dataset...")
    dataset = MMESGBenchDataset()
    dev_set = dataset.dev_set
    print(f"   Dev set: {len(dev_set)} examples")

    # Configure DSPy
    print("\n🔧 Configuring DSPy with qwen2.5-7b-instruct...")
    student_lm = dspy.LM(
        model='openai/qwen2.5-7b-instruct',
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        api_base='https://dashscope.aliyuncs.com/compatible-mode/v1',
        temperature=0.0,
        max_tokens=1024
    )
    dspy.configure(lm=student_lm)

    # Run comparison
    results, eval_errors = evaluate_and_compare(dev_set, "Baseline vs GEPA Comparison")

    if results is None:
        print("\n❌ Analysis failed")
        return

    # Analyze
    analysis = analyze_results(results, eval_errors)

    # Save detailed report
    report = {
        'timestamp': datetime.now().isoformat(),
        'dataset_size': len(dev_set),
        'results': results,
        'analysis': {
            'transitions': {
                'both_right': len(analysis['transitions']['both_right']),
                'both_wrong': len(analysis['transitions']['both_wrong']),
                'degradations': len(analysis['transitions']['right_to_wrong']),
                'improvements': len(analysis['transitions']['wrong_to_right'])
            },
            'eval_errors': eval_errors
        }
    }

    output_file = f"detailed_error_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n💾 Detailed report saved to: {output_file}")
    print(f"\n✅ Analysis complete!")


if __name__ == "__main__":
    main()
