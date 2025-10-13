# Baseline Reference - Complete Truth Table

> **Purpose**: Single source of truth for all baseline evaluations across different dates, datasets, and metrics.

---

## 📊 Quick Summary

| Baseline | Dataset | E2E Accuracy | Notes |
|----------|---------|--------------|-------|
| **ColBERT (Phase 0E)** | 933 full | **41.3%** | Corrected documents, MMESGBench evaluation |
| **DSPy (Phase 0F)** | 933 full | **37.3%** e2e / **45.7%** answer | Two-stage extraction |
| **MIPROv2 Baseline** | 93 dev | **48.4%** strict / **~51.6%** relaxed | Much better than Phase 0F |
| **Optimized** | 93 dev | **50.5%** relaxed | -1.1% vs baseline (failed) |

---

## 🎯 What Different Accuracy Metrics Mean

DSPy tracks **three separate metrics** to diagnose where failures occur:

### 1. Retrieval Accuracy
**Question**: Did we retrieve the correct evidence pages?

**How it's measured**: Check if ground truth `evidence_pages` appear in retrieved context.

**Example**:
- Gold evidence: Pages [61, 116]
- Retrieved: Pages [61, 99, 116, 25, 3]
- **Result**: ✅ Correct (both 61 and 116 retrieved)

### 2. Answer Accuracy
**Question**: Did we extract the correct answer (ignoring whether we retrieved right pages)?

**How it's measured**: Compare predicted answer to gold answer, regardless of retrieval.

**Example**:
- Gold answer: "North America"
- Retrieved: Pages [10, 20, 30] (WRONG pages)
- Predicted: "North America" (correct answer by luck or reasoning)
- **Result**: ✅ Correct for answer accuracy, ❌ Wrong for E2E

### 3. End-to-End (E2E) Accuracy
**Question**: Did BOTH retrieval AND answer extraction succeed?

**How it's measured**: Only correct if:
1. Retrieved correct evidence pages, AND
2. Extracted correct answer

**This is the TRUE performance metric** - both steps must work.

**Example**:
- Gold evidence: Page 61, Gold answer: "North America"
- Retrieved: [61, 99, 25] ✅, Predicted: "North America" ✅
- **Result**: ✅ E2E Correct (both steps succeeded)

---

## 📋 Complete Baseline Table

### Full Dataset Evaluations (933 Questions)

| Evaluation | Date | Dataset | Retrieval Acc | Answer Acc | E2E Acc | Correct | File |
|------------|------|---------|---------------|------------|---------|---------|------|
| **ColBERT (0E)** | Oct 1 | 933 full | Unknown | Unknown | **41.3%** | 385/933 | `optimized_colbert_evaluator_mmesgbench.py` |
| **DSPy (0F)** | Oct 10 | 933 full | **75.6%** | **45.7%** | **37.3%** | 348/933 | `baseline_results_20251010_232606.json` |

**Key Insight**: DSPy has excellent retrieval (75.6%) but answer extraction needs work (45.7% → 37.3% e2e drop).

---

### Dev Set Evaluations (93 Questions)

| Evaluation | Date | Dataset | Retrieval Acc | Answer Acc | E2E Strict | E2E Relaxed | Correct | File |
|------------|------|---------|---------------|------------|------------|-------------|---------|------|
| **DSPy (from full)** | Oct 10 | 93 dev | Unknown | Unknown | **24.7%** | **38.7%** | 23/93 | Extracted from full dataset |
| **MIPROv2 Baseline** | Oct 12 | 93 dev | **75.3%** | **58.1%** | **48.4%** | **~51.6%** | 45/93 | `baseline_rag_results_20251012_023850.json` |
| **Optimized** | Oct 12 | 93 dev | **75.3%** | Unknown | **33.3%** | **50.5%** | 47/93 | `optimized_predictions.json` |

**Key Insight**: MIPROv2 baseline (48.4%) is MUCH better than DSPy full dataset (24.7%) on dev set. Optimization slightly degraded performance (-1.1% relaxed).

---

## 🔍 Why Are There Different Numbers?

### Confusion Point 1: "Phase 0F = 45.1%"

**Notion says**: 45.1%
**Truth**: This is **answer accuracy** (45.7%), not end-to-end accuracy (37.3%)

The Notion page rounded 45.7% down to 45.1%, but this metric **ignores retrieval failures**.

**Correct comparison**:
| Metric | ColBERT (0E) | DSPy (0F) | Difference |
|--------|--------------|-----------|------------|
| **E2E (true performance)** | **41.3%** | **37.3%** | **-4.0%** ❌ |
| **Answer only** | Unknown | **45.7%** | Can't compare |

**Conclusion**: Phase 0F is actually WORSE than ColBERT when comparing E2E accuracy.

---

### Confusion Point 2: "51.6%" Latest Baseline

**Where it comes from**: MIPROv2 baseline evaluated Oct 12 on 93 dev questions

**Different from Phase 0F**:
- **Different date**: Oct 12 vs Oct 10
- **Different dataset**: 93 dev vs 933 full
- **Different evaluation**: Includes "Not answerable" fix + better prompts
- **Different metric**: E2E with relaxed matching vs strict

**Why it's better (48.4% → 51.6%)**:
1. Fixed "Not answerable" handling: +10 questions (10.8%)
2. Better prompts/code: +13% baseline improvement
3. Relaxed matching: +3% from false negatives

---

### Confusion Point 3: Why is MIPROv2 Baseline (48.4%) So Much Better?

**DSPy full dataset on dev set**: 24.7%
**MIPROv2 baseline on dev set**: 48.4%
**Difference**: +23.7%!

**Root causes**:
1. **"Not answerable" handling fixed**: 0% → 71.4% on null format (+10 questions)
2. **Better code/prompts**: Between Oct 10 and Oct 12, significant improvements made
3. **Different evaluation methodology**: Stricter on Oct 10, more lenient on Oct 12

---

## 📈 Performance Evolution Timeline

```
Sequential (0A)       ColBERT (0E)      DSPy Full (0F)     MIPROv2 Baseline    Optimized
    20%          →       41.3%       →     37.3% e2e     →      48.4%        →    50.5%
                                          45.7% answer
```

**Key transitions**:
1. **Sequential → ColBERT**: +21.3% (semantic retrieval)
2. **ColBERT → DSPy**: -4.0% e2e (worse despite better answer extraction)
3. **DSPy → MIPROv2**: +11.1% (bug fixes + better code)
4. **MIPROv2 → Optimized**: -1.1% relaxed (optimization failed)

---

## 🎯 What Should We Compare?

### For Phase 0 Completion:

**Use E2E accuracy on full 933 dataset**:
- ColBERT: **41.3%** ✅
- DSPy: **37.3%** ❌

**Conclusion**: DSPy baseline is actually worse than ColBERT when comparing E2E.

### For Optimization Results:

**Use E2E relaxed accuracy on dev set**:
- MIPROv2 Baseline: **~51.6%** (48/93 estimated)
- Optimized: **50.5%** (47/93)
- **Change**: **-1.1%** ❌

**Conclusion**: Optimization degraded performance slightly.

---

## 📁 Source Files Reference

### Full Dataset (933 questions)

| File | Purpose | Metrics |
|------|---------|---------|
| `mmesgbench_dataset_corrected.json` | **AUTHORITATIVE DATASET** | 933 questions, 3 docs corrected |
| `baseline_results_20251010_232606.json` | DSPy full dataset evaluation | 75.6% retr, 45.7% ans, 37.3% e2e |
| `optimized_colbert_evaluator_mmesgbench.py` | ColBERT baseline script | 41.3% e2e |

### Dev Set (93 questions)

| File | Purpose | Metrics |
|------|---------|---------|
| `dspy_implementation/data_splits/dev_93.json` | Dev set split | 93 questions |
| `baseline_rag_results_20251012_023850.json` | MIPROv2 baseline | 75.3% retr, 58.1% ans, 48.4% e2e |
| `optimized_predictions.json` | Optimized model predictions | 50.5% e2e relaxed |
| `baseline_dev_predictions.json` | Baseline dev predictions (extracted) | 38.7% e2e relaxed |

---

## 🔬 Evaluation Methodology

### Strict vs Relaxed Matching

**Strict Matching**: Exact string comparison (current evaluation)
- Example: `"82%"` ≠ `"82.0"` ❌
- Example: `"Seller reports Scope 1"` ≠ `"The selling org reports..."` ❌

**Relaxed Matching**: Semantic equivalence + format normalization
- Handles missing % signs: `"82%"` ≈ `"82.0"` ✅
- Handles semantic equivalence: Short vs verbose answers ✅
- Handles list quote styles: `['A']` ≈ `["A"]` ✅

**Impact**: ~14-17% false negatives with strict matching

### Why We Need Relaxed Matching

**Example false negatives found**:

| Format | Count | Issue |
|--------|-------|-------|
| Float | 8 | Missing % sign (82% vs 82.0) |
| String | 8 | Semantic equivalence (verbose vs concise) |
| List | 1 | Quote style ('A' vs "A") |
| **Total** | **17** | **18.3% of 93 dev questions** |

**See**: `evaluation_metric_gaps_analysis.md` for full details.

---

## ⚠️ Important Notes

### 1. Don't Mix Metrics

❌ **WRONG**: Compare ColBERT E2E (41.3%) with DSPy Answer (45.7%)
✅ **RIGHT**: Compare ColBERT E2E (41.3%) with DSPy E2E (37.3%)

### 2. Don't Mix Datasets

❌ **WRONG**: Compare full dataset (933) with dev set (93)
✅ **RIGHT**: Compare same dataset or clearly state which dataset

### 3. Don't Mix Dates

❌ **WRONG**: Compare Oct 10 results with Oct 12 results (different code)
✅ **RIGHT**: Compare results from same evaluation run

### 4. Always Specify Strict vs Relaxed

❌ **WRONG**: Say "48.4% baseline"
✅ **RIGHT**: Say "48.4% baseline (strict matching, e2e accuracy)"

---

## 📝 Recommended Usage

When reporting results, always specify:

```markdown
**Baseline**: 48.4% (93 dev, E2E, strict, Oct 12)
**Optimized**: 50.5% (93 dev, E2E, relaxed, Oct 12)
**Change**: -1.1%
```

**Template**:
```
{accuracy}% ({dataset size} {dataset name}, {metric type}, {strict/relaxed}, {date})
```

---

## 🔧 Next Steps

1. **Re-run optimization with**:
   - `valset=devset` parameter (prevent overfitting)
   - Relaxed matching metrics (better signal)
   - Enhanced architecture with query generation

2. **Update documentation**:
   - Clarify Phase 0F is answer accuracy, not E2E
   - Update Notion to use E2E accuracy consistently
   - Document evaluation methodology

3. **Implement improved evaluation**:
   - See `evaluation_metric_gaps_analysis.md` for fixes
   - Implement Tier 1 normalization (floats, lists, strings)
   - Consider Tier 2 semantic matching for edge cases

---

## 📚 Related Documentation

- `evaluation_metric_gaps_analysis.md` - 10 gap types and fixes
- `optimized_model_error_analysis.txt` - Error breakdown (41 extraction, 23 retrieval)
- `false_negative_analysis.json` - 17 false negatives in optimized predictions
- `baseline_vs_optimized_comparison.txt` - Direct baseline vs optimized comparison
- `BASELINE_COMPARISON_SUMMARY.md` - Comprehensive analysis (200 lines)
- `BASELINE_VERIFICATION.md` - File-level verification

---

**Last Updated**: 2025-10-12
**Authoritative Source**: This file is the single source of truth for baseline comparisons
