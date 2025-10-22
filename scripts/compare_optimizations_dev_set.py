#!/usr/bin/env python3
"""
Question-Level Error Analysis: Baseline vs MIPROv2 vs GEPA on Dev Set

Loads existing baseline predictions and saved optimized programs,
runs evaluations to get MIPROv2 and GEPA predictions, then performs
detailed question-level comparison.

Following CODING_BEST_PRACTICES.md:
- Uses existing data where available
- Structured logging
- Retry logic with exponential backoff
- Progress tracking with tqdm
- Saves predictions for future analysis
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict
import dspy
from tqdm import tqdm
import time

# Setup logging
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_dir = Path("logs/error_analysis")
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"dev_set_comparison_{timestamp}.log"

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
import sys
sys.path.insert(0, str(Path(__file__).parent / "dspy_implementation"))

from dspy_rag_enhanced import BaselineMMESGBenchRAG
from dspy_postgres_retriever import DSPyPostgresRetriever
from MMESGBench.src.eval.eval_score import eval_score


def load_baseline_predictions(checkpoint_path: str) -> Dict[str, Any]:
    """Load existing baseline predictions from checkpoint."""
    logger.info(f"📦 Loading baseline predictions from {checkpoint_path}")
    with open(checkpoint_path, 'r') as f:
        data = json.load(f)

    predictions = data.get('predictions', [])
    logger.info(f"✅ Loaded {len(predictions)} baseline predictions")
    return {f"q{i}": pred['_store'] for i, pred in enumerate(predictions)}


def load_dev_set() -> List[dspy.Example]:
    """Load the dev set (93 questions)."""
    logger.info("📊 Loading dev set...")
    dev_path = Path("dspy_implementation/data_splits/dev_93.json")

    with open(dev_path, 'r') as f:
        dev_data = json.load(f)

    dev_set = [dspy.Example(**item).with_inputs('question', 'doc_id', 'evidence_pages', 'answer_format')
               for item in dev_data]

    logger.info(f"✅ Loaded {len(dev_set)} dev questions")
    return dev_set


def load_optimized_program(program_path: str, module_class) -> Any:
    """Load an optimized DSPy program."""
    logger.info(f"📦 Loading optimized program from {program_path}")

    # Initialize module
    module = module_class()

    # Load optimized state
    module.load(program_path)

    logger.info("✅ Optimized program loaded")
    return module


def evaluate_with_retry(module, example: dspy.Example, max_retries: int = 3) -> Dict[str, Any]:
    """Evaluate a single example with retry logic."""
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
                'rationale': getattr(prediction, 'rationale', '')
            }

        except Exception as e:
            if "Connection" in str(e) and attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"Connection error (attempt {attempt+1}/{max_retries}), retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"Error evaluating question: {e}")
                return {
                    'answer': 'ERROR',
                    'analysis': str(e),
                    'context': '',
                    'rationale': ''
                }

    return {
        'answer': 'ERROR',
        'analysis': 'Max retries exceeded',
        'context': '',
        'rationale': ''
    }


def run_evaluation(module, dev_set: List[dspy.Example], name: str) -> Dict[str, Any]:
    """Run evaluation on dev set and return predictions."""
    logger.info(f"🔄 Evaluating {name} on {len(dev_set)} questions...")

    predictions = {}

    for i, example in enumerate(tqdm(dev_set, desc=f"Evaluating {name}")):
        pred = evaluate_with_retry(module, example)
        predictions[f"q{i}"] = pred

    logger.info(f"✅ {name} evaluation complete")
    return predictions


def compare_predictions(baseline: Dict, miprov2: Dict, gepa: Dict, dev_set: List[dspy.Example]) -> Dict[str, Any]:
    """Perform detailed question-level comparison."""
    logger.info("📊 Performing question-level comparison...")

    results = {
        'baseline_correct': [],
        'miprov2_correct': [],
        'gepa_correct': [],
        'baseline_only': [],  # Correct in baseline, wrong in both MIPROv2 and GEPA
        'miprov2_only': [],   # Correct in MIPROv2, wrong in others
        'gepa_only': [],      # Correct in GEPA, wrong in others
        'all_correct': [],
        'all_wrong': [],
        'miprov2_degraded': [],  # Right in baseline, wrong in MIPROv2
        'gepa_degraded': [],     # Right in baseline, wrong in GEPA
        'miprov2_improved': [],  # Wrong in baseline, right in MIPROv2
        'gepa_improved': [],     # Wrong in baseline, right in GEPA
        'by_format': defaultdict(lambda: {
            'baseline': {'correct': 0, 'total': 0},
            'miprov2': {'correct': 0, 'total': 0},
            'gepa': {'correct': 0, 'total': 0}
        })
    }

    for i, example in enumerate(dev_set):
        qid = f"q{i}"
        gt_answer = example.answer
        answer_format = example.answer_format

        # Get predictions
        base_pred = baseline.get(qid, {}).get('answer', 'MISSING')
        mipro_pred = miprov2.get(qid, {}).get('answer', 'MISSING')
        gepa_pred = gepa.get(qid, {}).get('answer', 'MISSING')

        # Evaluate correctness
        try:
            base_score = eval_score(gt_answer, base_pred, answer_format) if base_pred != 'MISSING' else 0
            mipro_score = eval_score(gt_answer, mipro_pred, answer_format) if mipro_pred != 'MISSING' else 0
            gepa_score = eval_score(gt_answer, gepa_pred, answer_format) if gepa_pred != 'MISSING' else 0
        except Exception as e:
            logger.warning(f"eval_score error for q{i}: {e}")
            base_score = mipro_score = gepa_score = 0

        base_correct = base_score >= 0.5
        mipro_correct = mipro_score >= 0.5
        gepa_correct = gepa_score >= 0.5

        # Track correctness
        if base_correct:
            results['baseline_correct'].append(i)
        if mipro_correct:
            results['miprov2_correct'].append(i)
        if gepa_correct:
            results['gepa_correct'].append(i)

        # Track patterns
        if base_correct and mipro_correct and gepa_correct:
            results['all_correct'].append(i)
        elif not base_correct and not mipro_correct and not gepa_correct:
            results['all_wrong'].append(i)

        if base_correct and not mipro_correct and not gepa_correct:
            results['baseline_only'].append(i)
        if mipro_correct and not base_correct and not gepa_correct:
            results['miprov2_only'].append(i)
        if gepa_correct and not base_correct and not mipro_correct:
            results['gepa_only'].append(i)

        # Track degradations and improvements
        if base_correct and not mipro_correct:
            results['miprov2_degraded'].append({
                'idx': i,
                'question': example.question,
                'gt_answer': gt_answer,
                'baseline_pred': base_pred,
                'miprov2_pred': mipro_pred,
                'answer_format': answer_format
            })
        if base_correct and not gepa_correct:
            results['gepa_degraded'].append({
                'idx': i,
                'question': example.question,
                'gt_answer': gt_answer,
                'baseline_pred': base_pred,
                'gepa_pred': gepa_pred,
                'answer_format': answer_format
            })

        if not base_correct and mipro_correct:
            results['miprov2_improved'].append({
                'idx': i,
                'question': example.question,
                'gt_answer': gt_answer,
                'baseline_pred': base_pred,
                'miprov2_pred': mipro_pred,
                'answer_format': answer_format
            })
        if not base_correct and gepa_correct:
            results['gepa_improved'].append({
                'idx': i,
                'question': example.question,
                'gt_answer': gt_answer,
                'baseline_pred': base_pred,
                'gepa_pred': gepa_pred,
                'answer_format': answer_format
            })

        # Track by format
        fmt = answer_format if answer_format else 'null'
        results['by_format'][fmt]['baseline']['total'] += 1
        results['by_format'][fmt]['miprov2']['total'] += 1
        results['by_format'][fmt]['gepa']['total'] += 1

        if base_correct:
            results['by_format'][fmt]['baseline']['correct'] += 1
        if mipro_correct:
            results['by_format'][fmt]['miprov2']['correct'] += 1
        if gepa_correct:
            results['by_format'][fmt]['gepa']['correct'] += 1

    logger.info("✅ Question-level comparison complete")
    return results


def print_analysis(results: Dict[str, Any], dev_set: List[dspy.Example]):
    """Print detailed error analysis."""
    print("\n" + "="*80)
    print("QUESTION-LEVEL ERROR ANALYSIS: Baseline vs MIPROv2 vs GEPA")
    print("="*80)

    total = len(dev_set)

    print(f"\n📊 Overall Performance ({total} questions):")
    print(f"   Baseline:  {len(results['baseline_correct']):2d}/{total} ({len(results['baseline_correct'])/total*100:.1f}%)")
    print(f"   MIPROv2:   {len(results['miprov2_correct']):2d}/{total} ({len(results['miprov2_correct'])/total*100:.1f}%)")
    print(f"   GEPA:      {len(results['gepa_correct']):2d}/{total} ({len(results['gepa_correct'])/total*100:.1f}%)")

    print(f"\n🔄 Question Patterns:")
    print(f"   All 3 correct:     {len(results['all_correct']):2d} questions")
    print(f"   All 3 wrong:       {len(results['all_wrong']):2d} questions")
    print(f"   Baseline only:     {len(results['baseline_only']):2d} questions")
    print(f"   MIPROv2 only:      {len(results['miprov2_only']):2d} questions")
    print(f"   GEPA only:         {len(results['gepa_only']):2d} questions")

    print(f"\n📉 Degradations from Baseline:")
    print(f"   MIPROv2: {len(results['miprov2_degraded']):2d} questions (right→wrong)")
    print(f"   GEPA:    {len(results['gepa_degraded']):2d} questions (right→wrong)")

    print(f"\n📈 Improvements over Baseline:")
    print(f"   MIPROv2: {len(results['miprov2_improved']):2d} questions (wrong→right)")
    print(f"   GEPA:    {len(results['gepa_improved']):2d} questions (wrong→right)")

    print(f"\n📋 Performance by Answer Format:")
    for fmt, data in results['by_format'].items():
        base_acc = data['baseline']['correct'] / data['baseline']['total'] * 100
        mipro_acc = data['miprov2']['correct'] / data['miprov2']['total'] * 100
        gepa_acc = data['gepa']['correct'] / data['gepa']['total'] * 100

        print(f"   {fmt:6s}: Base={base_acc:4.1f}%  MIPROv2={mipro_acc:4.1f}%  GEPA={gepa_acc:4.1f}%")

    # Show degradation examples
    if results['gepa_degraded']:
        print(f"\n❌ GEPA Degradation Examples (first 5):")
        for item in results['gepa_degraded'][:5]:
            print(f"\n   Q{item['idx']}: {item['question'][:80]}...")
            print(f"      GT:       {item['gt_answer']}")
            print(f"      Baseline: {item['baseline_pred']}")
            print(f"      GEPA:     {item['gepa_pred']}")
            print(f"      Type:     {item['answer_type']}")


def main():
    """Main execution."""
    print("\n" + "="*80)
    print("DEV SET COMPARISON: Baseline vs MIPROv2 vs GEPA")
    print("="*80)

    # Configure DSPy
    logger.info("🔧 Configuring DSPy with qwen2.5-7b-instruct...")
    dspy.configure(lm=dspy.LM('dashscope/qwen2.5-7b-instruct', api_key=Path('.env').read_text().strip().split('=')[1]))

    # Load dev set
    dev_set = load_dev_set()

    # Load baseline predictions
    baseline_predictions = load_baseline_predictions('dspy_baseline_dev_checkpoint.json')

    # Check if we need to complete baseline (90→93 questions)
    if len(baseline_predictions) < len(dev_set):
        logger.info(f"⚠️  Baseline has {len(baseline_predictions)}/93 questions, will evaluate missing ones")
        # TODO: Complete baseline if needed

    # Check if MIPROv2 predictions exist
    miprov2_predictions_path = Path("miprov2_dev_predictions.json")
    if miprov2_predictions_path.exists():
        logger.info("📦 Loading existing MIPROv2 predictions...")
        with open(miprov2_predictions_path, 'r') as f:
            miprov2_predictions = json.load(f)
    else:
        logger.info("🔄 Running MIPROv2 evaluation...")
        # Load MIPROv2 program (use most recent baseline_rag)
        miprov2_module = load_optimized_program(
            'dspy_implementation/optimized_modules/baseline_rag_20251015_134537.json',
            BaselineMMESGBenchRAG
        )
        miprov2_predictions = run_evaluation(miprov2_module, dev_set, "MIPROv2")

        # Save predictions
        with open(miprov2_predictions_path, 'w') as f:
            json.dump(miprov2_predictions, f, indent=2)
        logger.info(f"💾 Saved MIPROv2 predictions to {miprov2_predictions_path}")

    # Check if GEPA predictions exist
    gepa_predictions_path = Path("gepa_dev_predictions.json")
    if gepa_predictions_path.exists():
        logger.info("📦 Loading existing GEPA predictions...")
        with open(gepa_predictions_path, 'r') as f:
            gepa_predictions = json.load(f)
    else:
        logger.info("🔄 Running GEPA evaluation...")
        # Load GEPA program
        gepa_module = load_optimized_program(
            'dspy_implementation/optimized_programs/gepa_skip_baseline_20251018_150806.json',
            BaselineMMESGBenchRAG
        )
        gepa_predictions = run_evaluation(gepa_module, dev_set, "GEPA")

        # Save predictions
        with open(gepa_predictions_path, 'w') as f:
            json.dump(gepa_predictions, f, indent=2)
        logger.info(f"💾 Saved GEPA predictions to {gepa_predictions_path}")

    # Perform comparison
    results = compare_predictions(baseline_predictions, miprov2_predictions, gepa_predictions, dev_set)

    # Print analysis
    print_analysis(results, dev_set)

    # Save detailed results
    results_path = Path(f"dev_set_error_analysis_{timestamp}.json")
    with open(results_path, 'w') as f:
        # Convert to JSON-serializable format
        json_results = {
            'baseline_correct': results['baseline_correct'],
            'miprov2_correct': results['miprov2_correct'],
            'gepa_correct': results['gepa_correct'],
            'baseline_only': results['baseline_only'],
            'miprov2_only': results['miprov2_only'],
            'gepa_only': results['gepa_only'],
            'all_correct': results['all_correct'],
            'all_wrong': results['all_wrong'],
            'miprov2_degraded': results['miprov2_degraded'],
            'gepa_degraded': results['gepa_degraded'],
            'miprov2_improved': results['miprov2_improved'],
            'gepa_improved': results['gepa_improved'],
            'by_format': dict(results['by_format'])
        }
        json.dump(json_results, f, indent=2)

    logger.info(f"💾 Detailed results saved to {results_path}")
    logger.info(f"📋 Full log available at {log_file}")

    print("\n✅ Analysis complete!")


if __name__ == "__main__":
    main()
