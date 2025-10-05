# DSPy Optimization: Train/Dev/Test Split Strategy

## 📋 Executive Summary

**Date**: 2025-10-05
**Phase**: Phase 1 - DSPy/GEPA Optimization
**Baseline Performance**: 45.1% accuracy (421/933 questions) - ColBERT + DSPy baseline
**Total Dataset**: 933 questions from MMESGBench

## 🎯 Split Design Philosophy

### Core Principles
1. **Sample Efficiency**: DSPy is designed to work with 30-300 training examples (per DSPy documentation)
2. **Stratified Sampling**: Balance across answer formats, evidence types, and difficulty
3. **Large Test Set**: Maintain statistical significance by keeping majority of data for final evaluation
4. **Preserve Baseline Comparability**: Test on same full dataset (933 questions) as MMESGBench for fair comparison

### Optimization Metric Decision

**Recommended: Optimize on ACCURACY only**

**Rationale**:
- MMESGBench paper reports **accuracy** as primary metric
- Current baseline (45.1%) and target (41.5%) both use accuracy
- F1 score correlation with accuracy is high (~41.5% F1 vs 45.1% accuracy)
- Simpler optimization objective reduces overfitting risk
- Enables direct comparison with MMESGBench baselines and other approaches

**F1 as Secondary Metric**: Report F1 for completeness but don't optimize on it directly

---

## 📊 Proposed Split Configuration

### **Option A: Conservative Split (Recommended)**
```
Train:  93 questions  (10%)  - For DSPy/GEPA prompt optimization
Dev:    93 questions  (10%)  - For validation during optimization
Test:   747 questions (80%)  - For final evaluation and comparison
```

**Justification**:
- **Train (93)**: Within DSPy recommended range (30-300), provides ~18-19 examples per answer format
- **Dev (93)**: Equal size to train for robust validation
- **Test (747)**: Large enough for statistical significance (±1.8% margin at 95% CI)
- **Total train+dev (186)**: Well within DSPy optimal range, prevents overfitting

### **Option B: Minimal Split (Ultra Sample-Efficient)**
```
Train:  50 questions  (5%)   - Minimal for DSPy optimization
Dev:    43 questions  (5%)   - Quick validation
Test:   840 questions (90%)  - Maximum test coverage
```

**Justification**:
- **Train (50)**: Absolute minimum for balanced representation (~10 per format)
- **Dev (43)**: Small but sufficient for trend detection
- **Test (840)**: Nearly full dataset for comprehensive evaluation
- **Risk**: May underfit due to limited training examples for complex reasoning chains

### **Option C: Balanced Split**
```
Train:  140 questions (15%)  - More examples for complex patterns
Dev:    93 questions  (10%)  - Standard validation
Test:   700 questions (75%)  - Still large test set
```

**Justification**:
- **Train (140)**: ~28 examples per format, better for learning rare patterns
- **Dev (93)**: Same as Option A
- **Test (700)**: Slightly smaller but still robust
- **Trade-off**: More training data but less test coverage

---

## 📊 Stratification Dimensions

### 1. Answer Format Distribution (5 types)

| Format | Total | % of Dataset | Train (A) | Dev (A) | Test (A) |
|--------|-------|--------------|-----------|---------|----------|
| String | 299   | 32.0%        | 30        | 30      | 239      |
| Integer| 207   | 22.2%        | 21        | 21      | 165      |
| Float  | 148   | 15.9%        | 15        | 15      | 118      |
| None   | 148   | 15.9%        | 15        | 15      | 118      |
| List   | 131   | 14.0%        | 12        | 12      | 107      |
| **TOTAL** | **933** | **100%** | **93** | **93** | **747** |

### 2. Evidence Type Distribution (5 types)

| Evidence Type     | Total | % of Dataset | Train (A) | Dev (A) | Test (A) |
|-------------------|-------|--------------|-----------|---------|----------|
| Pure-text         | 395   | 42.3%        | 39        | 39      | 317      |
| Generalized-text  | 225   | 24.1%        | 23        | 23      | 179      |
| Table             | 123   | 13.2%        | 12        | 12      | 99       |
| Chart             | 100   | 10.7%        | 10        | 10      | 80       |
| Image             | 90    | 9.6%         | 9         | 9       | 72       |
| **TOTAL**         | **933** | **100%**   | **93**    | **93**  | **747**  |

### 3. Performance-Based Stratification

**Priority Areas for Training Set** (based on 45.1% baseline):
- **Float** (40.5% accuracy) - Include more challenging examples
- **List** (41.2% accuracy) - Needs optimization for multi-value extraction
- **Table+Chart** - Multimodal reasoning complexity
- **Cross-document questions** - Complex reasoning chains

**Balanced Representation**:
- Include mix of easy/medium/hard examples in training
- Ensure dev set has similar difficulty distribution
- Reserve edge cases for test set to measure generalization

---

## 🔧 Stratified Sampling Strategy

### Stratification Method: **Proportional Random Sampling with Constraints**

```python
# Pseudo-code for sampling strategy
for each (answer_format, evidence_type) combination:
    n_train = round(total_count × 0.10)  # 10% for Option A
    n_dev = round(total_count × 0.10)
    n_test = total_count - n_train - n_dev

    # Sample with constraints:
    # 1. Maintain format proportions
    # 2. Maintain evidence type proportions
    # 3. Ensure document diversity (max 2 questions per doc in train/dev)
    # 4. Include performance outliers (both easy and hard)
```

### Document Diversity Constraint
- **Train**: Max 2 questions per document (to ensure diversity across 45 docs)
- **Dev**: Max 2 questions per document
- **Test**: Remaining questions distributed naturally

### Cross-Format Balance
Ensure training set includes all meaningful format×evidence combinations:
- String + Pure-text (most common)
- Float + Table (numeric reasoning)
- List + Chart (multi-value extraction)
- None + Generalized-text (unanswerable detection)

---

## 📈 Expected Outcomes & Success Criteria

### Phase 1 Goals
1. **Baseline Maintenance**: Test accuracy ≥ 45.1% (current DSPy baseline)
2. **Optimization Target**: Test accuracy ≥ 46-47% (+1-2% improvement)
3. **Format Improvements**:
   - Float: 40.5% → 43-45% (±3% numeric precision improvement)
   - List: 41.2% → 43-45% (better multi-value extraction)
4. **Generalization**: Dev accuracy within ±1% of test accuracy (no overfitting)

### DSPy/GEPA Optimization Metrics
- **Primary**: Test set accuracy (compare to 45.1% baseline)
- **Secondary**: F1 score, format-specific accuracy
- **Efficiency**: Training cost (API tokens), optimization time
- **Robustness**: Performance variance across random seeds

---

## 🚀 Implementation Plan

### Step 1: Create Stratified Splits (Week 1)
```bash
python create_stratified_splits.py \
  --input MMESGBench/dataset/samples.json \
  --output splits/ \
  --strategy option_a \
  --seed 42
```

**Outputs**:
- `splits/train.json` (93 questions)
- `splits/dev.json` (93 questions)
- `splits/test.json` (747 questions)
- `splits/split_analysis.json` (distribution verification)

### Step 2: Validate Split Quality (Week 1)
```python
# Verify stratification quality
python validate_splits.py --splits_dir splits/

# Checks:
# 1. Format distribution matches proportions (±2%)
# 2. Evidence type distribution matches (±2%)
# 3. Document diversity (no doc has >2 train/dev questions)
# 4. No data leakage between splits
# 5. Performance distribution is balanced
```

### Step 3: Baseline Evaluation on Splits (Week 1)
```bash
# Evaluate current ColBERT+DSPy baseline on all splits
python evaluate_baseline_on_splits.py \
  --model colbert_dspy_baseline \
  --splits_dir splits/

# Expected results (based on 45.1% overall):
# - Train: ~45% (should match overall)
# - Dev: ~45% (should match overall)
# - Test: ~45% (should match overall)
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
  --target_accuracy 0.47

# Expected optimization time: 2-4 hours
# Expected API cost: $5-15 (based on 93 train + 93 dev examples)
```

### Step 5: Final Evaluation (Week 3)
```bash
# Evaluate optimized model on test set
python evaluate_optimized_model.py \
  --model dspy_gepa_optimized \
  --test_set splits/test.json \
  --output results/phase1_final_results.json

# Report all metrics:
# - Overall accuracy
# - Format-specific accuracy
# - Evidence-type specific accuracy
# - F1 score
# - Comparison to baseline (45.1%)
```

---

## 📋 Quality Assurance Checklist

### Pre-Optimization Validation
- [ ] Split distributions match target proportions (±2% tolerance)
- [ ] No data leakage between train/dev/test
- [ ] Document diversity maintained (max 2 per doc in train/dev)
- [ ] Baseline evaluation on splits matches expected ~45%
- [ ] All format×evidence combinations represented in training

### During Optimization
- [ ] Monitor dev set accuracy to detect overfitting
- [ ] Track optimization metrics (iterations, improvements)
- [ ] Document prompt evolution and changes
- [ ] Validate on dev set after each GEPA iteration

### Post-Optimization Evaluation
- [ ] Test accuracy ≥ 45.1% (baseline maintenance)
- [ ] Dev-test accuracy gap < 2% (generalization check)
- [ ] Format-specific improvements documented
- [ ] Statistical significance testing (bootstrap CI)
- [ ] Comparison table: Baseline vs Optimized

---

## 🔍 Alternative Considerations

### Should we include difficulty labels?

**Current Status**: MMESGBench dataset has **no difficulty field**

**Options**:
1. **Proxy Difficulty Metrics**:
   - Use baseline accuracy as proxy (questions with <30% = hard, >60% = easy)
   - Evidence page count (single-page vs cross-page)
   - Answer format complexity (None/Int = easier, Float/List = harder)

2. **Manual Annotation**:
   - Annotate subset for difficulty (not recommended - time-intensive)

3. **Ignore Difficulty**:
   - Rely on proportional sampling to naturally balance difficulty
   - Performance-based stratification captures difficulty implicitly

**Recommendation**: Use **performance-based proxies** (baseline accuracy) to ensure balanced difficulty distribution without manual annotation.

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
