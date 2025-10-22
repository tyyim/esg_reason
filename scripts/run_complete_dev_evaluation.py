#!/usr/bin/env python3
"""
Complete Dev Set Evaluation: Baseline vs MIPROv2 vs GEPA

Runs all three approaches on the same 93 dev questions to get accurate comparison.
Saves predictions for question-level error analysis.
"""

import json
import logging
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict
import dspy
from tqdm import tqdm

# Setup logging
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_dir = Path("logs/complete_evaluation")
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"complete_eval_{timestamp}.log"

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
    import os
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


def load_dev_set() -> List[dspy.Example]:
    """Load dev set."""
    dev_path = Path("dspy_implementation/data_splits/dev_93.json")
    with open(dev_path, 'r') as f:
        dev_data = json.load(f)
    dev_set = [dspy.Example(**item).with_inputs('question', 'doc_id', 'evidence_pages', 'answer_format')
               for item in dev_data]
    logger.info(f"✅ Loaded {len(dev_set)} dev questions")
    return dev_set


def evaluate_single(module, example: dspy.Example, max_retries: int = 3) -> Dict[str, Any]:
    """Evaluate single example with retry."""
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


def run_evaluation(module, dev_set: List[dspy.Example], name: str) -> Dict[str, Any]:
    """Run full evaluation on dev set."""
    logger.info(f"\n{'='*80}")
    logger.info(f"EVALUATING {name.upper()} ON DEV SET")
    logger.info(f"{'='*80}\n")

    predictions = {}
    correct_count = 0
    error_count = 0

    for i, example in enumerate(tqdm(dev_set, desc=f"Evaluating {name}")):
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

    accuracy = correct_count / len(dev_set) * 100
    logger.info(f"\n✅ {name} Evaluation Complete")
    logger.info(f"   Correct: {correct_count}/{len(dev_set)} ({accuracy:.1f}%)")
    logger.info(f"   Errors: {error_count}/{len(dev_set)}")

    return {
        'predictions': predictions,
        'correct_count': correct_count,
        'total': len(dev_set),
        'accuracy': accuracy,
        'error_count': error_count
    }


def compare_results(baseline: Dict, miprov2: Dict, gepa: Dict, dev_set: List[dspy.Example]):
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
        'by_format': defaultdict(lambda: {'baseline': 0, 'miprov2': 0, 'gepa': 0, 'total': 0})
    }

    baseline_preds = baseline['predictions']
    miprov2_preds = miprov2['predictions']
    gepa_preds = gepa['predictions']

    for i, example in enumerate(dev_set):
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
    print("COMPLETE DEV SET EVALUATION RESULTS")
    print("="*80)

    total = baseline['total']

    print(f"\n📊 Overall Performance ({total} questions):")
    print(f"   Baseline:  {baseline['correct_count']:2d}/{total} ({baseline['accuracy']:.1f}%)")
    print(f"   MIPROv2:   {miprov2['correct_count']:2d}/{total} ({miprov2['accuracy']:.1f}%)")
    print(f"   GEPA:      {gepa['correct_count']:2d}/{total} ({gepa['accuracy']:.1f}%)")

    print(f"\n📈 Relative to Baseline:")
    mipro_delta = miprov2['accuracy'] - baseline['accuracy']
    gepa_delta = gepa['accuracy'] - baseline['accuracy']
    print(f"   MIPROv2: {mipro_delta:+.1f}% ({'+' if mipro_delta >= 0 else ''}{miprov2['correct_count'] - baseline['correct_count']} questions)")
    print(f"   GEPA:    {gepa_delta:+.1f}% ({'+' if gepa_delta >= 0 else ''}{gepa['correct_count'] - baseline['correct_count']} questions)")

    print(f"\n🔄 Question Patterns:")
    print(f"   All 3 correct:  {len(analysis['all_correct']):2d} questions")
    print(f"   All 3 wrong:    {len(analysis['all_wrong']):2d} questions")

    print(f"\n📉 Degradations (Baseline Right → Wrong):")
    print(f"   MIPROv2: {len(analysis['degradations']['miprov2']):2d} questions")
    print(f"   GEPA:    {len(analysis['degradations']['gepa']):2d} questions")

    print(f"\n📈 Improvements (Baseline Wrong → Right):")
    print(f"   MIPROv2: {len(analysis['improvements']['miprov2']):2d} questions")
    print(f"   GEPA:    {len(analysis['improvements']['gepa']):2d} questions")

    print(f"\n📋 Performance by Answer Format:")
    print(f"   Format    Baseline  MIPROv2   GEPA      Total")
    print(f"   -------   --------  --------  --------  -----")
    for fmt, data in sorted(analysis['by_format'].items()):
        base_pct = data['baseline'] / data['total'] * 100 if data['total'] > 0 else 0
        mipro_pct = data['miprov2'] / data['total'] * 100 if data['total'] > 0 else 0
        gepa_pct = data['gepa'] / data['total'] * 100 if data['total'] > 0 else 0
        print(f"   {fmt:8s}  {base_pct:6.1f}%   {mipro_pct:6.1f}%   {gepa_pct:6.1f}%   {data['total']:3d}")

    print("\n" + "="*80)


def main():
    """Main execution."""
    print("\n" + "="*80)
    print("COMPLETE DEV SET EVALUATION")
    print("Baseline vs MIPROv2 vs GEPA")
    print("="*80)

    # Configure DSPy
    configure_dspy('qwen2.5-7b-instruct')

    # Load dev set
    logger.info("📊 Loading dev set...")
    dev_set = load_dev_set()

    # 1. Evaluate Baseline (fresh, no optimization)
    logger.info("\n🔧 Initializing Baseline module...")
    baseline_module = BaselineMMESGBenchRAG()
    baseline_results = run_evaluation(baseline_module, dev_set, "Baseline")

    # Save baseline predictions
    with open(f'baseline_dev_predictions_{timestamp}.json', 'w') as f:
        json.dump(baseline_results, f, indent=2)
    logger.info(f"💾 Saved: baseline_dev_predictions_{timestamp}.json")

    # 2. Evaluate MIPROv2
    logger.info("\n🔧 Loading MIPROv2 optimized module...")
    miprov2_module = BaselineMMESGBenchRAG()
    miprov2_module.load('dspy_implementation/optimized_modules/baseline_rag_20251015_134537.json')
    miprov2_results = run_evaluation(miprov2_module, dev_set, "MIPROv2")

    # Save MIPROv2 predictions
    with open(f'miprov2_dev_predictions_{timestamp}.json', 'w') as f:
        json.dump(miprov2_results, f, indent=2)
    logger.info(f"💾 Saved: miprov2_dev_predictions_{timestamp}.json")

    # 3. Evaluate GEPA
    logger.info("\n🔧 Loading GEPA optimized module...")
    gepa_module = BaselineMMESGBenchRAG()
    gepa_module.load('dspy_implementation/optimized_programs/gepa_skip_baseline_20251018_150806.json')
    gepa_results = run_evaluation(gepa_module, dev_set, "GEPA")

    # Save GEPA predictions
    with open(f'gepa_dev_predictions_{timestamp}.json', 'w') as f:
        json.dump(gepa_results, f, indent=2)
    logger.info(f"💾 Saved: gepa_dev_predictions_{timestamp}.json")

    # 4. Compare results
    analysis = compare_results(baseline_results, miprov2_results, gepa_results, dev_set)

    # Save complete analysis
    complete_analysis = {
        'timestamp': timestamp,
        'baseline': baseline_results,
        'miprov2': miprov2_results,
        'gepa': gepa_results,
        'analysis': {
            'degradations': analysis['degradations'],
            'improvements': analysis['improvements'],
            'all_correct': analysis['all_correct'],
            'all_wrong': analysis['all_wrong'],
            'by_format': dict(analysis['by_format'])
        }
    }

    with open(f'complete_dev_analysis_{timestamp}.json', 'w') as f:
        json.dump(complete_analysis, f, indent=2)
    logger.info(f"💾 Saved: complete_dev_analysis_{timestamp}.json")

    # Print summary
    print_summary(baseline_results, miprov2_results, gepa_results, analysis)

    logger.info(f"\n✅ Complete evaluation finished!")
    logger.info(f"📋 Log file: {log_file}")


if __name__ == "__main__":
    main()
