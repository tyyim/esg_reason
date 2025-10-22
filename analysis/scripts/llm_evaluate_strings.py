#!/usr/bin/env python3
"""
LLM-assisted evaluation of String questions

Uses qwen-max to evaluate if GEPA's string answers are semantically better
but ANLS metric can't capture it.
"""

import json
import os
import time
from dotenv import load_dotenv
import dspy

load_dotenv()

def load_string_degradations():
    """Load string questions where baseline was right but GEPA was wrong."""
    with open('dspy_implementation/data_splits/test_654.json', 'r') as f:
        test_set = json.load(f)
    
    with open('baseline_test_predictions_20251021_225632.json', 'r') as f:
        baseline = json.load(f)
    
    with open('gepa_test_predictions_20251021_225632.json', 'r') as f:
        gepa = json.load(f)
    
    degradations = []
    for i, example in enumerate(test_set):
        if example.get('answer_format') == 'Str':
            qid = f'q{i}'
            base_pred = baseline['predictions'][qid]
            gepa_pred = gepa['predictions'][qid]
            
            # Only analyze degradations (baseline right, GEPA wrong)
            if base_pred.get('correct', False) and not gepa_pred.get('correct', False):
                degradations.append({
                    'idx': i,
                    'question': example['question'],
                    'gt': example['answer'],
                    'baseline_ans': base_pred['answer'],
                    'gepa_ans': gepa_pred['answer'],
                    'baseline_score': base_pred.get('score', 0),
                    'gepa_score': gepa_pred.get('score', 0)
                })
    
    return degradations

def evaluate_with_llm(degradations, sample_size=15):
    """Use qwen-max to evaluate semantic quality."""
    print(f"\n{'='*80}")
    print("LLM-ASSISTED STRING EVALUATION")
    print(f"{'='*80}")
    print(f"\nTotal string degradations: {len(degradations)}")
    print(f"Evaluating sample: {sample_size} questions")
    print(f"Model: qwen-max")
    print(f"Estimated cost: ~$0.03-0.05\n")
    
    # Configure LLM
    lm = dspy.LM(
        model='openai/qwen-max',
        api_key=os.getenv('DASHSCOPE_API_KEY'),
        api_base='https://dashscope.aliyuncs.com/compatible-mode/v1',
        temperature=0.0,
        max_tokens=512
    )
    dspy.configure(lm=lm)
    
    # Sample questions
    sample = degradations[:sample_size]
    
    results = {
        'better': [],
        'same': [],
        'worse': []
    }
    
    for i, q in enumerate(sample):
        print(f"[{i+1}/{sample_size}] Evaluating q{q['idx']}...", end=' ')
        
        prompt = f"""You are an expert evaluator for question-answering systems.

Question: {q['question']}

Ground Truth Answer: {q['gt']}

Answer A (Baseline): {q['baseline_ans']}
Answer B (GEPA): {q['gepa_ans']}

The ANLS fuzzy string matching metric scored:
- Answer A: {q['baseline_score']:.2f} (≥0.5 = CORRECT)
- Answer B: {q['gepa_score']:.2f} (<0.5 = WRONG)

However, ANLS may miss semantic equivalence or penalize minor formatting differences.

Task: Compare the semantic quality of Answer B relative to Answer A.

Consider:
1. Completeness - Does it answer the full question?
2. Accuracy - Is it factually correct?
3. Relevance - Does it address what was asked?
4. Format - Ignore capitalization, punctuation, minor wording differences

Respond with ONLY ONE WORD:
- BETTER: Answer B is semantically superior to Answer A
- SAME: Both answers are semantically equivalent (ANLS failed to recognize this)
- WORSE: Answer B is semantically inferior to Answer A

Your evaluation:"""
        
        try:
            response = lm(prompt)
            # Handle both string and list responses
            if isinstance(response, list):
                verdict = str(response[0]).strip().upper() if response else "WORSE"
            else:
                verdict = str(response).strip().upper()
            
            # Parse verdict
            if 'BETTER' in verdict:
                category = 'better'
                symbol = '✨'
            elif 'SAME' in verdict:
                category = 'same'
                symbol = '='
            else:
                category = 'worse'
                symbol = '❌'
            
            results[category].append({
                'idx': q['idx'],
                'question': q['question'][:80] + '...' if len(q['question']) > 80 else q['question'],
                'gt': q['gt'],
                'baseline': q['baseline_ans'],
                'gepa': q['gepa_ans'],
                'verdict': category
            })
            
            print(f"{symbol} {category.upper()}")
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            print(f"ERROR: {e}")
            results['worse'].append({
                'idx': q['idx'],
                'question': q['question'][:80],
                'error': str(e)
            })
    
    return results

def print_summary(results, total_degradations, sample_size):
    """Print evaluation summary."""
    better_count = len(results['better'])
    same_count = len(results['same'])
    worse_count = len(results['worse'])
    
    print(f"\n{'='*80}")
    print("EVALUATION RESULTS")
    print(f"{'='*80}")
    
    print(f"\nOut of {sample_size} string degradations (Baseline✅ → GEPA❌ per ANLS):")
    print(f"\n   ✨ GEPA BETTER:  {better_count:2d} ({better_count/sample_size*100:5.1f}%)")
    print(f"      → GEPA's answer is semantically superior")
    print(f"\n   =  GEPA SAME:   {same_count:2d} ({same_count/sample_size*100:5.1f}%)")
    print(f"      → Semantically equivalent, ANLS too strict")
    print(f"\n   ❌ GEPA WORSE:  {worse_count:2d} ({worse_count/sample_size*100:5.1f}%)")
    print(f"      → ANLS correctly identified inferior answer")
    
    # Calculate ANLS false negatives
    anls_errors = better_count + same_count
    anls_error_rate = anls_errors / sample_size * 100
    
    print(f"\n{'='*80}")
    print("ANLS METRIC ANALYSIS")
    print(f"{'='*80}")
    
    print(f"\n   ANLS False Negatives: {anls_errors}/{sample_size} ({anls_error_rate:.1f}%)")
    
    if anls_errors > 0:
        print(f"\n   💡 INSIGHT: GEPA may be {anls_errors} answers better than ANLS suggests!")
        
        # Extrapolate to full degradation set
        estimated_false_negatives = int(total_degradations * anls_errors / sample_size)
        print(f"\n   📊 Extrapolated to {total_degradations} total string degradations:")
        print(f"      → ~{estimated_false_negatives} may be false negatives")
        print(f"      → True string impact: -{total_degradations} + {estimated_false_negatives} = -{total_degradations - estimated_false_negatives} questions")
        
        # Impact on overall accuracy
        true_string_impact = -(total_degradations - estimated_false_negatives) + 17  # 17 improvements
        print(f"\n   🎯 Corrected String Performance (with improvements):")
        print(f"      → Net: {true_string_impact:+d} questions (vs -3 by ANLS)")
        if true_string_impact > -3:
            print(f"      → GEPA may be better on strings than ANLS shows!")
    else:
        print(f"\n   ✅ ANLS correctly identified all degradations")
    
    # Show examples
    if results['better']:
        print(f"\n{'='*80}")
        print("EXAMPLES: GEPA BETTER (ANLS missed)")
        print(f"{'='*80}")
        for ex in results['better'][:3]:
            print(f"\n   q{ex['idx']}: {ex['question']}")
            print(f"   GT:       {ex['gt']}")
            print(f"   Baseline: {ex['baseline']}")
            print(f"   GEPA:     {ex['gepa']}")
    
    if results['same']:
        print(f"\n{'='*80}")
        print("EXAMPLES: GEPA SAME (ANLS too strict)")
        print(f"{'='*80}")
        for ex in results['same'][:3]:
            print(f"\n   q{ex['idx']}: {ex['question']}")
            print(f"   GT:       {ex['gt']}")
            print(f"   Baseline: {ex['baseline']}")
            print(f"   GEPA:     {ex['gepa']}")
    
    if results['worse']:
        print(f"\n{'='*80}")
        print("EXAMPLES: GEPA WORSE (ANLS correct)")
        print(f"{'='*80}")
        for ex in results['worse'][:3]:
            if 'error' not in ex:
                print(f"\n   q{ex['idx']}: {ex['question']}")
                print(f"   GT:       {ex['gt']}")
                print(f"   Baseline: {ex['baseline']}")
                print(f"   GEPA:     {ex['gepa']}")

def main():
    """Main execution."""
    print(f"\n{'='*80}")
    print("STRING QUESTION SEMANTIC EVALUATION")
    print(f"{'='*80}\n")
    
    # Load degradations
    print("Loading string degradations...")
    degradations = load_string_degradations()
    print(f"Found {len(degradations)} degradations (Baseline✅ → GEPA❌)")
    
    # Evaluate with LLM
    results = evaluate_with_llm(degradations, sample_size=15)
    
    # Print summary
    print_summary(results, len(degradations), 15)
    
    # Save results
    output = {
        'total_degradations': len(degradations),
        'sample_size': 15,
        'results': results,
        'counts': {
            'better': len(results['better']),
            'same': len(results['same']),
            'worse': len(results['worse'])
        }
    }
    
    with open('string_llm_evaluation_results.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n{'='*80}")
    print("💾 Results saved to: string_llm_evaluation_results.json")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()

