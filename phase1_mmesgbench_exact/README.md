# Phase 1: MMESGBench Exact Replication

## Goal
Replicate MMESGBench's ColBERT text retrieval approach exactly as described in their paper.

**Target**: ~40% answer accuracy

## Method
- **Retrieval**: ColBERT with sentence-transformers embeddings
- **Top-k**: 5 chunks per question
- **LLM**: qwen-max (two-stage extraction)
- **Evaluation**: MMESGBench's exact eval_score() function
- **Parallelism**: ThreadPoolExecutor for faster processing

## Files
- `colbert_evaluator.py` - Sequential version (basic)
- `colbert_evaluator_parallel.py` - **RECOMMENDED**: Parallel version with batch processing
- `README.md` - This file

## Usage

### Recommended: Parallel Version (Faster)
```bash
# Using esg_reasoning conda environment
source ~/anaconda3/etc/profile.d/conda.sh
conda activate esg_reasoning
python phase1_mmesgbench_exact/colbert_evaluator_parallel.py

# Or use the run script
./run_phase1.sh
```

**Performance**:
- Pre-computes all retrievals first
- Processes questions in parallel batches (10 questions/batch)
- ~2-3x faster than sequential version

### Alternative: Sequential Version
```bash
python phase1_mmesgbench_exact/colbert_evaluator.py
```

## Expected Output
- Answer accuracy: ~40%
- Retrieval accuracy: (research metric)
- E2E accuracy: (research metric)
- Results saved to: `phase1_mmesgbench_exact/results/`
- Checkpoint file: `colbert_checkpoint.json` (auto-resume on crashes)

## Features

### Checkpoint/Resume ✅
- Saves progress automatically
- Can resume from interruptions
- No work lost on crashes

### Parallel Processing ✅
- Pre-computation: Index all documents first
- Parallel generation: Process batches concurrently
- Configurable batch size (default: 10)

### Structured Logging ✅
- Logs to file and console
- Progress tracking with time estimates
- Error handling with graceful degradation

### MMESGBench Evaluation ✅
- Uses their exact eval_score() function
- ANLS 0.5 fuzzy matching
- Handles all answer types (Int, Float, Str, List)

## Notes
- This replicates MMESGBench's published baseline
- Uses sentence-transformers for embeddings (as they did)
- No optimization - just exact replication for baseline comparison
- Parallel version is ~2-3x faster with same results
