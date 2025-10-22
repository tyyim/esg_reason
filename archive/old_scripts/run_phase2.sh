#!/bin/bash
# Run Phase 2: Qwen + PGvector Baseline

echo "=========================================="
echo "Phase 2: Qwen + PGvector Baseline"
echo "Target: ~42% answer accuracy"
echo "=========================================="

# Activate conda environment
source ~/anaconda3/etc/profile.d/conda.sh
conda activate esg_reasoning

# Run baseline evaluator
python phase2_qwen_pgvector/baseline_evaluator.py

echo ""
echo "✅ Phase 2 complete!"
echo "Results saved to: phase2_qwen_pgvector/results/"
