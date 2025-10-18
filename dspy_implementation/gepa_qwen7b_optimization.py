#!/usr/bin/env python3
"""
GEPA Optimization with qwen2.5-7b-instruct

GEPA (Genetic-Pareto) optimizer uses reflective prompt evolution:
- Reflection LM (qwen-max) analyzes failures and proposes better instructions
- Task LM (qwen2.5-7b) executes with evolved prompts
- Rich textual feedback guides optimization

Key differences from MIPROv2:
1. Uses reflection_lm instead of prompt_model
2. Metric returns {"score": float, "feedback": str}
3. Feedback-driven prompt evolution (not just score-based)
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import dspy
from dspy.teleprompt import GEPA
import mlflow

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from dspy_implementation.dspy_setup import setup_dspy_qwen
from dspy_implementation.dspy_dataset import MMESGBenchDataset
from dspy_implementation.dspy_rag_enhanced import BaselineMMESGBenchRAG
from dspy_implementation.dspy_metrics_gepa import mmesgbench_answer_only_gepa_metric
from dspy_implementation.dspy_metrics_enhanced import evaluate_predictions_enhanced
from dspy_implementation.mlflow_tracking import DSPyMLFlowTracker, create_run_name


def evaluate_rag_with_metrics(rag_module, examples, desc: str = "Evaluation"):
    """Evaluate RAG module with enhanced metrics."""
    predictions = []

    for example in tqdm(examples, desc=desc):
        try:
            pred = rag_module(
                question=example.question,
                doc_id=example.doc_id,
                answer_format=example.answer_format
            )
            predictions.append(pred)
        except Exception as e:
            print(f"\n⚠️  Error on question: {e}")
            predictions.append(dspy.Prediction(answer="Failed"))

    results = evaluate_predictions_enhanced(predictions, examples)
    return results, predictions


def optimize_with_gepa(train_set, dev_set, mlflow_tracker):
    """
    Run GEPA optimization with qwen2.5-7b student and qwen-max reflection LM.

    GEPA workflow:
    1. Student (qwen2.5-7b) executes task
    2. Metric provides rich feedback (not just score)
    3. Reflection LM (qwen-max) analyzes feedback + traces
    4. Proposes improved instructions based on failures
    5. Repeat with evolved prompts
    """
    print("\n" + "=" * 80)
    print("GEPA OPTIMIZATION - Reflective Prompt Evolution")
    print("=" * 80)
    print(f"\n🧬 Reflection LM: qwen-max (analyzes failures, proposes improvements)")
    print(f"🎓 Task LM: qwen2.5-7b-instruct (executes with evolved prompts)")
    print(f"📝 Metric: Returns score + detailed feedback")

    # ==================================================
    # Step 1: Evaluate Student Baseline (qwen2.5-7b)
    # ==================================================
    print(f"\n📊 Step 1: Evaluating STUDENT BASELINE (qwen2.5-7b-instruct)...")

    # Configure student model (task execution)
    student_lm = dspy.LM(
        model='openai/qwen2.5-7b-instruct',
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        api_base='https://dashscope.aliyuncs.com/compatible-mode/v1',
        temperature=0.0,  # Deterministic for evaluation
        max_tokens=1024
    )

    dspy.configure(lm=student_lm)
    print(f"✅ Configured student model: qwen2.5-7b-instruct")

    rag_student = BaselineMMESGBenchRAG()
    baseline_results, baseline_preds = evaluate_rag_with_metrics(
        rag_student, dev_set, "Baseline eval (student)"
    )

    print(f"\n📈 Student Baseline Results:")
    print(f"   Retrieval: {baseline_results['retrieval_accuracy']:.1%}")
    print(f"   Answer: {baseline_results['answer_accuracy']:.1%}")
    print(f"   End-to-End: {baseline_results['end_to_end_accuracy']:.1%}")

    # Log baseline metrics
    mlflow_tracker.log_baseline(
        metrics=baseline_results,
        config={'model': 'qwen2.5-7b-instruct', 'phase': 'gepa_baseline'}
    )

    # ==================================================
    # Step 2: Configure Reflection LM (qwen-max)
    # ==================================================
    print(f"\n🔧 Step 2: Configuring REFLECTION LM (qwen-max)...")

    reflection_lm = dspy.LM(
        model='openai/qwen-max',
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        api_base='https://dashscope.aliyuncs.com/compatible-mode/v1',
        temperature=1.0,  # Higher temp for creative reflection
        max_tokens=4096   # Longer for detailed analysis
    )

    print(f"✅ Configured reflection model: qwen-max")
    print(f"   Temperature: 1.0 (creative prompt proposals)")
    print(f"   Max tokens: 4096 (detailed failure analysis)")

    # ==================================================
    # Step 3: Run GEPA Optimization
    # ==================================================
    print(f"\n🧬 Step 3: Running GEPA optimization...")
    print(f"   Reflection LM (qwen-max): Analyzes failures + proposes improvements")
    print(f"   Task LM (qwen2.5-7b): Executes with evolved prompts")
    print(f"   Mode: auto='light' (~10-20 candidates, 30-45 min)")
    print(f"   Metric: Rich textual feedback for each prediction")

    mlflow_tracker.log_params({
        'optimizer': 'GEPA',
        'reflection_lm': 'qwen-max',
        'task_lm': 'qwen2.5-7b-instruct',
        'auto_mode': 'light',
        'train_size': len(train_set),
        'dev_size': len(dev_set),
        'metric_type': 'answer_only_with_feedback'
    })

    print(f"\n💡 Key Insight:")
    print(f"   Unlike MIPROv2 (score-only), GEPA uses rich feedback:")
    print(f"   - What went wrong (missing pages, wrong extraction)")
    print(f"   - Why it went wrong (analysis of context)")
    print(f"   - How to improve (specific recommendations)")
    print(f"   Reflection LM reads this and proposes better prompts!\n")

    # Create GEPA optimizer
    optimizer = GEPA(
        metric=mmesgbench_answer_only_gepa_metric,  # Returns {"score": float, "feedback": str}
        reflection_lm=reflection_lm,  # qwen-max for reflection
        auto='light',  # Light mode for initial test
        reflection_minibatch_size=3,  # 3 examples per reflection
        candidate_selection_strategy='pareto',  # Pareto frontier selection
        use_merge=True,  # Enable merge-based optimization
        track_stats=True,  # Return detailed statistics
        seed=42  # Reproducibility
    )

    print(f"✅ GEPA optimizer configured")
    print(f"   Reflection minibatch size: 3 examples")
    print(f"   Selection strategy: Pareto (non-dominated candidates)")
    print(f"   Merge enabled: Yes (combines good components)")

    try:
        # Run GEPA optimization
        # Note: GEPA doesn't distinguish task_model - it uses dspy.configure()
        print(f"\n🚀 Starting GEPA optimization...")
        print(f"   This will take ~30-45 minutes for light mode")
        print(f"   Watch for reflection insights in the output!\n")

        optimized_rag = optimizer.compile(
            student=rag_student,
            trainset=train_set,
            valset=dev_set  # Explicit valset for fair comparison
            # Note: GEPA does NOT support requires_permission_to_run parameter
        )

        print("\n✅ GEPA optimization completed!")

    except Exception as e:
        print(f"\n❌ Optimization failed: {e}")
        import traceback
        traceback.print_exc()
        raise

    # ==================================================
    # Step 4: Evaluate Optimized Student
    # ==================================================
    print(f"\n📊 Step 4: Evaluating OPTIMIZED STUDENT...")

    # Ensure student model is configured for evaluation
    dspy.configure(lm=student_lm)

    opt_results, opt_preds = evaluate_rag_with_metrics(
        optimized_rag, dev_set, "Optimized eval (student)"
    )

    print(f"\n📈 Optimized Student Results:")
    print(f"   Retrieval: {opt_results['retrieval_accuracy']:.1%}")
    print(f"   Answer: {opt_results['answer_accuracy']:.1%}")
    print(f"   End-to-End: {opt_results['end_to_end_accuracy']:.1%}")

    # Log optimized metrics
    mlflow_tracker.log_final_results(opt_results)

    # ==================================================
    # Step 5: Compare Results
    # ==================================================
    print(f"\n" + "=" * 80)
    print("GEPA OPTIMIZATION RESULTS")
    print("=" * 80)

    print(f"\n📊 Answer Accuracy (PRIMARY METRIC):")
    print(f"   Baseline:  {baseline_results['answer_accuracy']:.1%}")
    print(f"   Optimized: {opt_results['answer_accuracy']:.1%}")
    delta_answer = opt_results['answer_accuracy'] - baseline_results['answer_accuracy']
    print(f"   Change:    {delta_answer:+.1%} {'✅' if delta_answer > 0 else '⚠️'}")

    print(f"\n📊 End-to-End Accuracy:")
    print(f"   Baseline:  {baseline_results['end_to_end_accuracy']:.1%}")
    print(f"   Optimized: {opt_results['end_to_end_accuracy']:.1%}")
    delta_e2e = opt_results['end_to_end_accuracy'] - baseline_results['end_to_end_accuracy']
    print(f"   Change:    {delta_e2e:+.1%}")

    print(f"\n📊 Retrieval Accuracy (should be constant):")
    print(f"   Baseline:  {baseline_results['retrieval_accuracy']:.1%}")
    print(f"   Optimized: {opt_results['retrieval_accuracy']:.1%}")
    print(f"   Change:    {opt_results['retrieval_accuracy'] - baseline_results['retrieval_accuracy']:+.1%}")

    # Success check
    if delta_answer > 0:
        print(f"\n✅ SUCCESS: GEPA improved answer accuracy by {delta_answer:+.1%}!")
        print(f"   Reflective prompt evolution worked! 🎉")
    elif delta_answer == 0:
        print(f"\n⚠️  NEUTRAL: No improvement, but also no degradation")
    else:
        print(f"\n⚠️  WARNING: Answer accuracy decreased by {delta_answer:.1%}")
        print(f"   This is unusual for GEPA - check the logs for issues")

    return optimized_rag, opt_results, baseline_results


def main():
    """Main execution function."""
    print("\n" + "=" * 80)
    print("GEPA OPTIMIZATION - Qwen 2.5 7B with Qwen-Max Reflection")
    print("=" * 80)

    # Create run name
    run_name = create_run_name("gepa_qwen7b")
    print(f"\nRun Name: {run_name}")

    # Initialize MLFlow tracker
    mlflow_tracker = DSPyMLFlowTracker(
        experiment_name="ESG_GEPA_Optimization"
    )

    # Start MLFlow run
    mlflow_tracker.start_run(
        run_name=run_name,
        tags={'optimizer': 'GEPA', 'model': 'qwen2.5-7b-instruct', 'reflection': 'qwen-max'}
    )

    # Load dataset
    print(f"\n📊 Loading MMESGBench dataset...")
    dataset = MMESGBenchDataset()
    train_set = dataset.train_set
    dev_set = dataset.dev_set

    print(f"   Training: {len(train_set)} examples")
    print(f"   Dev: {len(dev_set)} examples")

    # Run GEPA optimization
    optimized_rag, opt_results, baseline_results = optimize_with_gepa(
        train_set, dev_set, mlflow_tracker
    )

    # ==================================================
    # Save Results
    # ==================================================
    print(f"\n💾 Saving results...")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"gepa_qwen7b_results_{timestamp}.json"

    results_data = {
        "timestamp": datetime.now().isoformat(),
        "run_name": run_name,
        "optimizer": "GEPA",
        "reflection_lm": "qwen-max",
        "task_lm": "qwen2.5-7b-instruct",
        "optimization": {
            "auto_mode": "light",
            "train_size": len(train_set),
            "dev_size": len(dev_set)
        },
        "baseline_results": baseline_results,
        "optimized_results": opt_results,
        "improvements": {
            "answer_accuracy": opt_results['answer_accuracy'] - baseline_results['answer_accuracy'],
            "end_to_end_accuracy": opt_results['end_to_end_accuracy'] - baseline_results['end_to_end_accuracy']
        }
    }

    with open(results_file, 'w') as f:
        json.dump(results_data, f, indent=2)

    print(f"   Saved to: {results_file}")

    # Save optimized module
    module_file = f"dspy_implementation/optimized_modules/gepa_qwen7b_{timestamp}.json"
    os.makedirs("dspy_implementation/optimized_modules", exist_ok=True)
    optimized_rag.save(module_file)
    print(f"   Optimized module: {module_file}")

    # Final summary
    print(f"\n" + "=" * 80)
    print("EXPERIMENT COMPLETE")
    print("=" * 80)
    print(f"\n📊 Final Comparison:")
    print(f"   Baseline Answer Accuracy: {baseline_results['answer_accuracy']:.1%}")
    print(f"   Optimized Answer Accuracy: {opt_results['answer_accuracy']:.1%}")
    print(f"   Improvement: {opt_results['answer_accuracy'] - baseline_results['answer_accuracy']:+.1%}")
    print(f"\n📁 Results saved to: {results_file}")
    print(f"📁 Module saved to: {module_file}")
    print(f"\n🔬 Next: Compare GEPA vs MIPROv2 teacher-student results!")


if __name__ == "__main__":
    main()
