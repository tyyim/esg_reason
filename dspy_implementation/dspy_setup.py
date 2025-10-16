#!/usr/bin/env python3
"""
DSPy Environment Setup for MMESGBench RAG
Configures DSPy to work with Qwen API (OpenAI-compatible)
"""

import os
import dspy
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_dspy_qwen(model_name='qwen-max'):
    """
    Configure DSPy to use Qwen API (OpenAI-compatible interface)

    Args:
        model_name: Qwen model to use (default: 'qwen-max')
                   Options: 'qwen-max', 'qwen2.5-7b-instruct', 'qwen2.5-14b-instruct', etc.
    """
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY not found in environment")

    # Configure DSPy with Qwen's OpenAI-compatible endpoint
    lm = dspy.LM(
        model=f'openai/{model_name}',
        api_key=api_key,
        api_base='https://dashscope.aliyuncs.com/compatible-mode/v1',
        temperature=0.0,  # Deterministic for baseline
        max_tokens=1024
    )

    dspy.configure(lm=lm)

    print(f"✅ DSPy configured with {model_name}")
    print(f"   Model: {model_name}")
    print(f"   Temperature: 0.0")
    print(f"   Max tokens: 1024")

    return lm

def test_dspy_setup():
    """Test DSPy setup with a simple example"""
    print("\n🧪 Testing DSPy setup...")

    try:
        lm = setup_dspy_qwen()

        # Simple test with dspy.Predict
        class SimpleQA(dspy.Signature):
            """Answer a simple question."""
            question: str = dspy.InputField()
            answer: str = dspy.OutputField()

        predictor = dspy.Predict(SimpleQA)
        response = predictor(question="What is 2+2?")

        print(f"✅ Test successful!")
        print(f"   Question: What is 2+2?")
        print(f"   Answer: {response.answer}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("DSPy Setup for MMESGBench RAG")
    print("=" * 60)

    test_dspy_setup()
