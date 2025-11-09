# DC-RS Implementation Notes

**Date**: November 9, 2025  
**Status**: Ready for testing

---

## Summary

Implemented DC-Retrieval & Synthesis (DC-RS) variant using **original DC code directly** from https://github.com/suzgunmirac/dynamic-cheatsheet

### Key Changes

#### 1. Added DashScope Model Support to DC's Original Code

**File**: `dc_repo/dynamic_cheatsheet/language_model.py`  
**Lines**: 51-58  
**Change**: Added DashScope models to supported model list

```python
# Add these models to the list at lines 28-59:
"dashscope/qwen-max",
"dashscope/qwen-plus",
"dashscope/qwen-turbo",
"dashscope/qwen2.5-7b-instruct",
"dashscope/qwen2.5-14b-instruct",
"dashscope/qwen2.5-32b-instruct",
"dashscope/qwen2.5-72b-instruct",
```

**Why**: Allows using our DashScope API keys with DC's original implementation

---

#### 2. Fixed ANLS String Evaluation Bug

**File**: `src/evaluation_utils.py`  
**Lines**: 96-116  
**Issue**: MMESGBench's `eval_score()` has a bug in Str type evaluation (line 221 of `MMESGBench/src/eval/eval_score.py`)

**Bug Details**:
```python
# Original bug (line 221):
score = anls_compute(gt, pred)  # ❌ Passes string instead of list

# But anls_compute signature (line 33):
def anls_compute(ground_truth_answers, predicted_answer, threshold=0.5):
    for gt_answer in ground_truth_answers:  # Expects LIST
        # When passed string, iterates character-by-character!
```

**Fix**: Wrap `gt` in a list before calling `anls_compute([gt], pred)`

**Impact**: This bug caused ANLS to always return 0.5 for string comparisons regardless of actual similarity.

---

#### 3. Created DC Evaluator V2 - Uses Original DC Implementation

**File**: `dspy_implementation/dc_module/dc_evaluator_v2.py`  
**Purpose**: Directly uses DC's `LanguageModel.advanced_generate()` method

**What It Does**:
- ✅ Imports original `LanguageModel` from `dc_repo/`
- ✅ Calls `advanced_generate()` with proper approach names:
  - `"DynamicCheatsheet_Cumulative"` for DC-CU
  - `"DynamicCheatsheet_RetrievalSynthesis"` for DC-RS
- ✅ Only adapts MMESGBench data format (question, context, format)
- ✅ Uses corrected evaluation with null equivalence + string fix
- ✅ Loads original prompts from `dc_repo/prompts/`

**What It Doesn't Do**:
- ❌ Reimplement DC logic ourselves
- ❌ Modify DC's core algorithms
- ❌ Use DSPy framework

---

## Running DC-RS

### Prerequisites

1. **Install DC repository**:
```bash
cd /Users/victoryim/Local_Git/CC
git clone https://github.com/suzgunmirac/dynamic-cheatsheet dc_repo
```

2. **Apply DashScope model support**:
Edit `dc_repo/dynamic_cheatsheet/language_model.py` lines 51-58 to add DashScope models (see above)

3. **Activate conda environment**:
```bash
conda activate esg_reasoning
```

### Commands

**DC-CU (Cumulative) - Dev Set**:
```bash
python dspy_implementation/dc_module/dc_evaluator_v2.py \
  --dataset dev \
  --variant cumulative \
  --model qwen2.5-7b-instruct
```

**DC-RS (Retrieval & Synthesis) - Dev Set**:
```bash
python dspy_implementation/dc_module/dc_evaluator_v2.py \
  --dataset dev \
  --variant retrieval_synthesis \
  --model qwen2.5-7b-instruct
```

**Test on first 10 questions**:
```bash
python dspy_implementation/dc_module/dc_evaluator_v2.py \
  --dataset dev \
  --variant retrieval_synthesis \
  --max-questions 10
```

---

## Comparison: Old vs New Implementation

| Aspect | Old (dc_rag_module.py) | New (dc_evaluator_v2.py) |
|--------|------------------------|--------------------------|
| **DC Core** | Reimplemented ourselves | Uses original DC code |
| **Method** | Custom `generate_with_cheatsheet()` | Calls `advanced_generate()` |
| **Prompts** | Custom ESG prompts | Original DC prompts from repo |
| **Risk** | May deviate from paper | Exact replication of paper |
| **Maintenance** | Need to track DC updates | Just update dc_repo/ |

---

## Key Differences: DC-CU vs DC-RS

### DC-CU (Cumulative)
```
Question 1 → Generator (empty cheatsheet) → Answer 1
          → Curator (update cheatsheet v1)
          
Question 2 → Generator (cheatsheet v1) → Answer 2
          → Curator (update cheatsheet v2)
          
Question 3 → Generator (cheatsheet v2) → Answer 3
          ...
```

- **Cheatsheet**: Single, growing knowledge base
- **Used by**: Every question uses same accumulated cheatsheet
- **Update**: After each question, curator updates the cheatsheet

### DC-RS (Retrieval & Synthesis)
```
Question 1 → Retrieve (empty history) → no similar Q&As
          → Curator (synthesize custom cheatsheet v1 for Q1)
          → Generator (custom cheatsheet v1) → Answer 1
          → Store Q1+A1 in history
          
Question 2 → Retrieve (Q1) → similar Q&A: Q1+A1
          → Curator (synthesize custom cheatsheet v2 for Q2 from Q1+A1)
          → Generator (custom cheatsheet v2) → Answer 2
          → Store Q2+A2 in history
          
Question 3 → Retrieve (Q1,Q2) → top-K similar Q&As
          → Curator (synthesize custom cheatsheet v3 for Q3 from similar Q&As)
          → Generator (custom cheatsheet v3) → Answer 3
          ...
```

- **Cheatsheet**: Custom synthesized for each question
- **Used by**: Each question gets a tailored cheatsheet from similar past Q&As
- **Update**: Curator synthesizes new cheatsheet using:
  - Global cheatsheet (knowledge base)
  - Retrieved similar Q&As (top-K by cosine similarity)
  - Current question

---

## Expected Results

Based on DC paper and our previous runs:

| Variant | Dev Set (93q) | Test Set (654q) | Notes |
|---------|---------------|-----------------|-------|
| **DC-CU** | ~57% | ~49% | Already validated |
| **DC-RS** | ? | ? | New - needs testing |

**Hypothesis**: DC-RS might perform better if similar questions exist in history, or worse if early questions don't provide useful patterns.

---

## Next Steps

1. ✅ Test DC-RS on dev set (10 questions POC)
2. ⏳ Compare DC-RS vs DC-CU on full dev set
3. ⏳ If promising, run on test set
4. ⏳ Document results and update main README

---

## Files Created/Modified

### New Files
- `dspy_implementation/dc_module/dc_evaluator_v2.py` - Main evaluator using original DC
- `dspy_implementation/dc_module/dc_prompts.py` - Added `CURATOR_PROMPT_RS`
- `DC_RS_IMPLEMENTATION_NOTES.md` - This file

### Modified Files
- `src/evaluation_utils.py` - Fixed ANLS string bug
- `dspy_implementation/dc_module/dc_rag_module.py` - Enhanced with DC-RS support (legacy)
- `dc_repo/dynamic_cheatsheet/language_model.py` - Added DashScope models (external, not tracked)

---

## Known Issues

None currently. Both evaluation bugs (null equivalence + ANLS string) are now fixed.

---

**Last Updated**: November 9, 2025  
**Author**: AI Assistant + Sum Yee Chan (RA - evaluation fixes)

