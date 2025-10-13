# Refactoring Code Mapping Plan

## Phase Directory Structure

```
phase1_mmesgbench_exact/   - ColBERT + Sentence Transformer (MMESGBench exact replication)
phase2_qwen_pgvector/      - Qwen embeddings + PGvector semantic search (our baseline)
phase3a_dspy_prompts/      - DSPy prompt optimization (NO query generation)
phase3b_dspy_query_gen/    - DSPy with query generation optimization
unified_evaluator/         - Consistent evaluation across all phases
```

## Code Mapping from Archive

### Phase 1: MMESGBench Exact Replication (~40% target)

**Source**: `archive_old_project/code_old/`

Primary scripts:
- `colbert_full_dataset_evaluation.py` → `phase1_mmesgbench_exact/colbert_evaluator.py`
  - Full ColBERT text retrieval implementation
  - Uses Sentence Transformer embeddings
  - Top-5 chunk retrieval
  - Two-stage Qwen extraction

Configuration:
- Retrieval: ColBERT with sentence-transformers
- Top-k: 5 chunks
- LLM: qwen-max (two-stage extraction)
- Evaluation: MMESGBench exact scoring

### Phase 2: Qwen + PGvector Baseline (~42% target)

**Source**: `archive_old_project/code_old/` + existing `dspy_implementation/`

Primary scripts:
- `quick_dev_eval.py` → `phase2_qwen_pgvector/baseline_evaluator.py`
  - Uses BaselineMMESGBenchRAG from dspy_implementation
  - PGvector semantic search (54,608 chunks already indexed)
  - NO re-parsing needed

- `unified_baseline_evaluator.py` → `unified_evaluator/evaluator.py`
  - Imports MMESGBench's exact eval_score()
  - Provides retrieval + answer + E2E metrics
  - Used across ALL phases for consistency

Supporting modules (already exists in root):
- `dspy_implementation/dspy_setup.py` - DSPy + Qwen setup
- `dspy_implementation/dspy_dataset.py` - Dataset loading
- `dspy_implementation/dspy_rag_enhanced.py` - BaselineMMESGBenchRAG class
- `dspy_implementation/dspy_postgres_retriever.py` - PGvector retriever

Configuration:
- Retrieval: Qwen text-embedding-v4 (1024-dim) + pgvector
- Data: Existing MMESG collection (NO re-parsing)
- Top-k: 5 chunks
- LLM: qwen-max
- Evaluation: Same unified evaluator

### Phase 3a: DSPy Prompt Optimization (~45% target)

**Source**: Existing `dspy_implementation/` directory

Primary scripts:
- `dspy_implementation/enhanced_miprov2_optimization.py` → Configure for Phase 3a
  - Set `query_optimization: False` in config
  - Optimize only ESGReasoning + AnswerExtraction signatures
  - Use Phase 2 baseline as starting point

Key modules (already exists):
- `dspy_implementation/dspy_signatures_enhanced.py` - ESGReasoning, AnswerExtraction
- `dspy_implementation/dspy_rag_enhanced.py` - BaselineMMESGBenchRAG
- `dspy_implementation/dspy_metrics_enhanced.py` - MIPROv2 metrics
- `dspy_implementation/mlflow_tracking.py` - Experiment tracking

Configuration:
- Base: Phase 2 pipeline (no changes to retrieval)
- Optimize: Reasoning + extraction prompts ONLY
- Optimizer: MIPROv2 (light mode, 6-10 trials)
- Metrics: Answer accuracy (PRIMARY), retrieval + E2E (RESEARCH)

### Phase 3b: DSPy Query Generation (~47% target)

**Source**: Same `dspy_implementation/` directory

Primary scripts:
- `dspy_implementation/enhanced_miprov2_optimization.py` → Configure for Phase 3b
  - Set `query_optimization: True` in config
  - Optimize QueryGeneration + ESGReasoning + AnswerExtraction
  - Build on Phase 3a results

Key modules (same as 3a plus):
- `dspy_implementation/dspy_signatures_enhanced.py` - QueryGeneration signature
- `dspy_implementation/dspy_rag_enhanced.py` - EnhancedMMESGBenchRAG (with query gen)

Configuration:
- Base: Phase 3a optimized prompts
- Add: Query generation module
- Optimize: All three signatures (query + reasoning + extraction)
- Optimizer: MIPROv2 (medium mode, 10-15 trials)

### Unified Evaluator (All Phases)

**Source**: `archive_old_project/code_old/unified_baseline_evaluator.py`

Key features:
- Imports MMESGBench's exact `eval_score()` function
- Handles ANLS 0.5 fuzzy matching automatically
- Reports three metrics:
  - **Answer Accuracy** (PRIMARY - for MMESGBench comparison)
  - **Retrieval Accuracy** (RESEARCH - did we get the right pages?)
  - **E2E Accuracy** (RESEARCH - both retrieval AND answer correct)
- Works with any prediction format
- Consistent across all 4 phases

## Implementation Steps

1. **Copy unified evaluator** → `unified_evaluator/evaluator.py` ✅
2. **Setup Phase 1** → Copy ColBERT script ✅
3. **Setup Phase 2** → Copy baseline evaluator + configure ✅
4. **Setup Phase 3a** → Configure DSPy optimization (no query gen) ✅
5. **Setup Phase 3b** → Configure DSPy optimization (with query gen) ✅
6. **Create run scripts** → Easy commands for each phase ✅

## Expected Results

| Phase | Method | Answer Accuracy (PRIMARY) | Notes |
|-------|--------|---------------------------|-------|
| 1 | ColBERT exact | ~40% | MMESGBench replication |
| 2 | Qwen + PGvector | ~42% | Our baseline (+2%) |
| 3a | DSPy prompts | ~45% | Prompt optimization (+3%) |
| 3b | DSPy query gen | ~47% | Query optimization (+2%) |

**Total improvement**: 40% → 47% (+7% answer accuracy)

## Notes

- ALL phases use the same unified evaluator (fair comparison)
- Phase 2 uses existing PGvector data (no re-parsing)
- Phase 3a/3b build incrementally on Phase 2
- Answer accuracy is PRIMARY metric (for MMESGBench comparison)
- Retrieval + E2E are RESEARCH metrics (for our analysis)
