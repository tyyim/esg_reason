# GEPA ScoreWithFeedback Fix - Summary

**Date**: 2025-10-17
**Status**: ✅ **SOLVED** - GEPA optimization now working!

## Problem Statement

GEPA optimizer was failing with:
```
AttributeError: 'dict' object has no attribute 'score'
```

**Error Location**: `dspy/teleprompt/gepa/gepa_utils.py:217` in `_normalize_score()` function trying to access `fb.score`

## Root Cause

The metric function was returning a plain Python `dict` with `{"score": float, "feedback": str}`, but GEPA expected a **`ScoreWithFeedback` object** (Prediction subclass) with `.score` and `.feedback` **attributes**.

**Key Difference**:
- ❌ Dict: `fb["score"]` (bracket access)
- ✅ Object: `fb.score` (dot attribute access)

## Investigation Process

1. **Analyzed GEPA Source Code**:
   - Located installed package: `/Users/victoryim/anaconda3/envs/esg_reasoning/lib/python3.10/site-packages/gepa/`
   - Found adapter: `adapters/dspy_adapter/dspy_adapter.py`

2. **Discovered ScoreWithFeedback Class**:
   ```python
   class ScoreWithFeedback(Prediction):
       """
       Prediction subclass for GEPA feedback metrics.
       Must have .score and .feedback attributes.
       """
       score: float
       feedback: str
   ```

3. **Key Insight**:
   - ScoreWithFeedback is a **Prediction subclass**, not a plain dict
   - It's a dataclass-like structure with typed attributes
   - GEPA reflection mechanism expects this specific type

## Solution Implemented

**File Modified**: `dspy_implementation/dspy_metrics_gepa_fixed.py`

### Changes Made:

1. **Added ScoreWithFeedback Class** (lines 22-30):
   ```python
   from dspy.primitives import Prediction

   class ScoreWithFeedback(Prediction):
       """
       Prediction subclass for GEPA feedback metrics.
       Must have .score and .feedback attributes for GEPA's reflection mechanism.
       """
       score: float
       feedback: str
   ```

2. **Updated All Return Statements**:

   **Before (incorrect)**:
   ```python
   return {
       "score": score,
       "feedback": "\n".join(feedback_parts)
   }
   ```

   **After (correct)**:
   ```python
   return ScoreWithFeedback(
       score=score,
       feedback="\n".join(feedback_parts)
   )
   ```

3. **Four Return Statements Fixed**:
   - Line 67-70: Error handling in `mmesgbench_answer_only_gepa_metric`
   - Line 126-129: Main return in `mmesgbench_answer_only_gepa_metric`
   - Line 158: Error handling in `mmesgbench_full_gepa_metric`
   - Line 227-230: Main return in `mmesgbench_full_gepa_metric`

## Verification

### Quick Test (10 examples)
```bash
python dspy_implementation/gepa_quick_test.py
```

**Result**: ✅ **SUCCESS**
- No more `AttributeError`
- GEPA successfully started optimization
- Completed 3 iterations with scores: 0.4, 1.0, 0.33
- Progress: 4% (29/790 rollouts)

### Full Optimization (186 train / 93 dev)
```bash
python dspy_implementation/gepa_qwen7b_optimization.py 2>&1 | tee logs/gepa_test/gepa_full_run.log
```

**Status**: 🔄 **Running in background**
- MLFlow run: `gepa_qwen7b_20251017_100839`
- Experiment: `ESG_GEPA_Optimization`
- Expected runtime: ~45 minutes
- Target: ≥+2.2% improvement (match MIPROv2)

## Technical Details

### GEPA Metric Protocol

The metric function has **dual behavior** based on `pred_name` parameter:

1. **When `pred_name is None`** (aggregation mode):
   ```python
   return 0.5  # Plain float for DSPy evaluation
   ```

2. **When `pred_name` is provided** (reflection mode):
   ```python
   return ScoreWithFeedback(
       score=0.5,
       feedback="✅ CORRECT: Both retrieval and answer are correct..."
   )
   ```

### Why This Works

**DSPy's evaluation framework**:
- Calls metric with `pred_name=None` for aggregation
- Can sum floats: `0.5 + 0.0 + 1.0 = 1.5`
- Cannot sum dicts: `{} + {} = TypeError`

**GEPA's reflection mechanism**:
- Calls metric with `pred_name="predictor_name"` for feedback
- Analyzes `feedback` string to understand failures
- Uses `score` to track performance
- Expects object with `.score` and `.feedback` attributes (not dict)

## GEPA Architecture

```
┌──────────────────────────────────────┐
│ GEPA Reflective Optimization         │
│                                      │
│  1. Task LM (qwen2.5-7b)             │
│     ↓                                │
│     Executes current prompts         │
│     ↓                                │
│  2. Metric Function                  │
│     ↓                                │
│     Returns ScoreWithFeedback        │
│     - score: 0.5                     │
│     - feedback: "❌ Missing page 12" │
│     ↓                                │
│  3. Reflection LM (qwen-max)         │
│     ↓                                │
│     Reads detailed feedback          │
│     ↓                                │
│     Proposes improved prompts        │
│     ↓                                │
│  4. Pareto Selection                 │
│     ↓                                │
│     Evolves prompts                  │
└──────────────────────────────────────┘
```

## Comparison: MIPROv2 vs GEPA

| Aspect | MIPROv2 Teacher-Student | GEPA Reflection |
|--------|------------------------|-----------------|
| **Metric Return** | `float` only | `float` OR `ScoreWithFeedback` |
| **Feedback Signal** | Scalar score | Rich textual feedback |
| **Prompt Evolution** | Teacher proposes | Reflection LM analyzes failures |
| **Selection** | Best candidates | Pareto frontier |
| **Result** | +2.2% (54.8% → 57.0%) | **TBD** (target: ≥+2.2%) |

## Files Modified

**Primary**:
- [dspy_implementation/dspy_metrics_gepa_fixed.py](../dspy_implementation/dspy_metrics_gepa_fixed.py) - Fixed metric returns

**Supporting**:
- [dspy_implementation/gepa_qwen7b_optimization.py](../dspy_implementation/gepa_qwen7b_optimization.py) - Main script
- [dspy_implementation/gepa_quick_test.py](../dspy_implementation/gepa_quick_test.py) - Quick test
- [CLAUDE.md](../CLAUDE.md) - Updated status

**Documentation**:
- [GEPA_APPROACH.md](GEPA_APPROACH.md) - Methodology
- [config_gepa_qwen7b.yaml](config_gepa_qwen7b.yaml) - Configuration
- This file (GEPA_FIX_SUMMARY.md)

## Lessons Learned

1. **Type matters**: Dict vs Object with attributes is critical
2. **Read source code**: GEPA's installed package revealed the correct implementation
3. **Dual behavior**: Metrics can return different types based on context
4. **Prediction subclass**: ScoreWithFeedback extends DSPy's Prediction class
5. **Rich feedback**: Textual feedback is GEPA's key innovation over score-only optimizers

## Next Steps

1. ⏳ **Wait for optimization to complete** (~45 min)
2. ⏳ **Analyze GEPA results** vs MIPROv2 baseline (+2.2%)
3. ⏳ **Inspect reflection insights** - what did qwen-max learn?
4. ⏳ **Compare interpretability** - GEPA vs teacher-student
5. ⏳ **Update Notion** with findings
6. ⏳ **Prepare publication analysis** - reflective vs teacher-student optimization

## Success Criteria

✅ **Primary**: GEPA optimization runs without errors
⏳ **Secondary**: Answer accuracy improvement ≥ +2.2%
⏳ **Tertiary**: Interpretable reflection insights from qwen-max

## References

- **GEPA Paper**: "GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning" (Agrawal et al., 2025, arxiv:2507.19457)
- **GEPA GitHub**: https://github.com/gepa-ai/gepa
- **DSPy Adapter**: https://github.com/gepa-ai/gepa/tree/main/src/gepa/adapters/dspy_full_program_adapter
- **DSPy Docs**: https://dspy.ai/api/optimizers/GEPA/overview/

---

**Status**: ✅ Issue resolved, optimization running successfully!
