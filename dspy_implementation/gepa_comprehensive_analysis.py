#!/usr/bin/env python3
"""
Comprehensive GEPA Analysis

Analyzes why GEPA performed worse than baseline and MIPROv2.
Compares prompts, error patterns, and question-level predictions.

User Questions to Answer:
1. Why is baseline so good without explicit prompts?
2. Did reflection prompts help? (They should...)
3. Dev set bias vs test set?
4. Right→Wrong and Wrong→Right analysis
"""

import os
import sys
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

import dspy
from tqdm import tqdm

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from dspy_implementation.dspy_dataset import MMESGBenchDataset
from dspy_implementation.dspy_rag_enhanced import BaselineMMESGBenchRAG
from dspy_implementation.dspy_metrics_enhanced import evaluate_predictions_enhanced
from MMESGBench.src.eval.eval_score import eval_score


def load_programs():
    """Load baseline, MIPROv2, and GEPA programs."""
    print("\n" + "="*80)
    print("LOADING PROGRAMS")
    print("="*80)

    programs = {}

    # 1. Baseline (no optimization - will create on-the-fly)
    print("\n📦 Baseline: Creating fresh BaselineMMESGBenchRAG...")
    programs['baseline'] = {
        'module': BaselineMMESGBenchRAG(),
        'source': 'fresh_initialization',
        'description': 'Baseline with default DSPy prompts (no optimization)'
    }

    # 2. MIPROv2 (teacher-student)
    mipro_path = "logs/qwen7b_test/teacher_student_qwen7b_results_20251016_230050.json"
    print(f"\n📦 MIPROv2: Loading from {mipro_path}...")

    if not os.path.exists(mipro_path):
        print(f"   ⚠️  File not found! Will skip MIPROv2 comparison")
        programs['miprov2'] = None
    else:
        with open(mipro_path) as f:
            mipro_data = json.load(f)
        print(f"   ✅ Loaded MIPROv2 results")
        print(f"      Answer accuracy: {mipro_data['dev_results']['answer_accuracy']:.1%}")
        programs['miprov2'] = {
            'results_data': mipro_data,
            'source': mipro_path,
            'description': 'MIPROv2 teacher-student optimization'
        }

    # 3. GEPA (reflection-based)
    gepa_path = "dspy_implementation/optimized_programs/gepa_skip_baseline_20251018_150806.json"
    print(f"\n📦 GEPA: Loading from {gepa_path}...")

    if not os.path.exists(gepa_path):
        print(f"   ⚠️  File not found! Will skip GEPA comparison")
        programs['gepa'] = None
    else:
        # Load GEPA module
        gepa_module = BaselineMMESGBenchRAG()
        gepa_module.load(gepa_path)

        # Extract prompts from loaded module
        gepa_prompts = {}
        if hasattr(gepa_module, 'reasoning') and hasattr(gepa_module.reasoning, 'predict'):
            sig = gepa_module.reasoning.predict.signature
            if hasattr(sig, 'instructions'):
                gepa_prompts['reasoning'] = sig.instructions

        if hasattr(gepa_module, 'extraction') and hasattr(gepa_module.extraction, 'signature'):
            sig = gepa_module.extraction.signature
            if hasattr(sig, 'instructions'):
                gepa_prompts['extraction'] = sig.instructions

        print(f"   ✅ Loaded GEPA module")
        print(f"      Extracted {len(gepa_prompts)} prompts")

        programs['gepa'] = {
            'module': gepa_module,
            'prompts': gepa_prompts,
            'source': gepa_path,
            'description': 'GEPA reflection-based optimization'
        }

    return programs


def extract_baseline_prompts(baseline_module):
    """Extract prompts from baseline module."""
    prompts = {}

    # Reasoning stage
    if hasattr(baseline_module, 'reasoning'):
        if hasattr(baseline_module.reasoning, 'signature'):
            sig = baseline_module.reasoning.signature
            if hasattr(sig, 'instructions'):
                prompts['reasoning'] = sig.instructions
            elif hasattr(sig, '__doc__'):
                prompts['reasoning'] = sig.__doc__ or "No instructions"
            else:
                prompts['reasoning'] = "Default DSPy ChainOfThought prompt"

    # Extraction stage
    if hasattr(baseline_module, 'extraction'):
        if hasattr(baseline_module.extraction, 'signature'):
            sig = baseline_module.extraction.signature
            if hasattr(sig, 'instructions'):
                prompts['extraction'] = sig.instructions
            elif hasattr(sig, '__doc__'):
                prompts['extraction'] = sig.__doc__ or "No instructions"
            else:
                prompts['extraction'] = "Default DSPy Predict prompt"

    return prompts


def compare_prompts(programs):
    """Compare prompts across baseline, MIPROv2, and GEPA."""
    print("\n" + "="*80)
    print("PROMPT COMPARISON")
    print("="*80)

    # Extract baseline prompts
    print("\n📝 Extracting baseline prompts...")
    baseline_prompts = extract_baseline_prompts(programs['baseline']['module'])

    # GEPA prompts already extracted
    gepa_prompts = programs['gepa']['prompts'] if programs['gepa'] else {}

    # Compare reasoning prompts
    print("\n" + "-"*80)
    print("REASONING STAGE PROMPTS")
    print("-"*80)

    print("\n🔵 BASELINE Reasoning Prompt:")
    print(baseline_prompts.get('reasoning', 'NOT FOUND')[:500] + "...")

    if programs['gepa']:
        print("\n🟢 GEPA Reasoning Prompt:")
        gepa_reasoning = gepa_prompts.get('reasoning', 'NOT FOUND')
        print(gepa_reasoning[:500] + "...")
        print(f"\n   Length: Baseline={len(baseline_prompts.get('reasoning', ''))} chars, "
              f"GEPA={len(gepa_reasoning)} chars")

    # Compare extraction prompts
    print("\n" + "-"*80)
    print("EXTRACTION STAGE PROMPTS")
    print("-"*80)

    print("\n🔵 BASELINE Extraction Prompt:")
    print(baseline_prompts.get('extraction', 'NOT FOUND')[:500] + "...")

    if programs['gepa']:
        print("\n🟢 GEPA Extraction Prompt:")
        gepa_extraction = gepa_prompts.get('extraction', 'NOT FOUND')
        print(gepa_extraction[:500] + "...")
        print(f"\n   Length: Baseline={len(baseline_prompts.get('extraction', ''))} chars, "
              f"GEPA={len(gepa_extraction)} chars")

    # Save detailed comparison
    comparison = {
        'baseline': baseline_prompts,
        'gepa': gepa_prompts,
        'analysis': {
            'reasoning_length_baseline': len(baseline_prompts.get('reasoning', '')),
            'reasoning_length_gepa': len(gepa_prompts.get('reasoning', '')),
            'extraction_length_baseline': len(baseline_prompts.get('extraction', '')),
            'extraction_length_gepa': len(gepa_prompts.get('extraction', ''))
        }
    }

    return comparison


def evaluate_program(module, dataset, desc="Evaluation"):
    """Evaluate a DSPy module on dataset."""
    predictions = []

    for example in tqdm(dataset, desc=desc):
        try:
            pred = module(
                question=example.question,
                doc_id=example.doc_id,
                answer_format=example.answer_format
            )
            predictions.append(pred)
        except Exception as e:
            print(f"\n⚠️  Error on question: {e}")
            predictions.append(dspy.Prediction(answer="Failed"))

    # Compute metrics
    results = evaluate_predictions_enhanced(predictions, dataset)

    # Add question-level results
    question_results = []
    for i, (pred, example) in enumerate(zip(predictions, dataset)):
        score = eval_score(
            example.answer,
            pred.answer,
            example.answer_format
        )
        question_results.append({
            'question_id': i,
            'question': example.question[:100],
            'doc_id': example.doc_id,
            'format': example.answer_format,
            'ground_truth': example.answer,
            'prediction': pred.answer,
            'score': score,
            'correct': score >= 0.5
        })

    return results, question_results


def analyze_transitions(baseline_results, gepa_results):
    """Analyze right→wrong and wrong→right transitions."""
    print("\n" + "="*80)
    print("PREDICTION TRANSITION ANALYSIS")
    print("="*80)

    right_to_wrong = []
    wrong_to_right = []
    both_right = []
    both_wrong = []

    for i, (b, g) in enumerate(zip(baseline_results, gepa_results)):
        baseline_correct = b['correct']
        gepa_correct = g['correct']

        if baseline_correct and not gepa_correct:
            right_to_wrong.append((i, b, g))
        elif not baseline_correct and gepa_correct:
            wrong_to_right.append((i, b, g))
        elif baseline_correct and gepa_correct:
            both_right.append((i, b, g))
        else:
            both_wrong.append((i, b, g))

    print(f"\n📊 Transition Summary:")
    print(f"   ✅→✅ Both Correct: {len(both_right)}")
    print(f"   ❌→❌ Both Wrong: {len(both_wrong)}")
    print(f"   ✅→❌ Right → Wrong (DEGRADATION): {len(right_to_wrong)} ⚠️")
    print(f"   ❌→✅ Wrong → Right (IMPROVEMENT): {len(wrong_to_right)} 🎉")

    # Detailed analysis of degradations
    if right_to_wrong:
        print(f"\n" + "-"*80)
        print(f"DEGRADATION CASES (Baseline Right → GEPA Wrong): {len(right_to_wrong)}")
        print("-"*80)

        for i, (qid, baseline, gepa) in enumerate(right_to_wrong[:5], 1):
            print(f"\n{i}. Question {qid}:")
            print(f"   Q: {baseline['question']}")
            print(f"   Format: {baseline['format']}")
            print(f"   Ground Truth: {baseline['ground_truth']}")
            print(f"   Baseline (✅): {baseline['prediction']} (score={baseline['score']:.2f})")
            print(f"   GEPA (❌): {gepa['prediction']} (score={gepa['score']:.2f})")

    # Detailed analysis of improvements
    if wrong_to_right:
        print(f"\n" + "-"*80)
        print(f"IMPROVEMENT CASES (Baseline Wrong → GEPA Right): {len(wrong_to_right)}")
        print("-"*80)

        for i, (qid, baseline, gepa) in enumerate(wrong_to_right[:5], 1):
            print(f"\n{i}. Question {qid}:")
            print(f"   Q: {baseline['question']}")
            print(f"   Format: {baseline['format']}")
            print(f"   Ground Truth: {baseline['ground_truth']}")
            print(f"   Baseline (❌): {baseline['prediction']} (score={baseline['score']:.2f})")
            print(f"   GEPA (✅): {gepa['prediction']} (score={gepa['score']:.2f})")

    return {
        'both_right': both_right,
        'both_wrong': both_wrong,
        'right_to_wrong': right_to_wrong,
        'wrong_to_right': wrong_to_right
    }


def main():
    print("\n" + "="*80)
    print("GEPA COMPREHENSIVE ANALYSIS")
    print("="*80)
    print("\nResearch Questions:")
    print("1. Why is baseline so good without explicit prompts?")
    print("2. Did reflection prompts help?")
    print("3. Dev set bias vs test set?")
    print("4. What are the right→wrong and wrong→right patterns?")

    # Load dataset
    print("\n📊 Loading dataset...")
    dataset = MMESGBenchDataset()
    dev_set = dataset.dev_set
    print(f"   Dev set: {len(dev_set)} examples")

    # Configure DSPy
    print("\n🔧 Configuring DSPy with qwen2.5-7b-instruct...")
    student_lm = dspy.LM(
        model='openai/qwen2.5-7b-instruct',
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        api_base='https://dashscope.aliyuncs.com/compatible-mode/v1',
        temperature=0.0,
        max_tokens=1024
    )
    dspy.configure(lm=student_lm)

    # Load programs
    programs = load_programs()

    # Compare prompts
    prompt_comparison = compare_prompts(programs)

    # Evaluate baseline (re-run for question-level results)
    print("\n" + "="*80)
    print("EVALUATING BASELINE")
    print("="*80)
    baseline_metrics, baseline_questions = evaluate_program(
        programs['baseline']['module'],
        dev_set,
        "Baseline evaluation"
    )
    print(f"\n📈 Baseline Results:")
    print(f"   Answer Accuracy: {baseline_metrics['answer_accuracy']:.1%}")

    # Evaluate GEPA
    if programs['gepa']:
        print("\n" + "="*80)
        print("EVALUATING GEPA")
        print("="*80)
        gepa_metrics, gepa_questions = evaluate_program(
            programs['gepa']['module'],
            dev_set,
            "GEPA evaluation"
        )
        print(f"\n📈 GEPA Results:")
        print(f"   Answer Accuracy: {gepa_metrics['answer_accuracy']:.1%}")

        # Analyze transitions
        transitions = analyze_transitions(baseline_questions, gepa_questions)

        # Generate report
        report = {
            'timestamp': datetime.now().isoformat(),
            'dataset': {
                'split': 'dev',
                'size': len(dev_set)
            },
            'results': {
                'baseline': baseline_metrics,
                'gepa': gepa_metrics,
                'miprov2': programs['miprov2']['results_data']['dev_results'] if programs['miprov2'] else None
            },
            'prompts': prompt_comparison,
            'transitions': {
                'both_right': len(transitions['both_right']),
                'both_wrong': len(transitions['both_wrong']),
                'degradations': len(transitions['right_to_wrong']),
                'improvements': len(transitions['wrong_to_right'])
            },
            'question_level': {
                'baseline': baseline_questions,
                'gepa': gepa_questions
            }
        }

        # Save report
        output_file = f"gepa_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n💾 Saved detailed report to: {output_file}")

        # Final summary
        print("\n" + "="*80)
        print("ANALYSIS SUMMARY")
        print("="*80)

        print("\n📊 Performance Comparison:")
        print(f"   Baseline:  {baseline_metrics['answer_accuracy']:.1%}")
        print(f"   GEPA:      {gepa_metrics['answer_accuracy']:.1%}")
        print(f"   Change:    {(gepa_metrics['answer_accuracy'] - baseline_metrics['answer_accuracy'])*100:+.1f}%")

        if programs['miprov2']:
            mipro_acc = programs['miprov2']['results_data']['dev_results']['answer_accuracy']
            print(f"   MIPROv2:   {mipro_acc:.1%}")

        print("\n🔍 Key Findings:")
        print(f"   • GEPA degraded {len(transitions['right_to_wrong'])} questions")
        print(f"   • GEPA improved {len(transitions['wrong_to_right'])} questions")
        print(f"   • Net change: {len(transitions['wrong_to_right']) - len(transitions['right_to_wrong'])} questions")

        print(f"\n📁 Detailed results saved to: {output_file}")
        print(f"\n✅ Analysis complete!")

        return report


if __name__ == "__main__":
    main()
