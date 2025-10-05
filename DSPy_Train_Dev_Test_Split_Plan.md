# DSPy Optimization: Train/Dev/Test Split Strategy (REVISED)

## 📋 Executive Summary

**Date**: 2025-10-05 (Revised)
**Phase**: Phase 1 - DSPy/GEPA Optimization
**Baseline Performance**: 41.3% accuracy (385/933 questions) - ColBERT baseline with MMESGBench evaluation
**Total Dataset**: 933 questions from MMESGBench

## 🎯 Split Design Philosophy

### Core Principles
1. **Generous Training Set**: 20% training data (186 questions) provides robust examples for DSPy optimization
2. **Evidence Type Focus**: Stratify primarily by evidence type (Pure-text, Table, Chart, Image, Generalized-text)
3. **Difficulty Balance**: Include Easy/Medium/Hard examples based on baseline performance
4. **Large Test Set**: 70% test set maintains statistical significance and comparability
5. **Preserve Baseline Comparability**: Enable direct comparison with MMESGBench baselines

### Optimization Metric Decision

**APPROVED: Optimize on ACCURACY only**

**Rationale**:
- MMESGBench paper reports **accuracy** as primary metric
- Current baseline (41.3%) and target (41.5%) both use accuracy
- Simpler optimization objective reduces overfitting risk
- Enables direct comparison with MMESGBench baselines and other approaches

**F1 as Secondary Metric**: Report F1 for completeness but don't optimize on it directly

---

## 📊 Final Split Configuration

### **20/10/70 Split (Approved)**
```
Train:  186 questions (~20%)  - For DSPy/GEPA prompt optimization
Dev:     93 questions (~10%)  - For validation during optimization
Test:   654 questions (~70%)  - For final evaluation and comparison
```

**Justification**:
- **Train (186)**: Sufficient examples for learning complex reasoning patterns across all evidence types
- **Dev (93)**: Robust validation set for monitoring optimization progress
- **Test (654)**: Large test set ensures statistical significance (±1.9% margin at 95% CI)
- **Total train+dev (279)**: Within DSPy recommended range (30-300), prevents overfitting
- **Training coverage**: ~12-26 examples per evidence type per difficulty level

---

## 📊 Stratification Strategy: Evidence Type × Difficulty

### Difficulty Definition (Proxy from 41.3% Baseline)

**Difficulty Levels** assigned by sorting questions within each evidence type by baseline score:
- **Easy**: Top 1/3 by score (highest performing questions)
- **Medium**: Middle 1/3 by score
- **Hard**: Bottom 1/3 by score (lowest performing questions)

### Evidence Type Performance Analysis

| Evidence Type     | Total | Correct | Accuracy | Overall Difficulty |
|-------------------|-------|---------|----------|-------------------|
| Pure-text         | 394   | 172     | 43.7%    | Medium            |
| Generalized-text  | 226   | 96      | 42.5%    | Medium            |
| Image             | 90    | 33      | 36.7%    | Medium            |
| Table             | 122   | 43      | 35.2%    | Medium            |
| Chart             | 101   | 28      | 27.7%    | Hard              |

### Complete Evidence Type × Difficulty Matrix

| Evidence Type       | Difficulty | Total | Train | Dev  | Test |
|---------------------|------------|-------|-------|------|------|
| Pure-text           | Easy       | 131   | 26    | 13   | 92   |
| Pure-text           | Medium     | 131   | 26    | 13   | 92   |
| Pure-text           | Hard       | 132   | 26    | 13   | 93   |
| Table               | Easy       | 40    | 8     | 4    | 28   |
| Table               | Medium     | 40    | 8     | 4    | 28   |
| Table               | Hard       | 42    | 8     | 4    | 30   |
| Chart               | Easy       | 33    | 6     | 3    | 24   |
| Chart               | Medium     | 33    | 6     | 3    | 24   |
| Chart               | Hard       | 35    | 7     | 3    | 25   |
| Image               | Easy       | 30    | 6     | 3    | 21   |
| Image               | Medium     | 30    | 6     | 3    | 21   |
| Image               | Hard       | 30    | 6     | 3    | 21   |
| Generalized-text    | Easy       | 75    | 15    | 7    | 53   |
| Generalized-text    | Medium     | 75    | 15    | 7    | 53   |
| Generalized-text    | Hard       | 76    | 15    | 7    | 54   |
| **TOTAL**           |            | **933** | **184** | **90** | **659** |

**Note**: Actual totals (184/90/659) differ slightly from target (186/93/654) due to rounding in stratified sampling

### Stratification Summary

**Evidence Type Coverage in Training Set**:
- Pure-text: 78 questions (42.4%)
- Generalized-text: 45 questions (24.5%)
- Table: 24 questions (13.0%)
- Chart: 19 questions (10.3%)
- Image: 18 questions (9.8%)

**Difficulty Balance in Training Set**:
- Easy: ~61 questions (33%)
- Medium: ~61 questions (33%)
- Hard: ~62 questions (34%)

---

## 🔧 Stratified Sampling Strategy

### Sampling Method: **Evidence Type × Difficulty Proportional Sampling**

```python
# Pseudo-code for sampling strategy
for each evidence_type in [Pure-text, Table, Chart, Image, Generalized-text]:
    # Get all questions for this evidence type
    questions = filter_by_evidence_type(evidence_type)

    # Sort by baseline score (descending)
    questions.sort(by=baseline_score, reverse=True)

    # Divide into difficulty terciles
    n = len(questions)
    easy = questions[0 : n//3]
    medium = questions[n//3 : 2*n//3]
    hard = questions[2*n//3 : n]

    # Sample from each difficulty level
    for difficulty_level in [easy, medium, hard]:
        n_train = int(len(difficulty_level) × 0.20)
        n_dev = int(len(difficulty_level) × 0.10)
        n_test = len(difficulty_level) - n_train - n_dev

        # Random sample with constraints:
        # 1. Maintain evidence type × difficulty proportions
        # 2. Ensure document diversity (max 2 questions per doc in train/dev)
        # 3. Randomize within difficulty level to avoid bias
```

### Key Constraints

**Document Diversity**:
- **Train**: Max 2 questions per document (ensures coverage across 45 docs)
- **Dev**: Max 2 questions per document
- **Test**: Remaining questions distributed naturally
- **Rationale**: Prevents overfitting to specific document styles

**Random Seed**:
- Use fixed seed (42) for reproducibility
- All experiments use same train/dev/test splits for fair comparison

**No Answer Format Stratification**:
- Answer format distribution naturally maintained through evidence type stratification
- Focus on evidence type ensures multimodal reasoning coverage

---

## 📈 Expected Outcomes & Success Criteria

### Phase 1 Goals
1. **Baseline Maintenance**: Test accuracy ≥ 41.3% (current ColBERT baseline)
2. **Optimization Target**: Test accuracy ≥ 42-43% (+0.7-1.7% improvement to match/exceed 41.5% MMESGBench target)
3. **Evidence Type Improvements**:
   - Chart: 27.7% → 30-32% (hardest category, biggest opportunity)
   - Table: 35.2% → 37-39% (numeric reasoning improvement)
   - Image: 36.7% → 38-40% (visual understanding enhancement)
4. **Generalization**: Dev accuracy within ±1% of test accuracy (no overfitting)
5. **Sample Efficiency**: Demonstrate improvement with only 186 training examples (~20% of data)

### DSPy/GEPA Optimization Metrics
- **Primary**: Test set accuracy (compare to 41.3% baseline)
- **Secondary**: F1 score, evidence-type specific accuracy
- **Efficiency**: Training cost (API tokens), optimization time, convergence speed
- **Robustness**: Performance variance across random seeds, generalization gap (dev vs test)

---

## 🚀 Implementation Plan

### Step 1: Create Stratified Splits (Week 1)
```bash
python create_stratified_splits.py \
  --input MMESGBench/dataset/samples.json \
  --baseline_results optimized_full_dataset_mmesgbench_with_f1.json \
  --output splits/ \
  --strategy evidence_difficulty \
  --train_ratio 0.20 \
  --dev_ratio 0.10 \
  --test_ratio 0.70 \
  --seed 42
```

**Outputs**:
- `splits/train.json` (~186 questions) - Stratified by Evidence Type × Difficulty
- `splits/dev.json` (~93 questions) - Stratified by Evidence Type × Difficulty
- `splits/test.json` (~654 questions) - Remaining questions
- `splits/split_analysis.json` - Distribution verification report
- `splits/difficulty_assignments.json` - Question-level difficulty labels

### Step 2: Validate Split Quality (Week 1)
```bash
# Verify stratification quality
python validate_splits.py --splits_dir splits/

# Automated checks:
# 1. Evidence type distribution matches proportions (±2%)
# 2. Difficulty distribution balanced across Easy/Medium/Hard (±3%)
# 3. Document diversity (max 2 questions per doc in train/dev)
# 4. No data leakage between splits
# 5. Answer format naturally balanced (not explicitly stratified)
# 6. Train+dev size within DSPy range (30-300)
```

### Step 3: Baseline Evaluation on Splits (Week 1)
```bash
# Evaluate current ColBERT baseline on all splits
python evaluate_baseline_on_splits.py \
  --model colbert_mmesgbench_baseline \
  --splits_dir splits/ \
  --evaluation_method mmesgbench_exact

# Expected results (based on 41.3% overall):
# - Train: ~41% (should match overall, validates split quality)
# - Dev: ~41% (should match overall)
# - Test: ~41% (should match overall)
# - Evidence type breakdown by split
```

### Step 4: DSPy Optimization (Week 2-3)
```bash
# Run GEPA optimization on training set
python dspy_optimize.py \
  --train splits/train.json \
  --dev splits/dev.json \
  --optimizer GEPA \
  --metric accuracy \
  --max_iterations 20 \
  --target_accuracy 0.425 \
  --focus_evidence_types Chart,Table,Image

# Expected optimization time: 3-6 hours (186 train + 93 dev examples)
# Expected API cost: $10-25 (based on Qwen API pricing)
# Monitor dev set performance to prevent overfitting
```

### Step 5: Final Evaluation (Week 3)
```bash
# Evaluate optimized model on test set
python evaluate_optimized_model.py \
  --model dspy_gepa_optimized \
  --test_set splits/test.json \
  --evaluation_method mmesgbench_exact \
  --output results/phase1_dspy_final_results.json

# Report all metrics:
# - Overall accuracy (compare to 41.3% baseline)
# - Evidence-type specific accuracy (focus on Chart/Table/Image improvements)
# - Difficulty-level performance (Easy/Medium/Hard breakdown)
# - F1 score
# - Generalization gap (dev vs test)
# - Statistical significance (bootstrap CI)
```

---

## 📋 Quality Assurance Checklist

### Pre-Optimization Validation
- [ ] Split distributions match Evidence Type × Difficulty proportions (±2% tolerance)
- [ ] No data leakage between train/dev/test
- [ ] Document diversity maintained (max 2 per doc in train/dev)
- [ ] Baseline evaluation on splits matches expected ~41.3%
- [ ] Difficulty terciles balanced (Easy/Medium/Hard ~33% each)
- [ ] Train+dev size within DSPy range (184+90=274, target 30-300) ✓

### During Optimization
- [ ] Monitor dev set accuracy after each GEPA iteration
- [ ] Track optimization metrics (accuracy improvements, convergence)
- [ ] Document prompt evolution and reasoning chain changes
- [ ] Early stopping if dev accuracy plateaus or decreases
- [ ] Monitor evidence-type specific performance (focus on Chart/Table)

### Post-Optimization Evaluation
- [ ] Test accuracy ≥ 41.3% (baseline maintenance)
- [ ] Dev-test accuracy gap < 2% (generalization check)
- [ ] Evidence-type improvements documented (Chart, Table, Image priority)
- [ ] Statistical significance testing (bootstrap CI, p-value vs baseline)
- [ ] Comparison table: Baseline vs Optimized (overall + evidence-type breakdown)

---

## 🔍 Implementation Details

### Difficulty Assignment Method

**Approach**: Performance-based terciles within each evidence type

**Why this works**:
1. **Data-driven**: Uses actual baseline performance (41.3% evaluation results)
2. **Evidence-specific**: Accounts for different difficulty distributions across modalities
3. **Balanced**: Ensures ~33% Easy, ~33% Medium, ~33% Hard across dataset
4. **No manual annotation**: Automated based on `score` field from baseline results

**Process**:
```python
for evidence_type in [Pure-text, Table, Chart, Image, Generalized-text]:
    questions = get_questions_by_evidence_type(evidence_type)
    questions.sort(by='baseline_score', descending=True)

    easy_questions = top_third(questions)      # Highest scores
    medium_questions = middle_third(questions) # Middle scores
    hard_questions = bottom_third(questions)   # Lowest scores
```

### Why Not Stratify by Answer Format?

**Rationale**:
1. **Evidence type is more fundamental**: Determines reasoning complexity (text vs visual vs tabular)
2. **Answer format is secondary**: String/Int/Float/List reflect output type, not input complexity
3. **Natural distribution preserved**: Stratifying by evidence type automatically maintains reasonable answer format balance
4. **Simplicity**: 5×3=15 cells vs 5×5×3=75 cells if both dimensions stratified
5. **Focus on research goal**: Multimodal reasoning (evidence types) is core research question

### Comparison: Our Difficulty Method vs MMESGBench Paper

**MMESGBench Paper Approach** (Section 3.3):
- **Method**: LLM assigns difficulty during QA generation based on reasoning depth + modality complexity
- **Categories**: Easy, Medium, Difficult
- **Philosophy**: Intrinsic task complexity (prospective assessment)

**Our Performance-Based Approach**:
- **Method**: Sort questions by baseline score within each evidence type, divide into terciles
- **Categories**: Easy (top 1/3), Medium (middle 1/3), Hard (bottom 1/3)
- **Philosophy**: Extrinsic difficulty relative to baseline model (empirical assessment)

**Why Our Approach is Appropriate for DSPy Optimization**:
1. **Calibrated to baseline**: Difficulty is relative to the 41.3% baseline we're optimizing from
2. **Data-driven**: Uses actual performance rather than predicted complexity
3. **No additional annotation**: Automated from existing evaluation results
4. **Balanced by design**: Guarantees ~33% distribution in each difficulty level
5. **Optimization-relevant**: Questions that are hard for the baseline are priority targets for DSPy improvement

---

## 📊 Comparison to MMESGBench Paper

### How MMESGBench Reports Results

**From paper analysis**:
- MMESGBench reports on **full 933-question dataset** (no train/test split mentioned)
- Baselines: Sequential (20%), ColBERT Text (41.5%), ColPali Visual (51.8%)
- Evaluation: Accuracy with fuzzy matching, numeric tolerance
- **No mention of optimization or few-shot learning**

### Our Approach Difference

**Why we need splits**:
1. **DSPy requires training data**: GEPA optimizer needs examples to evolve prompts
2. **Prevent overfitting**: Need held-out dev set for validation
3. **Fair comparison**: Test on large unseen set (747 questions = 80%)
4. **Reproducibility**: Fixed splits enable consistent comparison

**Maintaining comparability**:
- Use same evaluation metrics (accuracy + F1)
- Test set large enough for statistical comparison
- Report on full dataset after optimization for direct comparison
- Document any performance differences between split-based and full-dataset evaluation

---

## 💡 Recommendations

### **Primary Recommendation: Option A (Conservative Split)**

**Rationale**:
1. ✅ **Balanced**: 10/10/80 split is standard for small-medium datasets
2. ✅ **DSPy-friendly**: 93 train + 93 dev = 186 total within recommended 30-300 range
3. ✅ **Statistical power**: 747 test questions provides robust evaluation
4. ✅ **Format coverage**: ~15-30 examples per format in training
5. ✅ **Prevents overfitting**: Large test set ensures generalization

### **Optimization Metric: Accuracy Only**

**Rationale**:
1. ✅ **Direct comparability**: MMESGBench paper uses accuracy
2. ✅ **Simpler objective**: Less risk of multi-objective optimization conflicts
3. ✅ **Strong correlation**: F1 and accuracy highly correlated in our baseline
4. ✅ **Report F1 anyway**: Include as secondary metric for completeness

### **Next Steps**

1. **Create splits** using stratified sampling (Option A)
2. **Validate quality** with statistical tests
3. **Baseline evaluation** on splits to verify ~45% performance
4. **Begin DSPy optimization** with GEPA on training set
5. **Monitor dev performance** to prevent overfitting
6. **Final test evaluation** and comparison to baseline

---

## 📚 References

- **DSPy Documentation**: Recommends 30-300 examples for optimization
- **MMESGBench Paper**: 933 questions, accuracy-based evaluation
- **Notion Research Proposal**: Phase 1 DSPy integration plan
- **Current Baseline**: 45.1% accuracy (421/933) with ColBERT + DSPy

---

**Document Version**: 1.0
**Last Updated**: 2025-10-05
**Status**: Ready for Implementation
