#!/usr/bin/env python3
"""
Robust ColPali visual RAG evaluation with checkpoint/resume functionality
Target: 51.8% accuracy (MMESGBench paper)
"""
import sys
import os
import json
import logging
import time
import traceback
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.evaluation.prototype_evaluator import SimpleESGEvaluator
from mmesgbench_retrieval_replication import ColPaliVisualRetriever, MMESGBenchRetrievalReplicator

logger = logging.getLogger(__name__)

class RobustColPaliEvaluator:
    """Robust ColPali evaluation with checkpoint/resume functionality"""

    def __init__(self, checkpoint_file: str = "colpali_checkpoint.json"):
        self.checkpoint_file = checkpoint_file
        self.results_file = "colpali_visual_results.json"
        self.replicator = None
        self.evaluator = SimpleESGEvaluator()
        self.colpali_retriever = None

        # Document setup
        self.test_pdf = "source_documents/AR6 Synthesis Report Climate Change 2023.pdf"
        self.doc_id = "AR6 Synthesis Report Climate Change 2023.pdf"

    def _save_checkpoint(self, results: List[Dict], completed_idx: int, total_samples: int, initialization_done: bool = False):
        """Save current progress to checkpoint file"""
        try:
            checkpoint_data = {
                "completed_questions": completed_idx,
                "total_questions": total_samples,
                "initialization_done": initialization_done,
                "results": results,
                "timestamp": time.time(),
                "doc_id": self.doc_id
            }
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
            logger.info(f"💾 ColPali checkpoint saved: {completed_idx}/{total_samples} questions")
        except Exception as e:
            logger.warning(f"Failed to save checkpoint: {e}")

    def _load_checkpoint(self) -> Tuple[List[Dict], int, bool]:
        """Load progress from checkpoint file"""
        if not os.path.exists(self.checkpoint_file):
            return [], 0, False

        try:
            with open(self.checkpoint_file, 'r') as f:
                checkpoint_data = json.load(f)

            results = checkpoint_data.get("results", [])
            completed_idx = checkpoint_data.get("completed_questions", 0)
            initialization_done = checkpoint_data.get("initialization_done", False)

            logger.info(f"📂 Loaded ColPali checkpoint: {completed_idx} questions completed, init: {initialization_done}")
            return results, completed_idx, initialization_done

        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}")
            return [], 0, False

    def _initialize_components(self) -> bool:
        """Initialize ColPali components with timeout protection"""
        try:
            logger.info("🔧 Initializing ColPali components...")

            # Initialize replicator
            if self.replicator is None:
                logger.info("  - Initializing replicator...")
                self.replicator = MMESGBenchRetrievalReplicator()

            # Initialize ColPali retriever (this is the slow part)
            if self.colpali_retriever is None:
                logger.info("  - Initializing ColPali visual retriever (may take 5+ minutes)...")
                start_time = time.time()
                self.colpali_retriever = ColPaliVisualRetriever(self.replicator.client)
                init_time = time.time() - start_time
                logger.info(f"  - ColPali initialization completed in {init_time:.1f}s")

            # Index document
            if not os.path.exists(self.test_pdf):
                logger.error(f"Test PDF not found: {self.test_pdf}")
                return False

            logger.info("📚 Indexing document for visual retrieval...")
            index_start = time.time()
            self.colpali_retriever.index_document(self.doc_id, self.test_pdf)
            index_time = time.time() - index_start
            logger.info(f"Document indexing completed in {index_time:.1f}s")

            return True

        except Exception as e:
            logger.error(f"Failed to initialize ColPali components: {e}")
            logger.error(traceback.format_exc())
            return False

    def _load_ar6_data(self, limit: int = None) -> List[Dict[str, Any]]:
        """Load AR6 data"""
        try:
            with open("./MMESGBench/dataset/samples.json", 'r') as f:
                full_dataset = json.load(f)
            ar6_samples = [s for s in full_dataset if s.get("doc_id") == self.doc_id]
            return ar6_samples[:limit] if limit else ar6_samples
        except Exception as e:
            logger.error(f"Error loading AR6 data: {e}")
            return []

    def _evaluate_single_question(self, sample: Dict[str, Any], question_id: int) -> Dict[str, Any]:
        """Evaluate a single question with error handling"""
        question = sample["question"]
        ground_truth = sample["answer"]
        answer_format = sample["answer_format"]

        logger.info(f"🔍 Q{question_id}: {answer_format} - {question[:60]}...")

        result = {
            "question_id": question_id,
            "question": question,
            "predicted_answer": "",
            "ground_truth": ground_truth,
            "answer_format": answer_format,
            "is_correct": False,
            "confidence": 0.0,
            "processing_time": 0.0,
            "visual_pages": [],
            "visual_scores": [],
            "error": None
        }

        try:
            start_time = time.time()

            # ColPali Visual Retrieval
            visual_pages, image_paths, scores = self.colpali_retriever.retrieve(
                self.doc_id, question, top_k=5
            )

            # Generate response
            visual_response = self.colpali_retriever.generate_response(
                question, (visual_pages, image_paths, scores), self.replicator.extraction_prompt
            )

            processing_time = time.time() - start_time
            predicted = visual_response["predicted_answer"]

            # Evaluate prediction
            is_correct, confidence = self.evaluator.evaluate_prediction(
                predicted, ground_truth, answer_format
            )

            # Update result
            result.update({
                "predicted_answer": predicted,
                "is_correct": is_correct,
                "confidence": confidence,
                "processing_time": processing_time,
                "visual_pages": visual_pages,
                "visual_scores": scores[:5],
                "response": visual_response.get("response", "")
            })

            # Log result
            status = "✅" if is_correct else "❌"
            logger.info(f"   {status} Predicted: '{predicted}' | Truth: '{ground_truth}'")
            logger.info(f"   Pages: {visual_pages}, Time: {processing_time:.1f}s")

        except Exception as e:
            error_msg = str(e)
            result["error"] = error_msg
            logger.error(f"   ❌ Error evaluating Q{question_id}: {error_msg}")

        return result

    def run_evaluation(self, limit: int = 10, resume: bool = True) -> Dict[str, Any]:
        """Run ColPali evaluation with checkpoint/resume"""
        logger.info("🚀 Starting Robust ColPali Visual RAG Evaluation")

        # Load samples
        samples = self._load_ar6_data(limit)
        if not samples:
            logger.error("No samples loaded")
            return {}

        # Load checkpoint if resuming
        results, start_idx, initialization_done = self._load_checkpoint() if resume else ([], 0, False)

        if start_idx >= len(samples):
            logger.info("✅ All ColPali questions already completed!")
            return self._compile_results(results)

        # Initialize components (skip if already done from checkpoint)
        if not initialization_done:
            logger.info("🔧 Initializing ColPali components...")
            if not self._initialize_components():
                logger.error("Failed to initialize ColPali components")
                return {}

            # Save checkpoint after successful initialization
            self._save_checkpoint(results, start_idx, len(samples), initialization_done=True)
        else:
            logger.info("📂 Skipping initialization (already done from checkpoint)")
            # Still need to reinitialize objects (they're not serialized)
            if not self._initialize_components():
                logger.error("Failed to reinitialize ColPali components")
                return {}

        # Run evaluation
        logger.info(f"📊 Evaluating {len(samples)} questions, starting from #{start_idx + 1}")

        for i in range(start_idx, len(samples)):
            try:
                sample = samples[i]
                result = self._evaluate_single_question(sample, i + 1)
                results.append(result)

                # Save checkpoint every question (ColPali is slow)
                self._save_checkpoint(results, i + 1, len(samples), initialization_done=True)

            except KeyboardInterrupt:
                logger.info("🛑 ColPali evaluation interrupted by user")
                self._save_checkpoint(results, i, len(samples), initialization_done=True)
                break
            except Exception as e:
                logger.error(f"Unexpected error on question {i + 1}: {e}")
                logger.error(traceback.format_exc())
                # Create error result and continue
                error_result = {
                    "question_id": i + 1,
                    "question": samples[i]["question"],
                    "predicted_answer": "System Error",
                    "ground_truth": samples[i]["answer"],
                    "answer_format": samples[i]["answer_format"],
                    "is_correct": False,
                    "confidence": 0.0,
                    "processing_time": 0.0,
                    "error": str(e)
                }
                results.append(error_result)
                continue

        # Final save
        final_results = self._compile_results(results)
        self._save_final_results(final_results)
        return final_results

    def _compile_results(self, results: List[Dict]) -> Dict[str, Any]:
        """Compile final evaluation results"""
        if not results:
            return {}

        total_samples = len(results)
        correct_count = sum(1 for r in results if r.get("is_correct", False))
        total_time = sum(r.get("processing_time", 0) for r in results)

        accuracy = correct_count / total_samples if total_samples else 0

        return {
            "approach": "ColPali Visual RAG (MMESGBench Replication)",
            "model": "qwen-vl-max",
            "dataset": "AR6 Synthesis Report (MMESGBench)",
            "total_samples": total_samples,
            "correct_predictions": correct_count,
            "accuracy": accuracy,
            "target_accuracy": 0.518,
            "avg_processing_time": total_time / total_samples if total_samples else 0,
            "total_time": total_time,
            "results": results
        }

    def _save_final_results(self, results: Dict[str, Any]):
        """Save final results to file"""
        try:
            with open(self.results_file, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"💾 Final ColPali results saved to: {self.results_file}")
        except Exception as e:
            logger.error(f"Failed to save final results: {e}")

    def print_results(self, results: Dict[str, Any]):
        """Print evaluation results"""
        if not results:
            print("❌ No results to display")
            return

        print("\\n" + "="*80)
        print("🎯 COLPALI VISUAL RAG EVALUATION RESULTS")
        print("="*80)

        accuracy = results.get('accuracy', 0)
        target = results.get('target_accuracy', 0.518)
        correct = results.get('correct_predictions', 0)
        total = results.get('total_samples', 0)

        print(f"Dataset: {results.get('dataset', 'AR6')}")
        print(f"Approach: {results.get('approach', 'ColPali Visual RAG')}")
        print(f"Model: {results.get('model', 'qwen-vl-max')}")

        print(f"\\n📊 PERFORMANCE METRICS:")
        print(f"Accuracy: {accuracy:.1%} (Target: {target:.1%})")
        print(f"Correct Predictions: {correct}/{total}")
        print(f"Average Time: {results.get('avg_processing_time', 0):.1f}s per question")

        target_met = "✅" if accuracy >= target else "❌"
        print(f"\\nTarget Achievement: {target_met}")

        if accuracy >= target:
            print("🎉 ColPali target accuracy achieved!")
        else:
            gap = target - accuracy
            print(f"📈 Gap to target: {gap:.1%}")

        # Show question breakdown
        print(f"\\n📝 QUESTION BREAKDOWN:")
        for result in results.get('results', []):
            status = "✅" if result.get('is_correct', False) else "❌"
            error = " (ERROR)" if result.get('error') else ""
            print(f"{result['question_id']}. {status} {result['answer_format']}: '{result['predicted_answer']}' vs '{result['ground_truth']}'{error}")


def main():
    """Run robust ColPali evaluation"""
    print("🛡️ Robust ColPali Visual RAG Evaluation with Checkpoints")
    print("Target: 51.8% accuracy (MMESGBench)")
    print("="*80)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    evaluator = RobustColPaliEvaluator()

    try:
        results = evaluator.run_evaluation(limit=10, resume=True)

        if results:
            evaluator.print_results(results)
            print("\\n🎉 Robust ColPali evaluation completed!")
        else:
            print("❌ ColPali evaluation failed")

    except KeyboardInterrupt:
        print("\\n🛑 Evaluation interrupted. Progress saved to checkpoint.")
    except Exception as e:
        print(f"\\n💥 Unexpected error: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()