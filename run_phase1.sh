#!/bin/bash
# Run Phase 1: MMESGBench ColBERT Exact Replication

echo "=========================================="
echo "Phase 1: MMESGBench ColBERT Replication"
echo "Target: ~40% answer accuracy"
echo "=========================================="

# Activate conda environment
source ~/anaconda3/etc/profile.d/conda.sh
conda activate esg_reasoning

# Export API key from .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "Error: .env file not found"
    exit 1
fi

# Run ColBERT evaluator (parallel version for speed)
python phase1_mmesgbench_exact/colbert_evaluator_parallel.py

echo ""
echo "✅ Phase 1 complete!"
echo "Results saved to: phase1_mmesgbench_exact/results/"
