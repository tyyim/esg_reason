#!/usr/bin/env python3
"""
Dynamic Cheatsheet Evaluation for ESG Reasoning
Integrates DC's test-time learning with baseline's retrieval and evaluation
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
from openai import OpenAI
from dotenv import load_dotenv
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import tiktoken

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "dc_repo"))

from dspy_implementation.dspy_dataset import MMESGBenchDataset
from dspy_implementation.dspy_postgres_retriever import DSPyPostgresRetriever
from dspy_implementation.dc.prompt_manager import get_prompts
from dynamic_cheatsheet.utils.extractor import extract_answer, extract_cheatsheet
from dynamic_cheatsheet.utils.execute_code import extract_and_run_python_code
from dynamic_cheatsheet.language_model import LanguageModel
from src.evaluation_utils import eval_score
from langchain_community.embeddings import DashScopeEmbeddings


class DCLanguageModel(LanguageModel):
    """
    Dynamic Cheatsheet Language Model wrapper
    Extends LanguageModel to work with OpenAI client (used by baseline)
    """
    
    def __init__(self, client: OpenAI, model_name: str):
        # Initialize parent class with a valid model name (for compatibility)
        # We'll use our own OpenAI client instead of litellm
        # Pass a dummy model name that's in the supported list to avoid ValueError
        super().__init__(model_name="openai/gpt-4o")
        self.openai_client = client  # Store OpenAI client separately
        self.model_name = model_name  # Store actual model name for our use
        # Override parent's client to prevent it from being used
        self.client = None  # Parent's client won't be used
    
    def generate(
        self,
        messages: list = None,
        history: list = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        current_depth: int = 1,
        max_depth_num_rounds: int = 3,
        allow_code_execution: bool = True,
        code_execution_flag: str = "EXECUTE CODE!",
        final_output: str = ""
    ) -> str:
        """
        Generate response from language model with optional code execution
        Supports both 'messages' (OpenAI format) and 'history' (DC format) parameters
        
        Args:
            messages: List of message dicts with 'role' and 'content' (OpenAI format)
            history: List of message dicts (DC format, for compatibility)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            current_depth: Current depth of the conversation
            max_depth_num_rounds: Maximum number of rounds allowed
            allow_code_execution: Whether to execute Python code
            code_execution_flag: Flag to trigger code execution
            final_output: Final output to return (for recursive calls)
        
        Returns:
            Final output string
        """
        # Support both 'messages' and 'history' parameters for compatibility
        if messages is None:
            messages = history
        if messages is None or len(messages) == 0:
            raise ValueError("Messages must contain at least one message.")
        

        is_cheatsheet = max_tokens > 3000
        call_type = "CHEATSHEET" if is_cheatsheet else "GENERATOR"
        
        print(f"[{call_type}] max_tokens={max_tokens}", end=" ... ")
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            print("✓")
        except Exception as e:
            print(f"✗ {type(e).__name__}")
            raise
        
        output = response.choices[0].message.content.strip()
        
        # Handle code execution if enabled (with recursive logic like language_model.py)
        pre_code_execution_flag = output.split(code_execution_flag)[0].strip()
        if allow_code_execution and code_execution_flag in output and '```' == pre_code_execution_flag[-3:]:
            if code_execution_flag in output:
                output_prefix = output.split(code_execution_flag)[0].strip()
            else:
                output_prefix = output
            executed_code = extract_and_run_python_code(output_prefix)
            executed_code = executed_code.strip()
            current_output = f"{output_prefix}\n{code_execution_flag}\n\n{executed_code}"
            final_output = f"{final_output}\n\n{current_output}".strip()
            
            # If the current depth is less than or equal to the maximum depth, add a new message to the history
            if current_depth <= max_depth_num_rounds:
                warning_txt = ""
                if current_depth == max_depth_num_rounds:
                    warning_txt = f" (This is the last round. No more code execution will be allowed. Please present your final solution now.)"
                new_messages = [
                    {"role": "assistant", "content": current_output},
                    {"role": "user", "content": f"Proceed with any additional steps required and provide the completed solution. If everything is already complete, type FINAL ANSWER and submit it in the expected format. If you are stucked, please try alternative methods to solve the problem and provide the final solution.{warning_txt}"}
                ]
                messages += new_messages
                return self.generate(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    current_depth=current_depth+1,
                    max_depth_num_rounds=max_depth_num_rounds,
                    allow_code_execution=allow_code_execution,
                    code_execution_flag=code_execution_flag,
                    final_output=final_output,
                )
            else:
                final_output = f"{final_output}\n\n{current_output}".strip()
                return final_output
        else:
            # If code execution is not allowed or no code block is found, return the final output
            final_output = f"{final_output}\n\n{output}".strip()
            return final_output
    
    def _format_model_answer_for_original_curator(self, generator_output: str, extracted_answer: str) -> str:
        """
        Format generator output for original curator prompt.
        Since generator now returns JSON, we need to format it in a readable way.
        
        Args:
            generator_output: Raw generator output (JSON format)
            extracted_answer: Extracted final answer
        
        Returns:
            Formatted string for original curator
        """
        # Try to parse JSON and format nicely
        output_stripped = generator_output.strip()
        if output_stripped.startswith('{'):
            try:
                resp_dict = json.loads(output_stripped)
                reasoning = resp_dict.get('reasoning', '')
                final_answer = resp_dict.get('final_answer', extracted_answer)
                if (final_answer is None or final_answer == '' or str(final_answer).strip().lower() in ['none', 'null', 'n/a', 'na', 'str']):
                    final_answer = "Not answerable"
                # Format as readable text for original curator
                formatted = f"Reasoning:\n{reasoning}\n\nFinal Answer:\n{final_answer}"
                return formatted
            except json.JSONDecodeError:
                # If JSON parsing fails, try to find JSON in code blocks
                if '```json' in generator_output:
                    try:
                        json_start = generator_output.find('```json') + 7
                        json_end = generator_output.find('```', json_start)
                        json_str = generator_output[json_start:json_end].strip()
                        resp_dict = json.loads(json_str)
                        reasoning = resp_dict.get('reasoning', '')
                        final_answer = resp_dict.get('final_answer', extracted_answer)
                        if (final_answer is None or final_answer == '' or str(final_answer).strip().lower() in ['none', 'null', 'n/a', 'na', 'str']):
                            final_answer = "Not answerable"
                        formatted = f"Reasoning:\n{reasoning}\n\nFinal Answer:\n{final_answer}"
                        return formatted
                    except (json.JSONDecodeError, ValueError):
                        pass
        
        # Fallback: return original output if not JSON
        return generator_output
    
    def _extract_answer_from_output(self, output: str, prompt_type: str) -> str:
        """
        Extract answer from model output based on prompt type
        
        Args:
            output: Raw model output
            prompt_type: 'original' or 'custom'
        
        Returns:
            Extracted answer string
        """
        if prompt_type == 'custom':
            # Custom prompts return JSON format: {"reasoning": "...", "final_answer": "..."}
            # Try multiple strategies to extract JSON
            
            # Strategy 1: Try parsing the entire output as JSON
            output_stripped = output.strip()
            if output_stripped.startswith('{'):
                try:
                    resp_dict = json.loads(output_stripped)
                    final_answer = resp_dict.get('final_answer', '')
                    if (final_answer is None or final_answer == '' or str(final_answer).strip().lower() in ['none', 'null', 'n/a', 'na', 'str']):
                        final_answer = "Not answerable"
                    return final_answer
                except json.JSONDecodeError:
                    # Strategy 2: Try to fix common JSON issues (single quotes, etc.)
                    try:
                        # Replace single quotes around string values with double quotes
                        # This is a simple fix for cases like: "final_answer": 'value'
                        import re
                        # Pattern to match: "key": 'value' and replace with "key": "value"
                        fixed_output = re.sub(r'"(\w+)":\s*\'([^\']+)\'', r'"\1": "\2"', output_stripped)
                        # Also handle nested quotes: "key": '["item1", "item2"]'
                        fixed_output = re.sub(r'"(\w+)":\s*\'([^\']+)\'', r'"\1": "\2"', fixed_output)
                        resp_dict = json.loads(fixed_output)
                        final_answer = resp_dict.get('final_answer', '')
                        if (final_answer is None or final_answer == '' or str(final_answer).strip().lower() in ['none', 'null', 'n/a', 'na', 'str']):
                            final_answer = "Not answerable"
                        return final_answer
                    except (json.JSONDecodeError, ValueError):
                        pass
                    
                    # Strategy 3: Try to find JSON block in markdown code blocks
                    if '```json' in output:
                        try:
                            json_start = output.find('```json') + 7
                            json_end = output.find('```', json_start)
                            json_str = output[json_start:json_end].strip()
                            resp_dict = json.loads(json_str)
                            final_answer = resp_dict.get('final_answer', '')
                            if (final_answer is None or final_answer == '' or str(final_answer).strip().lower() in ['none', 'null', 'n/a', 'na', 'str']):
                                final_answer = "Not answerable"
                            return final_answer
                        except (json.JSONDecodeError, ValueError):
                            pass
                    
                    # Strategy 4: Use regex to extract final_answer value directly
                    import re
                    # Try to find "final_answer": 'value' or "final_answer": "value"
                    patterns = [
                        r'"final_answer"\s*:\s*\'([^\']+)\'',  # "final_answer": 'value'
                        r'"final_answer"\s*:\s*"([^"]+)"',    # "final_answer": "value"
                        r'"final_answer"\s*:\s*(\d+\.?\d*)',  # "final_answer": 123 or 123.45
                        r'"final_answer"\s*:\s*\[([^\]]+)\]', # "final_answer": [...]
                    ]
                    for pattern in patterns:
                        match = re.search(pattern, output)
                        if match:
                            answer = match.group(1)
                            if answer and answer.strip().lower() not in ['none', 'null', 'n/a', 'na', 'str']:
                                return answer.strip()
                    
                    # Strategy 5: Fall back to extract_answer
                    extracted = extract_answer(output)
                    if extracted != "No final answer found":
                        return extracted
                    
                    # Last resort: return "Not answerable"
                    return "Not answerable"
            else:
                # Not JSON format, try extract_answer
                return extract_answer(output)
        else:
            # Original prompts return <answer>...</answer> or FINAL ANSWER: ...
            return extract_answer(output)
    
    def advanced_generate(
        self,
        approach: str,
        input_txt: str,
        cheatsheet: str,
        generator_template: str,
        cheatsheet_template: str,
        context: str,
        question: str,
        answer_format: str,
        prompt_type: str = 'custom',  # 'original' or 'custom'
        temperature: float = 0.1,
        max_tokens: int = 2048,
        max_num_rounds: int = 1,
        allow_code_execution: bool = True,
        code_execution_flag: str = "EXECUTE CODE!",
        add_previous_answers_to_cheatsheet: bool = True,
        original_input_corpus: list = None,
        original_input_embeddings: np.ndarray = None,
        generator_outputs_so_far: list = None,
        retrieve_top_k: int = 3,
    ) -> dict:
        """
        Generate response using Dynamic Cheatsheet approach
        
        Args:
            approach: 'cumulative' or 'retrieval_synthesis'
            input_txt: Input text (question)
            cheatsheet: Current cheatsheet
            generator_template: Generator prompt template
            cheatsheet_template: Curator prompt template
            context: Retrieved context from document
            question: Question text
            answer_format: Expected answer format
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            max_num_rounds: Maximum number of rounds
            allow_code_execution: Whether to allow code execution
            code_execution_flag: Flag for code execution
            original_input_corpus: Previous questions for retrieval
            original_input_embeddings: Embeddings for retrieval
            generator_outputs_so_far: Previous generator outputs
            retrieve_top_k: Number of similar examples to retrieve
        
        Returns:
            dict with final_answer, final_output, final_cheatsheet, steps
        """
        
        if approach == 'cumulative':
            return self._cumulative_approach(
                input_txt, cheatsheet, generator_template, cheatsheet_template,
                context, question, answer_format, prompt_type, temperature, max_tokens,
                max_num_rounds, allow_code_execution, code_execution_flag,
                add_previous_answers_to_cheatsheet
            )
        elif approach == 'retrieval_synthesis':
            return self._retrieval_synthesis_approach(
                input_txt, cheatsheet, generator_template, cheatsheet_template,
                context, question, answer_format, prompt_type, temperature, max_tokens,
                allow_code_execution, code_execution_flag,
                original_input_corpus, original_input_embeddings,
                generator_outputs_so_far, retrieve_top_k
            )
        else:
            raise ValueError(f"Unknown approach: {approach}")
    
    def _cumulative_approach(
        self, input_txt, cheatsheet, generator_template, cheatsheet_template,
        context, question, answer_format, prompt_type, temperature, max_tokens,
        max_num_rounds, allow_code_execution, code_execution_flag,
        add_previous_answers_to_cheatsheet
    ):
        """Cumulative approach: update cheatsheet after each question"""
        steps = []
        previous_answers = []
        generator_output = ''
        
        for round in range(max(1, max_num_rounds)):
            ## STEP 1: Run the generator model with the input text and the cheatsheet
            generator_cheatsheet_content = cheatsheet

            # If there are previous answers, add them to the cheatsheet content for the generator
            if round > 0 and add_previous_answers_to_cheatsheet:
                previous_answers_txt = f"PREVIOUS ANSWERS:\n{'; '.join(previous_answers)}"
                generator_cheatsheet_content = f"{generator_cheatsheet_content}\n\n{previous_answers_txt}"

            # Format generator prompt (keep custom format for ESG)
            generator_prompt = generator_template.format(
                context=context,
                cheatsheet=generator_cheatsheet_content if generator_cheatsheet_content != "(empty)" else "No previous insights available.",
                question=question,
                answer_format=answer_format
            )
            current_cheatsheet = cheatsheet

            # Prepare the message history for the generator model
            generator_history = [{"role": "user", "content": generator_prompt}]
            # Run the generator model
            generator_output = self.generate(
                messages=generator_history,
                temperature=temperature,
                max_tokens=max_tokens,
                allow_code_execution=allow_code_execution,
                code_execution_flag=code_execution_flag,
            )
            # Extract the output from the generator model (keep custom extraction)
            generator_answer = self._extract_answer_from_output(generator_output, 'custom')

            ## STEP 2: Run the cheatsheet extraction model with the generator output and the current cheatsheet
            # Format curator prompt (handle both original and custom formats)
            if "[[PREVIOUS_CHEATSHEET]]" in cheatsheet_template and "[[QUESTION]]" in cheatsheet_template:
                # Original DC format curator
                model_answer_for_curator = self._format_model_answer_for_original_curator(generator_output, generator_answer)
                cheatsheet_prompt = cheatsheet_template.replace("[[QUESTION]]", input_txt).replace("[[MODEL_ANSWER]]", model_answer_for_curator).replace("[[PREVIOUS_CHEATSHEET]]", current_cheatsheet)
            else:
                # Custom ESG format curator
                cheatsheet_prompt = cheatsheet_template.format(
                    current_cheatsheet=current_cheatsheet if current_cheatsheet != "(empty)" else "No previous insights available.",
                    question=question,
                    answer_format=answer_format,
                    answer=generator_answer,
                    context=context
                )

            cheatsheet_history = [{"role": "user", "content": cheatsheet_prompt}]
            
            cheatsheet_output = self.generate(
                messages=cheatsheet_history,
                temperature=temperature,
                max_tokens=2*max_tokens,
                allow_code_execution=False,
            )

            # Extract the new cheatsheet from the output (if present); otherwise, return the old cheatsheet
            new_cheatsheet = extract_cheatsheet(response=cheatsheet_output, old_cheatsheet=current_cheatsheet)
            cheatsheet = new_cheatsheet

            previous_answers.append(f"Round {round+1}: {generator_answer}")
        
            steps.append({
                "round": round,
                "generator_prompt": generator_prompt,
                "generator_output": generator_output,
                "generator_answer": generator_answer,
                "current_cheatsheet": current_cheatsheet,
                "new_cheatsheet": new_cheatsheet,
            })
        
        return {
            "input_txt": input_txt,
            "steps": steps,
            "previous_answers": previous_answers,
            "final_answer": generator_answer,
            "final_cheatsheet": new_cheatsheet,
            "final_output": generator_output,
        }
    
    def _retrieval_synthesis_approach(
        self, input_txt, cheatsheet, generator_template, cheatsheet_template,
        context, question, answer_format, prompt_type, temperature, max_tokens,
        allow_code_execution, code_execution_flag,
        original_input_corpus, original_input_embeddings,
        generator_outputs_so_far, retrieve_top_k
    ):
        """Retrieval & Synthesis approach: retrieve similar examples and synthesize cheatsheet"""
        # Get the current original input embedding
        # Note: This matches run_benchmark.py logic where embeddings[:idx+1] includes current question
        if original_input_embeddings is None or len(original_input_embeddings) == 0:
            raise ValueError("original_input_embeddings is required for retrieval_synthesis approach but is None or empty. Please provide embeddings.")
        current_original_input_embedding = original_input_embeddings[-1]  # Current original input embedding
        prev_original_input_embeddings = original_input_embeddings[:-1]  # Note that this can be empty
        
        # Retrieve the most similar k input-output pairs from the previous inputs and outputs
        if len(prev_original_input_embeddings) > 0:
            similarities = cosine_similarity([current_original_input_embedding], prev_original_input_embeddings)
            top_k_indices = np.argsort(similarities[0])[::-1][:retrieve_top_k]
            top_k_original_inputs = [original_input_corpus[i] for i in top_k_indices]
            top_k_original_outputs = [generator_outputs_so_far[i] for i in top_k_indices]
            top_k_similar_values = similarities[0][top_k_indices]
            # Use the retrieved pairs to curate the cheatsheet for the generator model
            curated_cheatsheet = "### PREVIOUS SOLUTIONS (START)\n\nNote: The input-output pairs listed below are taken from previous test cases and are meant to assist you in understanding potential solution strategies or tool usages. While they can offer insight and inspiration, they should not be blindly copied, as they may contain errors or may not fit your specific use case. Approach them with a critical mindset—analyze their logic, verify their correctness, and adapt them as needed. Your goal should be to develop a well-reasoned solution that best addresses the problem at hand.\n\n"
        else:
            top_k_original_inputs = []
            top_k_original_outputs = []
            top_k_similar_values = []
            curated_cheatsheet = '(empty)'
        
        # The following only adds the previous input-output pairs to the cheatsheet
        for i, (previous_input_txt, previous_output_txt, similarity) in enumerate(zip(top_k_original_inputs[::-1], top_k_original_outputs[::-1], top_k_similar_values[::-1])):
            curated_cheatsheet += f"#### Previous Input #{i+1} (Similarity: {similarity:.2f}):\n\n{previous_input_txt}\n\n#### Model Solution to Previous Input  #{i+1}:\n\n{previous_output_txt}\n---\n---\n\n"
        curated_cheatsheet = curated_cheatsheet.strip()
        
        # If it is empty, we should not add the "PREVIOUS SOLUTIONS (END)" to the cheatsheet
        if curated_cheatsheet != '(empty)':
            curated_cheatsheet += "\n\n#### PREVIOUS SOLUTIONS (END)"
        
        # Run the Generator model with the input text and the curated cheatsheet (input-output pairs) to generate a better (more tailored) cheatsheet   
        previous_cheatsheet = cheatsheet
        if "[[PREVIOUS_INPUT_OUTPUT_PAIRS]]" in cheatsheet_template:
            # Original DC format curator
            # First, we need to make the necessary replacements in the cheatsheet template
            cheatsheet_prompt = cheatsheet_template.replace("[[PREVIOUS_INPUT_OUTPUT_PAIRS]]", curated_cheatsheet)
            cheatsheet_prompt = cheatsheet_prompt.replace("[[NEXT_INPUT]]", input_txt)
            cheatsheet_prompt = cheatsheet_prompt.replace("[[PREVIOUS_CHEATSHEET]]", previous_cheatsheet)
            # Now, we are ready to run the cheatsheet curator model
            cheatsheet_history = [{"role": "user", "content": cheatsheet_prompt}]
            cheatsheet_output = self.generate(
                messages=cheatsheet_history,
                temperature=temperature,
                max_tokens=2*max_tokens,
                allow_code_execution=False,
            )
            # Finally, extract the new cheatsheet from the output (if present); otherwise, return the old cheatsheet
            new_cheatsheet = extract_cheatsheet(response=cheatsheet_output, old_cheatsheet=curated_cheatsheet)
            curated_cheatsheet = new_cheatsheet
        else:
            # Custom ESG format curator
            cheatsheet_prompt = cheatsheet_template.format(
                previous_cheatsheet=previous_cheatsheet if previous_cheatsheet != "(empty)" else "No previous insights available.",
                retrieved_qa_pairs=curated_cheatsheet if curated_cheatsheet != "(empty)" else "No similar examples found.",
                next_input=input_txt
            )
            cheatsheet_history = [{"role": "user", "content": cheatsheet_prompt}]
            
            cheatsheet_output = self.generate(
                messages=cheatsheet_history,
                temperature=temperature,
                max_tokens=2*max_tokens,
                allow_code_execution=False,
            )
            new_cheatsheet = extract_cheatsheet(response=cheatsheet_output, old_cheatsheet=curated_cheatsheet)
            curated_cheatsheet = new_cheatsheet

        # Replace the relevant placeholders in the generator template with the input text and the curated cheatsheet and then run the generator model
        # Note: generator now always uses custom prompts (from dc_prompts.py), regardless of prompt_type
        generator_prompt = generator_template.format(
            context=context,
            cheatsheet=curated_cheatsheet if curated_cheatsheet != "(empty)" else "No previous insights available.",
            question=question,
            answer_format=answer_format
        )
        generator_history = [{"role": "user", "content": generator_prompt}]
        generator_output = self.generate(
                messages=generator_history,
                temperature=temperature,
                max_tokens=max_tokens,
                allow_code_execution=allow_code_execution,
                code_execution_flag=code_execution_flag,
            )
        # Extract the answer from the generator model (keep custom extraction)
        # Note: generator always returns JSON format (custom prompts), so always use 'custom' for extraction
        generator_answer = self._extract_answer_from_output(generator_output, 'custom')
        
        return {
            "input_txt": input_txt,
            "steps": [{
                "round": 0,
                "generator_prompt": generator_prompt,
                "generator_output": generator_output,
                "generator_answer": generator_answer,
                "current_cheatsheet": curated_cheatsheet,
                "new_cheatsheet": None,
            }],
            "top_k_original_inputs": top_k_original_inputs,
            "top_k_original_outputs": top_k_original_outputs,
            "final_answer": generator_answer,
            "final_output": generator_output,
            "final_cheatsheet": curated_cheatsheet,
        }


def evaluate_dc(
    dataset_name='dev',
    model_name='deepseek-v3.1',
    prompt_type='custom',  # 'original' or 'custom'
    approach='cumulative',  # 'cumulative' or 'retrieval_synthesis'
    max_questions=None,
    max_num_rounds=1,
    retrieve_top_k=3,
    allow_code_execution=True,
):
    """
    Evaluate Dynamic Cheatsheet approach on ESG dataset
    
    Args:
        dataset_name: 'dev' or 'test'
        model_name: Model name for OpenAI client
        prompt_type: 'original' (DC prompts) or 'custom' (ESG prompts)
        approach: 'cumulative' or 'retrieval_synthesis'
        max_questions: Limit number of questions (None for all)
        max_num_rounds: Maximum rounds for cumulative approach
        retrieve_top_k: Number of similar examples to retrieve
        allow_code_execution: Whether to allow Python code execution
    """
    
    print("="*70)
    print(f"Dynamic Cheatsheet Evaluation")
    print(f"  Model: {model_name}")
    print(f"  Prompt Type: {prompt_type}")
    print(f"  Approach: {approach}")
    print("="*70)
    
    # Load environment
    load_dotenv()
    api_key = os.getenv("API_KEY")
    base_url = os.getenv("API_BASE")
    
    if not api_key:
        raise ValueError("API_KEY not found in environment. Please set it in your .env file.")
    
    if not base_url:
        base_url = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
        print(f"⚠️  BASE_URL not set, using default: {base_url}")
    
    print(f"   API Key: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else '***'}")
    print(f"   Base URL: {base_url}")
    
    # Initialize OpenAI client
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=120.0
    )
    
    # Initialize DC Language Model
    dc_model = DCLanguageModel(client, model_name)
    
    # Load prompts
    prompts = get_prompts(prompt_type=prompt_type, approach=approach)
    generator_template = prompts['generator']
    cheatsheet_template = prompts['curator']
    
    # Load dataset
    print(f"\n Loading {dataset_name} set...")
    dataset = MMESGBenchDataset()
    
    if dataset_name == 'dev':
        eval_set = dataset.dev_set
    elif dataset_name == 'test':
        eval_set = dataset.test_set
    else:
        raise ValueError(f"Unknown dataset: {dataset_name}")
    
    if max_questions:
        eval_set = eval_set[:max_questions]
    
    print(f"   Total questions: {len(eval_set)}")
    
    # Initialize retriever
    print("\n  Initializing retriever...")
    retriever = DSPyPostgresRetriever()
    
    # Prepare output file path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = project_root / f"results/{model_name}_dc/{prompt_type}_{approach}_{dataset_name}_{timestamp}.json"
    output_file.parent.mkdir(exist_ok=True)
    
    # Initialize cheatsheet
    cheatsheet = "(empty)"
    
    # For retrieval_synthesis: prepare embeddings and corpus
    original_input_corpus = []
    original_input_embeddings = []
    generator_outputs_so_far = []
    embedding_model = None
    
    if approach == 'retrieval_synthesis':
        # Initialize embedding model (same as dc_evaluator_v2.py)
        print("  Initializing embedding model for retrieval synthesis...")
        embedding_model = DashScopeEmbeddings(
            model="text-embedding-v4",
            dashscope_api_key=api_key
        )
        print("  ✓ Embedding model ready")
    
    # Evaluate
    print(f"\n Running evaluation on {len(eval_set)} questions...")
    print(f"   Results will be saved every 5 questions to: {output_file}")
    
    correct = 0
    predictions = []
    format_breakdown = {}
    save_interval = 5
    
    def save_results():
        """Save current results to file"""
        accuracy = correct / len(predictions) if len(predictions) > 0 else 0.0
        results = {
            'model': model_name,
            'implementation': 'dynamic_cheatsheet',
            'prompt_type': prompt_type,
            'approach': approach,
            'dataset': dataset_name,
            'total': len(eval_set),
            'completed': len(predictions),
            'correct': correct,
            'accuracy': accuracy,
            'format_breakdown': format_breakdown,
            'final_cheatsheet': cheatsheet,  # Final cheatsheet state after all processed questions
            'predictions': predictions,
            'timestamp': timestamp
        }
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    
    for i, item in enumerate(tqdm(eval_set, desc="Evaluating")):
        question = item['question']
        doc_id = item['doc_id']
        answer_format = item['answer_format']
        gt = item['answer']
        
        # Track format
        if answer_format not in format_breakdown:
            format_breakdown[answer_format] = {'correct': 0, 'total': 0}
        format_breakdown[answer_format]['total'] += 1
        
        try:
            print(f"\n[Q{i+1}] ", end="")
            
            dc_model._current_question_index = i
            
            # Retrieve context (baseline way)
            context = retriever.retrieve(doc_id, question, top_k=5)
            
            # Prepare input text
            input_txt = f"Question #{i+1}:\n{question}"
            
            # For retrieval_synthesis: generate embedding and add to corpus BEFORE calling advanced_generate
            # This matches run_benchmark.py logic where questions[:idx+1] includes current question
            # and dc_evaluator_v2.py lines 175-178
            if approach == 'retrieval_synthesis':
                current_embedding = embedding_model.embed_query(question)
                original_input_embeddings.append(current_embedding)
                original_input_corpus.append(input_txt)
            
            # Generate using DC approach
            output_dict = dc_model.advanced_generate(
                approach=approach,
                input_txt=input_txt,
                cheatsheet=cheatsheet,
                generator_template=generator_template,
                cheatsheet_template=cheatsheet_template,
                context=context,
                question=question,
                answer_format=answer_format,
                prompt_type=prompt_type,
                temperature=0.1,
                max_tokens=2048,
                max_num_rounds=max_num_rounds,
                allow_code_execution=allow_code_execution,
                code_execution_flag="EXECUTE CODE!",
                original_input_corpus=original_input_corpus if approach == 'retrieval_synthesis' else None,
                original_input_embeddings=np.array(original_input_embeddings) if approach == 'retrieval_synthesis' and len(original_input_embeddings) > 0 else None,
                generator_outputs_so_far=generator_outputs_so_far if approach == 'retrieval_synthesis' else None,
                retrieve_top_k=retrieve_top_k,
            )
            
            # Save cheatsheet before update (for tracking how cheatsheet affects the answer)
            cheatsheet_before = cheatsheet
            
            # Update cheatsheet for next question
            cheatsheet_after = output_dict['final_cheatsheet']
            cheatsheet = cheatsheet_after
            
            # Extract final answer (already extracted in advanced_generate based on prompt_type)
            final_answer = output_dict['final_answer']
            raw_output = output_dict.get('final_output', '')
            
            # For retrieval_synthesis: update generator_outputs_so_far AFTER getting result
            # This matches run_benchmark.py line 247 and dc_evaluator_v2.py line 214
            if approach == 'retrieval_synthesis':
                generator_outputs_so_far.append(raw_output)
            
            # Extract analysis/reasoning text based on prompt type
            if prompt_type == 'custom':
                # Custom prompts return JSON with reasoning field
                raw_stripped = raw_output.strip()
                if raw_stripped.startswith('{'):
                    try:
                        resp_dict = json.loads(raw_stripped)
                        analysis_text = resp_dict.get('reasoning', '')
                    except json.JSONDecodeError:
                        # Try to find JSON in code blocks
                        if '```json' in raw_output:
                            try:
                                json_start = raw_output.find('```json') + 7
                                json_end = raw_output.find('```', json_start)
                                json_str = raw_output[json_start:json_end].strip()
                                resp_dict = json.loads(json_str)
                                analysis_text = resp_dict.get('reasoning', '')
                            except (json.JSONDecodeError, ValueError):
                                analysis_text = raw_output
                        else:
                            analysis_text = raw_output
                else:
                    analysis_text = raw_output
            else:
                # Original prompts: use full output as analysis
                analysis_text = raw_output
            
            # Normalize null/None/empty answers
            if (final_answer is None or 
                final_answer == '' or 
                str(final_answer).strip().lower() in ['none', 'null', 'n/a', 'na', 'str']):
                final_answer = "Not answerable"
            
            # Evaluate (baseline way)
            answer_score = eval_score(gt, final_answer, answer_format)
            is_correct = (answer_score >= 0.5)
            
            if is_correct:
                correct += 1
                format_breakdown[answer_format]['correct'] += 1
            
            predictions.append({
                'question': question,
                'doc_id': doc_id,
                'answer_format': answer_format,
                'context': context,
                'ground_truth': gt,
                'predicted_answer': final_answer,
                'analysis': analysis_text,
                'correct': is_correct,
                'score': answer_score,
                'cheatsheet_before': cheatsheet_before,  # Cheatsheet before processing this question
                'cheatsheet_after': cheatsheet_after,    # Cheatsheet after processing this question
            })
            
        except Exception as e:
            print(f"\n⚠️  Q{i+1} 失败: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # For retrieval_synthesis: remove the embedding/corpus we added if there was an error
            # This matches dc_evaluator_v2.py lines 235-237
            if approach == 'retrieval_synthesis' and len(original_input_embeddings) > len(generator_outputs_so_far):
                original_input_embeddings.pop()
                original_input_corpus.pop()
            
            predictions.append({
                'question': question,
                'doc_id': doc_id,
                'context': context if 'context' in locals() else '',
                'answer_format': answer_format,
                'ground_truth': gt,
                'predicted_answer': f'ERROR: {str(e)}',
                'analysis': f'ERROR: {str(e)}',
                'correct': False,
                'score': 0.0,
                'cheatsheet_before': cheatsheet if 'cheatsheet' in locals() else '(empty)',
                'cheatsheet_after': cheatsheet if 'cheatsheet' in locals() else '(empty)',
            })
        
        # Save every 5 questions
        if (i + 1) % save_interval == 0:
            save_results()
            current_acc = correct / len(predictions) if len(predictions) > 0 else 0.0
            print(f"\n   [Progress] Saved results after {i + 1} questions (Accuracy: {current_acc:.1%})")
    
    # Final save
    save_results()
    
    # Calculate accuracy
    accuracy = correct / len(eval_set)
    
    # Print results
    print("\n" + "="*70)
    print("FINAL RESULTS - Dynamic Cheatsheet")
    print("="*70)
    print(f"Accuracy: {accuracy:.1%} ({correct}/{len(eval_set)})")
    print("\nFormat Breakdown:")
    
    valid_formats = [k for k in format_breakdown.keys() if k is not None]
    for fmt in sorted(valid_formats):
        stats = format_breakdown[fmt]
        fmt_acc = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"  {fmt}: {fmt_acc:.1f}% ({stats['correct']}/{stats['total']})")
    
    print(f"\n Results saved to: {output_file}")
    
    return {
        'model': model_name,
        'implementation': 'dynamic_cheatsheet',
        'prompt_type': prompt_type,
        'approach': approach,
        'dataset': dataset_name,
        'total': len(eval_set),
        'correct': correct,
        'accuracy': accuracy,
        'format_breakdown': format_breakdown,
        'predictions': predictions,
        'timestamp': timestamp
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Evaluate Dynamic Cheatsheet on ESG dataset')
    parser.add_argument('--dataset', default='dev', choices=['dev', 'test'], help='Dataset to evaluate')
    parser.add_argument('--model', default='deepseek-v3.1', help='Model name')
    parser.add_argument('--prompt-type', default='custom', choices=['original', 'custom'], 
                       help='Prompt type: original (DC prompts) or custom (ESG prompts)')
    parser.add_argument('--approach', default='cumulative', choices=['cumulative', 'retrieval_synthesis'],
                       help='DC approach: cumulative or retrieval_synthesis')
    parser.add_argument('--max-questions', type=int, default=None, help='Limit number of questions')
    parser.add_argument('--max-rounds', type=int, default=1, help='Max rounds for cumulative approach')
    parser.add_argument('--retrieve-top-k', type=int, default=3, help='Top k for retrieval synthesis')
    parser.add_argument('--no-code-execution', action='store_false', dest='code_execution',
                       default=True, help='Disable code execution (enabled by default)')
    
    args = parser.parse_args()
    
    evaluate_dc(
        dataset_name=args.dataset,
        model_name=args.model,
        prompt_type=args.prompt_type,
        approach=args.approach,
        max_questions=args.max_questions,
        max_num_rounds=args.max_rounds,
        retrieve_top_k=args.retrieve_top_k,
        allow_code_execution=args.code_execution,
    )

