#!/usr/bin/env python3
"""
Dev Set Comparison with Improved Error Handling
Tests if DashScope API limits persist, with option to switch models
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
log_dir = Path("logs/error_analysis")
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"comparison_{timestamp}.log"

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


def load_baseline_predictions(checkpoint_path: str) -> Dict[str, Any]:
    """Load existing baseline predictions."""
    logger.info(f"📦 Loading baseline predictions from {checkpoint_path}")
    with open(checkpoint_path, 'r') as f:
        data = json.load(f)
    predictions = data.get('predictions', [])
    logger.info(f"✅ Loaded {len(predictions)} baseline predictions")
    return {f"q{i}": pred['_store'] for i, pred in enumerate(predictions)}


def load_dev_set() -> List[dspy.Example]:
    """Load dev set."""
    logger.info("📊 Loading dev set...")
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
                'success': True
            }
        except Exception as e:
            if "Connection" in str(e) or "rate" in str(e).lower():
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"API error (attempt {attempt+1}/{max_retries}), waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Max retries exceeded: {e}")
                    return {'answer': 'ERROR', 'analysis': str(e), 'success': False}
            else:
                logger.error(f"Error: {e}")
                return {'answer': 'ERROR', 'analysis': str(e), 'success': False}
    return {'answer': 'ERROR', 'analysis': 'Unknown error', 'success': False}


def test_model_availability(model_name: str) -> bool:
    """Test if model is accessible."""
    logger.info(f"🧪 Testing model: {model_name}")
    try:
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

        # Simple test
        class SimpleQA(dspy.Signature):
            question: str = dspy.InputField()
            answer: str = dspy.OutputField()

        predictor = dspy.Predict(SimpleQA)
        result = predictor(question="What is 2+2?")

        logger.info(f"✅ Model {model_name} is accessible")
        logger.info(f"   Test response: {result.answer}")
        return True

    except Exception as e:
        logger.error(f"❌ Model {model_name} test failed: {e}")
        return False


def run_limited_evaluation(model_name: str, num_questions: int = 10):
    """Run evaluation on limited questions to test API stability."""
    logger.info(f"\n{'='*80}")
    logger.info(f"TESTING API WITH {model_name.upper()} ({num_questions} questions)")
    logger.info(f"{'='*80}\n")

    # Configure model
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

    # Load data
    dev_set = load_dev_set()
    baseline_preds = load_baseline_predictions('dspy_baseline_dev_checkpoint.json')

    # Load saved program
    logger.info("📦 Loading MIPROv2 optimized program...")
    module = BaselineMMESGBenchRAG()
    module.load('dspy_implementation/optimized_modules/baseline_rag_20251015_134537.json')
    logger.info("✅ Module loaded")

    # Run limited evaluation
    results = {
        'success_count': 0,
        'error_count': 0,
        'connection_errors': 0,
        'predictions': {},
        'timings': []
    }

    for i in tqdm(range(min(num_questions, len(dev_set))), desc=f"Testing {model_name}"):
        example = dev_set[i]

        start_time = time.time()
        pred = evaluate_single(module, example)
        elapsed = time.time() - start_time

        results['predictions'][f'q{i}'] = pred
        results['timings'].append(elapsed)

        if pred['success']:
            results['success_count'] += 1
        else:
            results['error_count'] += 1
            if 'Connection' in pred['analysis']:
                results['connection_errors'] += 1

    # Print results
    avg_time = sum(results['timings']) / len(results['timings']) if results['timings'] else 0

    print(f"\n{'='*80}")
    print(f"RESULTS FOR {model_name.upper()}")
    print(f"{'='*80}")
    print(f"Questions evaluated: {num_questions}")
    print(f"Successful: {results['success_count']}/{num_questions} ({results['success_count']/num_questions*100:.1f}%)")
    print(f"Errors: {results['error_count']}/{num_questions}")
    print(f"Connection errors: {results['connection_errors']}/{num_questions}")
    print(f"Average time: {avg_time:.1f}s per question")
    print(f"{'='*80}\n")

    return results


def main():
    """Main execution."""
    # Test models
    models_to_test = [
        'qwen2.5-7b-instruct',   # Current model
        'qwen-max',              # Larger model (might have higher limits)
        'qwen2.5-14b-instruct',  # Middle-sized model
    ]

    print("\n" + "="*80)
    print("DEV SET COMPARISON - MODEL TESTING")
    print("="*80)
    print("\nTesting DashScope API stability with different models...")
    print("Will evaluate 10 questions with each model to test API limits\n")

    all_results = {}

    for model in models_to_test:
        # Test if model is available
        if not test_model_availability(model):
            logger.warning(f"⚠️  Skipping {model} - not available")
            continue

        # Run limited evaluation
        try:
            results = run_limited_evaluation(model, num_questions=10)
            all_results[model] = results

            # If this model works well, ask user if they want to continue
            if results['success_count'] >= 8:  # 80% success rate
                logger.info(f"✅ {model} is working well!")
                print(f"\n✅ Model {model} is stable (80%+ success rate)")
                print(f"Continue with full evaluation using {model}? (This will take ~2 hours)")

                # Save partial results
                with open(f'api_test_{model.replace(".", "_")}_{timestamp}.json', 'w') as f:
                    json.dump(all_results, f, indent=2)

                break
            else:
                logger.warning(f"⚠️  {model} has connection issues, trying next model...")
                time.sleep(5)  # Wait before trying next model

        except Exception as e:
            logger.error(f"❌ Error testing {model}: {e}")
            continue

    # Summary
    print("\n" + "="*80)
    print("API TESTING SUMMARY")
    print("="*80)
    for model, results in all_results.items():
        success_rate = results['success_count'] / 10 * 100
        print(f"{model:30s}: {success_rate:5.1f}% success, {results['connection_errors']} connection errors")
    print("="*80)

    logger.info(f"📋 Results saved to api_test_*_{timestamp}.json")


if __name__ == "__main__":
    main()
