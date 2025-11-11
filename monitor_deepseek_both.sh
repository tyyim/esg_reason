#!/bin/bash
# Monitor both DeepSeek evaluations

echo "======================================================================"
echo "DeepSeek v3.1 Comparison Monitor - Fair RAW Implementations"
echo "======================================================================"
echo ""
echo "Simple Baseline (RAW): No DSPy framework"
echo "DC-CU: Original DC implementation"
echo "Both use: Direct OpenAI API calls"
echo ""
echo "======================================================================"
echo ""

echo "📊 Simple Baseline (RAW) - Last 3 lines:"
tail -3 /Users/victoryim/Local_Git/CC/logs/deepseek_simple_baseline_raw.log | grep -E "Evaluating:|Accuracy:"
echo ""

echo "📊 DC-CU - Last 3 lines:"
tail -3 /Users/victoryim/Local_Git/CC/logs/deepseek_dc_cu.log | grep -E "Evaluating:|Accuracy:"
echo ""

echo "======================================================================"
echo "Full logs:"
echo "  Simple Baseline: logs/deepseek_simple_baseline_raw.log"
echo "  DC-CU:           logs/deepseek_dc_cu.log"
echo ""
echo "To monitor live:"
echo "  tail -f logs/deepseek_simple_baseline_raw.log"
echo "  tail -f logs/deepseek_dc_cu.log"
echo "======================================================================"
