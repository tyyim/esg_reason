#!/usr/bin/env python3
"""
Analyze and visualize cheatsheet growth from DC-CU evaluation results
"""

import json
import sys
from pathlib import Path

def analyze_cheatsheet_evolution(results_file):
    """Analyze how cheatsheet evolved during evaluation"""
    
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    print("="*70)
    print("DeepSeek DC-CU Cheatsheet Evolution Analysis")
    print("="*70)
    
    print(f"\nModel: {results['model']}")
    print(f"Dataset: {results['dataset']}")
    print(f"Total Questions: {results['total']}")
    print(f"Final Accuracy: {results['accuracy']*100:.1f}%")
    print(f"Final Cheatsheet: {len(results['final_cheatsheet'])} characters")
    
    if 'cheatsheet_evolution' not in results:
        print("\n⚠️  No cheatsheet evolution data found in results")
        return
    
    evolution = results['cheatsheet_evolution']
    
    print(f"\n" + "="*70)
    print("Cheatsheet Growth Pattern")
    print("="*70)
    
    # Analyze growth pattern
    growth_points = []
    for i, entry in enumerate(evolution):
        if i == 0 or entry['length'] != evolution[i-1]['length']:
            growth_points.append(entry)
    
    print(f"\nTotal growth events: {len(growth_points)}")
    print(f"Starting length: {evolution[0]['length']} chars")
    print(f"Ending length: {evolution[-1]['length']} chars")
    print(f"Net growth: {evolution[-1]['length'] - evolution[0]['length']} chars")
    
    # Show growth milestones
    print(f"\n" + "="*70)
    print("Growth Milestones (every 10 questions)")
    print("="*70)
    print(f"{'Question':<10} {'Length':<12} {'Change':<12} {'Accuracy'}")
    print("-"*70)
    
    for i in range(0, len(evolution), 10):
        entry = evolution[i]
        if i > 0:
            prev = evolution[i-10] if i >= 10 else evolution[0]
            change = entry['length'] - prev['length']
            change_str = f"+{change}" if change > 0 else str(change)
        else:
            change_str = "baseline"
        
        # Calculate accuracy up to this point
        correct_so_far = sum(1 for e in evolution[:i+1] if e.get('correct', False))
        acc = (correct_so_far / (i+1) * 100) if i+1 > 0 else 0
        
        print(f"{i+1:<10} {entry['length']:<12} {change_str:<12} {acc:.1f}%")
    
    # Check for consolidation
    print(f"\n" + "="*70)
    print("Consolidation Analysis")
    print("="*70)
    
    max_length = max(e['length'] for e in evolution)
    max_idx = next(i for i, e in enumerate(evolution) if e['length'] == max_length)
    final_length = evolution[-1]['length']
    
    print(f"Max cheatsheet size: {max_length} chars at question {max_idx+1}")
    print(f"Final cheatsheet size: {final_length} chars at question {len(evolution)}")
    
    if final_length < max_length:
        reduction = max_length - final_length
        reduction_pct = (reduction / max_length * 100)
        print(f"✅ CONSOLIDATION DETECTED!")
        print(f"   Reduced by {reduction} chars ({reduction_pct:.1f}%)")
        print(f"   Paper's prediction confirmed: Cheatsheet consolidates over time")
    elif final_length == max_length:
        print(f"→ Cheatsheet reached steady state (no consolidation yet)")
    else:
        print(f"↗ Cheatsheet still growing")
    
    # Show significant growth/shrinkage events
    print(f"\n" + "="*70)
    print("Significant Changes (>500 chars)")
    print("="*70)
    
    for i in range(1, len(evolution)):
        change = evolution[i]['length'] - evolution[i-1]['length']
        if abs(change) > 500:
            direction = "📈 GROWTH" if change > 0 else "📉 CONSOLIDATION"
            print(f"Q{i+1}: {direction} of {abs(change)} chars ({evolution[i-1]['length']} → {evolution[i]['length']})")
    
    # Errors
    errors = [e for e in evolution if 'error' in e]
    if errors:
        print(f"\n" + "="*70)
        print(f"Errors: {len(errors)}")
        print("="*70)
        for err in errors:
            print(f"Q{err['iteration']}: {err.get('error', 'Unknown')}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        results_file = sys.argv[1]
    else:
        # Find most recent DeepSeek DC-CU results
        results_dir = Path("results/deepseek_comparison")
        files = list(results_dir.glob("dc_cu_deepseek_dev_*.json"))
        if not files:
            print("No results files found!")
            sys.exit(1)
        results_file = max(files, key=lambda f: f.stat().st_mtime)
        print(f"Using most recent file: {results_file.name}\n")
    
    analyze_cheatsheet_evolution(results_file)

