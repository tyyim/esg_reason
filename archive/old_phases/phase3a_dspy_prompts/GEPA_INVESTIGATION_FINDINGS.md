# GEPA Investigation Findings
**Date**: October 17, 2025
**Status**: ⚠️ PARTIALLY SOLVED - Additional work needed

---

## 🎯 Objective
Implement GEPA (Genetic-Pareto) optimizer with reflective feedback for ESG question answering optimization.

---

## 📊 Progress Summary

### ✅ Issues Solved

#### 1. **Python Version Incompatibility** ✅
- **Problem**: GEPA requires Python ≥3.10, environment had Python 3.9
- **Solution**: Upgraded to Python 3.10.18
- **Impact**: All GEPA dependencies now installable

#### 2. **Missing Dependencies** ✅
- **Problem**: Multiple packages missing after Python upgrade
- **Solution**: Installed: `langchain-community`, `rapidfuzz`, `dashscope`, `psycopg2-binary`
- **Impact**: All imports working correctly

#### 3. **Optimizer Parameter Mismatch** ✅
- **Problem**: GEPA doesn't accept `requires_permission_to_run` parameter
- **Error**: `TypeError: GEPA.compile() got an unexpected keyword argument`
- **Solution**: Removed parameter from GEPA compile call
- **Documentation**: Added to CLAUDE.md

#### 4. **Dataset Consistency Verification** ✅
- **Question**: Are performance variations due to different dev sets?
- **Answer**: No - all experiments use identical splits with seed=42
- **Evidence**: Splits saved to JSON, verified timestamps match
- **Impact**: All comparisons are scientifically valid

#### 5. **Metric Return Type (First Issue)** ✅
- **Problem**: DSPy's evaluation framework tries to sum metric results
- **Error**: `TypeError: unsupported operand type(s) for +: 'int' and 'dict'`
- **Solution**: Return `float` when `pred_name is None`, return `dict` only when `pred_name` is provided
- **Fixed in**: `dspy_metrics_gepa_fixed.py`

---

### ⚠️ Current Blocker

#### **Metric Return Type (Second Issue)** 🔴
- **Problem**: GEPA expects feedback object with `.score` attribute, not dict
- **Error**: `AttributeError: 'dict' object has no attribute 'score'`
- **Location**: `dspy/teleprompt/gepa/gepa_utils.py:217`
- **Code**:
  ```python
  assert fb["score"] == module_score, f"... the feedback score is {fb.score}."
  # Problem: fb.score fails when fb is a dict
  ```

**Root Cause**:
GEPA's internal code expects a `ScoreWithFeedback` object with:
- Attribute access: `fb.score`
- Not dict access: `fb["score"]`

**Evidence from Test Output**:
```
2025/10/17 09:09:21 INFO dspy.teleprompt.gepa.gepa:
  Iteration 1: Exception during reflection/proposal:
  'dict' object has no attribute 'score'
```

---

## 📚 Key Documentation Findings

### From DSPy.ai Official Docs

**Metric Signature**:
```python
def metric(
    gold: Example,
    pred: Prediction,
    trace: Optional[DSPyTrace] = None,
    pred_name: Optional[str] = None,
    pred_trace: Optional[DSPyTrace] = None,
) -> float | ScoreWithFeedback
```

**Key Points**:
1. Metric can return **either** `float` OR `ScoreWithFeedback`
2. `ScoreWithFeedback` format not clearly documented (dict vs object?)
3. When `pred_name` is None: Returns score for aggregation
4. When `pred_name` is provided: Returns feedback for reflection

**What Worked** (Initial execution):
- ✅ GEPA started optimization
- ✅ Baseline evaluation completed: 4/10 (40%)
- ✅ Iteration 0 completed successfully
- ✅ Iteration 1 selected program with score 0.4

**What Failed** (Reflection phase):
- ❌ Reflection/proposal step failed when accessing `.score` attribute
- ❌ Cannot complete optimization without successful reflection

---

## 🔍 Next Steps

### Option 1: Find ScoreWithFeedback Class ⭐ **RECOMMENDED**
```python
# Check if DSPy provides ScoreWithFeedback
from dspy import ScoreWithFeedback  # Does this exist?

# Or check GEPA package
from gepa import ScoreWithFeedback  # Does this exist?
```

**Action**:
1. Search DSPy source code for `ScoreWithFeedback` class definition
2. Check if it's a dataclass, namedtuple, or custom object
3. Update metric to return proper type

### Option 2: Create Custom ScoreWithFeedback Class
```python
from dataclasses import dataclass

@dataclass
class ScoreWithFeedback:
    score: float
    feedback: str
```

**Action**:
1. Define class matching GEPA's expectations
2. Update `dspy_metrics_gepa_fixed.py` to return this type
3. Test with quick test script

### Option 3: Fix GEPA Source Code
```python
# In gepa_utils.py line 217, change:
assert fb["score"] == module_score, f"... the feedback score is {fb.score}."
# To:
assert fb["score"] == module_score, f"... the feedback score is {fb['score']}."
```

**Action**:
1. Locate `gepa_utils.py` in installed packages
2. Make local modification
3. Re-run test (not recommended for production)

### Option 4: Use MIPROv2 Instead ✅ **PRAGMATIC**
- **Reason**: MIPROv2 already works with teacher-student approach (+2.2% improvement)
- **Trade-off**: Miss out on GEPA's reflective feedback benefits
- **Decision**: May be best to stick with proven MIPROv2 approach

---

## 📁 Files Created

### Working Files
1. **`dspy_metrics_gepa_fixed.py`** - Partially fixed metric (solves Issue 1, not Issue 2)
2. **`gepa_quick_test.py`** - Quick test script that skips baseline evaluation
3. **`gepa_qwen7b_optimization.py`** - Main GEPA optimization script (blocked)

### Documentation
1. **`GEPA_APPROACH.md`** - GEPA architecture and approach
2. **`config_gepa_qwen7b.yaml`** - GEPA configuration
3. **`GEPA_INVESTIGATION_FINDINGS.md`** - This file

### Updated
1. **`CLAUDE.md`** - Added GEPA parameter warnings and issue documentation

---

## 💡 Research Implications

**If GEPA can be fixed**:
- ✅ Provides rich textual feedback for prompt evolution
- ✅ May outperform MIPROv2's score-only approach
- ✅ Could be a publication-worthy comparison

**If GEPA cannot be fixed**:
- ✅ MIPROv2 teacher-student already works (+2.2%)
- ✅ Can focus on other optimizations (medium/heavy mode)
- ✅ Can try alternative optimizers (BayesianOptimization, etc.)

**Current Recommendation**:
- **Spend 30-60 minutes investigating ScoreWithFeedback class**
- If not found quickly, **proceed with MIPROv2 medium mode** instead
- GEPA can be revisited in future work if time permits

---

## 📊 Test Results

### GEPA Quick Test (with fixed metric v1)
```
✅ GEPA optimizer created
✅ GEPA.compile() started
✅ Baseline evaluation: 4/10 (40%)
✅ Iteration 0: Base program score 0.4
✅ Iteration 1: Selected program score 0.4
❌ Iteration 1: Exception during reflection - 'dict' has no attribute 'score'
⏸️  Optimization continuing but cannot complete reflections
```

**Progress**: 75% complete - only reflection phase failing

---

## 🔗 References

1. **DSPy GEPA Docs**: https://dspy.ai/api/optimizers/GEPA/overview/
2. **GEPA GitHub**: https://github.com/gepa-ai/gepa
3. **GEPA Metric Signature**: https://dspy.ai/api/optimizers/GEPA/overview/#dspy.teleprompt.gepa.gepa.GEPAFeedbackMetric
4. **Teacher-Student Results**: `logs/qwen7b_test/teacher_student_qwen7b_results_20251016_230050.json`

---

**Last Updated**: 2025-10-17 09:15 AM
**Next Action**: Investigate ScoreWithFeedback class or proceed with MIPROv2 medium mode
