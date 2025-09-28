#!/usr/bin/env python3
"""
Detailed Analysis of Evaluation Metric Discrepancies
Compares our current evaluation logic with MMESGBench's exact implementation
"""

import json
from mmesgbench_exact_evaluation import evaluate_prediction_mmesgbench, eval_score
from colbert_full_dataset_evaluation import MMESGBenchEvaluator

def compare_evaluation_methods():
    """Compare our evaluation with MMESGBench's exact evaluation on sample data"""

    print("🔍 Detailed Evaluation Comparison Analysis")
    print("=" * 60)

    # Load our latest results to analyze evaluation differences
    with open('optimized_full_dataset_fixed_results.json', 'r') as f:
        our_results = json.load(f)

    print(f"📊 Analyzing {len(our_results['detailed_results'])} questions...")

    # Initialize our evaluator
    our_evaluator = MMESGBenchEvaluator()

    # Track differences
    differences = []
    our_correct = 0
    mmesgbench_correct = 0

    # Analyze first 50 questions for detailed comparison
    sample_size = min(50, len(our_results['detailed_results']))

    print(f"\n🧪 Testing first {sample_size} questions for detailed analysis:")
    print("-" * 60)

    for i, result in enumerate(our_results['detailed_results'][:sample_size]):
        predicted = result['predicted_answer']
        ground_truth = result['ground_truth']
        answer_format = result['answer_format']

        # Our evaluation
        our_correct_bool, our_exact, our_f1 = our_evaluator.evaluate_prediction(
            predicted, ground_truth, answer_format
        )

        # MMESGBench evaluation
        mmesg_correct_bool, mmesg_exact, mmesg_f1 = evaluate_prediction_mmesgbench(
            predicted, ground_truth, answer_format
        )

        # Track totals
        if our_correct_bool:
            our_correct += 1
        if mmesg_correct_bool:
            mmesgbench_correct += 1

        # Check for differences
        if our_correct_bool != mmesg_correct_bool:
            differences.append({
                'question_num': i + 1,
                'question': result['question'][:100] + "..." if len(result['question']) > 100 else result['question'],
                'predicted': predicted,
                'ground_truth': ground_truth,
                'format': answer_format,
                'our_result': our_correct_bool,
                'mmesg_result': mmesg_correct_bool,
                'our_f1': our_f1,
                'mmesg_f1': mmesg_f1
            })

        # Show detailed comparison for first few differences
        if len(differences) <= 5 and our_correct_bool != mmesg_correct_bool:
            print(f"\n❌ DIFFERENCE #{len(differences)} (Question {i+1}):")
            print(f"   Question: {result['question'][:80]}...")
            print(f"   Format: {answer_format}")
            print(f"   Predicted: '{predicted}'")
            print(f"   Ground Truth: '{ground_truth}'")
            print(f"   Our Evaluation: {our_correct_bool} (F1: {our_f1:.3f})")
            print(f"   MMESGBench: {mmesg_correct_bool} (F1: {mmesg_f1:.3f})")

            # Show detailed evaluation logic
            if answer_format.lower() in ["int", "integer"]:
                print(f"   🔍 Numeric evaluation difference detected")
            elif answer_format.lower() == "float":
                print(f"   🔍 Float evaluation difference detected")
            elif answer_format.lower() == "str":
                print(f"   🔍 String evaluation difference detected")
            elif answer_format.lower() == "list":
                print(f"   🔍 List evaluation difference detected")

    # Summary statistics
    our_accuracy = our_correct / sample_size * 100
    mmesg_accuracy = mmesgbench_correct / sample_size * 100
    accuracy_difference = mmesg_accuracy - our_accuracy

    print(f"\n📈 SAMPLE EVALUATION COMPARISON ({sample_size} questions):")
    print(f"Our Evaluation:     {our_correct}/{sample_size} = {our_accuracy:.1f}%")
    print(f"MMESGBench Logic:   {mmesgbench_correct}/{sample_size} = {mmesg_accuracy:.1f}%")
    print(f"Accuracy Difference: {accuracy_difference:+.1f}%")
    print(f"Total Differences:   {len(differences)} questions")

    if accuracy_difference > 0:
        print(f"✅ MMESGBench evaluation is MORE LENIENT (+{accuracy_difference:.1f}%)")
    elif accuracy_difference < 0:
        print(f"🔴 MMESGBench evaluation is MORE STRICT ({accuracy_difference:.1f}%)")
    else:
        print(f"⚪ Both evaluations are EQUIVALENT")

    # Extrapolate to full dataset
    if len(differences) > 0:
        projected_difference = (accuracy_difference / 100) * our_results['total_questions']
        print(f"\n🎯 PROJECTED FULL DATASET IMPACT:")
        print(f"Current Accuracy: {our_results['accuracy']:.1%} ({our_results['total_score']:.0f}/{our_results['total_questions']})")
        print(f"Projected with MMESGBench logic: {our_results['accuracy'] + accuracy_difference/100:.1%} ({our_results['total_score'] + projected_difference:.0f}/{our_results['total_questions']})")
        print(f"Expected gain: ~{projected_difference:.0f} additional correct answers")

    # Detailed difference analysis by format
    print(f"\n📋 DIFFERENCE BREAKDOWN BY FORMAT:")
    format_differences = {}
    for diff in differences:
        fmt = diff['format']
        if fmt not in format_differences:
            format_differences[fmt] = {'our_strict': 0, 'mmesg_lenient': 0}

        if not diff['our_result'] and diff['mmesg_result']:
            format_differences[fmt]['mmesg_lenient'] += 1
        elif diff['our_result'] and not diff['mmesg_result']:
            format_differences[fmt]['our_strict'] += 1

    for fmt, counts in format_differences.items():
        total_format_diffs = counts['our_strict'] + counts['mmesg_lenient']
        print(f"  {fmt}: {total_format_diffs} differences")
        if counts['mmesg_lenient'] > 0:
            print(f"    - MMESGBench more lenient: {counts['mmesg_lenient']}")
        if counts['our_strict'] > 0:
            print(f"    - Our evaluation more strict: {counts['our_strict']}")

    # Save detailed analysis
    analysis_result = {
        'sample_size': sample_size,
        'our_accuracy': our_accuracy,
        'mmesgbench_accuracy': mmesg_accuracy,
        'accuracy_difference': accuracy_difference,
        'total_differences': len(differences),
        'differences_by_format': format_differences,
        'detailed_differences': differences[:10],  # Save first 10 for review
        'projected_full_dataset_gain': projected_difference if len(differences) > 0 else 0
    }

    with open('evaluation_comparison_analysis.json', 'w') as f:
        json.dump(analysis_result, f, indent=2)

    print(f"\n✅ Detailed analysis saved to: evaluation_comparison_analysis.json")

    return analysis_result

def test_specific_cases():
    """Test specific evaluation edge cases that might cause differences"""

    print(f"\n🧪 TESTING SPECIFIC EDGE CASES:")
    print("-" * 40)

    test_cases = [
        # Numeric tolerance cases
        ("3.0", "3", "Int", "Integer parsing"),
        ("1.001", "1.0", "Float", "Float tolerance"),
        ("19.62", "19.6", "Float", "Float precision"),

        # String matching cases
        ("North America", "north america", "Str", "Case sensitivity"),
        ("CO2", "CO₂", "Str", "Special characters"),
        ("Not answerable", "not answerable", "Str", "Unanswerable case"),

        # List parsing cases
        ("['A', 'B']", "['A', 'B', 'C']", "List", "Partial list match"),
        ("[\"item1\", \"item2\"]", "item1, item2", "List", "List format parsing"),
    ]

    our_evaluator = MMESGBenchEvaluator()

    for predicted, ground_truth, fmt, description in test_cases:
        our_result, _, our_f1 = our_evaluator.evaluate_prediction(predicted, ground_truth, fmt)
        mmesg_result, _, mmesg_f1 = evaluate_prediction_mmesgbench(predicted, ground_truth, fmt)

        status = "✅" if our_result == mmesg_result else "❌"
        print(f"{status} {description}:")
        print(f"    Pred: '{predicted}' | GT: '{ground_truth}' | Format: {fmt}")
        print(f"    Our: {our_result} (F1: {our_f1:.3f}) | MMESGBench: {mmesg_result} (F1: {mmesg_f1:.3f})")

        if our_result != mmesg_result:
            print(f"    🔍 DIFFERENCE: Our evaluation {'more strict' if not our_result else 'more lenient'}")
        print()

if __name__ == "__main__":
    print("🚀 Starting Comprehensive Evaluation Comparison...")

    # Run main comparison
    analysis = compare_evaluation_methods()

    # Run specific test cases
    test_specific_cases()

    # Final recommendation
    print(f"\n🎯 RECOMMENDATION:")
    if analysis['accuracy_difference'] > 2.0:
        print(f"✅ IMPLEMENT MMESGBench evaluation logic immediately")
        print(f"   Expected gain: ~{analysis['projected_full_dataset_gain']:.0f} additional correct answers")
        print(f"   Accuracy improvement: +{analysis['accuracy_difference']:.1f}%")
    elif analysis['accuracy_difference'] > 0.5:
        print(f"⚠️ Consider implementing MMESGBench evaluation logic")
        print(f"   Expected gain: ~{analysis['projected_full_dataset_gain']:.0f} additional correct answers")
    else:
        print(f"✅ Current evaluation logic is aligned with MMESGBench")
        print(f"   Difference is minimal ({analysis['accuracy_difference']:.1f}%)")