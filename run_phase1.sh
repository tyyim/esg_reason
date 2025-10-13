#!/bin/bash
# Run Phase 1: MMESGBench ColBERT Exact Replication

echo "=========================================="
echo "Phase 1: MMESGBench ColBERT Replication"
echo "Target: ~40% answer accuracy"
echo "=========================================="

# Activate conda environment
source ~/anaconda3/etc/profile.d/conda.sh
conda activate esg_reasoning

# Run ColBERT evaluator (parallel version for speed)
python phase1_mmesgbench_exact/colbert_evaluator_parallel.py

echo ""
echo "✅ Phase 1 complete!"
echo "Results saved to: phase1_mmesgbench_exact/results/"
