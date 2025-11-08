"""
Central evaluation module for all MMESGBench scoring.

This module provides the corrected eval_score that handles null equivalence.
All evaluation scripts should import from here instead of directly from MMESGBench.

Usage:
    from src.evaluation import eval_score

    score = eval_score(gt, pred, answer_type)  # Uses corrected version

Author: Sum Yee Chan
Date: November 7, 2025
"""

from src.evaluation_utils import eval_score_fixed as eval_score

__all__ = ['eval_score']
