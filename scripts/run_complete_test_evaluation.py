#!/usr/bin/env python3
"""
Complete Test Set Evaluation: Baseline vs MIPROv2 vs GEPA

Runs all three approaches on the same 654 test questions to validate dev set findings.
Includes checkpoint/resume for long-running evaluation.
Saves predictions for question-level error analysis.
"""

import json
import logging
import sys
import time
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict
import dspy
from tqdm import tqdm

# Setup logging
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_dir = Path("logs/test_evaluation")
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"test_eval_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import local modules
sys.path.insert(0, str(Path(__file__).parent / "dspy_implementation"))
from dspy_rag_enhanced import BaselineMMESGBenchRAG
from MMESGBench.src.eval.eval_score import eval_score


def configure_dspy(model_name: str = 'qwen2.5-7b-instruct'):
    """Configure DSPy with specified model."""
    from dotenv import load_dotenv
    load_dotenv()

    lm = dspy.LM(
        model=f'openai/{model_name}',
        api_key=os.getenv('DASHSCOPE_API_KEY'),
        api_base='https://dashscope.aliyuncs.com/compatible-mode/v1',
        temperature=0.0,
        max_tokens=1024
    )
    dspy.configure(lm=lm)
    logger.info(f"✅ DSPy configured with {model_name}")
    return lm


def load_test_set() -> List[dspy.Example]:
    """Load test set (654 questions)."""
    test_path = Path("dspy_implementation/data_splits/test_654.json")
    with open(test_path, 'r') as f:
        test_data = json.load(f)
    test_set = [dspy.Example(**item).with_inputs('question', 'doc_id', 'evidence_pages', 'answer_format')
                for item in test_data]
    logger.info(f"✅ Loaded {len(test_set)} test questions")
    return test_set


def evaluate_single(module, example: dspy.Example, max_retries: int = 3) -> Dict[str, Any]:
    """Evaluate single example with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            prediction = module(
                question=example.question,
                doc_id=example.doc_id,
                answer_format=example.answer_format
            )
            return {
                'answer': prediction.answer,
                'analysis': prediction.analysis,
                'context': getattr(prediction, 'context', ''),
                'success': True
            }
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"Error (attempt {attempt+1}/{max_retries}), waiting {wait_time}s: {str(e)[:100]}")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed after {max_retries} attempts: {str(e)[:100]}")
                return {'answer': 'ERROR', 'analysis': str(e), 'context': '', 'success': False}


def run_evaluation(module, test_set: List[dspy.Example], name: str, checkpoint_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Run full evaluation on test set with checkpoint/resume.
    
    Args:
        module: DSPy module to evaluate
        test_set: List of test examples
        name: Name of approach (for logging)
        checkpoint_file: Optional checkpoint file for resume
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"EVALUATING {name.upper()} ON TEST SET (654 questions)")
    logger.info(f"{'='*80}\n")

    # Check for existing checkpoint
    predictions = {}
    start_idx = 0
    
    if checkpoint_file and os.path.exists(checkpoint_file):
        logger.info(f"📂 Found checkpoint: {checkpoint_file}")
        with open(checkpoint_file, 'r') as f:
            checkpoint_data = json.load(f)
        predictions = checkpoint_data.get('predictions', {})
        start_idx = len(predictions)
        logger.info(f"   Resuming from question {start_idx + 1}/{len(test_set)}")
    
    correct_count = sum(1 for p in predictions.values() if p.get('correct', False))
    error_count = sum(1 for p in predictions.values() if not p.get('success', True))

    # Run evaluation
    for i in range(start_idx, len(test_set)):
        example = test_set[i]
        
        # Evaluate single question
        pred = evaluate_single(module, example)
        predictions[f'q{i}'] = pred

        # Evaluate correctness
        if pred['success']:
            try:
                score = eval_score(example.answer, pred['answer'], example.answer_format)
                is_correct = score >= 0.5
                predictions[f'q{i}']['score'] = score
                predictions[f'q{i}']['correct'] = is_correct
                if is_correct:
                    correct_count += 1
            except Exception as e:
                logger.warning(f"eval_score error for q{i}: {e}")
                predictions[f'q{i}']['score'] = 0.0
                predictions[f'q{i}']['correct'] = False
                error_count += 1
        else:
            error_count += 1
            predictions[f'q{i}']['score'] = 0.0
            predictions[f'q{i}']['correct'] = False

        # Save checkpoint every 20 questions
        if checkpoint_file and (i + 1) % 20 == 0:
            checkpoint_data = {
                'predictions': predictions,
                'correct_count': correct_count,
                'total': i + 1,
                'accuracy': correct_count / (i + 1) * 100,
                'error_count': error_count
            }
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
            logger.info(f"   ✓ Checkpoint saved: {i + 1}/{len(test_set)} questions "
                       f"({correct_count}/{i+1} = {correct_count/(i+1)*100:.1f}%)")

    accuracy = correct_count / len(test_set) * 100
    logger.info(f"\n✅ {name} Evaluation Complete")
    logger.info(f"   Correct: {correct_count}/{len(test_set)} ({accuracy:.1f}%)")
    logger.info(f"   Errors: {error_count}/{len(test_set)}")

    return {
        'predictions': predictions,
        'correct_count': correct_count,
        'total': len(test_set),
        'accuracy': accuracy,
        'error_count': error_count
    }


def compare_results(baseline: Dict, miprov2: Dict, gepa: Dict, test_set: List[dspy.Example]):
    """Compare results across all three approaches."""
    logger.info(f"\n{'='*80}")
    logger.info("QUESTION-LEVEL COMPARISON")
    logger.info(f"{'='*80}\n")

    analysis = {
        'degradations': {
            'miprov2': [],  # Right in baseline, wrong in MIPROv2
            'gepa': []      # Right in baseline, wrong in GEPA
        },
        'improvements': {
            'miprov2': [],  # Wrong in baseline, right in MIPROv2
            'gepa': []      # Wrong in baseline, right in GEPA
        },
        'all_correct': [],
        'all_wrong': [],
        'unique_wins': {
            'miprov2': [],  # Only MIPROv2 correct
            'gepa': []      # Only GEPA correct
        },
        'by_format': defaultdict(lambda: {'baseline': 0, 'miprov2': 0, 'gepa': 0, 'total': 0})
    }

    baseline_preds = baseline['predictions']
    miprov2_preds = miprov2['predictions']
    gepa_preds = gepa['predictions']

    for i, example in enumerate(test_set):
        qid = f'q{i}'

        base_correct = baseline_preds[qid].get('correct', False)
        mipro_correct = miprov2_preds[qid].get('correct', False)
        gepa_correct = gepa_preds[qid].get('correct', False)

        fmt = example.answer_format if example.answer_format else 'null'
        analysis['by_format'][fmt]['total'] += 1

        if base_correct:
            analysis['by_format'][fmt]['baseline'] += 1
        if mipro_correct:
            analysis['by_format'][fmt]['miprov2'] += 1
        if gepa_correct:
            analysis['by_format'][fmt]['gepa'] += 1

        # Track patterns
        if base_correct and mipro_correct and gepa_correct:
            analysis['all_correct'].append(i)
        elif not base_correct and not mipro_correct and not gepa_correct:
            analysis['all_wrong'].append(i)
        
        # Unique wins
        if not base_correct and mipro_correct and not gepa_correct:
            analysis['unique_wins']['miprov2'].append(i)
        if not base_correct and not mipro_correct and gepa_correct:
            analysis['unique_wins']['gepa'].append(i)

        # Degradations
        if base_correct and not mipro_correct:
            analysis['degradations']['miprov2'].append({
                'idx': i,
                'question': example.question,
                'gt': example.answer,
                'baseline': baseline_preds[qid]['answer'],
                'miprov2': miprov2_preds[qid]['answer'],
                'format': fmt
            })
        if base_correct and not gepa_correct:
            analysis['degradations']['gepa'].append({
                'idx': i,
                'question': example.question,
                'gt': example.answer,
                'baseline': baseline_preds[qid]['answer'],
                'gepa': gepa_preds[qid]['answer'],
                'format': fmt
            })

        # Improvements
        if not base_correct and mipro_correct:
            analysis['improvements']['miprov2'].append({
                'idx': i,
                'question': example.question,
                'gt': example.answer,
                'baseline': baseline_preds[qid]['answer'],
                'miprov2': miprov2_preds[qid]['answer'],
                'format': fmt
            })
        if not base_correct and gepa_correct:
            analysis['improvements']['gepa'].append({
                'idx': i,
                'question': example.question,
                'gt': example.answer,
                'baseline': baseline_preds[qid]['answer'],
                'gepa': gepa_preds[qid]['answer'],
                'format': fmt
            })

    return analysis


def print_summary(baseline: Dict, miprov2: Dict, gepa: Dict, analysis: Dict):
    """Print comprehensive summary."""
    print("\n" + "="*80)
    print("COMPLETE TEST SET EVALUATION RESULTS (654 Questions)")
    print("="*80)

    total = baseline['total']

    print(f"\n📊 Overall Performance ({total} questions):")
    print(f"   Baseline:  {baseline['correct_count']:3d}/{total} ({baseline['accuracy']:.1f}%)")
    print(f"   MIPROv2:   {miprov2['correct_count']:3d}/{total} ({miprov2['accuracy']:.1f}%)")
    print(f"   GEPA:      {gepa['correct_count']:3d}/{total} ({gepa['accuracy']:.1f}%)")

    print(f"\n📈 Relative to Baseline:")
    mipro_delta = miprov2['accuracy'] - baseline['accuracy']
    gepa_delta = gepa['accuracy'] - baseline['accuracy']
    mipro_q_delta = miprov2['correct_count'] - baseline['correct_count']
    gepa_q_delta = gepa['correct_count'] - baseline['correct_count']
    
    print(f"   MIPROv2: {mipro_delta:+.1f}% ({mipro_q_delta:+d} questions)")
    print(f"   GEPA:    {gepa_delta:+.1f}% ({gepa_q_delta:+d} questions)")

    print(f"\n🔄 Question Patterns:")
    print(f"   All 3 correct:  {len(analysis['all_correct']):3d} questions ({len(analysis['all_correct'])/total*100:.1f}%)")
    print(f"   All 3 wrong:    {len(analysis['all_wrong']):3d} questions ({len(analysis['all_wrong'])/total*100:.1f}%)")
    print(f"   MIPROv2 only:   {len(analysis['unique_wins']['miprov2']):3d} questions")
    print(f"   GEPA only:      {len(analysis['unique_wins']['gepa']):3d} questions")

    print(f"\n📉 Degradations (Baseline Right → Wrong):")
    print(f"   MIPROv2: {len(analysis['degradations']['miprov2']):3d} questions")
    print(f"   GEPA:    {len(analysis['degradations']['gepa']):3d} questions")

    print(f"\n📈 Improvements (Baseline Wrong → Right):")
    print(f"   MIPROv2: {len(analysis['improvements']['miprov2']):3d} questions")
    print(f"   GEPA:    {len(analysis['improvements']['gepa']):3d} questions")

    print(f"\n📋 Performance by Answer Format:")
    print(f"   Format    Baseline  MIPROv2   GEPA      Total")
    print(f"   -------   --------  --------  --------  -----")
    for fmt in ['Int', 'Float', 'Str', 'List', 'null']:
        if fmt in analysis['by_format']:
            data = analysis['by_format'][fmt]
            base_pct = data['baseline'] / data['total'] * 100 if data['total'] > 0 else 0
            mipro_pct = data['miprov2'] / data['total'] * 100 if data['total'] > 0 else 0
            gepa_pct = data['gepa'] / data['total'] * 100 if data['total'] > 0 else 0
            print(f"   {fmt:8s}  {base_pct:6.1f}%   {mipro_pct:6.1f}%   {gepa_pct:6.1f}%   {data['total']:3d}")

    print("\n" + "="*80)


def main():
    """Main execution."""
    print("\n" + "="*80)
    print("COMPLETE TEST SET EVALUATION (654 Questions)")
    print("Baseline vs MIPROv2 vs GEPA")
    print("Expected runtime: 3-4 hours")
    print("="*80)

    # Configure DSPy
    configure_dspy('qwen2.5-7b-instruct')

    # Load test set
    logger.info("📊 Loading test set...")
    test_set = load_test_set()
    logger.info(f"   Total questions: {len(test_set)}")

    # 1. Evaluate Baseline (fresh, no optimization)
    logger.info("\n🔧 Initializing Baseline module...")
    baseline_module = BaselineMMESGBenchRAG()
    baseline_results = run_evaluation(
        baseline_module, 
        test_set, 
        "Baseline",
        checkpoint_file=f'baseline_test_checkpoint_{timestamp}.json'
    )

    # Save baseline predictions
    output_file = f'baseline_test_predictions_{timestamp}.json'
    with open(output_file, 'w') as f:
        json.dump(baseline_results, f, indent=2)
    logger.info(f"💾 Saved: {output_file}")

    # 2. Evaluate MIPROv2
    logger.info("\n🔧 Loading MIPROv2 optimized module...")
    miprov2_module = BaselineMMESGBenchRAG()
    miprov2_module.load('dspy_implementation/optimized_modules/baseline_rag_20251015_134537.json')
    miprov2_results = run_evaluation(
        miprov2_module, 
        test_set, 
        "MIPROv2",
        checkpoint_file=f'miprov2_test_checkpoint_{timestamp}.json'
    )

    # Save MIPROv2 predictions
    output_file = f'miprov2_test_predictions_{timestamp}.json'
    with open(output_file, 'w') as f:
        json.dump(miprov2_results, f, indent=2)
    logger.info(f"💾 Saved: {output_file}")

    # 3. Evaluate GEPA
    logger.info("\n🔧 Loading GEPA optimized module...")
    gepa_module = BaselineMMESGBenchRAG()
    gepa_module.load('dspy_implementation/optimized_programs/gepa_skip_baseline_20251018_150806.json')
    gepa_results = run_evaluation(
        gepa_module, 
        test_set, 
        "GEPA",
        checkpoint_file=f'gepa_test_checkpoint_{timestamp}.json'
    )

    # Save GEPA predictions
    output_file = f'gepa_test_predictions_{timestamp}.json'
    with open(output_file, 'w') as f:
        json.dump(gepa_results, f, indent=2)
    logger.info(f"💾 Saved: {output_file}")

    # 4. Compare results
    logger.info("\n📊 Comparing results across all three approaches...")
    analysis = compare_results(baseline_results, miprov2_results, gepa_results, test_set)

    # Save complete analysis
    complete_analysis = {
        'timestamp': timestamp,
        'dataset': 'test_set',
        'total_questions': len(test_set),
        'baseline': baseline_results,
        'miprov2': miprov2_results,
        'gepa': gepa_results,
        'analysis': {
            'degradations': analysis['degradations'],
            'improvements': analysis['improvements'],
            'all_correct': analysis['all_correct'],
            'all_wrong': analysis['all_wrong'],
            'unique_wins': analysis['unique_wins'],
            'by_format': dict(analysis['by_format'])
        }
    }

    output_file = f'complete_test_analysis_{timestamp}.json'
    with open(output_file, 'w') as f:
        json.dump(complete_analysis, f, indent=2)
    logger.info(f"💾 Saved: {output_file}")

    # Print summary
    print_summary(baseline_results, miprov2_results, gepa_results, analysis)

    logger.info(f"\n✅ Complete test set evaluation finished!")
    logger.info(f"📋 Log file: {log_file}")
    logger.info(f"\n🎯 Next Steps:")
    logger.info(f"   1. Review results above")
    logger.info(f"   2. Compare with dev set findings")
    logger.info(f"   3. Statistical significance testing")
    logger.info(f"   4. Update documentation with validated results")


if __name__ == "__main__":
    main()

