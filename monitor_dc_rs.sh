#!/bin/bash
# Monitor DC-RS progress

LOG_FILE=$(ls -t logs/dc_rs_dev_*.log | head -1)

echo "==================================="
echo "DC-RS Dev Set Evaluation Monitor"
echo "==================================="
echo ""
echo "Log file: $LOG_FILE"
echo ""
echo "Latest progress:"
tail -5 "$LOG_FILE"
echo ""
echo "-----------------------------------"
echo "Refresh every 30s with: watch -n 30 ./monitor_dc_rs.sh"

