#!/usr/bin/env python3
"""
MMESGBench-Aligned ColBERT Evaluator with Parallel Processing
Exact replication of MMESGBench evaluation logic with parallel API calls
"""

import os
import re
import ast
import json
import asyncio
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from math import isclose
from rapidfuzz import fuzz
from difflib import SequenceMatcher
import time

# Import our existing ColBERT infrastructure
from colbert_full_dataset_evaluation import MultiDocumentColBERTRetriever


@dataclass
class EvaluationQuestion:
    doc_id: str
    question: str
    answer: str
    answer_format: str
    evidence_pages: str
    evidence_sources: str
    doc_type: str


class MMESGBenchEvaluator:
    """Exact replication of MMESGBench evaluation logic"""

    @staticmethod
    def get_clean_string(s):
        """MMESGBench text cleaning logic"""
        s = str(s).lower().strip()
        if s.endswith("mile"):
            s = s.rstrip("mile").strip()
        if s.endswith("miles"):
            s = s.rstrip("miles").strip()
        if s.endswith("million"):
            s = s.rstrip("million").strip()
        # remove parenthesis
        s = re.sub(r'\s*\([^)]*\)', '', s).strip()
        # remove quotes
        s = re.sub(r"^['\"]|['\"]$", "", s).strip()
        s = s.strip().lstrip("$").strip()
        s = s.strip().rstrip("%").strip()
        return s

    @staticmethod
    def is_exact_match(s):
        """MMESGBench exact match detection"""
        flag = False
        # Website
        if "https://" in s:
            flag = True
        # code file
        if s.endswith(".py") or s.endswith("ipynb"):
            flag = True
        if s.startswith("page"):
            flag = True
        # telephone number
        if re.fullmatch(r'\b\d+(-\d+|\s\d+)?\b', s):
            flag = True
        # time
        if "a.m." in s or "p.m." in s:
            flag = True
        # YYYY-MM-DD
        if re.fullmatch(r'\b\d{4}[-\s]\d{2}[-\s]\d{2}\b', s):
            flag = True
        # YYYY-MM
        if re.fullmatch(r'\b\d{4}[-\s]\d{2}\b', s):
            flag = True
        # Email address
        if re.fullmatch(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', s):
            flag = True
        return flag

    @staticmethod
    def is_float_equal(reference, prediction, include_percentage: bool = False, is_close: float = False) -> bool:
        """MMESGBench float comparison"""
        def get_precision(gt_ans: float) -> int:
            precision = 3
            if '.' in str(gt_ans):
                precision = len(str(gt_ans).split('.')[-1])
            return precision

        try:
            reference = float(str(reference).strip().rstrip("%").strip())
            prediction = float(str(prediction).strip().rstrip("%").strip())
        except:
            return False

        if include_percentage:
            gt_result = [reference / 100, reference, reference * 100]
        else:
            gt_result = [reference]

        for item in gt_result:
            try:
                if is_close:
                    if isclose(item, prediction, rel_tol=0.01):
                        return True
                precision = max(min(get_precision(prediction), get_precision(item)), 2)
                if round(prediction, precision) == round(item, precision):
                    return True
            except Exception:
                continue
        return False

    @staticmethod
    def anls_compute(ground_truth, predicted_answer, threshold=0.5):
        """MMESGBench ANLS computation"""
        if isinstance(ground_truth, list):
            ground_truth_answers = ground_truth
        else:
            ground_truth_answers = [ground_truth]

        max_similarity = 0
        for gt_answer in ground_truth_answers:
            similarity = fuzz.ratio(predicted_answer.lower(), gt_answer.lower()) / 100
            max_similarity = max(max_similarity, similarity)

        return max(0, 1 - max(0, 1 - max_similarity)) if max_similarity >= threshold else 0

    @staticmethod
    def fuzzy_match(a, b):
        """MMESGBench fuzzy matching"""
        return SequenceMatcher(None, a, b).ratio() > 0.8

    @staticmethod
    def safe_literal_eval(s):
        """MMESGBench safe list parsing"""
        try:
            return ast.literal_eval(s)
        except SyntaxError:
            s_fixed = s.strip()
            if s_fixed.startswith("[") and not s_fixed.endswith("]"):
                s_fixed = s_fixed + "]"
            s_fixed = re.sub(r"(?<=\w)'(?=\w)", r"\\'", s_fixed)
            try:
                return ast.literal_eval(s_fixed)
            except Exception:
                return None

    @classmethod
    def eval_score(cls, gt, pred, answer_type):
        """Exact MMESGBench evaluation logic"""
        if answer_type == "Int":
            try:
                gt, pred = int(gt), int(float(pred))
            except:
                pred = ""
            score = (gt == pred)

        elif answer_type == "Float":
            try:
                gt = float(cls.get_clean_string(str(gt)))
                pred = float(cls.get_clean_string(str(pred)))
            except:
                pred = ""
            score = cls.is_float_equal(gt, pred, include_percentage=True, is_close=True)

        elif answer_type in ["None"]:
            if isinstance(gt, str) and gt.startswith("[") and gt.endswith("]"):
                try:
                    gt_list = eval(gt)
                    gt = " ".join(gt_list) if isinstance(gt_list, list) else gt
                except:
                    pass
            if isinstance(pred, str) and pred.startswith("[") and pred.endswith("]"):
                try:
                    pred_list = eval(pred)
                    pred = " ".join(pred_list) if isinstance(pred_list, list) else pred
                except:
                    pass
            gt = cls.get_clean_string(gt)
            pred = cls.get_clean_string(pred)
            score = (gt == pred)

        elif answer_type in ["Str"]:
            if isinstance(gt, str) and gt.startswith("[") and gt.endswith("]"):
                try:
                    gt_list = eval(gt)
                    gt = " ".join(gt_list) if isinstance(gt_list, list) else gt
                except:
                    pass
            if isinstance(pred, str) and pred.startswith("[") and pred.endswith("]"):
                try:
                    pred_list = eval(pred)
                    pred = " ".join(pred_list) if isinstance(pred_list, list) else pred
                except:
                    pass
            gt = cls.get_clean_string(gt)
            pred = cls.get_clean_string(pred)

            if isinstance(pred, str):
                if gt in pred:
                    score = 1.0
                else:
                    if cls.is_exact_match(gt):
                        score = (gt == pred)
                    else:
                        score = cls.anls_compute(gt, pred)
            else:
                score = 0.0

        else:  # List type
            if isinstance(gt, str) and gt.startswith("["):
                gt = eval(gt)
            if not isinstance(gt, list):
                gt = [gt]
            if isinstance(pred, str) and pred.startswith("["):
                pred = cls.safe_literal_eval(pred)
                if pred is None:
                    score = 0.0
                    return float(score)

            if not isinstance(pred, list):
                pred = [pred]

            if len(gt) == 0 or len(pred) == 0:
                return 0.0
            if len(gt) != len(pred):
                score = 0.0
            else:
                gt_clean = [cls.get_clean_string(a) for a in gt]
                pred_clean = [cls.get_clean_string(a) for a in pred]

                matched = []
                unmatched_pred = pred_clean.copy()

                for gt_item in gt_clean:
                    found = False
                    for pred_item in unmatched_pred:
                        if cls.fuzzy_match(gt_item, pred_item):
                            matched.append(gt_item)
                            unmatched_pred.remove(pred_item)
                            found = True
                            break

                score = len(matched) / len(gt_clean)

        return float(score)


class ParallelColBERTEvaluator:
    """ColBERT evaluator with parallel processing and MMESGBench-aligned evaluation"""

    def __init__(self, dataset_file: str = "MMESGBench/dataset/samples.json",
                 api_key: str = None, batch_size: int = 10):
        self.dataset_file = dataset_file
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        self.batch_size = batch_size

        # Initialize ColBERT retriever
        self.retriever = MultiDocumentColBERTRetriever()

        # Load dataset
        self.questions = self._load_dataset()
        print(f"📊 Loaded {len(self.questions)} questions from {len(set(q.doc_id for q in self.questions))} documents")

    def _load_dataset(self) -> List[EvaluationQuestion]:
        """Load questions from MMESGBench dataset"""
        with open(self.dataset_file, 'r') as f:
            data = json.load(f)

        questions = []
        for item in data:
            questions.append(EvaluationQuestion(
                doc_id=item['doc_id'],
                question=item['question'],
                answer=item['answer'],
                answer_format=item['answer_format'],
                evidence_pages=item.get('evidence_pages', '[]'),
                evidence_sources=item.get('evidence_sources', '[]'),
                doc_type=item.get('doc_type', 'Unknown')
            ))

        return questions

    def process_question_batch(self, questions: List[EvaluationQuestion]) -> List[Dict[str, Any]]:
        """Process a batch of questions with parallel API calls"""
        print(f"🔄 Processing batch of {len(questions)} questions...")

        # Use ThreadPoolExecutor for parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.batch_size) as executor:
            # Submit all questions in the batch
            future_to_question = {
                executor.submit(self._process_single_question, q): q
                for q in questions
            }

            results = []
            for future in concurrent.futures.as_completed(future_to_question):
                question = future_to_question[future]
                try:
                    result = future.result()
                    results.append(result)
                    print(f"✅ Completed: {question.question[:60]}...")
                except Exception as e:
                    print(f"❌ Error processing question: {e}")
                    results.append({
                        'question': question.question,
                        'ground_truth': question.answer,
                        'prediction': 'ERROR',
                        'score': 0.0,
                        'answer_format': question.answer_format,
                        'doc_id': question.doc_id,
                        'error': str(e)
                    })

        return results

    def _process_single_question(self, question: EvaluationQuestion) -> Dict[str, Any]:
        """Process a single question through ColBERT pipeline"""
        try:
            # Step 1: Retrieve relevant chunks using ColBERT
            retrieved_chunks = self.retriever.retrieve(
                question.doc_id,
                question.question,
                top_k=5
            )

            # Step 2: Generate response using retrieved chunks
            response = self.retriever.generate_response(
                question.question,
                retrieved_chunks
            )

            # Step 3: Extract prediction from response
            prediction = response.get('predicted_answer', 'ERROR')

            # Step 4: Evaluate using MMESGBench logic
            score = MMESGBenchEvaluator.eval_score(
                question.answer,
                prediction,
                question.answer_format
            )

            return {
                'question': question.question,
                'ground_truth': question.answer,
                'prediction': prediction,
                'score': score,
                'answer_format': question.answer_format,
                'doc_id': question.doc_id,
                'evidence_pages': question.evidence_pages,
                'evidence_sources': question.evidence_sources,
                'processing_time': 0  # Will be calculated at batch level
            }

        except Exception as e:
            raise Exception(f"Failed to process question: {e}")

    def run_evaluation(self, limit: int = None, start_from: int = 0) -> Dict[str, Any]:
        """Run evaluation with parallel processing"""
        print(f"🚀 Starting MMESGBench-aligned parallel evaluation...")

        # Select questions to evaluate
        questions_to_evaluate = self.questions[start_from:]
        if limit:
            questions_to_evaluate = questions_to_evaluate[:limit]

        print(f"📊 Evaluating {len(questions_to_evaluate)} questions in batches of {self.batch_size}")

        all_results = []
        total_batches = (len(questions_to_evaluate) + self.batch_size - 1) // self.batch_size

        start_time = time.time()

        for i in range(0, len(questions_to_evaluate), self.batch_size):
            batch_num = i // self.batch_size + 1
            batch = questions_to_evaluate[i:i + self.batch_size]

            print(f"\n📦 Processing batch {batch_num}/{total_batches} ({len(batch)} questions)")
            batch_start_time = time.time()

            batch_results = self.process_question_batch(batch)
            batch_time = time.time() - batch_start_time

            # Add timing info
            for result in batch_results:
                result['processing_time'] = batch_time / len(batch)

            all_results.extend(batch_results)

            print(f"⏱️  Batch {batch_num} completed in {batch_time:.1f}s ({batch_time/len(batch):.1f}s per question)")

        total_time = time.time() - start_time

        # Calculate final metrics
        return self._compile_results(all_results, total_time)

    def _compile_results(self, results: List[Dict[str, Any]], total_time: float) -> Dict[str, Any]:
        """Compile final evaluation results"""
        total_questions = len(results)
        total_score = sum(r['score'] for r in results)
        accuracy = total_score / total_questions if total_questions > 0 else 0

        # Group by answer format
        format_stats = {}
        for result in results:
            fmt = result['answer_format']
            if fmt not in format_stats:
                format_stats[fmt] = {'total': 0, 'correct': 0}
            format_stats[fmt]['total'] += 1
            format_stats[fmt]['correct'] += result['score']

        # Group by document
        doc_stats = {}
        for result in results:
            doc = result['doc_id']
            if doc not in doc_stats:
                doc_stats[doc] = {'total': 0, 'correct': 0}
            doc_stats[doc]['total'] += 1
            doc_stats[doc]['correct'] += result['score']

        # Calculate format accuracies
        for fmt, stats in format_stats.items():
            stats['accuracy'] = stats['correct'] / stats['total'] if stats['total'] > 0 else 0

        # Calculate document accuracies
        for doc, stats in doc_stats.items():
            stats['accuracy'] = stats['correct'] / stats['total'] if stats['total'] > 0 else 0

        compiled_results = {
            'accuracy': accuracy,
            'total_questions': total_questions,
            'total_score': total_score,
            'format_breakdown': format_stats,
            'document_breakdown': doc_stats,
            'avg_processing_time': total_time / total_questions if total_questions > 0 else 0,
            'total_time': total_time,
            'batch_size': self.batch_size,
            'evaluation_method': 'MMESGBench-aligned with parallel processing',
            'detailed_results': results
        }

        print(f"\n🎯 Evaluation Complete!")
        print(f"📊 Accuracy: {accuracy:.1%} ({total_score:.1f}/{total_questions})")
        print(f"⏱️  Total time: {total_time:.1f}s ({total_time/total_questions:.1f}s per question)")
        print(f"🚀 Speedup: ~{self.batch_size}x faster with parallel processing")

        return compiled_results


def main():
    """Test the new evaluator on a small sample"""
    print("🧪 Testing MMESGBench-aligned evaluator with parallel processing...")

    # Test with small sample first
    evaluator = ParallelColBERTEvaluator(batch_size=5)  # Small batch for testing

    # Run on first 5 questions for testing
    results = evaluator.run_evaluation(limit=5)

    # Save results
    output_file = "mmesgbench_aligned_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Test results saved to: {output_file}")

    # Show summary
    print(f"\n📈 Test Summary:")
    print(f"Overall Accuracy: {results['accuracy']:.1%}")
    print(f"Processing Time: {results['avg_processing_time']:.1f}s per question")
    print(f"Total Questions: {results['total_questions']}")

    print(f"\n📊 Format Breakdown:")
    for fmt, stats in results['format_breakdown'].items():
        print(f"  {fmt}: {stats['accuracy']:.1%} ({stats['correct']:.1f}/{stats['total']})")


if __name__ == "__main__":
    main()