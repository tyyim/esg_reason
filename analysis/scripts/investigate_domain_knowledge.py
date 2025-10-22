#!/usr/bin/env python3
"""
Investigate if GEPA's domain knowledge helped on test set.

Check improvements (Baseline wrong → GEPA right) to see if domain-specific
patterns in GEPA's prompts actually helped.
"""

import json

def load_data():
    """Load test set and predictions."""
    with open('dspy_implementation/data_splits/test_654.json', 'r') as f:
        test_set = json.load(f)
    
    with open('baseline_test_predictions_20251021_225632.json', 'r') as f:
        baseline = json.load(f)
    
    with open('gepa_test_predictions_20251021_225632.json', 'r') as f:
        gepa = json.load(f)
    
    return test_set, baseline, gepa

def analyze_improvements():
    """Analyze where GEPA improved over baseline."""
    test_set, baseline, gepa = load_data()
    
    improvements = []
    
    for i, example in enumerate(test_set):
        qid = f'q{i}'
        base_pred = baseline['predictions'][qid]
        gepa_pred = gepa['predictions'][qid]
        
        base_correct = base_pred.get('correct', False)
        gepa_correct = gepa_pred.get('correct', False)
        
        # Find improvements: baseline wrong → GEPA right
        if not base_correct and gepa_correct:
            improvements.append({
                'idx': i,
                'question': example['question'],
                'answer_format': example.get('answer_format'),
                'gt': example['answer'],
                'baseline_ans': base_pred['answer'],
                'gepa_ans': gepa_pred['answer'],
                'doc_id': example.get('doc_id', 'unknown')
            })
    
    return improvements

def categorize_improvements(improvements):
    """Categorize improvements by likely reason."""
    
    # Domain knowledge keywords from GEPA prompts
    domain_keywords = {
        'sa8000': ['sa8000', 'social accountability', 'clause'],
        'sustainability': ['sustainability', 'esg', 'csr', 'csro', 'chief sustainability'],
        'stem': ['stem', 'graduate', 'science technology engineering'],
        'carbon': ['carbon', 'emissions', 'ghg', 'scope'],
        'compliance': ['compliance', 'regulation', 'standard'],
        'renewable': ['renewable', 'solar', 'wind', 'energy']
    }
    
    categories = {
        'domain_knowledge': [],
        'numeric_precision': [],
        'format_extraction': [],
        'other': []
    }
    
    for imp in improvements:
        question_lower = imp['question'].lower()
        
        # Check for domain knowledge
        domain_match = False
        for domain, keywords in domain_keywords.items():
            if any(kw in question_lower for kw in keywords):
                categories['domain_knowledge'].append({
                    **imp,
                    'domain': domain,
                    'matched_keywords': [kw for kw in keywords if kw in question_lower]
                })
                domain_match = True
                break
        
        if domain_match:
            continue
        
        # Check for numeric precision
        fmt = imp['answer_format']
        if fmt in ['Int', 'Float']:
            categories['numeric_precision'].append(imp)
        elif fmt == 'List':
            categories['format_extraction'].append(imp)
        else:
            categories['other'].append(imp)
    
    return categories

def print_analysis(improvements, categories):
    """Print analysis results."""
    print("\n" + "="*80)
    print("DOMAIN KNOWLEDGE INVESTIGATION")
    print("="*80)
    
    print(f"\nTotal improvements (Baseline❌ → GEPA✅): {len(improvements)}")
    
    print(f"\n📊 Improvement Breakdown:")
    print(f"   Domain Knowledge:    {len(categories['domain_knowledge'])} ({len(categories['domain_knowledge'])/len(improvements)*100:.1f}%)")
    print(f"   Numeric Precision:   {len(categories['numeric_precision'])} ({len(categories['numeric_precision'])/len(improvements)*100:.1f}%)")
    print(f"   Format Extraction:   {len(categories['format_extraction'])} ({len(categories['format_extraction'])/len(improvements)*100:.1f}%)")
    print(f"   Other:               {len(categories['other'])} ({len(categories['other'])/len(improvements)*100:.1f}%)")
    
    # Domain knowledge examples
    if categories['domain_knowledge']:
        print(f"\n🎯 DOMAIN KNOWLEDGE IMPROVEMENTS ({len(categories['domain_knowledge'])} cases):")
        for i, case in enumerate(categories['domain_knowledge'], 1):
            print(f"\n--- Example {i} (q{case['idx']}) ---")
            print(f"Domain: {case['domain']}")
            print(f"Keywords: {', '.join(case['matched_keywords'])}")
            print(f"Question: {case['question'][:120]}...")
            print(f"Ground truth:  {case['gt']}")
            print(f"Baseline:      {case['baseline_ans']} ❌")
            print(f"GEPA:          {case['gepa_ans']} ✅")
            print("-" * 80)
    else:
        print(f"\n⚠️  NO domain knowledge improvements found!")
        print("   GEPA's domain-specific examples did NOT help on test set")
    
    # Numeric precision examples
    if categories['numeric_precision']:
        print(f"\n🔢 NUMERIC PRECISION IMPROVEMENTS ({len(categories['numeric_precision'])} cases):")
        for i, case in enumerate(categories['numeric_precision'][:3], 1):
            print(f"\n--- Example {i} (q{case['idx']}) ---")
            print(f"Format: {case['answer_format']}")
            print(f"Question: {case['question'][:120]}...")
            print(f"Ground truth:  {case['gt']}")
            print(f"Baseline:      {case['baseline_ans']} ❌")
            print(f"GEPA:          {case['gepa_ans']} ✅")
            print("-" * 80)
    
    # Format extraction examples
    if categories['format_extraction']:
        print(f"\n📋 FORMAT EXTRACTION IMPROVEMENTS ({len(categories['format_extraction'])} cases):")
        for i, case in enumerate(categories['format_extraction'][:3], 1):
            print(f"\n--- Example {i} (q{case['idx']}) ---")
            print(f"Question: {case['question'][:120]}...")
            print(f"Ground truth:  {case['gt']}")
            print(f"Baseline:      {case['baseline_ans']} ❌")
            print(f"GEPA:          {case['gepa_ans']} ✅")
            print("-" * 80)

def main():
    """Main execution."""
    print("\nInvestigating GEPA's domain knowledge impact on test set...")
    
    improvements = analyze_improvements()
    categories = categorize_improvements(improvements)
    print_analysis(improvements, categories)
    
    # Summary
    print(f"\n{'='*80}")
    print("CONCLUSION")
    print(f"{'='*80}")
    
    domain_pct = len(categories['domain_knowledge']) / len(improvements) * 100 if improvements else 0
    
    if domain_pct < 10:
        print(f"\n⚠️  Domain knowledge had MINIMAL impact ({domain_pct:.1f}% of improvements)")
        print("   GEPA's domain-specific examples (SA8000, CSRO, STEM) did NOT generalize to test set")
        print("   Most improvements came from numeric precision and format extraction")
    else:
        print(f"\n✅ Domain knowledge contributed to {domain_pct:.1f}% of improvements")
        print("   GEPA's domain-specific examples helped on test set")
    
    print(f"\n💡 Main contributors to GEPA improvements:")
    print(f"   1. Numeric precision (Int/Float): {len(categories['numeric_precision'])} cases")
    print(f"   2. Format extraction (List): {len(categories['format_extraction'])} cases")
    print(f"   3. Domain knowledge: {len(categories['domain_knowledge'])} cases")
    
    # Save results
    results = {
        'total_improvements': len(improvements),
        'breakdown': {
            'domain_knowledge': len(categories['domain_knowledge']),
            'numeric_precision': len(categories['numeric_precision']),
            'format_extraction': len(categories['format_extraction']),
            'other': len(categories['other'])
        },
        'domain_knowledge_cases': categories['domain_knowledge']
    }
    
    with open('domain_knowledge_investigation.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: domain_knowledge_investigation.json")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()

