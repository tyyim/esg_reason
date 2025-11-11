#!/usr/bin/env python3
"""
DC-CU (Cumulative) Evaluation with DeepSeek v3
Evaluates on dev set (93 questions) for comparison with Simple Baseline
Uses original DC repository's implementation
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# Add paths
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'dc_repo'))

from dspy_implementation.dspy_dataset import MMESGBenchDataset
from dspy_implementation.dspy_postgres_retriever import DSPyPostgresRetriever
from src.evaluation_utils import eval_score
from dynamic_cheatsheet.language_model import LanguageModel


class DCEvaluatorDeepSeek:
    """DC-CU evaluator using DeepSeek v3.1 via DashScope"""
    
    def __init__(self, model_name='deepseek-v3.1'):
        """Initialize with DeepSeek model"""
        from dotenv import load_dotenv
        load_dotenv(project_root / ".env")
        
        # Verify API key
        if not os.getenv("DASHSCOPE_API_KEY"):
            raise ValueError("DASHSCOPE_API_KEY not found in environment")
        
        # Initialize DC language model with DeepSeek
        # Note: We need to use the dashscope/ prefix for DashScope models
        self.model_name = model_name
        self.lm = LanguageModel(f"dashscope/{model_name}")
        self.retriever = DSPyPostgresRetriever()
        
        print(f"✅ DC-CU initialized with DeepSeek")
        print(f"   Model: {model_name}")
        
    def load_prompts(self):
        """Load DC-CU prompts from original repository"""
        prompts_dir = project_root / 'dc_repo' / 'prompts'
        
        with open(prompts_dir / 'generator_prompt.txt', 'r') as f:
            generator_template = f.read()
        
        with open(prompts_dir / 'curator_prompt_for_dc_cumulative.txt', 'r') as f:
            curator_template = f.read()
        
        return generator_template, curator_template
    
    def format_input(self, question, context, answer_format):
        """Format input for DC"""
        return f"""Question: {question}

Context from ESG Report:
{context}

Expected Answer Format: {answer_format}

Instructions:
- For Int: Return only the integer number
- For Float: Return only the decimal number
- For Str: Return only the text answer
- For List: Return comma-separated items
- For null: Return 'null' if information not in context"""
    
    def evaluate(self, dataset_name='dev', max_questions=None):
        """Evaluate DC-CU on dataset"""
        
        print("="*70)
        print("DC-CU Evaluation with DeepSeek v3")
        print("="*70)
        
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
        
        # Load prompts
        print("\n📝 Loading DC prompts...")
        generator_template, curator_template = self.load_prompts()
        
        # Initialize cheatsheet
        cheatsheet = ""
        
        # Evaluate
        print(f"\n🧪 Running DC-CU evaluation...")
        
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
                context = self.retriever.retrieve(doc_id, question, top_k=5)
                
                # Format input
                input_txt = self.format_input(question, context, answer_format)
                
                # Call DC-CU
                result = self.lm.advanced_generate(
                    approach_name="DynamicCheatsheet_Cumulative",
                    input_txt=input_txt,
                    cheatsheet=cheatsheet,
                    generator_template=generator_template,
                    cheatsheet_template=curator_template,
                    temperature=0.1,
                    max_tokens=512,
                    allow_code_execution=False
                )
                
                # Extract results
                pred = result['final_answer']
                cheatsheet = result['final_cheatsheet']
                
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
        print("FINAL RESULTS - DC-CU (DeepSeek v3)")
        print("="*70)
        print(f"Accuracy: {accuracy:.1%} ({correct}/{len(eval_set)})")
        print(f"Final Cheatsheet Length: {len(cheatsheet)} characters")
        print("\nFormat Breakdown:")
        
        valid_formats = [k for k in format_breakdown.keys() if k is not None]
        for fmt in sorted(valid_formats):
            stats = format_breakdown[fmt]
            fmt_acc = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"  {fmt}: {fmt_acc:.1f}% ({stats['correct']}/{stats['total']})")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = project_root / f"results/deepseek_comparison/dc_cu_deepseek_{dataset_name}_{timestamp}.json"
        output_file.parent.mkdir(exist_ok=True)
        
        results = {
            'model': f'dashscope/{self.model_name}',
            'dataset': dataset_name,
            'variant': 'cumulative',
            'total': len(eval_set),
            'correct': correct,
            'accuracy': accuracy,
            'format_breakdown': format_breakdown,
            'final_cheatsheet': cheatsheet,
            'predictions': predictions,
            'timestamp': timestamp
        }
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {output_file}")
        
        return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Evaluate DC-CU with DeepSeek')
    parser.add_argument('--dataset', default='dev', choices=['dev', 'test'], help='Dataset to evaluate')
    parser.add_argument('--model', default='deepseek-v3.1', help='DeepSeek model name')
    parser.add_argument('--max-questions', type=int, default=None, help='Limit number of questions')
    
    args = parser.parse_args()
    
    evaluator = DCEvaluatorDeepSeek(model_name=args.model)
    evaluator.evaluate(
        dataset_name=args.dataset,
        max_questions=args.max_questions
    )

