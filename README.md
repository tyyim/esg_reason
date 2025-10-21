# ESG Reasoning with DSPy Optimization

**Research Question**: Can DSPy prompt optimization match or exceed traditional fine-tuning (LoRA + RL) on ESG question answering with lower compute and fewer labels?

[![Dataset](https://img.shields.io/badge/Dataset-MMESGBench_933_QA-blue)](https://github.com/microsoft/Multimodal-ESG-Benchmark)
[![Status](https://img.shields.io/badge/Status-Dev_Set_Complete-yellow)]()

---

## 🎯 Quick Start

### Results Summary (93 Dev Set)

| Approach  | Model | Accuracy | Change | Date |
|-----------|-------|----------|--------|------|
| **Baseline** | qwen2.5-7b | **52.7%** (49/93) | baseline | Oct 19 |
| **GEPA** | qwen2.5-7b | **54.8%** (51/93) | **+2.2%** ✅ | Oct 19 |
| **MIPROv2** | qwen2.5-7b | 48.4% (45/93) | -4.3% ❌ | Oct 19 |

**Key Finding**: GEPA improved performance, especially on structured data (Int +10.5%, List +15.4%, Float +7.7%). See [`DEV_SET_ERROR_ANALYSIS.md`](DEV_SET_ERROR_ANALYSIS.md) for details.

---

## 📊 Full Dataset Results (933 Questions)

| Date | Approach | Model | Accuracy |
|------|----------|-------|----------|
| Sep 2025 | ColBERT Baseline | qwen-max | 40.5% (378/933) |
| Oct 2025 | DSPy Baseline | qwen-max | 55.6% (519/933) |
| **Pending** | DSPy Baseline | qwen2.5-7b | ? |
| **Pending** | GEPA Optimized | qwen2.5-7b | ? |

**Next Step**: Run 654-question test set evaluation to validate dev set findings.

---

## 🏗️ Architecture

### RAG Pipeline
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

### Optimization Approaches

**MIPROv2 (Teacher-Student)**:
- Teacher (qwen-max) generates optimized prompts
- Student (qwen2.5-7b) executes with those prompts
- Result: -4.3% (degraded) ❌

**GEPA (Reflection-Based)**:
- qwen-max provides feedback on failures
- Evolves prompts through 32 iterations
- Result: +2.2% (improved) ✅

---

## 📁 Repository Structure

### Essential Files
```
CC/
├── README.md                               # This file
├── RESEARCH_FINDINGS.md                    # Complete analysis & findings
├── CHANGELOG.md                            # Historical log
├── DEV_SET_ERROR_ANALYSIS.md              # Detailed dev set analysis
│
├── 📊 Authoritative Results
│   ├── baseline_dev_predictions_20251019_130401.json     # 52.7%
│   ├── gepa_dev_predictions_20251019_130401.json         # 54.8%
│   └── miprov2_dev_predictions_20251019_130401.json      # 48.4%
│
├── 💾 Data
│   ├── mmesgbench_dataset_corrected.json  # 933 questions
│   └── dspy_implementation/data_splits/
│       ├── train_186.json (20%)
│       ├── dev_93.json (10%)
│       └── test_654.json (70%)
│
├── 🏗️ Code
│   ├── dspy_implementation/               # DSPy modules
│   │   ├── dspy_rag_enhanced.py          # RAG modules
│   │   ├── dspy_signatures_enhanced.py   # Signatures
│   │   ├── dspy_postgres_retriever.py    # Retrieval
│   │   ├── dspy_metrics_gepa_fixed.py    # GEPA metrics
│   │   ├── evaluate_baseline.py          # Baseline eval
│   │   ├── gepa_skip_baseline.py         # GEPA optimization
│   │   └── enhanced_miprov2_qwen7b_optimization.py  # MIPROv2
│   │
│   ├── src/                               # Core utilities
│   └── MMESGBench/                        # Reference benchmark
│
├── 📝 Logs
│   ├── logs/qwen7b_test/                  # MIPROv2 logs
│   └── logs/gepa_optimization/            # GEPA logs
│
└── 🗄️ Archive
    └── archive_old_project/                # Historical work
```

---

## 🚀 Running Experiments

### Baseline Evaluation
```bash
conda activate esg_reasoning
cd /Users/victoryim/Local_Git/CC

python dspy_implementation/evaluate_baseline.py \
  --model qwen2.5-7b-instruct \
  --dataset dev \
  --output baseline_dev_predictions.json
```

### GEPA Optimization
```bash
python dspy_implementation/gepa_skip_baseline.py
```

### Test Set Evaluation (Next Step)
```bash
python dspy_implementation/evaluate_baseline.py \
  --model qwen2.5-7b-instruct \
  --dataset test \
  --output baseline_test_predictions.json
```

---

## 📊 Dataset

**MMESGBench**: 933 ESG question-answer pairs from 45 corporate ESG reports

- **Total**: 933 questions
- **Splits**: 186 train / 93 dev / 654 test
- **Chunks**: 54,608 (1024-dim embeddings, text-embedding-v4)
- **Types**: Integer, Float, String, List, None
- **Source**: [Microsoft Multimodal ESG Benchmark](https://github.com/microsoft/Multimodal-ESG-Benchmark)

### Evaluation: ANLS 0.5
Uses MMESGBench's exact `eval_score()` function with fuzzy matching (50% similarity threshold):
```python
from MMESGBench.src.eval.eval_score import eval_score

answer_score = eval_score(gt, pred, answer_type)
correct = (answer_score >= 0.5)  # ANLS 0.5 threshold
```

---

## 💡 Key Findings

### 1. GEPA Works Better Than MIPROv2
- **GEPA**: +2.2% improvement
- **MIPROv2**: -4.3% degradation
- **Reason**: Reflection-based evolution captures domain patterns better

### 2. Format-Specific Performance
| Format | Baseline | GEPA | Change |
|--------|----------|------|--------|
| **Int** | 63.2% | **73.7%** | **+10.5%** ✅ |
| **Float** | 69.2% | **76.9%** | **+7.7%** ✅ |
| **List** | 23.1% | **38.5%** | **+15.4%** ✅ |
| **Str** | 35.3% | 29.4% | -5.9% ❌ |
| **null** | 92.9% | 85.7% | -7.2% ❌ |

**Insight**: GEPA excels at structured extraction but struggles with text and "not answerable" detection.

### 3. Cost-Performance Tradeoff
| Model | Cost ($/1K tokens) | Dev Accuracy |
|-------|-------------------|--------------|
| qwen-max | $0.06 | ~69.9% |
| qwen2.5-7b (GEPA) | $0.0006 | 54.8% |
| **Ratio** | **100x cheaper** | **78% performance** |

### 4. Prompt Length Matters
- **Baseline**: 0 characters (DSPy default)
- **GEPA**: 7,749 characters
- **Trade-off**: Longer prompts help structured data but hurt text extraction

---

## 🔬 Research Contributions

### 1. Reflection > Teacher-Student for Small Models
GEPA (reflection-based) outperformed MIPROv2 (teacher-student) by 6.4% on qwen2.5-7b.

**Implication**: For 7B models, iterative reflection with feedback is more effective than using large model prompts.

### 2. Format-Specific Optimization Potential
Different answer types benefit differently from optimization:
- Structured (Int/Float/List): Large gains
- Text (Str): Degradation  
- Null: Degradation

**Implication**: Hybrid approaches with format-specific prompts may work best.

### 3. Small Dev Sets Are Noisy
93 questions → 1 question = 1.1% change

**Need**: Test set (654 questions) validation for confidence.

---

## 🚦 Next Steps

### Immediate (This Week)
1. ✅ Dev set evaluation complete
2. ⏳ **Run test set (654 questions)** - Validate GEPA improvement
3. ⏳ Statistical significance analysis
4. ⏳ Update Notion with findings

### Short-term (Next 2 Weeks)
1. Try GEPA-v2 with shorter prompts (<3,000 chars)
2. Format-specific optimization (separate prompts for Int/Str/null)
3. Try larger student model (qwen2.5-14b or 32b)
4. Error pattern analysis

### Long-term (Next Month)
1. Full test set comparison (all 3 approaches)
2. Compare DSPy vs fine-tuning (LoRA + RL)
3. Production deployment strategy
4. Paper preparation

---

## 🤝 Collaboration Workflow

### For Humans
1. **Check Status**: Read this README
2. **Deep Dive**: See [`RESEARCH_FINDINGS.md`](RESEARCH_FINDINGS.md)
3. **History**: See [`CHANGELOG.md`](CHANGELOG.md)
4. **Error Analysis**: See [`DEV_SET_ERROR_ANALYSIS.md`](DEV_SET_ERROR_ANALYSIS.md)
5. **Update Notion**: Sync key findings after experiments

### For AI Assistants
1. Read README (this file) for current state
2. Read RESEARCH_FINDINGS for complete context
3. Check authoritative result files (3 JSON files)
4. Update CHANGELOG after significant work
5. Create experiment logs in `logs/`

### Running New Experiments
1. Plan hypothesis and config
2. Run experiment, save predictions
3. Update results in README
4. Document findings in RESEARCH_FINDINGS
5. Log in CHANGELOG
6. Sync to Notion

---

## 📚 Documentation

- **README.md** (this file) - Quick overview & current status
- **[RESEARCH_FINDINGS.md](RESEARCH_FINDINGS.md)** - Complete analysis, findings, and recommendations
- **[CHANGELOG.md](CHANGELOG.md)** - Historical log of all work
- **[DEV_SET_ERROR_ANALYSIS.md](DEV_SET_ERROR_ANALYSIS.md)** - Detailed dev set analysis
- **[Notion Research Plan](https://www.notion.so/5f2084ba49f64166b17d52aff4abc7c2)** - Research narrative

---

## 🔧 Environment

```bash
# Setup
conda create -n esg_reasoning python=3.10
conda activate esg_reasoning
pip install -r dspy_implementation/requirements_dspy.txt

# Environment variables (.env)
DASHSCOPE_API_KEY=your_key
PG_URL=postgresql://user:pass@host:port/database
ESG_COLLECTION_NAME=MMESG
```

**Database**: PostgreSQL 15+ with pgvector extension (54,608 chunks)

---

## 📊 Current Status

**Phase**: Dev set optimization complete ✅  
**Best Result**: GEPA 54.8% (+2.2% vs baseline) ✅  
**Next**: Test set evaluation (654 questions) ⏳  
**Updated**: October 19, 2025

---

## 📖 Quick Reference

**Authoritative Result Files**:
- `baseline_dev_predictions_20251019_130401.json` (52.7%)
- `gepa_dev_predictions_20251019_130401.json` (54.8%)
- `miprov2_dev_predictions_20251019_130401.json` (48.4%)

**Key Scripts**:
- Baseline: `dspy_implementation/evaluate_baseline.py`
- GEPA: `dspy_implementation/gepa_skip_baseline.py`
- MIPROv2: `dspy_implementation/enhanced_miprov2_qwen7b_optimization.py`

**Evaluation**: Uses MMESGBench's `eval_score()` with ANLS 0.5 threshold

---

**Last Updated**: October 21, 2025  
**Status**: Dev set complete, test set pending  
**Contact**: [GitHub](https://github.com/tyyim/esg_reason) | [Notion](https://www.notion.so/5f2084ba49f64166b17d52aff4abc7c2)
