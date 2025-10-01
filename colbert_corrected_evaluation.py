#!/usr/bin/env python3
"""
ColBERT evaluation for corrected documents:
1. Microsoft CDP: Use corrected_ground_truth_answers.json
2. Gender 2024.pdf: Re-run with correct document

Uses optimized_colbert_evaluator_mmesgbench.py infrastructure
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from optimized_colbert_evaluator_mmesgbench import OptimizedColBERTEvaluatorMMESGBench

# Paths
BASE_DIR = Path("/Users/victoryim/Local_Git/CC")
SAMPLES_PATH = BASE_DIR / "MMESGBench/dataset/samples.json"
CORRECTED_GT_PATH = BASE_DIR / "corrected_ground_truth_answers.json"
RESULTS_DIR = BASE_DIR / "corrected_evaluation_results"
RESULTS_DIR.mkdir(exist_ok=True)

def load_samples() -> List[Dict[str, Any]]:
    """Load all questions from samples.json"""
    with open(SAMPLES_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_corrected_microsoft_gt() -> Dict[str, Dict[str, Any]]:
    """Load corrected Microsoft ground truth answers"""
    with open(CORRECTED_GT_PATH, 'r', encoding='utf-8') as f:
        corrected_data = json.load(f)

    # Create lookup by question text
    gt_lookup = {}
    for item in corrected_data:
        if item['doc_id'] == "Microsoft CDP Climate Change Response 2024.pdf":
            gt_lookup[item['question']] = item

    print(f"📊 Loaded {len(gt_lookup)} corrected Microsoft questions")
    return gt_lookup

def prepare_evaluation_questions() -> List[Dict[str, Any]]:
    """
    Prepare questions for evaluation:
    - Microsoft: Use corrected ground truth (doc_id is 2023 in samples but 2024 in corrected GT)
    - Gender 2024: Use original samples.json
    """
    all_samples = load_samples()
    corrected_microsoft_gt = load_corrected_microsoft_gt()

    eval_questions = []

    # Process Microsoft questions with corrected GT
    # Note: samples.json has "2023.pdf" but corrected GT has "2024.pdf"
    microsoft_doc_samples = "Microsoft CDP Climate Change Response 2023.pdf"
    microsoft_doc_corrected = "Microsoft CDP Climate Change Response 2024.pdf"

    for q in all_samples:
        if q['doc_id'] == microsoft_doc_samples:
            question_text = q['question']
            if question_text in corrected_microsoft_gt:
                # Use corrected ground truth
                corrected_q = corrected_microsoft_gt[question_text].copy()
                # Use 2024 doc_id to match the actual file
                eval_questions.append({
                    'doc_id': microsoft_doc_corrected,
                    'doc_type': q.get('doc_type', 'CDP Climate Responses'),
                    'question': question_text,
                    'answer': corrected_q['answer'],
                    'evidence_pages': corrected_q.get('evidence_pages', []),
                    'evidence_sources': corrected_q.get('evidence_sources', []),
                    'answer_format': corrected_q.get('answer_format', 'Str')
                })
            else:
                # Keep original if not in corrected GT (with 2024 doc_id)
                q_updated = q.copy()
                q_updated['doc_id'] = microsoft_doc_corrected
                eval_questions.append(q_updated)

    # Add Gender 2024 questions (use original)
    gender_doc = "Gender 2024.pdf"
    for q in all_samples:
        if q['doc_id'] == gender_doc:
            eval_questions.append(q)

    print(f"\n📋 Prepared evaluation questions:")
    print(f"   Microsoft CDP: {sum(1 for q in eval_questions if 'Microsoft' in q['doc_id'])}")
    print(f"   Gender 2024: {sum(1 for q in eval_questions if q['doc_id'] == gender_doc)}")
    print(f"   Total: {len(eval_questions)}")

    return eval_questions

def main():
    """Main ColBERT evaluation pipeline"""
    print("=" * 80)
    print("🔄 COLBERT CORRECTED EVALUATION")
    print("=" * 80)

    # Prepare questions
    eval_questions = prepare_evaluation_questions()

    # Initialize evaluator
    print("\n📝 Initializing ColBERT evaluator...")
    evaluator = OptimizedColBERTEvaluatorMMESGBench(batch_size=10)

    # Run evaluation
    print("\n🚀 Starting ColBERT evaluation...")
    results = evaluator.evaluate_with_precomputed(eval_questions)

    # Print results
    print("\n" + "=" * 80)
    print("📊 COLBERT EVALUATION RESULTS")
    print("=" * 80)
    print(f"\nOverall Performance:")
    print(f"  Accuracy: {results['accuracy']:.1%} ({results['total_score']:.0f}/{results['total_questions']})")
    print(f"  MMESGBench Accuracy: {results['mmesgbench_accuracy']:.1%}")
    print(f"  MMESGBench F1 Score: {results['mmesgbench_f1_score']:.1%}")
    print(f"  Total Time: {results['total_time']:.1f}s")
    print(f"  Avg Time/Question: {results['avg_processing_time']:.1f}s")

    # Per-document breakdown
    print(f"\n📄 Per-Document Breakdown:")
    for doc, stats in results['document_breakdown'].items():
        print(f"\n  {doc}:")
        print(f"    Accuracy: {stats['accuracy']:.1%} ({stats['correct']:.0f}/{stats['total']})")
        print(f"    Avg F1: {stats['avg_f1']:.1%}")

    # Format breakdown
    print(f"\n📋 Per-Format Breakdown:")
    for fmt, stats in results['format_breakdown'].items():
        print(f"  {fmt}: {stats['accuracy']:.1%} ({stats['correct']:.0f}/{stats['total']}) | F1: {stats['avg_f1']:.1%}")

    # Save results
    output_file = RESULTS_DIR / "colbert_corrected_evaluation.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Results saved: {output_file}")
    print("\n✅ ColBERT corrected evaluation complete!")

if __name__ == "__main__":
    main()
