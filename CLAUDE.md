# CLAUDE.md - ESG Reasoning Research

> **Maintenance**: See `.claude/CLAUDE_MD_GUIDELINES.md` | Keep concise - scannable in 30 seconds
> **Details**: Historical findings in `PHASE_1A_FINDINGS.md`, `BASELINE_COMPARISON.md`, `Research Plan — ESG Reasoning and Green Finance.md`

---

## 🎯 Current Focus

**Phase 1a**: DSPy MIPROv2 optimization on dev set (93 questions)

**Status**: Ready to run optimization (~45-90 min)

**Current Baseline** (Oct 9, 2025 - with FIXED metrics):
- **Dev set**: 38.7% E2E | 75.3% retrieval | 49.5% answer
- **Target**: 43-50% E2E after optimization

---

## 📁 Critical Files

### Production Scripts
- `dspy_implementation/enhanced_miprov2_optimization.py` - Phase 1a optimization (RUN THIS)
- `quick_dev_eval.py` - Quick baseline evaluation (dev set)
- `colbert_text_only_evaluation.py` - ColBERT baseline (40.0%)

### Core Implementation
- `dspy_implementation/dspy_rag_enhanced.py` - Enhanced + Baseline RAG modules
- `dspy_implementation/dspy_metrics_enhanced.py` - Retrieval + answer + E2E metrics (FIXED Oct 9)
- `dspy_implementation/dspy_signatures_enhanced.py` - Query generation signatures
- `dspy_implementation/mlflow_tracking.py` - Experiment tracking

### Datasets
- `mmesgbench_dataset_corrected.json` - Authoritative 933 questions
- `dspy_implementation/data_splits/` - train (186), dev (93), test (654)

### Documentation
- `PHASE_1A_FINDINGS.md` - Critical bugs discovered Oct 9, 2025
- `BASELINE_COMPARISON.md` - Dev vs full dataset comparison
- `DSPy_RAG_Redesign_Plan.md` - Architecture design

---

## 🚀 Key Commands

```bash
# Environment
cd /Users/victoryim/Local_Git/CC
conda activate esg_reasoning

# Phase 1a Optimization (NEXT STEP)
python dspy_implementation/enhanced_miprov2_optimization.py 2>&1 | tee logs/phase1a_$(date +%Y%m%d_%H%M%S).log

# Monitor
mlflow ui  # http://localhost:5000
tail -f logs/phase1a_*.log

# Quick Baseline Check
python quick_dev_eval.py
```

---

## 🔧 Environment

```bash
# .env
DASHSCOPE_API_KEY=your_key_here
PG_URL=postgresql://user:pass@host:port/database
ESG_COLLECTION_NAME=MMESG

# Database
PostgreSQL + pgvector: 54,608 chunks from 45 documents

# Models
qwen-max (LLM) | text-embedding-v4 (embeddings)
```

---

## ⚠️ Known Issues & Fixes

### FIXED (Oct 9, 2025)
1. **Retrieval metric bug**: Was always returning 1.0 → Now correctly returns 0.0 for failures
   - **Impact**: ALL previous baselines (39.9%, 41.3%, 45.1%) were INVALID
   - **True baseline**: 38.7% (dev set with fixed metrics)

2. **MLFlow logging**: Script crashed before logging → Now logs BEFORE printing + saves artifacts

### Active
- None currently blocking optimization

---

## 📊 Phase 1a Architecture

**4-Stage Pipeline** (all optimizable via MIPROv2):
1. Query Generation → optimize retrieval queries
2. Retrieval → PostgreSQL + pgvector (top-5 chunks)
3. ESG Reasoning → Chain-of-thought analysis
4. Answer Extraction → Structured format extraction

**Metrics** (separate tracking):
- Retrieval accuracy (evidence pages found)
- Answer accuracy (correct answer extracted)
- End-to-end accuracy (both correct)

---

## 🎯 Next Action

Run Phase 1a optimization:
```bash
# Start optimization
python dspy_implementation/enhanced_miprov2_optimization.py 2>&1 | tee logs/phase1a_$(date +%Y%m%d_%H%M%S).log

# Expected: 45-90 minutes
# Target: 38.7% → 43-50% on dev set
```

After dev set optimization, validate on full 933 questions for MMESGBench comparison.
