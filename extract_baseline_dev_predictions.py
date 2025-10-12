#!/usr/bin/env python3
"""
Extract baseline predictions for dev set from full dataset results
"""
import json

def main():
    # Load dev set
    with open('dspy_implementation/data_splits/dev_93.json', 'r') as f:
        dev_set = json.load(f)

    # Load full dataset baseline results
    with open('dspy_implementation/full_dataset_results/baseline_results_20251010_232606.json', 'r') as f:
        baseline_full = json.load(f)

    # Create mapping from question to prediction
    baseline_map = {}
    for pred in baseline_full['predictions']:
        # Use (question, doc_id) as key
        key = (pred['question'].strip(), pred['doc_id'].strip())
        baseline_map[key] = pred

    print(f"Total baseline predictions: {len(baseline_full['predictions'])}")
    print(f"Unique baseline predictions: {len(baseline_map)}")

    # Extract dev set predictions
    baseline_dev_preds = []
    missing = []

    for dev_q in dev_set:
        key = (dev_q['question'].strip(), dev_q['doc_id'].strip())
        if key in baseline_map:
            baseline_dev_preds.append(baseline_map[key])
        else:
            print(f"Warning: Missing baseline prediction for: {dev_q['question'][:60]}...")
            missing.append(dev_q)
            # Add placeholder
            baseline_dev_preds.append({
                'question': dev_q['question'],
                'predicted_answer': '',
                'ground_truth': dev_q.get('answer'),
                'doc_id': dev_q['doc_id'],
                'answer_format': dev_q.get('answer_format'),
                'evidence_pages': dev_q.get('evidence_pages', [])
            })

    print(f"\nExtracted {len(baseline_dev_preds)} baseline predictions for dev set")
    print(f"Missing: {len(missing)} predictions")

    # Save
    with open('baseline_dev_predictions.json', 'w') as f:
        json.dump(baseline_dev_preds, f, indent=2)

    print(f"\n✅ Saved to: baseline_dev_predictions.json")

if __name__ == '__main__':
    main()
