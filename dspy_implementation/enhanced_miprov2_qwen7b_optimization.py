#!/usr/bin/env python3
"""
MIPROv2 Optimization with Separate Teacher/Student Models

Key Setup:
- Teacher (prompt_model): qwen-max - Generates optimized prompts
- Student (task_model): qwen2.5-7b-instruct - Executes with those prompts

This tests if strong model prompts can help weak model perform better!
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import dspy
from dspy.teleprompt import MIPROv2
import mlflow

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from dspy_implementation.dspy_setup import setup_dspy_qwen
from dspy_implementation.dspy_dataset import MMESGBenchDataset
from dspy_implementation.dspy_rag_enhanced import BaselineMMESGBenchRAG
from dspy_implementation.dspy_metrics_enhanced import (
    mmesgbench_end_to_end_metric,
    evaluate_predictions_enhanced
)
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


def optimize_with_teacher_student(train_set, dev_set, mlflow_tracker):
    """
    Run MIPROv2 with separate teacher and student models.

    Teacher (qwen-max): Generates optimized prompts
    Student (qwen2.5-7b): Uses those prompts to answer questions
    """
    print("\n" + "=" * 80)
    print("TEACHER-STUDENT OPTIMIZATION")
    print("=" * 80)
    print(f"\n🎓 Teacher Model: qwen-max (prompt generation)")
    print(f"🎓 Student Model: qwen2.5-7b-instruct (task execution)")

    # ==================================================
    # Step 1: Evaluate Student Baseline (qwen2.5-7b)
    # ==================================================
    print(f"\n📊 Step 1: Evaluating STUDENT BASELINE (qwen2.5-7b-instruct)...")

    # Configure student model
    student_lm = dspy.LM(
        model='openai/qwen2.5-7b-instruct',
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        api_base='https://dashscope.aliyuncs.com/compatible-mode/v1',
        temperature=0.0,
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
        config={'model': 'qwen2.5-7b-instruct', 'phase': 'student_baseline'}
    )

    # ==================================================
    # Step 2: Configure Teacher Model (qwen-max)
    # ==================================================
    print(f"\n🔧 Step 2: Configuring TEACHER MODEL (qwen-max) for optimization...")

    teacher_lm = dspy.LM(
        model='openai/qwen-max',
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        api_base='https://dashscope.aliyuncs.com/compatible-mode/v1',
        temperature=1.0,  # Higher temp for diverse prompt generation
        max_tokens=2048
    )

    print(f"✅ Configured teacher model: qwen-max")

    # ==================================================
    # Step 3: Run MIPROv2 with Teacher/Student Split
    # ==================================================
    print(f"\n🚀 Step 3: Running MIPROv2 with teacher/student models...")
    print(f"   Teacher (qwen-max): Generates optimized prompts")
    print(f"   Student (qwen2.5-7b): Executes with those prompts")
    print(f"   Mode: auto='light' (6 trials, ~20-30 minutes)")

    mlflow_tracker.log_params({
        'optimizer': 'MIPROv2',
        'teacher_model': 'qwen-max',
        'student_model': 'qwen2.5-7b-instruct',
        'auto_mode': 'light',
        'train_size': len(train_set),
        'dev_size': len(dev_set)
    })

    optimizer = MIPROv2(
        metric=mmesgbench_end_to_end_metric,
        prompt_model=teacher_lm,  # Teacher generates prompts
        task_model=student_lm,    # Student executes task
        auto="light",
        verbose=True
    )

    print(f"\n💡 Key Insight:")
    print(f"   Strong teacher (qwen-max) crafts optimized prompts")
    print(f"   Weak student (qwen2.5-7b) benefits from those prompts")
    print(f"   Testing: Can good prompts help weaker models?\n")

    try:
        optimized_rag = optimizer.compile(
            student=rag_student,
            trainset=train_set,
            valset=dev_set,  # Use explicit valset for fair comparison
            requires_permission_to_run=False  # Skip confirmation prompt
        )

        print("\n✅ MIPROv2 optimization completed!")

    except Exception as e:
        print(f"\n❌ Optimization failed: {e}")
        import traceback
        traceback.print_exc()
        raise

    # ==================================================
    # Step 4: Evaluate Optimized Student
    # ==================================================
    print(f"\n📊 Step 4: Evaluating OPTIMIZED STUDENT...")

    # Make sure we're using student model for evaluation
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
    print("TEACHER-STUDENT OPTIMIZATION RESULTS")
    print("=" * 80)

    print(f"\n📊 Retrieval Accuracy:")
    print(f"   Baseline:  {baseline_results['retrieval_accuracy']:.1%}")
    print(f"   Optimized: {opt_results['retrieval_accuracy']:.1%}")
    print(f"   Change:    {opt_results['retrieval_accuracy'] - baseline_results['retrieval_accuracy']:+.1%}")

    print(f"\n📊 Answer Accuracy:")
    print(f"   Baseline:  {baseline_results['answer_accuracy']:.1%}")
    print(f"   Optimized: {opt_results['answer_accuracy']:.1%}")
    print(f"   Change:    {opt_results['answer_accuracy'] - baseline_results['answer_accuracy']:+.1%}")

    print(f"\n📊 End-to-End Accuracy:")
    print(f"   Baseline:  {baseline_results['end_to_end_accuracy']:.1%}")
    print(f"   Optimized: {opt_results['end_to_end_accuracy']:.1%}")
    change = opt_results['end_to_end_accuracy'] - baseline_results['end_to_end_accuracy']
    print(f"   Change:    {change:+.1%}")

    if change > 0:
        print(f"\n✅ SUCCESS: Teacher prompts helped student improve!")
    elif change < 0:
        print(f"\n⚠️  CAUTION: Student got worse with teacher prompts")
    else:
        print(f"\n➖ NEUTRAL: No change from optimization")

    return optimized_rag, opt_results


def main():
    """Main execution flow."""
    print("=" * 80)
    print("TEACHER-STUDENT MIPROV2 OPTIMIZATION")
    print("=" * 80)
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print(f"\n🎯 Experiment: Teacher-Student Optimization")
    print(f"   Teacher (qwen-max): Generates optimized prompts")
    print(f"   Student (qwen2.5-7b): Executes with those prompts")
    print(f"   Hypothesis: Strong prompts can help weak model")

    # Load dataset
    print(f"\n📊 Loading MMESGBench dataset...")
    dataset = MMESGBenchDataset()

    train_set = dataset.train_set
    dev_set = dataset.dev_set

    print(f"\n📈 Dataset Summary:")
    print(f"   Training: {len(train_set)} questions (20%)")
    print(f"   Dev: {len(dev_set)} questions (10%)")
    print(f"   Documents: 45/45 (100% coverage)")

    # Initialize MLFlow tracking
    print(f"\n📊 Initializing MLFlow tracking...")
    tracker = DSPyMLFlowTracker(experiment_name="TeacherStudent_Qwen7B_Test")

    run_name = create_run_name("teacher_student_qwen7b")
    tracker.start_run(
        run_name=run_name,
        tags={
            'optimizer': 'MIPROv2',
            'teacher_model': 'qwen-max',
            'student_model': 'qwen2.5-7b-instruct',
            'phase': 'teacher_student_optimization'
        }
    )

    # Run optimization
    try:
        optimized_rag, dev_results = optimize_with_teacher_student(
            train_set=train_set,
            dev_set=dev_set,
            mlflow_tracker=tracker
        )

        # Save results
        print(f"\n💾 Saving results...")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f"teacher_student_qwen7b_results_{timestamp}.json"

        detailed_results = {
            "timestamp": datetime.now().isoformat(),
            "run_name": run_name,
            "architecture": "Teacher-Student",
            "teacher_model": "qwen-max",
            "student_model": "qwen2.5-7b-instruct",
            "optimization": {
                "method": "MIPROv2",
                "train_size": len(train_set),
                "dev_size": len(dev_set),
                "auto_mode": "light"
            },
            "dev_results": {
                "retrieval_accuracy": dev_results['retrieval_accuracy'],
                "answer_accuracy": dev_results['answer_accuracy'],
                "end_to_end_accuracy": dev_results['end_to_end_accuracy'],
                "by_format": dev_results['by_format']
            }
        }

        with open(results_file, 'w') as f:
            json.dump(detailed_results, f, indent=2)

        print(f"   Saved to: {results_file}")
        mlflow.log_artifact(results_file, "results")

    finally:
        tracker.end_run()

    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    return optimized_rag, dev_results


if __name__ == "__main__":
    optimized_module, results = main()

    print("\n✅ Teacher-Student optimization complete!")
    print(f"   Student end-to-end accuracy: {results['end_to_end_accuracy']:.1%}")
    print(f"   View MLFlow results: mlflow ui")
