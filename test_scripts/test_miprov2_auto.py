#!/usr/bin/env python3
"""
Quick test to verify MIPROv2 with auto mode works before running full pipeline
"""

import dspy
from dspy.teleprompt import MIPROv2
from dspy_implementation.dspy_setup import setup_dspy_qwen
from dspy_implementation.dspy_rag_enhanced import BaselineMMESGBenchRAG
from dspy_implementation.dspy_metrics_enhanced import mmesgbench_end_to_end_metric

print("=" * 60)
print("MIPROv2 Auto Mode Test")
print("=" * 60)

# Setup DSPy
print("\n📋 Setting up DSPy...")
setup_dspy_qwen()

# Create a minimal test dataset (just 3 examples)
print("\n📊 Creating minimal test dataset...")
test_trainset = [
    dspy.Example(
        question="Test question 1?",
        doc_id="AR6 Synthesis Report Climate Change 2023.pdf",
        answer_format="Str",
        gold_answer="Test"
    ).with_inputs("question", "doc_id", "answer_format"),
    dspy.Example(
        question="Test question 2?",
        doc_id="AR6 Synthesis Report Climate Change 2023.pdf",
        answer_format="Int",
        gold_answer="42"
    ).with_inputs("question", "doc_id", "answer_format"),
    dspy.Example(
        question="Test question 3?",
        doc_id="AR6 Synthesis Report Climate Change 2023.pdf",
        answer_format="Float",
        gold_answer="1.5"
    ).with_inputs("question", "doc_id", "answer_format"),
]

print(f"✅ Created {len(test_trainset)} test examples")

# Initialize RAG module
print("\n🔧 Initializing RAG module...")
rag = BaselineMMESGBenchRAG()

# Test 1: Try to create MIPROv2 optimizer with auto mode
print("\n🧪 Test 1: Initialize MIPROv2 with auto='light'...")
try:
    optimizer = MIPROv2(
        metric=mmesgbench_end_to_end_metric,
        auto="light",
        verbose=True
    )
    print("✅ MIPROv2 initialized successfully with auto='light'")
except Exception as e:
    print(f"❌ FAILED to initialize MIPROv2: {e}")
    print("\nThis version of DSPy doesn't support auto mode.")
    print("Need to use manual parameters instead.")
    exit(1)

# Test 2: Try to compile with auto mode
print("\n🧪 Test 2: Test compile() with auto mode (dry run)...")
try:
    # This should work if auto mode is supported
    print("   Calling optimizer.compile() with student and trainset only...")
    optimized = optimizer.compile(
        student=rag,
        trainset=test_trainset
    )
    print("✅ Compile call succeeded! Auto mode is working.")
    print("\n🎉 SUCCESS! MIPROv2 auto mode is fully functional.")
    print("   Safe to run full optimization pipeline.")

except Exception as e:
    print(f"❌ FAILED during compile: {e}")
    print("\nAuto mode initialization worked but compile failed.")
    print("Check the error message above for details.")
    exit(1)

print("\n" + "=" * 60)
print("✅ All tests passed! MIPROv2 auto='light' mode is ready.")
print("=" * 60)
