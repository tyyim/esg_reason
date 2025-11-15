#!/usr/bin/env python3
"""
Simple Single-Stage Baseline Implementation (No DSPy)
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
from openai import OpenAI
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dspy_implementation.dspy_dataset import MMESGBenchDataset
from dspy_implementation.dspy_postgres_retriever import DSPyPostgresRetriever
from dspy_implementation.baseline.baseline_prompts import GENERATOR_PROMPT
from src.evaluation_utils import eval_score


def create_simple_baseline_prompt(context, question, answer_format):
    """Create a simple 1-stage prompt for direct QA using GENERATOR_PROMPT"""
    return GENERATOR_PROMPT.format(
        context=context,
        question=question,
        answer_format=answer_format
    )


def evaluate_simple_baseline_raw(dataset_name='dev', model_name='deepseek-v3.1',max_questions=None):
    """Evaluate Simple Baseline (raw LLM calls, no DSPy) with DeepSeek on dev set"""
    
    print("="*70)
    print(f"Simple Baseline (RAW) Evaluation with {model_name}")
    print("="*70)
    
    # Load environment
    load_dotenv()
    api_key = os.getenv("DASHSCOPE_API_KEY")
    base_url = os.getenv("QWEN_API_BASE")
    
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY not found in environment. Please set it in your .env file.")
    
    # Use default DashScope URL if not provided
    if not base_url:
        base_url = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
        print(f"⚠️  DASHSCOPE_BASE_URL not set, using default: {base_url}")
    
    # Validate API key and base_url configuration
    print(f"   API Key: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else '***'}")
    print(f"   Base URL: {base_url}")
    
    # Initialize OpenAI client (compatible with DashScope)
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    
    print(f"\n Initialized with {model_name}")
    
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
    output_file = project_root / f"results/{model_name}_baseline/simple_baseline_{dataset_name}_{timestamp}.json"
    output_file.parent.mkdir(exist_ok=True)
    
    # Evaluate
    print(f"\n Running evaluation on {len(eval_set)} questions...")
    print(f"   Results will be saved every 5 questions to: {output_file}")
    
    correct = 0
    predictions = []
    format_breakdown = {}
    save_interval = 5  # Save every 5 questions
    
    def save_results():
        """Save current results to file"""
        accuracy = correct / len(predictions) if len(predictions) > 0 else 0.0
        results = {
            'model': model_name,
            'implementation': 'baseline_no_dspy',
            'dataset': dataset_name,
            'total': len(eval_set),
            'completed': len(predictions),
            'correct': correct,
            'accuracy': accuracy,
            'format_breakdown': format_breakdown,
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
            # Retrieve context
            context = retriever.retrieve(doc_id, question, top_k=5)
            
            # Create prompt
            prompt = create_simple_baseline_prompt(context, question, answer_format)
            
            # Call LLM directly (same as DC)
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            resp = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                resp_dict = json.loads(resp)
                final_answer = resp_dict.get('final_answer', '')
                analysis_text = resp_dict.get('reasoning', '')
            except json.JSONDecodeError:
                # Fallback if response is not valid JSON
                final_answer = resp
                analysis_text = ''
            
            # Evaluate
            # Normalize null/None/empty answers
            if (final_answer is None or 
                final_answer == '' or 
                str(final_answer).strip().lower() in ['none', 'null', 'n/a', 'na']):
                final_answer = "Not answerable"
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
                'score': answer_score
            })
            
        except Exception as e:
            print(f"\n⚠️  Error on question {i+1}: {e}")
            predictions.append({
                'question': question,
                'doc_id': doc_id,
                'context': context,
                'answer_format': answer_format,
                'ground_truth': gt,
                'predicted_answer': f'ERROR: {str(e)}',
                'analysis': f'ERROR: {str(e)}',
                'correct': False,
                'score': 0.0
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
    print("FINAL RESULTS - Simple Baseline")
    print("="*70)
    print(f"Accuracy: {accuracy:.1%} ({correct}/{len(eval_set)})")
    print("\nFormat Breakdown:")
    
    valid_formats = [k for k in format_breakdown.keys() if k is not None]
    for fmt in sorted(valid_formats):
        stats = format_breakdown[fmt]
        fmt_acc = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"  {fmt}: {fmt_acc:.1f}% ({stats['correct']}/{stats['total']})")
    
    print(f"\n Results saved to: {output_file}")
    
    # Build final results for return
    final_results = {
        'model': model_name,
        'implementation': 'baseline_no_dspy',
        'dataset': dataset_name,
        'total': len(eval_set),
        'correct': correct,
        'accuracy': accuracy,
        'format_breakdown': format_breakdown,
        'predictions': predictions,
        'timestamp': timestamp
    }
    
    return final_results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Evaluate Baseline Without DSPy...')
    parser.add_argument('--dataset', default='dev', choices=['dev', 'test'], help='Dataset to evaluate')
    parser.add_argument('--model', default='deepseek-v3.1', help='DeepSeek model name')
    parser.add_argument('--max-questions', type=int, default=None, help='Limit number of questions')
    
    args = parser.parse_args()
    
    evaluate_simple_baseline_raw(
        dataset_name=args.dataset,
        model_name=args.model,
        max_questions=args.max_questions
    )

