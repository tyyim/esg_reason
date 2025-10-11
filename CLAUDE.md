# CLAUDE.md - ESG Reasoning Research

> **Maintenance**: See `.claude/CLAUDE_MD_GUIDELINES.md` | Keep concise - scannable in 30 seconds
> **Details**: Historical findings in `PHASE_1A_FINDINGS.md`, `BASELINE_COMPARISON.md`, `Research Plan — ESG Reasoning and Green Finance.md`

---

## 🎯 Current Focus

**Phase 1a Test**: Baseline prompt optimization (reasoning + extraction only, NO query generation)

**Status**: Ready to run - Configuration verified ✅

**Current Baseline** (Oct 12, 2025 - Full dataset with "Not answerable" fix):
- **Full dataset (933)**: 55.6% accuracy (519/933 correct)
- **Dev set (93)**: TBD (will evaluate as part of optimization)
- **Target**: +3-5% improvement from prompt optimization alone

**What We're Testing**: Can MIPROv2 optimize reasoning + extraction prompts to improve baseline?

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

### FIXED (Oct 12, 2025)
1. **"Not answerable" handling**: DSPy signatures didn't explicitly instruct model to output "Not answerable"
   - **Impact**: 0% accuracy on 150 "Not answerable" questions
   - **Fix**: Updated ESGReasoning and AnswerExtraction signatures with explicit instructions
   - **Result**: 37.3% → 55.6% accuracy (+18.3%)

### FIXED (Oct 11, 2025)
2. **Baseline calculation**: Was merging files instead of substituting corrected results
   - **Fix**: Created `substitute_corrected_results.py` to properly substitute 16 questions
   - **Corrected MMESGBench baseline**: 40.51% (vs our 55.6%)

### FIXED (Oct 9, 2025)
3. **Retrieval metric bug**: Was always returning 1.0 → Now correctly returns 0.0 for failures
   - **Impact**: ALL previous baselines (39.9%, 41.3%, 45.1%) were INVALID
   - **True baseline**: 38.7% (dev set with fixed metrics)

4. **MLFlow logging**: Script crashed before logging → Now logs BEFORE printing + saves artifacts

### Active
- None currently blocking optimization

### Process Improvements (Oct 12, 2025)
- ✅ Created CHANGELOG.md to track all changes
- ✅ Established workflow: Read CLAUDE.md → Update docs → Verify config → Run → Document
- ⏳ TODO: Clean up debug scripts (move to archive/)

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
