# CLAUDE.md - Project Guidelines

## ⚠️ **MANDATORY: Coding Standards**

**ALL evaluation and optimization scripts MUST follow:**
📘 **[CODING_BEST_PRACTICES.md](CODING_BEST_PRACTICES.md)**

**Required for every script**:
- ✅ Checkpoint/resume mechanism (>10 min evals)
- ✅ Structured logging (file + console)
- ✅ Retry logic with exponential backoff
- ✅ MLFlow tracking (Phase 2+)
- ✅ Progress bars with tqdm
- ✅ Structured JSON output
- ✅ MMESGBench's exact eval_score()

**Reference**: `archive_old_project/code_old/colbert_full_dataset_evaluation.py`

---

## 🎯 Project: ESG Reasoning with DSPy Optimization

Replicate MMESGBench baselines, then optimize with DSPy to improve ESG question answering accuracy.

---

## 📊 Current Status (2025-10-13)

**✅ Project refactored** - Old code archived to `archive_old_project/`

**Key Discoveries**:
- Dataset corrections: Microsoft 2023→2024, UN Gender, ISO14001
- **ANLS 0.5**: MMESGBench uses fuzzy matching (50% similarity threshold)
- **PRIMARY METRIC**: Answer accuracy (for MMESGBench comparison)
- **RESEARCH METRICS**: Retrieval & E2E accuracy (for our analysis)

---

## 🏗️ Implementation Plan (4 Phases)

### Phase 1: MMESGBench Exact Replication
- **Goal**: ColBERT + Sentence Transformer (their exact approach)
- **Target**: ~40% answer accuracy
- **Location**: `phase1_mmesgbench_exact/` (TO BE CREATED)

### Phase 2: Qwen + PGvector Baseline
- **Goal**: Use existing Qwen embeddings + semantic search (NO ColBERT)
- **Data**: Existing PGvector (54,608 chunks) - **no re-parsing needed**
- **Target**: ~42% answer accuracy
- **Location**: `phase2_qwen_pgvector/` (TO BE CREATED)

### Phase 3a: DSPy Prompt Optimization (No Query Gen)
- **Goal**: Optimize reasoning + extraction prompts only
- **Target**: ~45% answer accuracy (+3% over Phase 2)
- **Location**: `phase3a_dspy_prompts/` (TO BE CREATED)

### Phase 3b: DSPy Query Generation
- **Goal**: Add query generation optimization
- **Target**: ~47% answer accuracy (+2% over Phase 3a)
- **Location**: `phase3b_dspy_query_gen/` (TO BE CREATED)

**Total Expected Improvement**: 40% → 47% (+7% answer accuracy)

See `PROJECT_REFACTORING_PLAN.md` for complete details.

---

## 📁 Project Structure

```
CC/
├── 📝 Essential Documentation
├── CLAUDE.md                        # This file (quick reference)
├── CHANGELOG.md                     # Progress tracking
├── PROJECT_REFACTORING_PLAN.md      # Complete implementation plan
├── ANLS_EVALUATION_EXPLAINED.md     # Evaluation methodology
├── Research Plan.md                  # Research proposal (Notion sync)
│
├── 📊 Core Data
├── mmesgbench_dataset_corrected.json # 933 QA pairs (authoritative)
├── source_documents/                 # 45 ESG PDF documents
│
├── 🏗️ Core Infrastructure (Preserved)
├── src/                              # Core Python modules
├── MMESGBench/                       # Reference benchmark
│
├── 🔧 Phase Implementations (TO BE CREATED)
├── phase1_mmesgbench_exact/         # Phase 1
├── phase2_qwen_pgvector/            # Phase 2
├── phase3a_dspy_prompts/            # Phase 3a
├── phase3b_dspy_query_gen/          # Phase 3b
├── unified_evaluator/               # Shared evaluation
│
└── 🗄️ Archive
    └── archive_old_project/          # All old work (for reference)
        ├── code_old/                  # Old Python scripts
        ├── results_old/               # Old JSON results
        ├── documentation_old/         # Old documentation
        ├── analysis_old/              # Old analysis
        └── logs_old/                  # Old logs
```

---

## 🔧 Environment

```bash
cd /Users/victoryim/Local_Git/CC
conda activate esg_reasoning

# .env variables
DASHSCOPE_API_KEY=your_key
PG_URL=postgresql://user:pass@host:port/database
ESG_COLLECTION_NAME=MMESG

# Database: PostgreSQL + pgvector (54,608 chunks from 45 documents)
# Models: qwen-max (LLM), text-embedding-v4 (embeddings)
```

---

## 📊 Evaluation Methodology

### PRIMARY METRIC: Answer Accuracy (MMESGBench comparison)
- Uses MMESGBench's exact `eval_score()` function
- **ANLS 0.5**: Fuzzy matching with 50% similarity threshold
- Allows typos, formatting differences (e.g., "North America" = "north america" = "Noth America")

### RESEARCH METRICS (our analysis only)
- **Retrieval Accuracy**: % questions with all evidence pages retrieved
- **E2E Accuracy**: Both retrieval AND answer correct

### Evaluation Code:
```python
from MMESGBench.src.eval.eval_score import eval_score

answer_score = eval_score(gt, pred, answer_type)
answer_correct = (answer_score >= 0.5)  # ANLS 0.5 threshold
```

See `ANLS_EVALUATION_EXPLAINED.md` for complete details.

---

## 🚀 Next Steps

1. ✅ **Cleanup complete** - Old work archived
2. ⏳ Implement unified evaluator
3. ⏳ Implement Phase 1 (MMESGBench exact replication)
4. ⏳ Implement Phase 2 (Qwen + PGvector)
5. ⏳ Implement Phase 3a (DSPy prompts)
6. ⏳ Implement Phase 3b (DSPy query gen)
7. ⏳ Generate unified comparison table

---

## 📝 Documentation Index

- **CLAUDE.md** (this file) - Quick project guidelines
- **CHANGELOG.md** - Historical progress tracking
- **PROJECT_REFACTORING_PLAN.md** - Complete 4-phase implementation plan
- **ANLS_EVALUATION_EXPLAINED.md** - Evaluation methodology reference
- **Research Plan.md** - Research proposal (sync with Notion occasionally)

---

## 💡 Key Reminders

- **Answer accuracy** is PRIMARY metric (not retrieval or E2E)
- **ANLS 0.5** allows fuzzy matching for fair comparison
- Phase 2 uses **existing PGvector data** (no re-parsing!)
- All old code preserved in `archive_old_project/`

---

**Last Updated**: 2025-10-13 (Project refactoring and cleanup)
