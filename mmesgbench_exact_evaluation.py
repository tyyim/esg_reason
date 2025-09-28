#!/usr/bin/env python3
"""
MMESGBench Exact Evaluation Logic
Implements the exact evaluation functions from MMESGBench/src/eval/eval_score.py
"""

import re
import ast
import json
from typing import List, Union, Any
from difflib import SequenceMatcher

def get_clean_string(s: str) -> str:
    """Clean string by removing special characters and normalizing"""
    s = str(s).strip()
    # Remove percentage signs and clean up
    s = re.sub(r'[^\w\s\.\-\+]', '', s)
    return s.strip()

def is_float_equal(gt: float, pred: float, include_percentage: bool = True, is_close: bool = True) -> bool:
    """Check if two floats are equal with tolerance"""
    if is_close:
        # Use relative tolerance of 1e-3 (0.1%)
        tolerance = 1e-3
        if abs(gt) > 0:
            return abs(gt - pred) / abs(gt) <= tolerance
        else:
            return abs(pred) <= tolerance
    else:
        return gt == pred

def anls_compute(gt_ans: str, pred_ans: str, threshold: float = 0.5) -> float:
    """Compute Average Normalized Levenshtein Similarity"""
    gt_ans = gt_ans.strip().lower()
    pred_ans = pred_ans.strip().lower()

    if gt_ans == pred_ans:
        return 1.0

    # Normalized Levenshtein Distance
    edit_distance = levenshtein_distance(gt_ans, pred_ans)
    max_len = max(len(gt_ans), len(pred_ans))

    if max_len == 0:
        return 1.0

    normalized_distance = edit_distance / max_len
    similarity = 1.0 - normalized_distance

    return similarity if similarity >= threshold else 0.0

def levenshtein_distance(s1: str, s2: str) -> int:
    """Compute Levenshtein distance between two strings"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def fuzzy_match(gt_ans: str, pred_ans: str, threshold: float = 0.8) -> bool:
    """Fuzzy string matching using sequence matcher"""
    gt_ans = gt_ans.strip().lower()
    pred_ans = pred_ans.strip().lower()

    if gt_ans == pred_ans:
        return True

    # Check if prediction is substring of ground truth or vice versa
    if gt_ans in pred_ans or pred_ans in gt_ans:
        return True

    # Use SequenceMatcher for fuzzy matching
    similarity = SequenceMatcher(None, gt_ans, pred_ans).ratio()
    return similarity >= threshold

def eval_score(gt: Any, pred: Any, answer_type: str) -> bool:
    """
    Main evaluation function - exact replication of MMESGBench logic
    """
    gt = str(gt).strip() if gt is not None else ""
    pred = str(pred).strip() if pred is not None else ""

    if answer_type == "Int":
        try:
            # Try to parse as float first, then convert to int
            gt_int = int(float(gt))
            pred_int = int(float(pred))
            return gt_int == pred_int
        except (ValueError, TypeError):
            return False

    elif answer_type == "Float":
        try:
            gt_clean = get_clean_string(gt)
            pred_clean = get_clean_string(pred)

            gt_float = float(gt_clean)
            pred_float = float(pred_clean)

            return is_float_equal(gt_float, pred_float, include_percentage=True, is_close=True)
        except (ValueError, TypeError):
            return False

    elif answer_type == "Str":
        # First try exact match
        if gt.lower().strip() == pred.lower().strip():
            return True

        # Try substring matching
        if gt.lower().strip() in pred.lower().strip() or pred.lower().strip() in gt.lower().strip():
            return True

        # Use ANLS with threshold 0.5
        return anls_compute(gt, pred, threshold=0.5) >= 0.5

    elif answer_type == "List":
        try:
            # Parse ground truth list
            if gt.startswith('[') and gt.endswith(']'):
                gt_list = ast.literal_eval(gt)
            else:
                gt_list = [item.strip() for item in gt.split(',')]

            # Parse prediction list
            if pred.startswith('[') and pred.endswith(']'):
                pred_list = ast.literal_eval(pred)
            else:
                pred_list = [item.strip() for item in pred.split(',')]

            # Convert to strings and normalize
            gt_items = [str(item).strip().lower() for item in gt_list]
            pred_items = [str(item).strip().lower() for item in pred_list]

            # Use fuzzy matching for list comparison
            if len(gt_items) == 0 and len(pred_items) == 0:
                return True

            if len(gt_items) == 0 or len(pred_items) == 0:
                return False

            # Calculate fuzzy match score
            matched = 0
            for gt_item in gt_items:
                for pred_item in pred_items:
                    if fuzzy_match(gt_item, pred_item, threshold=0.8):
                        matched += 1
                        break

            # Require at least 80% of items to match
            return matched / len(gt_items) >= 0.8

        except (ValueError, SyntaxError, TypeError):
            return False

    elif answer_type == "None":
        # For None type, both should be empty or "none"
        gt_norm = gt.lower().strip()
        pred_norm = pred.lower().strip()

        none_values = ["", "none", "null", "n/a", "not applicable", "not answerable"]

        return (gt_norm in none_values) == (pred_norm in none_values)

    else:
        # Default to string comparison
        return gt.lower().strip() == pred.lower().strip()

def evaluate_prediction_mmesgbench(predicted_answer: str, ground_truth: str, answer_format: str) -> tuple:
    """
    Evaluate prediction using exact MMESGBench logic
    Returns: (is_correct, exact_match, f1_score)
    """
    # Main evaluation using their exact logic
    is_correct = eval_score(ground_truth, predicted_answer, answer_format)

    # Exact match (case-insensitive)
    exact_match = str(predicted_answer).strip().lower() == str(ground_truth).strip().lower()

    # F1 score calculation (for compatibility)
    if is_correct:
        f1_score = 1.0
    elif answer_format == "List":
        # For lists, use fuzzy matching score as F1
        try:
            if ground_truth.startswith('[') and ground_truth.endswith(']'):
                gt_list = ast.literal_eval(ground_truth)
            else:
                gt_list = [item.strip() for item in ground_truth.split(',')]

            if predicted_answer.startswith('[') and predicted_answer.endswith(']'):
                pred_list = ast.literal_eval(predicted_answer)
            else:
                pred_list = [item.strip() for item in predicted_answer.split(',')]

            gt_items = [str(item).strip().lower() for item in gt_list]
            pred_items = [str(item).strip().lower() for item in pred_list]

            if len(gt_items) == 0 and len(pred_items) == 0:
                f1_score = 1.0
            elif len(gt_items) == 0 or len(pred_items) == 0:
                f1_score = 0.0
            else:
                matched = 0
                for gt_item in gt_items:
                    for pred_item in pred_items:
                        if fuzzy_match(gt_item, pred_item, threshold=0.8):
                            matched += 1
                            break
                f1_score = matched / len(gt_items)
        except:
            f1_score = 0.0
    elif answer_format == "Str":
        # Use ANLS score as F1 for strings
        f1_score = anls_compute(ground_truth, predicted_answer, threshold=0.0)
    else:
        f1_score = 0.0

    return is_correct, exact_match, f1_score

# Test the evaluation functions
if __name__ == "__main__":
    # Test cases to verify the implementation
    test_cases = [
        # Int tests
        ("3", "3.0", "Int", True),
        ("3", "3", "Int", True),
        ("3", "4", "Int", False),

        # Float tests
        ("1.3", "1.3%", "Float", True),
        ("19.62", "4.10", "Float", False),
        ("1.0", "1.001", "Float", True),  # Within tolerance

        # String tests
        ("North America", "North America", "Str", True),
        ("[0.8, 1.3]", "[0.88, 1.21]", "Str", False),
        ("More than 4°C", "4.4", "Str", False),

        # List tests
        ("['Ocean warming', 'ocean acidification']", "['Ocean warming', 'Ocean acidification', 'Overfishing']", "List", True),
        ("['Africa', 'Asia', 'Central and South America']", "['Sub-Saharan Africa', 'South Asia', 'Small Island Developing States (SIDS)']", "List", False),
    ]

    print("🧪 Testing MMESGBench Exact Evaluation Logic")
    print("=" * 60)

    for i, (gt, pred, fmt, expected) in enumerate(test_cases, 1):
        result = eval_score(gt, pred, fmt)
        status = "✅" if result == expected else "❌"
        print(f"{status} Test {i}: {fmt}")
        print(f"   GT: {gt}")
        print(f"   Pred: {pred}")
        print(f"   Expected: {expected}, Got: {result}")
        print()