#!/bin/bash
# DeepSeek v3 Comparison: Simple Baseline vs DC-CU
# Tests Phase 2 hypothesis: "Bigger models might help DC/ACE more"

set -e

echo "=================================================="
echo "DeepSeek v3 Dev Set Comparison"
echo "=================================================="
echo ""
echo "Testing hypothesis: Larger models benefit DC more than static prompts"
echo "Comparing:"
echo "  1. Simple Baseline (1-stage direct QA)"
echo "  2. DC-CU (test-time learning with cumulative cheatsheet)"
echo ""
echo "Dataset: Dev set (93 questions)"
echo "Model: DeepSeek v3.1 via DashScope"
echo ""

# Activate conda environment
source ~/anaconda3/etc/profile.d/conda.sh
conda activate esg_reasoning

cd /Users/victoryim/Local_Git/CC

# Create results directory
mkdir -p results/deepseek_comparison

echo "=================================================="
echo "Step 1: Testing DeepSeek access..."
echo "=================================================="

python3 << 'EOF'
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('DASHSCOPE_API_KEY')

if not api_key:
    print("❌ ERROR: DASHSCOPE_API_KEY not found")
    print("Please set it in your .env file")
    exit(1)

client = OpenAI(api_key=api_key, base_url='https://dashscope.aliyuncs.com/compatible-mode/v1')

try:
    response = client.chat.completions.create(
        model='deepseek-v3.1',
        messages=[{'role': 'user', 'content': 'Say hello'}],
        max_tokens=20
    )
    print(f"✅ DeepSeek v3.1 accessible! Model: {response.model}")
except Exception as e:
    print(f"❌ ERROR: {e}")
    print("")
    print("Please enable DeepSeek in your DashScope console:")
    print("https://dashscope.console.aliyun.com/")
    exit(1)
EOF

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ DeepSeek access failed. Please enable DeepSeek first."
    exit 1
fi

echo ""
echo "=================================================="
echo "Step 2: Running Simple Baseline (RAW) with DeepSeek..."
echo "=================================================="
echo "Note: Using RAW implementation (no DSPy framework)"
echo "      Fair comparison with DC-CU (both use direct LLM calls)"
echo ""

python dspy_implementation/evaluate_simple_baseline_deepseek_raw.py \
    --dataset dev \
    --model deepseek-v3.1

echo ""
echo "=================================================="
echo "Step 3: Running DC-CU with DeepSeek..."
echo "=================================================="
echo ""

python dspy_implementation/dc_module/dc_evaluator_deepseek.py \
    --dataset dev \
    --model deepseek-v3.1

echo ""
echo "=================================================="
echo "Comparison Complete!"
echo "=================================================="
echo ""
echo "Results saved to: results/deepseek_comparison/"
echo ""
echo "Next step: Compare with qwen2.5-7b results to test hypothesis"
echo ""

