# Simple Single-Stage Baseline - Rationale

**Date**: November 9, 2025  
**Purpose**: Fair architectural comparison with Dynamic Cheatsheet (DC)

---

## The Problem

The original "DSPy Baseline" (reported as 46.9% test, 53.8% dev) is **not architecturally equivalent** to Dynamic Cheatsheet, making it an unfair comparison.

### DSPy Baseline Architecture (2-stage)

```
Question + Context
   ↓
ChainOfThought Reasoning
   ↓
Separate Answer Extraction
   ↓
Final Answer
```

**LLM Calls**: 2 per question

### DC Architecture (1-stage with learning)

```
Question + Context + Cheatsheet
   ↓
Direct Answer Generation
   ↓
Cheatsheet Update (Curator)
   ↓
Final Answer
```

**LLM Calls**: 1-2 per question (Generator + optional Curator)

---

## The Solution: Simple Single-Stage Baseline

A true single-stage baseline that's architecturally comparable to DC:

```
Question + Context
   ↓
Direct Answer Generation
   ↓
Final Answer
```

**LLM Calls**: 1 per question

### Key Differences

| Aspect | DSPy Baseline (2-stage) | Simple Baseline (1-stage) | DC (1-stage + learning) |
|--------|------------------------|---------------------------|-------------------------|
| **Reasoning Stage** | ✅ Separate CoT | ❌ Direct answer | ❌ Direct answer |
| **Extraction Stage** | ✅ Separate extraction | ❌ Direct answer | ❌ Direct answer |
| **LLM Calls** | 2 calls | 1 call | 1-2 calls |
| **Prompt Length** | ~200 chars (CoT) + ~150 chars (Extraction) | ~400 chars (combined) | ~400-8000 chars (with cheatsheet) |
| **Learning** | ❌ Static | ❌ Static | ✅ Test-time learning |

---

## Why This Matters

### Original Comparison (Unfair)

```
DSPy Baseline (2-stage): 46.9% vs DC-Cold (1-stage): 42.7%
Difference: +4.2%
```

**Problem**: DSPy Baseline uses more sophisticated architecture (2 stages), so the comparison conflates:
1. **Architectural advantage** (2-stage vs 1-stage)
2. **Optimization advantage** (prompt engineering vs test-time learning)

### Fair Comparison (Using Simple Baseline)

```
Simple Baseline (1-stage): ?% vs DC-Cold (1-stage): 42.7%
Difference: ?%
```

**Benefit**: This isolates the effect of:
- **Test-time learning** (DC's cheatsheet accumulation)
- **Prompt quality** (DC's optimized prompts vs basic prompts)

---

## Expected Results

### Hypothesis 1: Simple Baseline < DC

If Simple Baseline scores **lower** than DC (e.g., 38-40%):
- **Implication**: Test-time learning (DC's cheatsheet) provides value
- **Conclusion**: DC's approach has merit, but still lags 2-stage DSPy

### Hypothesis 2: Simple Baseline ≈ DC

If Simple Baseline scores **similar** to DC (e.g., 40-44%):
- **Implication**: Test-time learning provides marginal benefit
- **Conclusion**: Single-stage architecture is the limiting factor

### Hypothesis 3: Simple Baseline > DC

If Simple Baseline scores **higher** than DC (e.g., 45%+):
- **Implication**: DC's cheatsheet may accumulate noise
- **Conclusion**: Simple prompt engineering > test-time learning

---

## Implementation Details

### Signature

```python
class SimpleDirectQA(dspy.Signature):
    """Answer ESG questions from retrieved document context in exact format.
    
    Instructions:
    - Read question and context carefully
    - Extract answer in EXACT format specified
    - Return ONLY final answer, NO explanations
    - For Int: Return only integer (e.g., "42")
    - For Float: Return only number (e.g., "3.14")
    - For Str: Return exact text string (e.g., "Scope 1 emissions")
    - For List: Return valid JSON array (e.g., ["item1", "item2"])
    - For None/unanswerable: Return exactly "Not answerable"
    """
    question: str = dspy.InputField()
    context: str = dspy.InputField()
    answer_format: str = dspy.InputField()
    answer: str = dspy.OutputField()
```

### Module

```python
class SimpleBaselineRAG(dspy.Module):
    def __init__(self):
        super().__init__()
        self.retriever = DSPyPostgresRetriever()
        self.qa = dspy.Predict(SimpleDirectQA)
    
    def forward(self, question, doc_id, answer_format):
        context = self.retriever.retrieve(doc_id, question, top_k=5)
        result = self.qa(question=question, context=context, 
                        answer_format=answer_format)
        return dspy.Prediction(answer=result.answer, context=context)
```

**Key Points**:
- Same retrieval as all other approaches (top-5 chunks)
- Single LLM call per question
- No separate reasoning/extraction stages
- Clear format instructions in signature

---

## Evaluation Status

### Dev Set (93 Questions)

**Status**: 🔄 Running  
**Started**: Nov 9, 2025, 5:00 PM  
**ETA**: ~10 minutes  
**Log**: `logs/simple_baseline_dev.log`

### Test Set (654 Questions)

**Status**: 🔄 Running  
**Started**: Nov 9, 2025, 5:00 PM  
**ETA**: ~60 minutes  
**Log**: `logs/simple_baseline_test.log`

---

## Next Steps

Once evaluations complete:

1. **Compare Simple Baseline vs DC**:
   - Dev: Simple Baseline vs DC-Cold (44.1%)
   - Test: Simple Baseline vs DC-Cold (42.7%)

2. **Update Documentation**:
   - Add Simple Baseline row to all result tables
   - Update README.md with fair comparison
   - Update CHANGELOG.md with rationale

3. **Draw Conclusions**:
   - Is test-time learning beneficial? (DC vs Simple Baseline)
   - Is 2-stage architecture beneficial? (DSPy Baseline vs Simple Baseline)
   - What's the optimal approach? (Hybrid vs everything)

---

## Research Implications

This comparison will help us understand:

1. **Value of architectural complexity**:
   - 2-stage (DSPy Baseline) vs 1-stage (Simple Baseline)

2. **Value of test-time learning**:
   - DC (1-stage + learning) vs Simple Baseline (1-stage + static)

3. **Value of prompt optimization**:
   - DSPy optimization (GEPA/MIPROv2) vs Simple Baseline

4. **Optimal approach for ESG QA**:
   - Architecture, learning strategy, and optimization method

---

## Files

- **Script**: `dspy_implementation/evaluate_simple_baseline.py`
- **Dev Results**: `results/dev_set/simple_baseline_dev_predictions_*.json`
- **Test Results**: `results/test_set/simple_baseline_test_predictions_*.json`
- **Logs**: `logs/simple_baseline_*.log`

---

## Conclusion

The Simple Single-Stage Baseline provides a **fair architectural comparison** with Dynamic Cheatsheet by isolating the effect of test-time learning from architectural complexity. This allows us to draw more meaningful conclusions about the effectiveness of different approaches for ESG question answering.

**Updated**: November 9, 2025

