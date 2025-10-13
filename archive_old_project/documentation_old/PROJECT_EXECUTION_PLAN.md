# Project Execution Plan - Baseline Reset & DSPy Optimization

**Created**: 2025-10-11
**Status**: In Progress - Step 2
**Goal**: Establish proper baselines and re-run DSPy optimization experiments

---

## 🎯 **Executive Summary**

**CRITICAL DISCOVERY**: Current DSPy baseline has 0% accuracy on "Not answerable" questions (0/150), causing -2.6% performance drop vs Sept 28 baseline (39.9% → 37.3%).

**ROOT CAUSE**: Missing "Not answerable" handling in extraction prompt.

**SOLUTION PATH**: Reset baselines → Fix bugs → Re-run optimization

---

## 📋 **Execution Checklist**

### ✅ **Phase 0: Investigation** (COMPLETED)
- [x] Compare Sept 28 vs Oct 10 results
- [x] Identify "Not answerable" bug (0/150 correct)
- [x] Document performance degradation analysis
- [x] Create PERFORMANCE_DEGRADATION_ANALYSIS.md

### 🔄 **Phase 1: Baseline Reset** (IN PROGRESS)
- [ ] **Step 1**: Stop old autonomous evaluator (wrong filenames)
- [ ] **Step 2**: Create basic DSPy parallel evaluator
  - Uses corrected dataset (`mmesgbench_dataset_corrected.json`)
  - NO query generation (fair comparison)
  - Proper "Not answerable" prompt
  - Async parallel execution (8 workers)
- [ ] **Step 3**: Run basic DSPy baseline on full 933 questions
- [ ] **Step 4**: Compare with Sept 28 results (39.9%)

### ⏳ **Phase 2: Fix DSPy Implementation** (PENDING)
- [ ] **Step 5**: Fix "Not answerable" handling in signatures
  - Update `AnswerExtraction` signature
  - Add explicit "Not answerable" instruction
  - Test on dev set
- [ ] **Step 6**: Fix query generation hurting retrieval
  - Enhanced retrieval (71.9%) < Baseline (75.6%)
  - Investigate MIPROv2 optimization quality
- [ ] **Step 7**: Re-run baseline evaluation
  - Expected: ~45% accuracy (vs current 37.3%)

### ⏳ **Phase 3: Re-run Optimization** (PENDING)
- [ ] **Step 8**: Re-run MIPROv2 optimization on fixed baseline
  - Use auto="light" mode first
  - Then auto="medium" if needed
- [ ] **Step 9**: Evaluate optimized model on full dataset
- [ ] **Step 10**: Compare all results and update Notion

---

## 📊 **Performance Targets**

| Metric | Sept 28 | Current | Target (Fixed) | Status |
|--------|---------|---------|----------------|--------|
| **Overall Accuracy** | 39.9% | 37.3% | **45%+** | 🔄 In Progress |
| **"Not answerable"** | 48% | **0%** 🔴 | **48%+** | 🔧 Needs Fix |
| **Int Format** | 42.5% | 51.2% ✅ | 51%+ | ✅ Good |
| **Str Format** | 38.5% | 43.1% ✅ | 43%+ | ✅ Good |
| **Float Format** | 33.8% | 42.2% ✅ | 42%+ | ✅ Good |
| **List Format** | 36.6% | 39.4% ✅ | 39%+ | ✅ Good |

---

## 🔑 **Key Files & Locations**

### **Corrected Dataset**
- `mmesgbench_dataset_corrected.json` - Authoritative 933 questions with correct document names

### **DSPy Implementation**
- `dspy_implementation/dspy_dataset.py` - Dataset loader with corrected filenames
- `dspy_implementation/dspy_rag_enhanced.py` - RAG modules (baseline + enhanced)
- `dspy_implementation/dspy_signatures_enhanced.py` - Signatures (NEEDS FIX for "Not answerable")
- `dspy_implementation/dspy_metrics_enhanced.py` - Evaluation metrics

### **Results Storage**
- `dspy_implementation/full_dataset_results/` - Full dataset evaluation results
- `enhanced_rag_results_20251010_144213.json` - Phase 1a light mode results (46.2%)
- `optimized_full_dataset_mmesgbench_with_f1.json` - Sept 28 baseline (39.9%)

### **Analysis Documents**
- `PERFORMANCE_DEGRADATION_ANALYSIS.md` - Detailed investigation
- `DSPy_RAG_Redesign_Plan.md` - Architecture redesign plan
- `ENHANCED_RAG_IMPLEMENTATION_COMPLETE.md` - Implementation guide

---

## 🚀 **Current Action: Step 2**

**Creating**: `dspy_basic_parallel_evaluator.py`

**Key Features**:
1. ✅ Uses corrected dataset
2. ✅ NO query generation (baseline comparison)
3. ✅ Proper "Not answerable" handling
4. ✅ Async parallel execution (8 workers)
5. ✅ Checkpoint every 25 questions
6. ✅ Resume capability
7. ✅ Progress tracking with ETA

**Expected Runtime**: 45-60 minutes for 933 questions

**Expected Accuracy**: 42-45% (if extraction is better than Sept 28)

---

## 🐛 **Known Issues & Fixes**

### **Issue 1: "Not Answerable" Handling (CRITICAL)**

**Current Behavior**:
- 0/150 "Not answerable" questions correct
- Model hallucinates answers or returns `None`

**Fix Location**: `dspy_implementation/dspy_signatures_enhanced.py`
```python
# Line ~70-90: AnswerExtraction signature
# ADD THIS to instructions:
"""
If the context does not contain sufficient information to answer the question,
respond with "Not answerable".
"""
```

**Expected Impact**: +5-8% E2E accuracy

---

### **Issue 2: Query Generation Hurting Retrieval**

**Current Behavior**:
- Enhanced retrieval: 71.9%
- Baseline retrieval: 75.6% (better!)

**Hypothesis**:
- MIPROv2 optimization on dev set (93 questions) doesn't generalize
- Optimized queries too specific or too general
- Default prompts suboptimal

**Fix Options**:
1. Disable query optimization for now
2. Re-train on larger set (300+ questions)
3. Use auto="medium" for better generalization

**Expected Impact**: +3-4% E2E accuracy

---

## 📈 **Success Criteria**

### **Phase 1 Complete**:
- [x] Basic DSPy evaluator created
- [ ] Basic DSPy baseline evaluation complete
- [ ] Results comparable to Sept 28 (within ±2%)
- [ ] "Not answerable" handling verified working

### **Phase 2 Complete**:
- [ ] "Not answerable" bug fixed and verified
- [ ] Query generation issue resolved
- [ ] Fixed baseline achieves 45%+ accuracy
- [ ] All metrics in target range

### **Phase 3 Complete**:
- [ ] MIPROv2 optimization on fixed baseline complete
- [ ] Optimized model achieves 48-52% accuracy
- [ ] All results documented in Notion
- [ ] Ready for Phase 2 (advanced optimization)

---

## 🔄 **Progress Tracking**

| Date | Event | Result |
|------|-------|--------|
| 2025-09-28 | Sept 28 baseline | 39.9% (MMESGBench exact logic) |
| 2025-10-01 | Subset validation | 46.8% on 47 questions |
| 2025-10-10 | DSPy baseline | 37.3% (-2.6% - bug found) |
| 2025-10-10 | Phase 1a light mode | 46.2% on dev set (93q) |
| **2025-10-11** | **Investigation complete** | **Bug identified** |
| 2025-10-11 | Basic DSPy evaluator created | In progress |
| TBD | Basic DSPy baseline | Target: 42-45% |
| TBD | Fixed DSPy baseline | Target: 45%+ |
| TBD | Optimized DSPy | Target: 48-52% |

---

## 💡 **Next Steps After This Plan**

1. **Complete baseline reset and verification**
2. **Fix all identified bugs**
3. **Re-run MIPROv2 optimization**
4. **Document final results**
5. **Move to Phase 2**: Advanced optimization with RAG improvements
6. **Phase 3**: Compare with fine-tuning approaches

---

## 📞 **Contact & Updates**

- **Status Updates**: Check `autonomous_evaluation.log` for real-time progress
- **Results**: Check `dspy_implementation/full_dataset_results/` for outputs
- **Todo List**: Tracked in `PROJECT_EXECUTION_PLAN.md` and git commits

---

*Last Updated: 2025-10-11 13:00*
