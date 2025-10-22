#!/usr/bin/env python3
"""
Quick GEPA Test - Skip baseline evaluation, jump straight to optimization

This script tests if GEPA.compile() works correctly without spending 15-20 mins on baseline.
Uses pre-computed baseline results from teacher-student run.
"""

import os
import sys
import dspy
from dotenv import load_dotenv
from dspy.teleprompt import GEPA

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dspy_implementation.dspy_dataset import MMESGBenchDataset
from dspy_implementation.dspy_rag_enhanced import BaselineMMESGBenchRAG
from dspy_implementation.dspy_metrics_gepa_fixed import mmesgbench_answer_only_gepa_metric

# Load environment
load_dotenv()

def main():
    print("\n" + "="*80)
    print("GEPA QUICK TEST - Skip Baseline, Test Optimization")
    print("="*80)

    # Load dataset
    print(f"\n📊 Loading dataset...")
    dataset = MMESGBenchDataset()
    train_set = dataset.train_set
    dev_set = dataset.dev_set
    print(f"   Train: {len(train_set)} examples")
    print(f"   Dev: {len(dev_set)} examples")

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
        temperature=1.0,
        max_tokens=4096
    )
    print(f"✅ Reflection model configured")

    # Create GEPA optimizer
    print(f"\n⚙️ Creating GEPA optimizer...")
    optimizer = GEPA(
        metric=mmesgbench_answer_only_gepa_metric,
        reflection_lm=reflection_lm,
        auto='light',
        reflection_minibatch_size=3,
        candidate_selection_strategy='pareto',
        use_merge=True,
        track_stats=True,
        seed=42
    )
    print(f"✅ GEPA optimizer created")

    # Test GEPA.compile() - this is where it usually fails
    print(f"\n🚀 Testing GEPA.compile()...")
    print(f"   If this works, GEPA optimization can run successfully!")
    print(f"   Expected: Should start optimization without errors\n")

    try:
        optimized_rag = optimizer.compile(
            student=rag_student,
            trainset=train_set[:10],  # Use only 10 examples for quick test
            valset=dev_set[:10]        # Use only 10 examples for quick test
        )

        print(f"\n✅ SUCCESS! GEPA.compile() worked!")
        print(f"   GEPA optimization can run successfully")
        print(f"   Ready for full optimization run")

    except Exception as e:
        print(f"\n❌ FAILED! GEPA.compile() error:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
