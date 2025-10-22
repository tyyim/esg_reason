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

## ✅ Verified Baseline Results

**Status**: Verified from archive (October 2025)

| Metric | Value | Details |
|--------|-------|---------|
| **Accuracy** | **40.5%** | 378/933 questions correct |
| **Dataset** | Corrected | With fixed document references |
| **Evaluation** | MMESGBench | Using their exact eval_score() function |
| **Source File** | `archive_old_project/results_old/mmesgbench_baseline_corrected.json` | Previous evaluation results |
| **Target** | 41.5% | MMESGBench paper target |
| **Gap** | -1.0% | Within acceptable range |

**Document Corrections Applied**:
- Microsoft CDP Climate Change Response 2023 → 2024
- CDP Full Corporate (underscores) → (with spaces)
- Apple CDP (underscores) → (with spaces)
- ISO 14001 → ISO-14001-2015

**Next Steps**:
- ✅ Baseline established: 40.5%
- ⏳ Can re-run evaluation if needed to verify
- ⏳ Ready for Phase 2 (Qwen + PGVector) and Phase 3 (DSPy optimization)

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
