# GEPA Investigation Summary

**Date**: 2025-10-18
**Status**: 🔍 **Under Investigation** - GEPA performed worse than baseline

---

## 📊 Executive Summary

GEPA (reflective prompt optimization) performed **WORSE** than baseline:

| Approach | Answer Accuracy | Change | Runtime |
|----------|----------------|--------|---------|
| **Baseline** (no optimization) | 58.1% (54/93) | — | ~8 min |
| **MIPROv2** (teacher-student) | 57.0% (53/93) | -1.1% | ~45 min |
| **GEPA** (reflection) | 54.8% (51/93) | **-3.3%** ⚠️ | ~75 min |

**Critical Questions**:
1. Why is baseline so good without any explicit prompt optimization?
2. Did reflection prompts help? (They were supposed to!)
3. Is the dev set biased? Should we use test set instead?
4. What patterns explain right→wrong and wrong→right transitions?

---

## 🔍 Investigation Plan

### Phase 1: Prompt Comparison ✅ IN PROGRESS
**Script**: [gepa_comprehensive_analysis.py](../dspy_implementation/gepa_comprehensive_analysis.py)

**Comparing**:
- Baseline prompts (default DSPy)
- GEPA prompts (reflection-optimized)
- MIPROv2 prompts (teacher-student optimized)

**Questions**:
- What do the default DSPy prompts look like?
- How did GEPA's reflection change them?
- Are GEPA's prompts over-specified?

### Phase 2: Question-Level Error Analysis ⏳ PENDING
**Goal**: Identify degradation patterns

**Analysis Categories**:
1. ✅→❌ **Baseline Right → GEPA Wrong** (degradation cases)
2. ❌→✅ **Baseline Wrong → GEPA Right** (improvement cases)
3. ✅→✅ **Both Right** (stable good performance)
4. ❌→❌ **Both Wrong** (stable failures)

**Looking for**:
- Question types that GEPA breaks (String? Float? List?)
- Documents GEPA struggles with
- Patterns in GEPA's failures

### Phase 3: Dev vs Test Set Validation ⏳ PENDING
**Hypothesis**: Dev set (93 questions) may be biased or too small

**Action**: Evaluate all three approaches on **test set** (654 questions)
- Baseline on test set
- GEPA on test set
- Compare distributions

**Expected**: More stable, less noisy results with larger test set

### Phase 4: Reflection Analysis ⏳ PENDING
**Goal**: Understand what qwen-max reflection LM proposed

**Questions**:
- What did qwen-max suggest during GEPA's 32 iterations?
- Did reflection identify the right failure modes?
- Were the proposed prompt improvements actually improvements?

---

## 📈 Current Findings

### Finding 1: Baseline is surprisingly strong
**Observation**: 58.1% accuracy with NO optimization

**Hypotheses**:
1. **DSPy default prompts are already good** for ESG QA
2. **qwen2.5-7b is strong enough** that prompts don't matter much
3. **Task is well-scoped**: Two-stage reasoning+extraction is intuitive

**Evidence**:
- Baseline prompts (from [gepa_comprehensive_analysis.py](../dspy_implementation/gepa_comprehensive_analysis.py)):
  - Reasoning: ❓ **NOT FOUND** (may be using minimal ChainOfThought default)
  - Extraction: ~564 chars (concise extraction instructions)

- GEPA prompts:
  - Reasoning: **7,749 chars** (massive, detailed ESG analysis guide)
  - Extraction: **564 chars** (identical to baseline!)

**Key Insight**: GEPA only changed the reasoning prompt, not extraction. The reasoning prompt became **13x longer**.

### Finding 2: GEPA's prompt may be over-specified
**Observation**: GEPA reasoning prompt has 7,749 characters vs 0 for baseline

**GEPA Reasoning Prompt Includes**:
- Detailed ESG analysis instructions
- Multi-stage extraction process description
- Specific examples for SA8000, CSO, STEM graduates
- Format requirements (Str/Float/None)
- General strategy guidelines
- Domain-specific factual information

**Hypothesis**: The extremely detailed prompt may:
1. **Confuse the model** with too much context
2. **Overfitt** to specific examples (SA8000, CSO, STEM)
3. **Slow down reasoning** with verbose instructions
4. **Introduce noise** in the chain-of-thought

### Finding 3: GEPA ran 32 iterations successfully
**From logs** ([gepa_skip_baseline_20251018_150802.log](../logs/gepa_optimization/gepa_skip_baseline_20251018_150802.log)):

```
2025/10/18 15:08:04 INFO Completed 32 iterations
2025/10/18 15:08:04 INFO Best dev set score: 0.5483870967741935 (54.8%)
2025/10/18 16:24:54 INFO Selected Program #4 as best program
2025/10/18 16:33:54 INFO Final eval: 51.0 / 93 (54.8%)
```

**Observations**:
- ✅ GEPA completed all iterations without errors
- ✅ Selected "best" program from 32 candidates
- ❌ Best program was worse than unoptimized baseline
- ❌ 32 iterations consumed ~1 hour 14 minutes

**Question**: Why did GEPA's reflection think Program #4 was best if it performed worse?

---

## 🧩 Puzzle: Why Did GEPA Fail?

### Theory 1: Over-optimization
**Explanation**: GEPA evolved prompts that work well on training examples but generalize poorly

**Evidence**:
- Detailed, specific examples embedded in prompt (SA8000, CSO, STEM)
- May have overfitted to training distribution

**Test**: Evaluate GEPA on test set (654 questions) - should show different performance

### Theory 2: Reflection LM (qwen-max) misdiagnosed failures
**Explanation**: qwen-max analyzed failures incorrectly and proposed bad fixes

**Evidence**:
- GEPA degraded performance instead of improving it
- Reflection feedback may have been misleading

**Test**: Manually inspect GEPA logs for reflection proposals during optimization

### Theory 3: DSPy baseline prompts are already near-optimal
**Explanation**: The default ChainOfThought prompt is already excellent for this task

**Evidence**:
- Baseline achieved 58.1% with minimal prompt
- Adding detail made it worse

**Test**: Compare baseline prompt text - is it actually "minimal" or surprisingly good?

### Theory 4: Small dev set (93 questions) creates noise
**Explanation**: 3 questions difference (54→51) is only 3.3% on 93 questions

**Evidence**:
- Small sample size = high variance
- 51/93 vs 54/93 may not be statistically significant

**Test**: Evaluate on test set (654 questions) - larger sample reduces noise

---

## 🔬 Next Steps

### Immediate (Today)
1. ✅ Run comprehensive analysis script ← **IN PROGRESS**
2. ⏳ Compare baseline vs GEPA prompts in detail
3. ⏳ Analyze right→wrong and wrong→right question patterns
4. ⏳ Identify if degradations cluster by format (Str/Float/List/Int)

### Short-term (This Week)
5. ⏳ Evaluate all three approaches on **test set** (654 questions)
6. ⏳ Manual review of GEPA's reflection logs
7. ⏳ Test hypothesis: Remove detailed examples from GEPA prompt
8. ⏳ Update Notion research proposal with findings

### Research Questions
- **Q1**: Is GEPA's reflection mechanism fundamentally flawed for this task?
- **Q2**: Are teacher-student optimizers (MIPROv2) better for RAG tasks?
- **Q3**: Should we try GEPA with different hyperparameters (e.g., shorter prompts)?
- **Q4**: Is the baseline just unexpectedly good, making optimization hard?

---

## 📁 Files

**GEPA Optimized Program**:
- [gepa_skip_baseline_20251018_150806.json](../dspy_implementation/optimized_programs/gepa_skip_baseline_20251018_150806.json)

**GEPA Run Log**:
- [gepa_skip_baseline_20251018_150802.log](../logs/gepa_optimization/gepa_skip_baseline_20251018_150802.log)

**MIPROv2 Results**:
- [teacher_student_qwen7b_results_20251016_230050.json](../logs/qwen7b_test/teacher_student_qwen7b_results_20251016_230050.json)

**Analysis Scripts**:
- [gepa_comprehensive_analysis.py](../dspy_implementation/gepa_comprehensive_analysis.py)
- [gepa_skip_baseline.py](../dspy_implementation/gepa_skip_baseline.py)

**Documentation**:
- [GEPA_FIX_SUMMARY.md](./GEPA_FIX_SUMMARY.md) - How we fixed the TypeError
- [GEPA_APPROACH.md](./GEPA_APPROACH.md) - GEPA methodology
- [config_gepa_qwen7b.yaml](./config_gepa_qwen7b.yaml) - Configuration

---

## 💡 Lessons Learned (So Far)

1. **Baseline performance matters**: 58.1% without optimization is strong
2. **More prompting ≠ better performance**: 7,749 chars < 0 chars
3. **Small dev sets are noisy**: 3 questions = 3.3% swing on 93 examples
4. **Reflection can be wrong**: qwen-max may have misdiagnosed failures
5. **Optimization time is real**: GEPA took 75 minutes for worse results

---

**Status**: Analysis running, results pending. Will update with question-level findings.

**Last Updated**: 2025-10-18 16:50
