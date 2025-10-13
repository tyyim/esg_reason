#!/usr/bin/env python3
"""
Calculate exact MMESGBench F1 score for existing results
"""

import json
from mmesgbench_exact_evaluation import eval_acc_and_f1_mmesgbench

def calculate_f1_for_existing_results():
    """Calculate F1 score for our existing results using exact MMESGBench logic"""

    print("📊 Calculating exact MMESGBench F1 score for existing results...")

    # Load our latest results
    with open('optimized_full_dataset_mmesgbench_rescored.json', 'r') as f:
        results = json.load(f)

    # Convert to MMESGBench sample format
    mmesgbench_samples = []
    for result in results['detailed_results']:
        mmesgbench_samples.append({
            'score': result['score'],
            'answer': result['ground_truth'],
            'pred': result['predicted_answer']
        })

    # Calculate exact MMESGBench accuracy and F1
    accuracy, f1_score = eval_acc_and_f1_mmesgbench(mmesgbench_samples)

    print(f"\n📈 MMESGBench Exact Metrics:")
    print(f"Accuracy: {accuracy:.1%} ({accuracy*len(mmesgbench_samples):.0f}/{len(mmesgbench_samples)})")
    print(f"F1 Score: {f1_score:.1%}")

    # Add detailed breakdown
    answerable_samples = [s for s in mmesgbench_samples if s["answer"] != "Not answerable"]
    predicted_answerable = [s for s in mmesgbench_samples if s["pred"] != "Not answerable"]

    if answerable_samples:
        recall = sum([s["score"] for s in answerable_samples]) / len(answerable_samples)
        print(f"Recall: {recall:.1%} (correct answerable / total answerable)")
    else:
        recall = 0.0
        print(f"Recall: N/A (no answerable questions)")

    if predicted_answerable:
        precision = sum([s["score"] for s in predicted_answerable]) / len(predicted_answerable)
        print(f"Precision: {precision:.1%} (correct predictions / predicted answerable)")
    else:
        precision = 0.0
        print(f"Precision: N/A (no answerable predictions)")

    print(f"\nBreakdown:")
    print(f"  Total questions: {len(mmesgbench_samples)}")
    print(f"  Answerable questions: {len(answerable_samples)}")
    print(f"  Predicted answerable: {len(predicted_answerable)}")
    print(f"  Correct answerable: {sum([s['score'] for s in answerable_samples]):.0f}")
    print(f"  Correct predictions: {sum([s['score'] for s in predicted_answerable]):.0f}")

    # Compare with our calculated accuracy
    our_accuracy = results['accuracy']
    print(f"\n🔍 Comparison:")
    print(f"Our accuracy: {our_accuracy:.1%}")
    print(f"MMESGBench accuracy: {accuracy:.1%}")
    print(f"Difference: {accuracy - our_accuracy:.3%}")

    if abs(accuracy - our_accuracy) < 0.001:
        print("✅ Accuracies match - evaluation is correctly aligned!")
    else:
        print("⚠️ Accuracies differ - there may be an evaluation discrepancy")

    # Update results with F1 score
    results['mmesgbench_f1_score'] = f1_score
    results['mmesgbench_accuracy'] = accuracy
    results['evaluation_breakdown'] = {
        'total_questions': len(mmesgbench_samples),
        'answerable_questions': len(answerable_samples),
        'predicted_answerable': len(predicted_answerable),
        'recall': recall,
        'precision': precision,
        'f1_score': f1_score
    }

    # Save updated results
    output_file = 'optimized_full_dataset_mmesgbench_with_f1.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Updated results saved to: {output_file}")

    return accuracy, f1_score

if __name__ == "__main__":
    calculate_f1_for_existing_results()