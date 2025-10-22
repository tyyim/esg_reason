#!/bin/bash
# GEPA Optimization Runner with Timestamped Logging
# Usage: ./run_gepa_optimization.sh

set -e  # Exit on error

# Generate timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_DIR="logs/gepa_optimization"
LOG_FILE="${LOG_DIR}/gepa_qwen7b_${TIMESTAMP}.log"

# Create log directory if it doesn't exist
mkdir -p "${LOG_DIR}"

# Activate conda environment
source ~/anaconda3/etc/profile.d/conda.sh
conda activate esg_reasoning

# Print start info
echo "=========================================="
echo "GEPA Optimization Run"
echo "=========================================="
echo "Start Time: $(date)"
echo "Log File: ${LOG_FILE}"
echo "=========================================="
echo ""

# Run GEPA optimization with timestamped log
python dspy_implementation/gepa_qwen7b_optimization.py 2>&1 | tee "${LOG_FILE}"

# Print completion info
echo ""
echo "=========================================="
echo "GEPA Optimization Complete"
echo "=========================================="
echo "End Time: $(date)"
echo "Log File: ${LOG_FILE}"
echo "=========================================="
