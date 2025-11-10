# Simple Single-Stage Baseline Results

**Date**: November 9, 2025  
**Model**: qwen2.5-7b-instruct  
**Architecture**: Single-stage direct QA (like DC)  
**Status**: ✅ Evaluations Complete

---

## Summary

The Simple Single-Stage Baseline provides a fair architectural comparison with Dynamic Cheatsheet (DC), using the same single-stage architecture without separate reasoning and extraction steps.

### Results

| Dataset | Questions | Accuracy | Correct | Notes |
|---------|-----------|----------|---------|-------|
| **Dev Set** | 93 | **58.1%** | 54/93 | Fair reference for DC-Cold (44.1%) |
| **Test Set** | 654 | **48.5%** | 317/654 | Fair reference for DC-Cold (42.7%) |

---

## Key Findings

### 1. **Simple Baseline Outperforms DC**

**Dev Set Comparison**:
- Simple Baseline: **58.1%** (54/93)
- DC-Cold: 44.1% (41/93)
- **Gap**: +14.0% in favor of Simple Baseline

**Test Set Comparison**:
- Simple Baseline: **48.5%** (317/654)
- DC-Cold: 42.7% (279/654)
- **Gap**: +5.8% in favor of Simple Baseline

**Interpretation**: Even with the same single-stage architecture, a well-prompted direct QA approach (Simple Baseline) outperforms DC's test-time learning.

### 2. **2-Stage Architecture Provides Limited Value (Dev Set)**

**Dev Set**:
- DSPy 2-stage Baseline: 53.8% (50/93)
- Simple 1-stage Baseline: **58.1%** (54/93)
- **Gap**: +4.3% in favor of Simple Baseline

**Test Set**:
- DSPy 2-stage Baseline: 46.9% (307/654)
- Simple 1-stage Baseline: **48.5%** (317/654)
- **Gap**: +1.6% in favor of Simple Baseline

**Interpretation**: The 2-stage architecture (Reasoning + Extraction) provides minimal or even negative value compared to a single, well-designed direct QA prompt. The separation may introduce errors or dilute focus.

### 3. **Test-Time Learning Has Limited Impact**

DC's core advantage is supposed to be test-time learning (accumulating knowledge via cheatsheet), yet:

**No Learning (Simple Baseline)**: 48.5%
**With Learning (DC-Cold)**: 42.7%
**Gap**: -5.8%

**Interpretation**: The cheatsheet accumulation approach in DC is not providing value on MMESGBench. Possible reasons:
1. Noisy cheatsheet content
2. Poor retrieval/synthesis of relevant knowledge
3. ESG domain requires precise extraction, not general patterns
4. 7B model struggles to maintain effective cheatsheet

### 4. **Prompt Optimization Still Valuable (Dev Set)**

**Simple Baseline (no optimization)**: 58.1% (dev)
**DSPy GEPA (optimized 2-stage)**: 61.3% (dev)
**Gap**: +3.2%

**Test Set** (dev→test generalization):
**Simple Baseline**: 48.5% (test)
**DSPy GEPA**: 46.3% (test)
**Gap**: -2.2% (GEPA overfits to dev)

**Interpretation**: Prompt optimization (GEPA) helps on dev set but overfits. Simple, general prompts may generalize better.

---

## Comprehensive Rankings

### Dev Set (93 Questions)

| Rank | Approach | Architecture | Accuracy | vs Simple Baseline | Notes |
|------|----------|--------------|----------|--------------------|-------|
| 1 | **DSPy GEPA** | 2-stage + optimization | **61.3%** | +3.2% | Best dev, likely overfits |
| 2 | **Simple Baseline** | 1-stage direct | **58.1%** | baseline | Fair to DC |
| 3 | DSPy Baseline | 2-stage | 53.8% | -4.3% | More complex architecture |
| 4 | DSPy MIPROv2 | 2-stage + optimization | 52.7% | -5.4% | Teacher-student doesn't help |
| 5 | DC-Cold | 1-stage + learning | 44.1% | -14.0% ❌ | Test-time learning underperforms |

### Test Set (654 Questions)

| Rank | Approach | Architecture | Accuracy | vs Simple Baseline | Notes |
|------|----------|--------------|----------|--------------------|-------|
| 1 | **Hybrid (Format-Based)** | Format-specific routing | **50.2%** | +1.7% ✅ | Best overall |
| 2 | **Simple Baseline** | 1-stage direct | **48.5%** | baseline | Fair to DC |
| 3 | DSPy MIPROv2 | 2-stage + optimization | 47.4% | -1.1% | Competitive |
| 4 | DSPy Baseline | 2-stage | 46.9% | -1.6% | 2-stage costs performance |
| 5 | DSPy GEPA | 2-stage + optimization | 46.3% | -2.2% | Overfits to dev |
| 6 | DC-Bootstrap | 1-stage + learning | 43.7% | -4.8% ❌ | Bootstrap didn't help |
| 7 | DC-Cold | 1-stage + learning | 42.7% | -5.8% ❌ | Test-time learning underperforms |

---

## Insights for Paper

### What We Learned

1. **Architectural Complexity ≠ Better Performance**
   - Simpler 1-stage direct prompts can outperform complex 2-stage (Reasoning + Extraction) pipelines
   - Each additional stage introduces error risk and attention dilution

2. **Test-Time Learning Doesn't Always Help**
   - DC's cheatsheet accumulation underperforms even no-learning baselines
   - Domain-specific tasks (ESG extraction) may benefit more from precise prompts than accumulated patterns

3. **Prompt Optimization Has Limits**
   - GEPA helps on dev (+3.2%) but overfits to test (-2.2% vs Simple)
   - Generic, well-designed prompts may generalize better than heavily optimized ones

4. **Format-Specific Routing is Key**
   - Hybrid approach (50.2%) is still the best
   - Different answer types (Int, Float, Str, List, null) may benefit from different strategies

### Recommendations for Phase 2 (Novel Methodology)

Based on these findings, the proposed **Dynamic Knowledge Distillation (DKD)** should:

1. **Keep Architecture Simple**: Start with 1-stage, add stages only if proven necessary
2. **Focus on Knowledge Quality**: DC's weakness is noisy cheatsheet → DKD should extract clean, structured patterns
3. **Format-Specific Learning**: Don't accumulate generic knowledge → learn format-specific extraction strategies
4. **Test Generalization Early**: Avoid optimizing too hard on dev set → validate on test frequently

---

## Technical Details

### Prompt Used (Simple Baseline)

The Simple Baseline uses a single `SimpleDirectQA` signature:

```python
class SimpleDirectQA(dspy.Signature):
    """Answer ESG questions from retrieved document context in the exact specified format.
    
    Instructions:
    - Read the question and context carefully
    - Extract the answer in the EXACT format specified
    - Return ONLY the final answer, NO explanations or reasoning
    - For Int: Return only the integer (e.g., "42")
    - For Float: Return only the number (e.g., "3.14" or "10.5")
    - For Str: Return only the exact text string (e.g., "Scope 1 emissions")
    - For List: Return valid JSON array (e.g., ["item1", "item2"])
    - For None/unanswerable: Return exactly "Not answerable"
    """
    question: str = dspy.InputField(desc="The ESG question to answer")
    context: str = dspy.InputField(desc="Retrieved document context from ESG reports")
    answer_format: str = dspy.InputField(desc="Required answer format: Int, Float, Str, List, or None")
    answer: str = dspy.OutputField(desc="ONLY the final answer in the specified format, NO explanations")
```

### Evaluation Settings

- **Retrieval**: PostgreSQL + pgvector, top-5 chunks, same as all baselines
- **Embeddings**: text-embedding-v4 (DashScope)
- **LLM**: qwen2.5-7b-instruct, temperature=0.1, max_tokens=512
- **Evaluation**: Corrected eval_score (null equivalence + ANLS string bug fixed)

---

## Next Steps

1. ✅ **Fix script crash** (TypeError with None key in format_breakdown)
2. ✅ **Document results** (this file)
3. 🔄 **Update comparison tables** in README.md, RESEARCH_FINDINGS.md
4. 🔄 **Prepare for Phase 2** (DKD design with these insights)

---

**Conclusion**: The Simple Single-Stage Baseline provides a crucial fair comparison point. It demonstrates that:
1. DC's test-time learning underperforms even basic static prompts
2. Architectural complexity (2-stage) doesn't guarantee better performance
3. Format-specific routing (Hybrid) remains the best approach
4. Our proposed DKD must address these insights to achieve meaningful improvements

**Last Updated**: November 9, 2025

