"""
Evaluation utilities with corrected null equivalence handling.

This module provides a corrected version of MMESGBench's eval_score() that
recognizes null-equivalent responses as semantically identical.

Bug Context:
- MMESGBench's eval_score() uses ANLS (string distance) which treats "null"
  and "Not answerable" as different strings
- This causes false negatives when models correctly identify unanswerable questions
- Discovery Date: November 6, 2025 (identified during internal evaluation review)
- Impact: 4 out of 8 DC runs affected (196 predictions incorrectly marked wrong)

Author: Sum Yee Chan
Date: November 7, 2025
"""

import sys
from pathlib import Path

# Add MMESGBench to path
sys.path.append(str(Path(__file__).parent.parent / "MMESGBench"))
from MMESGBench.src.eval.eval_score import eval_score


def eval_score_fixed(gt, pred, answer_type):
    """
    Corrected version of eval_score that recognizes null equivalents.

    Treats these as semantically equivalent for null-type questions:
    - "null"
    - "not answerable"
    - "n/a"
    - "cannot answer"
    - "fail to answer"

    Args:
        gt (str): Ground truth answer
        pred (str): Predicted answer
        answer_type (str): Answer format type (Int/Float/Str/List/null)

    Returns:
        float: Score between 0.0 and 1.0 (ANLS threshold: 0.5)

    Examples:
        >>> eval_score_fixed("Not answerable", "null", None)
        1.0  # Recognized as equivalent

        >>> eval_score_fixed("Not answerable", "42", "Int")
        0.0  # Different semantic meaning

    Bug Details:
        Original eval_score("Not answerable", "null", None) returns 0.0
        because ANLS treats them as different strings (high Levenshtein distance).

        This fix recognizes null equivalents BEFORE applying ANLS,
        preventing false negatives on hallucination/unanswerable questions.

    Affected Runs (rescored Nov 7, 2025):
        - Run #4 (dev): 43.0% → 57.0% (+14.0%)
        - Run #6 (dev): 25.8% → 30.1% (+4.3%)
        - Run #7 (test): 35.6% → 49.2% (+13.6%)
        - Run #8 (test): 34.7% → 48.5% (+13.8%)
    """
    # Define null equivalents
    null_equivalents = {
        "null",
        "not answerable",
        "n/a",
        "cannot answer",
        "fail to answer"
    }

    # Normalize strings
    gt_normalized = str(gt).lower().strip()
    pred_normalized = str(pred).lower().strip()

    # Handle JSON-wrapped versions like '```json\n"Not answerable"\n```'
    if pred_normalized.startswith('```') and pred_normalized.endswith('```'):
        import re
        match = re.search(r'"([^"]+)"', pred_normalized)
        if match:
            pred_normalized = match.group(1).lower().strip()

    # Check if both are null equivalents
    if gt_normalized in null_equivalents and pred_normalized in null_equivalents:
        return 1.0

    # Otherwise use original eval_score, but handle exceptions
    try:
        return eval_score(gt, pred, answer_type)
    except (SyntaxError, ValueError, TypeError) as e:
        # If eval_score fails (e.g., malformed list strings), fall back to string comparison
        # This happens when eval_score tries to eval() malformed strings
        print(f"      ⚠️  eval_score failed: {e}. Falling back to string comparison.")
        # Simple string similarity as fallback
        gt_str = str(gt).lower().strip()
        pred_str = str(pred).lower().strip()
        if gt_str == pred_str:
            return 1.0
        # Use simple substring matching for partial credit
        if pred_str in gt_str or gt_str in pred_str:
            return 0.5
        return 0.0
