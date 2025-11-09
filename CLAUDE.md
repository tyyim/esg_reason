# CLAUDE.md - AI Assistant Guidelines

**Purpose**: Quick reference for AI assistants working on this ESG reasoning research project  
**Last Updated**: October 21, 2025

---

## 🎯 Project Overview

**Research Question**: Can DSPy prompt optimization match or exceed traditional fine-tuning (LoRA + RL) on ESG question answering with lower compute and fewer labels?

**Current Status**: Dev set optimization complete ✅ | Test set validation pending ⏳

---

## 📊 Current Results (AUTHORITATIVE)

### Dev Set (93 Questions) - October 19, 2025

| Approach  | Accuracy | vs Baseline | Source File |
|-----------|----------|-------------|-------------|
| **Baseline** | **52.7%** (49/93) | baseline | `baseline_dev_predictions_20251019_130401.json` |
| **GEPA** | **54.8%** (51/93) | **+2.2%** ✅ | `gepa_dev_predictions_20251019_130401.json` |
| **MIPROv2** | 48.4% (45/93) | **-4.3%** ❌ | `miprov2_dev_predictions_20251019_130401.json` |

**⚠️ CRITICAL**: These 3 JSON files are authoritative. Ignore all other result files.

### Full Dataset (933 Questions)

| Date | Approach | Model | Accuracy |
|------|----------|-------|----------|
| Sep 2025 | ColBERT | qwen-max | 40.5% (378/933) |
| Oct 2025 | DSPy | qwen-max | 55.6% (519/933) |
| **Pending** | DSPy | qwen2.5-7b | ? (test set) |

---

## 📁 Essential Documentation (READ THESE)

### 1. README.md
Quick overview, current status, running experiments

### 2. RESEARCH_FINDINGS.md
Complete analysis, recommendations, next steps

### 3. CHANGELOG.md
Historical log of all work and findings

### 4. DEV_SET_ERROR_ANALYSIS.md
Detailed error patterns by format type

**Start with README.md, then read RESEARCH_FINDINGS.md for complete context.**

---

## ⚠️ Critical Information

### Key Finding: GEPA > MIPROv2 (+6.4%)

**GEPA (Reflection-based)**: 54.8% (+2.2% vs baseline)  
**MIPROv2 (Teacher-student)**: 48.4% (-4.3% vs baseline)

**Why**: Reflection learns from actual student failures; teacher-student uses generic prompts that don't transfer well to 7B models.

### Format-Specific Performance

| Format | Baseline | GEPA | Insight |
|--------|----------|------|---------|
| **Int** | 63.2% | **73.7% (+10.5%)** | ✅ GEPA excels |
| **Float** | 69.2% | **76.9% (+7.7%)** | ✅ GEPA excels |
| **List** | 23.1% | **38.5% (+15.4%)** | ✅ GEPA excels |
| **Str** | **35.3%** | 29.4% (-5.9%) | ❌ Baseline better |
| **null** | **92.9%** | 85.7% (-7.2%) | ❌ Baseline better |

**Implication**: Use GEPA for structured data, baseline for text/refusal. Consider format-specific routing.

### Prompt Length Trade-offs

- **Baseline**: 0 characters (DSPy default)
- **GEPA**: 7,749 characters
- **Optimal**: ~3,000 characters (based on performance)

**Finding**: Longer prompts help structured extraction but hurt text extraction.

---

## 🔧 Development Standards

### Evaluation

**IMPORTANT - Use Corrected Evaluator (Nov 7, 2025):**
```python
from src.evaluation import eval_score  # Uses corrected version with null equivalence

answer_score = eval_score(gt, pred, answer_type)
correct = (answer_score >= 0.5)  # ANLS 0.5 threshold
```

**Bug Fix**: MMESGBench's original `eval_score()` treated "null" and "Not answerable" as different strings (ANLS string distance), causing false negatives. The corrected evaluator (`src/evaluation_utils.py`) recognizes null-equivalent responses ("null", "not answerable", "n/a", "cannot answer", "fail to answer") as semantically identical before applying ANLS.

**Impact**: +13.6% accuracy improvement for DC on test set (35.6% → 49.2%). All production scripts now use corrected evaluator automatically.

### Data Splits (AUTHORITATIVE)

```
dspy_implementation/data_splits/
├── train_186.json (20%)
├── dev_93.json (10%)
└── test_654.json (70%)
```

**Do NOT use other splits** (e.g., `splits/` directory has old/incorrect splits).

### Running Experiments

**Baseline Evaluation:**
```bash
python dspy_implementation/evaluate_baseline.py \
  --model qwen2.5-7b-instruct \
  --dataset dev \
  --output baseline_dev_predictions.json
```

**GEPA Optimization:**
```bash
python dspy_implementation/gepa_skip_baseline.py
```

**Dynamic Cheatsheet Evaluation (NEW):**
```bash
# POC test (10 questions)
python dspy_implementation/dc_module/dc_evaluator.py \
  --dataset dev --max-questions 10

# Cold start (fair comparison to DSPy)
python dspy_implementation/dc_module/dc_evaluator.py \
  --dataset test --variant cumulative

# Warm start (test-time learning advantage)
python dspy_implementation/dc_module/dc_evaluator.py \
  --dataset test --variant cumulative --warmup
```

### Code Quality Requirements

**For evaluation/optimization scripts (>10 min runtime):**
- ✅ Checkpoint/resume mechanism
- ✅ Structured logging (file + console)
- ✅ Retry logic with exponential backoff
- ✅ Progress bars (tqdm)
- ✅ Structured JSON output
- ✅ MMESGBench's exact eval_score()

**Reference**: `archive_old_project/code_old/colbert_full_dataset_evaluation.py`

---

## ⚠️ Common Pitfalls (AVOID THESE)

### 1. DC vs DSPy Comparison ❌
**CRITICAL**: DC-Warm vs DSPy is NOT a fair comparison!

**Fair Comparisons**:
- DSPy Baseline vs DC-Cold (both use no training data from test)
- DSPy GEPA/MIPROv2 vs DC-Cold (both optimize on train/dev only)

**Unfair Comparisons**:
- DC-Warm vs ANY DSPy approach (DC learns FROM test set)

**Always specify**:
- DC-Cold: Empty cheatsheet, fair to compare
- DC-Warm: Learns from test, shows upper bound only

### 2. Dataset Confusion ❌
**DON'T** mix full dataset (933) with dev set (93) results without clear labels.

**Example of WRONG**:
```
"Performance improved from 40% to 54.8%"
(40% is 933 questions, 54.8% is 93 questions - different datasets!)
```

**Correct**:
```
"Full dataset (933): 40.5% → 55.6%"
"Dev set (93): 52.7% → 54.8% (GEPA)"
```

### 2. Model Switching ❌
**DON'T** compare qwen-max results with qwen2.5-7b results without noting the model change.

**Always specify**: model name + dataset size

### 3. Old Result Files ❌
**DON'T** use result files other than the 3 authoritative files dated `20251019_130401`.

**If you see**:
- `baseline_rag_results_20251015_*.json` → IGNORE
- `quick_dev_eval_*.json` → IGNORE
- `dspy_baseline_dev_checkpoint.json` → IGNORE (incomplete, 90/93 only)

### 4. Optimizer Parameters ❌

**MIPROv2:**
```python
optimizer.compile(
    student=module,
    trainset=train_set,
    valset=dev_set,  # ✅ ALWAYS provide!
    num_trials=20,
    auto='light',
    requires_permission_to_run=False  # ✅ Works for MIPROv2
)
```

**GEPA:**
```python
optimizer.compile(
    student=module,
    trainset=train_set,
    valset=dev_set,  # ✅ ALWAYS provide!
    # ❌ NO requires_permission_to_run parameter!
)
```

**GEPA Metrics Return Type:**
```python
from dspy import ScoreWithFeedback

# ✅ Correct
return ScoreWithFeedback(
    score=float_score,
    feedback="explanation of score"
)

# ❌ Wrong
return {"score": float_score, "feedback": "..."}  # Plain dict fails!
```

---

## 🚀 Immediate Next Steps (Priority Order)

### 1. Dynamic Cheatsheet Evaluation ✅ **COMPLETE**
Evaluated DC test-time learning approach on MMESGBench against DSPy optimization.

**Implementation**: Nov 1, 2025 | **Corrected**: Nov 7, 2025
- Module: `dspy_implementation/dc_module/`
- DC-RAG integration (NOT using DSPy framework)
- Uses DC's native test-time learning

**Results (After Bug Fix)**:
- **DC-Cold (Test Set)**: 49.2% (+1.8% vs DSPy Baseline)
- **DC-Bootstrap**: 48.5% (no benefit from dev cheatsheet)
- **Evaluation Bug Fix**: +13.6% accuracy improvement (35.6% → 49.2%)

**Key Findings**:
- DC outperforms all DSPy optimization approaches except Hybrid
- Test-time learning is effective without train/dev optimization
- Bootstrap provided no benefit over cold start
- Evaluation bug was masking DC's true performance

### 2. Test Set Validation
Run all approaches (DSPy + DC) on 654 test questions.

### 2. Statistical Significance
- McNemar's test (paired accuracy)
- Bootstrap confidence intervals
- Document p-values

### 3. GEPA-v2 Optimization
- Reduce prompt length (7,749 → <3,000 chars)
- Improve Str and null performance
- Keep Int/Float/List gains

### 4. Update Notion
- Correct baseline (52.7% not 58.1%)
- GEPA +2.2% improvement
- Format-specific insights

---

## 📊 Database & Environment

### Database
```
PostgreSQL 15+ with pgvector
- Collection: MMESG
- Chunks: 54,608 (1024-dim embeddings)
- Embeddings: text-embedding-v4
- Retrieval: top-5 cosine similarity
```

### Environment Setup
```bash
conda activate esg_reasoning
cd /Users/victoryim/Local_Git/CC

# Required env vars (.env)
DASHSCOPE_API_KEY=your_key
PG_URL=postgresql://user:pass@host:port/database
ESG_COLLECTION_NAME=MMESG
```

### Models
- **LLM**: qwen-max ($0.06/1K), qwen2.5-7b-instruct ($0.0006/1K)
- **Embeddings**: text-embedding-v4
- **Cost difference**: 100x (qwen2.5-7b is cheaper)

---

## 🔍 Key Insights (Remember These)

### 1. Reflection > Teacher-Student for 7B Models
GEPA (+2.2%) outperformed MIPROv2 (-4.3%) by **6.4%**.

**Why**: 7B models handle iterative reflection better than following large model instructions.

### 2. Format-Specific Optimization
Don't optimize all formats the same way:
- **Structured (Int/Float/List)**: Use GEPA → +10-15%
- **Text (Str/null)**: Use baseline → better performance

**Recommendation**: Hybrid approach with format-specific routing.

### 3. Cost-Performance Trade-offs
- qwen2.5-7b (GEPA): 54.8% @ $0.0006/1K = **100x cheaper**
- qwen-max: ~69.9% @ $0.06/1K = expensive
- **Result**: 78% performance at 1% cost

### 4. Small Dev Sets Are Noisy
93 questions → ±1.1% per question

**Always validate on test set** (654 questions) before making production decisions.

### 5. Prompt Length Has Limits
- Too short: Misses patterns
- Optimal: ~3,000 chars
- Too long (7,749 chars): Attention dilution, confuses 7B models

---

## 💬 Collaboration Workflow

### When Starting Work
1. Read README.md for current status
2. Read RESEARCH_FINDINGS.md for complete context
3. Check CHANGELOG.md for recent changes
4. Verify you're using authoritative result files

### When Running Experiments
1. Use proper data splits (`dspy_implementation/data_splits/`)
2. Save predictions with clear naming: `{approach}_dev_predictions_YYYYMMDD_HHMMSS.json`
3. Use MMESGBench's eval_score() for evaluation
4. Log to `logs/` directory with timestamps

### After Completing Work
1. Update README.md with new results
2. Document findings in RESEARCH_FINDINGS.md
3. Add entry to CHANGELOG.md
4. Commit with clear message
5. Notify human to update Notion

### Documentation Updates
**DON'T** create new documentation files. Update existing 3:
- Quick updates → README.md
- Analysis/findings → RESEARCH_FINDINGS.md
- Historical log → CHANGELOG.md

---

## 🎓 Research Context

### Dataset
**MMESGBench**: 933 ESG question-answer pairs from 45 corporate ESG reports
- Source: [Microsoft Multimodal ESG Benchmark](https://github.com/microsoft/Multimodal-ESG-Benchmark)
- Types: Integer, Float, String, List, None
- Evaluation: ANLS 0.5 (fuzzy matching, 50% similarity threshold)

### Architecture
```
Question
   ↓
PostgreSQL + pgvector Retrieval (top-5 chunks)
   ↓
ESG Reasoning (DSPy ChainOfThought)
   ↓
Answer Extraction (DSPy)
   ↓
Structured Answer (Int/Float/Str/List/None)
```

### Research Contribution
This work demonstrates that **reflection-based optimization (GEPA) outperforms teacher-student (MIPROv2) for small language models** (7B parameters), with format-specific performance patterns and significant cost-performance trade-offs.

**Potential paper**: "When Reflection Beats Teacher-Student: Efficient Prompt Optimization for Small Language Models"

---

## 🔗 Quick Links

- **GitHub**: https://github.com/tyyim/esg_reason
- **Notion**: https://www.notion.so/5f2084ba49f64166b17d52aff4abc7c2
- **MMESGBench**: https://github.com/microsoft/Multimodal-ESG-Benchmark

---

## ✅ Pre-Flight Checklist

Before running experiments:
- [ ] Conda environment activated (`esg_reasoning`)
- [ ] Using correct data split (`dspy_implementation/data_splits/`)
- [ ] Clear output file naming with timestamp
- [ ] Checkpoint/resume mechanism implemented (if >10 min)
- [ ] Using MMESGBench's eval_score()
- [ ] Logging to `logs/` directory

Before claiming results:
- [ ] Verified on correct dataset (dev 93 or test 654?)
- [ ] Specified model clearly (qwen-max or qwen2.5-7b?)
- [ ] Compared against correct baseline (52.7% for dev set)
- [ ] Statistical significance tested (if claiming improvement)

---

**Remember**: Test set validation is the highest priority. Dev set results (93 questions) are provisional until validated on test set (654 questions).

**Last Updated**: October 21, 2025  
**Status**: Dev set complete, test set pending
