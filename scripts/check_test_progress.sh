#!/bin/bash
# Quick test evaluation progress checker

echo ""
echo "================================================================================"
echo "TEST SET EVALUATION - QUICK STATUS CHECK"
echo "================================================================================"
echo ""

# Check if process is running
if ps aux | grep -q "[r]un_complete_test_evaluation.py"; then
    echo "✅ Process Status: RUNNING"
    PID=$(ps aux | grep "[r]un_complete_test_evaluation.py" | awk '{print $2}' | head -1)
    echo "   PID: $PID"
else
    echo "⚠️  Process Status: NOT RUNNING"
fi

echo ""
echo "--------------------------------------------------------------------------------"
echo "Progress Check:"
echo "--------------------------------------------------------------------------------"

# Run monitor script
python monitor_test_evaluation.py

echo ""
echo "================================================================================"
echo "Commands:"
echo "  - Full monitor:    python monitor_test_evaluation.py"
echo "  - View logs:       tail -f logs/test_evaluation/test_run_output.log"
echo "  - Check process:   ps aux | grep run_complete_test_evaluation"
echo "================================================================================"
echo ""

