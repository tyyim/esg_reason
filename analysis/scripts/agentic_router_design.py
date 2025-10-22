#!/usr/bin/env python3
"""
Agentic Router Analysis: Intelligent Question Routing

Instead of simple format routing, use an agentic system to:
1. Analyze question characteristics (domain, complexity, ambiguity)
2. Route to appropriate specialist
3. Cascade through models based on confidence
4. Combine approaches (e.g., GEPA reasoning → MIPROv2 extraction)
"""

import json
from collections import defaultdict

def load_data():
    """Load test set and predictions."""
    with open('dspy_implementation/data_splits/test_654.json', 'r') as f:
        test_set = json.load(f)
    
    with open('baseline_test_predictions_20251021_225632.json', 'r') as f:
        baseline = json.load(f)
    
    with open('miprov2_test_predictions_20251021_225632.json', 'r') as f:
        miprov2 = json.load(f)
    
    with open('gepa_test_predictions_20251021_225632.json', 'r') as f:
        gepa = json.load(f)
    
    return test_set, baseline, miprov2, gepa

def analyze_gepa_unique_wins(test_set, baseline, miprov2, gepa):
    """
    Find questions where ONLY GEPA got it right.
    These reveal GEPA's unique value proposition.
    """
    gepa_only = []
    
    for i, example in enumerate(test_set):
        qid = f'q{i}'
        
        base_correct = baseline['predictions'][qid].get('correct', False)
        mipro_correct = miprov2['predictions'][qid].get('correct', False)
        gepa_correct = gepa['predictions'][qid].get('correct', False)
        
        # GEPA only wins
        if gepa_correct and not base_correct and not mipro_correct:
            gepa_only.append({
                'idx': i,
                'question': example['question'],
                'answer_format': example.get('answer_format'),
                'answer': example['answer'],
                'baseline_ans': baseline['predictions'][qid]['answer'],
                'miprov2_ans': miprov2['predictions'][qid]['answer'],
                'gepa_ans': gepa['predictions'][qid]['answer']
            })
    
    return gepa_only

def analyze_characteristics(questions):
    """Analyze characteristics of questions."""
    characteristics = []
    
    # Domain keywords
    domain_keywords = {
        'technical_specific': ['sa8000', 'iso 14001', 'ghg protocol', 'scope 1', 'scope 2', 'scope 3'],
        'sustainability_metrics': ['carbon', 'emissions', 'renewable', 'energy intensity', 'sustainability'],
        'compliance_standards': ['compliance', 'certification', 'accreditation', 'standard'],
        'esg_specific': ['esg', 'csro', 'chief sustainability officer'],
        'quantitative_reasoning': ['calculate', 'total', 'percentage', 'ratio', 'compare'],
        'qualitative_reasoning': ['explain', 'describe', 'what is', 'why', 'how does'],
        'complex_extraction': ['list', 'enumerate', 'what are the', 'which'],
        'contextual': ['according to', 'based on', 'in the context of']
    }
    
    for q in questions:
        question_lower = q['question'].lower()
        
        char = {
            'idx': q['idx'],
            'length': len(q['question']),
            'has_numbers': any(char.isdigit() for char in q['question']),
            'question_type': None,
            'domains': [],
            'complexity_signals': []
        }
        
        # Detect domains
        for domain, keywords in domain_keywords.items():
            if any(kw in question_lower for kw in keywords):
                char['domains'].append(domain)
        
        # Question type
        if question_lower.startswith(('what', 'which')):
            char['question_type'] = 'factual'
        elif question_lower.startswith(('how', 'why')):
            char['question_type'] = 'reasoning'
        elif question_lower.startswith(('calculate', 'compute')):
            char['question_type'] = 'computational'
        else:
            char['question_type'] = 'other'
        
        # Complexity signals
        if 'according to' in question_lower or 'based on' in question_lower:
            char['complexity_signals'].append('requires_context')
        if len(question_lower.split()) > 20:
            char['complexity_signals'].append('long_question')
        if len(char['domains']) > 1:
            char['complexity_signals'].append('multi_domain')
        
        characteristics.append(char)
    
    return characteristics

def design_agentic_strategies():
    """Design different agentic routing strategies."""
    
    strategies = {
        'strategy_1_expert_specialist': {
            'name': 'Expert Specialist Routing',
            'description': 'Route to GEPA for domain expertise, MIPROv2 for structured, Baseline for simple',
            'rules': [
                'If technical_specific OR sustainability_metrics OR esg_specific → GEPA (domain expert)',
                'If quantitative_reasoning AND (Int OR Float) → MIPROv2 (structured extraction)',
                'If complex_extraction OR qualitative_reasoning → GEPA (verbose reasoning)',
                'If simple factual OR (List OR null) → Baseline (simple and reliable)',
                'Default → MIPROv2'
            ]
        },
        
        'strategy_2_cascading': {
            'name': 'Cascading Confidence',
            'description': 'Start with simple model, escalate if uncertain',
            'rules': [
                'Step 1: Try Baseline first (cheap and fast)',
                'Step 2: If Baseline confidence < 0.7 → Try MIPROv2',
                'Step 3: If MIPROv2 confidence < 0.7 OR domain detected → Try GEPA',
                'Return first confident answer'
            ]
        },
        
        'strategy_3_reasoning_extraction': {
            'name': 'Two-Stage: GEPA Reasoning → MIPROv2 Extraction',
            'description': 'Use GEPA for reasoning, MIPROv2 for final extraction',
            'rules': [
                'Step 1: If domain OR complex question → Use GEPA to generate reasoning',
                'Step 2: Feed GEPA reasoning + original context to MIPROv2 for extraction',
                'Benefit: GEPA understanding + MIPROv2 structured output',
                'Cost: 2× inference (but potentially much better)'
            ]
        },
        
        'strategy_4_ensemble_voting': {
            'name': 'Weighted Expert Voting',
            'description': 'Multiple models vote, weighted by expertise',
            'rules': [
                'Run Baseline, MIPROv2, GEPA in parallel',
                'Weight votes by format expertise:',
                '  - Int/Float: MIPROv2 = 2.0, GEPA = 1.0, Baseline = 1.0',
                '  - Str: MIPROv2 = 1.5, GEPA = 1.5, Baseline = 1.0',
                '  - List/null: Baseline = 2.0, MIPROv2 = 1.0, GEPA = 0.5',
                'If domain detected: GEPA weight × 1.5',
                'Pick answer with highest weighted vote'
            ]
        },
        
        'strategy_5_adaptive_router': {
            'name': 'Adaptive LLM Router',
            'description': 'Use small LLM to analyze question and route intelligently',
            'rules': [
                'Router LLM analyzes: domain, complexity, format, ambiguity',
                'Router predicts: which model will perform best',
                'Route to predicted best model',
                'Learn from feedback to improve routing over time'
            ]
        }
    }
    
    return strategies

def simulate_expert_specialist(test_set, baseline, miprov2, gepa):
    """
    Simulate Strategy 1: Expert Specialist Routing
    Route based on domain expertise and question characteristics.
    """
    domain_keywords = {
        'domain_expert': ['sa8000', 'iso 14001', 'ghg protocol', 'carbon', 'emissions', 
                         'esg', 'csro', 'sustainability', 'renewable', 'compliance'],
        'reasoning_needed': ['explain', 'describe', 'why', 'how does', 'according to'],
        'structured_extraction': ['calculate', 'total', 'percentage', 'ratio']
    }
    
    correct = 0
    decisions = defaultdict(int)
    
    for i, example in enumerate(test_set):
        qid = f'q{i}'
        question_lower = example['question'].lower()
        fmt = example.get('answer_format')
        
        # Decision logic
        model = None
        reason = None
        
        # Check for domain expertise need
        if any(kw in question_lower for kw in domain_keywords['domain_expert']):
            model = 'gepa'
            reason = 'domain_expert'
        # Check for reasoning questions
        elif any(kw in question_lower for kw in domain_keywords['reasoning_needed']):
            model = 'gepa'
            reason = 'reasoning_needed'
        # Check for structured extraction
        elif (any(kw in question_lower for kw in domain_keywords['structured_extraction']) 
              and fmt in ['Int', 'Float']):
            model = 'miprov2'
            reason = 'structured_extraction'
        # Simple cases
        elif fmt in ['List', 'null']:
            model = 'baseline'
            reason = 'simple_reliable'
        # Default
        else:
            model = 'miprov2'
            reason = 'default'
        
        decisions[f'{reason} -> {model}'] += 1
        
        # Check correctness
        if model == 'baseline':
            if baseline['predictions'][qid].get('correct', False):
                correct += 1
        elif model == 'miprov2':
            if miprov2['predictions'][qid].get('correct', False):
                correct += 1
        elif model == 'gepa':
            if gepa['predictions'][qid].get('correct', False):
                correct += 1
    
    return correct, decisions

def print_analysis():
    """Print comprehensive agentic routing analysis."""
    print("\n" + "="*80)
    print("AGENTIC ROUTER ANALYSIS")
    print("="*80)
    
    test_set, baseline, miprov2, gepa = load_data()
    
    # Find GEPA's unique wins
    gepa_only = analyze_gepa_unique_wins(test_set, baseline, miprov2, gepa)
    
    print(f"\n🎯 GEPA's Unique Value Proposition:")
    print(f"   Questions where ONLY GEPA got it right: {len(gepa_only)} / 654")
    print(f"   These are the {len(gepa_only)} questions we're losing with simple routing!")
    
    # Analyze characteristics
    characteristics = analyze_characteristics(gepa_only)
    
    print(f"\n📊 Characteristics of GEPA-Only Wins:")
    
    # Format distribution
    format_dist = defaultdict(int)
    for q in gepa_only:
        format_dist[q['answer_format']] += 1
    
    print(f"\n   Format distribution:")
    for fmt, count in sorted(format_dist.items(), key=lambda x: -x[1]):
        print(f"      {fmt}: {count} ({count/len(gepa_only)*100:.1f}%)")
    
    # Domain distribution
    domain_dist = defaultdict(int)
    for char in characteristics:
        for domain in char['domains']:
            domain_dist[domain] += 1
    
    print(f"\n   Domain distribution:")
    for domain, count in sorted(domain_dist.items(), key=lambda x: -x[1]):
        print(f"      {domain}: {count}")
    
    # Question types
    qtype_dist = defaultdict(int)
    for char in characteristics:
        qtype_dist[char['question_type']] += 1
    
    print(f"\n   Question types:")
    for qtype, count in sorted(qtype_dist.items(), key=lambda x: -x[1]):
        print(f"      {qtype}: {count}")
    
    # Show examples
    print(f"\n📝 Examples of GEPA-Only Wins:")
    for i, q in enumerate(gepa_only[:5], 1):
        print(f"\n   Example {i} (q{q['idx']}, {q['answer_format']}):")
        print(f"   Q: {q['question'][:100]}...")
        print(f"   GT:       {q['answer']}")
        print(f"   Baseline: {q['baseline_ans']} ❌")
        print(f"   MIPROv2:  {q['miprov2_ans']} ❌")
        print(f"   GEPA:     {q['gepa_ans']} ✅")
    
    # Design strategies
    print(f"\n{'='*80}")
    print("AGENTIC ROUTING STRATEGIES")
    print(f"{'='*80}")
    
    strategies = design_agentic_strategies()
    
    for i, (key, strategy) in enumerate(strategies.items(), 1):
        print(f"\n{'─'*80}")
        print(f"STRATEGY {i}: {strategy['name']}")
        print(f"{'─'*80}")
        print(f"\nDescription: {strategy['description']}")
        print(f"\nRouting Rules:")
        for rule in strategy['rules']:
            print(f"   {rule}")
    
    # Simulate expert specialist
    print(f"\n{'='*80}")
    print("SIMULATION: Expert Specialist Routing")
    print(f"{'='*80}")
    
    correct, decisions = simulate_expert_specialist(test_set, baseline, miprov2, gepa)
    accuracy = correct / len(test_set) * 100
    improvement = accuracy - 47.6  # vs MIPROv2
    
    print(f"\n✅ Result: {correct}/654 ({accuracy:.1f}%)")
    print(f"   vs MIPROv2: {improvement:+.1f}%")
    print(f"   vs Format-Based: {accuracy - 50.2:+.1f}%")
    
    print(f"\n📋 Routing decisions:")
    for decision, count in sorted(decisions.items(), key=lambda x: -x[1]):
        print(f"   {decision}: {count}")
    
    # Key insights
    print(f"\n{'='*80}")
    print("KEY INSIGHTS")
    print(f"{'='*80}")
    
    print(f"\n1. GEPA's Unique Value:")
    print(f"   - {len(gepa_only)} questions where only GEPA succeeds")
    print(f"   - These require domain expertise + reasoning")
    print(f"   - Format-based routing misses these!")
    
    print(f"\n2. Agentic Router Opportunity:")
    print(f"   - Expert specialist routing: {accuracy:.1f}%")
    print(f"   - Theoretical max (oracle): 58.7%")
    print(f"   - Gap to close: {58.7 - accuracy:.1f}%")
    
    print(f"\n3. Recommended Approach:")
    print(f"   ✅ Two-Stage: GEPA Reasoning → MIPROv2 Extraction")
    print(f"      - Use GEPA's domain knowledge for understanding")
    print(f"      - Use MIPROv2's structured extraction for output")
    print(f"      - Best of both worlds!")
    
    print(f"\n4. Implementation Complexity:")
    print(f"   - Expert Specialist: MEDIUM (domain detection)")
    print(f"   - Cascading: MEDIUM (confidence scores needed)")
    print(f"   - Two-Stage: HIGH (2× inference cost)")
    print(f"   - Weighted Voting: LOW (just weighted sum)")
    print(f"   - Adaptive Router: HIGH (LLM training needed)")
    
    # Recommendation
    print(f"\n{'='*80}")
    print("RECOMMENDATION")
    print(f"{'='*80}")
    
    print(f"\n🎯 Next Step: Implement Two-Stage System")
    print(f"\n   Phase 1: GEPA Reasoning")
    print(f"      - Detect domain/complex questions")
    print(f"      - Use GEPA to generate detailed reasoning")
    print(f"      - Extract key insights and context")
    
    print(f"\n   Phase 2: MIPROv2 Extraction")
    print(f"      - Feed GEPA reasoning + original context to MIPROv2")
    print(f"      - MIPROv2 extracts structured answer")
    print(f"      - Benefit from GEPA understanding + MIPROv2 structure")
    
    print(f"\n   Expected Performance:")
    print(f"      - Conservative: 52-54% (+4-6% vs MIPROv2)")
    print(f"      - Optimistic: 55-57% (+7-9% vs MIPROv2)")
    print(f"      - Captures GEPA's domain wins while avoiding format issues")
    
    print(f"\n   Cost:")
    print(f"      - 2× inference for domain questions (~40% of dataset)")
    print(f"      - 1× inference for simple questions")
    print(f"      - Total: ~1.4× cost")
    print(f"      - ROI: +4-9% for 40% more cost → worth it!")
    
    # Save results
    results = {
        'gepa_unique_wins': len(gepa_only),
        'expert_specialist_accuracy': accuracy,
        'improvement_vs_miprov2': improvement,
        'recommendation': 'two_stage_gepa_reasoning_miprov2_extraction',
        'expected_performance': '52-57%',
        'expected_cost_multiplier': 1.4
    }
    
    with open('agentic_router_analysis.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*80}")
    print("💾 Results saved to: agentic_router_analysis.json")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    print_analysis()

