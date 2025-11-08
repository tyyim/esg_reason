#!/usr/bin/env python3
"""
GEPA-Compatible Metric Functions with Rich Textual Feedback

CRITICAL FIX (2025-10-17):
- GEPA metrics can return EITHER float OR ScoreWithFeedback (Prediction subclass)
- DSPy's evaluation framework needs to sum scores for aggregation
- Solution: Return float by default, ScoreWithFeedback only when pred_name is provided

Key insight from GEPA source code:
- When pred_name is None: Return float for aggregation
- When pred_name is provided: Return ScoreWithFeedback(score=float, feedback=str)
- ScoreWithFeedback is a Prediction subclass with .score and .feedback attributes
"""

from typing import Optional, Union
import dspy
from dspy.primitives import Prediction
from src.evaluation import eval_score


# Define ScoreWithFeedback class (from GEPA's dspy_adapter)
class ScoreWithFeedback(Prediction):
    """
    Prediction subclass for GEPA feedback metrics.
    Must have .score and .feedback attributes for GEPA's reflection mechanism.
    Supports addition for DSPy's aggregation.
    """
    score: float
    feedback: str

    def __add__(self, other):
        """Support addition for aggregation (returns score only)"""
        if isinstance(other, ScoreWithFeedback):
            return self.score + other.score
        elif isinstance(other, (int, float)):
            return self.score + other
        else:
            return NotImplemented

    def __radd__(self, other):
        """Support right-side addition (for sum() with start=0)"""
        if isinstance(other, (int, float)):
            return other + self.score
        else:
            return NotImplemented


def mmesgbench_answer_only_gepa_metric(
    gold: dspy.Example,
    pred: dspy.Prediction,
    trace: Optional = None,
    pred_name: Optional[str] = None,
    pred_trace: Optional = None
) -> Union[float, dict]:
    """
    GEPA-compatible metric focusing on answer accuracy with optional feedback.

    Returns:
        - float: When called for aggregation (pred_name is None)
        - dict: {"score": float, "feedback": str} when called for reflection (pred_name provided)

    Args:
        gold: Ground truth example
        pred: Model prediction
        trace: Full execution trace (optional)
        pred_name: Predictor name - if provided, return feedback
        pred_trace: Predictor-specific trace (optional)
    """

    # Extract answer and format
    predicted_answer = pred.answer if hasattr(pred, 'answer') else ""
    ground_truth = gold.answer
    answer_format = gold.answer_format

    # Calculate answer correctness using MMESGBench's eval_score
    try:
        answer_score = eval_score(ground_truth, predicted_answer, answer_format)
        answer_correct = (answer_score >= 0.5)  # ANLS 0.5 threshold
        score = 1.0 if answer_correct else 0.0
    except Exception as e:
        score = 0.0
        if pred_name:  # Only include feedback if requested
            return ScoreWithFeedback(
                score=0.0,
                feedback=f"❌ Evaluation failed: {str(e)}"
            )
        else:
            return 0.0

    # ==================================================
    # If no feedback requested, return score directly
    # ==================================================
    if not pred_name:
        return score

    # ==================================================
    # Generate Rich Textual Feedback for GEPA Reflection
    # ==================================================

    feedback_parts = []

    # 1. Overall outcome
    if answer_correct:
        feedback_parts.append(f"✅ CORRECT")
    else:
        feedback_parts.append(f"❌ INCORRECT")

    # 2. Question context
    feedback_parts.append(f"\nQuestion: {gold.question}")
    feedback_parts.append(f"Expected Answer: {ground_truth}")
    feedback_parts.append(f"Predicted Answer: {predicted_answer}")
    feedback_parts.append(f"Answer Type: {answer_format}")

    # 3. Answer analysis
    if not answer_correct:
        feedback_parts.append(f"\n🎯 ANSWER ISSUE:")

        # Type-specific guidance
        if answer_format == "Str":
            feedback_parts.append(f"  → Extract the exact string from the context")
            feedback_parts.append(f"  → Watch for capitalization and formatting")
        elif answer_format == "Float":
            feedback_parts.append(f"  → Extract the numeric value precisely")
            feedback_parts.append(f"  → Check units and decimal places")
        elif answer_format == "Int":
            feedback_parts.append(f"  → Extract the integer value")
            feedback_parts.append(f"  → Don't include units or descriptions")
        elif answer_format == "List":
            feedback_parts.append(f"  → Extract all items in the list")
            feedback_parts.append(f"  → Ensure proper list formatting")

    # 4. Actionable recommendation
    feedback_parts.append(f"\n💡 RECOMMENDATION:")
    if answer_correct:
        feedback_parts.append(f"  ✅ Current prompts work well for this type of question")
        feedback_parts.append(f"  → Keep similar approach for {answer_format} questions")
    else:
        feedback_parts.append(f"  → Improve {answer_format} answer extraction")
        feedback_parts.append(f"  → Be more precise in identifying the exact value")
        feedback_parts.append(f"  → Verify answer format matches expected type")

    return ScoreWithFeedback(
        score=score,
        feedback="\n".join(feedback_parts)
    )


def mmesgbench_full_gepa_metric(
    gold: dspy.Example,
    pred: dspy.Prediction,
    trace: Optional = None,
    pred_name: Optional[str] = None,
    pred_trace: Optional = None
) -> Union[float, dict]:
    """
    GEPA-compatible metric with retrieval + answer feedback.

    Returns:
        - float: When called for aggregation (pred_name is None)
        - dict: {"score": float, "feedback": str} when called for reflection (pred_name provided)
    """

    # Extract answer and format
    predicted_answer = pred.answer if hasattr(pred, 'answer') else ""
    ground_truth = gold.answer
    answer_format = gold.answer_format

    # Calculate answer correctness
    try:
        answer_score = eval_score(ground_truth, predicted_answer, answer_format)
        answer_correct = (answer_score >= 0.5)
    except Exception as e:
        if pred_name:
            return ScoreWithFeedback(score=0.0, feedback=f"❌ Evaluation failed: {str(e)}")
        else:
            return 0.0

    # Check retrieval correctness
    retrieved_pages = set()
    if hasattr(pred, 'context') and pred.context:
        import re
        page_matches = re.findall(r'\[Page (\d+)', pred.context)
        retrieved_pages = set(int(p) for p in page_matches)

    ground_truth_pages = set(gold.evidence_pages)
    retrieval_correct = ground_truth_pages.issubset(retrieved_pages)

    # End-to-end correctness
    e2e_correct = retrieval_correct and answer_correct
    score = 1.0 if e2e_correct else 0.0

    # If no feedback requested, return score directly
    if not pred_name:
        return score

    # ==================================================
    # Generate Rich Textual Feedback
    # ==================================================

    feedback_parts = []

    # 1. Overall outcome
    if e2e_correct:
        feedback_parts.append("✅ CORRECT: Both retrieval and answer are correct.")
    elif answer_correct:
        feedback_parts.append("⚠️ PARTIAL: Answer is correct but retrieval missed some evidence pages.")
    elif retrieval_correct:
        feedback_parts.append("⚠️ PARTIAL: Retrieved correct pages but answer extraction failed.")
    else:
        feedback_parts.append("❌ INCORRECT: Both retrieval and answer need improvement.")

    # 2. Question details
    feedback_parts.append(f"\nQuestion: {gold.question}")
    feedback_parts.append(f"Document: {gold.doc_id}")
    feedback_parts.append(f"Answer Type: {answer_format}")

    # 3. Retrieval feedback
    if not retrieval_correct:
        missing_pages = ground_truth_pages - retrieved_pages
        feedback_parts.append(f"\n🔍 RETRIEVAL ISSUE:")
        feedback_parts.append(f"  Required pages: {sorted(ground_truth_pages)}")
        feedback_parts.append(f"  Retrieved pages: {sorted(retrieved_pages) if retrieved_pages else 'None'}")
        if missing_pages:
            feedback_parts.append(f"  ❌ Missing pages: {sorted(missing_pages)}")
            feedback_parts.append(f"  → Query generation needs to better target these pages")

    # 4. Answer feedback
    if not answer_correct:
        feedback_parts.append(f"\n🎯 ANSWER ISSUE:")
        feedback_parts.append(f"  Expected: {ground_truth}")
        feedback_parts.append(f"  Predicted: {predicted_answer}")
        feedback_parts.append(f"  → Extract exact value from context")

    # 5. Recommendation
    feedback_parts.append(f"\n💡 RECOMMENDATION:")
    if e2e_correct:
        feedback_parts.append(f"  ✅ Current approach works well")
    elif not retrieval_correct:
        feedback_parts.append(f"  → Focus on improving query generation")
    elif not answer_correct:
        feedback_parts.append(f"  → Focus on improving answer extraction")

    return ScoreWithFeedback(
        score=score,
        feedback="\n".join(feedback_parts)
    )
