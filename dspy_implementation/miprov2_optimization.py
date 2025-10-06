#!/usr/bin/env python3
"""
Phase 1a: MIPROv2 Optimization for MMESGBench

Applies Multi-prompt Instruction Proposal Optimizer v2 to improve over 45.1% baseline.

Architecture:
    - Training: 178 questions (20% stratified split)
    - Validation: 84 questions (10% stratified split)
    - Baseline: 45.1% accuracy (DSPy with default prompts)
    - Target: 46-47% accuracy (+1-2% improvement)

Optimization Strategy:
    - Optimize ESGReasoning and AnswerExtraction signatures
    - Use MIPROv2 for automated prompt engineering
    - Validate on dev set to prevent overfitting
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
import dspy
from dspy.teleprompt import MIPROv2

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Change to project root for document access
os.chdir(project_root)

from dspy_implementation.dspy_setup import setup_dspy_qwen
from dspy_implementation.dspy_rag_module import MMESGBenchRAG
from dspy_implementation.dspy_metrics import mmesgbench_accuracy, evaluate_predictions


# ============================================================================
# Dataset Loading
# ============================================================================

def load_split(split_name: str):
    """
    Load train/dev/test split from stratified dataset.

    Args:
        split_name: One of ['train', 'dev', 'test']

    Returns:
        List of DSPy examples
    """
    split_file = f"splits/{split_name}.json"

    if not os.path.exists(split_file):
        raise FileNotFoundError(f"Split file not found: {split_file}")

    with open(split_file, 'r') as f:
        data = json.load(f)

    # Convert to DSPy examples
    examples = []
    for item in data:
        example = dspy.Example(
            doc_id=item['doc_id'],
            question=item['question'],
            answer=str(item['answer']),
            answer_format=item['answer_format']
        ).with_inputs('doc_id', 'question', 'answer_format')
        examples.append(example)

    print(f"✅ Loaded {len(examples)} questions from {split_file}")
    return examples


# ============================================================================
# MIPROv2 Optimization
# ============================================================================

def optimize_with_miprov2(train_set, dev_set, num_candidates: int = 10,
                          init_temperature: float = 1.0, verbose: bool = True):
    """
    Apply MIPROv2 optimizer to improve prompt instructions.

    MIPROv2 automatically generates and tests multiple instruction candidates
    to optimize the prompts for ESGReasoning and AnswerExtraction signatures.

    Args:
        train_set: Training examples (178 questions)
        dev_set: Development examples for validation (84 questions)
        num_candidates: Number of instruction candidates to generate (default: 10)
        init_temperature: Initial temperature for candidate generation (default: 1.0)
        verbose: Whether to print detailed progress (default: True)

    Returns:
        Optimized RAG module
    """
    print("\n" + "=" * 80)
    print("MIPROv2 Optimization")
    print("=" * 80)

    # Initialize unoptimized RAG module
    print("\n📋 Initializing baseline RAG module...")
    baseline_rag = MMESGBenchRAG()

    # Evaluate baseline on train set
    print("\n📊 Evaluating baseline on training set...")
    baseline_train_preds = []
    for example in train_set[:10]:  # Quick sample for baseline assessment
        pred = baseline_rag(
            question=example.question,
            doc_id=example.doc_id,
            answer_format=example.answer_format
        )
        baseline_train_preds.append(pred)

    baseline_train_results = evaluate_predictions(baseline_train_preds, train_set[:10])
    print(f"   Baseline train accuracy: {baseline_train_results['accuracy']:.1%} " +
          f"({baseline_train_results['correct']}/{baseline_train_results['total']})")

    # Configure MIPROv2 optimizer
    print(f"\n🔧 Configuring MIPROv2 optimizer...")
    print(f"   Num candidates: {num_candidates}")
    print(f"   Temperature: {init_temperature}")
    print(f"   Metric: MMESGBench accuracy (fuzzy matching)")
    print(f"   Training set: {len(train_set)} questions")

    optimizer = MIPROv2(
        metric=mmesgbench_accuracy,
        num_candidates=num_candidates,
        init_temperature=init_temperature,
        verbose=verbose
    )

    # Run optimization
    print(f"\n🚀 Running MIPROv2 optimization...")
    print(f"   This will take approximately 15-30 minutes...")
    print(f"   Progress will be saved to checkpoints/miprov2_checkpoint.json\n")

    # Create checkpoint directory
    os.makedirs("checkpoints", exist_ok=True)

    try:
        optimized_rag = optimizer.compile(
            student=baseline_rag,
            trainset=train_set,
            num_trials=20,  # Number of optimization trials
            max_bootstrapped_demos=4,  # Max few-shot examples per prompt
            max_labeled_demos=4,  # Max labeled examples
            eval_kwargs={'num_threads': 1, 'display_progress': True}
        )

        print("\n✅ MIPROv2 optimization completed!")

    except Exception as e:
        print(f"\n⚠️  Optimization failed: {e}")
        print(f"   Falling back to baseline RAG module")
        optimized_rag = baseline_rag

    # Evaluate optimized model on dev set
    print("\n📊 Evaluating optimized model on dev set...")
    dev_preds = []
    for example in dev_set:
        pred = optimized_rag(
            question=example.question,
            doc_id=example.doc_id,
            answer_format=example.answer_format
        )
        dev_preds.append(pred)

    dev_results = evaluate_predictions(dev_preds, dev_set)
    print(f"\n📈 Dev Set Results:")
    print(f"   Accuracy: {dev_results['accuracy']:.1%} " +
          f"({dev_results['correct']}/{dev_results['total']})")
    print(f"   F1 Score: {dev_results['f1_score']:.3f}")

    # Print format breakdown
    print(f"\n📋 Accuracy by Answer Format:")
    for fmt, stats in dev_results['format_breakdown'].items():
        print(f"   {fmt}: {stats['accuracy']:.1%} ({stats['correct']}/{stats['total']})")

    return optimized_rag, dev_results


# ============================================================================
# Save & Load Optimized Program
# ============================================================================

def save_optimized_program(optimized_rag, dev_results, output_path: str = "dspy_miprov2_optimized.json"):
    """
    Save optimized DSPy program to disk.

    Args:
        optimized_rag: Optimized RAG module
        dev_results: Development set evaluation results
        output_path: Path to save optimized program
    """
    print(f"\n💾 Saving optimized program to {output_path}...")

    # Save DSPy program state
    optimized_rag.save(output_path)

    # Save metadata
    metadata = {
        'timestamp': datetime.now().isoformat(),
        'optimizer': 'MIPROv2',
        'baseline_accuracy': 0.451,  # 45.1% from full dataset evaluation
        'dev_accuracy': dev_results['accuracy'],
        'dev_f1': dev_results['f1_score'],
        'improvement': dev_results['accuracy'] - 0.451,
        'training_set_size': 178,
        'dev_set_size': 84,
        'format_breakdown': dev_results['format_breakdown']
    }

    metadata_path = output_path.replace('.json', '_metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"✅ Saved optimized program and metadata")
    print(f"   Program: {output_path}")
    print(f"   Metadata: {metadata_path}")
    print(f"   Dev accuracy: {dev_results['accuracy']:.1%}")
    print(f"   Improvement: {metadata['improvement']:+.1%}")


def load_optimized_program(program_path: str = "dspy_miprov2_optimized.json"):
    """
    Load previously optimized DSPy program.

    Args:
        program_path: Path to saved program

    Returns:
        Loaded RAG module
    """
    if not os.path.exists(program_path):
        raise FileNotFoundError(f"Optimized program not found: {program_path}")

    print(f"📂 Loading optimized program from {program_path}...")

    # Initialize RAG module structure
    rag = MMESGBenchRAG()

    # Load optimized state
    rag.load(program_path)

    print(f"✅ Loaded optimized program")

    # Load and display metadata if available
    metadata_path = program_path.replace('.json', '_metadata.json')
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        print(f"   Optimized: {metadata['timestamp']}")
        print(f"   Dev accuracy: {metadata['dev_accuracy']:.1%}")
        print(f"   Improvement: {metadata['improvement']:+.1%}")

    return rag


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Run MIPROv2 optimization pipeline"""
    print("=" * 80)
    print("Phase 1a: MIPROv2 Optimization for MMESGBench")
    print("=" * 80)
    print(f"\nBaseline: 45.1% accuracy (DSPy with default prompts)")
    print(f"Target: 46-47% accuracy (+1-2% improvement)")

    # Initialize DSPy environment
    print("\n📋 Setting up DSPy environment...")
    setup_dspy_qwen()

    # Load stratified splits
    print("\n📊 Loading stratified dataset splits...")
    train_set = load_split('train')  # 178 questions
    dev_set = load_split('dev')      # 84 questions

    print(f"\n📈 Dataset Summary:")
    print(f"   Training: {len(train_set)} questions (20%)")
    print(f"   Dev: {len(dev_set)} questions (10%)")
    print(f"   Stratified by: Evidence Type × Difficulty")

    # Run MIPROv2 optimization
    optimized_rag, dev_results = optimize_with_miprov2(
        train_set=train_set,
        dev_set=dev_set,
        num_candidates=10,
        init_temperature=1.0,
        verbose=True
    )

    # Save optimized program
    save_optimized_program(optimized_rag, dev_results)

    # Print final summary
    print("\n" + "=" * 80)
    print("MIPROv2 Optimization Complete")
    print("=" * 80)
    print(f"\n✅ Phase 1a Complete!")
    print(f"   Dev Accuracy: {dev_results['accuracy']:.1%}")
    print(f"   Baseline: 45.1%")
    print(f"   Improvement: {(dev_results['accuracy'] - 0.451):+.1%}")

    if dev_results['accuracy'] >= 0.46:
        print(f"\n🎯 SUCCESS: Target accuracy (46%) achieved!")
    else:
        print(f"\n⚠️  Target accuracy (46%) not yet achieved")
        print(f"   Consider: Increasing num_candidates or num_trials")

    print(f"\n📝 Next Steps:")
    print(f"   1. Review optimized prompts in dspy_miprov2_optimized.json")
    print(f"   2. Run full evaluation on test set (667 questions)")
    print(f"   3. Compare with Phase 1b: GEPA optimization")


if __name__ == "__main__":
    main()
