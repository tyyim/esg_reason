# Dynamic Cheatsheet - Tests Status

**Date**: November 7, 2025 (Corrected Results)  
**Status**: ✅ COMPLETE - Bug Fix Applied

> **IMPORTANT**: Results corrected Nov 7, 2025 after fixing null equivalence bug in evaluation.
> Original MMESGBench `eval_score()` treated "null" and "Not answerable" as different strings,
> causing false negatives. See commit `9177497` for details.

---

## ✅ Test 1: Dev Set (COMPLETE)

**Purpose**: Establish baseline & generate reference cheatsheet

**Configuration**:
- Dataset: Dev (93 questions)
- Cheatsheet: Empty (starts blank)
- Prompts: Original DC prompts (not DSPy-matching)

**Results (Corrected)**: 
- **Accuracy**: **57.0%** (53/93) [was 43.0% before fix]
- **Runtime**: 34 minutes (15:31-16:05)
- **Cheatsheet**: 3,654 characters generated

**Format Breakdown (Corrected)**:
| Format | Accuracy | Correct | Total |
|--------|----------|---------|-------|
| Int | 42.1% | 8 | 19 |
| Float | **69.2%** ⭐ | 9 | 13 |
| Str | 50.0% | 17 | 34 |
| List | 46.2% | 6 | 13 |
| **null** | **92.9%** ✅ | 13 | 14 |

**vs DSPy Baseline on Dev**: **57.0% vs 52.7% (+4.3%)** ✅

**Files**:
- Results: `results/dc_experiments/dc_cumulative_cold_dev_20251101_153119.json`
- Validation: `results/dc_experiments/dc_cumulative_cold_dev_20251107_185530.json` (57.0% confirmed)
- Cheatsheet: Extracted to `results/dc_experiments/dev_cheatsheet_20251101.txt`

**Key Findings**: 
- ✅ **DC now outperforms DSPy baseline on dev set** (+4.3%)
- ⭐ **Float format still performs best** (69.2%)
- ✅ **Null format bug fixed**: 0.0% → 92.9% after evaluation correction

---

## ✅ Test 2: Test Set Cold Start (COMPLETE)

**Purpose**: Fair comparison to DSPy (no prior learning from test)

**Configuration**:
- Dataset: Test (654 questions)
- Cheatsheet: **Blank** (starts empty, learns during test)
- Prompts: Original DC prompts
- Model: qwen2.5-7b-instruct

**Results (Corrected - Nov 7, 2025)**:
- **Accuracy**: **49.2%** (322/654) [was 35.6% before null bug fix]
- **Runtime**: ~4 hours
- **Cost**: ~$0.31
- **Cheatsheet**: Evolved from empty → ~8,000 chars

**Format Breakdown**:
| Format | Accuracy | Correct | Total |
|--------|----------|---------|-------|
| Int | 44.1% | 67 | 152 |
| Float | 41.7% | 40 | 96 |
| Str | 44.5% | 94 | 211 |
| List | 36.4% | 32 | 88 |
| **null** | **83.2%** ✅ | 89 | 107 |

**vs DSPy Baseline on Test**: **49.2% vs 47.4% (+1.8%)** ✅

**Files**:
- Results: `results/dc_experiments/dc_cumulative_cold_test_20251101_171723.json`
- Cheatsheet: `results/dc_experiments/test_cold_cheatsheet_20251101.txt`

**Comparison Type**: ✅ **FAIR**
- DC-Cold vs DSPy Baseline (47.4%): Both start with no test knowledge → **DC wins by 1.8%**
- DC-Cold vs DSPy GEPA (45.7%): Both optimize/learn separately → **DC wins by 3.5%**
- DC-Cold vs DSPy MIPROv2 (47.6%): Both optimize/learn separately → **DC wins by 1.6%**
- DC-Cold vs Hybrid (50.2%): DC disadvantage (no format routing) → **Hybrid wins by 1.0%**

---

## ✅ Test 3: Test Set Bootstrapped (COMPLETE)

**Purpose**: Test if dev learning transfers to test set

**Configuration**:
- Dataset: Test (654 questions)
- Cheatsheet: **Bootstrapped from dev** (starts with 3,654 chars)
- Bootstrap file: `dc_cumulative_cold_dev_20251101_153119.json`
- Prompts: Original DC prompts
- Model: qwen2.5-7b-instruct

**Results (Corrected - Nov 7, 2025)**:
- **Accuracy**: **48.5%** (317/654) [was 34.7% before null bug fix]
- **Runtime**: ~4 hours
- **Cost**: ~$0.31
- **Cheatsheet**: Evolved from 3,654 → ~8,500 chars

**Format Breakdown**:
| Format | Accuracy | Correct | Total |
|--------|----------|---------|-------|
| Int | 44.1% | 67 | 152 |
| Float | 41.7% | 40 | 96 |
| Str | 43.1% | 91 | 211 |
| List | 36.4% | 32 | 88 |
| **null** | **81.3%** ✅ | 87 | 107 |

**vs Test Cold Start**: 48.5% vs 49.2% (-0.7%) - **No benefit from bootstrap**

**Files**:
- Results: `results/dc_experiments/dc_cumulative_bootstrap_test_20251101_172109.json`
- Cheatsheet: `results/dc_experiments/test_bootstrap_cheatsheet_20251101.txt`

**Comparison Type**: ⚠️ **PARTIALLY FAIR**
- DC-Bootstrap vs DSPy Baseline: DC has dev advantage → **DC still wins 48.5% vs 47.4%**
- DC-Bootstrap vs DSPy GEPA/MIPROv2: More comparable (both use non-test data)
- Shows that bootstrapping provided no advantage over cold start

---

## ✅ Final Results Summary (Corrected)

### Test Set Performance Comparison

| Approach | Accuracy | vs DSPy Baseline | Status |
|----------|----------|------------------|--------|
| **DSPy Hybrid** | 50.2% | +2.8% | ✅ Best |
| **DC-Cold** | **49.2%** | **+1.8%** | ✅ 2nd Best |
| **DC-Bootstrap** | **48.5%** | **+1.1%** | ✅ |
| **DSPy MIPROv2** | 47.6% | +0.2% | ✅ |
| **DSPy Baseline** | 47.4% | baseline | ✅ |
| **DSPy GEPA** | 45.7% | -1.7% | ⚠️ |

### Key Takeaways

✅ **DC-Cold outperforms all DSPy optimization approaches** except Hybrid  
✅ **DC achieves this with test-time learning only** (no train/dev optimization)  
❌ **Bootstrap provided NO benefit** (48.5% vs 49.2% cold)  
✅ **Evaluation bug fix was critical**: +13.6% accuracy improvement for DC

---

## Key Insights

### 1. Original DC Prompts Better Than "Fair" DSPy-Matching
- DSPy-matching prompts: 25.8% ❌
- Original DC prompts: 43.0% ✅
- **Lesson**: Different approaches need different prompts

### 2. Float Format Strong Performance
- Float: 69.2% on dev (vs DSPy baseline Int/Float ~60-70%)
- Suggests DC good at learning calculation patterns

### 2b. Null Format Bug Fixed ✅ (Was Critical Weakness)
- **Before fix**: DC scored 0% on null format (appeared to struggle)
- **After fix**: DC scores 83-93% on null format (competitive with DSPy)
- **Root cause**: Evaluation bug, not DC prompting/learning issue
- MMESGBench's `eval_score()` treated "null" and "Not answerable" as different
- DC was actually answering correctly, but marked wrong by evaluator
- **Impact**: +13-14% accuracy improvement across all DC runs

### 3. Test-Time Learning Trade-offs
- 2 API calls per question (vs DSPy's 2 for baseline)
- ~13 sec/question (reasonable for learning)
- Cost: 1.5x baseline (2 calls vs DSPy's 2 calls - same!)

### 4. Cheatsheet Quality
- Dev set generated useful 3.6K char cheatsheet
- Covers: terminology, calculations, format tips, pitfalls
- Will test if it transfers to test set

---

## Monitoring Commands

### Check Progress
```bash
# View both logs
tail -f logs/dc_evaluation/dc_eval_*.log

# Check checkpoints
ls -lh results/dc_experiments/*checkpoint*.json

# Count predictions
grep "Checkpoint saved" logs/dc_evaluation/dc_eval_*.log | tail -4
```

### Check if Complete
```bash
# Look for completion message
grep "COMPLETE" logs/dc_evaluation/dc_eval_*.log | tail -2

# Check final results
ls -lt results/dc_experiments/dc_cumulative_cold_test_*.json | head -2
```

### Quick Accuracy Check
```bash
python << 'EOF'
import json
import glob

files = sorted(glob.glob('results/dc_experiments/dc_cumulative_cold_test_*.json'))
for f in files[-2:]:
    with open(f) as fp:
        r = json.load(fp)
        acc = r.get('overall_accuracy', 0)
        total = r.get('total', 0)
        print(f"{f.split('/')[-1]}: {acc:.1%} ({total} questions)")
EOF
```

---

## Timeline

| Time | Event |
|------|-------|
| 15:31 | Test 1 started (dev set, original prompts) |
| 16:05 | Test 1 complete: 43.0% |
| 16:14 | Test 1 re-run (DSPy prompts) started |
| 17:05 | Test 1 re-run complete: 25.8% (worse) |
| 17:17 | **Test 2 started** (test cold) |
| 17:21 | **Test 3 started** (test bootstrap) |
| ~20:30 | Expected: Both tests complete |

---

## Next Steps After Completion

1. **Extract Results**: Parse both test JSON files
2. **Compare Accuracy**: DC-Cold vs DC-Bootstrap vs DSPy approaches
3. **Format Analysis**: Which formats benefit most from cheatsheet?
4. **Learning Curve**: Does accuracy improve over 654 questions?
5. **Statistical Testing**: McNemar's test for significance
6. **Update Documentation**: README, CHANGELOG with final results
7. **Decision**: When to use DC vs DSPy optimization?

---

**Current Status**: Both tests running, expected ~3 hours remaining  
**Next Update**: When tests complete (~20:30-21:00)

