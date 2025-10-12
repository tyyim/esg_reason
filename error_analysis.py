#!/usr/bin/env python3
"""
Error Analysis: Baseline vs Optimized Model
Analyzes prediction differences to understand optimization impact
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any

def load_json(filepath: str) -> Dict:
    """Load JSON file"""
    with open(filepath, 'r') as f:
        return json.load(f)

def normalize_answer(answer: Any) -> str:
    """Normalize answer for comparison"""
    if answer is None:
        return "Not answerable"
    return str(answer).strip()

def analyze_optimized_predictions(
    dev_set: List[Dict],
    optimized_preds: List[Dict]
) -> Dict:
    """
    Analyze optimized model predictions
    """

    results = {
        'total': len(dev_set),
        'correct': 0,
        'wrong': [],
        'retrieval_failures': [],
        'extraction_failures': [],
        'by_format': defaultdict(lambda: {
            'correct': 0,
            'wrong': 0,
            'total': 0,
            'retrieval_failures': 0,
            'extraction_failures': 0
        })
    }

    for idx, (question, opt_pred) in enumerate(zip(dev_set, optimized_preds)):
        # Normalize answers
        gold_answer = normalize_answer(question.get('answer'))
        pred_answer = normalize_answer(opt_pred.get('answer'))

        # Check retrieval correctness - did we retrieve the evidence pages?
        evidence_pages = question.get('evidence_pages', [])
        context = opt_pred.get('context', '')

        if not evidence_pages:
            # "Not answerable" questions - retrieval correct if we didn't retrieve specific evidence
            retrieval_correct = True
        else:
            # Check if any evidence page is in the context
            retrieval_correct = any(f"[Page {page}," in context for page in evidence_pages)

        # Check answer correctness - exact match
        answer_correct = gold_answer.lower().strip() == pred_answer.lower().strip()

        # End-to-end correct requires both
        e2e_correct = retrieval_correct and answer_correct

        answer_format = question.get('answer_format', 'Unknown')

        # Track statistics
        results['by_format'][answer_format]['total'] += 1

        if e2e_correct:
            results['correct'] += 1
            results['by_format'][answer_format]['correct'] += 1
        else:
            results['by_format'][answer_format]['wrong'] += 1

        # Create error record for failures
        if not e2e_correct:
            error_record = {
                'question_idx': idx,
                'question': question.get('question', ''),
                'doc_id': question.get('doc_id', ''),
                'answer_format': answer_format,
                'gold_answer': gold_answer,
                'predicted_answer': pred_answer,
                'retrieval_correct': retrieval_correct,
                'answer_correct': answer_correct,
                'evidence_pages': question.get('evidence_pages', []),
                'context': opt_pred.get('context', '')[:500]  # First 500 chars
            }

            results['wrong'].append(error_record)

            # Categorize failure type
            if not retrieval_correct:
                results['retrieval_failures'].append(error_record)
                results['by_format'][answer_format]['retrieval_failures'] += 1
            elif retrieval_correct and not answer_correct:
                results['extraction_failures'].append(error_record)
                results['by_format'][answer_format]['extraction_failures'] += 1

    return results

def generate_error_report(analysis: Dict) -> str:
    """Generate comprehensive error analysis report"""

    report = []
    report.append("=" * 80)
    report.append("ERROR ANALYSIS REPORT: Optimized Model Predictions")
    report.append("=" * 80)
    report.append("")

    # Summary
    total = analysis['total']
    correct = analysis['correct']
    wrong_count = len(analysis['wrong'])
    accuracy = (correct / total) * 100

    report.append("📊 OVERALL SUMMARY")
    report.append("-" * 80)
    report.append(f"Total questions: {total}")
    report.append(f"Correct: {correct}/{total} ({accuracy:.1f}%)")
    report.append(f"Wrong: {wrong_count}/{total} ({100-accuracy:.1f}%)")
    report.append("")

    # Failure breakdown
    retrieval_failures = len(analysis['retrieval_failures'])
    extraction_failures = len(analysis['extraction_failures'])

    report.append("🔍 FAILURE BREAKDOWN")
    report.append("-" * 80)
    report.append(f"Retrieval failures: {retrieval_failures} ({retrieval_failures/total*100:.1f}%)")
    report.append(f"  → Model retrieved wrong chunks, couldn't find evidence")
    report.append(f"Extraction failures: {extraction_failures} ({extraction_failures/total*100:.1f}%)")
    report.append(f"  → Model found evidence but extracted wrong answer")
    report.append("")

    # By format
    report.append("📋 PERFORMANCE BY ANSWER FORMAT")
    report.append("-" * 80)
    # Sort by format type, putting None last
    sorted_formats = sorted(analysis['by_format'].items(), key=lambda x: (x[0] is None, x[0] or ''))
    for format_type, stats in sorted_formats:
        if stats['total'] == 0:
            continue
        acc = (stats['correct'] / stats['total']) * 100

        format_name = format_type if format_type is not None else "null (Not answerable)"

        report.append(f"\n{format_name} ({stats['total']} questions):")
        report.append(f"  Accuracy: {stats['correct']}/{stats['total']} ({acc:.1f}%)")
        report.append(f"  Retrieval failures: {stats['retrieval_failures']}")
        report.append(f"  Extraction failures: {stats['extraction_failures']}")
    report.append("")

    # Retrieval failure analysis
    if retrieval_failures > 0:
        report.append("📍 RETRIEVAL FAILURE EXAMPLES (Top 10)")
        report.append("=" * 80)
        report.append(f"\nTotal retrieval failures: {retrieval_failures}")
        report.append("→ Model retrieved wrong chunks, couldn't find evidence pages\n")

        for i, example in enumerate(analysis['retrieval_failures'][:10], 1):
            report.append(f"\n{i}. Q: {example['question'][:120]}...")
            report.append(f"   Document: {example['doc_id']}")
            report.append(f"   Format: {example['answer_format']}")
            report.append(f"   Gold answer: {example['gold_answer']}")
            report.append(f"   Predicted: {example['predicted_answer']}")
            report.append(f"   Evidence pages needed: {example['evidence_pages']}")
            report.append(f"   Context preview: {example['context'][:150]}...")
            report.append(f"   → WHY: Model didn't retrieve pages {example['evidence_pages']}")

    # Extraction failure analysis
    if extraction_failures > 0:
        report.append("\n\n🔤 EXTRACTION FAILURE EXAMPLES (Top 10)")
        report.append("=" * 80)
        report.append(f"\nTotal extraction failures: {extraction_failures}")
        report.append("→ Model found correct evidence but extracted wrong answer\n")

        for i, example in enumerate(analysis['extraction_failures'][:10], 1):
            report.append(f"\n{i}. Q: {example['question'][:120]}...")
            report.append(f"   Document: {example['doc_id']}")
            report.append(f"   Format: {example['answer_format']}")
            report.append(f"   Gold answer: {example['gold_answer']}")
            report.append(f"   Predicted: {example['predicted_answer']}")
            report.append(f"   Evidence was retrieved: ✓")
            report.append(f"   Context preview: {example['context'][:150]}...")
            report.append(f"   → WHY: Model had evidence but failed to extract correct answer")

    report.append("\n" + "=" * 80)
    report.append("KEY INSIGHTS")
    report.append("=" * 80)

    # Generate insights
    if retrieval_failures > extraction_failures:
        report.append(f"⚠️  PRIMARY ISSUE: RETRIEVAL ({retrieval_failures} failures)")
        report.append(f"   - {retrieval_failures} questions failed at retrieval stage")
        report.append(f"   - {extraction_failures} questions failed at extraction stage")
        report.append(f"   - Retrieval accounts for {retrieval_failures/wrong_count*100:.1f}% of all failures")
        report.append("   - DIAGNOSIS: Optimized prompts didn't improve retrieval quality")
        report.append("   - May need query generation optimization to retrieve correct pages")
    else:
        report.append(f"⚠️  PRIMARY ISSUE: EXTRACTION ({extraction_failures} failures)")
        report.append(f"   - {extraction_failures} questions failed at extraction stage")
        report.append(f"   - {retrieval_failures} questions failed at retrieval stage")
        report.append(f"   - Extraction accounts for {extraction_failures/wrong_count*100:.1f}% of all failures")
        report.append("   - DIAGNOSIS: Optimized prompts had evidence but extracted wrong answers")
        report.append("   - May need better instruction tuning or few-shot examples")

    report.append("")
    report.append("RECOMMENDATION:")
    report.append(f"  → Overall accuracy: {accuracy:.1f}% on dev set")

    if retrieval_failures > extraction_failures:
        report.append("  → Focus on improving RETRIEVAL:")
        report.append("    1. Add query generation module (converts questions to better search queries)")
        report.append("    2. Optimize query generation prompts with MIPROv2")
        report.append("    3. Re-run evaluation to measure retrieval improvement")
    else:
        report.append("  → Focus on improving EXTRACTION:")
        report.append("    1. Analyze extraction failures to identify patterns")
        report.append("    2. Add more few-shot examples for extraction signature")
        report.append("    3. Try different instruction prompts for AnswerExtraction")
        report.append("    4. Consider re-running MIPROv2 with explicit valset parameter")

    report.append("")
    report.append("=" * 80)

    return "\n".join(report)

def main():
    """Run error analysis"""

    print("Loading data...")

    # Load dev set
    with open('dspy_implementation/data_splits/dev_93.json', 'r') as f:
        dev_set = json.load(f)

    # Load optimized predictions
    with open('optimized_predictions.json', 'r') as f:
        optimized_preds = json.load(f)

    print(f"Loaded {len(dev_set)} dev questions and {len(optimized_preds)} predictions")

    # Analyze predictions
    print("\nAnalyzing optimized predictions...")
    analysis = analyze_optimized_predictions(dev_set, optimized_preds)

    # Generate report
    print("\nGenerating error analysis report...")
    report = generate_error_report(analysis)

    # Save report
    output_file = 'optimized_model_error_analysis.txt'
    with open(output_file, 'w') as f:
        f.write(report)

    print(f"\n✅ Error analysis complete!")
    print(f"📄 Report saved to: {output_file}")
    print(f"\n{report}")

if __name__ == '__main__':
    main()
