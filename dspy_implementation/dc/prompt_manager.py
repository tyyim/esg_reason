"""
Prompt Manager for Dynamic Cheatsheet
Supports both original DC prompts and custom ESG prompts
"""

from pathlib import Path
from typing import Literal

# Import custom prompts
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from dspy_implementation.dc.dc_prompts import (
    GENERATOR_PROMPT as CUSTOM_GENERATOR_PROMPT,
    CURATOR_PROMPT as CUSTOM_CURATOR_PROMPT,
    CURATOR_PROMPT_RS as CUSTOM_CURATOR_PROMPT_RS
)


def load_original_prompts(prompts_dir: str = None) -> dict:
    """
    Load original Dynamic Cheatsheet prompts from dc_repo
    
    Args:
        prompts_dir: Path to prompts directory (default: dc_repo/prompts)
    
    Returns:
        dict with keys: 'generator', 'curator_cumulative', 'curator_rs'
    """
    if prompts_dir is None:
        project_root = Path(__file__).parent.parent.parent
        prompts_dir = project_root / "dc_repo" / "prompts"
    else:
        prompts_dir = Path(prompts_dir)
    
    prompts = {}
    
    # Load generator prompt
    generator_path = prompts_dir / "generator_prompt.txt"
    if generator_path.exists():
        with open(generator_path, 'r', encoding='utf-8') as f:
            prompts['generator'] = f.read()
    else:
        raise FileNotFoundError(f"Generator prompt not found at {generator_path}")
    
    # Load curator prompts
    curator_cumulative_path = prompts_dir / "curator_prompt_for_dc_cumulative.txt"
    if curator_cumulative_path.exists():
        with open(curator_cumulative_path, 'r', encoding='utf-8') as f:
            prompts['curator_cumulative'] = f.read()
    else:
        raise FileNotFoundError(f"Curator cumulative prompt not found at {curator_cumulative_path}")
    
    curator_rs_path = prompts_dir / "curator_prompt_for_dc_retrieval_synthesis.txt"
    if curator_rs_path.exists():
        with open(curator_rs_path, 'r', encoding='utf-8') as f:
            prompts['curator_rs'] = f.read()
    else:
        raise FileNotFoundError(f"Curator RS prompt not found at {curator_rs_path}")
    
    return prompts


def get_prompts(
    prompt_type: Literal['original', 'custom'],
    approach: Literal['cumulative', 'retrieval_synthesis'] = 'cumulative',
    prompts_dir: str = None
) -> dict:
    """
    Get prompts based on type and approach
    
    Args:
        prompt_type: 
            - 'custom': generator and curator both use custom prompts
            - 'original': generator uses custom prompts, curator uses original prompts
        approach: 'cumulative' or 'retrieval_synthesis'
        prompts_dir: Path to original prompts directory (used for curator in 'original' type)
    
    Returns:
        dict with 'generator' and 'curator' keys
    """
    if prompt_type == 'custom':
        # Custom mode: generator and curator both use custom prompts
        return {
            'generator': CUSTOM_GENERATOR_PROMPT,
            'curator': CUSTOM_CURATOR_PROMPT if approach == 'cumulative' 
                     else CUSTOM_CURATOR_PROMPT_RS
        }
    elif prompt_type == 'original':
        # Original mode: generator uses custom prompts, curator uses original prompts
        original_prompts = load_original_prompts(prompts_dir)
        return {
            'generator': CUSTOM_GENERATOR_PROMPT,
            'curator': original_prompts['curator_cumulative'] if approach == 'cumulative' 
                     else original_prompts['curator_rs']
        }
    else:
        raise ValueError(f"Unknown prompt_type: {prompt_type}. Must be 'original' or 'custom'")

