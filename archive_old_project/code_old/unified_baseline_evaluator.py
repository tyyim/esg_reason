#!/usr/bin/env python3
"""
Unified Baseline Evaluator
Uses MMESGBench's exact evaluation logic to re-evaluate all predictions consistently
Outputs separate retrieval, answer, and E2E accuracy for fair comparison
"""

import json
import sys
import ast
import re
from typing import Dict, List, Any, Tuple
from pathlib import Path

# Import MMESGBench's exact evaluation logic
sys.path.append('MMESGBench/src/eval')
from eval_score import eval_score as mmesgbench_eval_score, eval_acc_and_f1


def safe_literal_eval(s):
    """
    Safely evaluate string literals, handling malformed strings
    From MMESGBench's own code
    """
    try:
        return ast.literal_eval(s)
    except (SyntaxError, ValueError) as e:
        # Try to fix common issues
        s_fixed = s.strip()
        if s_fixed.startswith("[") and not s_fixed.endswith("]"):
            s_fixed = s_fixed + "]"
        # Fix single quotes in middle of words
        s_fixed = re.sub(r"(?<=\w)'(?=\w)", r"\\'", s_fixed)
        try:
            return ast.literal_eval(s_fixed)
        except Exception as e2:
            # If still fails, return original string
            return s


def eval_score_safe(gt, pred, answer_type):
    """
    Safe wrapper around MMESGBench's eval_score that handles malformed lists
    """
    try:
        # Pre-process list strings to avoid eval() errors
        if answer_type not in ["Int", "Float", "Str", "None"]:
            # This is likely a List type
            if isinstance(gt, str) and gt.startswith("["):
                gt = safe_literal_eval(gt)
            if isinstance(pred, str) and pred.startswith("["):
                pred = safe_literal_eval(pred)

        return mmesgbench_eval_score(gt, pred, answer_type)
    except (SyntaxError, ValueError) as e:
        # If evaluation fails, try string comparison as fallback
        print(f"⚠️  Evaluation error for {answer_type}: {e}")
        try:
            return 1.0 if str(gt).strip() == str(pred).strip() else 0.0
        except:
            return 0.0


class UnifiedBaselineEvaluator:
    """
    Unified evaluator using MMESGBench's exact evaluation logic
    Provides consistent evaluation across all prediction files
    """

    def __init__(self, dataset_path: str = 'mmesgbench_dataset_corrected.json'):
        """Initialize with ground truth dataset"""
        print(f"📚 Loading ground truth dataset from {dataset_path}...")
        with open(dataset_path, 'r') as f:
            self.dataset = json.load(f)

        # Create lookup dictionary for fast access
        self.ground_truth_lookup = {}
        for item in self.dataset:
            # Use question text as key (should be unique)
            key = item['question'].strip()
            self.ground_truth_lookup[key] = item

        print(f"✅ Loaded {len(self.dataset)} ground truth questions")

    def _extract_pages_from_context(self, context: Any) -> List[int]:
        """
        Extract page numbers from context string
        Context format: "[Page 31, score: 0.819]\n..."
        """
        if not context:
            return []

        if isinstance(context, list):
            return context

        if isinstance(context, str):
            # Extract page numbers using regex
            import re
            page_pattern = r'\[Page\s+(\d+)'
            matches = re.findall(page_pattern, context)
            return [int(page) for page in matches]

        return []

    def evaluate_predictions(
        self,
        predictions: List[Dict[str, Any]],
        predictions_name: str = "Unknown"
    ) -> Dict[str, Any]:
        """
        Evaluate predictions using MMESGBench's exact logic

        Args:
            predictions: List of prediction dicts with 'question', 'predicted_answer', 'retrieved_pages'
            predictions_name: Name of the prediction set for reporting

        Returns:
            Dictionary with comprehensive evaluation results
        """
        print(f"\n{'='*60}")
        print(f"🔍 Evaluating: {predictions_name}")
        print(f"{'='*60}")
        print(f"Total predictions: {len(predictions)}")

        results = {
            'predictions_name': predictions_name,
            'total_questions': len(predictions),
            'retrieval_correct': 0,
            'answer_correct': 0,
            'end_to_end_correct': 0,
            'by_format': {},
            'detailed_results': []
        }

        # Evaluate each prediction
        for i, pred in enumerate(predictions):
            question_text = pred.get('question', '').strip()
            predicted_answer = pred.get('predicted_answer', pred.get('answer', ''))

            # Extract retrieved pages from different possible fields
            retrieved_pages = pred.get('retrieved_pages', pred.get('pred_page', []))
            if not retrieved_pages:
                # Try to extract from context field
                context = pred.get('context', '')
                retrieved_pages = self._extract_pages_from_context(context)

            # Find ground truth
            gt_item = self.ground_truth_lookup.get(question_text)
            if gt_item is None:
                print(f"⚠️  Warning: Question not found in ground truth: {question_text[:50]}...")
                continue

            # Extract ground truth info
            gt_answer = gt_item['answer']
            gt_format = gt_item['answer_format']
            gt_evidence_pages = gt_item.get('evidence_pages', [])

            # Evaluate retrieval accuracy
            retrieval_correct = self._check_retrieval(retrieved_pages, gt_evidence_pages)

            # Evaluate answer accuracy using MMESGBench's exact logic (with safe wrapper)
            answer_score = eval_score_safe(gt_answer, predicted_answer, gt_format)
            answer_correct = (answer_score >= 0.5)  # MMESGBench uses 0.5 threshold for fuzzy matches

            # End-to-end accuracy: both retrieval AND answer must be correct
            e2e_correct = retrieval_correct and answer_correct

            # Update counters
            if retrieval_correct:
                results['retrieval_correct'] += 1
            if answer_correct:
                results['answer_correct'] += 1
            if e2e_correct:
                results['end_to_end_correct'] += 1

            # Track by format
            if gt_format not in results['by_format']:
                results['by_format'][gt_format] = {
                    'total': 0,
                    'retrieval_correct': 0,
                    'answer_correct': 0,
                    'e2e_correct': 0
                }

            results['by_format'][gt_format]['total'] += 1
            if retrieval_correct:
                results['by_format'][gt_format]['retrieval_correct'] += 1
            if answer_correct:
                results['by_format'][gt_format]['answer_correct'] += 1
            if e2e_correct:
                results['by_format'][gt_format]['e2e_correct'] += 1

            # Store detailed result
            results['detailed_results'].append({
                'question': question_text,
                'predicted_answer': predicted_answer,
                'ground_truth': gt_answer,
                'answer_format': gt_format,
                'retrieval_correct': retrieval_correct,
                'answer_correct': answer_correct,
                'e2e_correct': e2e_correct,
                'retrieved_pages': retrieved_pages,
                'evidence_pages': gt_evidence_pages,
                'mmesgbench_score': answer_score
            })

        # Calculate final metrics
        total = results['total_questions']
        results['retrieval_accuracy'] = results['retrieval_correct'] / total if total > 0 else 0
        results['answer_accuracy'] = results['answer_correct'] / total if total > 0 else 0
        results['end_to_end_accuracy'] = results['end_to_end_correct'] / total if total > 0 else 0

        # Calculate format-level metrics
        for fmt, stats in results['by_format'].items():
            fmt_total = stats['total']
            stats['retrieval_accuracy'] = stats['retrieval_correct'] / fmt_total if fmt_total > 0 else 0
            stats['answer_accuracy'] = stats['answer_correct'] / fmt_total if fmt_total > 0 else 0
            stats['e2e_accuracy'] = stats['e2e_correct'] / fmt_total if fmt_total > 0 else 0

        # Print results
        self._print_results(results)

        return results

    def _check_retrieval(self, retrieved_pages: List[int], evidence_pages: List[int]) -> bool:
        """
        Check if retrieval is correct (all evidence pages retrieved)

        Args:
            retrieved_pages: List of retrieved page numbers
            evidence_pages: List of ground truth evidence page numbers

        Returns:
            True if all evidence pages are in retrieved pages
        """
        if not evidence_pages:
            return True  # No evidence pages required

        if not retrieved_pages:
            return False  # Evidence required but nothing retrieved

        # Convert to sets for comparison
        retrieved_set = set(retrieved_pages)
        evidence_set = set(evidence_pages)

        # Check if all evidence pages are in retrieved pages
        return evidence_set.issubset(retrieved_set)

    def _print_results(self, results: Dict[str, Any]):
        """Print evaluation results in a clear format"""
        print(f"\n{'='*60}")
        print(f"📊 EVALUATION RESULTS: {results['predictions_name']}")
        print(f"{'='*60}")

        total = results['total_questions']
        print(f"\n🎯 Overall Accuracy ({total} questions):")
        print(f"  Retrieval Accuracy: {results['retrieval_accuracy']:.1%} ({results['retrieval_correct']}/{total})")
        print(f"  Answer Accuracy:    {results['answer_accuracy']:.1%} ({results['answer_correct']}/{total})")
        print(f"  End-to-End (E2E):   {results['end_to_end_accuracy']:.1%} ({results['end_to_end_correct']}/{total})")

        print(f"\n📋 By Format:")
        # Sort by format name
        sorted_formats = sorted(results['by_format'].items(),
                               key=lambda x: (x[0] is None, x[0] or ''))

        for fmt, stats in sorted_formats:
            fmt_total = stats['total']
            fmt_name = fmt if fmt else "null"
            print(f"  {fmt_name} ({fmt_total} questions):")
            print(f"    Retrieval: {stats['retrieval_accuracy']:.1%} ({stats['retrieval_correct']}/{fmt_total})")
            print(f"    Answer:    {stats['answer_accuracy']:.1%} ({stats['answer_correct']}/{fmt_total})")
            print(f"    E2E:       {stats['e2e_accuracy']:.1%} ({stats['e2e_correct']}/{fmt_total})")

        print(f"\n{'='*60}\n")


def load_predictions_file(file_path: str) -> Tuple[List[Dict[str, Any]], str]:
    """
    Load predictions from various file formats

    Returns:
        (predictions_list, predictions_name)
    """
    print(f"📂 Loading predictions from {file_path}...")

    with open(file_path, 'r') as f:
        data = json.load(f)

    predictions = []
    predictions_name = Path(file_path).stem

    # Handle different file structures
    if isinstance(data, list):
        # Simple list of predictions
        predictions = data
    elif isinstance(data, dict):
        # Check for different possible structures
        if 'detailed_results' in data:
            # From our evaluation results
            predictions = data['detailed_results']
            predictions_name = data.get('approach', predictions_name)
        elif 'predictions' in data:
            # From predictions field
            predictions = data['predictions']
        else:
            # Try to find prediction list in the dict
            for key in ['results', 'samples', 'data']:
                if key in data and isinstance(data[key], list):
                    predictions = data[key]
                    break

    print(f"✅ Loaded {len(predictions)} predictions")
    return predictions, predictions_name


def main():
    """Main evaluation function"""
    print("🚀 Unified Baseline Evaluator - COMPLETE EVALUATION")
    print("Using MMESGBench's exact evaluation logic")
    print("Evaluating ALL prediction files found in project")
    print("=" * 80)

    # Initialize evaluator
    evaluator = UnifiedBaselineEvaluator()

    # List of ALL prediction files to evaluate (with friendly names)
    prediction_files = [
        # Full dataset evaluations (933 questions)
        ('dspy_implementation/full_dataset_results/baseline_results_20251010_232606.json',
         'DSPy_Baseline_933'),
        ('dspy_implementation/full_dataset_results/enhanced_results_20251010_232606.json',
         'DSPy_Enhanced_933'),
        ('mmesgbench_baseline_corrected.json',
         'MMESGBench_Corrected_933'),
        ('optimized_full_dataset_mmesgbench_with_f1.json',
         'ColBERT_Optimized_933'),

        # Dev set evaluations (93 questions)
        ('baseline_dev_predictions.json',
         'Baseline_Dev_93'),
        ('optimized_predictions.json',
         'Optimized_Dev_93'),

        # Subset evaluation (47 questions)
        ('corrected_evaluation_results/colbert_corrected_evaluation.json',
         'ColBERT_Corrected_47'),
    ]

    all_results = {}
    print(f"\n📋 Will evaluate {len(prediction_files)} prediction files:")
    for pred_file, name in prediction_files:
        status = "✅" if Path(pred_file).exists() else "❌"
        print(f"  {status} {name}: {pred_file}")
    print()

    # Evaluate each prediction file
    for pred_file, friendly_name in prediction_files:
        if not Path(pred_file).exists():
            print(f"\n⚠️  Skipping {friendly_name}: {pred_file} (file not found)")
            continue

        try:
            predictions, pred_name = load_predictions_file(pred_file)

            # Use friendly name if provided
            if friendly_name:
                pred_name = friendly_name

            results = evaluator.evaluate_predictions(predictions, pred_name)
            all_results[pred_name] = results

            # Save individual results
            output_file = f"unified_eval_{pred_name}.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"💾 Results saved to: {output_file}")

        except Exception as e:
            print(f"\n❌ Error evaluating {friendly_name}: {e}")
            import traceback
            traceback.print_exc()

    # Print comparison table
    print("\n" + "=" * 100)
    print("📊 COMPARISON TABLE - All Evaluations with Unified Evaluator")
    print("=" * 100)
    print(f"{'Baseline':<30} {'Dataset':<12} {'Retrieval':<15} {'Answer':<15} {'E2E':<15} {'Notes':<15}")
    print("-" * 100)

    # Sort by dataset size, then name
    sorted_results = sorted(all_results.items(),
                           key=lambda x: (x[1]['total_questions'], x[0]))

    for name, results in sorted_results:
        dataset_size = results['total_questions']
        retr_acc = results['retrieval_accuracy']
        ans_acc = results['answer_accuracy']
        e2e_acc = results['end_to_end_accuracy']

        # Determine if we have context (can calculate E2E)
        has_context = retr_acc > 0.2  # If retrieval > 20%, we likely have context

        retr_str = f"{retr_acc:>12.1%}" if has_context else "      N/A   "
        e2e_str = f"{e2e_acc:>12.1%}" if has_context else "      N/A   "
        note = "✅ E2E" if has_context else "⚠️ Answer only"

        print(f"{name:<30} {str(dataset_size)+' q':<12} "
              f"{retr_str}  {ans_acc:>12.1%}  {e2e_str}  {note:<15}")

    print("=" * 100)

    # Save comparison results
    comparison_file = 'unified_evaluation_comparison.json'
    with open(comparison_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\n💾 Comparison results saved to: {comparison_file}")

    print("\n✅ Unified evaluation completed!")
    print("All results use MMESGBench's exact evaluation logic for fair comparison.")


if __name__ == "__main__":
    main()
