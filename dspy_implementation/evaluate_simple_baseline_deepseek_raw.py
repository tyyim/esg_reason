#!/usr/bin/env python3
"""
Simple Single-Stage Baseline with DeepSeek v3 - RAW Implementation (No DSPy)
Fair comparison with DC-CU - both use direct LLM calls without framework overhead
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
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dspy_implementation.dspy_dataset import MMESGBenchDataset
from dspy_implementation.dspy_postgres_retriever import DSPyPostgresRetriever
from src.evaluation_utils import eval_score


def create_simple_baseline_prompt(context, question, answer_format):
    """Create a simple 1-stage prompt for direct QA"""
    return f"""You are an ESG (Environmental, Social, Governance) analyst. Answer the following question based ONLY on the provided context from an ESG report.

Context from ESG Report:
{context}

Question: {question}

Expected Answer Format: {answer_format}

Instructions:
- For Int: Return only the integer number (e.g., '5')
- For Float: Return only the decimal number (e.g., '12.5')
- For Str: Return only the text answer (e.g., 'Apple')
- For List: Return comma-separated items (e.g., 'Apple, Google, Microsoft')
- For null: Return 'null' or 'Not answerable' if the information is not available in the context

CRITICAL: Return ONLY the final answer in the specified format. No explanations, no reasoning, no extra text.

Answer:"""


def evaluate_simple_baseline_raw(dataset_name='dev', model_name='deepseek-v3.1', max_questions=None):
    """Evaluate Simple Baseline (raw LLM calls, no DSPy) with DeepSeek on dev set"""
    
    print("="*70)
    print("Simple Baseline (RAW) Evaluation with DeepSeek v3")
    print("="*70)
    print("No DSPy framework - Direct LLM calls only")
    print("Fair comparison with DC-CU")
    print("="*70)
    
    # Load environment
    load_dotenv()
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY not found in environment")
    
    # Initialize OpenAI client (same as DC uses)
    client = OpenAI(
        api_key=api_key,
        base_url='https://dashscope.aliyuncs.com/compatible-mode/v1'
    )
    
    print(f"\n✅ Initialized with DeepSeek v3.1")
    print(f"   Model: {model_name}")
    print(f"   API: Direct OpenAI-compatible calls (no DSPy)")
    
    # Load dataset
    print(f"\n📊 Loading {dataset_name} set...")
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
    print("\n🔧 Initializing retriever...")
    retriever = DSPyPostgresRetriever()
    
    # Evaluate
    print(f"\n🧪 Running evaluation on {len(eval_set)} questions...")
    
    correct = 0
    predictions = []
    format_breakdown = {}
    
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
                temperature=0.0,
                max_tokens=512
            )
            
            pred = response.choices[0].message.content.strip()
            
            # Evaluate
            answer_score = eval_score(gt, pred, answer_format)
            is_correct = (answer_score >= 0.5)
            
            if is_correct:
                correct += 1
                format_breakdown[answer_format]['correct'] += 1
            
            predictions.append({
                'question': question,
                'doc_id': doc_id,
                'answer_format': answer_format,
                'ground_truth': gt,
                'predicted': pred,
                'correct': is_correct,
                'score': answer_score
            })
            
        except Exception as e:
            print(f"\n⚠️  Error on question {i+1}: {e}")
            predictions.append({
                'question': question,
                'doc_id': doc_id,
                'answer_format': answer_format,
                'ground_truth': gt,
                'predicted': f'ERROR: {str(e)}',
                'correct': False,
                'score': 0.0
            })
    
    # Calculate accuracy
    accuracy = correct / len(eval_set)
    
    # Print results
    print("\n" + "="*70)
    print("FINAL RESULTS - Simple Baseline RAW (DeepSeek v3)")
    print("="*70)
    print(f"Accuracy: {accuracy:.1%} ({correct}/{len(eval_set)})")
    print("\nFormat Breakdown:")
    
    valid_formats = [k for k in format_breakdown.keys() if k is not None]
    for fmt in sorted(valid_formats):
        stats = format_breakdown[fmt]
        fmt_acc = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"  {fmt}: {fmt_acc:.1f}% ({stats['correct']}/{stats['total']})")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = project_root / f"results/deepseek_comparison/simple_baseline_raw_deepseek_{dataset_name}_{timestamp}.json"
    output_file.parent.mkdir(exist_ok=True)
    
    results = {
        'model': model_name,
        'implementation': 'raw_llm_calls_no_dspy',
        'dataset': dataset_name,
        'total': len(eval_set),
        'correct': correct,
        'accuracy': accuracy,
        'format_breakdown': format_breakdown,
        'predictions': predictions,
        'timestamp': timestamp
    }
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Evaluate Simple Baseline (RAW) with DeepSeek')
    parser.add_argument('--dataset', default='dev', choices=['dev', 'test'], help='Dataset to evaluate')
    parser.add_argument('--model', default='deepseek-v3.1', help='DeepSeek model name')
    parser.add_argument('--max-questions', type=int, default=None, help='Limit number of questions')
    
    args = parser.parse_args()
    
    evaluate_simple_baseline_raw(
        dataset_name=args.dataset,
        model_name=args.model,
        max_questions=args.max_questions
    )

