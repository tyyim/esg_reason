#!/usr/bin/env python3
"""
Dynamic Cheatsheet Evaluator for MMESGBench
Follows project best practices: checkpointing, logging, retry logic
"""
import json
import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dspy_implementation.dc_module.dc_rag_module import DCRAGModule
from dspy_implementation.dspy_dataset import MMESGBenchDataset
from dspy_implementation.dspy_setup import setup_dspy_qwen
from MMESGBench.src.eval.eval_score import eval_score


class DCEvaluator:
    """
    Evaluator for Dynamic Cheatsheet on MMESGBench
    
    Features (following project best practices):
    - Checkpoint/resume mechanism
    - Structured logging (file + console)
    - Retry logic with exponential backoff
    - Progress bars (tqdm)
    - MMESGBench's exact eval_score()
    """
    
    def __init__(self, output_dir="results/dc_experiments"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.setup_logging()
    
    def setup_logging(self):
        """Setup structured logging"""
        log_dir = Path("logs/dc_evaluation")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"dc_eval_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"DC Evaluator initialized. Logs: {log_file}")
    
    def load_checkpoint(self, checkpoint_file):
        """Load checkpoint if exists"""
        if os.path.exists(checkpoint_file):
            self.logger.info(f"📂 Loading checkpoint: {checkpoint_file}")
            with open(checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
            return checkpoint
        return None
    
    def save_checkpoint(self, checkpoint_file, predictions, cheatsheet, metadata):
        """Save checkpoint"""
        checkpoint = {
            'predictions': predictions,
            'cheatsheet': cheatsheet,
            'metadata': metadata,
            'timestamp': datetime.now().isoformat()
        }
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        self.logger.info(f"💾 Checkpoint saved: {len(predictions)} predictions")
    
    def evaluate_with_retry(self, dc_module, example, max_retries=3):
        """
        Evaluate single example with retry logic
        
        Args:
            dc_module: DCRAGModule instance
            example: Dataset example
            max_retries: Maximum retry attempts
        
        Returns:
            dict: Prediction result
        """
        for attempt in range(max_retries):
            try:
                pred = dc_module(
                    question=example.question,
                    doc_id=example.doc_id,
                    answer_format=example.answer_format
                )
                
                # Compute ANLS score
                score = eval_score(example.answer, pred, example.answer_format)
                is_correct = (score >= 0.5)
                
                return {
                    'question': example.question,
                    'doc_id': example.doc_id,
                    'answer_format': example.answer_format,
                    'ground_truth': example.answer,
                    'prediction': pred,
                    'anls_score': score,
                    'correct': is_correct,
                    'cheatsheet_length': len(dc_module.cheatsheet)
                }
                
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"All retries failed: {e}")
                    return {
                        'question': example.question,
                        'doc_id': example.doc_id,
                        'answer_format': example.answer_format,
                        'ground_truth': example.answer,
                        'prediction': f"ERROR: {str(e)}",
                        'anls_score': 0.0,
                        'correct': False,
                        'cheatsheet_length': len(dc_module.cheatsheet)
                    }
    
    def evaluate(self, dataset_name="dev", model_name="qwen2.5-7b-instruct", 
                 variant="cumulative", warmup=False, max_questions=None, 
                 bootstrap_cheatsheet_file=None):
        """
        Run DC evaluation on dataset
        
        Args:
            dataset_name: "dev" or "test"
            model_name: Model to use
            variant: "cumulative" or "retrieval_synthesis"
            warmup: If True, warm up on train+dev before test
            max_questions: Limit questions (for testing)
            bootstrap_cheatsheet_file: Path to JSON file with pre-existing cheatsheet
        
        Returns:
            dict: Evaluation results
        """
        self.logger.info("="*80)
        self.logger.info("DC EVALUATION - MMESGBench")
        self.logger.info("="*80)
        self.logger.info(f"Dataset: {dataset_name}")
        self.logger.info(f"Model: {model_name}")
        self.logger.info(f"Variant: {variant}")
        self.logger.info(f"Warmup: {warmup}")
        
        # Setup
        setup_dspy_qwen()  # Setup environment (needed for retrieval)
        dataset = MMESGBenchDataset()
        
        # Select dataset
        if dataset_name == "dev":
            eval_set = dataset.dev_set
        elif dataset_name == "test":
            eval_set = dataset.test_set
        else:
            raise ValueError(f"Unknown dataset: {dataset_name}")
        
        if max_questions:
            eval_set = eval_set[:max_questions]
        
        # Checkpoint file
        warmup_suffix = "_warm" if warmup else "_cold"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_file = self.output_dir / f"dc_{variant}{warmup_suffix}_{dataset_name}_checkpoint.json"
        output_file = self.output_dir / f"dc_{variant}{warmup_suffix}_{dataset_name}_{timestamp}.json"
        
        # Initialize DC module
        dc_module = DCRAGModule(model_name=model_name, variant=variant)
        
        # Bootstrap from existing cheatsheet if provided
        if bootstrap_cheatsheet_file and os.path.exists(bootstrap_cheatsheet_file):
            self.logger.info(f"🔄 Loading bootstrap cheatsheet from: {bootstrap_cheatsheet_file}")
            with open(bootstrap_cheatsheet_file, 'r') as f:
                bootstrap_data = json.load(f)
                dc_module.cheatsheet = bootstrap_data.get('final_cheatsheet', '(empty)')
            self.logger.info(f"✅ Bootstrap cheatsheet loaded: {len(dc_module.cheatsheet)} chars")
        
        # Warmup if requested
        if warmup:
            self.logger.info("🔥 Warming up cheatsheet on train+dev sets...")
            warmup_set = dataset.train_set + dataset.dev_set
            for i, example in enumerate(tqdm(warmup_set, desc="Warmup")):
                try:
                    dc_module(example.question, example.doc_id, example.answer_format)
                except Exception as e:
                    self.logger.warning(f"Warmup Q{i+1} error: {e}")
            
            self.logger.info(f"✅ Warmup complete. Cheatsheet: {len(dc_module.cheatsheet)} chars")
        
        # Load checkpoint if exists
        checkpoint = self.load_checkpoint(checkpoint_file)
        if checkpoint:
            predictions = checkpoint['predictions']
            dc_module.cheatsheet = checkpoint['cheatsheet']
            start_idx = len(predictions)
            self.logger.info(f"Resuming from question {start_idx + 1}/{len(eval_set)}")
        else:
            predictions = []
            start_idx = 0
        
        # Evaluate
        self.logger.info(f"🔄 Evaluating {len(eval_set)} questions...")
        
        for i, example in enumerate(tqdm(eval_set[start_idx:], 
                                         initial=start_idx, 
                                         total=len(eval_set),
                                         desc="DC Evaluation")):
            result = self.evaluate_with_retry(dc_module, example)
            predictions.append(result)
            
            # Save checkpoint every 10 questions
            if len(predictions) % 10 == 0:
                metadata = {
                    'dataset': dataset_name,
                    'model': model_name,
                    'variant': variant,
                    'warmup': warmup,
                    'questions_processed': len(predictions)
                }
                self.save_checkpoint(checkpoint_file, predictions, 
                                   dc_module.cheatsheet, metadata)
        
        # Compute final metrics
        results = self.compute_metrics(predictions)
        results['metadata'] = {
            'dataset': dataset_name,
            'model': model_name,
            'variant': variant,
            'warmup': warmup,
            'total_questions': len(predictions),
            'timestamp': timestamp,
            'final_cheatsheet_length': len(dc_module.cheatsheet)
        }
        results['predictions'] = predictions
        results['final_cheatsheet'] = dc_module.cheatsheet
        
        # Save final results
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        self.logger.info("\n" + "="*80)
        self.logger.info("EVALUATION COMPLETE")
        self.logger.info("="*80)
        self.print_results(results)
        self.logger.info(f"\n💾 Results saved: {output_file}")
        
        # Remove checkpoint
        if checkpoint_file.exists():
            checkpoint_file.unlink()
            self.logger.info(f"🗑️  Checkpoint removed")
        
        return results
    
    def compute_metrics(self, predictions):
        """Compute evaluation metrics"""
        total = len(predictions)
        correct = sum(1 for p in predictions if p['correct'])
        accuracy = correct / total if total > 0 else 0.0
        
        # Format breakdown
        format_breakdown = {}
        for fmt in ['Int', 'Float', 'Str', 'List', 'null']:
            fmt_preds = [p for p in predictions if p['answer_format'] == fmt]
            if fmt_preds:
                fmt_correct = sum(1 for p in fmt_preds if p['correct'])
                format_breakdown[fmt] = {
                    'correct': fmt_correct,
                    'total': len(fmt_preds),
                    'accuracy': fmt_correct / len(fmt_preds)
                }
        
        return {
            'overall_accuracy': accuracy,
            'correct': correct,
            'total': total,
            'format_breakdown': format_breakdown
        }
    
    def print_results(self, results):
        """Print formatted results"""
        self.logger.info(f"\n🎯 Overall Performance:")
        self.logger.info(f"   Accuracy: {results['overall_accuracy']:.1%} ({results['correct']}/{results['total']})")
        
        self.logger.info(f"\n📋 Format Breakdown:")
        for fmt, stats in results['format_breakdown'].items():
            acc = stats['accuracy']
            correct = stats['correct']
            total = stats['total']
            self.logger.info(f"   {fmt:6s}: {acc:6.1%} ({correct:3d}/{total:3d})")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate Dynamic Cheatsheet on MMESGBench")
    parser.add_argument("--dataset", choices=["dev", "test"], default="dev",
                       help="Dataset to evaluate on")
    parser.add_argument("--model", default="qwen2.5-7b-instruct",
                       help="Model to use")
    parser.add_argument("--variant", choices=["cumulative", "retrieval_synthesis"],
                       default="cumulative", help="DC variant")
    parser.add_argument("--warmup", action="store_true",
                       help="Warm up cheatsheet on train+dev before test")
    parser.add_argument("--max-questions", type=int, default=None,
                       help="Limit number of questions (for testing)")
    parser.add_argument("--bootstrap-cheatsheet", type=str, default=None,
                       help="Path to JSON file with pre-existing cheatsheet to bootstrap from")
    parser.add_argument("--output-dir", default="results/dc_experiments",
                       help="Output directory")
    
    args = parser.parse_args()
    
    evaluator = DCEvaluator(output_dir=args.output_dir)
    results = evaluator.evaluate(
        dataset_name=args.dataset,
        model_name=args.model,
        variant=args.variant,
        warmup=args.warmup,
        max_questions=args.max_questions,
        bootstrap_cheatsheet_file=args.bootstrap_cheatsheet
    )
    
    print("\n✅ Evaluation complete!")

