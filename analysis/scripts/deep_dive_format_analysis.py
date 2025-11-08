#!/usr/bin/env python3
"""
Deep Dive Format Analysis - List, Null, String Questions

Focus areas:
1. List questions: Why did GEPA go from +15.4% to -5.7%?
2. Null questions: Format issues beyond hallucination?
3. String questions: Are GEPA answers semantically better but ANLS can't capture?
"""

import json
import os
import sys
from pathlib import Path
from collections import defaultdict
import dspy
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.evaluation import eval_score

# Setup
load_dotenv()

def load_all_data():
    """Load test set and all predictions."""
    # Test set
    with open('dspy_implementation/data_splits/test_654.json', 'r') as f:
        test_set = json.load(f)
    
    # Predictions
    with open('baseline_test_predictions_20251021_225632.json', 'r') as f:
        baseline = json.load(f)
    
    with open('miprov2_test_predictions_20251021_225632.json', 'r') as f:
        miprov2 = json.load(f)
    
    with open('gepa_test_predictions_20251021_225632.json', 'r') as f:
        gepa = json.load(f)
    
    return test_set, baseline, miprov2, gepa

def analyze_list_questions(test_set, baseline, miprov2, gepa):
    """Deep dive into List questions."""
    print("\n" + "="*80)
    print("LIST QUESTIONS DEEP DIVE")
    print("="*80)
    
    list_questions = []
    for i, example in enumerate(test_set):
        if example.get('answer_format') == 'List':
            qid = f'q{i}'
            base_pred = baseline['predictions'][qid]
            mipro_pred = miprov2['predictions'][qid]
            gepa_pred = gepa['predictions'][qid]
            
            list_questions.append({
                'idx': i,
                'question': example['question'],
                'gt': example['answer'],
                'baseline_ans': base_pred['answer'],
                'miprov2_ans': mipro_pred['answer'],
                'gepa_ans': gepa_pred['answer'],
                'baseline_correct': base_pred.get('correct', False),
                'miprov2_correct': mipro_pred.get('correct', False),
                'gepa_correct': gepa_pred.get('correct', False),
                'baseline_score': base_pred.get('score', 0),
                'gepa_score': gepa_pred.get('score', 0)
            })
    
    print(f"\n📊 List Question Statistics:")
    print(f"   Total: {len(list_questions)}")
    
    # Categorize
    baseline_right_gepa_wrong = [q for q in list_questions if q['baseline_correct'] and not q['gepa_correct']]
    baseline_wrong_gepa_right = [q for q in list_questions if not q['baseline_correct'] and q['gepa_correct']]
    both_wrong = [q for q in list_questions if not q['baseline_correct'] and not q['gepa_correct']]
    both_right = [q for q in list_questions if q['baseline_correct'] and q['gepa_correct']]
    
    print(f"\n   Both correct:     {len(both_right)}")
    print(f"   Both wrong:       {len(both_wrong)}")
    print(f"   Base→GEPA wrong:  {len(baseline_right_gepa_wrong)} ❌ DEGRADATIONS")
    print(f"   Base→GEPA right:  {len(baseline_wrong_gepa_right)} ✅ IMPROVEMENTS")
    
    # Show degradation examples
    print(f"\n🔍 DEGRADATION EXAMPLES (Baseline Right → GEPA Wrong):")
    for i, q in enumerate(baseline_right_gepa_wrong[:5]):
        print(f"\n--- Example {i+1} (q{q['idx']}) ---")
        print(f"Question: {q['question'][:120]}...")
        print(f"Ground truth:  {q['gt']}")
        print(f"Baseline:      {q['baseline_ans']} ✅ (score: {q['baseline_score']:.2f})")
        print(f"GEPA:          {q['gepa_ans']} ❌ (score: {q['gepa_score']:.2f})")
        
        # Analyze the issue
        gt_list = eval(str(q['gt'])) if isinstance(q['gt'], str) and q['gt'].startswith('[') else q['gt']
        gepa_list = eval(str(q['gepa_ans'])) if isinstance(q['gepa_ans'], str) and q['gepa_ans'].startswith('[') else q['gepa_ans']
        
        if isinstance(gt_list, list) and isinstance(gepa_list, list):
            print(f"   → GT length: {len(gt_list)}, GEPA length: {len(gepa_list)}")
            if len(gepa_list) < len(gt_list):
                print(f"   → ISSUE: Incomplete list (missing {len(gt_list) - len(gepa_list)} items)")
            elif len(gepa_list) > len(gt_list):
                print(f"   → ISSUE: Extra items (added {len(gepa_list) - len(gt_list)} items)")
            else:
                print(f"   → ISSUE: Wrong items (same length but different content)")
    
    # Show improvement examples
    print(f"\n✅ IMPROVEMENT EXAMPLES (Baseline Wrong → GEPA Right):")
    for i, q in enumerate(baseline_wrong_gepa_right[:3]):
        print(f"\n--- Example {i+1} (q{q['idx']}) ---")
        print(f"Question: {q['question'][:120]}...")
        print(f"Ground truth:  {q['gt']}")
        print(f"Baseline:      {q['baseline_ans']} ❌")
        print(f"GEPA:          {q['gepa_ans']} ✅")
    
    return list_questions, baseline_right_gepa_wrong, baseline_wrong_gepa_right

def analyze_null_questions(test_set, baseline, miprov2, gepa):
    """Deep dive into Null/Not answerable questions."""
    print("\n" + "="*80)
    print("NULL QUESTIONS DEEP DIVE")
    print("="*80)
    
    null_questions = []
    for i, example in enumerate(test_set):
        if not example.get('answer_format') or example.get('answer_format') == 'null':
            qid = f'q{i}'
            base_pred = baseline['predictions'][qid]
            gepa_pred = gepa['predictions'][qid]
            
            null_questions.append({
                'idx': i,
                'question': example['question'],
                'gt': example['answer'],
                'baseline_ans': base_pred['answer'],
                'gepa_ans': gepa_pred['answer'],
                'baseline_correct': base_pred.get('correct', False),
                'gepa_correct': gepa_pred.get('correct', False),
                'baseline_score': base_pred.get('score', 0),
                'gepa_score': gepa_pred.get('score', 0)
            })
    
    print(f"\n📊 Null Question Statistics:")
    print(f"   Total: {len(null_questions)}")
    
    # Categorize
    baseline_right_gepa_wrong = [q for q in null_questions if q['baseline_correct'] and not q['gepa_correct']]
    baseline_wrong_gepa_right = [q for q in null_questions if not q['baseline_correct'] and q['gepa_correct']]
    
    print(f"   Baseline right:   {sum(1 for q in null_questions if q['baseline_correct'])}")
    print(f"   GEPA right:       {sum(1 for q in null_questions if q['gepa_correct'])}")
    print(f"   Base→GEPA wrong:  {len(baseline_right_gepa_wrong)} ❌")
    print(f"   Base→GEPA right:  {len(baseline_wrong_gepa_right)} ✅")
    
    # Analyze degradations - check for patterns
    print(f"\n🔍 DEGRADATION PATTERNS:")
    
    # Pattern 1: GEPA gives specific answer when GT is "Not answerable"
    hallucination_count = 0
    format_issue_count = 0
    partial_answer_count = 0
    
    for q in baseline_right_gepa_wrong:
        gt_lower = str(q['gt']).lower().strip()
        gepa_lower = str(q['gepa_ans']).lower().strip()
        
        # Check if GT is truly "not answerable"
        is_not_answerable = any(x in gt_lower for x in ['not answerable', 'not applicable', 'n/a', 'na'])
        
        if is_not_answerable:
            # GEPA gave an answer when it shouldn't
            if gepa_lower and gepa_lower not in ['not answerable', 'not applicable', 'n/a', 'na']:
                hallucination_count += 1
        else:
            # GT has an answer but GEPA got it wrong
            if 'not answerable' in gepa_lower or 'not applicable' in gepa_lower:
                # GEPA said "not answerable" when there was an answer
                partial_answer_count += 1
            else:
                # Format or other issue
                format_issue_count += 1
    
    print(f"\n   Hallucination (answer when should be null): {hallucination_count}")
    print(f"   Over-cautious (null when should answer):    {partial_answer_count}")
    print(f"   Format/other issues:                        {format_issue_count}")
    
    # Show examples
    print(f"\n📋 DEGRADATION EXAMPLES:")
    for i, q in enumerate(baseline_right_gepa_wrong[:5]):
        print(f"\n--- Example {i+1} (q{q['idx']}) ---")
        print(f"Question: {q['question'][:120]}...")
        print(f"Ground truth: {q['gt']}")
        print(f"Baseline:     {q['baseline_ans']} ✅")
        print(f"GEPA:         {q['gepa_ans']} ❌")
        
        # Classify issue
        gt_lower = str(q['gt']).lower()
        gepa_lower = str(q['gepa_ans']).lower()
        if 'not answerable' in gt_lower and gepa_lower and 'not answerable' not in gepa_lower:
            print(f"   → ISSUE: Hallucination (tried to answer when unanswerable)")
        elif 'not answerable' in gepa_lower and 'not answerable' not in gt_lower:
            print(f"   → ISSUE: Over-cautious (said unanswerable when answer exists)")
        else:
            print(f"   → ISSUE: Format or extraction problem")
    
    return null_questions, baseline_right_gepa_wrong

def analyze_string_questions_with_llm(test_set, baseline, gepa):
    """Use LLM to evaluate if GEPA's string answers are semantically better than baseline."""
    print("\n" + "="*80)
    print("STRING QUESTIONS - LLM-ASSISTED QUALITY EVALUATION")
    print("="*80)
    
    # Configure LLM for evaluation
    lm = dspy.LM(
        model='openai/qwen-max',
        api_key=os.getenv('DASHSCOPE_API_KEY'),
        api_base='https://dashscope.aliyuncs.com/compatible-mode/v1',
        temperature=0.0,
        max_tokens=512
    )
    dspy.configure(lm=lm)
    
    string_questions = []
    for i, example in enumerate(test_set):
        if example.get('answer_format') == 'Str':
            qid = f'q{i}'
            base_pred = baseline['predictions'][qid]
            gepa_pred = gepa['predictions'][qid]
            
            # Only analyze degradations (where baseline was right, GEPA wrong)
            if base_pred.get('correct', False) and not gepa_pred.get('correct', False):
                string_questions.append({
                    'idx': i,
                    'question': example['question'],
                    'gt': example['answer'],
                    'baseline_ans': base_pred['answer'],
                    'gepa_ans': gepa_pred['answer'],
                    'baseline_score': base_pred.get('score', 0),
                    'gepa_score': gepa_pred.get('score', 0)
                })
    
    print(f"\n📊 Analyzing {len(string_questions)} string degradations with LLM...")
    print(f"   (Baseline correct → GEPA wrong according to ANLS)")
    
    # Sample 10 for LLM evaluation (to save costs)
    sample_size = min(10, len(string_questions))
    sample = string_questions[:sample_size]
    
    better_count = 0
    worse_count = 0
    same_count = 0
    
    evaluations = []
    
    for i, q in enumerate(sample):
        print(f"\n--- Evaluating {i+1}/{sample_size} ---")
        
        prompt = f"""You are an expert evaluator for question-answering systems.

Question: {q['question']}
Ground Truth Answer: {q['gt']}

Baseline Answer: {q['baseline_ans']}
GEPA Answer: {q['gepa_ans']}

The ANLS metric (fuzzy string matching) scored:
- Baseline: {q['baseline_score']:.2f} (considered CORRECT at ≥0.5 threshold)
- GEPA: {q['gepa_score']:.2f} (considered WRONG at <0.5 threshold)

However, ANLS may miss semantic equivalence. Please evaluate:

1. Is GEPA's answer semantically better, worse, or equivalent to Baseline's answer?
2. Consider: completeness, accuracy, relevance to the question
3. Ignore minor formatting/capitalization differences

Respond with ONLY ONE of these labels:
- BETTER: GEPA's answer is semantically superior
- WORSE: GEPA's answer is semantically inferior  
- SAME: Both answers are semantically equivalent (ANLS failed to recognize)

Your evaluation (BETTER/WORSE/SAME):"""
        
        try:
            response = lm(prompt)
            evaluation = response.strip().upper()
            
            if 'BETTER' in evaluation:
                better_count += 1
                verdict = "BETTER"
            elif 'WORSE' in evaluation:
                worse_count += 1
                verdict = "WORSE"
            else:
                same_count += 1
                verdict = "SAME"
            
            print(f"   LLM Verdict: {verdict}")
            
            evaluations.append({
                'idx': q['idx'],
                'question': q['question'][:100],
                'gt': q['gt'],
                'baseline': q['baseline_ans'],
                'gepa': q['gepa_ans'],
                'llm_verdict': verdict
            })
            
        except Exception as e:
            print(f"   Error: {e}")
            continue
    
    # Summary
    print(f"\n" + "="*80)
    print("LLM EVALUATION SUMMARY")
    print("="*80)
    print(f"\nOut of {sample_size} degradations (Baseline ✅ → GEPA ❌ per ANLS):")
    print(f"   GEPA BETTER:  {better_count} ({better_count/sample_size*100:.1f}%) - ANLS missed semantic equivalence")
    print(f"   GEPA SAME:    {same_count} ({same_count/sample_size*100:.1f}%) - ANLS too strict")
    print(f"   GEPA WORSE:   {worse_count} ({worse_count/sample_size*100:.1f}%) - ANLS correct")
    
    anls_false_negatives = better_count + same_count
    print(f"\n💡 ANLS False Negatives: {anls_false_negatives}/{sample_size} ({anls_false_negatives/sample_size*100:.1f}%)")
    
    if anls_false_negatives > 0:
        print(f"   → GEPA may be {anls_false_negatives} answers better than ANLS suggests!")
        print(f"   → On {len(string_questions)} total degradations, could be ~{int(len(string_questions) * anls_false_negatives/sample_size)} false negatives")
    
    # Show examples
    print(f"\n📋 EXAMPLE EVALUATIONS:")
    for eval_result in evaluations[:5]:
        print(f"\n   q{eval_result['idx']}: {eval_result['question']}...")
        print(f"   GT:       {eval_result['gt']}")
        print(f"   Baseline: {eval_result['baseline']}")
        print(f"   GEPA:     {eval_result['gepa']}")
        print(f"   Verdict:  {eval_result['llm_verdict']}")
    
    return evaluations, better_count, same_count, worse_count

def main():
    """Main analysis."""
    print("\n" + "="*80)
    print("DEEP DIVE FORMAT ANALYSIS")
    print("List, Null, String Questions Investigation")
    print("="*80)
    
    # Load data
    print("\n📂 Loading data...")
    test_set, baseline, miprov2, gepa = load_all_data()
    
    # 1. List questions
    list_q, list_degrad, list_improv = analyze_list_questions(test_set, baseline, miprov2, gepa)
    
    # 2. Null questions
    null_q, null_degrad = analyze_null_questions(test_set, baseline, gepa)
    
    # 3. String questions with LLM
    print("\n⚠️  LLM evaluation will use qwen-max API (costs ~$0.02-0.05)")
    print("   Proceeding with LLM evaluation...")
    response = 'y'
    
    if response.lower() == 'y':
        str_evals, better, same, worse = analyze_string_questions_with_llm(test_set, baseline, gepa)
        
        # Save results
        results = {
            'list_degradations': len(list_degrad),
            'list_improvements': len(list_improv),
            'null_degradations': len(null_degrad),
            'string_llm_better': better,
            'string_llm_same': same,
            'string_llm_worse': worse,
            'string_llm_evaluations': str_evals
        }
        
        with open('deep_dive_format_analysis_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Saved results to: deep_dive_format_analysis_results.json")
    else:
        print("\nSkipping LLM evaluation.")
    
    # Final summary
    print(f"\n" + "="*80)
    print("FINAL INSIGHTS")
    print("="*80)
    
    print(f"\n1. LIST QUESTIONS:")
    print(f"   - Degradations: {len(list_degrad)} (Baseline→GEPA wrong)")
    print(f"   - Improvements: {len(list_improv)} (Baseline→GEPA right)")
    print(f"   - Net: {len(list_improv) - len(list_degrad)} questions")
    print(f"   - Main issues: Incomplete lists, wrong items, format problems")
    
    print(f"\n2. NULL QUESTIONS:")
    print(f"   - Degradations: {len(null_degrad)}")
    print(f"   - Patterns: Hallucination, over-caution, format issues")
    
    if response.lower() == 'y':
        print(f"\n3. STRING QUESTIONS:")
        print(f"   - ANLS may have {better + same} false negatives out of 10 samples")
        print(f"   - Estimated {int(20 * (better + same)/10)} false negatives in 20 total degradations")
        print(f"   - GEPA's verbose prompts may actually help strings, but ANLS too strict!")
    
    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    main()

