#!/bin/bash
# Monitor DSPy full evaluation and trigger completion actions

LOG_FILE="dspy_full_933_run.log"
CHECKPOINT_FILE="dspy_full_dataset_checkpoint.json"
RESULTS_FILE="dspy_full_dataset_results.json"
MONITOR_INTERVAL=60  # Check every 60 seconds

echo "=================================================="
echo "DSPy Evaluation Monitor - 933 Questions"
echo "=================================================="
echo ""
echo "Log file: $LOG_FILE"
echo "Monitoring interval: ${MONITOR_INTERVAL}s"
echo ""

# Function to get progress from checkpoint
get_progress() {
    if [ -f "$CHECKPOINT_FILE" ]; then
        completed=$(jq -r '.completed // 0' "$CHECKPOINT_FILE" 2>/dev/null || echo "0")
        total=$(jq -r '.total // 933' "$CHECKPOINT_FILE" 2>/dev/null || echo "933")
        echo "$completed/$total"
    else
        echo "0/933"
    fi
}

# Function to check if evaluation is complete
is_complete() {
    if [ -f "$RESULTS_FILE" ]; then
        # Check if results file has final metrics
        if jq -e '.overall_metrics.accuracy' "$RESULTS_FILE" &>/dev/null; then
            return 0
        fi
    fi
    return 1
}

# Monitor loop
while true; do
    progress=$(get_progress)
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    echo "[$timestamp] Progress: $progress"

    # Check if complete
    if is_complete; then
        echo ""
        echo "=================================================="
        echo "✅ EVALUATION COMPLETE!"
        echo "=================================================="

        # Extract final results
        accuracy=$(jq -r '.overall_metrics.accuracy * 100' "$RESULTS_FILE")
        correct=$(jq -r '.overall_metrics.correct' "$RESULTS_FILE")
        total=$(jq -r '.overall_metrics.total' "$RESULTS_FILE")

        echo ""
        echo "📊 Final Results:"
        echo "   Accuracy: ${accuracy}%"
        echo "   Correct: $correct/$total"
        echo ""

        # Show last 30 lines of log
        echo "📝 Final log output:"
        tail -30 "$LOG_FILE"
        echo ""

        # Trigger completion actions
        echo "🚀 Triggering completion actions..."
        echo ""

        echo "1️⃣ Updating Notion research proposal..."
        # Trigger will happen via notification hook

        echo "2️⃣ Committing and syncing to GitHub..."
        # Trigger will happen via notification hook

        echo ""
        echo "✅ Monitoring complete!"
        echo "   Results saved to: $RESULTS_FILE"
        echo ""

        exit 0
    fi

    # Show last few lines of progress
    if [ -f "$LOG_FILE" ]; then
        tail -3 "$LOG_FILE" | grep -E "Evaluating:|Checkpoint" | tail -1
    fi

    echo ""
    sleep $MONITOR_INTERVAL
done
