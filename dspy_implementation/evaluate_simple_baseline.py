#!/usr/bin/env python3
"""
Simple Single-Stage Baseline for Fair Comparison with DC

This baseline uses:
- Same retrieval as other approaches (top-5 chunks)
- Single-stage direct question answering (like DC)
- NO multi-stage reasoning/extraction (unlike DSPy baseline)

Purpose: Fair comparison with Dynamic Cheatsheet's single-stage generation
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import dspy
from dspy_implementation.dspy_postgres_retriever import DSPyPostgresRetriever
from dspy_implementation.dspy_dataset import MMESGBenchDataset
from src.evaluation import eval_score
from collections import defaultdict


class SimpleDirectQA(dspy.Signature):
    """Answer ESG questions from retrieved document context in the exact specified format.
    
    Instructions:
    - Read the question and context carefully
    - Extract the answer in the EXACT format specified
    - Return ONLY the final answer, NO explanations or reasoning
    - For Int: Return only the integer (e.g., "42")
    - For Float: Return only the number (e.g., "3.14" or "10.5")
    - For Str: Return only the exact text string (e.g., "Scope 1 emissions")
    - For List: Return valid JSON array (e.g., ["item1", "item2"])
    - For None/unanswerable: Return exactly "Not answerable"
    """
    question: str = dspy.InputField(desc="The ESG question to answer")
    context: str = dspy.InputField(desc="Retrieved document context from ESG reports")
    answer_format: str = dspy.InputField(desc="Required answer format: Int, Float, Str, List, or None")
    answer: str = dspy.OutputField(desc="ONLY the final answer in the specified format, NO explanations")


class SimpleBaselineRAG(dspy.Module):
    """
    Simple single-stage RAG baseline for fair comparison with DC.
    
    Architecture:
    1. Retrieve context (top-5 chunks)
    2. Direct answer generation (single LLM call)
    
    No separate reasoning/extraction stages.
    """
    
    def __init__(self):
        super().__init__()
        self.retriever = DSPyPostgresRetriever()
        self.qa = dspy.Predict(SimpleDirectQA)
    
    def forward(self, question: str, doc_id: str, answer_format: str):
        """Single-stage forward pass"""
        # Retrieve context
        context = self.retriever.retrieve(doc_id, question, top_k=5)
        
        # Direct answer generation (single stage)
        result = self.qa(
            question=question,
            context=context,
            answer_format=answer_format
        )
        
        return dspy.Prediction(answer=result.answer, context=context)


def evaluate_simple_baseline(dataset_name="dev", model_name="qwen2.5-7b-instruct", 
                              max_questions=None, output_file=None):
    """
    Evaluate simple single-stage baseline.
    
    Args:
        dataset_name: 'dev' or 'test'
        model_name: Model to use (default: qwen2.5-7b-instruct)
        max_questions: Limit number of questions (for testing)
        output_file: Path to save results
    """
    
    print(f"\n{'='*60}")
    print(f"Simple Single-Stage Baseline Evaluation")
    print(f"{'='*60}")
    print(f"Dataset: {dataset_name}")
    print(f"Model: {model_name}")
    print(f"Architecture: Single-stage (like DC)")
    print(f"{'='*60}\n")
    
    # Initialize DSPy with DashScope (OpenAI-compatible)
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY environment variable not set")
    
    lm = dspy.LM(
        model=f'openai/{model_name}',
        api_key=api_key,
        api_base='https://dashscope.aliyuncs.com/compatible-mode/v1',
        temperature=0.1,
        max_tokens=512
    )
    
    dspy.configure(lm=lm)
    
    # Load dataset
    dataset = MMESGBenchDataset()
    if dataset_name == "dev":
        data = dataset.dev_set
    elif dataset_name == "test":
        data = dataset.test_set
    else:
        raise ValueError(f"Unknown dataset: {dataset_name}")
    
    if max_questions:
        data = data[:max_questions]
        print(f"⚠️  Limited to {max_questions} questions for testing\n")
    
    print(f"📊 Evaluating {len(data)} questions...\n")
    
    # Initialize model
    model = SimpleBaselineRAG()
    
    # Evaluate
    predictions = {}
    correct = 0
    format_breakdown = defaultdict(lambda: {'correct': 0, 'total': 0})
    
    for i, example in enumerate(tqdm(data, desc="Evaluating")):
        q_id = f"q{i}"
        
        try:
            # Get prediction
            pred = model(
                question=example.question,
                doc_id=example.doc_id,
                answer_format=example.answer_format
            )
            
            answer = pred.answer
            
            # Evaluate
            score = eval_score(example.answer, answer, example.answer_format)
            is_correct = (score >= 0.5)
            
            if is_correct:
                correct += 1
            
            # Store prediction
            predictions[q_id] = {
                'question': example.question,
                'ground_truth': example.answer,
                'answer': answer,
                'answer_format': example.answer_format,
                'doc_id': example.doc_id,
                'context': pred.context,
                'score': score,
                'correct': is_correct
            }
            
            # Update format breakdown
            format_breakdown[example.answer_format]['correct'] += (1 if is_correct else 0)
            format_breakdown[example.answer_format]['total'] += 1
            
        except Exception as e:
            print(f"\n⚠️  Error on question {i}: {e}")
            predictions[q_id] = {
                'question': example.question,
                'ground_truth': example.answer,
                'answer': f"ERROR: {str(e)}",
                'answer_format': example.answer_format,
                'doc_id': example.doc_id,
                'context': "",
                'score': 0.0,
                'correct': False
            }
            format_breakdown[example.answer_format]['total'] += 1
    
    # Compute metrics
    total = len(data)
    accuracy = correct / total if total > 0 else 0
    
    # Print results
    print(f"\n{'='*60}")
    print(f"Results - Simple Single-Stage Baseline")
    print(f"{'='*60}")
    print(f"Overall Accuracy: {accuracy:.1%} ({correct}/{total})")
    print(f"\n{'='*60}")
    print(f"Format-Specific Breakdown:")
    print(f"{'='*60}")
    
    for fmt in sorted(format_breakdown.keys()):
        stats = format_breakdown[fmt]
        fmt_acc = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
        print(f"{fmt:8s}: {fmt_acc:6.1%} ({stats['correct']:3d}/{stats['total']:3d})")
    
    # Save results
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = project_root / "results" / f"{dataset_name}_set"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"simple_baseline_{dataset_name}_predictions_{timestamp}.json"
    
    results = {
        'model': model_name,
        'dataset': dataset_name,
        'architecture': 'single_stage_direct_qa',
        'timestamp': datetime.now().isoformat(),
        'accuracy': accuracy,
        'overall_accuracy': accuracy,
        'correct': correct,
        'total': total,
        'format_breakdown': {k: dict(v) for k, v in format_breakdown.items()},
        'predictions': predictions
    }
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Results saved to: {output_file}")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate simple single-stage baseline (fair comparison with DC)"
    )
    parser.add_argument(
        '--dataset',
        type=str,
        default='dev',
        choices=['dev', 'test'],
        help='Dataset to evaluate (dev or test)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='qwen2.5-7b-instruct',
        help='Model name (default: qwen2.5-7b-instruct)'
    )
    parser.add_argument(
        '--max-questions',
        type=int,
        default=None,
        help='Maximum number of questions to evaluate (for testing)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output file path (default: auto-generated)'
    )
    
    args = parser.parse_args()
    
    evaluate_simple_baseline(
        dataset_name=args.dataset,
        model_name=args.model,
        max_questions=args.max_questions,
        output_file=args.output
    )


if __name__ == "__main__":
    main()

