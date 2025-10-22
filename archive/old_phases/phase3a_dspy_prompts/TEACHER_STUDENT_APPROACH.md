# Teacher-Student Optimization Approach

## The Problem We Discovered

When testing qwen-max with MIPROv2 optimization, we got **NEGATIVE -3.2% improvement**:
- Baseline: 51.6% → Optimized: 48.4%
- Root cause: Same strong model (qwen-max) used for both optimization AND execution
- Result: Overfitting to 186 training examples

## The Solution: Teacher-Student Split

Use **different models** for different roles:

```
┌─────────────────────────────────────┐
│ TEACHER (qwen-max)                  │
│ - Generates optimized prompts       │
│ - Higher creativity (temp=1.0)      │
│ - Strong reasoning for prompt craft │
└─────────────────────────────────────┘
                 ↓
         [Optimized Prompts]
                 ↓
┌─────────────────────────────────────┐
│ STUDENT (qwen2.5-7b-instruct)       │
│ - Executes RAG with those prompts   │
│ - Consistent (temp=0.0)             │
│ - Benefits from teacher's wisdom    │
└─────────────────────────────────────┘
```

## MIPROv2 Configuration

```python
teacher_lm = dspy.LM(
    model='openai/qwen-max',
    temperature=1.0,  # Creative for prompt generation
    max_tokens=2048
)

student_lm = dspy.LM(
    model='openai/qwen2.5-7b-instruct',
    temperature=0.0,  # Deterministic for task
    max_tokens=1024
)

optimizer = MIPROv2(
    metric=mmesgbench_end_to_end_metric,
    prompt_model=teacher_lm,  # ← Teacher generates prompts
    task_model=student_lm,    # ← Student executes task
    auto="light"
)
```

## Why This Should Work Better

### Previous Approach (Failed)
- **Qwen-max optimizes FOR qwen-max**
- Strong model overfits: Generates complex prompts that work on train but not dev
- Result: -3.2% (worse!)

### New Approach (Expected to Succeed)
- **Qwen-max optimizes FOR qwen2.5-7b**
- Strong teacher generates prompts that help weaker student
- Weaker student NEEDS good prompts (can't overfit like strong model)
- Result: Expected +5-10% improvement

## Hypothesis

**"Strong models benefit weak models through prompt engineering"**

If this works, it means:
1. ✅ Weak models (qwen2.5-7b) benefit from DSPy optimization
2. ✅ Strong teachers (qwen-max) can improve weak students
3. ✅ Cost-effective: 100x cheaper model with good prompts
4. ✅ Publication-worthy: Teacher-student DSPy optimization strategy

## Expected Results

| Scenario | Qwen-max Teacher → qwen2.5-7b Student |
|----------|--------------------------------------|
| **Student Baseline** | ~35-45% (weaker model) |
| **After Teacher Optimization** | ~45-55% (+10% expected) |
| **Improvement Type** | **POSITIVE** (unlike qwen-max self-optimization) |

### Comparison to Previous Results

| Setup | Teacher | Student | Result |
|-------|---------|---------|--------|
| **Previous** | qwen-max | qwen-max | -3.2% ❌ (overfit) |
| **New** | qwen-max | qwen2.5-7b | +5-10% ✅ (expected) |

## Research Implications

**If this works (positive gains):**
- Validates teacher-student DSPy optimization
- Shows strong models should teach, not execute
- Opens path for cost-effective deployment
- Novel contribution: Model role separation in DSPy

**If this fails (negative/zero gains):**
- Teacher prompts don't transfer to weaker models
- May need student-specific optimization
- Suggests fundamental limitations of prompt optimization

## Files

- `dspy_implementation/enhanced_miprov2_qwen7b_optimization.py` - Teacher-student script
- `phase3a_dspy_prompts/TEACHER_STUDENT_APPROACH.md` - This document
- `qwen7b_baseline_evaluation.log` - Student baseline results

## How to Run

### Step 1: Get Student Baseline (Currently Running)
```bash
export QWEN_MODEL=qwen2.5-7b-instruct
python dspy_implementation/evaluate_baseline.py --max-questions 93
```

### Step 2: Run Teacher-Student Optimization
```bash
python dspy_implementation/enhanced_miprov2_qwen7b_optimization.py
```

Expected runtime: ~20-30 minutes
Expected cost: $5-10 (teacher uses qwen-max)

### Step 3: Analyze Results
Compare:
- Student baseline (from Step 1)
- Student with teacher prompts (from Step 2)
- Qwen-max self-optimization (from previous run: -3.2%)

## Key Insight

**The teacher-student approach is fundamentally different:**
- Not testing "weak vs strong model"
- Testing "can strong model TEACH weak model?"
- Proper use of MIPROv2's `prompt_model` vs `task_model` parameters

This is how DSPy optimization SHOULD be used for production:
- Use best model to generate prompts (one-time cost)
- Deploy cheap model with optimized prompts (ongoing savings)
