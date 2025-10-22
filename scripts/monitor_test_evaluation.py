#!/usr/bin/env python3
"""
Monitor test set evaluation progress.

Checks checkpoint files and displays progress.
"""

import json
import os
from pathlib import Path
from datetime import datetime
import glob

def find_latest_checkpoint(pattern):
    """Find the most recent checkpoint file matching pattern."""
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def print_checkpoint_status(checkpoint_file):
    """Print status from checkpoint file."""
    if not checkpoint_file or not os.path.exists(checkpoint_file):
        return None
    
    with open(checkpoint_file, 'r') as f:
        data = json.load(f)
    
    total = data.get('total', 0)
    correct = data.get('correct_count', 0)
    accuracy = data.get('accuracy', 0.0)
    
    return {
        'file': checkpoint_file,
        'progress': total,
        'correct': correct,
        'accuracy': accuracy
    }

def main():
    print("\n" + "="*80)
    print("TEST SET EVALUATION PROGRESS MONITOR")
    print("="*80)
    print(f"\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nTotal questions: 654")
    print(f"Expected runtime: 3-4 hours (~20-30 seconds per question)")
    
    # Check for checkpoints
    approaches = {
        'Baseline': 'baseline_test_checkpoint_*.json',
        'MIPROv2': 'miprov2_test_checkpoint_*.json',
        'GEPA': 'gepa_test_checkpoint_*.json'
    }
    
    print("\n" + "-"*80)
    print("Current Progress:")
    print("-"*80)
    
    for name, pattern in approaches.items():
        checkpoint = find_latest_checkpoint(pattern)
        status = print_checkpoint_status(checkpoint)
        
        if status:
            progress_pct = status['progress'] / 654 * 100
            print(f"\n{name}:")
            print(f"  Progress: {status['progress']:3d}/654 ({progress_pct:5.1f}%)")
            print(f"  Accuracy: {status['accuracy']:5.1f}% ({status['correct']}/{status['progress']})")
            print(f"  File:     {Path(status['file']).name}")
        else:
            print(f"\n{name}:")
            print(f"  Status: Not started or no checkpoint yet")
    
    # Check for completion
    print("\n" + "-"*80)
    print("Completion Status:")
    print("-"*80)
    
    result_files = {
        'Baseline': 'baseline_test_predictions_*.json',
        'MIPROv2': 'miprov2_test_predictions_*.json',
        'GEPA': 'gepa_test_predictions_*.json'
    }
    
    completed = []
    for name, pattern in result_files.items():
        files = glob.glob(pattern)
        if files:
            latest = max(files, key=os.path.getmtime)
            with open(latest, 'r') as f:
                data = json.load(f)
            if data.get('total') == 654:
                completed.append(name)
                print(f"  ✅ {name}: COMPLETE ({data['accuracy']:.1f}%)")
            else:
                print(f"  ⏳ {name}: In progress ({data['total']}/654)")
        else:
            print(f"  ⏳ {name}: Running...")
    
    if len(completed) == 3:
        print("\n🎉 All evaluations complete!")
        print("\nNext steps:")
        print("  1. Review results in complete_test_analysis_*.json")
        print("  2. Compare with dev set findings")
        print("  3. Update documentation")
    else:
        print(f"\n⏳ {3 - len(completed)} evaluation(s) still running...")
        print("   Run this script again to check progress")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()

