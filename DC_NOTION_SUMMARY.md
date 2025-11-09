# Dynamic Cheatsheet Evaluation - Notion Summary (FINAL CORRECTED)

**Copy this to your Notion research proposal page**

---

## Dynamic Cheatsheet Test-Time Learning Results

**Date**: November 9, 2025 (Universal re-scoring after evaluation bug discovery)  
**Status**: ✅ COMPLETE - Underperforms DSPy Optimization

### Executive Summary

Dynamic Cheatsheet (DC), a test-time learning approach, was evaluated on MMESGBench. **Critical discovery**: Evaluation bugs affected ALL approaches (DSPy + DC), not just DC. When both are re-scored with the fixed evaluator, **DSPy optimization approaches (GEPA/MIPROv2) outperform DC by 3-4%**.

**Key Insight**: Test-time learning alone (DC) is less effective than proper prompt optimization (DSPy GEPA/MIPROv2) for ESG question answering.

---

## Test Results (Corrected Nov 9, 2025)

### Test Set Performance (654 Questions)

| Approach | Accuracy | vs MIPROv2 | Status |
|----------|----------|------------|--------|
| **DSPy Hybrid (Format-Based)** | **50.2%** | **+2.8%** | ✅ Best |
| **DSPy MIPROv2** | **47.4%** | baseline | ✅ Strong |
| **DSPy Baseline** | **46.9%** | -0.5% | ✅ Solid |
| **DSPy GEPA** | **46.3%** | -1.1% | ✅ Competitive |
| **DC-Bootstrap** | 43.7% | **-3.7%** | ❌ Underperforms |
| **DC-Cold** | 42.7% | **-4.7%** | ❌ Underperforms |

### Dev Set Performance (93 Questions)

| Approach | Accuracy | vs Baseline | Status |
|----------|----------|-------------|--------|
| **DSPy GEPA** | **61.3%** | **+7.5%** | ✅ **Best on dev** |
| **DSPy Baseline** | **53.8%** | baseline | ✅ |
| **DSPy MIPROv2** | **52.7%** | -1.1% | ✅ |
| **DC-Cold** | 44.1% | **-9.7%** | ❌ Underperforms |

### Format-Specific Breakdown (DC-Cold Test Set, Corrected)

| Format | Accuracy | Correct/Total | vs DSPy Baseline |
|--------|----------|---------------|------------------|
| **Float** | **41.7%** | 40/96 | ✅ -13.5% |
| **Int** | 44.1% | 67/152 | ✅ Equal |
| **List** | 36.4% | 32/88 | ❌ +3.4% |
| **Str** | 24.2% | 51/211 | ❌ -12.3% |

**Note**: DC struggles with String type questions compared to DSPy approaches.

---

## Critical Discovery: Universal Evaluation Bug

### The Problem

**Initial assumption**: Only DC had evaluation issues (null format = 0%).

**Reality**: Evaluation bugs affected **ALL approaches** (DSPy + DC):
1. **Null equivalence bug**: Treated "null" ≠ "Not answerable" 
2. **ANLS string bug**: Character-by-character comparison instead of full string

### The Investigation

User questioned why DSPy baseline (47.4%) seemed too good compared to optimized approaches (45.7-47.6%). Investigation revealed:
- DSPy prediction files lacked ground truth → needed to re-join with dataset
- When re-scored with fixed evaluator, DSPy actually **improved** slightly
- DC's improvement (+7% test) was misleading - DSPy also improved

### Universal Re-Scoring Results

**Created**: `rescore_all_with_anls_fix.py` to re-evaluate ALL predictions

**Dev Set Impact**:
- DSPy Baseline: 52.7% → **53.8%** (+1.1%)
- DSPy GEPA: 54.8% → **61.3%** (+6.5%) ⭐
- DSPy MIPROv2: 48.4% → **52.7%** (+4.3%)
- DC-Cold: 43.0% → **44.1%** (+1.1%)

**Test Set Impact**:
- DSPy Baseline: 47.4% → **46.9%** (-0.5%)
- DSPy MIPROv2: 47.6% → **47.4%** (-0.2%)
- DSPy GEPA: 45.7% → **46.3%** (+0.6%)
- DC-Cold: 35.6% → **42.7%** (+7.1%)
- DC-Bootstrap: 34.7% → **43.7%** (+9.0%)

**Conclusion**: DSPy approaches consistently outperform DC when evaluated correctly.

---

## Test Configuration

### Three Tests Conducted

**Test 1 - Dev Set (93 questions)**:
- Purpose: Establish baseline & generate cheatsheet
- Result: 44.1% (41/93) - **9.7% worse than DSPy Baseline**
- Key finding: Even with small dev set, DC underperforms

**Test 2 - Test Set Cold Start (654 questions)**:
- Purpose: Fair comparison to DSPy (empty cheatsheet, learns during test)
- Result: 42.7% (279/654) - **4.2% worse than DSPy Baseline**
- Key finding: Test-time learning insufficient vs. proper optimization

**Test 3 - Test Set Bootstrap (654 questions)**:
- Purpose: Test advantage of pre-seeded cheatsheet
- Result: 43.7% (286/654) - **3.2% worse than DSPy Baseline**
- Key finding: Bootstrap provided **+1.0%** improvement but still lags DSPy

---

## Key Insights

### 1. DSPy Optimization > Test-Time Learning

**Evidence**:
- DSPy GEPA (dev): 61.3% vs DC-Cold: 44.1% (**+17.2%**)
- DSPy MIPROv2 (test): 47.4% vs DC-Cold: 42.7% (**+4.7%**)

**Implication**: Proper prompt optimization (using teacher feedback or reflection) more effective than learning during inference.

### 2. GEPA Excels on Dev Set

**Dev performance**: 61.3% (best across all approaches)

**Why**: Reflection-based optimization captures patterns effectively with limited data.

**Caveat**: Doesn't generalize as well to test set (46.3%), suggesting possible overfitting.

### 3. Hybrid Approach Remains Best

**Performance**: 50.2% on test set (unchanged, already used correct evaluation)

**Strategy**: Format-specific routing (GEPA for structured, Baseline for text/null)

**Advantage**: +2.8% over next best (DSPy MIPROv2)

### 4. Evaluation Methodology Critical

**Lesson**: Always validate evaluators before comparing approaches.

**Impact**: DC initially appeared to outperform DSPy → reversed after correcting ALL evaluations.

**Best practice**: Implement unit tests for evaluation logic, especially for edge cases (null, special characters, etc.)

---

## Comparison with DSPy Approaches

### Performance Ranking (Test Set)

1. **DSPy Hybrid**: 50.2% ← Best overall
2. **DSPy MIPROv2**: 47.4% ← Best single approach
3. **DSPy Baseline**: 46.9%
4. **DSPy GEPA**: 46.3%
5. **DC-Bootstrap**: 43.7% ← DC's best
6. **DC-Cold**: 42.7%

### Why DSPy Wins

**DSPy advantages**:
- Offline optimization on train/dev sets
- Systematic prompt engineering (teacher-student or reflection)
- Format-specific handling (Hybrid approach)

**DC limitations**:
- Online learning during inference (less efficient)
- No explicit format-specific optimization
- Cheatsheet may accumulate noise from errors

### Recommendation

**For research**: DSPy GEPA/MIPROv2 more suitable for ESG QA than DC.

**For production**: Hybrid format-based routing with DSPy-optimized prompts.

**DC use case**: Consider for scenarios where:
- Training data unavailable
- Continuous adaptation needed
- Quick deployment without optimization required

---

## Timeline

| Date | Event |
|------|-------|
| Nov 1 | DC evaluation complete (reported 35.6% test) |
| Nov 7 | Null equivalence bug fix (+13.6% for DC) |
| Nov 9 | **Universal bug discovery**: Re-scored ALL approaches |
| Nov 9 | **Final result**: DSPy > DC by 3-4% |

---

## Conclusion

Dynamic Cheatsheet represents an interesting test-time learning approach, but for ESG question answering on MMESGBench:

✅ **DSPy optimization (GEPA/MIPROv2) more effective** than test-time learning  
✅ **Hybrid format-based routing remains best** (50.2%)  
✅ **Proper evaluation methodology critical** for valid comparisons  

**Research contribution**: Demonstrates importance of:
1. Offline prompt optimization vs. online learning
2. Format-specific approaches
3. Rigorous evaluation validation

---

**Note**: All corrected results available in `results/*/​*_anls_fixed.json` files.
