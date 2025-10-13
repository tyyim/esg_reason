#!/bin/bash
# Check Phase 1a Optimization Status

echo "📊 Phase 1a Optimization Status Check"
echo "=" | tr '=' '=' | head -c 80; echo
echo

# Check if optimization is running
if pgrep -f "enhanced_miprov2_optimization.py" > /dev/null; then
    PID=$(pgrep -f "enhanced_miprov2_optimization.py")
    echo "✅ Optimization is RUNNING"
    echo "   Process ID: $PID"

    # Get start time
    if [ -f logs/optimization.pid ]; then
        START_TIME=$(stat -f %Sm -t "%Y-%m-%d %H:%M:%S" logs/optimization.pid 2>/dev/null)
        echo "   Started: $START_TIME"
    fi

    # Find latest log file
    LATEST_LOG=$(ls -t logs/optimization_*.log 2>/dev/null | head -1)
    if [ -n "$LATEST_LOG" ]; then
        echo "   Log file: $LATEST_LOG"
        echo

        # Show last few lines
        echo "📝 Recent progress (last 10 lines):"
        echo "---"
        tail -10 "$LATEST_LOG" | grep -E "Step |%|✅|❌|📊|🚀" || tail -10 "$LATEST_LOG"
        echo "---"
        echo

        # Count progress if possible
        TOTAL_LINES=$(wc -l < "$LATEST_LOG")
        echo "   Total log lines: $TOTAL_LINES"

        # Check for completion markers
        if grep -q "Dev Set Results" "$LATEST_LOG"; then
            echo "   🎯 Status: Dev evaluation in progress or complete"
        elif grep -q "MIPROv2 optimization" "$LATEST_LOG"; then
            echo "   🔧 Status: Optimization in progress"
        elif grep -q "Baseline" "$LATEST_LOG"; then
            echo "   📊 Status: Baseline evaluation"
        fi
    fi

    echo
    echo "💡 Commands:"
    echo "   Watch live: tail -f $LATEST_LOG"
    echo "   Stop it: pkill -f enhanced_miprov2_optimization.py"

else
    echo "⏸️  Optimization is NOT running"
    echo

    # Check for completion
    LATEST_LOG=$(ls -t logs/optimization_*.log 2>/dev/null | head -1)
    if [ -n "$LATEST_LOG" ]; then
        echo "   Last log file: $LATEST_LOG"

        if grep -q "Optimization complete" "$LATEST_LOG"; then
            echo "   ✅ Status: COMPLETED"
            echo
            echo "📈 Final Results:"
            grep -A 5 "Dev Set Results" "$LATEST_LOG" | tail -10
        elif grep -q "failed" "$LATEST_LOG"; then
            echo "   ❌ Status: FAILED"
            echo "   Check log for errors: tail -50 $LATEST_LOG"
        else
            echo "   ⚠️  Status: INCOMPLETE (may have been interrupted)"
        fi
    else
        echo "   No optimization logs found"
    fi

    echo
    echo "💡 Commands:"
    echo "   Start optimization: ./run_phase1a_persistent.sh"
fi

echo
echo "🌐 MLFlow UI Status:"
if pgrep -f "mlflow ui" > /dev/null; then
    echo "   ✅ Running at http://localhost:5000"
else
    echo "   ⏸️  Not running"
    echo "   Start with: nohup mlflow ui --host 127.0.0.1 --port 5000 &"
fi

echo
echo "=" | tr '=' '=' | head -c 80; echo
