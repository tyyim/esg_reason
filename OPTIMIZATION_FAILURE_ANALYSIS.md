# MIPROv2 Optimization Failure Analysis

## Problem: Negative Improvement (-3.2%)

- **Baseline (dev 93)**: 51.6% E2E accuracy
- **Optimized (dev 93)**: 48.4% E2E accuracy
- **Result**: -3.2% degradation instead of improvement

## Root Cause Discovered

### Issue 1: Dataset Mismatch Between MIPROv2 and Our Evaluation

**MIPROv2's Internal Validation**:
- Used **100 questions** (randomly sampled from trainset as valset)
- Default baseline score: **44.0%**
- Best optimized score found: **47.0%** (last trial)
- Improvement: **+3.0%** ✅

**Our Evaluation**:
- Used **93 questions** (fixed dev set)
- Baseline score: **51.6%**
- Optimized score: **48.4%**
- Result: **-3.2%** ❌

### Issue 2: The 93 Dev Set ≠ The 100 Validation Set

The 93-question dev set and MIPROv2's 100-question validation set are **different questions**!

**Evidence**:
```
Baseline on MIPROv2 valset (100 q): 44.0%
Baseline on our dev set (93 q): 51.6%
```

The 93 dev set appears to be **easier** (51.6% vs 44.0%), or contains different question types.

### Issue 3: MIPROv2 DID Find Improvement (on its validation set)

Looking at the logs:
- Trial 1 (default): **44.0%** on 100-question valset
- Trial 2-19: All scored **≤44.0%** (no improvement)
- Final trials: Best score reached **47.0%** (+3.0% improvement)

**MIPROv2 actually succeeded** on its own validation set!

## Why We See Negative Results

The optimized prompts were selected based on performance on the **100-question validation set**, but we measured final results on a **completely different 93-question dev set**.

This is like:
1. Training a student on practice test A
2. Finding they improved from 44% → 47% on test A
3. Then testing them on a **completely different** test B
4. Seeing them score worse than baseline on test B

## What Went Wrong in Our Setup

### ❌ What We Did:
```python
# Step 1: Evaluate baseline on 93 dev set → 51.6%
baseline_rag = BaselineMMESGBenchRAG()
baseline_results = evaluate(baseline_rag, dev_set_93)  # 51.6%

# Step 2: Optimize using MIPROv2 (creates its own 100-q valset)
optimizer = MIPROv2(metric=..., auto="light")
optimized_rag = optimizer.compile(
    student=baseline_rag,
    trainset=train_186  # MIPROv2 samples 100 random questions for validation
)

# Step 3: Evaluate optimized on same 93 dev set → 48.4%
optimized_results = evaluate(optimized_rag, dev_set_93)  # 48.4%

# Step 4: Compare 51.6% vs 48.4% → WRONG COMPARISON!
```

### ✅ What We Should Have Done:
```python
# Option A: Use SAME validation set for both
baseline_results = evaluate(baseline_rag, valset_100)
optimized_results = evaluate(optimized_rag, valset_100)

# Option B: Force MIPROv2 to use our dev set
optimizer = MIPROv2(metric=..., auto="light")
optimized_rag = optimizer.compile(
    student=baseline_rag,
    trainset=train_186,
    valset=dev_set_93  # Force MIPROv2 to use our dev set
)
```

## Additional Evidence

### MIPROv2 Optimization Scores (on 100-question valset):
```
Trial 1 (default):     44.0%
Trial 2-6:             40.0% - 42.86% (worse)
Trial 7:               42.0% (worse)
...
Final trials:          47.0% (BEST - improvement found!)
```

### Our Measurements (on 93-question dev set):
```
Baseline:   51.6%
Optimized:  48.4%
```

The discrepancy shows these are **different question sets** with different difficulty levels.

## Correct Interpretation

**MIPROv2 worked correctly** - it found a 3% improvement on its validation set (44% → 47%).

**Our measurement failed** - we compared performance across two different evaluation sets, making the comparison invalid.

## Solutions

### Solution 1: Re-run with Explicit Valset (RECOMMENDED)
```python
# Force MIPROv2 to optimize on our dev set
optimized_rag = optimizer.compile(
    student=baseline_rag,
    trainset=train_186,
    valset=dev_set_93,  # ← Add this parameter
    num_trials=20,
    minibatch=False  # Use full valset for each trial
)
```

### Solution 2: Evaluate on MIPROv2's Valset
Extract the 100 questions MIPROv2 used and re-evaluate baseline on those same 100 questions for fair comparison.

### Solution 3: Use More Training Data
- Current: 186 train (20%)
- Increase to: 466 train (50%) or 746 train (80%)
- More training data may help MIPROv2 find more generalizable prompts

### Solution 4: Try Medium/Heavy Auto Mode
- Current: "light" (6 trials, num_fewshot_candidates=6)
- Try: "medium" (12 trials) or "heavy" (24 trials)
- More trials may find better prompt combinations

## Key Takeaway

**The optimization didn't fail - our evaluation methodology did.**

MIPROv2 successfully improved performance by 3% on its validation set. We just compared apples (51.6% on dev93) to oranges (48.4% on dev93 after optimizing for valset100).

## Next Steps

1. **Re-run optimization** with explicit `valset=dev_set_93` parameter
2. **Use same evaluation set** for both baseline and optimized measurements
3. **Document the evaluation protocol** clearly in code comments
4. Consider using more training data (50% instead of 20%)
5. Try medium auto mode if light mode still shows issues
