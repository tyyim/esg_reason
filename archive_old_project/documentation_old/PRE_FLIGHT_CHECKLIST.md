# Pre-Flight Checklist: Baseline Prompt Optimization
**Date**: 2025-10-12
**Task**: Run MIPROv2 optimization on baseline RAG (reasoning + extraction only)

---

## ✅ Configuration Verification

### Dataset
- [x] **File**: `mmesgbench_dataset_corrected.json` (authoritative 933 questions)
- [x] **Splits**: train_186.json, dev_93.json, test_654.json
- [x] **Baseline eval**: Dev set (93 questions) ✓
- [x] **Optimization training**: Train set (186 questions) ✓
- [x] **Optimized eval**: Dev set (93 questions) ✓
- [x] **Comparison**: Baseline vs Optimized on SAME 93 dev questions ✓

### Architecture
- [x] **Module**: BaselineMMESGBenchRAG (no query generation) ✓
- [x] **Optimizing**: ESGReasoning + AnswerExtraction only ✓
- [x] **NOT optimizing**: QueryGeneration ✓

### Parameters
- [x] **Auto mode**: "light" (6 trials, ~20-30 min) ✓
- [x] **query_optimization param**: False ✓
- [x] **No conflicting params**: max_bootstrapped_demos/max_labeled_demos removed ✓

### Metadata
- [x] **Architecture description**: "Baseline RAG (no query generation)" ✓
- [x] **Optimized components list**: ["ESGReasoning", "AnswerExtraction"] ✓
- [x] **Experiment name**: "MMESGBench_Baseline_Optimization" ✓
- [x] **File naming**: baseline_rag_* (not enhanced_rag_*) ✓

### Comparison Logic
- [x] **Baseline evaluation**: On dev set (93) ✓
- [x] **Optimized evaluation**: On dev set (93) ✓
- [x] **Comparison**: baseline_results vs dev_results (both on same 93) ✓
- [x] **Apples to apples**: YES ✓

---

## ✅ Documentation

- [x] **CLAUDE.md updated**: Current focus reflects this test
- [x] **CHANGELOG.md created**: Task documented
- [x] **WORKFLOW.md created**: Process established
- [x] **Pre-flight checklist**: This file

---

## ✅ Expected Outcome

### Baseline (Full dataset 933 questions)
- **Current**: 55.6% accuracy (519/933)
- **On dev set**: TBD (will measure)

### After Optimization
- **Target**: +3-5% improvement
- **Why realistic**: Just prompt optimization, no architecture changes

### Success Criteria
- Optimization completes without errors
- Results logged to MLFlow
- Clear comparison showing improvement (or lack thereof)
- Documented in CHANGELOG

---

## 🚀 Ready to Run

**Command**:
```bash
nohup python dspy_implementation/enhanced_miprov2_optimization.py > logs/baseline_opt_20251012.log 2>&1 &
```

**Monitor**:
```bash
tail -f logs/baseline_opt_20251012.log
```

**Expected Duration**: ~30-40 minutes total
- Baseline eval: ~5-8 min (93 questions)
- Optimization: ~20-25 min (6 trials, 186 train questions)
- Optimized eval: ~5-8 min (93 questions)

---

## 📝 After Completion

- [ ] Update CHANGELOG.md with results
- [ ] Update CLAUDE.md with new baseline/status
- [ ] Save optimization output
- [ ] Document lessons learned
- [ ] Clean up any debug files

---

**All checks passed ✅ - Ready to proceed**
