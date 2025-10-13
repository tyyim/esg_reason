#!/usr/bin/env python3
"""
Check progress of DSPy baseline evaluation
"""

import json
import os
from pathlib import Path

checkpoint_file = "dspy_baseline_dev_checkpoint.json"
results_file = "dspy_baseline_dev_results.json"

print("=" * 60)
print("DSPy Baseline Evaluation Progress")
print("=" * 60)

# Check checkpoint
if os.path.exists(checkpoint_file):
    with open(checkpoint_file, 'r') as f:
        checkpoint = json.load(f)

    predictions = checkpoint.get('predictions', [])
    print(f"\n📊 Checkpoint Status:")
    print(f"   Questions completed: {len(predictions)}/93")
    print(f"   Progress: {len(predictions)/93*100:.1f}%")

    if len(predictions) > 0:
        # Count correct predictions
        correct = sum(1 for p in predictions if p.get('answer') != 'Failed to generate')
        print(f"   Valid predictions: {correct}/{len(predictions)}")
else:
    print("\n⏳ No checkpoint found yet - evaluation just started")

# Check final results
if os.path.exists(results_file):
    print(f"\n✅ Final results available: {results_file}")
    with open(results_file, 'r') as f:
        results = json.load(f)

    metrics = results.get('overall_metrics', {})
    print(f"\n🎯 Final Metrics:")
    print(f"   Accuracy: {metrics.get('accuracy', 0)*100:.1f}%")
    print(f"   Correct: {metrics.get('correct', 0)}/{metrics.get('total', 0)}")
    print(f"   F1 Score: {metrics.get('f1_score', 0):.3f}")
else:
    print(f"\n⏳ Final results not yet available")

print("\n" + "=" * 60)
