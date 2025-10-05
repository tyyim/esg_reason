#!/usr/bin/env python3
"""
Re-run evaluations with corrected documents and ground truth:
1. Microsoft CDP: Use corrected_ground_truth_answers.json
2. Gender 2024.pdf: Re-run RAG with correct document
3. ISO-14001-2015.pdf: Keep existing (note: wrong doc)

This script will:
- Load corrected Microsoft ground truth
- Re-evaluate Gender 2024.pdf questions with ColBERT/ColPali
- Aggregate final accuracy metrics
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any
from mmesgbench_retrieval_replication import (
    ColBERTTextRAG,
    ColPaliVisualRAG,
    MMESGBenchEvaluator
)

# Paths
BASE_DIR = Path("/Users/victoryim/Local_Git/CC")
SAMPLES_PATH = BASE_DIR / "MMESGBench/dataset/samples.json"
CORRECTED_GT_PATH = BASE_DIR / "corrected_ground_truth_answers.json"
SOURCE_DOCS_DIR = BASE_DIR / "source_documents"
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

def filter_questions_by_doc(samples: List[Dict], doc_id: str) -> List[Dict]:
    """Filter questions for specific document"""
    return [q for q in samples if q['doc_id'] == doc_id]

def evaluate_document_colbert(doc_id: str, questions: List[Dict],
                               corrected_gt: Dict = None) -> Dict[str, Any]:
    """
    Evaluate a document using ColBERT Text RAG

    Args:
        doc_id: Document identifier
        questions: List of questions for this document
        corrected_gt: Optional corrected ground truth lookup
    """
    print(f"\n🔍 Evaluating {doc_id} with ColBERT Text RAG")
    print(f"   Questions: {len(questions)}")

    # Initialize ColBERT RAG
    pdf_path = SOURCE_DOCS_DIR / doc_id
    if not pdf_path.exists():
        print(f"❌ Document not found: {pdf_path}")
        return None

    rag = ColBERTTextRAG(str(pdf_path))

    # Process questions
    results = []
    correct = 0
    total = 0

    for q in questions:
        question_text = q['question']

        # Use corrected GT if available, otherwise use original
        if corrected_gt and question_text in corrected_gt:
            expected_answer = corrected_gt[question_text]['answer']
            evidence_pages = corrected_gt[question_text]['evidence_pages']
        else:
            expected_answer = q['answer']
            evidence_pages = q.get('evidence_pages', [])

        # Skip "Not answerable" questions
        if expected_answer == "Not answerable":
            continue

        # Get RAG answer
        try:
            answer = rag.answer_question(question_text)
            is_correct = MMESGBenchEvaluator.compare_answers(
                answer, expected_answer, q.get('answer_format', 'Str')
            )

            if is_correct:
                correct += 1
            total += 1

            results.append({
                'question': question_text,
                'predicted': answer,
                'expected': expected_answer,
                'correct': is_correct,
                'evidence_pages': evidence_pages
            })

            print(f"   {'✅' if is_correct else '❌'} Q{total}: {question_text[:60]}...")

        except Exception as e:
            print(f"   ⚠️  Error processing question: {str(e)}")
            continue

    accuracy = (correct / total * 100) if total > 0 else 0.0

    print(f"\n📊 {doc_id} ColBERT Results:")
    print(f"   Correct: {correct}/{total} = {accuracy:.1f}%")

    return {
        'doc_id': doc_id,
        'method': 'ColBERT Text RAG',
        'total_questions': total,
        'correct': correct,
        'accuracy': accuracy,
        'results': results
    }

def evaluate_document_colpali(doc_id: str, questions: List[Dict],
                               corrected_gt: Dict = None) -> Dict[str, Any]:
    """
    Evaluate a document using ColPali Visual RAG

    Args:
        doc_id: Document identifier
        questions: List of questions for this document
        corrected_gt: Optional corrected ground truth lookup
    """
    print(f"\n🔍 Evaluating {doc_id} with ColPali Visual RAG")
    print(f"   Questions: {len(questions)}")

    # Initialize ColPali RAG
    pdf_path = SOURCE_DOCS_DIR / doc_id
    if not pdf_path.exists():
        print(f"❌ Document not found: {pdf_path}")
        return None

    rag = ColPaliVisualRAG(str(pdf_path))

    # Process questions
    results = []
    correct = 0
    total = 0

    for q in questions:
        question_text = q['question']

        # Use corrected GT if available, otherwise use original
        if corrected_gt and question_text in corrected_gt:
            expected_answer = corrected_gt[question_text]['answer']
            evidence_pages = corrected_gt[question_text]['evidence_pages']
        else:
            expected_answer = q['answer']
            evidence_pages = q.get('evidence_pages', [])

        # Skip "Not answerable" questions
        if expected_answer == "Not answerable":
            continue

        # Get RAG answer
        try:
            answer = rag.answer_question(question_text)
            is_correct = MMESGBenchEvaluator.compare_answers(
                answer, expected_answer, q.get('answer_format', 'Str')
            )

            if is_correct:
                correct += 1
            total += 1

            results.append({
                'question': question_text,
                'predicted': answer,
                'expected': expected_answer,
                'correct': is_correct,
                'evidence_pages': evidence_pages
            })

            print(f"   {'✅' if is_correct else '❌'} Q{total}: {question_text[:60]}...")

        except Exception as e:
            print(f"   ⚠️  Error processing question: {str(e)}")
            continue

    accuracy = (correct / total * 100) if total > 0 else 0.0

    print(f"\n📊 {doc_id} ColPali Results:")
    print(f"   Correct: {correct}/{total} = {accuracy:.1f}%")

    return {
        'doc_id': doc_id,
        'method': 'ColPali Visual RAG',
        'total_questions': total,
        'correct': correct,
        'accuracy': accuracy,
        'results': results
    }

def main():
    """Main evaluation pipeline"""
    print("=" * 80)
    print("🔄 CORRECTED EVALUATION PIPELINE")
    print("=" * 80)

    # Load data
    print("\n📂 Loading data...")
    all_samples = load_samples()
    corrected_microsoft_gt = load_corrected_microsoft_gt()

    # Documents to evaluate
    docs_to_evaluate = [
        ("Microsoft CDP Climate Change Response 2024.pdf", True),  # Use corrected GT
        ("Gender 2024.pdf", False),  # Use original samples.json
        # ISO-14001-2015.pdf skipped (wrong doc, keep old results)
    ]

    all_results = {
        'colbert': [],
        'colpali': []
    }

    # Evaluate each document
    for doc_id, use_corrected_gt in docs_to_evaluate:
        print(f"\n{'=' * 80}")
        print(f"📄 Processing: {doc_id}")
        print(f"   Using corrected GT: {use_corrected_gt}")
        print('=' * 80)

        # Filter questions
        questions = filter_questions_by_doc(all_samples, doc_id)
        corrected_gt = corrected_microsoft_gt if use_corrected_gt else None

        # ColBERT evaluation
        colbert_result = evaluate_document_colbert(doc_id, questions, corrected_gt)
        if colbert_result:
            all_results['colbert'].append(colbert_result)

            # Save individual result
            output_path = RESULTS_DIR / f"{doc_id.replace('.pdf', '')}_colbert.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(colbert_result, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved: {output_path}")

        # ColPali evaluation
        colpali_result = evaluate_document_colpali(doc_id, questions, corrected_gt)
        if colpali_result:
            all_results['colpali'].append(colpali_result)

            # Save individual result
            output_path = RESULTS_DIR / f"{doc_id.replace('.pdf', '')}_colpali.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(colpali_result, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved: {output_path}")

    # Calculate aggregate metrics
    print("\n" + "=" * 80)
    print("📊 FINAL AGGREGATE RESULTS")
    print("=" * 80)

    for method in ['colbert', 'colpali']:
        results = all_results[method]
        if not results:
            continue

        total_correct = sum(r['correct'] for r in results)
        total_questions = sum(r['total_questions'] for r in results)
        overall_accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0.0

        print(f"\n🎯 {method.upper()} Text RAG:" if method == 'colbert' else f"\n🎯 {method.upper()} Visual RAG:")
        print(f"   Documents evaluated: {len(results)}")
        print(f"   Total questions: {total_questions}")
        print(f"   Correct answers: {total_correct}")
        print(f"   Overall accuracy: {overall_accuracy:.1f}%")

        # Per-document breakdown
        print(f"\n   Per-document breakdown:")
        for r in results:
            print(f"   - {r['doc_id']}: {r['correct']}/{r['total_questions']} = {r['accuracy']:.1f}%")

    # Save aggregate results
    aggregate_path = RESULTS_DIR / "aggregate_results.json"
    with open(aggregate_path, 'w', encoding='utf-8') as f:
        json.dump({
            'colbert_results': all_results['colbert'],
            'colpali_results': all_results['colpali'],
            'summary': {
                'colbert': {
                    'total_correct': sum(r['correct'] for r in all_results['colbert']),
                    'total_questions': sum(r['total_questions'] for r in all_results['colbert']),
                    'accuracy': (sum(r['correct'] for r in all_results['colbert']) /
                                sum(r['total_questions'] for r in all_results['colbert']) * 100)
                                if sum(r['total_questions'] for r in all_results['colbert']) > 0 else 0.0
                },
                'colpali': {
                    'total_correct': sum(r['correct'] for r in all_results['colpali']),
                    'total_questions': sum(r['total_questions'] for r in all_results['colpali']),
                    'accuracy': (sum(r['correct'] for r in all_results['colpali']) /
                                sum(r['total_questions'] for r in all_results['colpali']) * 100)
                                if sum(r['total_questions'] for r in all_results['colpali']) > 0 else 0.0
                }
            }
        }, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Aggregate results saved: {aggregate_path}")
    print("\n✅ Corrected evaluation complete!")

if __name__ == "__main__":
    main()
