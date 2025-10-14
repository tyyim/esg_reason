#!/usr/bin/env python3
"""
Test script to diagnose Qwen API content inspection failures
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    raise ValueError("DASHSCOPE_API_KEY not found in .env file")

client = OpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    timeout=60.0
)

# Load a few sample questions from the dataset
with open("MMESGBench/dataset/samples.json", "r") as f:
    dataset = json.load(f)

print("🧪 Testing Qwen API with sample ESG questions...")
print(f"API Key: {api_key[:15]}...")
print()

# Test with first 5 questions
for i, sample in enumerate(dataset[:5]):
    print(f"\n{'='*80}")
    print(f"Test {i+1}/5: {sample['question'][:100]}...")
    print(f"Document: {sample['doc_id']}")

    # Create a simple test prompt
    test_prompt = f"""Question: {sample['question']}

Please analyze this question about ESG (Environmental, Social, and Governance) topics."""

    try:
        response = client.chat.completions.create(
            model="qwen-max",
            messages=[{"role": "user", "content": test_prompt}],
            temperature=0.0,
            max_tokens=100
        )

        result = response.choices[0].message.content
        print(f"✅ SUCCESS: Got response ({len(result)} chars)")
        print(f"Response preview: {result[:100]}...")

    except Exception as e:
        error_str = str(e)
        print(f"❌ FAILED: {e}")

        if "data_inspection_failed" in error_str:
            print("⚠️  Content inspection failure detected!")
            print("   This suggests the API is flagging the content.")
            print(f"   Question: {sample['question']}")
        elif "Invalid Authentication" in error_str or "401" in error_str:
            print("⚠️  Authentication error - API key may be invalid or expired")
            break
        else:
            print(f"⚠️  Other error type")

print("\n" + "="*80)
print("✅ Test complete!")
