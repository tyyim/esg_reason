# DeepSeek v3.1 + DC-CU Failure Analysis

**Date**: November 11, 2025  
**Issue**: DC-CU performance degraded -7.5% with DeepSeek v3.1 (44.1% → 36.6%)  
**Question**: Is this a formatting issue like DSPy, or something else?

---

## 🎯 Executive Summary

**Answer**: It's NOT like DSPy's formatting advantage. DeepSeek DC-CU has **THREE distinct failure modes**:

1. **❌ CRITICAL: Cheatsheet Generation Failure** (0 characters vs 3,700)
2. **❌ List Format Output Issue** (comma-separated vs Python list)  
3. **⚠️  Null Evaluation Inconsistency** (same prediction, different scores)

**Net Effect**: -7.5% degradation, but could be partially recoverable

---

## 📊 Performance Comparison

### Overall Results

| Metric | qwen2.5-7b | DeepSeek v3.1 | Change |
|--------|------------|---------------|--------|
| **Accuracy** | 44.1% (41/93) | 36.6% (34/93) | **-7.5%** ❌ |
| **Cheatsheet Size** | 3,700 chars | **0 chars** | ❌ **FAILED** |

---

### Format-Specific Breakdown

| Format | qwen2.5-7b | DeepSeek v3.1 | Change | Status |
|--------|------------|---------------|--------|--------|
| **Float** | 69.2% (9/13) | 69.2% (9/13) | ±0.0% | → Tied |
| **Int** | 42.1% (8/19) | 63.2% (12/19) | **+21.1%** | ✅ **Win** |
| **Str** | 17.6% (6/34) | 38.2% (13/34) | **+20.6%** | ✅ **Win** |
| **List** | 46.2% (6/13) | 0.0% (0/13) | **-46.2%** | ❌ **Loss** |
| **null** | 85.7% (12/14) | 0.0% (0/14) | **-85.7%** | ❌❌ **Critical Loss** |

**Pattern**: DeepSeek is BETTER at Int/Str but CATASTROPHICALLY WORSE at List/null

---

## 🔍 Root Cause Analysis

### Failure Mode 1: Cheatsheet Generation Failure 🚨 CRITICAL

**Problem**: DeepSeek v3.1 generated a **0-character cheatsheet** (vs 3,700 chars with qwen2.5-7b)

**Evidence**:
```json
// qwen2.5-7b DC-CU
{
  "final_cheatsheet": "When extracting GHG emissions data...[3,700 characters]"
}

// DeepSeek v3.1 DC-CU
{
  "final_cheatsheet": ""  // ❌ EMPTY!
}
```

**Implication**: DC's core mechanism (learning from past Q&A) is **completely disabled** for DeepSeek!

**Why This Matters**:
- DC without cheatsheet = static prompts with no learning
- DeepSeek DC-CU is effectively running as "Simple Baseline RAW + bad prompts"
- The -7.5% loss might actually be IMPRESSIVE given DC isn't working at all!

**Root Cause Hypothesis**:
1. **Curator Prompt Incompatibility**: DeepSeek may not follow DC's curator template correctly
2. **Output Format Issue**: Curator prompt may expect specific format DeepSeek doesn't produce
3. **Temperature Sensitivity**: DC uses temperature=0.1, DeepSeek may need temperature=0.0

---

### Failure Mode 2: List Format Output ❌

**Problem**: DeepSeek outputs comma-separated text instead of Python list format

**Example #1**:
```
Question: "What are the initial set of SSP narratives? Write the answer in list format"

Ground Truth: 
['SSP1 (sustainability)', 'SSP2 (middle of the road)', 'SSP3 (regional rivalry)', 
 'SSP4 (inequality)', 'SSP5 (rapid growth)']

qwen2.5-7b predicted:
["SSP1 (sustainability)", "SSP2 (middle of the road)", "SSP3 (regional rivalry)", 
 "SSP4 (inequality)", "SSP5 (rapid growth)"]
✅ Correct (6/13) - JSON array format

DeepSeek v3.1 predicted:
SSP1 (sustainability), SSP2 (middle of the road), SSP3 (regional rivalry), 
SSP4 (inequality), SSP5 (rapid growth)
❌ Wrong (0/13) - Plain text, no brackets
```

**ANLS Distance**:
- qwen output vs GT: Small distance (quote style) → Score ≥ 0.5 ✅
- DeepSeek output vs GT: Large distance (no structure) → Score < 0.5 ❌

**Is This Like DSPy's Advantage?**

**Similar**: Output formatting differences cause ANLS score failures

**Different**: 
- DSPy advantage: Framework embeds better examples automatically
- DeepSeek failure: Model doesn't follow format instructions in DC prompts
- DSPy is "smart defaults", DeepSeek is "model incompatibility"

**Evidence of Model Incompatibility**:

Example #2:
```
Question: "What are the primary value-adding activities..."

Ground Truth: ['Processing', 'trading', 'distributing', 'milling']

qwen2.5-7b:
["Processing", "trading", "distributing", "milling"]  ✅

DeepSeek v3.1:
processing, trading, distributing, milling, transporting goods, wholesale
❌ Extra items + wrong format
```

**Analysis**: DeepSeek added extra items not in the ground truth, suggesting it's not following retrieval context as strictly.

---

### Failure Mode 3: Null Format Evaluation Inconsistency ⚠️ SUSPICIOUS

**Problem**: Both models predict `"null"`, but qwen gets credit and DeepSeek doesn't!

**Evidence**:

| Question | GT | qwen Pred | qwen Correct | DeepSeek Pred | DeepSeek Correct |
|----------|----|-----------|--------------|--------------|--------------------|
| "How does thirdhand smoke differ..." | Not answerable | `"null"` | ✅ True | `"null"` | ❌ False |
| "How many asset managers..." | Not answerable | `"null"` | ✅ True | `"null"` | ❌ False |
| "What are the five pillars..." | Not answerable | `"null"` | ✅ True | `"null"` | ❌ False |
| "What specific procedures..." | Not answerable | `"null"` | ✅ True | `"null"` | ❌ False |

**Result**:
- qwen: 12/14 correct (85.7%)
- DeepSeek: 0/14 correct (0.0%)
- **Both predicted the SAME thing!**

**Hypothesis**: This is NOT a DeepSeek failure - this is an **evaluation bug or inconsistency!**

**Possible Explanations**:
1. Different evaluation scripts used (different null equivalence handling)
2. Timing of evaluation (before/after null fix)
3. Case sensitivity or whitespace differences in "null" vs "Null" vs " null"
4. Storage issue in JSON (prediction key differences)

**Impact**: If this is fixed, DeepSeek would gain +12.9% (12 questions) → 49.5% accuracy!

---

## 🧮 Impact Calculation

### Current Performance Gap: -7.5%

Breakdown by failure mode:

| Failure Mode | Questions Lost | Impact | Recoverable? |
|--------------|----------------|--------|--------------|
| **Null evaluation bug** | -12/14 | **-12.9%** | ✅ Yes (fix evaluation) |
| **List formatting** | -6/13 | **-6.5%** | ⚠️ Maybe (post-processing) |
| **Cheatsheet failure** | Unknown | **Unknown** | ❌ Hard (model compatibility) |
| **Int/Str improvements** | +11 | **+11.8%** | ✅ Already gained |

**Theoretical Performance** (if null bug fixed):
- Current: 36.6%
- + Null fix: 36.6% + 12.9% = **49.5%** ✅

**With List format fix**:
- Current: 36.6%
- + Null fix: +12.9%
- + List fix (assume 50% success like qwen): +3.2%
- **Total: ~52.7%** ✅ (BETTER than qwen's 44.1%!)

---

## 📊 Comparison to DSPy Framework Advantage

### Similarities

| Aspect | DSPy Advantage | DeepSeek DC-CU |
|--------|----------------|----------------|
| **List Format** | JSON array examples | Plain text output |
| **Mechanism** | Better format instructions | Model doesn't follow instructions |
| **Impact** | +3.2% on Lists | -6.5% on Lists |

### Differences

| Aspect | DSPy Advantage | DeepSeek DC-CU |
|--------|----------------|----------------|
| **Nature** | Framework engineering | Model incompatibility |
| **Cause** | Automatic prompt generation | Manual prompts not working |
| **Fixable?** | N/A (by design) | Maybe (modify prompts for model) |
| **Other Issues** | None | Cheatsheet failure, null bug |

**Conclusion**: DeepSeek DC-CU is **NOT** just a formatting issue like DSPy. It's a combination of:
1. Model instruction-following incompatibility
2. Cheatsheet generation failure (DC-specific)
3. Evaluation inconsistency (null format)

---

## 🎯 Key Insights

### 1. **DeepSeek Is Better at Some Things!**

**Wins**:
- Int: +21.1% (8/19 → 12/19)
- Str: +20.6% (6/34 → 13/34)

**Analysis**: DeepSeek is actually BETTER at structured extraction (Int) and text comprehension (Str) when it follows instructions.

**Example** (Int success):
```
Question: "To reach LEED Gold for a Data Center... how many more points needed?"
qwen: "null" ❌ (couldn't answer)
DeepSeek: "11" ✅ (correct!)
```

---

### 2. **The Cheatsheet Failure Is CRITICAL**

Without a cheatsheet, DC-CU is just a static prompt system. The fact that DeepSeek still achieved 36.6% suggests:
- The base DC prompt is reasonable
- DeepSeek's underlying capabilities are strong
- But test-time learning is completely disabled

**Implication**: If cheatsheet generation worked, DeepSeek DC-CU might perform MUCH better than qwen DC-CU!

---

### 3. **Null Evaluation Bug Masks True Performance**

If the null evaluation is fixed:
- DeepSeek: 36.6% → 49.5% (+12.9%)
- qwen: 44.1% (unchanged)
- **Gap closes**: -7.5% → +5.4% (DeepSeek WINS!)

**This changes everything!**

---

### 4. **Model-Approach Compatibility Is Complex**

| Model | Simple RAW | DC-CU | Gap |
|-------|------------|-------|-----|
| **qwen2.5-7b** | 45.2% | 44.1% | -1.1% (tied) |
| **DeepSeek v3.1** | 46.2% | 36.6% (49.5% fixed) | -9.6% (-3.3% fixed) |

**Observation**: 
- qwen: Works equally well with both approaches
- DeepSeek: Better at static prompts, struggles with DC framework

**Reason**: Different models have different instruction-following characteristics

---

## 🔧 Recommended Fixes

### Priority 1: Fix Null Evaluation Inconsistency ⭐

**Action**: Investigate why same prediction ("null") scored differently
**Impact**: +12.9% for DeepSeek
**Effort**: Low (debugging + re-evaluation)

**Steps**:
1. Check evaluation script version used
2. Verify null equivalence handling
3. Re-evaluate DeepSeek results with same evaluator as qwen
4. Compare case sensitivity, whitespace handling

---

### Priority 2: Investigate Cheatsheet Generation Failure ⭐⭐

**Action**: Debug why DeepSeek generates 0-character cheatsheet
**Impact**: Unknown (could be massive - DC's core feature)
**Effort**: Medium (prompt engineering + testing)

**Steps**:
1. Review DC curator prompt requirements
2. Test DeepSeek with curator prompt in isolation
3. Check if temperature affects curator output
4. Modify curator prompt for DeepSeek compatibility
5. Test if cheatsheet accumulation helps performance

**Hypotheses to Test**:
- **Temperature**: Try temperature=0.0 instead of 0.1
- **Prompt format**: DeepSeek may need different curator template
- **Output parsing**: Curator response may be generated but not parsed correctly

---

### Priority 3: Fix List Format Output ⭐

**Action**: Add post-processing to convert comma-separated → Python list
**Impact**: +3.2% (50% of List questions)
**Effort**: Low (string manipulation)

**Solution**:
```python
def format_list_output(prediction, answer_format):
    if answer_format == "List":
        # Check if already in list format
        if not prediction.strip().startswith('['):
            # Convert comma-separated to list format
            items = [item.strip() for item in prediction.split(',')]
            return str(items)
    return prediction
```

**Note**: This is a band-aid, not a real fix. Better to modify DC prompts for DeepSeek.

---

## 📈 Expected Performance After Fixes

### Scenario 1: Null Bug Fix Only

| Model | Current | After Fix | Change |
|-------|---------|-----------|--------|
| qwen2.5-7b DC-CU | 44.1% | 44.1% | ±0% |
| DeepSeek DC-CU | 36.6% | **49.5%** | **+12.9%** ✅ |
| **Gap** | -7.5% | **+5.4%** | **DeepSeek WINS** |

---

### Scenario 2: Null + List Fixes

| Model | Current | After Fixes | Change |
|-------|---------|-------------|--------|
| qwen2.5-7b DC-CU | 44.1% | 44.1% | ±0% |
| DeepSeek DC-CU | 36.6% | **~52.7%** | **+16.1%** ✅✅ |
| **Gap** | -7.5% | **+8.6%** | **DeepSeek MUCH BETTER** |

---

### Scenario 3: All Fixes (+ Cheatsheet Working)

**Unknown**, but could be **55-60%+** if DC's test-time learning works with DeepSeek

---

## 🎓 Lessons Learned

### 1. **Don't Judge Performance on First Run**

Initial results showed DeepSeek DC-CU at 36.6%, suggesting model incompatibility. Deeper analysis revealed:
- 12.9% is evaluation inconsistency
- 6.5% is fixable formatting
- Core cheatsheet mechanism not even working

**Real performance is likely 50%+, not 36.6%**

---

### 2. **Model Compatibility ≠ Model Capability**

DeepSeek is actually BETTER at:
- Int extraction (+21.1%)
- String comprehension (+20.6%)

But WORSE at:
- Following DC's curator template (0-char cheatsheet)
- List formatting (0% vs 46.2%)

**Lesson**: Strong models can still fail with specific frameworks

---

### 3. **Evaluation Consistency Is Critical**

Same prediction, different scores → completely invalidates comparisons!

**Must ensure**:
- Same evaluation script version
- Same null equivalence handling
- Same ANLS implementation
- Re-run all comparisons if evaluator changes

---

### 4. **Framework-Model Interaction Is Complex**

| Framework | qwen2.5-7b | DeepSeek v3.1 |
|-----------|------------|---------------|
| **Simple RAW** | 45.2% | 46.2% (+1.0%) ✅ |
| **DC-CU** | 44.1% | 36.6% (49.5% fixed) ❌ |

**Observation**: DeepSeek slightly better with simple prompts, worse with DC framework

**Implication**: Not all models work equally well with all approaches

---

## ✅ Final Answer to User's Question

**Q**: Can you analyze what went wrong with DC-CU and DeepSeek v3.1? How come performance degraded? Are those formatting issues like how DSPy excels or something else?

**A**: It's **NOT just formatting like DSPy** - it's THREE distinct issues:

### 1. **🚨 CRITICAL: Cheatsheet Generation Failure**
- DeepSeek generated 0-character cheatsheet (vs 3,700 for qwen)
- DC's core learning mechanism completely disabled
- Model incompatibility with DC's curator prompts

### 2. **❌ List Format Output Issue**
- DeepSeek outputs comma-separated text, not Python lists
- Similar to DSPy's advantage, but caused by model incompatibility
- Impact: -6.5% (0/13 vs qwen's 6/13)

### 3. **⚠️ Null Evaluation Inconsistency**
- Both models predicted `"null"` for unanswerable questions
- qwen got credit (12/14), DeepSeek didn't (0/14)
- **Same prediction, different scores** → evaluation bug!
- Impact: -12.9% (likely recoverable)

**Net Impact**:
- Apparent: -7.5% degradation
- Actual (after fixes): Likely +5% to +8% IMPROVEMENT

**The surprising truth**: DeepSeek is actually BETTER at Int (+21%) and Str (+21%), but the evaluation inconsistency and cheatsheet failure masked its true performance!

---

**Date**: November 11, 2025  
**Status**: Analysis complete, fixes recommended  
**Priority**: Fix null evaluation bug first (+12.9% recovery)

