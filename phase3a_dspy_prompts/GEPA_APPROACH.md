# GEPA Optimization Approach

## What is GEPA?

**GEPA (Genetic-Pareto)** is a reflective optimizer from "GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning" (Agrawal et al., 2025).

### Key Innovation: Reflective Prompt Evolution

Unlike traditional optimizers that only use scalar scores, GEPA uses **rich textual feedback** to guide optimization:

1. **Execute** task with current prompts
2. **Analyze** failures with detailed feedback (not just score)
3. **Reflect** using strong LM to understand what went wrong
4. **Propose** improved instructions based on insights
5. **Evolve** prompts through Pareto-based selection

## Architecture: GEPA vs MIPROv2 Teacher-Student

### MIPROv2 Teacher-Student (Previous Test)

```
┌──────────────────────────────────────┐
│ MIPROv2 Optimizer                    │
│                                      │
│  Teacher (prompt_model):             │
│    qwen-max                          │
│    ↓                                 │
│    Generates optimized prompts       │
│    ↓                                 │
│  Student (task_model):               │
│    qwen2.5-7b                        │
│    ↓                                 │
│    Executes with teacher prompts     │
│                                      │
│  Metric: Returns float score         │
└──────────────────────────────────────┘
```

**Result**: 54.8% → 57.0% (+2.2% ✅)

### GEPA (Current Test)

```
┌──────────────────────────────────────┐
│ GEPA Optimizer                       │
│                                      │
│  Task LM:                            │
│    qwen2.5-7b (executes)             │
│    ↓                                 │
│  Metric:                             │
│    Returns {"score": float,          │
│             "feedback": str}         │
│    ↓                                 │
│  Reflection LM:                      │
│    qwen-max (analyzes feedback)      │
│    ↓                                 │
│    Reads detailed failure reasons    │
│    ↓                                 │
│    Proposes improved instructions    │
│    ↓                                 │
│  Pareto Selection:                   │
│    Non-dominated candidates          │
│    ↓                                 │
│  Evolved Prompts                     │
└──────────────────────────────────────┘
```

**Expected**: Similar or better improvement than MIPROv2

## Key Differences

| Feature | MIPROv2 | GEPA |
|---------|---------|------|
| **Prompt Generation** | Teacher model separate | Reflection LM integrated |
| **Metric Format** | Float score only | Score + feedback |
| **Optimization Signal** | Score comparison | Textual feedback analysis |
| **Selection Strategy** | Best candidates | Pareto frontier |
| **Feedback Loop** | Implicit | Explicit & interpretable |

## Rich Feedback Example

### MIPROv2 Metric (Score Only)
```python
def metric(example, pred, trace):
    return 0.5  # Just a number
```

### GEPA Metric (Score + Feedback)
```python
def metric(gold, pred, trace, pred_name, pred_trace):
    return {
        "score": 0.5,
        "feedback": """
        ❌ INCORRECT: Both retrieval and answer need improvement.

        Question: What is Microsoft's 2024 carbon emissions target?
        Answer Type: Float

        🔍 RETRIEVAL ISSUE:
          Required pages: [12, 15]
          Retrieved pages: [10, 11]
          ❌ Missing pages: [12, 15]
          → Query generation needs to target sustainability sections

        🎯 ANSWER ISSUE:
          Ground truth: 50000.0
          Predicted: Not found
          → Once correct pages retrieved, extract numeric value only

        💡 RECOMMENDATION:
          1. Improve query to find pages 12, 15
          2. Once found, extract numeric emissions target
        """
    }
```

**Impact**: Reflection LM (qwen-max) reads this detailed feedback and proposes:
- Better query formulation strategies
- Improved answer extraction instructions
- Specific fixes for observed failure patterns

## Configuration

### Reflection LM (qwen-max)
```python
reflection_lm = dspy.LM(
    model='openai/qwen-max',
    temperature=1.0,  # Higher for creative proposals
    max_tokens=4096   # Longer for detailed analysis
)
```

### Task LM (qwen2.5-7b)
```python
task_lm = dspy.LM(
    model='openai/qwen2.5-7b-instruct',
    temperature=0.0,  # Deterministic for evaluation
    max_tokens=1024
)
```

### GEPA Optimizer
```python
optimizer = GEPA(
    metric=mmesgbench_answer_only_gepa_metric,  # Returns feedback
    reflection_lm=reflection_lm,  # qwen-max for reflection
    auto='light',  # Budget mode
    reflection_minibatch_size=3,  # Examples per reflection
    candidate_selection_strategy='pareto',  # Non-dominated selection
    use_merge=True,  # Combine good components
    track_stats=True,  # Return detailed statistics
    seed=42  # Reproducibility
)
```

## Expected Outcomes

### Hypothesis 1: GEPA ≥ MIPROv2
- **MIPROv2 Result**: +2.2% (54.8% → 57.0%)
- **GEPA Target**: ≥+2.2% improvement
- **Rationale**: Textual feedback provides richer optimization signal

### Hypothesis 2: Interpretability
- GEPA's reflection process is more interpretable
- Can inspect what the reflection LM learned from failures
- Easier to debug and understand optimization

### Hypothesis 3: Efficiency
- Fewer iterations needed with rich feedback
- More targeted prompt improvements
- Potentially faster convergence

## Success Criteria

✅ **Primary**: Answer accuracy improvement ≥ +2.2%
✅ **Secondary**: Optimization time ≤ MIPROv2 (~35 min)
✅ **Tertiary**: Interpretable reflection insights

## Files

**Implementation**:
- `dspy_implementation/gepa_qwen7b_optimization.py` - Main script
- `dspy_implementation/dspy_metrics_gepa.py` - Feedback metrics

**Configuration**:
- `phase3a_dspy_prompts/config_gepa_qwen7b.yaml` - GEPA config

**Results** (after run):
- `gepa_qwen7b_results_YYYYMMDD_HHMMSS.json` - Results
- `logs/gepa_test/gepa_optimization.log` - Execution log

## Running the Experiment

```bash
# Activate environment
conda activate esg_reasoning

# Run GEPA optimization
python dspy_implementation/gepa_qwen7b_optimization.py 2>&1 | tee logs/gepa_test/gepa_optimization.log

# Expected runtime: ~30-45 minutes (light mode)
# Expected improvement: ≥+2.2% answer accuracy
```

## Research Implications

If GEPA shows **better or equal results** to MIPROv2:
- Validates reflective prompt evolution approach
- Demonstrates value of rich textual feedback
- Opens path for more interpretable optimization

If GEPA shows **worse results**:
- Score-based optimization may be sufficient
- Feedback quality matters (not just presence)
- May need better feedback engineering

**Either way**: Valuable comparison for publication!

## References

- **Paper**: "GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning" (Agrawal et al., 2025, arxiv:2507.19457)
- **DSPy Docs**: https://dspy.ai/api/optimizers/GEPA/overview/
- **Previous Work**: Teacher-Student MIPROv2 (+2.2%, Oct 16 2025)
