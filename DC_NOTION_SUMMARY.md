# Dynamic Cheatsheet Evaluation - Notion Summary

**Copy this to your Notion research proposal page**

---

## Dynamic Cheatsheet Test-Time Learning Results

**Date**: November 1, 2025  
**Status**: ❌ COMPLETE - Underperformed

### Executive Summary

Dynamic Cheatsheet (DC), a test-time learning approach, was evaluated on MMESGBench and **significantly underperformed** all DSPy optimization approaches (35.6% vs 45.7-50.2%). The root cause: **DC scored 0% on all 107 "null" format questions** (questions requiring "null" when unanswerable), representing 16.4% of the test set.

---

## Test Results

### Test Set Performance (654 Questions)

| Approach | Accuracy | vs Baseline | Status |
|----------|----------|-------------|--------|
| **DSPy Hybrid** | 50.2% | +2.8% | ✅ Best |
| **DSPy Baseline** | 47.4% | baseline | ✅ |
| **DSPy MIPROv2** | 47.6% | +0.2% | ✅ |
| **DSPy GEPA** | 45.7% | -1.7% | ⚠️ |
| **DC-Cold** | **35.6%** | **-11.8%** | ❌ |
| **DC-Bootstrap** | **34.7%** | **-12.7%** | ❌ |

### Format-Specific Breakdown (DC-Cold)

| Format | Accuracy | Correct/Total | Notes |
|--------|----------|---------------|-------|
| Int | 44.1% | 67/152 | Reasonable |
| Float | 41.7% | 40/96 | Reasonable |
| Str | 44.5% | 94/211 | Reasonable |
| List | 36.4% | 32/88 | Weak |
| **null** | **0.0%** | **0/107** | ❌ **Critical failure** |

---

## Critical Finding: Null Format Problem

### The Issue

**DC scored 0% on ALL null format questions** across dev (0/14) and test (0/107) sets.

- Null format = questions that should return "null" when not answerable from context
- DC "tries too hard" to extract an answer instead of recognizing unanswerable questions
- **107 guaranteed wrong answers** = 16.4% of test set

### Impact Analysis

If DC had better null format handling:

| Null Accuracy | Overall Accuracy | vs Baseline | Result |
|---------------|------------------|-------------|--------|
| **0% (actual)** | **35.6%** | -11.8% | ❌ Major underperformance |
| 50% | 43.9% | -3.5% | Competitive with GEPA |
| 90% | 50.3% | +2.9% | **Beats baseline!** |

**Conclusion**: The null format problem alone explains DC's underperformance.

---

## Test Configuration

### Three Tests Conducted

**Test 1: Dev Set (93 questions)**
- Purpose: Establish baseline, generate cheatsheet
- Result: 43.0% (40/93)
- Null: 0/14 (0%)

**Test 2: Test Set - Cold Start (654 questions)**
- Purpose: Fair comparison to DSPy (no prior learning)
- Cheatsheet: Empty → learns during test
- Result: 35.6% (233/654)
- Null: 0/107 (0%)

**Test 3: Test Set - Bootstrap (654 questions)**
- Purpose: Test if dev learning transfers
- Cheatsheet: Pre-loaded with dev cheatsheet (3,654 chars)
- Result: 34.7% (227/654)
- Null: 0/107 (0%)
- **Finding**: Bootstrap didn't help (-0.9% vs cold)

---

## Key Insights

### 1. Null Format is the Killer

- DC cannot recognize when questions are unanswerable
- Consistently attempts to extract answers even when none exist
- 16.4% of test set guaranteed wrong
- **Root cause of 11.8% performance gap**

### 2. Bootstrap Didn't Transfer

- Dev cheatsheet (43.0% accuracy) didn't help test set (34.7%)
- Suggests overfitting to dev set patterns
- Test set may have different distribution
- **Test-time learning didn't generalize**

### 3. Reasonable Performance on Other Formats

- Int/Float/Str: 39-46% (comparable to some DSPy approaches on these formats)
- List: 36% (weaker)
- **DC isn't fundamentally broken** - just has null format blindspot

### 4. Prompt Engineering Matters

- Attempted "fair" comparison with DSPy-matching prompts: 25.8% (worse)
- Original DC prompts: 43.0% (better)
- **Different approaches need different prompts**

---

## Comparison with DSPy Approaches

### Performance Ranking (Test Set, 654 Questions)

1. **DSPy Hybrid (Format-Based)**: 50.2% ✅ Best
2. **DSPy Baseline**: 47.4%
3. **DSPy MIPROv2**: 47.6%
4. **DSPy GEPA**: 45.7%
5. **DC-Cold**: 35.6% ❌ -11.8% vs baseline
6. **DC-Bootstrap**: 34.7% ❌ -12.7% vs baseline

### Cost Analysis

| Approach | API Calls/Question | Time/Question | Relative Cost |
|----------|-------------------|---------------|---------------|
| DSPy Baseline | 2 | ~20 sec | 1x |
| DSPy GEPA | 2 | ~20 sec | 1x |
| **DC** | **2** | **~13 sec** | **1x** |

**Note**: DC has same API cost as DSPy approaches, but faster per question due to simpler architecture.

---

## Recommendation

### DO NOT Use DC for MMESGBench

**Unless null format detection is fixed**:
- Test-time learning concept is theoretically sound
- Implementation has critical flaw in recognizing unanswerable questions
- Would require significant prompt engineering to fix

### Future Work (If Pursuing DC)

1. **Fix null format detection**:
   - Add explicit "not answerable" detection to generator prompt
   - Train model to output "null" when context is insufficient
   - Test on null-only subset before full evaluation

2. **Improve cheatsheet transfer**:
   - Current dev→test transfer didn't help
   - May need better generalization in curator prompt
   - Consider format-specific cheatsheets

3. **Format-specific routing**:
   - DC performs decently on Int/Float/Str (39-46%)
   - Could use DC for answerable questions, fallback for null
   - Similar to Hybrid approach that achieved 50.2%

### Recommended Approach for MMESGBench

**DSPy Hybrid (Format-Based Routing)** remains the best approach:
- 50.2% accuracy (2.8% above baseline)
- Uses different strategies per format
- No null format catastrophic failure
- Proven generalization from dev to test

---

## Files and Documentation

**Results Files**:
- Test 2 (Cold): `results/dc_experiments/dc_cumulative_cold_test_20251101_171723.json`
- Test 3 (Bootstrap): `results/dc_experiments/dc_cumulative_cold_test_20251101_172109.json`
- Dev cheatsheet: `results/dc_experiments/dev_cheatsheet_20251101.txt`

**Documentation**:
- Implementation: `dspy_implementation/dc_module/`
- Complete results: `DC_TESTS_STATUS.md`
- Plan: `DC_THREE_TESTS_PLAN.md`
- Summary: `DC_IMPLEMENTATION_SUMMARY.md`

---

## Timeline

| Date | Event | Result |
|------|-------|--------|
| Nov 1, 15:31 | Test 1 started (dev set) | 43.0% |
| Nov 1, 17:17 | Test 2 started (cold) | - |
| Nov 1, 17:21 | Test 3 started (bootstrap) | - |
| Nov 1, 20:44 | Test 3 complete | 34.7% |
| Nov 1, 21:12 | Test 2 complete | 35.6% |

**Total runtime**: ~6 hours  
**Total cost**: ~$0.66

---

## Conclusion

Dynamic Cheatsheet's test-time learning approach showed promise but **failed critically on null format questions** (0%), resulting in 35.6% accuracy vs DSPy Hybrid's 50.2%. The null format problem alone accounts for the entire performance gap. 

**Verdict**: ❌ Not recommended for MMESGBench without significant improvements to null format detection.

**Best approach remains**: DSPy Hybrid (Format-Based Routing) at 50.2%

---

**Updated**: November 1, 2025  
**Status**: Evaluation complete, DC not recommended for production

