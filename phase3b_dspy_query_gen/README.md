# Phase 3b: DSPy Query Generation Optimization

## Goal
Add query generation optimization on top of Phase 3a optimized prompts.

**Target**: ~47% answer accuracy (+2% over Phase 3a)

## Method
- **Base**: Phase 3a optimized prompts (reasoning + extraction)
- **Add**: QueryGeneration signature (learnable query reformulation)
- **Optimization**: All three signatures (query + reasoning + extraction)
- **Optimizer**: MIPROv2 (medium mode, 10-15 trials)
- **Training**: 186 questions (20% of dataset)
- **Validation**: 93 questions (10% of dataset)

## Files
- `config_phase3b.yaml` - Configuration for Phase 3b optimization
- `README.md` - This file
- `run_optimization.py` - Will call dspy_implementation/enhanced_miprov2_optimization.py

## Usage
```bash
# Run Phase 3b optimization (after Phase 3a completes)
./run_phase3b.sh

# Or directly
python -m dspy_implementation.enhanced_miprov2_optimization \
  --config phase3b_dspy_query_gen/config_phase3b.yaml
```

## Expected Output
- Phase 3a answer accuracy: ~45%
- Phase 3b answer accuracy: ~47% (+2%)
- Optimized module saved to: `phase3b_dspy_query_gen/optimized_module.json`
- MLFlow experiment: "Phase3b_DSPy_QueryGen"

## What Gets Optimized
- **QueryGeneration**: How to reformulate questions for better retrieval
- **ESGReasoning**: Continue optimizing reasoning (starts from Phase 3a)
- **AnswerExtraction**: Continue optimizing extraction (starts from Phase 3a)

## Key Innovation
- **Better retrieval** through optimized query reformulation
- Should improve retrieval accuracy significantly
- This addresses the "retrieval bottleneck" identified in research

## Runtime
- Expected: 30-45 minutes (medium mode)
- Can monitor with: `mlflow ui`

## Notes
- Builds incrementally on Phase 3a (doesn't start from scratch)
- Query generation helps find more relevant evidence
- This is the FULL DSPy optimization pipeline
- Final accuracy target: 47% (7% improvement over Phase 1 baseline)
