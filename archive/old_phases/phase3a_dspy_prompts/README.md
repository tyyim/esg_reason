# Phase 3a: DSPy Prompt Optimization (No Query Generation)

## Goal
Optimize reasoning and extraction prompts using DSPy MIPROv2, WITHOUT query generation.

**Target**: ~45% answer accuracy (+3% over Phase 2)

## Method
- **Base**: Phase 2 pipeline (Qwen + PGvector retrieval unchanged)
- **Optimization**: ESGReasoning + AnswerExtraction signatures ONLY
- **Optimizer**: MIPROv2 (light mode, 6-10 trials)
- **Training**: 186 questions (20% of dataset)
- **Validation**: 93 questions (10% of dataset)

## Files
- `config_phase3a.yaml` - Configuration for Phase 3a optimization
- `README.md` - This file
- `run_optimization.py` - Will call dspy_implementation/enhanced_miprov2_optimization.py

## Usage
```bash
# Run Phase 3a optimization
./run_phase3a.sh

# Or directly
python -m dspy_implementation.enhanced_miprov2_optimization \
  --config phase3a_dspy_prompts/config_phase3a.yaml
```

## Expected Output
- Baseline answer accuracy: ~42% (Phase 2)
- Optimized answer accuracy: ~45% (+3%)
- Optimized module saved to: `phase3a_dspy_prompts/optimized_module.json`
- MLFlow experiment: "Phase3a_DSPy_Prompts_Only"

## What Gets Optimized
- **ESGReasoning**: How to reason about ESG questions given context
- **AnswerExtraction**: How to extract precise answers from reasoning

## What Stays the Same
- Retrieval pipeline (no query generation)
- Top-5 semantic search with Qwen embeddings
- Same PGvector collection

## Runtime
- Expected: 20-30 minutes (light mode)
- Can monitor with: `mlflow ui`

## Notes
- This isolates the effect of prompt optimization alone
- No query generation complexity yet
- Results should show clear improvement from better prompts
- Phase 3b will add query generation on top of this
