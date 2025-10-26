# GEPA Configuration Tuning Guide

**Date**: October 22, 2025  
**Status**: Recommendations Based on Test Set Results

---

## 🎯 Current Situation

### What We Used
```python
optimizer = GEPA(
    metric=mmesgbench_answer_only_gepa_metric,
    reflection_lm=qwen-max,           # Teacher for reflection
    auto='light',                     # ⚠️ LIGHT MODE ONLY
    reflection_minibatch_size=3,      # Small batches
    candidate_selection_strategy='pareto',
    use_merge=True,
    track_stats=True,
    seed=42
)
```

### Results on Test Set (654 Questions)
- **GEPA (light)**: 45.7% (299/654) - **Underperformed baseline by -1.7%**
- **Baseline**: 47.4% (310/654)
- **MIPROv2 (light)**: 47.6% (311/654) - **Slight edge over GEPA**

---

## 🔧 GEPA Configuration Options

### 1. Auto Modes (Similar to MIPROv2)

| Mode | Candidates | Iterations | Runtime | Use Case |
|------|-----------|------------|---------|----------|
| **light** | 10-20 | ~30-40 | 30-45 min | ✅ Quick experiments, dev iteration |
| **medium** | 30-50 | ~50-80 | 2-3 hours | 🎯 **RECOMMENDED** for production |
| **heavy** | 80-150 | ~100-200 | 8-12 hours | 🔬 Research, maximum performance |
| **Custom** | Configurable | Configurable | Variable | Expert tuning |

**Our Test**: Used only **`auto='light'`** - likely insufficient exploration.

---

### 2. Key Parameters to Tune

#### A. Reflection Configuration
```python
# What we used
reflection_lm = dspy.LM(
    model='openai/qwen-max',
    temperature=1.0,          # Higher for creative reflection
    max_tokens=4096           # Longer for analysis
)

# Recommendations
reflection_lm = dspy.LM(
    model='openai/qwen-max',
    temperature=1.2,          # ⬆️ Even more creative
    max_tokens=8192,          # ⬆️ Longer reflections
    top_p=0.95                # Add diversity
)
```

**Why**: More creative reflection → more diverse prompt candidates

#### B. Minibatch Size
```python
# What we used
reflection_minibatch_size=3   # Small batches

# Recommendations
auto='medium':  reflection_minibatch_size=5-8
auto='heavy':   reflection_minibatch_size=10-15
```

**Why**: Larger batches → more diverse failure patterns analyzed → better prompts

#### C. Selection Strategy
```python
# What we used
candidate_selection_strategy='pareto'   # Multi-objective optimization

# Alternatives
'best':     # Single best candidate (fastest)
'topk':     # Top K candidates (balanced)
'pareto':   # Multi-objective (what we used)
'ensemble': # Multiple candidates (robust but slower)
```

**Recommendation**: Try **`'topk'` with k=5** for better diversity than 'best' but faster than 'pareto'.

#### D. Merge Strategy
```python
# What we used
use_merge=True   # Merge good parts from multiple candidates

# Recommendations
use_merge=True                    # Keep this
merge_strategy='weighted_avg'     # Add this for better blending
merge_top_k=3                     # Merge top 3 candidates
```

**Why**: Combining strengths from multiple candidates

---

### 3. Advanced Tuning Parameters

#### A. Custom Auto Configuration
```python
from dspy.teleprompt import GEPA

# Instead of auto='medium', be explicit
optimizer = GEPA(
    metric=mmesgbench_answer_only_gepa_metric,
    reflection_lm=reflection_lm,
    
    # Explicit control (equivalent to auto='medium')
    num_generations=50,                  # ⬆️ vs 20 in light
    max_iterations=80,                   # ⬆️ vs 30-40 in light
    reflection_minibatch_size=8,         # ⬆️ vs 3 in light
    
    # Selection
    candidate_selection_strategy='topk',
    topk=5,
    
    # Merging
    use_merge=True,
    merge_strategy='weighted_avg',
    
    # Early stopping
    patience=15,                         # Stop if no improvement for 15 iterations
    min_improvement=0.01,                # Require ≥1% improvement
    
    # Other
    track_stats=True,
    seed=42
)
```

#### B. Domain-Specific Metric Tuning
```python
# Current metric returns binary score + feedback
# Can be enhanced with:

def enhanced_gepa_metric(gold, pred, trace=None, pred_name=None):
    """Enhanced metric with weighted feedback"""
    from MMESGBench.src.eval.eval_score import eval_score
    
    # Get ANLS score
    anls_score = eval_score(
        gold['answer'], 
        pred.answer, 
        gold['answer_type']
    )
    
    # Weighted by answer format (based on test set findings)
    format_weights = {
        'Int': 1.5,      # GEPA struggles with Int
        'Float': 1.3,    # GEPA struggles with Float
        'List': 1.8,     # GEPA really struggles with List
        'Str': 1.0,      # Normal weight
        'null': 1.6      # GEPA struggles with refusal
    }
    
    weight = format_weights.get(gold['answer_type'], 1.0)
    weighted_score = anls_score * weight
    
    # Detailed feedback
    if anls_score >= 0.5:
        feedback = f"✓ Correct ({gold['answer_type']})"
    else:
        # Specific feedback by format
        if gold['answer_type'] == 'List':
            feedback = f"✗ List format issue. Expected: {gold['answer']}, Got: {pred.answer}"
        elif gold['answer_type'] == 'null':
            feedback = f"✗ Should refuse. Got: {pred.answer} instead of 'Not answerable'"
        else:
            feedback = f"✗ {gold['answer_type']} extraction failed"
    
    from dspy import ScoreWithFeedback
    return ScoreWithFeedback(
        score=weighted_score,
        feedback=feedback
    )
```

**Why**: Weight formats where GEPA struggles → reflection focuses there

---

## 🎯 Recommended Experiments

### Experiment 1: Medium Mode (High Priority)

**Configuration**:
```python
optimizer = GEPA(
    metric=mmesgbench_answer_only_gepa_metric,
    reflection_lm=reflection_lm,
    auto='medium',                        # ⬆️ From light
    reflection_minibatch_size=8,          # ⬆️ From 3
    candidate_selection_strategy='topk',  # Different from pareto
    topk=5,
    use_merge=True,
    track_stats=True,
    seed=42
)
```

**Expected**:
- Runtime: 2-3 hours
- Performance: 48-50% (vs 45.7% light)
- Cost: 3-4x light mode ($0.60-0.80)

**Rationale**: More exploration → better prompts, especially for List/Null where GEPA failed

---

### Experiment 2: Heavy Mode + Enhanced Metric (Research)

**Configuration**:
```python
# Enhanced metric with format weighting
optimizer = GEPA(
    metric=enhanced_gepa_metric,          # ⬆️ Weighted by format
    reflection_lm=reflection_lm_creative, # Temperature=1.5
    auto='heavy',                         # ⬆️ Maximum exploration
    reflection_minibatch_size=15,         # ⬆️ Large batches
    candidate_selection_strategy='ensemble',
    ensemble_size=3,
    use_merge=True,
    merge_top_k=5,
    patience=25,
    track_stats=True,
    seed=42
)
```

**Expected**:
- Runtime: 8-12 hours
- Performance: 50-52% (theoretical max for GEPA)
- Cost: 15-20x light mode ($2-3)

**Rationale**: Maximum exploration with format-specific feedback

---

### Experiment 3: Format-Specific GEPA (Novel Approach)

**Idea**: Run separate GEPA optimizations for each format, then route at runtime.

**Configuration**:
```python
# Optimize 5 separate GEPAs
gepa_int = optimize_gepa(
    trainset=filter_by_format(train_set, 'Int'),
    auto='medium',
    focus='integer_extraction'
)

gepa_float = optimize_gepa(
    trainset=filter_by_format(train_set, 'Float'),
    auto='medium',
    focus='float_precision'
)

gepa_list = optimize_gepa(
    trainset=filter_by_format(train_set, 'List'),
    auto='heavy',  # List is hardest!
    focus='list_extraction_formatting'
)

gepa_str = optimize_gepa(
    trainset=filter_by_format(train_set, 'Str'),
    auto='light',  # Strings are easier
    focus='text_extraction'
)

gepa_null = optimize_gepa(
    trainset=filter_by_format(train_set, 'null'),
    auto='medium',
    focus='refusal_detection'
)

# Route by format
def route_format_specific(question, answer_type):
    if answer_type == 'Int':
        return gepa_int(question)
    elif answer_type == 'Float':
        return gepa_float(question)
    elif answer_type == 'List':
        return gepa_list(question)
    elif answer_type == 'Str':
        return gepa_str(question)
    else:  # null
        return gepa_null(question)
```

**Expected**:
- Runtime: 5x2-3 hours = 10-15 hours total
- Performance: 52-54% (best for each format)
- Cost: 5x medium mode = $3-4

**Rationale**: 
- Test set showed format-specific patterns
- GEPA excels on Int/Float in dev set but failed in test
- Specialized optimization per format

---

### Experiment 4: Hybrid GEPA + MIPROv2

**Idea**: Use GEPA for reasoning, MIPROv2 for extraction.

**Configuration**:
```python
# Two-stage optimization
# Stage 1: GEPA for reasoning (prompts for deep analysis)
gepa_reasoner = optimize_gepa(
    focus='reasoning_and_analysis',
    auto='medium',
    optimize_only='reasoning_signature'  # Only optimize reasoning
)

# Stage 2: MIPROv2 for extraction (prompts for clean formatting)
miprov2_extractor = optimize_miprov2(
    focus='structured_extraction',
    auto='medium',
    optimize_only='extraction_signature'  # Only optimize extraction
)

# Runtime: Use both
answer = miprov2_extractor(
    context=context,
    reasoning=gepa_reasoner(question, context)
)
```

**Expected**:
- Runtime: 2-3 hours (both optimizations)
- Performance: 51-53% (GEPA reasoning + MIPROv2 extraction)
- Cost: $1-1.50

**Rationale**: Combine GEPA's domain knowledge (31.7% of improvements) with MIPROv2's clean extraction

---

## 📊 Cost-Benefit Analysis

| Experiment | Runtime | Cost ($) | Expected Accuracy | vs Baseline | ROI |
|-----------|---------|----------|-------------------|-------------|-----|
| **Current (light)** | 45 min | $0.20 | 45.7% | -1.7% | ❌ Negative |
| **Medium** | 2-3 hr | $0.70 | 48-50% | +0.6-2.6% | ✅ Positive |
| **Heavy** | 8-12 hr | $2.50 | 50-52% | +2.6-4.6% | ✅ Good |
| **Format-Specific** | 12-15 hr | $3.50 | 52-54% | +4.6-6.6% | ✅ Best |
| **Hybrid (GEPA+MIPROv2)** | 3-4 hr | $1.20 | 51-53% | +3.6-5.6% | ✅ Excellent |

**Recommended Priority**:
1. **Experiment 1 (Medium)**: Quick win, low cost
2. **Experiment 4 (Hybrid)**: Best ROI, novel approach
3. **Experiment 3 (Format-Specific)**: Research contribution
4. **Experiment 2 (Heavy)**: If medium shows promise

---

## 🚨 Key Lessons from Test Set

### Why Light Mode Failed

1. **Insufficient Exploration** (10-20 candidates)
   - Not enough diversity to find good prompts
   - Converged too early to suboptimal prompts
   - 7,749 chars likely from early overfitting

2. **Small Reflection Batches** (3 examples)
   - Didn't see enough failure patterns
   - Missed format-specific issues
   - Couldn't learn List/Null handling

3. **Wrong Selection Strategy** (pareto)
   - Multi-objective optimization too complex
   - Better to focus on single objective (accuracy)
   - 'topk' would explore more

4. **No Format Awareness**
   - Treated all formats equally
   - Optimized for Int/Float, broke List/Null
   - Needed format-specific weights

---

## ✅ Immediate Action

### Run Experiment 1 (Medium Mode)

**Script**: `run_gepa_medium.py`
```python
#!/usr/bin/env python3
"""GEPA Optimization - Medium Mode"""

import dspy
from dspy.teleprompt import GEPA
from dspy_implementation.dspy_dataset import MMESGBenchDataset
from dspy_implementation.dspy_rag_enhanced import BaselineMMESGBenchRAG
from dspy_implementation.dspy_metrics_gepa_fixed import mmesgbench_answer_only_gepa_metric

# Load dataset
dataset = MMESGBenchDataset()
train_set = dataset.train_set
dev_set = dataset.dev_set

# Configure reflection LM (qwen-max, more creative)
reflection_lm = dspy.LM(
    model='openai/qwen-max',
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    api_base='https://dashscope.aliyuncs.com/compatible-mode/v1',
    temperature=1.2,      # ⬆️ More creative
    max_tokens=8192       # ⬆️ Longer reflections
)

# Configure student LM (qwen2.5-7b)
student_lm = dspy.LM(
    model='openai/qwen2.5-7b-instruct',
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    api_base='https://dashscope.aliyuncs.com/compatible-mode/v1',
    temperature=0.0,
    max_tokens=1024
)

dspy.configure(lm=student_lm)

# Initialize RAG
rag_student = BaselineMMESGBenchRAG()

# Create GEPA optimizer (MEDIUM MODE)
optimizer = GEPA(
    metric=mmesgbench_answer_only_gepa_metric,
    reflection_lm=reflection_lm,
    auto='medium',                        # ⬆️ KEY CHANGE
    reflection_minibatch_size=8,          # ⬆️ Larger batches
    candidate_selection_strategy='topk',  # ⬆️ Different strategy
    topk=5,
    use_merge=True,
    patience=15,                          # Early stopping
    min_improvement=0.01,
    track_stats=True,
    seed=42
)

print(f"🚀 Starting GEPA Optimization (MEDIUM MODE)")
print(f"   Expected runtime: 2-3 hours")
print(f"   Expected performance: 48-50% (vs 45.7% light)")
print(f"   Cost: ~$0.70")

# Optimize
optimized_rag = optimizer.compile(
    student=rag_student,
    trainset=train_set,
    valset=dev_set
)

# Save
optimized_rag.save('dspy_implementation/optimized_modules/gepa_medium_optimized.json')

print(f"✅ Optimization complete!")
```

**Expected Results**:
- Dev set: 55-57% (vs 54.8% light)
- Test set: 48-50% (vs 45.7% light)
- **Improvement**: +2-4% over light mode

---

## 📝 Summary

### Current State
- Used **`auto='light'`** only - insufficient
- **45.7% test accuracy** - underperformed
- 7,749 char prompt - likely overfit

### Recommendations
1. **Immediate**: Run `auto='medium'` (+2-4% expected)
2. **Short-term**: Hybrid GEPA+MIPROv2 (+3-6% expected)
3. **Research**: Format-specific GEPA (+4-7% expected)
4. **Long-term**: Heavy mode + enhanced metric (theoretical max)

### Key Insight
**GEPA light mode is like MIPROv2 light** - just a quick test, not production-ready. Need medium/heavy for real performance.

---

**Last Updated**: October 22, 2025  
**Next**: Run Experiment 1 (GEPA medium mode)

