#!/usr/bin/env python3
"""
Simple Single-Stage Baseline Evaluation with DeepSeek v3
Evaluates on dev set (93 questions) for comparison with DC-CU
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import dspy

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dspy_implementation.dspy_dataset import MMESGBenchDataset
from dspy_implementation.dspy_postgres_retriever import DSPyPostgresRetriever
from src.evaluation_utils import eval_score

class SimpleDirectQA(dspy.Signature):
    """Answer ESG questions directly from context with proper formatting"""
    
    context = dspy.InputField(desc="Retrieved ESG report context")
    question = dspy.InputField(desc="ESG question to answer")
    answer_format = dspy.InputField(desc="Expected answer format: Int, Float, Str, List, or null")
    
    answer = dspy.OutputField(desc="""Final answer in the specified format. 
    - For Int: Return only the integer number (e.g., '5')
    - For Float: Return only the decimal number (e.g., '12.5')
    - For Str: Return only the text answer (e.g., 'Apple')
    - For List: Return comma-separated items (e.g., 'Apple, Google, Microsoft')
    - For null: Return 'null' or 'Not answerable' if information is not in context
    
    CRITICAL: Return ONLY the final answer in the specified format. No explanations, no reasoning, no extra text.""")


def setup_deepseek(model_name='deepseek-v3.1'):
    """Configure DSPy to use DeepSeek v3.1 via DashScope OpenAI-compatible endpoint"""
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY not found in environment")
    
    # Configure DSPy with DeepSeek via DashScope
    lm = dspy.LM(
        model=f'openai/{model_name}',
        api_key=api_key,
        api_base='https://dashscope.aliyuncs.com/compatible-mode/v1',
        temperature=0.0,
        max_tokens=1024
    )
    
    dspy.configure(lm=lm)
    
    print(f"✅ DSPy configured with DeepSeek")
    print(f"   Model: {model_name}")
    print(f"   Temperature: 0.0")
    print(f"   Max tokens: 1024")
    
    return lm


def evaluate_simple_baseline_deepseek(dataset_name='dev', model_name='deepseek-v3.1', max_questions=None):
    """Evaluate Simple Baseline with DeepSeek on dev set"""
    
    print("="*70)
    print("Simple Baseline Evaluation with DeepSeek v3")
    print("="*70)
    
    # Setup DeepSeek
    lm = setup_deepseek(model_name)
    
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
    
    # Initialize retriever and module
    print("\n🔧 Initializing retriever...")
    retriever = DSPyPostgresRetriever()
    
    print("\n🤖 Creating Simple QA module...")
    qa_module = dspy.Predict(SimpleDirectQA)
    
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
            retrieved = retriever.retrieve_contexts([doc_id], question, top_k=5)
            context = "\n\n".join(retrieved)
            
            # Get answer
            result = qa_module(
                context=context,
                question=question,
                answer_format=answer_format
            )
            
            pred = result.answer.strip()
            
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
    print("FINAL RESULTS - Simple Baseline (DeepSeek v3)")
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
    output_file = project_root / f"results/deepseek_comparison/simple_baseline_deepseek_{dataset_name}_{timestamp}.json"
    output_file.parent.mkdir(exist_ok=True)
    
    results = {
        'model': model_name,
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
    
    parser = argparse.ArgumentParser(description='Evaluate Simple Baseline with DeepSeek')
    parser.add_argument('--dataset', default='dev', choices=['dev', 'test'], help='Dataset to evaluate')
    parser.add_argument('--model', default='deepseek-v3.1', help='DeepSeek model name')
    parser.add_argument('--max-questions', type=int, default=None, help='Limit number of questions')
    
    args = parser.parse_args()
    
    evaluate_simple_baseline_deepseek(
        dataset_name=args.dataset,
        model_name=args.model,
        max_questions=args.max_questions
    )

