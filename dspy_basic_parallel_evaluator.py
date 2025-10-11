#!/usr/bin/env python3
"""
Basic DSPy Parallel Evaluator - Fair Comparison with MMESGBench

This evaluator uses:
- Corrected dataset (mmesgbench_dataset_corrected.json)
- NO query generation (baseline comparison)
- Proper "Not answerable" handling
- Async parallel execution (8 workers)
- Checkpoint every 25 questions
- Resume capability
"""

import os
import sys
import json
import asyncio
import aiohttp
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging
from tqdm import tqdm

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# DSPy imports
import dspy
from dspy_implementation.dspy_rag_enhanced import BaselineMMESGBenchRAG
from dspy_implementation.dspy_dataset import MMESGBenchDataset
from dspy_implementation.dspy_metrics_enhanced import evaluate_answer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dspy_basic_evaluation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BasicDSPyEvaluator:
    """Basic DSPy evaluator with parallel execution"""

    def __init__(self, max_workers: int = 8):
        """
        Initialize evaluator

        Args:
            max_workers: Maximum concurrent API calls
        """
        self.max_workers = max_workers
        self.checkpoint_file = "dspy_basic_checkpoint.json"
        self.results_file = "dspy_basic_results.json"

        # Setup DSPy with Qwen
        self._setup_dspy()

        # Initialize baseline RAG (no query generation)
        self.rag_module = BaselineMMESGBenchRAG()

        # Load dataset
        self.dataset = MMESGBenchDataset()
        self.questions = self.dataset.data

        logger.info(f"✅ Basic DSPy Evaluator initialized")
        logger.info(f"   • Workers: {max_workers}")
        logger.info(f"   • Dataset: {len(self.questions)} questions")
        logger.info(f"   • RAG: Baseline (no query generation)")

    def _setup_dspy(self):
        """Setup DSPy with Qwen configuration"""
        api_key = os.environ.get("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("DASHSCOPE_API_KEY not found in environment")

        # Initialize Qwen LLM
        qwen_lm = dspy.LM(
            model="qwen/qwen-max",
            api_key=api_key,
            api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model_type="chat"
        )

        dspy.configure(lm=qwen_lm)
        logger.info("✅ DSPy configured with Qwen Max")

    def load_checkpoint(self) -> Dict:
        """Load checkpoint if exists"""
        if Path(self.checkpoint_file).exists():
            try:
                with open(self.checkpoint_file, 'r') as f:
                    checkpoint = json.load(f)
                logger.info(f"📂 Loaded checkpoint: {checkpoint['completed']}/{checkpoint['total']} questions")
                return checkpoint
            except Exception as e:
                logger.error(f"Error loading checkpoint: {e}")
                return {"results": [], "completed": 0, "total": len(self.questions)}
        return {"results": [], "completed": 0, "total": len(self.questions)}

    def save_checkpoint(self, results: List[Dict], completed: int):
        """Save checkpoint"""
        try:
            checkpoint = {
                "results": results,
                "completed": completed,
                "total": len(self.questions),
                "timestamp": datetime.now().isoformat()
            }
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint, f, indent=2)
            logger.info(f"💾 Checkpoint saved: {completed}/{len(self.questions)}")
        except Exception as e:
            logger.error(f"Error saving checkpoint: {e}")

    def save_results(self, results: List[Dict], completed: int):
        """Save final results"""
        try:
            output = {
                "metadata": {
                    "evaluator": "Basic DSPy (Baseline RAG)",
                    "dataset": "mmesgbench_dataset_corrected.json",
                    "total_questions": len(self.questions),
                    "completed": completed,
                    "timestamp": datetime.now().isoformat(),
                    "query_generation": False,
                    "max_workers": self.max_workers
                },
                "results": results
            }
            with open(self.results_file, 'w') as f:
                json.dump(output, f, indent=2)
            logger.info(f"💾 Results saved: {self.results_file}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")

    async def evaluate_question(self, question_data: Dict, semaphore: asyncio.Semaphore) -> Dict:
        """
        Evaluate a single question using DSPy baseline RAG

        Args:
            question_data: Question from dataset
            semaphore: Concurrency limiter

        Returns:
            Result dictionary
        """
        async with semaphore:
            try:
                sample_id = question_data.get('sample_id', question_data.get('id', 'unknown'))
                question = question_data['question']
                doc_id = question_data['doc_id']
                ground_truth = question_data['ground_truth']
                answer_format = question_data['answer_format']

                # Run DSPy RAG module (synchronous call wrapped in async)
                loop = asyncio.get_event_loop()
                prediction = await loop.run_in_executor(
                    None,
                    lambda: self.rag_module.forward(
                        question=question,
                        doc_id=doc_id,
                        answer_format=answer_format
                    )
                )

                predicted_answer = prediction.answer

                # Evaluate
                is_correct, e2e_metrics = evaluate_answer(
                    predicted_answer=predicted_answer,
                    ground_truth=ground_truth,
                    answer_format=answer_format
                )

                result = {
                    "sample_id": sample_id,
                    "question": question,
                    "doc_id": doc_id,
                    "answer_format": answer_format,
                    "ground_truth": ground_truth,
                    "predicted_answer": predicted_answer,
                    "is_correct": is_correct,
                    "search_query": prediction.search_query,
                    "analysis": prediction.analysis[:500],  # Truncate for storage
                    "context_length": len(prediction.context) if prediction.context else 0,
                    "metrics": e2e_metrics
                }

                logger.info(f"✅ Q{sample_id}: {'CORRECT' if is_correct else 'WRONG'} - {predicted_answer}")
                return result

            except Exception as e:
                logger.error(f"❌ Error evaluating Q{sample_id}: {e}")
                return {
                    "sample_id": sample_id,
                    "question": question_data['question'],
                    "doc_id": question_data['doc_id'],
                    "answer_format": question_data['answer_format'],
                    "ground_truth": question_data['ground_truth'],
                    "predicted_answer": "ERROR",
                    "is_correct": False,
                    "error": str(e),
                    "metrics": {"exact_match": 0}
                }

    async def run_evaluation(self):
        """Run parallel evaluation on all questions"""
        logger.info("🚀 Starting Basic DSPy Parallel Evaluation")
        logger.info(f"📊 {len(self.questions)} questions to evaluate")
        logger.info(f"⚙️  {self.max_workers} parallel workers")

        # Load checkpoint
        checkpoint = self.load_checkpoint()
        completed = checkpoint['completed']
        results = checkpoint['results']

        # Skip completed questions
        remaining_questions = self.questions[completed:]

        if not remaining_questions:
            logger.info("✅ All questions already evaluated!")
            return results

        logger.info(f"▶️  Resuming from question {completed + 1}")

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_workers)

        # Progress bar
        pbar = tqdm(total=len(remaining_questions), initial=0, desc="Evaluating")

        # Process in batches for checkpoint
        batch_size = 25
        for batch_start in range(0, len(remaining_questions), batch_size):
            batch_end = min(batch_start + batch_size, len(remaining_questions))
            batch = remaining_questions[batch_start:batch_end]

            # Evaluate batch
            tasks = [self.evaluate_question(q, semaphore) for q in batch]
            batch_results = await asyncio.gather(*tasks)

            # Add to results
            results.extend(batch_results)
            completed += len(batch_results)

            # Update progress
            pbar.update(len(batch_results))

            # Save checkpoint
            self.save_checkpoint(results, completed)

        pbar.close()

        # Calculate final statistics
        total_correct = sum(1 for r in results if r['is_correct'])
        accuracy = (total_correct / len(results)) * 100

        logger.info("\n" + "=" * 60)
        logger.info("📊 FINAL RESULTS")
        logger.info("=" * 60)
        logger.info(f"Total Questions: {len(results)}")
        logger.info(f"Correct: {total_correct}")
        logger.info(f"Accuracy: {accuracy:.2f}%")
        logger.info("=" * 60)

        # Save final results
        self.save_results(results, completed)

        return results


async def main():
    """Main entry point"""
    # Setup environment
    if "DASHSCOPE_API_KEY" not in os.environ:
        api_key = "sk-398b62f740a643458bf06c26f0324df1"
        os.environ["DASHSCOPE_API_KEY"] = api_key
        logger.info("✅ API key set from default")

    # Create evaluator
    evaluator = BasicDSPyEvaluator(max_workers=8)

    # Run evaluation
    try:
        results = await evaluator.run_evaluation()
        logger.info("✅ Evaluation completed successfully!")
        return 0
    except KeyboardInterrupt:
        logger.info("\n🛑 Evaluation interrupted by user")
        logger.info("💾 Progress saved - resume by running again")
        return 1
    except Exception as e:
        logger.error(f"❌ Evaluation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
