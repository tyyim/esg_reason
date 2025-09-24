"""
Prototype evaluator for MMESGBench using DSPy and Qwen models.
Simple evaluation pipeline for testing the basic functionality.
"""

import logging
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from src.utils.config import config
from src.data.mmesg_loader import MMESGSampleLoader

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Store evaluation results for a single prediction"""
    question: str
    predicted_answer: str
    ground_truth: str
    answer_format: str
    is_correct: bool
    confidence_score: float
    processing_time: float
    reasoning_trace: str


class SimpleESGEvaluator:
    """Simple evaluator for ESG questions using basic string matching"""

    def __init__(self):
        self.tolerance = 0.01  # 1% tolerance for numeric answers

    def evaluate_prediction(self, prediction: str, ground_truth: str,
                          answer_format: str) -> Tuple[bool, float]:
        """
        Evaluate a single prediction against ground truth
        Returns (is_correct, confidence_score)
        """
        try:
            if answer_format == "Str":
                return self._evaluate_string(prediction, ground_truth)
            elif answer_format == "Int":
                return self._evaluate_integer(prediction, ground_truth)
            elif answer_format == "Float":
                return self._evaluate_float(prediction, ground_truth)
            elif answer_format == "List":
                return self._evaluate_list(prediction, ground_truth)
            else:
                # Default to string comparison
                return self._evaluate_string(prediction, ground_truth)
        except Exception as e:
            logger.error(f"Error evaluating prediction: {e}")
            return False, 0.0

    def _evaluate_string(self, prediction: str, ground_truth: str) -> Tuple[bool, float]:
        """Evaluate string answers with fuzzy matching"""
        pred_clean = prediction.strip().lower()
        gt_clean = ground_truth.strip().lower()

        if pred_clean == gt_clean:
            return True, 1.0

        # Check if prediction contains the ground truth
        if gt_clean in pred_clean:
            return True, 0.8

        # Basic fuzzy matching (simple word overlap)
        pred_words = set(pred_clean.split())
        gt_words = set(gt_clean.split())

        if gt_words and pred_words:
            overlap = len(pred_words.intersection(gt_words))
            total = len(gt_words)
            similarity = overlap / total

            if similarity >= 0.7:
                return True, similarity

        return False, 0.0

    def _evaluate_integer(self, prediction: str, ground_truth: str) -> Tuple[bool, float]:
        """Evaluate integer answers"""
        try:
            pred_val = int(float(prediction.strip()))
            gt_val = int(float(ground_truth.strip()))

            if pred_val == gt_val:
                return True, 1.0
            else:
                return False, 0.0
        except (ValueError, TypeError):
            return False, 0.0

    def _evaluate_float(self, prediction: str, ground_truth: str) -> Tuple[bool, float]:
        """Evaluate float answers with tolerance"""
        try:
            pred_val = float(prediction.strip())
            gt_val = float(ground_truth.strip())

            if abs(pred_val - gt_val) < 1e-10:  # Exact match
                return True, 1.0

            # Check tolerance (1% as per spec)
            relative_error = abs(pred_val - gt_val) / max(abs(gt_val), 1e-10)
            if relative_error <= self.tolerance:
                confidence = 1.0 - (relative_error / self.tolerance) * 0.2
                return True, max(confidence, 0.8)

            return False, 0.0
        except (ValueError, TypeError):
            return False, 0.0

    def _evaluate_list(self, prediction: str, ground_truth: str) -> Tuple[bool, float]:
        """Evaluate list answers"""
        try:
            # Try to parse as JSON lists
            if prediction.startswith('[') and prediction.endswith(']'):
                pred_list = json.loads(prediction)
            else:
                pred_list = [item.strip() for item in prediction.split(',')]

            if ground_truth.startswith('[') and ground_truth.endswith(']'):
                gt_list = json.loads(ground_truth)
            else:
                gt_list = [item.strip() for item in ground_truth.split(',')]

            # Check exact match
            if pred_list == gt_list:
                return True, 1.0

            # Check partial match
            if isinstance(pred_list, list) and isinstance(gt_list, list):
                correct_items = sum(1 for item in pred_list if item in gt_list)
                if correct_items > 0:
                    confidence = correct_items / len(gt_list)
                    return confidence >= 0.5, confidence

            return False, 0.0
        except (json.JSONDecodeError, ValueError):
            return False, 0.0


class MockQwenReasoner:
    """Mock reasoner for testing without actual API calls"""

    def __init__(self):
        self.model_name = "mock-qwen-plus"

    def reason(self, question: str, context: str = "", doc_id: str = "") -> Dict[str, Any]:
        """Mock reasoning that returns simple answers for testing"""

        # Simple pattern matching for demo
        question_lower = question.lower()

        if "north america" in question_lower or "highest per capita" in question_lower:
            answer = "North America"
            reasoning = "Based on the context about GHG emissions, North America has the highest per capita emissions."
        elif "2040" in question_lower and "flooding" in question_lower:
            answer = "19.62"
            reasoning = "Calculated from the coastal flooding projections in the IPCC report."
        elif "net zero" in question_lower and "2050" in question_lower:
            answer = "2050"
            reasoning = "According to IPCC projections for the SSP1-1.9 scenario."
        elif "working groups" in question_lower:
            answer = "3"
            reasoning = "The AR6 report mentions three working groups."
        else:
            # Default response
            answer = "Unknown"
            reasoning = "Unable to determine answer from available context."

        return {
            "answer": answer,
            "reasoning": reasoning,
            "confidence": 0.85,
            "model": self.model_name
        }


class PrototypeEvaluationPipeline:
    """Main evaluation pipeline for prototype testing"""

    def __init__(self, use_mock: bool = True):
        self.loader = MMESGSampleLoader(sample_size=5)
        self.evaluator = SimpleESGEvaluator()
        self.use_mock = use_mock

        if use_mock:
            self.reasoner = MockQwenReasoner()
            logger.info("Using mock reasoner for testing")
        else:
            # TODO: Implement actual Qwen API integration
            logger.warning("Real Qwen API not implemented yet, using mock")
            self.reasoner = MockQwenReasoner()

    def run_evaluation(self) -> Dict[str, Any]:
        """Run evaluation on sample dataset"""
        logger.info("Starting prototype evaluation")

        # Load sample data
        samples = self.loader.load_sample_data()
        if not samples:
            logger.error("No samples loaded")
            return {}

        results = []
        total_time = 0
        correct_count = 0

        for i, sample in enumerate(samples):
            logger.info(f"Processing sample {i+1}/{len(samples)}")

            start_time = time.time()

            # Get prediction from reasoner
            prediction_result = self.reasoner.reason(
                question=sample["question"],
                context="",  # TODO: Add actual context from PDFs
                doc_id=sample["doc_id"]
            )

            processing_time = time.time() - start_time
            total_time += processing_time

            # Evaluate prediction
            is_correct, confidence = self.evaluator.evaluate_prediction(
                prediction=prediction_result["answer"],
                ground_truth=sample["answer"],
                answer_format=sample["answer_format"]
            )

            if is_correct:
                correct_count += 1

            # Store result
            result = EvaluationResult(
                question=sample["question"],
                predicted_answer=prediction_result["answer"],
                ground_truth=sample["answer"],
                answer_format=sample["answer_format"],
                is_correct=is_correct,
                confidence_score=confidence,
                processing_time=processing_time,
                reasoning_trace=prediction_result["reasoning"]
            )
            results.append(result)

            logger.info(f"Sample {i+1}: {'✓' if is_correct else '✗'} "
                       f"(confidence: {confidence:.2f})")

        # Calculate metrics
        accuracy = correct_count / len(samples) if samples else 0
        avg_time = total_time / len(samples) if samples else 0

        evaluation_summary = {
            "total_samples": len(samples),
            "correct_predictions": correct_count,
            "accuracy": accuracy,
            "average_processing_time": avg_time,
            "total_time": total_time,
            "results": results
        }

        logger.info(f"Evaluation completed: {correct_count}/{len(samples)} correct "
                   f"(accuracy: {accuracy:.2%})")

        return evaluation_summary

    def print_detailed_results(self, evaluation_summary: Dict[str, Any]):
        """Print detailed evaluation results"""
        print("\n" + "="*80)
        print("PROTOTYPE EVALUATION RESULTS")
        print("="*80)

        print(f"Total Samples: {evaluation_summary['total_samples']}")
        print(f"Correct Predictions: {evaluation_summary['correct_predictions']}")
        print(f"Accuracy: {evaluation_summary['accuracy']:.2%}")
        print(f"Average Processing Time: {evaluation_summary['average_processing_time']:.2f}s")
        print(f"Total Time: {evaluation_summary['total_time']:.2f}s")

        print("\nDETAILED RESULTS:")
        print("-"*80)

        for i, result in enumerate(evaluation_summary['results']):
            status = "✓ CORRECT" if result.is_correct else "✗ INCORRECT"
            print(f"\nSample {i+1}: {status}")
            print(f"Question: {result.question[:100]}...")
            print(f"Predicted: {result.predicted_answer}")
            print(f"Ground Truth: {result.ground_truth}")
            print(f"Format: {result.answer_format}")
            print(f"Confidence: {result.confidence_score:.2f}")
            print(f"Time: {result.processing_time:.2f}s")
            print(f"Reasoning: {result.reasoning_trace[:150]}...")


def run_prototype_test():
    """Run the prototype evaluation test"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create and run pipeline
    pipeline = PrototypeEvaluationPipeline(use_mock=True)
    results = pipeline.run_evaluation()

    if results:
        pipeline.print_detailed_results(results)
        return results
    else:
        print("Evaluation failed")
        return None


if __name__ == "__main__":
    run_prototype_test()