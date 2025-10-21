# Dev Set Error Analysis: Baseline vs MIPROv2 vs GEPA

**Date**: October 19, 2025
**Evaluation**: Complete fresh evaluation on 93 dev questions
**Model**: qwen2.5-7b-instruct (all three approaches)

---

## 🎯 Executive Summary

### MAJOR DISCOVERY: Previous Baseline Was WRONG!

**❌ Old Baseline** (stated in logs): 58.1% (54/93)
**✅ TRUE Baseline** (fresh evaluation): **52.7% (49/93)**

**Impact**: The "baseline" we were comparing against was inflated by ~5.4%. This explains the confusion!

### Corrected Results

| Approach  | Accuracy | Correct | Change vs Baseline |
|-----------|----------|---------|-------------------|
| **Baseline** | **52.7%** | 49/93 | **baseline** |
| **MIPROv2** | 48.4% | 45/93 | **-4.3%** ❌ |
| **GEPA** | **54.8%** | 51/93 | **+2.2%** ✅ |

**KEY FINDING**: **GEPA actually IMPROVED performance by 2.2%!**

---

## 📊 Detailed Performance Breakdown

### Overall Metrics

| Metric | Baseline | MIPROv2 | GEPA |
|--------|----------|---------|------|
| **Correct** | 49 | 45 | **51** |
| **Wrong** | 44 | 48 | 42 |
| **Accuracy** | 52.7% | 48.4% | **54.8%** |

### Question Patterns

| Pattern | Count | Description |
|---------|-------|-------------|
| All 3 Correct | 36 | Easy questions all approaches solved |
| All 3 Wrong | 33 | Hard questions none solved |
| Baseline Only | 6 | Baseline solved, optimizers didn't |
| GEPA Only | 2 | Only GEPA solved |
| MIPROv2 Only | 0 | None unique to MIPROv2 |

### Degradations & Improvements

**MIPROv2**:
- ❌ Degradations: 11 questions (baseline right → MIPROv2 wrong)
- ✅ Improvements: 7 questions (baseline wrong → MIPROv2 right)
- **Net**: -4 questions

**GEPA**:
- ❌ Degradations: 7 questions (baseline right → GEPA wrong)
- ✅ Improvements: 9 questions (baseline wrong → GEPA right)
- **Net**: +2 questions ✅

---

## 🔬 Performance by Answer Format

| Format | Total | Baseline | MIPROv2 | GEPA | GEPA Advantage |
|--------|-------|----------|---------|------|----------------|
| **Float** | 13 | 69.2% | 76.9% | **76.9%** | +7.7% |
| **Int** | 19 | 63.2% | 52.6% | **73.7%** | **+10.5%** ✅ |
| **List** | 13 | 23.1% | 38.5% | **38.5%** | +15.4% |
| **Str** | 34 | 35.3% | 29.4% | 29.4% | -5.9% |
| **null** | 14 | **92.9%** | 71.4% | 85.7% | -7.2% |

### Key Insights by Format

1. **Int (Integers)**: GEPA's biggest win (+10.5% vs baseline)
   - GEPA correctly extracts numeric answers
   - Domain knowledge examples helped (SA8000 clauses, percentages)

2. **List**: Both optimizers improve significantly (+15.4%)
   - Structured extraction prompts help
   - GEPA and MIPROv2 tied at 38.5%

3. **Str (String)**: Both optimizers hurt performance (-5.9%)
   - Long verbose prompts may confuse on text extraction
   - Baseline's simpler approach works better

4. **null (Not answerable)**: Baseline best (92.9%)
   - Baseline correctly identifies unanswerable questions
   - Optimizers over-think and hallucinate answers

5. **Float**: Both optimizers improve (+7.7%)
   - Precision-focused prompts help numeric extraction

---

## ✅ What GEPA Did Well

### 1. **Integer Extraction** (+10.5% vs baseline)

**Example Improvements**:
- SA8000 clause numbers (8.1, 8.4)
- Percentage calculations
- Count-based answers

**Why it worked**:
- GEPA's domain knowledge included SA8000 examples
- Explicit instructions about numeric precision
- Examples showed exact integer extraction patterns

### 2. **Float Extraction** (+7.7% vs baseline)

**Why it worked**:
- Instructions emphasized "precision is required"
- Examples showed decimal places matter
- Unit awareness (percentages, ratios)

### 3. **List Extraction** (+15.4% vs baseline)

**Why it worked**:
- Structured output format in examples
- Clear List type distinction
- Examples showed multi-item extraction

### 4. **Domain-Specific Questions**

GEPA's hard-coded examples helped on:
- SA8000 compliance questions
- Chief Sustainability Officer responsibilities
- STEM graduate statistics

**Evidence**: GEPA improved 9 questions, many related to these domains

### 5. **Better than MIPROv2** (+6.4% absolute)

GEPA outperformed MIPROv2 across most formats:
- Int: 73.7% vs 52.6% (MIPROv2 actually hurt!)
- null: 85.7% vs 71.4%
- Same on Float and List

---

## ❌ What GEPA Did Wrong

### 1. **String Extraction** (-5.9% vs baseline)

**Problem**: Over-specification hurts text answers
- Long prompts add noise for simple string extraction
- Baseline's "just extract the answer" works better
- GEPA's examples don't cover diverse string patterns

**Examples of degradation**:
- Company names
- Policy descriptions
- Qualitative answers

### 2. **"Not Answerable" Detection** (-7.2% vs baseline)

**Problem**: GEPA tries too hard to answer
- Baseline: 92.9% correctly says "Not answerable"
- GEPA: 85.7% (hallucinates answers 7.2% more)

**Why**:
- Long prompt encourages extracting something
- Examples show successful extractions, not refusals
- "Be precise" instruction pressures model to guess

### 3. **Degraded 7 Questions** vs Baseline

While GEPA improved 9, it also degraded 7 questions baseline got right.

**Degradation patterns**:
- Over-specific domain knowledge biases other questions
- Verbose prompt confuses on edge cases
- Format-specific instructions too rigid

### 4. **Prompt Length Issues**

**GEPA Reasoning Prompt**: 7,749 characters
**Baseline Reasoning Prompt**: 0 characters (DSPy default)

**Problem**:
- 7B model may struggle with 7,749-char prompts
- Attention dilution across long context
- More tokens = more chances for error

---

## 🎯 Recommendations

### Immediate Actions

1. **✅ GEPA is Better than MIPROv2**
   - Use GEPA as new baseline for future work
   - 54.8% is new performance target to beat

2. **🔄 Optimize GEPA Further**
   - Reduce prompt length (target <3,000 chars)
   - Remove hard-coded domain examples
   - Use few-shot learning instead of inline examples

3. **📝 Focus on Weak Areas**
   - String extraction: simplify instructions
   - "Not answerable": add negative examples
   - null format: teach refusal better

### Future Optimization Strategies

1. **Hybrid Approach**:
   - Use GEPA for Int/Float/List (strong)
   - Use Baseline for Str/null (strong)
   - Format-specific prompts

2. **Larger Student Model**:
   - Try qwen2.5-14b-instruct or qwen2.5-32b-instruct
   - Larger models handle longer prompts better
   - May capture GEPA's complexity better

3. **Iterative Validation**:
   - Validate each GEPA iteration on dev set
   - Stop if degradation occurs
   - Use early stopping

4. **Prompt Compression**:
   - Keep successful patterns (Int/Float/List instructions)
   - Remove verbose examples
   - Use DSPy's BootstrapFewShot for dynamic examples

---

## 📈 Next Steps

1. **✅ Update Notion** with correct baseline (52.7%)
2. **✅ Archive old confusing results**
3. **🔄 Run on Test Set** (654 questions)
   - Validate GEPA's 54.8% holds
   - Get final comparison
4. **🔬 Investigate String Degradation**
   - Analyze the 7 degraded questions
   - Identify common patterns
5. **🧪 Try GEPA-v2**
   - Shorter prompts
   - Format-specific optimization
   - Larger student model

---

## 📊 Statistical Significance

**Sample Size**: 93 questions (dev set)
**GEPA Improvement**: +2 questions (+2.2%)

**Is this significant?**
- Small sample size (93 questions)
- Improvement: 2 questions
- **Need test set validation** (654 questions) for confidence

**Test Set Projection**:
- If 2.2% holds: 654 × 0.022 = ~14 more questions
- Current baseline: ~345 questions (52.7%)
- GEPA target: ~359 questions (54.9%)

---

**Conclusion**: GEPA shows promising improvements, especially on structured formats (Int, Float, List). However, it degrades on string extraction and "not answerable" detection. With refinement (shorter prompts, better examples), GEPA has potential for further gains.
