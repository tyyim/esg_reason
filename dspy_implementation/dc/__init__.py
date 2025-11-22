"""
Dynamic Cheatsheet Integration for ESG Reasoning
"""

import sys
from pathlib import Path

# Add dc_repo to path for direct imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "dc_repo"))

from .evaluate_dc import evaluate_dc, DCLanguageModel
from .prompt_manager import get_prompts, load_original_prompts
from dynamic_cheatsheet.utils.extractor import extract_answer, extract_cheatsheet

__all__ = [
    'evaluate_dc',
    'DCLanguageModel',
    'get_prompts',
    'load_original_prompts',
    'extract_answer',
    'extract_cheatsheet',
]

