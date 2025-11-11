#!/bin/bash
# Monitor DeepSeek DC-CU cheatsheet growth in real-time

LOG_FILE="/Users/victoryim/Local_Git/CC/logs/deepseek_dc_cu_rerun.log"

echo "======================================================================="
echo "DeepSeek DC-CU Cheatsheet Growth Monitor"
echo "======================================================================="
echo ""
echo "Watching: $LOG_FILE"
echo "Press Ctrl+C to stop monitoring"
echo ""

# Function to extract and display cheatsheet info
display_progress() {
    if [ -f "$LOG_FILE" ]; then
        echo "======================================================================="
        echo "Latest Progress Updates:"
        echo "======================================================================="
        
        # Show all progress updates
        grep -A 3 "Progress Update" "$LOG_FILE" | tail -20
        
        echo ""
        echo "======================================================================="
        echo "Cheatsheet Growth Pattern:"
        echo "======================================================================="
        
        # Extract cheatsheet lengths
        grep "Cheatsheet:" "$LOG_FILE" | awk '{print $3, $4}' | tail -10
        
        echo ""
        echo "======================================================================="
        echo "Latest Activity (last 10 lines):"
        echo "======================================================================="
        tail -10 "$LOG_FILE"
        
        echo ""
        echo "======================================================================="
        date
        echo "======================================================================="
    else
        echo "⏳ Waiting for log file to be created..."
    fi
}

# Initial display
display_progress

# Watch for changes every 30 seconds
while true; do
    sleep 30
    clear
    display_progress
done

