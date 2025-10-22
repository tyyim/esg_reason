#!/bin/bash
# GEPA Optimization Runner - SKIP BASELINE
# Fast development mode that jumps straight to optimization

set -e

# Generate timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_DIR="logs/gepa_optimization"
LOG_FILE="${LOG_DIR}/gepa_skip_baseline_${TIMESTAMP}.log"

# Create log directory
mkdir -p "${LOG_DIR}"

# Activate conda
source ~/anaconda3/etc/profile.d/conda.sh
conda activate esg_reasoning

# Print start
echo "=========================================="
echo "GEPA Optimization - SKIP BASELINE"
echo "=========================================="
echo "Start Time: $(date)"
echo "Log File: ${LOG_FILE}"
echo "⚡ Fast mode: No baseline evaluation!"
echo "=========================================="
echo ""

# Run GEPA (skip baseline)
python dspy_implementation/gepa_skip_baseline.py 2>&1 | tee "${LOG_FILE}"

# Print completion
echo ""
echo "=========================================="
echo "GEPA Optimization Complete"
echo "=========================================="
echo "End Time: $(date)"
echo "Log File: ${LOG_FILE}"
echo "=========================================="
