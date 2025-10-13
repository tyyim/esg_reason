# Phase 1: MMESGBench Exact Replication

## Goal
Replicate MMESGBench's ColBERT text retrieval approach exactly as described in their paper.

**Target**: ~40% answer accuracy

## Method
- **Retrieval**: ColBERT with sentence-transformers embeddings
- **Top-k**: 5 chunks per question
- **LLM**: qwen-max (two-stage extraction)
- **Evaluation**: MMESGBench's exact eval_score() function

## Files
- `colbert_evaluator.py` - Main evaluation script with ColBERT retrieval
- `README.md` - This file

## Usage
```bash
# Run Phase 1 evaluation
python phase1_mmesgbench_exact/colbert_evaluator.py

# Or use the run script
./run_phase1.sh
```

## Expected Output
- Answer accuracy: ~40%
- Retrieval accuracy: (research metric)
- E2E accuracy: (research metric)
- Results saved to: `phase1_mmesgbench_exact/results/`

## Notes
- This replicates MMESGBench's published baseline
- Uses sentence-transformers for embeddings (as they did)
- No optimization - just exact replication for baseline comparison
