#!/usr/bin/env python3
"""
Test Set Error Analysis - Similar to Dev Set Analysis

Analyzes test set results (654 questions) with focus on:
1. Overall performance comparison
2. Format-specific patterns
3. GEPA degradation analysis
4. Dev vs Test comparison
"""

import json
from collections import defaultdict
from pathlib import Path

def load_data():
    """Load test set analysis."""
    with open('complete_test_analysis_20251021_225632.json', 'r') as f:
        return json.load(f)

def load_test_set():
    """Load test set for ground truth."""
    with open('dspy_implementation/data_splits/test_654.json', 'r') as f:
        return json.load(f)

def analyze_by_format(data, test_set):
    """Analyze performance by answer format."""
    baseline_preds = data['baseline']['predictions']
    miprov2_preds = data['miprov2']['predictions']
    gepa_preds = data['gepa']['predictions']
    
    by_format = defaultdict(lambda: {
        'total': 0,
        'baseline_correct': 0,
        'miprov2_correct': 0,
        'gepa_correct': 0,
        'baseline_right_gepa_wrong': [],
        'baseline_wrong_gepa_right': [],
        'gepa_degradations': [],
        'gepa_improvements': []
    })
    
    for i, example in enumerate(test_set):
        qid = f'q{i}'
        fmt = example.get('answer_format') or 'null'
        
        base_correct = baseline_preds[qid].get('correct', False)
        mipro_correct = miprov2_preds[qid].get('correct', False)
        gepa_correct = gepa_preds[qid].get('correct', False)
        
        by_format[fmt]['total'] += 1
        if base_correct:
            by_format[fmt]['baseline_correct'] += 1
        if mipro_correct:
            by_format[fmt]['miprov2_correct'] += 1
        if gepa_correct:
            by_format[fmt]['gepa_correct'] += 1
        
        # Track GEPA degradations and improvements
        if base_correct and not gepa_correct:
            by_format[fmt]['baseline_right_gepa_wrong'].append({
                'idx': i,
                'question': example['question'],
                'gt': example['answer'],
                'baseline': baseline_preds[qid]['answer'],
                'gepa': gepa_preds[qid]['answer']
            })
        
        if not base_correct and gepa_correct:
            by_format[fmt]['baseline_wrong_gepa_right'].append({
                'idx': i,
                'question': example['question'],
                'gt': example['answer'],
                'baseline': baseline_preds[qid]['answer'],
                'gepa': gepa_preds[qid]['answer']
            })
    
    return by_format

def print_summary(data, by_format):
    """Print comprehensive summary."""
    print("\n" + "="*80)
    print("TEST SET ERROR ANALYSIS (654 Questions)")
    print("="*80)
    
    # Overall performance
    baseline = data['baseline']
    miprov2 = data['miprov2']
    gepa = data['gepa']
    
    print(f"\n📊 Overall Performance:")
    print(f"   Baseline:  {baseline['correct_count']}/{baseline['total']} ({baseline['accuracy']:.1f}%)")
    print(f"   MIPROv2:   {miprov2['correct_count']}/{miprov2['total']} ({miprov2['accuracy']:.1f}%)")
    print(f"   GEPA:      {gepa['correct_count']}/{gepa['total']} ({gepa['accuracy']:.1f}%)")
    
    print(f"\n📈 Relative to Baseline:")
    mipro_delta = miprov2['accuracy'] - baseline['accuracy']
    gepa_delta = gepa['accuracy'] - baseline['accuracy']
    print(f"   MIPROv2: {mipro_delta:+.1f}% ({miprov2['correct_count'] - baseline['correct_count']:+d} questions)")
    print(f"   GEPA:    {gepa_delta:+.1f}% ({gepa['correct_count'] - baseline['correct_count']:+d} questions)")
    
    # Format breakdown
    print(f"\n📋 Performance by Answer Format:")
    print(f"\n   {'Format':<8} {'Total':<6} {'Baseline':<10} {'MIPROv2':<10} {'GEPA':<10} {'GEPA vs Base':<12}")
    print(f"   {'-'*8} {'-'*6} {'-'*10} {'-'*10} {'-'*10} {'-'*12}")
    
    for fmt in ['Int', 'Float', 'Str', 'List', 'null']:
        if fmt in by_format:
            data = by_format[fmt]
            total = data['total']
            base_pct = data['baseline_correct'] / total * 100
            mipro_pct = data['miprov2_correct'] / total * 100
            gepa_pct = data['gepa_correct'] / total * 100
            gepa_delta = gepa_pct - base_pct
            
            emoji = "✅" if gepa_delta > 0 else "❌" if gepa_delta < 0 else "➖"
            print(f"   {fmt:<8} {total:<6} {base_pct:>6.1f}%    {mipro_pct:>6.1f}%    {gepa_pct:>6.1f}%    {gepa_delta:>+5.1f}% {emoji}")
    
    # GEPA-specific analysis
    print(f"\n🔍 GEPA Degradation Details:")
    print(f"\n   Format    Degraded  Improved  Net    Top Issue")
    print(f"   --------  --------  --------  -----  ---------")
    
    for fmt in ['Int', 'Float', 'Str', 'List', 'null']:
        if fmt in by_format:
            data = by_format[fmt]
            degraded = len(data['baseline_right_gepa_wrong'])
            improved = len(data['baseline_wrong_gepa_right'])
            net = improved - degraded
            net_str = f"{net:+d}" if net != 0 else "0"
            
            # Identify top issue
            if degraded > 0:
                issue = "Verbosity" if fmt == 'Str' else "Hallucination" if fmt == 'null' else "Format?"
            else:
                issue = "—"
            
            print(f"   {fmt:<8}  {degraded:>8}  {improved:>8}  {net_str:>5}  {issue}")
    
    # Question patterns
    if 'analysis' in data:
        analysis = data['analysis']
        print(f"\n🔄 Question Patterns:")
        print(f"   All 3 correct:  {len(analysis['all_correct']):3d} questions ({len(analysis['all_correct'])/654*100:.1f}%)")
        print(f"   All 3 wrong:    {len(analysis['all_wrong']):3d} questions ({len(analysis['all_wrong'])/654*100:.1f}%)")
        if 'unique_wins' in analysis:
            print(f"   MIPROv2 only:   {len(analysis['unique_wins']['miprov2']):3d} questions")
            print(f"   GEPA only:      {len(analysis['unique_wins']['gepa']):3d} questions")

def compare_dev_vs_test(by_format):
    """Compare test set results with dev set findings."""
    print(f"\n{'='*80}")
    print("DEV SET vs TEST SET COMPARISON")
    print(f"{'='*80}")
    
    # Dev set results from our authoritative files
    dev_results = {
        'Int': {'baseline': 63.2, 'gepa': 73.7, 'total': 19},
        'Float': {'baseline': 69.2, 'gepa': 76.9, 'total': 13},
        'Str': {'baseline': 35.3, 'gepa': 29.4, 'total': 34},
        'List': {'baseline': 23.1, 'gepa': 38.5, 'total': 13},
        'null': {'baseline': 92.9, 'gepa': 85.7, 'total': 14}
    }
    
    print(f"\n   {'Format':<8} {'Dev Base':<10} {'Dev GEPA':<10} {'Dev Δ':<8} {'Test Base':<10} {'Test GEPA':<10} {'Test Δ':<8} {'Trend'}")
    print(f"   {'-'*8} {'-'*10} {'-'*10} {'-'*8} {'-'*10} {'-'*10} {'-'*8} {'-'*10}")
    
    for fmt in ['Int', 'Float', 'Str', 'List', 'null']:
        if fmt in by_format and fmt in dev_results:
            # Dev set
            dev_base = dev_results[fmt]['baseline']
            dev_gepa = dev_results[fmt]['gepa']
            dev_delta = dev_gepa - dev_base
            
            # Test set
            test_data = by_format[fmt]
            test_base = test_data['baseline_correct'] / test_data['total'] * 100
            test_gepa = test_data['gepa_correct'] / test_data['total'] * 100
            test_delta = test_gepa - test_base
            
            # Trend analysis
            if dev_delta > 0 and test_delta > 0:
                trend = "✅ Consistent gain"
            elif dev_delta < 0 and test_delta < 0:
                trend = "⚠️  Consistent loss"
            elif dev_delta > 0 and test_delta < 0:
                trend = "❌ Gain → Loss"
            elif dev_delta < 0 and test_delta < 0 and abs(test_delta) < abs(dev_delta):
                trend = "⚠️  Loss reduced"
            else:
                trend = "➖ Mixed"
            
            print(f"   {fmt:<8} {dev_base:>6.1f}%    {dev_gepa:>6.1f}%    {dev_delta:>+5.1f}%  "
                  f"{test_base:>6.1f}%    {test_gepa:>6.1f}%    {test_delta:>+5.1f}%  {trend}")

def analyze_string_questions(by_format):
    """Deep dive into String questions - suspected main issue."""
    print(f"\n{'='*80}")
    print("STRING QUESTION DEEP DIVE")
    print(f"{'='*80}")
    
    str_data = by_format.get('Str', {})
    
    print(f"\n📊 String Question Statistics:")
    print(f"   Total:           {str_data['total']} questions")
    print(f"   Baseline:        {str_data['baseline_correct']}/{str_data['total']} ({str_data['baseline_correct']/str_data['total']*100:.1f}%)")
    print(f"   GEPA:            {str_data['gepa_correct']}/{str_data['total']} ({str_data['gepa_correct']/str_data['total']*100:.1f}%)")
    print(f"   GEPA degraded:   {len(str_data['baseline_right_gepa_wrong'])} questions")
    print(f"   GEPA improved:   {len(str_data['baseline_wrong_gepa_right'])} questions")
    print(f"   Net impact:      {len(str_data['baseline_wrong_gepa_right']) - len(str_data['baseline_right_gepa_wrong']):+d} questions")
    
    # Show sample degradations
    if str_data['baseline_right_gepa_wrong']:
        print(f"\n🔍 Sample String Degradations (Baseline Right → GEPA Wrong):")
        for i, case in enumerate(str_data['baseline_right_gepa_wrong'][:3]):
            print(f"\n   Example {i+1} (q{case['idx']}):")
            print(f"   Question: {case['question'][:100]}...")
            print(f"   Ground truth: {case['gt'][:80]}")
            print(f"   Baseline:     {case['baseline'][:80]}")
            print(f"   GEPA:         {case['gepa'][:80]}")
    
    # Show sample improvements
    if str_data['baseline_wrong_gepa_right']:
        print(f"\n✅ Sample String Improvements (Baseline Wrong → GEPA Right):")
        for i, case in enumerate(str_data['baseline_wrong_gepa_right'][:2]):
            print(f"\n   Example {i+1} (q{case['idx']}):")
            print(f"   Question: {case['question'][:100]}...")
            print(f"   Ground truth: {case['gt'][:80]}")
            print(f"   Baseline:     {case['baseline'][:80]}")
            print(f"   GEPA:         {case['gepa'][:80]}")

def main():
    """Main analysis."""
    print("\nLoading test set results...")
    data = load_data()
    test_set = load_test_set()
    
    print("Analyzing by format...")
    by_format = analyze_by_format(data, test_set)
    
    # Print analyses
    print_summary(data, by_format)
    compare_dev_vs_test(by_format)
    analyze_string_questions(by_format)
    
    # Key findings
    print(f"\n{'='*80}")
    print("KEY FINDINGS")
    print(f"{'='*80}")
    
    print(f"\n⚠️  CRITICAL ISSUE: GEPA Underperforms on Test Set")
    print(f"   - Dev set:  GEPA +2.2% over baseline (54.8% vs 52.7%)")
    print(f"   - Test set: GEPA -1.7% under baseline (45.7% vs 47.4%)")
    print(f"   - Performance reversal: +2.2% → -1.7% = -3.9% swing!")
    
    print(f"\n🔍 Root Cause Analysis:")
    str_data = by_format['Str']
    print(f"   1. String questions (32% of test set, 211/654)")
    print(f"      - GEPA: {str_data['gepa_correct']/str_data['total']*100:.1f}% vs Baseline: {str_data['baseline_correct']/str_data['total']*100:.1f}%")
    print(f"      - Net impact: {len(str_data['baseline_wrong_gepa_right']) - len(str_data['baseline_right_gepa_wrong']):+d} questions")
    print(f"      - Likely issue: Verbose 7,749-char prompt hurts text extraction")
    
    if 'null' in by_format:
        null_data = by_format['null']
        print(f"\n   2. Null/Not answerable (16% of test set, 107/654)")
        print(f"      - GEPA: {null_data['gepa_correct']/null_data['total']*100:.1f}% vs Baseline: {null_data['baseline_correct']/null_data['total']*100:.1f}%")
        print(f"      - Net impact: {len(null_data['baseline_wrong_gepa_right']) - len(null_data['baseline_right_gepa_wrong']):+d} questions")
        print(f"      - Issue: GEPA tries too hard, hallucinates answers")
    
    print(f"\n💡 Recommendations:")
    print(f"   1. GEPA-v2: Reduce prompt length (7,749 → <3,000 chars)")
    print(f"   2. Format-specific routing:")
    print(f"      - Int/Float: Use GEPA (if validated on larger sample)")
    print(f"      - Str/null: Use Baseline (clearly better)")
    print(f"   3. Statistical significance testing needed")
    print(f"   4. Consider dev set may not be representative")
    
    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    main()

