# CHANGELOG - ESG Reasoning Project

## 2025-10-12 - Baseline Prompt Optimization Test

### What We're Doing
Testing MIPROv2 optimization on ONLY reasoning + extraction prompts (no query generation) as a simplified test.

### Why
- Simplify first test to isolate prompt optimization effects
- Avoid complexity of query generation in initial test
- Establish baseline improvement metrics

### Configuration
- **Approach**: Baseline RAG (no query generation)
- **Optimizing**: ESGReasoning + AnswerExtraction signatures only
- **Mode**: Light (6 trials, ~20-30 min)
- **Training**: 186 questions (20%)
- **Evaluation**: 93 dev questions (10%)
- **Comparison**: Baseline vs Optimized on same 93 dev questions

### Critical Fixes Made
1. **Baseline evaluation dataset**: Changed from 20-question sample to full 93-question dev set (fair comparison)
2. **MLFlow parameter**: `query_optimization: False` (was True)
3. **Architecture metadata**: Updated to "Baseline RAG (no query generation)"
4. **Optimized components**: Removed QueryGeneration, only ESGReasoning + AnswerExtraction
5. **File naming**: Changed from `enhanced_rag_*` to `baseline_rag_*`

### Expected Outcome
- Baseline: ~55.6% on dev set (from full dataset eval)
- Target: +3-5% improvement from prompt optimization alone
- This will establish whether prompt optimization helps before adding query generation

---

## 2025-10-11 - Major Bug Discovery: "Not Answerable" Handling

### Issue Found
DSPy signatures didn't explicitly instruct the model to output "Not answerable" when context lacks information. This caused 0% accuracy on 150 "Not answerable" questions.

### Files Fixed
- `dspy_implementation/dspy_signatures.py`
- `dspy_implementation/dspy_signatures_enhanced.py`

### Impact
- **Before fix**: 37.3% accuracy on full dataset
- **After fix**: 55.6% accuracy (519/933 correct)
- **Improvement**: +18.3% just from fixing this bug

### Lesson Learned
Always explicitly specify edge case handling in DSPy signatures, even if it seems obvious.

---

## 2025-10-11 - Baseline Correction

### Issue
MMESGBench baseline was incorrectly calculated by just merging two files instead of substituting corrected results.

### Fix
Created `substitute_corrected_results.py` to properly:
1. Map questions by (question text, doc_id)
2. Substitute 16 corrected results into original 933
3. Recalculate overall accuracy

### Result
- **Corrected MMESGBench baseline**: 40.51% (378/933)
- **Our DSPy baseline**: 55.6% (519/933)
- **Our advantage**: +15.1% over MMESGBench baseline

---

## 2025-10-08 - Dataset Correction

### Issue
Dataset had incorrect document filenames (e.g., "AR6_SYR.pdf" instead of "AR6 Synthesis Report Climate Change 2023.pdf")

### Fix
Created mapping and corrected dataset saved as `mmesgbench_dataset_corrected.json`

### Files Created
- `mmesgbench_dataset_corrected.json` - Authoritative dataset (933 questions)
- Document name mapping in dataset loader

---

## Common Mistakes We Keep Making

1. **Not updating CLAUDE.md after major changes**
2. **Not testing on same dataset for comparisons** (20 samples vs full dev set)
3. **Incorrect metadata** (saying we're doing query optimization when we're not)
4. **Not documenting bug fixes immediately**
5. **Not cleaning up debug/test scripts**

---

## Workflow Improvements Needed

### Before Starting Any Task
1. ✅ Read CLAUDE.md to understand current state
2. ✅ Update todo list with specific task
3. ✅ Document what we're about to do in CHANGELOG

### During Work
1. ✅ Test on consistent datasets (no switching between samples)
2. ✅ Double-check metadata matches what we're actually doing
3. ✅ Verify configuration before running (checklist review)

### After Completing Task
1. ✅ Update CHANGELOG with what was done
2. ✅ Update CLAUDE.md with new status
3. ✅ Clean up any debug scripts → move to archive
4. ✅ Update todo list to mark complete
5. ✅ Commit changes with clear message

---

## Files to Clean Up (TODO)

### Debug/Test Scripts (move to archive/)
- `dspy_basic_parallel_evaluator.py` - Was for testing, now we have proper evaluation
- Old optimization logs

### Keep (Production)
- `dspy_implementation/enhanced_miprov2_optimization.py` - Main optimization script
- `quick_dev_eval.py` - Quick baseline checks
- `mmesgbench_exact_evaluation.py` - Exact evaluation logic
- All `dspy_implementation/` core modules

---
