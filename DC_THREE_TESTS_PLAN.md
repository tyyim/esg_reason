# Dynamic Cheatsheet - Three Tests Plan

**Date**: November 1, 2025  
**Status**: IN PROGRESS

---

## Testing Strategy

We're running 3 comprehensive tests to evaluate Dynamic Cheatsheet's test-time learning:

1. **Test 1: Dev Set Only** - Establish reference performance & generate cheatsheet
2. **Test 2: Test Set Cold** - Fair comparison to DSPy (blank cheatsheet)
3. **Test 3: Test Set Bootstrapped** - Dev cheatsheet -> Test set (partial warmup)

## ⚠️ IMPORTANT: Fair Comparison Update (Nov 1, 16:14)

**Original DC prompts** (43.0% on dev) were too different from DSPy baseline.

**New approach - FAIR COMPARISON**:
- DC now uses **exact same 2-stage structure as DSPy** (Reasoning -> Extraction)
- **ONLY difference**: Cheatsheet added to Stage 1 (Reasoning)
- Stage 3 (Curator) updates cheatsheet after both stages
- **Trade-off**: 3 API calls/question (~37 sec) vs DSPy's 2 calls (~20 sec)

**Expected improvement**: Should be much closer to DSPy baseline (52.7% on dev)

---

## Test 1: Dev Set Evaluation

### Purpose
- Establish DC performance on dev set (93 questions)
- Generate reference cheatsheet from dev set learning
- Compare to DSPy baseline dev performance

### Command
```bash
python dspy_implementation/dc_module/dc_evaluator.py \
  --dataset dev \
  --variant cumulative
```

### Expected Results (UPDATED with fair prompts)
- **Accuracy**: 50-55% (vs DSPy baseline 52.7% on dev) - Should be much closer now!
- **Runtime**: ~60 minutes (93 Q × ~37 sec/Q) - 3 API calls per question
- **Cost**: ~$0.066 (93 Q × 3 calls × 400 tokens × $0.0006/1K)
- **Cheatsheet**: ~2-4K characters

### Status
**RE-RUNNING with Fair Prompts** - Started at 16:14:36
- Old test (different prompts): 43.0% (15:31-16:05)
- New test (DSPy-matching prompts): In progress

### Output Files
- Results: `results/dc_experiments/dc_cumulative_cold_dev_{timestamp}.json`
- Cheatsheet: Saved in `final_cheatsheet` field
- Logs: `logs/dc_evaluation/dc_eval_20251101_153119.log`

---

## Test 2: Test Set Cold (Fair Comparison)

### Purpose
- Fair comparison to DSPy approaches (no training from test)
- DC starts with blank cheatsheet, learns only during test
- **This is the main comparison point**

### Command
```bash
python dspy_implementation/dc_module/dc_evaluator.py \
  --dataset test \
  --variant cumulative
```

### Expected Results
- **Accuracy**: 48-50%
  - vs DSPy Baseline: 47.4% ✅ Similar
  - vs DSPy MIPROv2: 47.6% ✅ Similar
  - vs DSPy GEPA: 45.7% ✅ Better
  - vs Hybrid: 50.2% ⚠️ Slightly lower
- **Runtime**: ~3-4 hours (654 Q × ~13 sec/Q = ~2.36 hours)
- **Cost**: ~$0.31 (654 Q × 2 calls × 400 tokens)
- **Cheatsheet**: ~5-10K characters (evolves from empty)

### Status
**PENDING** - Will start after Test 1 completes

### Comparison Type
✅ **FAIR** - Both DC and DSPy start with no test set knowledge

### Output Files
- Results: `results/dc_experiments/dc_cumulative_cold_test_{timestamp}.json`
- Logs: `logs/dc_evaluation/dc_eval_{timestamp}.log`

---

## Test 3: Test Set Bootstrapped from Dev

### Purpose
- Test if dev set learning transfers to test set
- Partial warmup strategy (learns from dev, applies to test)
- Shows value of accumulated domain knowledge

### Command
```bash
# Extract dev cheatsheet path from Test 1 results
DEV_RESULTS="results/dc_experiments/dc_cumulative_cold_dev_{timestamp}.json"

python dspy_implementation/dc_module/dc_evaluator.py \
  --dataset test \
  --variant cumulative \
  --bootstrap-cheatsheet $DEV_RESULTS
```

### Expected Results
- **Accuracy**: 50-53%
  - Better than Test 2 (cold start)
  - Lower than full warmup (52-56%)
  - Similar or better than Hybrid (50.2%)
- **Runtime**: ~3-4 hours (654 Q × ~13 sec/Q)
- **Cost**: ~$0.31
- **Cheatsheet**: Starts at ~2-4K (from dev), grows to ~7-12K

### Status
**PENDING** - Will start after Test 2 completes

### Comparison Type
⚠️ **PARTIALLY FAIR** - DC learns from dev (93 Q), DSPy optimizes on train+dev (279 Q)
- More fair than full warmup (doesn't see test)
- Less fair than cold start (uses dev learning)
- Similar to DSPy GEPA/MIPROv2 (both use non-test data)

### Output Files
- Results: `results/dc_experiments/dc_cumulative_bootstrap_test_{timestamp}.json`
- Logs: `logs/dc_evaluation/dc_eval_{timestamp}.log`

---

## Comparison Matrix

### Fair Comparisons ✅

| DC Approach | DSPy Approach | Training Data | Fair? | Expected DC vs DSPy |
|-------------|---------------|---------------|-------|---------------------|
| **Test 2: Cold** | Baseline | None | ✅ Yes | 48-50% vs 47.4% (+0.6-2.6%) |
| **Test 3: Bootstrap** | GEPA/MIPROv2 | Dev only vs Train+Dev | ⚠️ Mostly | 50-53% vs 45-48% (+2-8%) |

### Unfair Comparisons ❌

| DC Approach | DSPy Approach | Why Unfair? |
|-------------|---------------|-------------|
| Full Warmup | Any DSPy | DC sees test set during warmup |
| Test 3 | Baseline | DC uses dev, Baseline doesn't |

---

## Expected Findings

### Hypothesis 1: Cold Start Similar to Baseline
**Test 2 should match DSPy Baseline** (~47-50%)
- Both start with no domain knowledge
- DC learns during test, DSPy uses static prompt
- If DC > Baseline: Test-time learning helps
- If DC = Baseline: Learning too slow / test set diverse
- If DC < Baseline: Learning adds noise

### Hypothesis 2: Bootstrap Better Than Cold
**Test 3 should beat Test 2** (+2-5%)
- Dev learning should transfer to test
- Cheatsheet captures generalizable patterns
- If YES: Domain knowledge accumulation works
- If NO: Dev/test distribution mismatch

### Hypothesis 3: Format-Specific Performance
**DC should excel at structured formats** (Int, Float, List)
- Formulas and patterns easier to learn
- String extraction harder to generalize
- Expected: +5-15% on Int/Float/List, -5% on Str

---

## Timeline & Costs

### Test 1: Dev Set
- **Duration**: ~20-25 minutes
- **Cost**: $0.044
- **Status**: RUNNING (15:31:19 - expected done 15:51)

### Test 2: Test Set Cold
- **Duration**: ~3-4 hours
- **Cost**: $0.31
- **Status**: PENDING (will start ~15:51)

### Test 3: Test Set Bootstrap
- **Duration**: ~3-4 hours
- **Cost**: $0.31
- **Status**: PENDING (will start after Test 2)

### Total
- **Duration**: ~7-9 hours (with sequential execution)
- **Cost**: $0.66
- **Start**: 15:31 (Nov 1)
- **Expected Complete**: ~00:30 (Nov 2)

---

## Success Criteria

### Minimum Success
- ✅ All 3 tests complete without errors
- ✅ Test 2 accuracy ≥ 45% (not worse than GEPA)
- ✅ Test 3 accuracy > Test 2 (bootstrap helps)

### Good Success
- ✅ Test 2 accuracy ≈ 47-50% (matches baseline/MIPROv2)
- ✅ Test 3 accuracy ≈ 50-53% (beats most DSPy approaches)
- ✅ Format-specific gains visible (Int/Float/List improved)

### Excellent Success
- ✅ Test 2 accuracy > 48% (beats baseline)
- ✅ Test 3 accuracy > 50% (beats Hybrid)
- ✅ Clear evidence of test-time learning benefit

---

## Analysis Plan

After all 3 tests complete:

### 1. Overall Performance Comparison
- DC-Cold vs DSPy Baseline/MIPROv2/GEPA
- DC-Bootstrap vs DSPy approaches
- Statistical significance (McNemar's test)

### 2. Format-Specific Analysis
- Breakdown by Int/Float/Str/List/null
- Where does DC excel vs DSPy?
- Where does learning help most?

### 3. Cheatsheet Evolution Analysis
- Dev cheatsheet content & patterns
- How much does cheatsheet grow on test?
- What insights are captured?

### 4. Learning Curve Analysis
- Does accuracy improve over time?
- First 100 Q vs last 100 Q on test
- Bootstrap starting advantage?

### 5. Cost-Performance Trade-off
- DC: 2x API calls per question
- Is test-time learning worth the cost?
- When to use DC vs DSPy optimization?

---

## Next Steps After Tests

1. **Document Results** - Create `DC_FINAL_RESULTS.md`
2. **Update CHANGELOG.md** - Record all 3 test results
3. **Update README.md** - Add DC results to main table
4. **Statistical Analysis** - Significance testing
5. **Write Findings** - DC vs DSPy comparison paper

---

## Monitoring Commands

### Check Test Progress
```bash
# Check latest log
tail -f logs/dc_evaluation/dc_eval_*.log

# Check checkpoint (saved every 10 Q)
ls -lh results/dc_experiments/*checkpoint.json

# Check if process still running
ps aux | grep dc_evaluator
```

### Get Current Results
```bash
# Latest results file
ls -lt results/dc_experiments/*.json | head -1

# Quick accuracy check
python -c "
import json
with open('results/dc_experiments/dc_cumulative_cold_dev_20251101_153119.json') as f:
    r = json.load(f)
    print(f\"Accuracy: {r['overall_accuracy']:.1%}\")
"
```

---

**Status**: Test 1 running, Tests 2 & 3 pending  
**Next Update**: After Test 1 completes (~15:51)

