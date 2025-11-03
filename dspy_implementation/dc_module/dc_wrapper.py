"""
Wrapper around Dynamic Cheatsheet for MMESGBench evaluation
Uses DC's own framework (NOT DSPy) but adapted for DashScope/Qwen models
"""
import sys
import os
import tiktoken
import dashscope
from dashscope import Generation

# Add DC repo to path for utility functions
DC_REPO_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'dc_repo')
if os.path.exists(DC_REPO_PATH):
    sys.path.insert(0, DC_REPO_PATH)

try:
    from dynamic_cheatsheet.utils.extractor import extract_answer, extract_cheatsheet
    DC_UTILS_AVAILABLE = True
except ImportError:
    DC_UTILS_AVAILABLE = False
    print("Warning: DC utils not found. Please clone:")
    print("  git clone https://github.com/suzgunmirac/dynamic-cheatsheet.git dc_repo")


class DCWrapper:
    """
    Wrapper implementing Dynamic Cheatsheet test-time learning for DashScope/Qwen models
    
    Uses DC's concept but adapted for DashScope API via litellm.
    NOT using DSPy framework - this is a separate approach.
    """
    
    def __init__(self, model_name="qwen2.5-7b-instruct"):
        if not DC_UTILS_AVAILABLE:
            raise ImportError("Dynamic Cheatsheet utils not available. Clone the repository first.")
        
        # Configure DashScope API key
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("DASHSCOPE_API_KEY environment variable not set")
        
        dashscope.api_key = api_key
        
        # Use DashScope SDK directly
        self.model_name = model_name
        self.tokenizer = tiktoken.encoding_for_model('gpt-4o')
        
        print(f"✅ DC Wrapper initialized: {model_name}")
        print(f"   Using DashScope SDK directly")
    
    def generate(self, messages, temperature=0.1, max_tokens=2048):
        """
        Generate response using DashScope SDK
        
        Args:
            messages: List of message dicts [{"role": "user", "content": "..."}]
            temperature: Sampling temperature
            max_tokens: Max completion tokens
        
        Returns:
            str: Generated response
        """
        response = Generation.call(
            model=self.model_name,
            messages=messages,
            result_format='message',
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        if response.status_code == 200:
            return response.output.choices[0].message.content
        else:
            raise RuntimeError(f"DashScope API error: {response.code} - {response.message}")
    
    def generate_with_cheatsheet(self, question, context, answer_format, cheatsheet,
                                 generator_prompt_template, curator_prompt_template):
        """
        Generate answer using DC's test-time learning approach
        
        This implements the core DC algorithm:
        1. Generator: Use cheatsheet + context to answer question
        2. Curator: Extract insights from Q/A pair to update cheatsheet
        
        Args:
            question: ESG question
            context: Retrieved document context
            answer_format: Expected format (Int/Float/Str/List/null)
            cheatsheet: Current cheatsheet string
            generator_prompt_template: Template for generation
            curator_prompt_template: Template for curation
        
        Returns:
            dict with 'answer' and 'updated_cheatsheet'
        """
        # Step 1: Generator - Answer the question using cheatsheet
        generator_prompt = generator_prompt_template.format(
            context=context,
            cheatsheet=cheatsheet,
            question=question,
            answer_format=answer_format
        )
        
        generator_messages = [
            {"role": "user", "content": generator_prompt}
        ]
        
        answer = self.generate(generator_messages, temperature=0.1, max_tokens=512)
        answer = answer.strip()
        
        # Step 2: Curator - Update cheatsheet with insights from this Q/A
        # Truncate context for curator to avoid token limits
        context_excerpt = context[:500] + "..." if len(context) > 500 else context
        
        curator_prompt = curator_prompt_template.format(
            current_cheatsheet=cheatsheet,
            question=question,
            answer_format=answer_format,
            answer=answer,
            context=context_excerpt
        )
        
        curator_messages = [
            {"role": "user", "content": curator_prompt}
        ]
        
        updated_cheatsheet = self.generate(curator_messages, temperature=0.1, max_tokens=1024)
        updated_cheatsheet = updated_cheatsheet.strip()
        
        return {
            'answer': answer,
            'updated_cheatsheet': updated_cheatsheet
        }

