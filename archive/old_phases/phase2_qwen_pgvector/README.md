# Phase 2: Qwen + PGvector Baseline

## Goal
Establish our own baseline using existing Qwen embeddings and PGvector semantic search.

**Target**: ~42% answer accuracy (+2% over Phase 1)

## Method
- **Retrieval**: Qwen text-embedding-v4 (1024-dim) + pgvector
- **Data**: Existing MMESG collection (54,608 chunks) - **NO re-parsing**
- **Top-k**: 5 chunks per question
- **LLM**: qwen-max
- **Evaluation**: Same unified evaluator as Phase 1

## Files
- `baseline_evaluator.py` - Main evaluation script using BaselineMMESGBenchRAG
- `README.md` - This file

## Usage
```bash
# Run Phase 2 evaluation
python phase2_qwen_pgvector/baseline_evaluator.py

# Or use the run script
./run_phase2.sh
```

## Expected Output
- Answer accuracy: ~42%
- Retrieval accuracy: (research metric)
- E2E accuracy: (research metric)
- Results saved to: `phase2_qwen_pgvector/results/`

## Key Differences from Phase 1
- Uses our Qwen embeddings (not ColBERT)
- Uses existing PGvector data (no re-parsing needed)
- Pure semantic search (no ColBERT reranking)
- Should be slightly better than Phase 1 due to better embeddings

## Notes
- This is OUR baseline for subsequent DSPy optimization
- No prompt optimization yet - just retrieval + extraction
- Phase 3a will optimize prompts on top of this baseline
