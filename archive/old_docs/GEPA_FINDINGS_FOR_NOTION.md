# GEPA Optimization Findings

**Research Question**: Can reflective prompt evolution (GEPA) outperform teacher-student optimization (MIPROv2) for ESG question answering?

**Short Answer**: ❌ **No** - GEPA performed worse than both baseline and MIPROv2

---

## 📊 Results Summary

| Approach | Method | Answer Accuracy | vs Baseline | Runtime |
|----------|--------|----------------|-------------|---------|
| **Baseline** | Default DSPy prompts | **58.1%** (54/93) | — | ~8 min |
| **MIPROv2** | Teacher-student | 57.0% (53/93) | -1.1% | ~45 min |
| **GEPA** | Reflection-based | **54.8%** (51/93) | **-3.3%** ⚠️ | ~75 min |

**Dataset**: MMESGBench dev set (93 questions)
**Model**: qwen2.5-7b-instruct (student), qwen-max (teacher/reflection)
**Metric**: Answer accuracy (ANLS 0.5 threshold)

---

## 🔍 Key Findings

### Finding 1: Baseline is Surprisingly Strong
**Without any optimization**, the default DSPy prompts achieved 58.1% accuracy.

**Why?**
- DSPy's default ChainOfThought is minimal but effective
- qwen2.5-7b-instruct is capable enough that verbose prompts don't help
- Two-stage architecture (reasoning → extraction) is well-designed

**Evidence**:
- Baseline reasoning prompt: **0 characters** (uses default CoT)
- GEPA reasoning prompt: **7,749 characters** (13x longer)
- GEPA extraction prompt: **564 characters** (identical to baseline!)

**Interpretation**: "Less is more" for this task. Verbose instructions may confuse rather than clarify.

### Finding 2: GEPA Over-Specified the Reasoning Prompt
GEPA's reflection mechanism (qwen-max) evolved a massive, detailed prompt that actually hurt performance.

**GEPA Prompt Includes** (from 32 iterations of reflection):
1. Detailed ESG analysis instructions
2. Multi-stage extraction process description
3. **Specific examples**: SA8000 clauses, CSO responsibilities, STEM graduates
4. Format requirements (Str/Float/None)
5. General strategy guidelines
6. Domain-specific factual information

**Problem**: These specific examples (SA8000, CSO, STEM) may have caused overfitting:
- Model focuses on memorized examples
- Generalizes poorly to other ESG topics
- Adds cognitive load without benefit

### Finding 3: Reflection Mechanism May Have Misdiagnosed Failures
GEPA ran successfully for 32 iterations, but selected a program that performed worse than baseline.

**From GEPA Logs**:
```
Completed 32 iterations
Best dev set score: 0.5483870967741935 (54.8%)
Selected Program #4 as best program
```

**Questions**:
1. Why did qwen-max think Program #4 was "best"?
2. Did reflection correctly identify failure modes?
3. Were the proposed improvements actually improvements?

**Hypothesis**: qwen-max's textual feedback may have been misleading:
- Identified symptoms, not root causes
- Proposed overly specific fixes (SA8000 examples)
- Optimized for training set, not dev set

### Finding 4: Both Optimizers Struggled vs Baseline
**Neither** MIPROv2 nor GEPA improved on the baseline:
- MIPROv2: -1.1% (likely noise on small dev set)
- GEPA: -3.3% (significant degradation)

**Possible Explanations**:
1. **Baseline is near-optimal**: DSPy defaults are already excellent
2. **Task is simple enough**: qwen2.5-7b doesn't need fancy prompts
3. **Dev set is too small**: 93 questions → high variance (3 questions = 3.3%)
4. **Optimization overfits**: Both methods learned training set, not general patterns

---

## 🧩 Why Did GEPA Fail?

### Theory 1: Over-Optimization (Most Likely)
**Explanation**: GEPA evolved highly specific prompts that work on training examples but don't generalize.

**Supporting Evidence**:
- Baseline (generic): 58.1%
- GEPA (specific examples): 54.8%
- Prompt length: 0 → 7,749 characters

**Analogy**: Like memorizing exam answers vs understanding concepts.

### Theory 2: Small Dev Set Creates Noise
**Explanation**: 3 question difference is only 3.3% on 93 examples - may not be statistically significant.

**Supporting Evidence**:
- Dev set: 93 questions (small)
- Test set: 654 questions (7x larger)
- Improvement needed: +1 question = +1.1%

**Next Step**: Validate on test set for stable comparison.

### Theory 3: Reflection Feedback Was Misleading
**Explanation**: qwen-max analyzed failures but proposed incorrect fixes.

**Supporting Evidence**:
- GEPA selected "best" program that was worse than baseline
- Specific examples (SA8000, CSO) may have been red herrings
- Feedback-driven evolution can compound errors

**Analogy**: Like debugging by guessing instead of logging.

### Theory 4: DSPy Baseline Is Already Near-Optimal
**Explanation**: Default ChainOfThought prompt is excellent for ESG QA.

**Supporting Evidence**:
- Baseline: 58.1% with minimal prompt
- All optimizations made it worse
- Adding detail ≠ adding value

**Implication**: This task may not benefit from optimization.

---

## 📈 Comparison: MIPROv2 vs GEPA

| Aspect | MIPROv2 (Teacher-Student) | GEPA (Reflection) |
|--------|--------------------------|-------------------|
| **Metric Return** | `float` only | `ScoreWithFeedback` (score + feedback) |
| **Feedback Signal** | Scalar score | Rich textual feedback |
| **Prompt Evolution** | Teacher proposes candidates | Reflection LM analyzes failures |
| **Selection** | Best candidates | Pareto frontier |
| **Result** | -1.1% (54→53) | **-3.3%** (54→51) ⚠️ |
| **Runtime** | ~45 min | ~75 min |

**Surprising Result**: Despite richer feedback, GEPA performed worse than MIPROv2.

**Possible Reasons**:
1. Textual feedback can be misleading
2. Reflection overfitted to specific examples
3. Teacher-student learns from demonstrations (more robust)

---

## ⏳ Next Steps

### Immediate Actions
1. ✅ Complete comprehensive analysis (running)
2. ⏳ Identify right→wrong and wrong→right question patterns
3. ⏳ Analyze if degradations cluster by answer format (Str/Float/List/Int)
4. ⏳ Check if specific documents cause failures

### Short-Term Validation
5. ⏳ **Evaluate on test set** (654 questions) for statistical significance
6. ⏳ Manually review GEPA's reflection logs to understand proposals
7. ⏳ Test hypothesis: Remove specific examples from GEPA prompt
8. ⏳ Compare MIPROv2 prompts to understand why it also degraded

### Research Directions
9. ⏳ Try GEPA with different hyperparameters (e.g., max prompt length limit)
10. ⏳ Test if reflection works better on harder tasks
11. ⏳ Investigate why baseline is so strong - is it the architecture or the model?

---

## 💡 Insights for Research

### For ESG Question Answering
1. **Two-stage architecture works**: Reasoning → Extraction is effective
2. **qwen2.5-7b is capable**: Doesn't need verbose prompts
3. **Retrieval is critical**: 75.3% retrieval accuracy limits final performance
4. **Domain examples can hurt**: Specific examples (SA8000) may cause overfitting

### For DSPy Optimization
1. **Baseline matters**: Always measure unoptimized performance first
2. **Small dev sets are risky**: 93 questions → 3.3% variance per question
3. **More prompting ≠ better**: 7,749 chars worse than 0 chars
4. **Reflection can mislead**: Textual feedback needs validation

### For Future Work
1. **Focus on retrieval**: 75.3% → 90%+ would help more than prompt optimization
2. **Test on larger datasets**: 654-question test set for stable results
3. **Consider simpler approaches**: Baseline is hard to beat
4. **Ablation studies**: What components of GEPA/MIPROv2 actually help?

---

## 📁 Deliverables

### Code
- ✅ GEPA implementation ([gepa_qwen7b_optimization.py](dspy_implementation/gepa_qwen7b_optimization.py))
- ✅ Fast mode skip baseline ([gepa_skip_baseline.py](dspy_implementation/gepa_skip_baseline.py))
- ✅ Comprehensive analysis ([gepa_comprehensive_analysis.py](dspy_implementation/gepa_comprehensive_analysis.py))
- ✅ Fixed GEPA metrics ([dspy_metrics_gepa_fixed.py](dspy_implementation/dspy_metrics_gepa_fixed.py))

### Documentation
- ✅ GEPA fix summary ([GEPA_FIX_SUMMARY.md](phase3a_dspy_prompts/GEPA_FIX_SUMMARY.md))
- ✅ GEPA approach ([GEPA_APPROACH.md](phase3a_dspy_prompts/GEPA_APPROACH.md))
- ✅ Investigation summary ([GEPA_INVESTIGATION_SUMMARY.md](phase3a_dspy_prompts/GEPA_INVESTIGATION_SUMMARY.md))
- ✅ Configuration ([config_gepa_qwen7b.yaml](phase3a_dspy_prompts/config_gepa_qwen7b.yaml))

### Results
- ✅ GEPA optimized program ([gepa_skip_baseline_20251018_150806.json](dspy_implementation/optimized_programs/gepa_skip_baseline_20251018_150806.json))
- ✅ GEPA run logs ([logs/gepa_optimization/](logs/gepa_optimization/))
- ⏳ Question-level analysis (pending)
- ⏳ Test set validation (pending)

---

## 🎓 Lessons Learned

### Technical
1. **ScoreWithFeedback requires `__add__`**: DSPy's evaluator needs summable metrics
2. **Reflection ≠ Improvement**: qwen-max's feedback can be wrong
3. **Prompt length ≠ Performance**: Shorter prompts can outperform longer ones
4. **Optimization time is real**: 75 minutes for 3.3% degradation

### Research
1. **Measure baseline first**: 58.1% was already strong
2. **Small datasets are noisy**: Need test set validation
3. **Trust but verify**: GEPA "selected best" but it was worst
4. **Architecture > Prompts**: Two-stage design matters more than prompt details

### Practical
1. **Skip redundant baselines**: Saves 10-15 minutes per run
2. **Use timestamped logs**: Easier to track experiments
3. **Monitor background processes**: Zombie connections cause issues
4. **Clear Python cache**: Old .pyc files can cause confusing errors

---

## 📚 References

- **GEPA Paper**: "Reflective Prompt Evolution Can Outperform Reinforcement Learning" (Agrawal et al., 2025, arxiv:2507.19457)
- **GEPA GitHub**: https://github.com/gepa-ai/gepa
- **DSPy Docs**: https://dspy.ai/api/optimizers/GEPA/overview/
- **MMESGBench**: ESG document QA benchmark (933 questions, 45 documents)

---

**Status**: Analysis running, detailed question-level results pending.

**Date**: 2025-10-18
**Authors**: Research Team
**Experiment**: GEPA vs MIPROv2 vs Baseline on MMESGBench
