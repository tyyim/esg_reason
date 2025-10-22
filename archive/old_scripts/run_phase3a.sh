#!/bin/bash
# Run Phase 3a: DSPy Prompt Optimization (No Query Generation)

echo "=========================================="
echo "Phase 3a: DSPy Prompt Optimization"
echo "Target: ~45% answer accuracy"
echo "Runtime: ~20-30 minutes"
echo "=========================================="

# Activate conda environment
source ~/anaconda3/etc/profile.d/conda.sh
conda activate esg_reasoning

# Check if Phase 2 results exist
if [ ! -d "phase2_qwen_pgvector/results" ]; then
    echo "⚠️  Warning: Phase 2 results not found. Run Phase 2 first for baseline comparison."
    echo "Run: ./run_phase2.sh"
    exit 1
fi

# Start MLFlow UI in background (optional)
echo "Starting MLFlow UI on http://localhost:5000..."
mlflow ui --host 127.0.0.1 --port 5000 &
MLFLOW_PID=$!

# Run optimization
python -m dspy_implementation.enhanced_miprov2_optimization \
    --config phase3a_dspy_prompts/config_phase3a.yaml \
    2>&1 | tee phase3a_dspy_prompts/optimization.log

echo ""
echo "✅ Phase 3a complete!"
echo "Optimized module saved to: phase3a_dspy_prompts/optimized_module.json"
echo "View results: mlflow ui (http://localhost:5000)"

# Stop MLFlow UI
kill $MLFLOW_PID 2>/dev/null
