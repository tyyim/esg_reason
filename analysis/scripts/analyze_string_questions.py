#!/usr/bin/env python3
"""
Analyze String type questions to understand GEPA's -5.9% degradation.
Compare gold answers vs predictions to identify evaluator strictness issues.
"""

import json
import os
from typing import Dict, List

def load_json(filepath: str) -> Dict:
    """Load JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_string_questions():
    """Analyze String type questions across all approaches."""

    # Load CORRECT dev set (dev_93.json, not full dataset!)
    dataset = load_json('dspy_implementation/data_splits/dev_93.json')

    # Load predictions (they use dict structure with question IDs as keys)
    baseline_preds = load_json('baseline_dev_predictions_20251019_130401.json')['predictions']
    miprov2_preds = load_json('miprov2_dev_predictions_20251019_130401.json')['predictions']
    gepa_preds = load_json('gepa_dev_predictions_20251019_130401.json')['predictions']

    # Filter String type questions
    string_questions = []
    for idx, item in enumerate(dataset):
        question_id = f"q{idx}"

        # Check if this is a String type question
        if item.get('answer_format') == 'Str':
            # Get predictions
            baseline_pred = baseline_preds[question_id]
            miprov2_pred = miprov2_preds.get(question_id)
            gepa_pred = gepa_preds.get(question_id)

            if baseline_pred and miprov2_pred and gepa_pred:
                # Evaluate scores
                gt_answer = item['answer']

                # Extract the actual answer (stored in 'analysis' field)
                baseline_answer = baseline_pred.get('analysis', '')
                miprov2_answer = miprov2_pred.get('analysis', '')
                gepa_answer = gepa_pred.get('analysis', '')

                baseline_score = baseline_pred.get('score', 0.0)
                miprov2_score = miprov2_pred.get('score', 0.0)
                gepa_score = gepa_pred.get('score', 0.0)

                string_questions.append({
                    'id': question_id,
                    'question': item['question'],
                    'doc_id': item['doc_id'],
                    'gold_answer': gt_answer,
                    'gold_sources': item.get('source', []),
                    'baseline': {
                        'answer': baseline_answer,
                        'score': baseline_score,
                        'correct': baseline_score >= 0.5
                    },
                    'miprov2': {
                        'answer': miprov2_answer,
                        'score': miprov2_score,
                        'correct': miprov2_score >= 0.5
                    },
                    'gepa': {
                        'answer': gepa_answer,
                        'score': gepa_score,
                        'correct': gepa_score >= 0.5
                    }
                })

    print(f"\n{'='*80}")
    print(f"STRING TYPE QUESTIONS ANALYSIS ({len(string_questions)} questions)")
    print(f"{'='*80}\n")

    # Overall accuracy
    baseline_correct = sum(1 for q in string_questions if q['baseline']['correct'])
    miprov2_correct = sum(1 for q in string_questions if q['miprov2']['correct'])
    gepa_correct = sum(1 for q in string_questions if q['gepa']['correct'])

    print(f"Overall Accuracy:")
    print(f"  Baseline: {baseline_correct}/{len(string_questions)} = {baseline_correct/len(string_questions)*100:.1f}%")
    print(f"  MIPROv2:  {miprov2_correct}/{len(string_questions)} = {miprov2_correct/len(string_questions)*100:.1f}%")
    print(f"  GEPA:     {gepa_correct}/{len(string_questions)} = {gepa_correct/len(string_questions)*100:.1f}%")
    print()

    # Category 1: Baseline correct, GEPA wrong (degradations)
    degradations = [q for q in string_questions if q['baseline']['correct'] and not q['gepa']['correct']]
    print(f"\n{'='*80}")
    print(f"CATEGORY 1: GEPA DEGRADATIONS ({len(degradations)} cases)")
    print(f"Baseline ✅ → GEPA ❌")
    print(f"{'='*80}\n")

    for i, q in enumerate(degradations, 1):
        print(f"\n--- Degradation {i}/{len(degradations)} ---")
        print(f"Question ID: {q['id']}")
        print(f"Document: {q['doc_id']}")
        print(f"Question: {q['question']}")
        print(f"\nGold Answer: '{q['gold_answer']}'")
        print(f"Gold Sources: {q['gold_sources']}")
        print(f"\nBaseline Answer: '{q['baseline']['answer']}' (score: {q['baseline']['score']:.3f}) ✅")
        print(f"MIPROv2 Answer:  '{q['miprov2']['answer']}' (score: {q['miprov2']['score']:.3f}) {'✅' if q['miprov2']['correct'] else '❌'}")
        print(f"GEPA Answer:     '{q['gepa']['answer']}' (score: {q['gepa']['score']:.3f}) ❌")

        # Check if GEPA's answer is semantically similar but scored low
        if q['gepa']['score'] > 0.3:  # Close but not passing 0.5 threshold
            print(f"  ⚠️  GEPA score {q['gepa']['score']:.3f} is close to threshold (0.5) - possible evaluator strictness issue")

    # Category 2: Baseline wrong, GEPA correct (improvements)
    improvements = [q for q in string_questions if not q['baseline']['correct'] and q['gepa']['correct']]
    print(f"\n{'='*80}")
    print(f"CATEGORY 2: GEPA IMPROVEMENTS ({len(improvements)} cases)")
    print(f"Baseline ❌ → GEPA ✅")
    print(f"{'='*80}\n")

    for i, q in enumerate(improvements, 1):
        print(f"\n--- Improvement {i}/{len(improvements)} ---")
        print(f"Question ID: {q['id']}")
        print(f"Document: {q['doc_id']}")
        print(f"Question: {q['question']}")
        print(f"\nGold Answer: '{q['gold_answer']}'")
        print(f"Gold Sources: {q['gold_sources']}")
        print(f"\nBaseline Answer: '{q['baseline']['answer']}' (score: {q['baseline']['score']:.3f}) ❌")
        print(f"MIPROv2 Answer:  '{q['miprov2']['answer']}' (score: {q['miprov2']['score']:.3f}) {'✅' if q['miprov2']['correct'] else '❌'}")
        print(f"GEPA Answer:     '{q['gepa']['answer']}' (score: {q['gepa']['score']:.3f}) ✅")

    # Category 3: Near-miss cases (score 0.3-0.5)
    near_misses = [q for q in string_questions
                   if (q['gepa']['score'] >= 0.3 and q['gepa']['score'] < 0.5)]

    print(f"\n{'='*80}")
    print(f"CATEGORY 3: GEPA NEAR-MISSES ({len(near_misses)} cases)")
    print(f"ANLS score 0.3-0.5 (may indicate evaluator too strict)")
    print(f"{'='*80}\n")

    for i, q in enumerate(near_misses, 1):
        print(f"\n--- Near-Miss {i}/{len(near_misses)} ---")
        print(f"Question ID: {q['id']}")
        print(f"Question: {q['question']}")
        print(f"\nGold Answer: '{q['gold_answer']}'")
        print(f"GEPA Answer: '{q['gepa']['answer']}' (score: {q['gepa']['score']:.3f})")
        print(f"Baseline Answer: '{q['baseline']['answer']}' (score: {q['baseline']['score']:.3f})")
        print(f"\n  ⚠️  GEPA answer is semantically close but below 0.5 threshold")
        print(f"      This may indicate the evaluator is being too strict.")

    # Category 4: Both wrong - compare similarity
    both_wrong = [q for q in string_questions
                  if not q['baseline']['correct'] and not q['gepa']['correct']]

    print(f"\n{'='*80}")
    print(f"CATEGORY 4: BOTH WRONG ({len(both_wrong)} cases)")
    print(f"Compare GEPA vs Baseline scores")
    print(f"{'='*80}\n")

    gepa_better = [q for q in both_wrong if q['gepa']['score'] > q['baseline']['score']]
    baseline_better = [q for q in both_wrong if q['baseline']['score'] > q['gepa']['score']]
    same_score = [q for q in both_wrong if q['gepa']['score'] == q['baseline']['score']]

    print(f"When both wrong:")
    print(f"  GEPA closer to answer: {len(gepa_better)} cases")
    print(f"  Baseline closer: {len(baseline_better)} cases")
    print(f"  Same distance: {len(same_score)} cases")

    if gepa_better:
        print(f"\nGEPA was closer in these cases:")
        for q in gepa_better[:3]:  # Show top 3
            print(f"\n  Q: {q['question']}")
            print(f"  Gold: '{q['gold_answer']}'")
            print(f"  Baseline: '{q['baseline']['answer']}' (score: {q['baseline']['score']:.3f})")
            print(f"  GEPA: '{q['gepa']['answer']}' (score: {q['gepa']['score']:.3f})")

    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}\n")

    print(f"Total String questions: {len(string_questions)}")
    print(f"\nDegradations (Baseline ✅ → GEPA ❌): {len(degradations)}")
    print(f"Improvements (Baseline ❌ → GEPA ✅): {len(improvements)}")
    print(f"Net change: {len(improvements) - len(degradations)} ({(len(improvements) - len(degradations))/len(string_questions)*100:+.1f}%)")
    print(f"\nNear-misses (0.3 ≤ ANLS < 0.5): {len(near_misses)}")
    print(f"  → Potential evaluator strictness issues")

    # Save detailed results
    output = {
        'total_questions': len(string_questions),
        'accuracy': {
            'baseline': baseline_correct / len(string_questions),
            'miprov2': miprov2_correct / len(string_questions),
            'gepa': gepa_correct / len(string_questions)
        },
        'degradations': [
            {
                'id': q['id'],
                'question': q['question'],
                'doc_id': q['doc_id'],
                'gold_answer': q['gold_answer'],
                'gold_sources': q['gold_sources'],
                'baseline_answer': q['baseline']['answer'],
                'baseline_score': q['baseline']['score'],
                'gepa_answer': q['gepa']['answer'],
                'gepa_score': q['gepa']['score'],
                'possibly_too_strict': q['gepa']['score'] >= 0.3
            }
            for q in degradations
        ],
        'improvements': [
            {
                'id': q['id'],
                'question': q['question'],
                'doc_id': q['doc_id'],
                'gold_answer': q['gold_answer'],
                'gold_sources': q['gold_sources'],
                'baseline_answer': q['baseline']['answer'],
                'baseline_score': q['baseline']['score'],
                'gepa_answer': q['gepa']['answer'],
                'gepa_score': q['gepa']['score']
            }
            for q in improvements
        ],
        'near_misses': [
            {
                'id': q['id'],
                'question': q['question'],
                'gold_answer': q['gold_answer'],
                'gepa_answer': q['gepa']['answer'],
                'gepa_score': q['gepa']['score'],
                'baseline_score': q['baseline']['score']
            }
            for q in near_misses
        ]
    }

    output_file = 'string_questions_detailed_analysis.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nDetailed analysis saved to: {output_file}")

if __name__ == '__main__':
    analyze_string_questions()
