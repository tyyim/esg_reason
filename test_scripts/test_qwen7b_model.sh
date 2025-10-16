#!/bin/bash
# Quick test to verify qwen2.5-7b-instruct API works before running full optimization

echo "=========================================="
echo "Testing Qwen 2.5 7B Model API"
echo "=========================================="

# Activate conda environment
source ~/anaconda3/etc/profile.d/conda.sh
conda activate esg_reasoning

# Test the model
python -c "
from dspy_implementation.dspy_setup import setup_dspy_qwen
import dspy

print('Testing qwen2.5-7b-instruct...')
lm = setup_dspy_qwen(model_name='qwen2.5-7b-instruct')

class SimpleQA(dspy.Signature):
    question: str = dspy.InputField()
    answer: str = dspy.OutputField()

predictor = dspy.Predict(SimpleQA)
response = predictor(question='What is ESG? Answer in one sentence.')

print(f'\nTest Response: {response.answer}')
print('\n✅ Qwen 2.5 7B API is working!')
"

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ API Test Successful!"
    echo ""
    echo "Ready to run optimization with:"
    echo "  python dspy_implementation/enhanced_miprov2_optimization.py --model qwen2.5-7b-instruct"
    echo "=========================================="
else
    echo ""
    echo "❌ API Test Failed"
    echo "Check your DASHSCOPE_API_KEY and network connection"
fi
