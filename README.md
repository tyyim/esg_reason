# ESG Reasoning with DSPy Optimization

**Research Question**: Can DSPy prompt optimization match or exceed traditional fine-tuning (LoRA + RL) on ESG question answering with lower compute and fewer labels?

[![Dataset](https://img.shields.io/badge/Dataset-MMESGBench_933_QA-blue)](https://github.com/microsoft/Multimodal-ESG-Benchmark)
[![Status](https://img.shields.io/badge/Status-Test_Set_Complete-green)]()
[![Best](https://img.shields.io/badge/Best_Result-Hybrid_50.2%25-brightgreen)]()

---

## 🎯 Quick Start

### ✅ FINAL Results (654 Test Set)

| Approach  | Model | Accuracy | Change | Status |
|-----------|-------|----------|--------|--------|
| **Baseline** | qwen2.5-7b | 47.4% (310/654) | baseline | Oct 22 |
| **MIPROv2** | qwen2.5-7b | 47.6% (311/654) | +0.2% | Oct 22 |
| **GEPA** | qwen2.5-7b | 45.7% (299/654) | -1.7% ❌ | Oct 22 |
| **GEPA (LLM-corrected)** | qwen2.5-7b | 47.1% (308/654) | -0.3% | Oct 22 |
| **🏆 Hybrid (Format-Based)** | qwen2.5-7b | **50.2% (328/654)** | **+2.6%** ✅ | Oct 22 |
| **DC-Cold (Test-Time Learning)** | qwen2.5-7b | 35.6% (233/654) | -11.8% ❌ | Nov 1 |
| **DC-Bootstrap** | qwen2.5-7b | 34.7% (227/654) | -12.7% ❌ | Nov 1 |

**Major Discovery**: 
- Dev set results (93 Q) didn't generalize to test set (654 Q)
- ANLS metric failed: 46.7% false negative rate on strings
- **Hybrid format-based routing beats all single models!**

See [`analysis/reports/COMPLETE_ERROR_ANALYSIS.md`](analysis/reports/COMPLETE_ERROR_ANALYSIS.md) for full analysis.

---

## 📊 Full Dataset Evolution

| Date | Approach | Model | Dataset | Accuracy |
|------|----------|-------|---------|----------|
| Sep 2025 | ColBERT | qwen-max | 933 questions | 40.5% (378/933) |
| Oct 2025 | DSPy | qwen-max | 933 questions | 55.6% (519/933) |
| Oct 19 | Baseline | qwen2.5-7b | 93 dev | 52.7% (49/93) |
| Oct 19 | GEPA | qwen2.5-7b | 93 dev | 54.8% (51/93) |
| **Oct 22** | **Hybrid** | **qwen2.5-7b** | **654 test** | **50.2% (328/654)** ✅ |

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

**Dynamic Cheatsheet (Test-Time Learning)**:
- Model learns from past questions during evaluation
- Accumulates insights in evolving "cheatsheet"
- DC-Cold: 35.6% (empty cheatsheet, learns during test)
- DC-Bootstrap: 34.7% (starts with dev cheatsheet)
- **Critical weakness**: 0% on null format (107 questions)
- Result: Underperformed due to inability to recognize unanswerable questions

---

## 📁 Repository Structure (Updated Nov 1, 2025)

```
CC/
├── README.md                          # This file - Quick overview
├── RESEARCH_FINDINGS.md               # Complete analysis & insights
├── CHANGELOG.md                       # Historical log
├── CLAUDE.md                          # AI collaboration guidelines
├── DC_NOTION_SUMMARY.md               # DC results for Notion ⭐ NEW
├── DC_TESTS_STATUS.md                 # DC test status & monitoring ⭐ NEW
│
├── 📊 results/                        # Organized prediction results
│   ├── dev_set/                       # Dev set (93 questions)
│   │   ├── baseline_dev_predictions_20251019_130401.json (52.7%)
│   │   ├── gepa_dev_predictions_20251019_130401.json (54.8%)
│   │   ├── miprov2_dev_predictions_20251019_130401.json (48.4%)
│   │   └── complete_dev_analysis_20251019_130401.json
│   ├── test_set/                      # Test set (654 questions)
│   │   ├── baseline_test_predictions_20251021_225632.json (47.4%)
│   │   ├── gepa_test_predictions_20251021_225632.json (45.7%)
│   │   ├── miprov2_test_predictions_20251021_225632.json (47.6%)
│   │   └── complete_test_analysis_20251021_225632.json
│   ├── dc_experiments/                # DC test-time learning ⭐ NEW
│   │   ├── dc_cumulative_cold_dev_20251101_153119.json (43.0%)
│   │   ├── dc_cumulative_cold_test_20251101_171723.json (35.6%)
│   │   ├── dc_cumulative_cold_test_20251101_172109.json (34.7% bootstrap)
│   │   └── dev_cheatsheet_20251101.txt
│   └── analysis/                      # Analysis result files
│       ├── hybrid_system_analysis_results.json
│       ├── domain_knowledge_investigation.json
│       └── string_llm_evaluation_results.json
│
├── 🔬 analysis/                       # Analysis scripts & reports
│   ├── scripts/                       # Python analysis scripts
│   │   ├── analyze_test_set_results.py
│   │   ├── hybrid_system_analysis.py
│   │   ├── investigate_domain_knowledge.py
│   │   └── llm_evaluate_strings.py
│   ├── reports/                       # Comprehensive markdown reports
│   │   ├── COMPLETE_ERROR_ANALYSIS.md (616 lines) ⭐
│   │   ├── HYBRID_SYSTEM_FINDINGS.md (520 lines)
│   │   ├── TWO_STAGE_AGENTIC_DESIGN.md (900 lines)
│   │   └── STRING_LLM_EVALUATION_FINDINGS.md (341 lines)
│   └── outputs/                       # Text outputs from analyses
│
├── 📝 docs/                           # Additional documentation
│   ├── ANLS_EVALUATION_EXPLAINED.md
│   ├── MODEL_CONFIGURATION.md
│   ├── CODING_BEST_PRACTICES.md
│   ├── GEPA_OPTIMIZED_PROMPTS.md
│   ├── TEST_EVALUATION_STATUS.md
│   ├── DC_IMPLEMENTATION_GUIDE.md     # DC step-by-step guide ⭐ NEW
│   └── DYNAMIC_CHEATSHEET_PLAN.md     # DC planning doc ⭐ NEW
│
├── ⚙️ scripts/                        # Utility scripts
│   ├── run_complete_dev_evaluation.py
│   ├── run_complete_test_evaluation.py
│   ├── monitor_test_evaluation.py
│   └── compare_optimizations_dev_set.py
│
├── 🏗️ dspy_implementation/           # Core DSPy implementation
│   ├── data_splits/                   # Train/dev/test splits
│   ├── optimized_modules/             # GEPA/MIPROv2 modules
│   ├── dc_module/                     # Dynamic Cheatsheet ⭐ NEW
│   │   ├── dc_evaluator.py            # Evaluation with checkpointing
│   │   ├── dc_wrapper.py              # DashScope SDK wrapper
│   │   ├── dc_prompts.py              # ESG-specific prompts
│   │   ├── dc_rag_module.py           # DC + RAG integration
│   │   └── README.md                  # DC setup & usage
│   ├── dspy_rag_enhanced.py
│   ├── dspy_signatures_enhanced.py
│   ├── dspy_postgres_retriever.py
│   ├── evaluate_baseline.py
│   ├── gepa_skip_baseline.py
│   └── enhanced_miprov2_qwen7b_optimization.py
│
├── 💾 Data
│   ├── data/
│   │   └── mmesgbench_dataset_corrected.json  # 933 ESG questions
│   ├── MMESGBench/                    # Original benchmark (external repo)
│   ├── dc_repo/                       # Dynamic Cheatsheet repo (gitignored) ⭐ NEW
│   ├── source_documents/              # Original PDFs
│   └── processed_data/                # Processed chunks
│
├── 🔧 Core
│   ├── src/                           # Utility modules
│   ├── configs/                       # Configuration files
│   ├── logs/                          # Runtime logs
│   │   └── dc_evaluation/             # DC evaluation logs ⭐ NEW
│   └── cache/                         # Cache data
│
└── 🗄️ archive/                       # Old/outdated files
    ├── old_results/                   # Old prediction files
    ├── old_phases/                    # Old phase directories
    ├── old_scripts/                   # Old scripts
    ├── old_docs/                      # Old documentation
    └── archive_old_project/           # Historical archive
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

### Dynamic Cheatsheet Evaluation (COMPLETE)
```bash
# Test set - Cold start
python dspy_implementation/dc_module/dc_evaluator.py \
  --dataset test \
  --variant cumulative

# Test set - Bootstrap from dev cheatsheet
python dspy_implementation/dc_module/dc_evaluator.py \
  --dataset test \
  --variant cumulative \
  --bootstrap-cheatsheet results/dc_experiments/dc_cumulative_cold_dev_{timestamp}.json
```

**Results**: DC achieved 35.6% (cold) and 34.7% (bootstrap) on test set.
**Critical Finding**: DC scored 0% on all 107 null format questions, explaining the large performance gap vs DSPy approaches.

---

## 📊 Dataset

**MMESGBench**: 933 ESG question-answer pairs from 45 corporate ESG reports

- **Total**: 933 questions
- **Location**: `data/mmesgbench_dataset_corrected.json`
- **Splits**: 186 train / 93 dev / 654 test (in `dspy_implementation/data_splits/`)
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

**Phase**: Test set validation complete ✅  
**Best Result**: Hybrid system 50.2% (+2.6% vs MIPROv2) ✅  
**Major Discovery**: Format-based routing beats all single models ⭐  
**Updated**: October 22, 2025

---

## 📖 Quick Reference

**Authoritative Result Files**:
- `results/dev_set/*_20251019_130401.json` - Dev set predictions (baseline, GEPA, MIPROv2)
- `results/test_set/*_20251021_225632.json` - Test set predictions (baseline, GEPA, MIPROv2)

**Key Analysis Reports**:
- `analysis/reports/COMPLETE_ERROR_ANALYSIS.md` ⭐ - Full dev + test analysis
- `analysis/reports/HYBRID_SYSTEM_FINDINGS.md` - Format-based routing (50.2%)
- `analysis/reports/TWO_STAGE_AGENTIC_DESIGN.md` - Two-stage system design (53-55% expected)

**Key Scripts**:
- Baseline eval: `dspy_implementation/evaluate_baseline.py`
- GEPA optimization: `dspy_implementation/gepa_skip_baseline.py`
- MIPROv2 optimization: `dspy_implementation/enhanced_miprov2_qwen7b_optimization.py`
- Complete evaluation: `scripts/run_complete_test_evaluation.py`
- Hybrid analysis: `analysis/scripts/hybrid_system_analysis.py`

**Evaluation**: Uses MMESGBench's `eval_score()` with ANLS 0.5 threshold + LLM validation for strings

---

## 🎯 Next Steps

**Immediate (This Week)**:
1. ✅ Test set validation complete
2. ✅ Error analysis complete  
3. ✅ Hybrid system designed
4. ⏳ Implement two-stage agentic system (expected 53-55%)

**Short-term (Next 2 Weeks)**:
1. Implement format-based hybrid router
2. Test two-stage system (GEPA reasoning → MIPROv2 extraction)
3. Statistical significance testing
4. Paper draft preparation

**Long-term (Next Month)**:
1. Production deployment of hybrid system
2. Compare against fine-tuning (LoRA + RL)
3. Paper submission (ACL/EMNLP 2026)

---

**Last Updated**: October 22, 2025  
**Status**: Test set complete, hybrid system ready, two-stage design complete  
**Contact**: [GitHub](https://github.com/tyyim/esg_reason) | [Notion](https://www.notion.so/5f2084ba49f64166b17d52aff4abc7c2)
