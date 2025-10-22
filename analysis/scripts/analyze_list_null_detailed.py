#!/usr/bin/env python3
"""
Detailed analysis of List and Null questions (no LLM needed)
"""

import json
from collections import defaultdict

def load_all_data():
    """Load test set and all predictions."""
    with open('dspy_implementation/data_splits/test_654.json', 'r') as f:
        test_set = json.load(f)
    
    with open('baseline_test_predictions_20251021_225632.json', 'r') as f:
        baseline = json.load(f)
    
    with open('gepa_test_predictions_20251021_225632.json', 'r') as f:
        gepa = json.load(f)
    
    return test_set, baseline, gepa

def analyze_list_questions():
    """Deep dive into List questions."""
    test_set, baseline, gepa = load_all_data()
    
    print("\n" + "="*80)
    print("LIST QUESTIONS DEEP DIVE (88 questions)")
    print("="*80)
    
    list_degradations = []
    list_improvements = []
    
    for i, example in enumerate(test_set):
        if example.get('answer_format') == 'List':
            qid = f'q{i}'
            base_pred = baseline['predictions'][qid]
            gepa_pred = gepa['predictions'][qid]
            
            base_correct = base_pred.get('correct', False)
            gepa_correct = gepa_pred.get('correct', False)
            
            if base_correct and not gepa_correct:
                list_degradations.append({
                    'idx': i,
                    'question': example['question'],
                    'gt': example['answer'],
                    'baseline': base_pred['answer'],
                    'gepa': gepa_pred['answer'],
                    'baseline_score': base_pred.get('score', 0),
                    'gepa_score': gepa_pred.get('score', 0)
                })
            elif not base_correct and gepa_correct:
                list_improvements.append({
                    'idx': i,
                    'question': example['question'],
                    'gt': example['answer'],
                    'baseline': base_pred['answer'],
                    'gepa': gepa_pred['answer']
                })
    
    print(f"\n📊 Summary:")
    print(f"   Degradations (Base✅ → GEPA❌): {len(list_degradations)}")
    print(f"   Improvements (Base❌ → GEPA✅): {len(list_improvements)}")
    print(f"   Net impact: {len(list_improvements) - len(list_degradations)}")
    
    print(f"\n❌ DEGRADATION EXAMPLES:")
    for i, q in enumerate(list_degradations):
        print(f"\n--- Example {i+1} (q{q['idx']}) ---")
        print(f"Question: {q['question']}")
        print(f"\nGround truth:  {q['gt']}")
        print(f"Baseline:      {q['baseline']} ✅ (score: {q['baseline_score']:.2f})")
        print(f"GEPA:          {q['gepa']} ❌ (score: {q['gepa_score']:.2f})")
        
        # Try to analyze the issue
        try:
            gt_str = str(q['gt'])
            gepa_str = str(q['gepa'])
            
            # Check list length
            if isinstance(q['gt'], list) and isinstance(q['gepa'], list):
                gt_len = len(q['gt'])
                gepa_len = len(q['gepa'])
                print(f"\nAnalysis:")
                print(f"   GT items: {gt_len}, GEPA items: {gepa_len}")
                if gepa_len < gt_len:
                    print(f"   → Missing {gt_len - gepa_len} items")
                elif gepa_len > gt_len:
                    print(f"   → Extra {gepa_len - gt_len} items")
                else:
                    print(f"   → Same length but wrong items")
        except Exception as e:
            print(f"\nAnalysis: (parsing error: {e})")
        
        print("-" * 80)
    
    print(f"\n✅ IMPROVEMENT EXAMPLES:")
    for i, q in enumerate(list_improvements[:3]):
        print(f"\n--- Example {i+1} (q{q['idx']}) ---")
        print(f"Question: {q['question']}")
        print(f"\nGround truth:  {q['gt']}")
        print(f"Baseline:      {q['baseline']} ❌")
        print(f"GEPA:          {q['gepa']} ✅")
        print("-" * 80)

def analyze_null_questions():
    """Deep dive into Null questions."""
    test_set, baseline, gepa = load_all_data()
    
    print("\n" + "="*80)
    print("NULL QUESTIONS DEEP DIVE (107 questions)")
    print("="*80)
    
    null_degradations = []
    
    for i, example in enumerate(test_set):
        if not example.get('answer_format') or example.get('answer_format') == 'null':
            qid = f'q{i}'
            base_pred = baseline['predictions'][qid]
            gepa_pred = gepa['predictions'][qid]
            
            base_correct = base_pred.get('correct', False)
            gepa_correct = gepa_pred.get('correct', False)
            
            if base_correct and not gepa_correct:
                null_degradations.append({
                    'idx': i,
                    'question': example['question'],
                    'gt': example['answer'],
                    'baseline': base_pred['answer'],
                    'gepa': gepa_pred['answer'],
                    'baseline_score': base_pred.get('score', 0),
                    'gepa_score': gepa_pred.get('score', 0)
                })
    
    print(f"\n📊 Summary:")
    print(f"   Degradations (Base✅ → GEPA❌): {len(null_degradations)}")
    
    # Categorize by issue type
    hallucination = []  # GT is "not answerable" but GEPA gives answer
    over_cautious = []  # GT has answer but GEPA says "not answerable"
    format_issue = []   # Other problems
    
    for q in null_degradations:
        gt_lower = str(q['gt']).lower().strip()
        gepa_lower = str(q['gepa']).lower().strip()
        
        gt_is_na = any(x in gt_lower for x in ['not answerable', 'not applicable', 'n/a'])
        gepa_is_na = any(x in gepa_lower for x in ['not answerable', 'not applicable', 'n/a'])
        
        if gt_is_na and not gepa_is_na and gepa_lower:
            hallucination.append(q)
        elif not gt_is_na and gepa_is_na:
            over_cautious.append(q)
        else:
            format_issue.append(q)
    
    print(f"\n🔍 Issue Breakdown:")
    print(f"   Hallucination (answer when should be N/A):    {len(hallucination)}")
    print(f"   Over-cautious (N/A when should answer):       {len(over_cautious)}")
    print(f"   Format/extraction issues:                     {len(format_issue)}")
    
    print(f"\n❌ HALLUCINATION EXAMPLES:")
    for i, q in enumerate(hallucination[:5]):
        print(f"\n--- Example {i+1} (q{q['idx']}) ---")
        print(f"Question: {q['question'][:150]}...")
        print(f"\nGround truth:  {q['gt']}")
        print(f"Baseline:      {q['baseline']} ✅")
        print(f"GEPA:          {q['gepa']} ❌ (hallucinated answer)")
        print("-" * 80)
    
    if over_cautious:
        print(f"\n⚠️  OVER-CAUTIOUS EXAMPLES:")
        for i, q in enumerate(over_cautious[:3]):
            print(f"\n--- Example {i+1} (q{q['idx']}) ---")
            print(f"Question: {q['question'][:150]}...")
            print(f"\nGround truth:  {q['gt']}")
            print(f"Baseline:      {q['baseline']} ✅")
            print(f"GEPA:          {q['gepa']} ❌ (said N/A when answer exists)")
            print("-" * 80)
    
    if format_issue:
        print(f"\n🔧 FORMAT/OTHER ISSUE EXAMPLES:")
        for i, q in enumerate(format_issue[:3]):
            print(f"\n--- Example {i+1} (q{q['idx']}) ---")
            print(f"Question: {q['question'][:150]}...")
            print(f"\nGround truth:  {q['gt']}")
            print(f"Baseline:      {q['baseline']} ✅")
            print(f"GEPA:          {q['gepa']} ❌")
            print("-" * 80)

if __name__ == "__main__":
    print("\nDEEP DIVE FORMAT ANALYSIS")
    print("List and Null Questions")
    print("="*80)
    
    analyze_list_questions()
    analyze_null_questions()
    
    print("\n" + "="*80)
    print("Analysis complete!")
    print("="*80 + "\n")

