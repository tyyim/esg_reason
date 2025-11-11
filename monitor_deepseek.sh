#!/bin/bash
# Monitor DeepSeek v3.1 Comparison Progress

LOG_FILE="logs/deepseek_comparison.log"

echo "=================================================="
echo "DeepSeek v3.1 Comparison Monitor"
echo "=================================================="
echo ""

# Check if process is running
if ps -p 31545 > /dev/null 2>&1; then
    echo "✅ Status: RUNNING (PID: 31545)"
else
    echo "⏹️  Status: COMPLETED or STOPPED"
fi

echo ""
echo "Last 30 lines of log:"
echo "=================================================="
tail -30 "$LOG_FILE"
echo ""
echo "=================================================="
echo ""
echo "To monitor live: tail -f $LOG_FILE"
echo "To check results: ls -lh results/deepseek_comparison/"

