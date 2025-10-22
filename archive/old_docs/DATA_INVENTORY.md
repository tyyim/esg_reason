# Data Inventory: Available Predictions and Results

**Last Updated**: 2025-10-19

This document tracks all saved predictions, evaluation results, and optimization outputs to avoid redundant searches and re-evaluations.

## Dev Set (93 questions)

### Baseline Predictions
- **File**: `dspy_baseline_dev_checkpoint.json`
- **Coverage**: 90/93 questions
- **Status**: ✅ Available
- **Format**: JSON with question-level predictions
  ```python
  {
    "predictions": [
      {
        "_store": {
          "answer": "...",
          "analysis": "...",
          "context": "...",
          "rationale": "..."
        }
      },
      ...
    ]
  }
  ```
- **Missing**: Questions 90-92 (3 questions)
- **Created**: October 16, 2025 (from qwen7b baseline evaluation)

### MIPROv2 Predictions
- **Saved Program**: `dspy_implementation/optimized_modules/baseline_rag_20251015_134537.json`
- **Question-Level Predictions**: ❌ NOT YET GENERATED
- **Aggregate Results**: `logs/qwen7b_test/teacher_student_qwen7b_results_20251016_230050.json`
  - Answer accuracy: 57.0% (53/93)
  - By format breakdowns available
- **Note**: Need to load program and evaluate to get question-level predictions

### GEPA Predictions
- **Saved Program**: `dspy_implementation/optimized_programs/gepa_skip_baseline_20251018_150806.json`
- **Question-Level Predictions**: ⚠️  PARTIALLY GENERATED (all ERROR due to missing answer_format param)
  - File: `gepa_dev_predictions.json`
  - Status: Invalid (missing parameter in call)
- **Aggregate from Log**: 54.8% (51/93)
- **Optimization Log**: `logs/gepa_optimization/gepa_skip_baseline_20251018_150802.log`
  - Contains iteration history
  - 84 connection errors during optimization
  - No question-level predictions saved

## Test Set (654 questions)

### Status
- **Baseline**: ❌ NOT YET EVALUATED
- **MIPROv2**: ❌ NOT YET EVALUATED
- **GEPA**: ❌ NOT YET EVALUATED

**Plan**: After dev set error analysis, run all three on test set for final comparison.

## Aggregate Performance Summary

From logs and partial results:

| Approach  | Dev Accuracy | Source |
|-----------|--------------|--------|
| Baseline  | 58.1% (54/93) | GEPA log baseline stated performance |
| MIPROv2   | 57.0% (53/93) | teacher_student_qwen7b_results JSON |
| GEPA      | 54.8% (51/93) | GEPA optimization log |

**Note**: These aggregate numbers don't match across sources - need to verify with question-level analysis.

## Data Source Files

### Dataset
- **Authoritative**: `mmesgbench_dataset_corrected.json` (933 questions)
- **Splits**:
  - Train: `dspy_implementation/data_splits/train_186.json` (186 questions, 20%)
  - Dev: `dspy_implementation/data_splits/dev_93.json` (93 questions, 10%)
  - Test: `dspy_implementation/data_splits/test_654.json` (654 questions, 70%)

### Optimization Programs
1. **Baseline (no optimization)**:
   - Module class: `BaselineMMESGBenchRAG`
   - Location: `dspy_implementation/dspy_rag_enhanced.py`
   - No saved program (initialized fresh each time)

2. **MIPROv2**:
   - Latest: `dspy_implementation/optimized_modules/baseline_rag_20251015_134537.json`
   - Size: 11KB
   - Modified: Oct 15, 2025 13:45
   - Python version mismatch warning: saved with 3.11, running on 3.10

3. **GEPA**:
   - Program: `dspy_implementation/optimized_programs/gepa_skip_baseline_20251018_150806.json`
   - Size: 10KB
   - Modified: Oct 18, 2025 16:24
   - Contains optimized reasoning prompts (7,749 chars)

### Logs
- **Baseline evaluation**: `logs/qwen7b_test/qwen7b_baseline_evaluation.log`
- **MIPROv2 optimization**: `logs/qwen7b_test/teacher_student_optimization_with_retry.log`
- **GEPA optimization**: `logs/gepa_optimization/gepa_skip_baseline_20251018_150802.log`

## Known Issues

### Baseline Predictions
- Missing 3/93 questions (indices 90-92)
- Need to complete evaluation

### MIPROv2
- Only aggregate results available
- Need question-level evaluation
- Python version mismatch (3.11 → 3.10)

### GEPA
- Failed question-level evaluation due to missing `answer_format` parameter
- All predictions show ERROR
- Need to fix script and re-evaluate

### Field Name Issues
- Dev set uses `answer` field, not `gt_answer`
- Need to check data schema before accessing fields

## Next Steps

1. ✅ Create data inventory (this file)
2. ⏳ Fix evaluation script bugs:
   - Add `answer_format` parameter to module calls
   - Use correct field name (`answer` not `gt_answer`)
3. ⏳ Complete baseline predictions (3 missing questions)
4. ⏳ Generate MIPROv2 question-level predictions
5. ⏳ Generate GEPA question-level predictions (fixed)
6. ⏳ Perform question-level error analysis
7. ⏳ Run test set evaluations (all three approaches)
