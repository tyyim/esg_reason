# Quick Start Guide - Running All Phases

## Overview

This project implements a 4-phase approach to ESG QA optimization:

1. **Phase 1**: MMESGBench ColBERT exact replication (~40% accuracy)
2. **Phase 2**: Qwen + PGvector baseline (~42% accuracy)
3. **Phase 3a**: DSPy prompt optimization (~45% accuracy)
4. **Phase 3b**: DSPy query generation (~47% accuracy)

**Total Expected Improvement**: 40% → 47% (+7% answer accuracy)

## Quick Commands

```bash
# Run all phases sequentially
./run_phase1.sh  # ~10-15 minutes
./run_phase2.sh  # ~10-15 minutes
./run_phase3a.sh # ~20-30 minutes
./run_phase3b.sh # ~30-45 minutes

# Or run individually as needed
```

## Phase Details

### Phase 1: MMESGBench ColBERT Replication
**Goal**: Establish MMESGBench baseline for comparison
**Method**: ColBERT text retrieval + Sentence Transformer embeddings
**Runtime**: ~10-15 minutes
**Output**: `phase1_mmesgbench_exact/results/`

```bash
./run_phase1.sh
```

### Phase 2: Qwen + PGvector Baseline
**Goal**: Establish our own baseline using existing infrastructure
**Method**: Qwen embeddings + PGvector semantic search
**Runtime**: ~10-15 minutes
**Output**: `phase2_qwen_pgvector/results/`

```bash
./run_phase2.sh
```

**Note**: Phase 2 uses existing PGvector data (54,608 chunks) - no re-parsing needed.

### Phase 3a: DSPy Prompt Optimization
**Goal**: Optimize reasoning + extraction prompts (no query generation)
**Method**: DSPy MIPROv2 on ESGReasoning + AnswerExtraction
**Runtime**: ~20-30 minutes
**Output**: `phase3a_dspy_prompts/optimized_module.json`

```bash
./run_phase3a.sh

# Monitor optimization progress
mlflow ui  # Open http://localhost:5000
```

**Note**: Requires Phase 2 to complete first for baseline comparison.

### Phase 3b: DSPy Query Generation
**Goal**: Add query generation optimization on top of Phase 3a
**Method**: DSPy MIPROv2 on QueryGeneration + ESGReasoning + AnswerExtraction
**Runtime**: ~30-45 minutes
**Output**: `phase3b_dspy_query_gen/optimized_module.json`

```bash
./run_phase3b.sh

# Monitor optimization progress
mlflow ui  # Open http://localhost:5000
```

**Note**: Requires Phase 3a to complete first (builds on optimized prompts).

## Results Comparison

After running all phases, use the unified evaluator to compare:

```bash
# Compare all phase results
python unified_evaluator/evaluator.py \
  --phase1 phase1_mmesgbench_exact/results/predictions.json \
  --phase2 phase2_qwen_pgvector/results/predictions.json \
  --phase3a phase3a_dspy_prompts/results/predictions.json \
  --phase3b phase3b_dspy_query_gen/results/predictions.json
```

## Expected Results

| Phase | Method | Answer Accuracy | Improvement |
|-------|--------|-----------------|-------------|
| 1 | ColBERT baseline | ~40% | Baseline |
| 2 | Qwen + PGvector | ~42% | +2% |
| 3a | DSPy prompts | ~45% | +5% |
| 3b | DSPy query gen | ~47% | +7% |

## Metrics Explained

### PRIMARY Metric (for MMESGBench comparison)
- **Answer Accuracy**: % questions with correct answer (using ANLS 0.5 fuzzy matching)

### RESEARCH Metrics (for our analysis)
- **Retrieval Accuracy**: % questions with all evidence pages retrieved in top-5
- **E2E Accuracy**: Both retrieval AND answer correct

## Environment Setup

```bash
# Activate conda environment
conda activate esg_reasoning

# Set API key
export DASHSCOPE_API_KEY=your_key_here

# Verify PostgreSQL connection
psql $PG_URL -c "SELECT COUNT(*) FROM chunks WHERE collection_name='MMESG';"
# Should return: 54608
```

## Troubleshooting

**Phase 3a won't start**:
- Make sure Phase 2 has completed successfully
- Check that `phase2_qwen_pgvector/results/` exists

**Phase 3b won't start**:
- Make sure Phase 3a has completed successfully
- Check that `phase3a_dspy_prompts/optimized_module.json` exists

**MLFlow UI not accessible**:
- Check if port 5000 is already in use: `lsof -i :5000`
- Kill existing process: `kill $(lsof -t -i :5000)`
- Restart: `mlflow ui --host 127.0.0.1 --port 5000`

**PGvector connection error**:
- Verify `$PG_URL` environment variable is set
- Test connection: `psql $PG_URL -c "SELECT 1;"`

## Files and Directories

```
.
├── phase1_mmesgbench_exact/     # ColBERT baseline
│   ├── colbert_evaluator.py
│   ├── README.md
│   └── results/
├── phase2_qwen_pgvector/        # Qwen baseline
│   ├── baseline_evaluator.py
│   ├── README.md
│   └── results/
├── phase3a_dspy_prompts/        # DSPy prompts only
│   ├── config_phase3a.yaml
│   ├── README.md
│   ├── optimized_module.json
│   └── results/
├── phase3b_dspy_query_gen/      # DSPy query gen
│   ├── config_phase3b.yaml
│   ├── README.md
│   ├── optimized_module.json
│   └── results/
├── unified_evaluator/           # Consistent evaluation
│   └── evaluator.py
├── dspy_implementation/         # DSPy modules
│   ├── enhanced_miprov2_optimization.py
│   ├── dspy_signatures_enhanced.py
│   ├── dspy_rag_enhanced.py
│   └── ...
└── run_phase*.sh               # Execution scripts
```

## Documentation

- **CLAUDE.md**: Project guidelines and current status
- **CHANGELOG.md**: Historical progress tracking
- **PROJECT_REFACTORING_PLAN.md**: Detailed 4-phase implementation plan
- **ANLS_EVALUATION_EXPLAINED.md**: MMESGBench evaluation methodology
- **REFACTORING_MAPPING.md**: Code mapping from archive to phases
- **Research Plan — ESG Reasoning and Green Finance.md**: Research proposal

## Next Steps

After completing all phases:

1. Analyze results across all phases
2. Document key findings in CHANGELOG.md
3. Update Research Plan with actual results
4. Consider Phase 4: Fine-tuning comparison (LoRA + small-RL)
