#!/usr/bin/env python3
"""
Optimized ColBERT Evaluator with Exact MMESGBench Evaluation Logic
Uses exact evaluation functions from MMESGBench to fix accuracy discrepancies
"""

import json
import time
import concurrent.futures
from typing import Dict, List, Any
from colbert_full_dataset_evaluation import MultiDocumentColBERTRetriever
from mmesgbench_exact_evaluation import evaluate_prediction_mmesgbench

print("🔄 Optimized ColBERT evaluator with MMESGBench evaluation loaded!")

class OptimizedColBERTEvaluatorMMESGBench:
    """Optimized evaluator with exact MMESGBench evaluation logic"""

    def __init__(self, batch_size: int = 10):
        print("📝 Initializing ColBERT components with MMESGBench evaluation...")
        self.retriever = MultiDocumentColBERTRetriever()
        self.batch_size = batch_size
        self.precomputed_cache = {}
        print("✅ Components ready with MMESGBench evaluation")

    def precompute_retrievals_for_questions(self, questions: List[Dict[str, Any]]) -> None:
        """Pre-compute retrievals for better memory management"""
        print(f"🔍 Pre-computing retrievals for {len(questions)} questions...")

        start_time = time.time()
        for i, question in enumerate(questions):
            if i % 50 == 0:
                elapsed = time.time() - start_time
                rate = i / elapsed if elapsed > 0 else 0
                remaining = (len(questions) - i) / rate if rate > 0 else 0
                print(f"   Progress: {i}/{len(questions)} ({i/len(questions)*100:.1f}%) | ETA: {remaining:.0f}s")

            try:
                doc_id = question['doc_id']
                question_text = question['question']
                cache_key = f"{doc_id}::{question_text}"

                # Index document first (critical step!)
                if not self.retriever.index_document(doc_id):
                    print(f"   Warning: Failed to index document {doc_id}")
                    self.precomputed_cache[cache_key] = []
                    continue

                # Retrieve using existing infrastructure
                chunks = self.retriever.retrieve(doc_id, question_text, top_k=5)
                self.precomputed_cache[cache_key] = chunks

            except Exception as e:
                print(f"   Warning: Failed to retrieve for question {i}: {e}")
                cache_key = f"{question['doc_id']}::{question['question']}"
                self.precomputed_cache[cache_key] = []

        total_time = time.time() - start_time
        print(f"✅ Pre-computation completed in {total_time:.1f}s")

    def evaluate_with_precomputed(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run evaluation using pre-computed retrievals and exact MMESGBench evaluation"""
        print(f"🚀 Starting optimized evaluation with MMESGBench evaluation logic...")

        # Step 1: Pre-compute all retrievals
        self.precompute_retrievals_for_questions(questions)

        # Step 2: Parallel generation phase
        print(f"🚀 Starting parallel generation for {len(questions)} questions...")

        all_results = []
        total_batches = (len(questions) + self.batch_size - 1) // self.batch_size
        start_time = time.time()

        for i in range(0, len(questions), self.batch_size):
            batch_num = i // self.batch_size + 1
            batch = questions[i:i + self.batch_size]

            print(f"📦 Processing batch {batch_num}/{total_batches} ({len(batch)} questions)")
            batch_start = time.time()

            # Process batch in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.batch_size) as executor:
                future_to_question = {
                    executor.submit(self._process_single_question, q): q
                    for q in batch
                }

                batch_results = []
                for future in concurrent.futures.as_completed(future_to_question):
                    try:
                        result = future.result()
                        batch_results.append(result)
                    except Exception as e:
                        question = future_to_question[future]
                        print(f"❌ Error processing question: {e}")
                        batch_results.append({
                            'question': question['question'],
                            'predicted_answer': 'ERROR',
                            'ground_truth': question['answer'],
                            'score': 0.0,
                            'answer_format': question['answer_format'],
                            'doc_id': question['doc_id']
                        })

            all_results.extend(batch_results)
            batch_time = time.time() - batch_start
            print(f"⏱️  Batch {batch_num} completed in {batch_time:.1f}s")

        total_time = time.time() - start_time
        return self._compile_results(all_results, total_time)

    def _process_single_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Process single question using pre-computed retrieval and MMESGBench evaluation"""
        try:
            # Get pre-computed chunks
            cache_key = f"{question['doc_id']}::{question['question']}"
            retrieved_chunks = self.precomputed_cache.get(cache_key, [])

            # Generate response using existing infrastructure
            response = self.retriever.generate_response(
                question['question'],
                retrieved_chunks
            )

            # Extract answer from response
            extracted_answer = response.get('predicted_answer', 'Failed to extract')

            # Use exact MMESGBench evaluation logic
            is_correct, exact_match, f1_score = evaluate_prediction_mmesgbench(
                extracted_answer,
                question['answer'],
                question['answer_format']
            )

            return {
                'question': question['question'],
                'predicted_answer': extracted_answer,
                'ground_truth': question['answer'],
                'score': 1.0 if is_correct else 0.0,
                'answer_format': question['answer_format'],
                'doc_id': question['doc_id'],
                'exact_match': exact_match,
                'f1_score': f1_score
            }

        except Exception as e:
            print(f"Error processing question: {e}")
            return {
                'question': question['question'],
                'predicted_answer': 'ERROR',
                'ground_truth': question['answer'],
                'score': 0.0,
                'answer_format': question['answer_format'],
                'doc_id': question['doc_id']
            }

    def _compile_results(self, results: List[Dict[str, Any]], total_time: float) -> Dict[str, Any]:
        """Compile final results"""
        total_questions = len(results)
        total_score = sum(r['score'] for r in results)
        accuracy = total_score / total_questions if total_questions > 0 else 0

        # Group by format
        format_stats = {}
        for result in results:
            fmt = result['answer_format']
            if fmt not in format_stats:
                format_stats[fmt] = {'total': 0, 'correct': 0}
            format_stats[fmt]['total'] += 1
            format_stats[fmt]['correct'] += result['score']

        # Calculate format accuracies
        for fmt, stats in format_stats.items():
            stats['accuracy'] = stats['correct'] / stats['total'] if stats['total'] > 0 else 0

        # Group by document
        doc_stats = {}
        for result in results:
            doc = result['doc_id']
            if doc not in doc_stats:
                doc_stats[doc] = {'total': 0, 'correct': 0}
            doc_stats[doc]['total'] += 1
            doc_stats[doc]['correct'] += result['score']

        # Calculate doc accuracies
        for doc, stats in doc_stats.items():
            stats['accuracy'] = stats['correct'] / stats['total'] if stats['total'] > 0 else 0

        return {
            'accuracy': accuracy,
            'total_questions': total_questions,
            'total_score': total_score,
            'total_time': total_time,
            'avg_processing_time': total_time / total_questions if total_questions > 0 else 0,
            'format_breakdown': format_stats,
            'document_breakdown': doc_stats,
            'detailed_results': results,
            'evaluation_method': 'Optimized ColBERT with MMESGBench exact evaluation logic'
        }


def main():
    """Test evaluator with MMESGBench evaluation logic"""
    print("🚀 Testing Optimized ColBERT Evaluator with MMESGBench Evaluation...")

    # Load dataset
    with open('MMESGBench/dataset/samples.json', 'r') as f:
        dataset = json.load(f)

    print(f"🎯 Running FULL dataset evaluation with {len(dataset)} questions using MMESGBench evaluation")

    evaluator = OptimizedColBERTEvaluatorMMESGBench(batch_size=10)
    results = evaluator.evaluate_with_precomputed(dataset)

    print(f"\n📊 Full Dataset Results (MMESGBench Evaluation):")
    print(f"Accuracy: {results['accuracy']:.1%} ({results['total_score']:.0f}/{results['total_questions']})")
    print(f"Processing Time: {results['avg_processing_time']:.1f}s per question")
    print(f"Total Time: {results['total_time']:.1f}s")

    # Save results
    output_file = 'optimized_full_dataset_mmesgbench_evaluation.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"✅ Evaluation completed with MMESGBench logic! Results saved to: {output_file}")

    # Compare with previous results
    try:
        with open('optimized_full_dataset_fixed_results.json', 'r') as f:
            old_results = json.load(f)

        old_accuracy = old_results['accuracy']
        new_accuracy = results['accuracy']
        improvement = new_accuracy - old_accuracy

        print(f"\n📈 Evaluation Logic Comparison:")
        print(f"Previous (Our Logic): {old_accuracy:.1%} ({old_results['total_score']:.0f}/{old_results['total_questions']})")
        print(f"Current (MMESGBench): {new_accuracy:.1%} ({results['total_score']:.0f}/{results['total_questions']})")
        print(f"Improvement: {improvement:.1%} ({improvement*results['total_questions']:.0f} additional correct)")

    except FileNotFoundError:
        print("Previous results not found for comparison")

    # Show format breakdown
    print(f"\n📊 Format Breakdown (MMESGBench Evaluation):")
    for fmt, stats in results['format_breakdown'].items():
        print(f"  {fmt}: {stats['accuracy']:.1%} ({stats['correct']:.0f}/{stats['total']})")


if __name__ == "__main__":
    main()