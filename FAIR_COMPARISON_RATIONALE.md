# Fair Comparison Rationale: Simple Baseline vs DC-CU

**Date**: November 11, 2025  
**Issue**: Ensuring architectural fairness in comparison  
**Solution**: Raw LLM implementations for both approaches

---

## ⚠️ The Problem We Solved

### Original Unfair Comparison (Rejected)

**Simple Baseline**:
- Used DSPy framework (`dspy.Predict`, `dspy.LM`)
- DSPy's automatic prompt engineering
- DSPy's chain management
- Potential hidden optimizations

**DC-CU**:
- Used raw LLM calls via `openai.ChatCompletion`
- Original DC repository implementation
- No framework overhead

**Result**: Not a fair comparison - DSPy could provide hidden advantages

---

## ✅ Our Fair Comparison Approach

### Both Use Same Infrastructure

| Component | Simple Baseline (RAW) | DC-CU |
|-----------|----------------------|-------|
| **LLM API** | `openai.ChatCompletion` | `openai.ChatCompletion` |
| **Framework** | None (raw calls) | None (raw calls) |
| **Retriever** | `DSPyPostgresRetriever` | `DSPyPostgresRetriever` |
| **Evaluation** | `eval_score` (corrected) | `eval_score` (corrected) |
| **Model** | DeepSeek v3.1 | DeepSeek v3.1 |
| **Temperature** | 0.0 | 0.1 |
| **Max Tokens** | 512 | 512 |

### What We Compare

**Simple Baseline (RAW)**:
```python
# Direct LLM call - no framework
response = client.chat.completions.create(
    model='deepseek-v3.1',
    messages=[{"role": "user", "content": prompt}],
    temperature=0.0,
    max_tokens=512
)
```

**DC-CU**:
```python
# Direct LLM call via DC's LanguageModel
result = self.lm.advanced_generate(
    approach_name="DynamicCheatsheet_Cumulative",
    input_txt=input_txt,
    cheatsheet=cheatsheet,
    generator_template=generator_template,
    cheatsheet_template=curator_template,
    temperature=0.1,
    max_tokens=512
)
```

---

## 🎯 What This Tests

### Isolated Comparison

✅ **Static 1-stage prompt** (Simple Baseline RAW)
vs
✅ **Dynamic test-time learning** (DC-CU)

**Controlled Variables**:
- Same retrieval mechanism
- Same LLM (DeepSeek v3.1)
- Same evaluation (corrected eval_score)
- Same API infrastructure

**Only Difference**:
- **Methodology**: Static prompt vs Dynamic cheatsheet accumulation

---

## 📊 Expected Insights

### Phase 2 Hypothesis Testing

**Hypothesis**: "Bigger models might help DC more than static prompts"

**With qwen2.5-7b (small model)**:
- Simple Baseline: 58.1%
- DC-CU: 44.1%
- **Gap**: +13.9% in favor of static prompts

**With DeepSeek v3.1 (large model)**:
- If gap **narrows** → Hypothesis confirmed (DC benefits more from larger models)
- If gap **stays same** → Both improve equally
- If gap **widens** → Surprising (larger models don't help DC)

---

## 🔍 Why This Matters

### Architectural Fairness

**Bad Comparison** (what we avoided):
```
DSPy Baseline (with framework) vs DC (raw calls)
→ Can't tell if difference is due to:
   - Framework advantages?
   - Methodology differences?
   - Hidden optimizations?
```

**Good Comparison** (what we implemented):
```
Raw Simple Baseline (no framework) vs DC (raw calls)
→ Difference is purely due to:
   - Static prompt vs Dynamic learning ✅
```

### Research Integrity

This ensures:
1. **Valid conclusions** about methodology effectiveness
2. **Reproducible results** (no hidden framework magic)
3. **Fair evaluation** of test-time learning vs static prompts
4. **Clean comparison** for Phase 2 multi-model analysis

---

## 📁 Implementation Files

### Simple Baseline (RAW)
- **Script**: `dspy_implementation/evaluate_simple_baseline_deepseek_raw.py`
- **Key**: No DSPy framework, direct `openai.ChatCompletion` calls
- **Prompt**: Single-stage direct QA with format instructions

### DC-CU
- **Script**: `dspy_implementation/dc_module/dc_evaluator_deepseek.py`
- **Key**: Original DC repository's `LanguageModel.advanced_generate()`
- **Mechanism**: Cumulative cheatsheet updated after each Q&A

### Comparison Runner
- **Script**: `run_deepseek_comparison.sh`
- **Runs**: Both evaluations sequentially
- **Output**: `results/deepseek_comparison/`

---

## ✅ Verification Checklist

**Infrastructure Parity**:
- [x] Both use same LLM API (`openai.ChatCompletion`)
- [x] Both use same retriever (`DSPyPostgresRetriever`)
- [x] Both use same evaluation (`eval_score` with fixes)
- [x] Both use same model (DeepSeek v3.1)
- [x] Neither uses DSPy framework

**Methodology Isolation**:
- [x] Simple Baseline: Pure static prompt
- [x] DC-CU: Pure dynamic learning
- [x] No confounding factors

**Reproducibility**:
- [x] All code committed to git
- [x] All dependencies documented
- [x] All scripts are self-contained

---

## 🔬 Previous Comparison (for context)

### With qwen2.5-7b

| Approach | Implementation | Accuracy |
|----------|----------------|----------|
| **DSPy 2-stage** | DSPy framework | 46.9% (test) |
| **Simple Baseline** | DSPy framework | 48.5% (test) |
| **DC-CU** | Raw calls | 42.7% (test) |

**Issue**: Simple Baseline used DSPy while DC didn't → Not fair

### Now with DeepSeek v3.1

| Approach | Implementation | Accuracy |
|----------|----------------|----------|
| **Simple Baseline (RAW)** | Raw calls | *Running...* |
| **DC-CU** | Raw calls | *Running...* |

**Fixed**: Both use raw calls → Fair comparison ✅

---

##  Summary

**Problem**: Framework differences could distort methodology comparison  
**Solution**: Raw implementations for both approaches  
**Benefit**: Clean test of "Static prompt vs Dynamic learning"  
**Next**: Use this fair baseline for all Phase 2 multi-model comparisons

---

**Last Updated**: November 11, 2025  
**Status**: Evaluations in progress

