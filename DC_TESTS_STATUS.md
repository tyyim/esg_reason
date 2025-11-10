# DC Tests Status - FINAL CORRECTED

**Date**: November 9, 2025 (Universal re-scoring after evaluation bug discovery)  
**Status**: ✅ COMPLETE - DSPy Outperforms DC

---

## 🚨 CRITICAL UPDATE: Universal Evaluation Bug Discovery

### What Happened

User questioned why DSPy baseline (47.4%) seemed too good. Investigation revealed:
- **Evaluation bugs affected ALL approaches** (DSPy + DC), not just DC
- **Original results were INCORRECT** for both DSPy and DC
- **Re-scoring with fixed evaluator** → DSPy consistently outperforms DC

### The Bugs

1. **Null equivalence**: Treated "null" ≠ "Not answerable" (fixed Nov 7)
2. **ANLS string bug**: Character-by-character comparison (fixed Nov 9)

### Re-Scoring Impact

**DC improvements**:
- Test Cold: 35.6% → **42.7%** (+7.1%)
- Test Bootstrap: 34.7% → **43.7%** (+9.0%)

**But DSPy also improved**:
- Dev GEPA: 54.8% → **61.3%** (+6.5%)
- Dev Baseline: 52.7% → **53.8%** (+1.1%)

**Final verdict**: DSPy approaches outperform DC by 3-4%.

---

## ✅ Final Results Summary (Corrected)

| Approach | Dev (93 Q) | Test (654 Q) | vs DSPy Baseline | Rank |
|----------|------------|--------------|------------------|------|
| **DSPy Hybrid** | — | **50.2%** | **+3.3%** | 🥇 1st |
| **DSPy MIPROv2** | 52.7% | **47.4%** | **+0.5%** | 🥈 2nd |
| **DSPy Baseline** | **53.8%** | **46.9%** | baseline | 🥉 3rd |
| **DSPy GEPA** | **61.3%** ⭐ | 46.3% | -0.6% | 4th |
| **DC-Bootstrap** | — | 43.7% | **-3.2%** ❌ | 5th |
| **DC-Cold (CU)** | 44.1% | 42.7% | **-4.2%** ❌ | 6th |
| **DC-RS** | 44.1% | — | **-9.7%** ❌ | 6th (tie) |

**Key Finding**: DSPy optimization > Test-time learning for ESG QA

**DC-RS Note**: DC-RS (Retrieval & Synthesis) = DC-CU (Cumulative) in accuracy (44.1%) but **10x slower** (43s vs 4s per question). Not worth the cost.

---

## Test 1: Dev Set (93 Questions) - Corrected

**Purpose**: Establish baseline & generate cheatsheet  
**Result**: 44.1% (41/93)  
**vs DSPy Baseline**: **-9.7%** (53.8% → 44.1%)

### Format Breakdown

| Format | Accuracy | Correct/Total | vs DSPy Baseline |
|--------|----------|---------------|------------------|
| **Float** | **69.2%** | 9/13 | ✅ Equal |
| **Int** | 42.1% | 8/19 | ❌ -21.1% |
| **List** | 46.2% | 6/13 | ✅ +23.1% |
| **Str** | 14.7% | 5/34 | ❌ -23.5% |

**Issue**: DC struggles significantly with Int and Str types on dev set.

---

## Test 2: Test Set Cold Start (654 Questions) - Corrected

**Purpose**: Fair comparison to DSPy (empty cheatsheet, learns during test)  
**Result**: 42.7% (279/654)  
**vs DSPy Baseline**: **-4.2%** (46.9% → 42.7%)

### Format Breakdown

| Format | Accuracy | Correct/Total | vs DSPy Baseline |
|--------|----------|---------------|------------------|
| **Int** | 44.1% | 67/152 | ✅ Equal |
| **Float** | 41.7% | 40/96 | ❌ -13.5% |
| **List** | 36.4% | 32/88 | ❌ +3.4% |
| **Str** | 24.2% | 51/211 | ❌ -12.3% |

**Key Findings**:
- DC performs comparably to DSPy on Int type
- DC significantly lags on Str and Float types
- Test-time learning insufficient to match DSPy optimization

---

## Test 3: Test Set Bootstrap (654 Questions) - Corrected

**Purpose**: Test advantage of pre-seeded cheatsheet from dev set  
**Result**: 43.7% (286/654)  
**vs Test 2 (Cold)**: **+1.0%** (42.7% → 43.7%)  
**vs DSPy Baseline**: **-3.2%** (46.9% → 43.7%)

### Format Breakdown

| Format | Accuracy | Correct/Total | vs Cold Start | vs DSPy Baseline |
|--------|----------|---------------|---------------|------------------|
| **Int** | 46.1% | 70/152 | +2.0% | ✅ +2.0% |
| **Float** | 43.8% | 42/96 | +2.1% | ❌ -11.4% |
| **List** | 36.4% | 32/88 | Equal | ❌ +3.4% |
| **Str** | 24.6% | 52/211 | +0.4% | ❌ -11.9% |

**Key Findings**:
- Bootstrap provides **+1.0%** overall improvement
- Improvements in Int (+2.0%) and Float (+2.1%)
- Still underperforms DSPy Baseline across most formats

---

## Cheatsheet Analysis

### Dev Set Cheatsheet (After 93 Questions)

**Size**: ~3,500 characters  
**Key insights learned**:
- ESG terminology (Scope 1/2/3, GHG protocols)
- Calculation patterns (percentages, ratios)
- Document structure (tables, headers)
- Format-specific extraction tips

**Location**: `results/dc_experiments/dev_cheatsheet_20251101.txt`

### Test Cold Cheatsheet Evolution

**Initial**: Empty  
**After 654 questions**: ~8,200 characters  
**Growth**: Accumulated patterns from all test questions

**Observation**: Continuous learning during test, but still lags optimized DSPy prompts.

### Test Bootstrap Cheatsheet Evolution

**Initial**: Pre-seeded with dev cheatsheet (~3,500 chars)  
**After 654 questions**: ~9,100 characters  
**Impact**: Marginal improvement (+1.0%) over cold start

**Conclusion**: Pre-seeding helps slightly, but DSPy's offline optimization more effective.

---

## Key Insights

### 1. DSPy Optimization > Test-Time Learning

**Evidence**:
- DSPy GEPA (dev): **61.3%** vs DC-Cold: 44.1% (**+17.2%**)
- DSPy MIPROv2 (test): **47.4%** vs DC-Cold: 42.7% (**+4.7%**)

**Implication**: Proper prompt optimization using train/dev data more effective than learning during inference.

### 2. Bootstrap Provides Minimal Benefit

**Test Cold**: 42.7%  
**Test Bootstrap**: 43.7% (+1.0%)

**Implication**: Pre-seeded cheatsheet helps marginally, but doesn't close gap with DSPy.

### 3. Format-Specific Struggles

**DC weaknesses**:
- **Str**: 24.2% vs DSPy Baseline 36.5% (-12.3%)
- **Float**: 41.7% vs DSPy Baseline 55.2% (-13.5%)

**Implication**: DC's generic cheatsheet less effective than DSPy's format-specific optimization.

### 4. Evaluation Methodology Critical

**Original assumption**: DC underperforms due to null handling (0% on null).

**Truth**: Evaluation bug affected ALL approaches. When corrected:
- DC improved (+7-9%)
- DSPy also improved (+1-6%)
- **DSPy still outperforms DC**

**Lesson**: Always validate evaluators before drawing conclusions.

---

## Comparison with DSPy Approaches (All Corrected)

### Dev Set (93 Questions)

| Rank | Approach | Accuracy | Change |
|------|----------|----------|--------|
| 🥇 | DSPy GEPA | **61.3%** | **+7.5% vs Baseline** |
| 🥈 | DSPy Baseline | **53.8%** | baseline |
| 🥉 | DSPy MIPROv2 | **52.7%** | -1.1% |
| 4th | DC-Cold | **44.1%** | **-9.7%** ❌ |

### Test Set (654 Questions)

| Rank | Approach | Accuracy | Change |
|------|----------|----------|--------|
| 🥇 | DSPy Hybrid | **50.2%** | **+3.3%** |
| 🥈 | DSPy MIPROv2 | **47.4%** | **+0.5%** |
| 🥉 | DSPy Baseline | **46.9%** | baseline |
| 4th | DSPy GEPA | **46.3%** | -0.6% |
| 5th | DC-Bootstrap | **43.7%** | **-3.2%** ❌ |
| 6th | DC-Cold | **42.7%** | **-4.2%** ❌ |

**Conclusion**: DSPy approaches consistently outperform DC across both dev and test sets.

---

## Recommendation

### For Research

- **DSPy GEPA/MIPROv2 preferred** for ESG question answering
- Test-time learning (DC) interesting but less effective
- Offline optimization > Online learning for this task

### For Production

- **Hybrid format-based routing** with DSPy-optimized prompts (50.2%)
- Consider DC only if training data unavailable or continuous adaptation needed

### For Future Work

- Investigate why DC underperforms on Str/Float types
- Test DC on other domains where test-time adaptation more critical
- Explore hybrid approaches: DC + DSPy optimization

---

## Files & Artifacts

### Corrected Prediction Files (Nov 9, 2025)

**Dev Set**:
- `results/dev_set/baseline_dev_predictions_20251019_130401_anls_fixed.json` (53.8%)
- `results/dev_set/gepa_dev_predictions_20251019_130401_anls_fixed.json` (61.3%)
- `results/dev_set/miprov2_dev_predictions_20251019_130401_anls_fixed.json` (52.7%)
- `results/dc_experiments/dc_cumulative_cold_dev_20251101_153119_anls_fixed.json` (44.1%)

**Test Set**:
- `results/test_set/baseline_test_predictions_20251021_225632_anls_fixed.json` (46.9%)
- `results/test_set/gepa_test_predictions_20251021_225632_anls_fixed.json` (46.3%)
- `results/test_set/miprov2_test_predictions_20251021_225632_anls_fixed.json` (47.4%)
- `results/dc_experiments/dc_cumulative_cold_test_20251101_171723_anls_fixed.json` (42.7%)
- `results/dc_experiments/dc_cumulative_cold_test_20251101_172109_anls_fixed.json` (43.7%)

### Cheatsheets

- `results/dc_experiments/dev_cheatsheet_20251101.txt` (3,500 chars)
- `results/dc_experiments/test_cold_cheatsheet_20251101.txt` (8,200 chars)
- `results/dc_experiments/test_bootstrap_cheatsheet_20251101.txt` (9,100 chars)

### Re-Scoring Script

- `rescore_all_with_anls_fix.py` - Universal re-scoring tool for all predictions

---

## Test 4: DC-RS (Retrieval & Synthesis) - Dev Set

**Date**: November 10, 2025  
**Status**: ✅ COMPLETE  
**Duration**: 1 hour 7 minutes (93 questions)

### Configuration
- **Variant**: DC-RS (Retrieval & Synthesis)
- **Model**: qwen2.5-7b-instruct
- **Dataset**: Dev set (93 questions)
- **Mechanism**: Retrieves top-5 similar past Q&As, synthesizes custom cheatsheet per question

### Results

**Overall**: 44.1% (41/93) - **Identical to DC-CU!**

**Format Breakdown**:

| Format | Correct | Total | Accuracy | vs DC-CU | Insight |
|--------|---------|-------|----------|----------|---------|
| Float | 9 | 13 | 69.2% | ±0.0% | Same |
| Str | 15 | 34 | 44.1% | **+26.5%** | ✅ Much better! |
| Int | 8 | 19 | 42.1% | ±0.0% | Same |
| null | 5 | 14 | 35.7% | **-50.0%** | ❌ Much worse! |
| List | 4 | 13 | 30.8% | -15.4% | ❌ Worse |

### Key Findings

#### 1. **No Overall Benefit Despite 10x Cost**
- DC-RS = DC-CU in accuracy (44.1%)
- DC-RS is **10x slower**: ~43s vs ~4s per question
- Retrieval overhead not justified

#### 2. **Format-Specific Trade-offs**
- ✅ **Strings**: +26.5% improvement (17.6% → 44.1%)
  - Retrieval of similar Q&As helps text extraction
- ❌ **Null detection**: -50.0% degradation (85.7% → 35.7%)
  - Retrieval adds noise, confuses refusal detection
- ❌ **Lists**: -15.4% degradation (46.2% → 30.8%)

#### 3. **Why Gains/Losses Cancel Out**
- Gained: +9 String questions (from 6 → 15)
- Lost: -7 null questions (from 12 → 5)
- Lost: -2 List questions (from 6 → 4)
- **Net**: +9 - 7 - 2 = ±0 questions

#### 4. **Computational Analysis**
- **Memory**: ~437 KB (3 parallel lists: corpus, embeddings, outputs)
- **Time complexity**: O(N) per question (N = history size)
- **Slowdown**: Questions 1-20 (~20-30s), Questions 51-93 (~60-90s)

### Cost-Benefit Analysis

| Metric | DC-CU | DC-RS | Winner |
|--------|-------|-------|--------|
| Accuracy | 44.1% | 44.1% | **Tie** |
| Speed | ~4s/Q | ~43s/Q | **DC-CU (10x)** |
| Memory | ~50 KB | ~437 KB | **DC-CU** |
| String perf | 17.6% | 44.1% | **DC-RS (+26.5%)** |
| Null detect | 85.7% | 35.7% | **DC-CU (+50%)** |

### Recommendation

**❌ Do NOT use DC-RS** because:
1. Same overall accuracy as DC-CU
2. 10x slower (impractical for large datasets)
3. Worse null detection (critical for ESG QA)
4. String improvement doesn't justify cost

**Exception**: Only consider if dataset has mostly Str questions and few null questions.

### File
`results/dc_experiments/dc_v2_retrieval_synthesis_dev_20251110_233010.json`

---

## Conclusion

Dynamic Cheatsheet evaluation complete with corrected results. Key findings:

1. ✅ **DSPy optimization outperforms test-time learning** by 3-4%
2. ✅ **Hybrid approach remains best** (50.2%)
3. ✅ **Evaluation methodology critical** - bugs masked true performance
4. ❌ **DC-CU and DC-RS both underperform** - not viable as primary approaches
5. ❌ **DC-RS adds no value** - 10x slower with same accuracy as DC-CU

**Research contribution**: Demonstrates importance of offline prompt optimization vs. online learning for structured ESG question answering. DC-RS's retrieval mechanism doesn't improve accuracy despite significant computational overhead.
