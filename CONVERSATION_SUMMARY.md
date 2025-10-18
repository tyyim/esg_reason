# Conversation Summary - GEPA Investigation

**Date**: 2025-10-18
**Topic**: Investigating why GEPA performed worse than baseline

---

## 📊 Core Problem

GEPA optimization completed successfully but performed **worse** than the unoptimized baseline:

| Approach | Answer Accuracy | Difference |
|----------|----------------|------------|
| Baseline (no optimization) | 58.1% (54/93) | — |
| MIPROv2 (teacher-student) | 57.0% (53/93) | -1.1% |
| GEPA (reflection) | 54.8% (51/93) | **-3.3%** ⚠️ |

---

## 🎯 User Questions

The user requested investigation into these critical questions:

1. **"Why is baseline so good without any explicit prompt?"**
   - Answer: DSPy's default ChainOfThought prompt is minimal (0 characters!) but effective
   - The two-stage architecture (reasoning → extraction) is well-designed
   - qwen2.5-7b-instruct is capable enough that verbose prompts don't help

2. **"Did the reflective prompt help? It should..."**
   - Answer: **No** - reflection actually hurt performance
   - GEPA's qwen-max reflection evolved a 7,749-character prompt (vs 0 for baseline)
   - The detailed prompt included specific examples (SA8000, CSO, STEM) that may have caused overfitting
   - "Less is more" for this task

3. **"Are there any problems or bias with our dev set or should we use the test set for fair comparison?"**
   - Answer: **Likely yes** - dev set is small (93 questions)
   - 3 questions difference = 3.3% swing
   - **Recommendation**: Evaluate on test set (654 questions) for stable results
   - Status: ⏳ Pending

4. **"Where was our stored program on MIPROv2?"**
   - Answer: ✅ **Found**:
     - Primary: `logs/qwen7b_test/teacher_student_qwen7b_results_20251016_230050.json`
     - MLflow artifact: `mlruns/650826956800499313/5c760978fc75403b8f44818eeea9dfff/artifacts/results/`

5. **"Please perform the prompt comparison and error analysis first, especially on those right→wrong and wrong→right questions"**
   - Status: ✅ **IN PROGRESS**
   - Script: `dspy_implementation/gepa_comprehensive_analysis.py` (running)
   - Current progress: 34% complete (32/93 questions evaluated)
   - Expected completion: ~10 more minutes

---

## 🔍 Analysis Completed So Far

### 1. Prompt Comparison ✅ DONE
**Key Finding**: GEPA dramatically increased prompt length without benefit

**Baseline Prompts**:
- Reasoning: **0 characters** (uses default DSPy ChainOfThought)
- Extraction: 564 characters

**GEPA Prompts**:
- Reasoning: **7,749 characters** (13x longer!)
- Extraction: 564 characters (identical to baseline)

**What GEPA Added**:
- Detailed ESG analysis instructions
- Multi-stage process descriptions
- Specific examples: SA8000 clauses, CSO responsibilities, STEM graduates
- Format requirements and strategy guidelines
- Domain-specific factual information

**Interpretation**: GEPA only optimized the reasoning prompt, making it 13x longer. This likely confused the model rather than helping it.

### 2. Found MIPROv2 Program Location ✅ DONE
Located in `logs/qwen7b_test/teacher_student_qwen7b_results_20251016_230050.json`

**MIPROv2 Results**:
```json
{
  "dev_results": {
    "answer_accuracy": 0.5698924731182796  // 57.0%
  }
}
```

### 3. Question-Level Analysis ⏳ IN PROGRESS
**Script**: `gepa_comprehensive_analysis.py` (running in background)

**What it will provide**:
- Baseline vs GEPA predictions for all 93 dev questions
- Right→Wrong transitions (baseline correct, GEPA wrong)
- Wrong→Right transitions (baseline wrong, GEPA correct)
- Error patterns by answer format (Str/Float/List/Int)
- Detailed examples of degradation cases

**Current Status**: Evaluating baseline (32/93 complete, ~34%)

---

## 📝 Deliverables Created

### Documentation
1. ✅ [GEPA_INVESTIGATION_SUMMARY.md](phase3a_dspy_prompts/GEPA_INVESTIGATION_SUMMARY.md)
   - Technical investigation details
   - Theories about why GEPA failed
   - Next steps

2. ✅ [GEPA_FINDINGS_FOR_NOTION.md](GEPA_FINDINGS_FOR_NOTION.md)
   - Research-ready summary
   - Formatted for Notion update
   - Includes insights and lessons learned

3. ✅ This conversation summary (CONVERSATION_SUMMARY.md)

### Analysis Scripts
1. ✅ [gepa_comprehensive_analysis.py](dspy_implementation/gepa_comprehensive_analysis.py)
   - Compares prompts: Baseline vs GEPA vs MIPROv2
   - Evaluates both baseline and GEPA on dev set
   - Identifies right→wrong and wrong→right transitions
   - Generates detailed question-level analysis report

### Existing GEPA Implementation
1. ✅ [gepa_qwen7b_optimization.py](dspy_implementation/gepa_qwen7b_optimization.py)
   - Full GEPA optimization (with baseline evaluation)

2. ✅ [gepa_skip_baseline.py](dspy_implementation/gepa_skip_baseline.py)
   - Fast mode (skips redundant baseline eval)
   - Saves 10-15 minutes per run

3. ✅ [dspy_metrics_gepa_fixed.py](dspy_implementation/dspy_metrics_gepa_fixed.py)
   - ScoreWithFeedback with `__add__` and `__radd__` methods
   - Fixes TypeError that blocked GEPA

---

## 💡 Key Insights

### Finding 1: Baseline is Strong
**58.1% without optimization** is surprisingly good.

**Reasons**:
- DSPy's default ChainOfThought works well
- Two-stage architecture (reason → extract) is intuitive
- qwen2.5-7b-instruct is capable

### Finding 2: GEPA Over-Specified Prompts
**7,749 characters vs 0 characters** - more is not better.

**Problems**:
- Specific examples (SA8000, CSO) may cause overfitting
- Verbose instructions add cognitive load
- Model gets confused by too much detail

### Finding 3: Reflection Can Be Wrong
**GEPA selected "best" program that was actually worst.**

**Questions**:
- Did qwen-max correctly identify failure modes?
- Were proposed improvements actually improvements?
- Can textual feedback be misleading?

### Finding 4: Small Dev Sets Are Noisy
**93 questions → 3 questions = 3.3% swing**

**Solution**: Validate on test set (654 questions)

---

## ⏳ Next Steps

### Immediate (Today)
1. ✅ Create comprehensive analysis script
2. ⏳ **Wait for analysis to complete** (~10 min remaining)
3. ⏳ Review right→wrong and wrong→right patterns
4. ⏳ Check if errors cluster by format (Str/Float/List/Int)
5. ⏳ Update Notion research proposal with findings

### Short-Term (This Week)
6. ⏳ Evaluate all three approaches on **test set** (654 questions)
7. ⏳ Manually review GEPA's reflection logs
8. ⏳ Test hypothesis: Remove specific examples from GEPA prompt
9. ⏳ Clean up codebase and sync with GitHub

### Research Questions
- Is GEPA fundamentally flawed for RAG tasks?
- Are teacher-student optimizers better than reflection?
- Should we try GEPA with different hyperparameters?
- Is the baseline just too good to optimize?

---

## 📊 Files Generated This Session

### Analysis
- `gepa_comprehensive_analysis.py` - Prompt comparison & error analysis script (running)
- `gepa_analysis_YYYYMMDD_HHMMSS.json` - Will contain question-level results (pending)

### Documentation
- `phase3a_dspy_prompts/GEPA_INVESTIGATION_SUMMARY.md` - Technical summary
- `GEPA_FINDINGS_FOR_NOTION.md` - Research findings for Notion
- `CONVERSATION_SUMMARY.md` - This file

### Logs
- `logs/gepa_optimization/gepa_comprehensive_analysis.log` - Analysis run log

---

## 🎓 Lessons Learned

### Technical
1. **ScoreWithFeedback needs arithmetic operators**: `__add__` and `__radd__` for DSPy evaluation
2. **Python cache matters**: Clear `.pyc` files when code changes don't take effect
3. **Zombie processes**: Kill background processes to avoid database connection issues
4. **Timestamped logs**: Make experiment tracking much easier

### Research
1. **Measure baseline first**: Know what you're trying to beat
2. **Small datasets are noisy**: 93 questions is not enough for stable comparison
3. **Trust but verify**: "Best" program may not actually be best
4. **Prompt length ≠ quality**: Shorter can be better

### Optimization
1. **Reflection can mislead**: qwen-max's feedback needs validation
2. **Over-specification hurts**: Detailed examples cause overfitting
3. **Architecture > Prompts**: Two-stage design matters more than prompt details
4. **Time is real**: 75 minutes for 3.3% degradation is expensive

---

## 🔄 Status Update

**Current Activity**:
- Comprehensive analysis script running in background
- Evaluating baseline predictions (32/93 complete)
- Will then evaluate GEPA predictions
- Will compare and identify patterns
- Expected completion: ~10 minutes

**Next Action** (when analysis completes):
1. Review question-level results
2. Extract degradation patterns
3. Update Notion research proposal
4. Clean up and sync codebase with GitHub

**User can expect**:
- Detailed JSON report with all predictions
- Right→Wrong and Wrong→Right examples
- Format-specific error patterns
- Actionable insights for next steps

---

**Last Updated**: 2025-10-18 17:00
**Analysis Status**: ⏳ Running (34% complete)
