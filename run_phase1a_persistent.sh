#!/bin/bash
# Persistent Phase 1a Optimization Runner
# This script runs the optimization in the background using nohup
# The process will continue even if you close your terminal or computer

set -e

echo "🚀 Starting Phase 1a Enhanced MIPROv2 Optimization (Persistent Mode)"
echo "=" | tr '=' '=' | head -c 80; echo

# Change to project directory
cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"

echo "📁 Working directory: $PROJECT_DIR"
echo

# Create logs directory
mkdir -p logs

# Check if optimization is already running
if pgrep -f "enhanced_miprov2_optimization.py" > /dev/null; then
    echo "⚠️  Optimization already running!"
    echo "   Process IDs:"
    pgrep -f "enhanced_miprov2_optimization.py"
    echo
    echo "   To check progress: tail -f logs/optimization_$(date +%Y%m%d).log"
    echo "   To kill it: pkill -f enhanced_miprov2_optimization.py"
    exit 1
fi

# Start MLFlow UI in background
echo "🎯 Step 1: Starting MLFlow UI..."
if pgrep -f "mlflow ui" > /dev/null; then
    echo "   ✅ MLFlow UI already running"
else
    nohup mlflow ui --host 127.0.0.1 --port 5000 \
        > logs/mlflow_ui.log 2>&1 &
    MLFLOW_PID=$!
    sleep 3

    if pgrep -f "mlflow ui" > /dev/null; then
        echo "   ✅ MLFlow UI started (PID: $MLFLOW_PID)"
        echo "   📊 Dashboard: http://localhost:5000"
    else
        echo "   ❌ Failed to start MLFlow UI"
        exit 1
    fi
fi

echo

# Start optimization in background with nohup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="logs/optimization_${TIMESTAMP}.log"

echo "🔧 Step 2: Starting Enhanced MIPROv2 Optimization..."
echo "   Log file: $LOG_FILE"
echo "   Expected duration: 45-90 minutes"
echo

nohup python dspy_implementation/enhanced_miprov2_optimization.py \
    > "$LOG_FILE" 2>&1 &

OPT_PID=$!

# Wait a bit and verify it started
sleep 5

if pgrep -f "enhanced_miprov2_optimization.py" > /dev/null; then
    echo "✅ Optimization started successfully!"
    echo "   Process ID: $OPT_PID"
    echo "   Log file: $LOG_FILE"
    echo
    echo "=" | tr '=' '=' | head -c 80; echo
    echo "🎉 Phase 1a optimization is now running in the background!"
    echo
    echo "📊 You can now:"
    echo "   • Close this terminal - optimization will continue"
    echo "   • Close your computer - optimization will continue"
    echo "   • Monitor progress: tail -f $LOG_FILE"
    echo "   • View MLFlow UI: http://localhost:5000"
    echo "   • Check status: pgrep -f enhanced_miprov2_optimization.py"
    echo "   • Stop it: pkill -f enhanced_miprov2_optimization.py"
    echo
    echo "⏱️  Expected completion: $(date -v +90M '+%Y-%m-%d %H:%M:%S') (approx)"
    echo "=" | tr '=' '=' | head -c 80; echo

    # Save PID to file for easy reference
    echo "$OPT_PID" > logs/optimization.pid
    echo "Saved PID to logs/optimization.pid"

else
    echo "❌ Optimization failed to start"
    echo "   Check log file: $LOG_FILE"
    exit 1
fi
