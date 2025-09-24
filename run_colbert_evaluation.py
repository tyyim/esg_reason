#!/usr/bin/env python3
"""
Focused ColBERT text-only evaluation command
Target: 41.5% accuracy (MMESGBench paper)
"""
import sys
import os
import json
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """Run ColBERT evaluation"""
    print("📝 ColBERT Text RAG Evaluation")
    print("Target: 41.5% accuracy (MMESGBench)")
    print("="*50)

    # Check if we have recent results
    results_file = "colbert_text_only_results.json"
    if os.path.exists(results_file):
        try:
            with open(results_file, 'r') as f:
                results = json.load(f)

            print("📊 EXISTING COLBERT RESULTS:")
            print(f"Accuracy: {results['accuracy']:.1%} (Target: {results['target_accuracy']:.1%})")
            print(f"Correct: {results['correct_predictions']}/{results['total_samples']}")
            print(f"F1 Score: {results['avg_f1_score']:.3f}")
            print(f"Processing Time: {results['avg_processing_time']:.1f}s per question")
            print(f"Tokens: {results['avg_tokens_per_query']:.0f} per query")

            target_met = "✅" if results['accuracy'] >= results['target_accuracy'] else "❌"
            print(f"\\nTarget Achievement: {target_met}")

            if results['accuracy'] >= results['target_accuracy']:
                print("🎉 ColBERT target accuracy achieved!")
            else:
                gap = results['target_accuracy'] - results['accuracy']
                print(f"📈 Gap to target: {gap:.1%}")

            # Show detailed results
            print(f"\\n📝 QUESTION BREAKDOWN:")
            for i, result in enumerate(results['results']):
                status = "✅" if result['is_correct'] else "❌"
                print(f"{i+1}. {status} {result['answer_format']}: '{result['predicted_answer']}' vs '{result['ground_truth']}'")

            return results

        except Exception as e:
            print(f"Error loading results: {e}")

    # If no results exist, run the evaluation
    print("No existing results found. Running ColBERT evaluation...")
    try:
        import subprocess
        env = os.environ.copy()
        env['TOKENIZERS_PARALLELISM'] = 'false'
        result = subprocess.run(['python', 'colbert_text_only_evaluation.py'],
                              env=env, capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ ColBERT evaluation completed successfully!")
            # Load and display results
            if os.path.exists(results_file):
                with open(results_file, 'r') as f:
                    results = json.load(f)
                print(f"Final Accuracy: {results['accuracy']:.1%}")
                return results
        else:
            print(f"❌ ColBERT evaluation failed: {result.stderr}")
            return None

    except Exception as e:
        print(f"Failed to run ColBERT evaluation: {e}")
        return None

if __name__ == "__main__":
    main()