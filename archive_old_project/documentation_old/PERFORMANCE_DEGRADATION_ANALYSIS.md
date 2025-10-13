# Performance Degradation Analysis - Sept 28 → Oct 10

## Executive Summary

**CRITICAL BUG FOUND**: The current DSPy baseline implementation has **0% accuracy on "Not answerable" questions** (0/150), whereas the Sept 28 evaluation correctly handled these questions at **48% accuracy** (71/148).

This bug accounts for the entire 2.6% performance degradation from 39.9% → 37.3%.

---

## Timeline of Evaluations

| Date | Method | Accuracy | Questions | File |
|------|--------|----------|-----------|------|
| **Sept 28** | ColBERT + MMESGBench exact logic | **39.9%** | 933 | `optimized_full_dataset_mmesgbench_with_f1.json` |
| **Oct 1** | ColBERT corrected (subset) | 46.8% | 47 | `corrected_evaluation_results/colbert_corrected_evaluation.json` |
| **Oct 10** | DSPy Baseline RAG | **37.3%** | 933 | `baseline_results_20251010_232606.json` |
| **Oct 10** | DSPy Enhanced RAG | **32.9%** | 933 | `enhanced_results_20251010_232606.json` |

---

## Overall Performance Comparison

```
Sept 28 Optimized:   39.9% (372/933 correct)
Oct 10 Baseline:     37.3% (348/933 correct)  ⬇️ -2.6%
Oct 10 Enhanced:     32.9% (307/933 correct)  ⬇️ -7.0%
```

### Degradation Breakdown:
- **Sept 28 → Oct 10 Baseline**: -2.6% (24 questions lost)
- **Baseline → Enhanced**: -4.4% (41 questions lost)

---

## Three-Metric Breakdown

### Oct 10 Baseline (37.3% E2E):
- **Retrieval**: 75.6% (705/933)
- **Answer**: 45.7% (426/933)
- **E2E**: 37.3% (348/933)

### Oct 10 Enhanced (32.9% E2E):
- **Retrieval**: 71.9% (671/933) ⚠️ **WORSE than baseline**
- **Answer**: 41.1% (383/933)
- **E2E**: 32.9% (307/933)

**KEY FINDING**: Query generation is hurting retrieval performance by 3.7%!

---

## Format-Level Performance Comparison

| Format | Sept 28 | Oct 10 Baseline | Oct 10 Enhanced | Δ (Sept→Base) |
|--------|---------|-----------------|-----------------|---------------|
| **Int** | 42.5% | **51.2%** ✅ | 45.9% | **+8.7%** |
| **Str** | 38.5% | **43.1%** ✅ | 40.1% | **+4.7%** |
| **Float** | 33.8% | **42.2%** ✅ | 40.1% | **+8.4%** |
| **List** | 36.6% | **39.4%** ✅ | 25.8% ⬇️ | **+2.8%** |
| **None/null** | 48.0% | **0.0%** 🔴 | **0.0%** 🔴 | **-48.0%** |

### Critical Finding: "Not Answerable" Questions Completely Broken

**Sept 28**:
- 148 "Not answerable" questions
- 71 correctly predicted as "Not answerable" (48% accuracy)
- Model correctly recognized unanswerable questions

**Oct 10 Baseline**:
- 150 "Not answerable" questions
- **0 correctly predicted as "Not answerable" (0% accuracy)** 🔴
- Model either returns `None` (empty) or hallucinates answers

**Example Failures**:
```
Q: "Which five countries have the highest percentage of girls proficient in advanced programming?"
Ground Truth: "Not answerable"
Oct 10 Predicted: ['State of Palestine', 'Albania', 'Saudi Arabia', 'Egypt', 'Jordan']
Result: WRONG (hallucinated answer)

Q: "What are the key areas of social determinants that the campaign focuses on?"
Ground Truth: "Not answerable"
Oct 10 Predicted: ["Socioeconomic conditions", "Education", "Housing and living conditions", ...]
Result: WRONG (hallucinated answer)
```

---

## Root Cause Analysis

### 1. **Implementation Differences**

**Sept 28 (Working)**:
- Method: "Optimized ColBERT with pre-computed retrievals"
- Evaluation: "Re-evaluated with exact MMESGBench evaluation logic"
- Script: Likely `colbert_text_only_evaluation.py` or `mmesgbench_retrieval_replication.py`
- Correctly handles "Not answerable" cases

**Oct 10 (Broken)**:
- Method: `dspy_rag_enhanced.py` → `BaselineMMESGBenchRAG`
- Evaluation: `dspy_metrics_enhanced.py` → `evaluate_predictions_enhanced()`
- New DSPy-based implementation with different answer extraction logic
- **Cannot recognize "Not answerable" cases**

### 2. **Answer Extraction Logic Broken**

The DSPy implementation's answer extraction is either:
- Not prompting the model to output "Not answerable"
- Not recognizing "Not answerable" in model outputs
- Stripping/filtering "Not answerable" responses
- Hallucinating answers instead of declining

### 3. **Query Generation Hurting Retrieval**

Enhanced RAG retrieval (71.9%) is **worse** than Baseline (75.6%):
- Query generation adds noise/complexity
- Default prompts may be suboptimal
- MIPROv2 optimization on dev set didn't generalize

---

## Impact Analysis

### If "Not Answerable" Bug is Fixed:

Assuming we restore Sept 28's 48% accuracy on 150 null questions:
```
Current Oct 10 Baseline: 348 correct
Add back null questions: +72 correct (150 × 0.48)
Projected accuracy: 420/933 = 45.0%
```

**This would put us at 45.0%**, which is:
- ✅ Better than Sept 28 (39.9%)
- ✅ Validates improvements in Int/Str/Float/List formats
- ✅ Matches our dev set performance (46.2%)

---

## Next Steps (Priority Order)

### 1. **FIX: "Not Answerable" Handling (CRITICAL)**

**Investigation**:
- [ ] Compare `dspy_signatures_enhanced.py` extraction signature with Sept 28's prompts
- [ ] Check if "Not answerable" is in the extraction signature instructions
- [ ] Review `dspy_metrics_enhanced.py` evaluation logic for null handling

**Fix Strategy**:
- Update `AnswerExtraction` signature to explicitly handle "Not answerable"
- Add instructions: "If the context does not contain the answer, respond with 'Not answerable'"
- Test on dev set null questions before full re-evaluation

**Expected Impact**: +5-8% E2E accuracy

### 2. **FIX: Query Generation Hurting Retrieval**

Enhanced retrieval (71.9%) < Baseline (75.6%) suggests query optimization is counterproductive.

**Investigation**:
- [ ] Compare baseline vs enhanced retrieval on same questions
- [ ] Check if MIPROv2 optimized queries are too specific or too general
- [ ] Verify dev set → full dataset generalization

**Fix Strategy**:
- Disable query optimization until prompts are better optimized
- Or run MIPROv2 on larger training set (300+ questions)
- Or use medium/heavy mode for better generalization

**Expected Impact**: +3-4% E2E accuracy

### 3. **VALIDATE: Sept 28 Script Still Works**

Re-run Sept 28's exact evaluation method to ensure reproducibility:
```bash
# Find and run original script
python colbert_text_only_evaluation.py  # or similar
```

**Purpose**: Confirm Sept 28 results are reproducible and establish "gold standard"

### 4. **DOCUMENT: Evaluation Method Differences**

Create clear documentation of:
- Which scripts produce which metrics
- What evaluation logic each uses
- How to compare results across methods

---

## Positive Findings

Despite the "Not answerable" bug, the new implementation shows improvements:
- **Int format**: +8.7% (42.5% → 51.2%) ✅
- **Str format**: +4.7% (38.5% → 43.1%) ✅
- **Float format**: +8.4% (33.8% → 42.2%) ✅
- **List format**: +2.8% (36.6% → 39.4%) ✅

This suggests the DSPy baseline RAG has **better answer extraction** for extractable answers, but **completely fails** on unanswerable questions.

---

## Conclusion

The 2.6% performance degradation is **entirely due to a single bug**: the DSPy implementation cannot handle "Not answerable" questions.

**Once fixed, we expect 45%+ accuracy**, which would validate:
1. Improvements in extractable answer formats
2. DSPy baseline architecture
3. Three-metric evaluation methodology

**Priority**: Fix "Not answerable" handling before any further optimization work.
