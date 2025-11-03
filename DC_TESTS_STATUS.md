# Dynamic Cheatsheet - Tests Status

**Date**: November 1, 2025, 17:22  
**Status**: Tests 2 & 3 Running in Parallel

---

## ✅ Test 1: Dev Set (COMPLETE)

**Purpose**: Establish baseline & generate reference cheatsheet

**Configuration**:
- Dataset: Dev (93 questions)
- Cheatsheet: Empty (starts blank)
- Prompts: Original DC prompts (not DSPy-matching)

**Results**: 
- **Accuracy**: 43.0% (40/93)
- **Runtime**: 34 minutes (15:31-16:05)
- **Cheatsheet**: 3,654 characters generated

**Format Breakdown**:
| Format | Accuracy | Correct | Total |
|--------|----------|---------|-------|
| Int | 42.1% | 8 | 19 |
| Float | **69.2%** ⭐ | 9 | 13 |
| Str | 50.0% | 17 | 34 |
| List | 46.2% | 6 | 13 |
| **null** | **0.0%** ❌ | 0 | 14 |

**vs DSPy Baseline on Dev**: 43.0% vs 52.7% (-9.7%)

**Files**:
- Results: `results/dc_experiments/dc_cumulative_cold_dev_20251101_153119.json`
- Cheatsheet: Extracted to `results/dc_experiments/dev_cheatsheet_20251101.txt`

**Key Findings**: 
- ⭐ **Float format performs best** (69.2%)
- ❌ **Critical weakness: 0% on null format** - DC struggles to recognize when questions are not answerable

---

## 🔄 Test 2: Test Set Cold Start (IN PROGRESS)

**Purpose**: Fair comparison to DSPy (no prior learning from test)

**Configuration**:
- Dataset: Test (654 questions)
- Cheatsheet: **Blank** (starts empty, learns during test)
- Prompts: Original DC prompts
- Model: qwen2.5-7b-instruct

**Status**: RUNNING
- Started: 17:17:23
- Progress: 10+ questions complete
- Log: `logs/dc_evaluation/dc_eval_20251101_171723.log`

**Expected**:
- Runtime: ~3-4 hours
- Completion: ~20:30-21:00
- Cost: ~$0.31
- Accuracy: 42-46% (similar to dev 43.0%)
- Cheatsheet growth: ~5-10K characters

**Comparison Type**: ✅ **FAIR**
- DC-Cold vs DSPy Baseline (47.4%): Both start with no test knowledge
- DC-Cold vs DSPy GEPA (45.7%): Both optimize/learn separately
- DC-Cold vs Hybrid (50.2%): DC disadvantage (no format routing)

---

## 🔄 Test 3: Test Set Bootstrapped (IN PROGRESS)

**Purpose**: Test if dev learning transfers to test set

**Configuration**:
- Dataset: Test (654 questions)
- Cheatsheet: **Bootstrapped from dev** (starts with 3,654 chars)
- Bootstrap file: `dc_cumulative_cold_dev_20251101_153119.json`
- Prompts: Original DC prompts
- Model: qwen2.5-7b-instruct

**Status**: RUNNING
- Started: 17:21:11
- Progress: Resumed from question 11/654
- Log: `logs/dc_evaluation/dc_eval_20251101_172109.log`

**Expected**:
- Runtime: ~3-4 hours
- Completion: ~20:30-21:00
- Cost: ~$0.31
- Accuracy: 45-50% (better than Test 2 cold)
- Cheatsheet growth: Starts 3.6K → ~7-12K characters

**Comparison Type**: ⚠️ **PARTIALLY FAIR**
- DC-Bootstrap vs DSPy Baseline: DC has dev advantage
- DC-Bootstrap vs DSPy GEPA/MIPROv2: More comparable (both use non-test data)
- Shows value of accumulated domain knowledge

---

## Expected Final Results

### Test 2: Cold Start Predictions

vs DSPy Test Set Results:
| Approach | Accuracy | Difference |
|----------|----------|------------|
| DSPy Baseline | 47.4% | DC: -1 to +2% |
| DSPy MIPROv2 | 47.6% | DC: -1 to +2% |
| DSPy GEPA | 45.7% | DC: -2 to +4% |
| DSPy Hybrid | 50.2% | DC: -4 to -8% |
| **DC-Cold (predicted)** | **42-46%** | - |

**Success Criteria**:
- Minimum: ≥ 42% (not worse than dev)
- Good: 44-46% (matches GEPA/MIPROv2)
- Excellent: ≥ 47% (matches baseline)

### Test 3: Bootstrap Predictions

| Approach | Learning Data | Accuracy (predicted) |
|----------|---------------|---------------------|
| DC-Cold | None (test only) | 42-46% |
| DC-Bootstrap | Dev (93 Q) | 45-50% |
| DSPy GEPA | Train+Dev (279 Q) | 45.7% (actual) |
| DSPy Hybrid | Train+Dev (279 Q) | 50.2% (actual) |

**Success Criteria**:
- Minimum: > Test 2 (+2-3%)
- Good: ≈ 46-48% (beats GEPA)
- Excellent: ≥ 50% (matches Hybrid)

---

## Key Insights

### 1. Original DC Prompts Better Than "Fair" DSPy-Matching
- DSPy-matching prompts: 25.8% ❌
- Original DC prompts: 43.0% ✅
- **Lesson**: Different approaches need different prompts

### 2. Float Format Strong Performance
- Float: 69.2% on dev (vs DSPy baseline Int/Float ~60-70%)
- Suggests DC good at learning calculation patterns

### 2b. Critical Weakness: Null Format (0%)
- **DC got 0/14 (0%) on null format questions**
- Struggles to recognize when questions are not answerable
- May be "trying too hard" to answer from context
- vs DSPy baseline: likely much better on null (typically ~90%+)
- **Major performance drag**: 14 guaranteed wrong answers

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

