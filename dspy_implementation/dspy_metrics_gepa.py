#!/usr/bin/env python3
"""
GEPA-specific Metric Functions with Rich Textual Feedback

Key difference from standard metrics:
- Returns {"score": float, "feedback": str} instead of just float
- Feedback provides detailed explanation of what went wrong/right
- Helps GEPA's reflection LM understand failures and propose better prompts
"""

from typing import Optional
import dspy
from MMESGBench.src.eval.eval_score import eval_score


def mmesgbench_gepa_metric(
    gold: dspy.Example,
    pred: dspy.Prediction,
    trace: Optional = None,
    pred_name: Optional[str] = None,
    pred_trace: Optional = None
) -> dict:
    """
    GEPA metric with rich feedback for ESG question answering.

    Returns dict with:
    - score: float between 0.0 and 1.0
    - feedback: str explaining the result

    Args:
        gold: Ground truth example
        pred: Model prediction
        trace: Full execution trace (optional)
        pred_name: Predictor name (optional)
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
    except Exception as e:
        return {
            "score": 0.0,
            "feedback": f"Evaluation failed: {str(e)}"
        }

    # Check retrieval correctness
    retrieved_pages = set()
    if hasattr(pred, 'context') and pred.context:
        # Extract page numbers from context
        import re
        page_matches = re.findall(r'\[Page (\d+)', pred.context)
        retrieved_pages = set(int(p) for p in page_matches)

    ground_truth_pages = set(gold.evidence_pages)
    retrieval_correct = ground_truth_pages.issubset(retrieved_pages)

    # End-to-end correctness
    e2e_correct = retrieval_correct and answer_correct

    # ==================================================
    # Generate Rich Textual Feedback for GEPA
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
    feedback_parts.append(f"Answer Type: {answer_format}")
    feedback_parts.append(f"Document: {gold.doc_id}")

    # 3. Retrieval feedback
    if not retrieval_correct:
        missing_pages = ground_truth_pages - retrieved_pages
        extra_pages = retrieved_pages - ground_truth_pages

        feedback_parts.append(f"\n🔍 RETRIEVAL ISSUE:")
        feedback_parts.append(f"  Required pages: {sorted(ground_truth_pages)}")
        feedback_parts.append(f"  Retrieved pages: {sorted(retrieved_pages) if retrieved_pages else 'None'}")

        if missing_pages:
            feedback_parts.append(f"  ❌ Missing pages: {sorted(missing_pages)}")
            feedback_parts.append(f"  → The query generation needs to better target these pages.")

        if extra_pages:
            feedback_parts.append(f"  ⚠️ Extra pages: {sorted(extra_pages)}")
            feedback_parts.append(f"  → These pages are irrelevant to the question.")
    else:
        feedback_parts.append(f"\n✅ RETRIEVAL OK: Found all {len(ground_truth_pages)} required pages")

    # 4. Answer feedback
    if not answer_correct:
        feedback_parts.append(f"\n🎯 ANSWER ISSUE:")
        feedback_parts.append(f"  Ground truth: {ground_truth}")
        feedback_parts.append(f"  Predicted: {predicted_answer}")
        feedback_parts.append(f"  Similarity score: {answer_score:.2f} (threshold: 0.50)")

        # Provide specific guidance based on answer type
        if answer_format == "Str":
            feedback_parts.append(f"  → Extract the exact string from context, avoid paraphrasing.")
        elif answer_format in ["Int", "Float"]:
            feedback_parts.append(f"  → Extract only the numeric value, no units or explanations.")
        elif answer_format == "List":
            feedback_parts.append(f"  → Return all matching items as a list, in correct format.")
        elif answer_format is None:
            feedback_parts.append(f"  → Question cannot be answered from the document.")
    else:
        feedback_parts.append(f"\n✅ ANSWER OK: Correct extraction (score: {answer_score:.2f})")

    # 5. Reasoning analysis (if available)
    if hasattr(pred, 'analysis') and pred.analysis:
        analysis_preview = pred.analysis[:200] + "..." if len(pred.analysis) > 200 else pred.analysis
        feedback_parts.append(f"\n📝 REASONING: {analysis_preview}")

    # 6. Actionable recommendation
    if not e2e_correct:
        feedback_parts.append(f"\n💡 RECOMMENDATION:")
        if not retrieval_correct and not answer_correct:
            feedback_parts.append(f"  1. Improve query generation to find pages {sorted(ground_truth_pages)}")
            feedback_parts.append(f"  2. Once correct pages retrieved, improve answer extraction")
        elif not retrieval_correct:
            feedback_parts.append(f"  Focus on query generation - answer extraction is working")
        else:
            feedback_parts.append(f"  Focus on answer extraction - retrieval is working")

    # Combine all feedback
    feedback = "\n".join(feedback_parts)

    # Return score with detailed feedback
    final_score = 1.0 if e2e_correct else (0.5 if (retrieval_correct or answer_correct) else 0.0)

    return {
        "score": final_score,
        "feedback": feedback
    }


def mmesgbench_answer_only_gepa_metric(
    gold: dspy.Example,
    pred: dspy.Prediction,
    trace: Optional = None,
    pred_name: Optional[str] = None,
    pred_trace: Optional = None
) -> dict:
    """
    GEPA metric focusing ONLY on answer correctness (for fair model comparison).

    This matches our PRIMARY METRIC where retrieval is constant across models.
    """

    predicted_answer = pred.answer if hasattr(pred, 'answer') else ""
    ground_truth = gold.answer
    answer_format = gold.answer_format

    try:
        answer_score = eval_score(ground_truth, predicted_answer, answer_format)
        answer_correct = (answer_score >= 0.5)
    except Exception as e:
        return {
            "score": 0.0,
            "feedback": f"Evaluation failed: {str(e)}"
        }

    # Simplified feedback for answer-only optimization
    feedback_parts = []

    if answer_correct:
        feedback_parts.append(f"✅ CORRECT ANSWER (score: {answer_score:.2f})")
    else:
        feedback_parts.append(f"❌ INCORRECT ANSWER")
        feedback_parts.append(f"\nQuestion: {gold.question}")
        feedback_parts.append(f"Expected: {ground_truth} ({answer_format})")
        feedback_parts.append(f"Got: {predicted_answer}")
        feedback_parts.append(f"Similarity: {answer_score:.2f} (need ≥0.50)")

        # Type-specific guidance
        if answer_format == "Str":
            feedback_parts.append(f"\n→ Extract exact string from context")
        elif answer_format in ["Int", "Float"]:
            feedback_parts.append(f"\n→ Extract only numeric value")
        elif answer_format == "List":
            feedback_parts.append(f"\n→ Return complete list of items")

    feedback = "\n".join(feedback_parts)

    return {
        "score": 1.0 if answer_correct else 0.0,
        "feedback": feedback
    }
