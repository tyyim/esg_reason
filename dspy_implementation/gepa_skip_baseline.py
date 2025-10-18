#!/usr/bin/env python3
"""
GEPA Optimization - SKIP BASELINE EVALUATION

This script jumps straight to GEPA optimization without wasting time on baseline evaluation.
We already know the baseline: qwen2.5-7b = 58.1% answer accuracy.

Key difference from gepa_qwen7b_optimization.py:
- ❌ NO Step 1 baseline evaluation (saves 10-15 minutes!)
- ✅ Direct to Step 2: GEPA optimization
- ✅ Uses full dataset (186 train / 93 dev)
"""

import os
import sys
import dspy
from dotenv import load_dotenv
from dspy.teleprompt import GEPA
import mlflow
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dspy_implementation.dspy_dataset import MMESGBenchDataset
from dspy_implementation.dspy_rag_enhanced import BaselineMMESGBenchRAG
from dspy_implementation.dspy_metrics_gepa_fixed import mmesgbench_answer_only_gepa_metric

# Load environment
load_dotenv()

def main():
    print("\n" + "="*80)
    print("GEPA OPTIMIZATION - SKIP BASELINE (Fast Development Mode)")
    print("="*80)

    # Generate run name with timestamp
    run_name = f"gepa_skip_baseline_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"\nRun Name: {run_name}")

    # Initialize MLFlow
    mlflow.set_tracking_uri("file:///Users/victoryim/Local_Git/CC/mlruns")
    mlflow.set_experiment("ESG_GEPA_Fast_Dev")
    mlflow.start_run(run_name=run_name)
    print(f"✅ MLFlow tracker initialized")
    print(f"   Experiment: ESG_GEPA_Fast_Dev")
    print(f"   Run ID: {mlflow.active_run().info.run_id}")

    # Load dataset
    print(f"\n📊 Loading dataset...")
    dataset = MMESGBenchDataset()
    train_set = dataset.train_set
    dev_set = dataset.dev_set
    print(f"   Train: {len(train_set)} examples")
    print(f"   Dev: {len(dev_set)} examples")

    # Log dataset info
    mlflow.log_param("train_size", len(train_set))
    mlflow.log_param("dev_size", len(dev_set))
    mlflow.log_param("skip_baseline", True)

    # Configure student model (qwen2.5-7b)
    print(f"\n🎓 Configuring student model: qwen2.5-7b-instruct...")
    student_lm = dspy.LM(
        model='openai/qwen2.5-7b-instruct',
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        api_base='https://dashscope.aliyuncs.com/compatible-mode/v1',
        temperature=0.0,
        max_tokens=1024
    )
    dspy.configure(lm=student_lm)
    print(f"✅ Student model configured")

    # Initialize RAG module
    print(f"\n🔍 Initializing RAG module...")
    rag_student = BaselineMMESGBenchRAG()
    print(f"✅ RAG module initialized")

    # Configure reflection model (qwen-max)
    print(f"\n🧬 Configuring reflection model: qwen-max...")
    reflection_lm = dspy.LM(
        model='openai/qwen-max',
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        api_base='https://dashscope.aliyuncs.com/compatible-mode/v1',
        temperature=1.0,  # Higher temp for creative reflection
        max_tokens=4096   # Longer for detailed analysis
    )
    print(f"✅ Reflection model configured")

    # Create GEPA optimizer
    print(f"\n⚙️ Creating GEPA optimizer...")
    optimizer = GEPA(
        metric=mmesgbench_answer_only_gepa_metric,
        reflection_lm=reflection_lm,
        auto='light',  # Light mode: ~10-20 candidates, faster
        reflection_minibatch_size=3,
        candidate_selection_strategy='pareto',
        use_merge=True,
        track_stats=True,
        seed=42
    )
    print(f"✅ GEPA optimizer created")

    # Log GEPA parameters
    mlflow.log_param("optimizer", "GEPA")
    mlflow.log_param("gepa_mode", "light")
    mlflow.log_param("reflection_lm", "qwen-max")
    mlflow.log_param("student_lm", "qwen2.5-7b-instruct")
    mlflow.log_param("reflection_minibatch_size", 3)
    mlflow.log_param("selection_strategy", "pareto")

    # Run GEPA optimization (NO BASELINE STEP!)
    print(f"\n" + "="*80)
    print("STARTING GEPA OPTIMIZATION")
    print("="*80)
    print(f"\n💡 SKIPPING baseline evaluation (we already know: 58.1% answer accuracy)")
    print(f"🚀 Jumping straight to GEPA optimization...")
    print(f"⏱️  Expected time: ~30-45 minutes for light mode\n")

    try:
        optimized_rag = optimizer.compile(
            student=rag_student,
            trainset=train_set,  # Full 186 examples
            valset=dev_set        # Full 93 examples
        )

        print(f"\n" + "="*80)
        print("✅ GEPA OPTIMIZATION COMPLETE!")
        print("="*80)

        # Save optimized program
        output_dir = "dspy_implementation/optimized_programs"
        os.makedirs(output_dir, exist_ok=True)
        output_file = f"{output_dir}/{run_name}.json"
        optimized_rag.save(output_file)
        print(f"\n💾 Saved optimized program to: {output_file}")
        mlflow.log_artifact(output_file)

        # Evaluate optimized model
        print(f"\n📊 Evaluating optimized model on dev set...")
        from dspy.evaluate import Evaluate
        evaluator = Evaluate(
            devset=dev_set,
            metric=lambda gold, pred, trace=None: mmesgbench_answer_only_gepa_metric(gold, pred, trace, pred_name=None),
            num_threads=1,
            display_progress=True
        )
        optimized_score = evaluator(optimized_rag)

        print(f"\n📈 RESULTS:")
        print(f"   Baseline (known): 58.1%")
        print(f"   Optimized (GEPA): {optimized_score*100:.1f}%")
        print(f"   Improvement: {(optimized_score - 0.581)*100:+.1f}%")

        # Log final metrics
        mlflow.log_metric("baseline_accuracy", 0.581)
        mlflow.log_metric("optimized_accuracy", optimized_score)
        mlflow.log_metric("improvement", optimized_score - 0.581)

        mlflow.end_run()
        return optimized_rag, optimized_score

    except Exception as e:
        print(f"\n❌ GEPA optimization failed: {e}")
        import traceback
        traceback.print_exc()
        mlflow.end_run(status="FAILED")
        raise

if __name__ == "__main__":
    main()
