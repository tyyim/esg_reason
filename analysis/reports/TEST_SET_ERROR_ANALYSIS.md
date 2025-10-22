# Test Set Error Analysis (654 Questions)

**Date**: October 22, 2025  
**Dataset**: Test set (70% of 933 questions)  
**Model**: qwen2.5-7b-instruct  
**Evaluation**: ANLS 0.5 threshold

---

## Executive Summary

### ⚠️ CRITICAL FINDING: GEPA Does NOT Generalize

**Dev Set (93 questions)**:
- Baseline: 52.7% (49/93)
- GEPA: 54.8% (51/93) → **+2.2% improvement** ✅

**Test Set (654 questions)**:
- Baseline: 47.4% (310/654)
- GEPA: 45.7% (299/654) → **-1.7% degradation** ❌

**Performance Reversal**: +2.2% → -1.7% = **-3.9% swing!**

### Key Insight

The dev set results were **misleading**. GEPA's apparent improvement on 93 questions did not hold when validated on 654 questions. This suggests:

1. **Small sample size noise**: 93 questions too small for reliable conclusions (1 question = 1.1%)
2. **Overfitting to dev set**: GEPA optimization may have overfit to specific dev set patterns
3. **Dev set not representative**: Dev set distribution differs from test set

---

## Overall Performance Comparison

| Approach | Dev Set (93) | Test Set (654) | Consistency |
|----------|--------------|----------------|-------------|
| **Baseline** | 52.7% (49/93) | 47.4% (310/654) | ✅ Stable |
| **MIPROv2** | 48.4% (45/93) | 47.6% (311/654) | ✅ Stable |
| **GEPA** | 54.8% (51/93) | 45.7% (299/654) | ❌ **Reversal** |

### Relative to Baseline

| Approach | Dev Set | Test Set | Trend |
|----------|---------|----------|-------|
| **MIPROv2** | -4.3% | +0.2% | Slight improvement on larger set |
| **GEPA** | **+2.2%** | **-1.7%** | ❌ **Complete reversal** |

---

## Performance by Answer Format

### Test Set Results

| Format | Total | Baseline | MIPROv2 | GEPA | GEPA vs Base |
|--------|-------|----------|---------|------|--------------|
| **Int** | 152 (23%) | 44.1% | 50.7% | 44.7% | **+0.7%** ✅ |
| **Float** | 96 (15%) | 55.2% | 56.2% | 55.2% | **+0.0%** ➖ |
| **Str** | 211 (32%) | 37.9% | 41.2% | 36.5% | **-1.4%** ❌ |
| **List** | 88 (13%) | 33.0% | 28.4% | 27.3% | **-5.7%** ❌ |
| **null** | 107 (16%) | 75.7% | 63.6% | 72.0% | **-3.7%** ❌ |

### Dev vs Test Comparison

| Format | Dev Baseline | Dev GEPA | Dev Δ | Test Baseline | Test GEPA | Test Δ | Trend |
|--------|--------------|----------|-------|---------------|-----------|--------|-------|
| **Int** | 63.2% | 73.7% | **+10.5%** | 44.1% | 44.7% | **+0.7%** | ✅ Consistent gain (but much weaker) |
| **Float** | 69.2% | 76.9% | **+7.7%** | 55.2% | 55.2% | **+0.0%** | ➖ Mixed (gain disappeared) |
| **Str** | 35.3% | 29.4% | **-5.9%** | 37.9% | 36.5% | **-1.4%** | ⚠️  Consistent loss (reduced) |
| **List** | 23.1% | 38.5% | **+15.4%** | 33.0% | 27.3% | **-5.7%** | ❌ **Gain → Loss** (major reversal!) |
| **null** | 92.9% | 85.7% | **-7.2%** | 75.7% | 72.0% | **-3.7%** | ⚠️  Consistent loss (reduced) |

### Critical Observations

1. **Int gains evaporated**: +10.5% → +0.7% (dev to test)
2. **Float gains vanished**: +7.7% → 0.0% (dev to test)
3. **List performance reversed**: +15.4% → -5.7% (dev to test) **⚠️ MAJOR CONCERN**
4. **Str losses persisted**: -5.9% → -1.4% (actually improved slightly, but still negative)
5. **null losses persisted**: -7.2% → -3.7% (improved, but still negative)

---

## GEPA Degradation Analysis

### Net Impact by Format

| Format | Degraded (Base→GEPA wrong) | Improved (Base→GEPA right) | Net | Primary Issue |
|--------|----------------------------|----------------------------|-----|---------------|
| **Int** | 6 | 7 | **+1** | Minimal impact |
| **Float** | 6 | 6 | **0** | No net impact |
| **Str** | 20 | 17 | **-3** | Verbosity |
| **List** | 7 | 2 | **-5** | ❌ **Format extraction failure** |
| **null** | 13 | 9 | **-4** | Hallucination |
| **Total** | 52 | 41 | **-11** | Net degradation |

---

## Root Cause Analysis

### 1. String Questions (32% of test set, 211/654)

**Performance**:
- Baseline: 80/211 (37.9%)
- GEPA: 77/211 (36.5%)
- Net impact: **-3 questions**

**Issue**: Verbose 7,749-character prompt

**Sample Degradations**:

**Example 1 (q94)**: 
- Question: "What approach do governments need to adopt to improve innovation outcomes..."
- Ground truth: `Mission-oriented approach`
- Baseline: `mission-oriented approach` ✅
- GEPA: `Mission-oriented` ❌
- **Issue**: Partial answer, missing "approach"

**Example 2 (q97)**:
- Question: "Which iterative cycle model does ISO 14001 base its management approach on?"
- Ground truth: `Plan-Do-Check-Act (PDCA)`
- Baseline: `Plan-Do-Check-Act` ✅
- GEPA: `PDCA` ❌
- **Issue**: Abbreviation instead of full form

**Example 3 (q191)**:
- Question: "Which metric specifically discloses the percentage of student data breaches..."
- Ground truth: `SV-ED-230a.3`
- Baseline: `SV-ED-230a.3` ✅
- GEPA: `percentage` ❌
- **Issue**: Completely wrong extraction

**Pattern**: GEPA's verbose prompt (7,749 chars) confuses text extraction, leading to:
- Incomplete answers
- Abbreviations instead of full forms
- Wrong extractions

---

### 2. List Questions (13% of test set, 88/654)

**Performance**:
- Baseline: 29/88 (33.0%)
- GEPA: 24/88 (27.3%)
- Net impact: **-5 questions**

**⚠️ MAJOR CONCERN**: Dev set showed **+15.4% improvement**, test set shows **-5.7% degradation**!

**Issue**: GEPA's list extraction optimized for dev set patterns that don't generalize.

**Hypothesis**: 
- Dev set list questions (13 total) had specific patterns that GEPA learned
- Test set list questions (88 total) have different patterns
- GEPA's structured examples in prompts overfitted to dev set

---

### 3. Null/Not Answerable (16% of test set, 107/654)

**Performance**:
- Baseline: 81/107 (75.7%)
- GEPA: 77/107 (72.0%)
- Net impact: **-4 questions**

**Issue**: GEPA tries too hard to answer, leading to hallucinations.

**Pattern**: Consistent with dev set (-7.2%), but magnitude reduced on test set (-3.7%).

---

### 4. Integer Questions (23% of test set, 152/654)

**Performance**:
- Baseline: 67/152 (44.1%)
- GEPA: 68/152 (44.7%)
- Net impact: **+1 question**

**Dev set showed +10.5% improvement, test set only +0.7%**.

**Conclusion**: Dev set gains did not generalize. The apparent strong performance on integers was sample size noise.

---

### 5. Float Questions (15% of test set, 96/654)

**Performance**:
- Baseline: 53/96 (55.2%)
- GEPA: 53/96 (55.2%)
- Net impact: **0 questions**

**Dev set showed +7.7% improvement, test set shows 0% change**.

**Conclusion**: Float performance gains completely vanished on larger dataset.

---

## Question Patterns

| Pattern | Count | Percentage |
|---------|-------|------------|
| All 3 correct | 230 | 35.2% |
| All 3 wrong | 270 | 41.3% |
| MIPROv2 only correct | 33 | 5.0% |
| GEPA only correct | 23 | 3.5% |

**Key Insight**: MIPROv2 has more unique wins than GEPA (33 vs 23), despite lower overall accuracy. This suggests MIPROv2's approach has some strengths that GEPA lacks.

---

## Statistical Significance

### Sample Size Analysis

**Dev Set (93 questions)**:
- 1 question = 1.1% accuracy change
- GEPA improvement: +2 questions (+2.2%)
- Margin of error: Very high
- Confidence: Low

**Test Set (654 questions)**:
- 1 question = 0.15% accuracy change  
- GEPA degradation: -11 questions (-1.7%)
- Margin of error: Much smaller
- Confidence: High

**Conclusion**: Test set results are **much more reliable** than dev set due to larger sample size.

---

## Why Did GEPA Fail?

### Hypothesis 1: Overfitting to Dev Set
- GEPA optimized on 186 training questions + 93 dev questions
- Total: 279 questions (30% of dataset)
- Learned patterns specific to these 279 questions
- Did not generalize to remaining 654 test questions

### Hypothesis 2: Prompt Over-Engineering
- GEPA prompt: **7,749 characters** (very long!)
- Baseline prompt: 0 characters (DSPy default)
- Long prompts help on some formats (Int/Float on dev set)
- Long prompts hurt on others (Str/null/List)
- Net effect on test set: Negative

### Hypothesis 3: Dev Set Not Representative
- Dev set may have had easier or different patterns
- Baseline: 52.7% dev vs 47.4% test (-5.3%)
- GEPA: 54.8% dev vs 45.7% test (-9.1%)
- **GEPA degraded more** than baseline when moving to test set

### Hypothesis 4: Small Model Limitations
- qwen2.5-7b-instruct may struggle with 7,749-char prompts
- Attention dilution across very long context
- Larger models (14B, 32B) might handle GEPA better

---

## Recommendations

### 1. ⚠️ DO NOT Deploy GEPA (Current Version)
- Test set shows **-1.7% degradation** vs baseline
- Dev set results were misleading due to small sample size
- GEPA is **not ready for production**

### 2. Investigate Why List Performance Reversed
- Dev set: +15.4% (biggest gain)
- Test set: -5.7% (major loss)
- This is a **-21.1% swing** - needs deep investigation
- Analyze specific list questions that failed

### 3. GEPA-v2 Development Strategy

**Option A: Prompt Compression**
- Reduce from 7,749 → <3,000 chars
- Keep only essential instructions
- Remove dev-set-specific examples
- Validate on test set FIRST

**Option B: Format-Specific GEPA**
- Train separate GEPA for each format
- Int-GEPA, Float-GEPA, Str-GEPA, List-GEPA, null-GEPA
- Each optimized for specific extraction pattern
- Higher overhead but potentially better performance

**Option C: Hybrid Approach**
- Use baseline for all formats (safest)
- OR use MIPROv2 (slightly better than baseline on test set: +0.2%)
- Abandon GEPA optimization for this task

### 4. Try Larger Student Models
- qwen2.5-14b-instruct (still affordable, 100x cheaper than qwen-max)
- qwen2.5-32b-instruct (if budget allows)
- Larger models handle long prompts better
- May reduce attention dilution issues

### 5. Statistical Validation Process
**Before claiming ANY optimization improvement**:
- ✅ Validate on test set (not just dev set)
- ✅ Minimum 500+ questions for reliable conclusions
- ✅ McNemar's test for paired accuracy (p < 0.05)
- ✅ Bootstrap confidence intervals
- ✅ Format-specific validation

---

## Lessons Learned

### 1. Small Dev Sets Are Unreliable
- 93 questions too small for optimization validation
- Need minimum 500+ questions for confident conclusions
- Dev set should be used for quick iteration only
- **Always validate on large hold-out test set**

### 2. Prompt Optimization Can Hurt
- Longer prompts ≠ better performance
- GEPA's 7,749-char prompt helped on dev set, hurt on test set
- Optimization can overfit to specific patterns
- Simpler often better (baseline performed better!)

### 3. Format-Specific Analysis Essential
- Overall accuracy masks format-specific patterns
- GEPA's list reversal (+15.4% → -5.7%) hidden in overall numbers
- Need separate validation for each answer type

### 4. Reflection vs Teacher-Student Inconclusive
- Dev set: GEPA (+2.2%) > MIPROv2 (-4.3%)
- Test set: MIPROv2 (+0.2%) > GEPA (-1.7%)
- **Test set shows MIPROv2 is actually better!**
- Original research conclusion was wrong

---

## Updated Research Findings

### Original Claim (Based on Dev Set)
> "GEPA outperforms MIPROv2 by 6.4% on small models. Reflection-based optimization is superior to teacher-student for 7B models."

### Corrected Claim (Based on Test Set)
> "MIPROv2 marginally outperforms GEPA on test set (+0.2% vs -1.7% relative to baseline). Neither optimization approach provides reliable improvement over baseline for qwen2.5-7b-instruct on this ESG QA task. Baseline is the safest choice for production deployment."

---

## Next Steps

1. **Analyze List Question Failures** (highest priority)
   - Why did +15.4% become -5.7%?
   - What patterns in dev list questions don't generalize?
   - Can we recover list performance?

2. **Try MIPROv2 as Default** (if any optimization needed)
   - Test set: +0.2% (small but positive)
   - More stable across formats than GEPA
   - Less overfitting risk

3. **Larger Model Experiments**
   - qwen2.5-14b-instruct
   - qwen2.5-32b-instruct  
   - Test if GEPA works better with larger context windows

4. **Abandon GEPA for This Task** (realistic option)
   - Baseline: 47.4%
   - GEPA: 45.7%
   - Cost of optimization not justified
   - Use baseline or try fine-tuning instead

---

## Publication Impact

### Original Paper Outline (Based on Dev Set)
**Title**: "When Reflection Beats Teacher-Student: Efficient Prompt Optimization for Small Language Models"

**Claim**: GEPA > MIPROv2 by 6.4% on 7B models

### Revised Reality (Based on Test Set)
**Cannot publish original claims** - test set contradicts dev set findings.

**New potential paper** (if we pivot):
**Title**: "Why Small Dev Sets Mislead: Lessons from ESG Question Answering Optimization"

**Contributions**:
1. Case study of dev/test set divergence (+2.2% → -1.7%)
2. Format-specific overfitting analysis (List: +15.4% → -5.7%)
3. Statistical validation requirements for prompt optimization
4. Baseline often beats over-optimized prompts

---

**Last Updated**: October 22, 2025  
**Status**: Test set validation complete, GEPA optimization failed

