#!/usr/bin/env python3
"""
Generate baseline predictions for error analysis
"""
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from dspy_implementation.dspy_rag import BaselineMMESGBenchRAG
from dspy_implementation.dspy_metrics import exact_match_metric

def main():
    print("Loading dev set...")
    with open('dspy_implementation/data_splits/dev_93.json', 'r') as f:
        dev_set = json.load(f)

    print(f"Loaded {len(dev_set)} dev questions")

    # Initialize baseline RAG
    print("\nInitializing baseline RAG...")
    baseline_rag = BaselineMMESGBenchRAG()

    # Evaluate and collect predictions
    print("\nEvaluating baseline RAG on dev set...")
    predictions = []

    retrieval_correct = 0
    answer_correct = 0
    end_to_end_correct = 0

    for idx, example in enumerate(dev_set, 1):
        try:
            # Run prediction
            pred = baseline_rag(
                question=example['question'],
                doc_id=example['doc_id']
            )

            # Evaluate
            result = exact_match_metric(
                example=example,
                pred=pred,
                trace=None
            )

            # Store prediction with evaluation
            prediction_record = {
                'question': example['question'],
                'answer': pred.extracted_answer,
                'context': pred.context,
                'doc_id': example['doc_id'],
                'ground_truth': example.get('answer', 'Not answerable'),
                'evidence_pages': example.get('evidence_pages', []),
                'answer_format': example.get('answer_format'),
                'retrieval_correct': result.get('retrieval_correct', False),
                'answer_correct': result.get('answer_correct', False),
                'end_to_end_correct': result.get('end_to_end_correct', False)
            }

            predictions.append(prediction_record)

            # Track metrics
            if result.get('retrieval_correct', False):
                retrieval_correct += 1
            if result.get('answer_correct', False):
                answer_correct += 1
            if result.get('end_to_end_correct', False):
                end_to_end_correct += 1

            if idx % 10 == 0:
                print(f"Processed {idx}/{len(dev_set)} questions")
                print(f"  Current retrieval: {retrieval_correct}/{idx} ({retrieval_correct/idx*100:.1f}%)")
                print(f"  Current answer: {answer_correct}/{idx} ({answer_correct/idx*100:.1f}%)")
                print(f"  Current E2E: {end_to_end_correct}/{idx} ({end_to_end_correct/idx*100:.1f}%)")

        except Exception as e:
            print(f"Error processing question {idx}: {e}")
            predictions.append({
                'question': example['question'],
                'answer': "Error",
                'context': "",
                'doc_id': example['doc_id'],
                'ground_truth': example.get('answer', 'Not answerable'),
                'evidence_pages': example.get('evidence_pages', []),
                'answer_format': example.get('answer_format'),
                'retrieval_correct': False,
                'answer_correct': False,
                'end_to_end_correct': False,
                'error': str(e)
            })

    # Save predictions
    output_file = 'baseline_predictions.json'
    with open(output_file, 'w') as f:
        json.dump(predictions, f, indent=2)

    print(f"\n✅ Saved {len(predictions)} baseline predictions to {output_file}")

    # Print summary
    total = len(predictions)
    print(f"\n📊 Baseline Performance:")
    print(f"  Retrieval: {retrieval_correct}/{total} ({retrieval_correct/total*100:.1f}%)")
    print(f"  Answer: {answer_correct}/{total} ({answer_correct/total*100:.1f}%)")
    print(f"  E2E: {end_to_end_correct}/{total} ({end_to_end_correct/total*100:.1f}%)")

if __name__ == '__main__':
    main()
