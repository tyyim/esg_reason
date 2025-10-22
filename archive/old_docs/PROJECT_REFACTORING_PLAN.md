# 🔄 Project Refactoring Plan - Clean Rebuild with Unified Evaluation

## 🎯 Objective
Build a robust, maintainable RAG pipeline with:
1. **Clear baseline replication** of MMESGBench ColBERT approach
2. **Secondary baseline** using our Qwen + PGvector infrastructure
3. **Unified evaluator** for fair comparison across all approaches
4. **Clean optimization path** with DSPy on top of established baselines

---

## 📋 Lessons Learned (Foundation for Rebuild)

### Dataset Corrections Applied
1. **Microsoft CDP Report**: Changed from 2023 to 2024 version
2. **UN Gender Report**: Downloaded correct file
3. **ISO14001**: Fixed filename reference
4. **Manual Answer Correction**: Labeled correct answers for Microsoft file questions

### Key Insights
- **Unified evaluation is critical**: Can't compare without consistent metrics
- **Need two baselines**: (1) Exact MMESGBench replication, (2) Our optimized infrastructure
- **Answer accuracy for MMESGBench comparison**: Retrieval and E2E are for our own research only
- **MMESGBench gaps**: They use k=5 retrieval + Sentence Transformer parsing (not documented)

---

## 🏗️ New Project Structure

```
/Users/victoryim/Local_Git/CC/
│
├── 📊 CORE DATASET (Authoritative Source)
│   ├── mmesgbench_dataset_corrected.json          # 933 QA pairs (our corrections applied)
│   └── source_documents/                           # 45 PDF documents (corrected versions)
│
├── 🎯 PHASE 1: MMESGBench Exact Replication
│   ├── phase1_mmesgbench_exact/
│   │   ├── colbert_exact_replication.py            # Exact MMESGBench ColBERT (k=5, SentenceTransformer)
│   │   ├── sentence_transformer_chunker.py         # Their parsing logic
│   │   └── phase1_results.json                     # Target: ~40% answer accuracy
│   │
│   └── README_PHASE1.md                            # Implementation notes
│
├── 🎯 PHASE 2: Our Qwen + PGvector Baseline
│   ├── phase2_qwen_pgvector/
│   │   ├── qwen_semantic_baseline.py               # Qwen embeddings + PGvector semantic search (NO ColBERT)
│   │   ├── vector_store_manager.py                 # PGvector database manager (already populated)
│   │   └── phase2_results.json                     # Our baseline performance
│   │
│   └── README_PHASE2.md                            # Implementation notes
│
├── 🎯 PHASE 3a: DSPy Prompt Optimization (No Query Gen)
│   ├── phase3a_dspy_prompts/
│   │   ├── dspy_baseline_rag.py                    # DSPy RAG WITHOUT query generation
│   │   ├── miprov2_optimizer.py                    # MIPROv2 for reasoning + extraction prompts
│   │   ├── dspy_signatures.py                      # ReasoningSignature + ExtractionSignature
│   │   └── phase3a_results.json                    # Prompt optimization results
│   │
│   └── README_PHASE3a.md                           # Implementation notes
│
├── 🎯 PHASE 3b: DSPy Query Generation Optimization
│   ├── phase3b_dspy_query_gen/
│   │   ├── dspy_enhanced_rag.py                    # Add query generation to Phase 3a
│   │   ├── miprov2_optimizer.py                    # MIPROv2 for full pipeline
│   │   ├── dspy_signatures.py                      # QueryGeneration + others
│   │   └── phase3b_results.json                    # Full optimization results
│   │
│   └── README_PHASE3b.md                           # Implementation notes
│
├── 🔧 UNIFIED EVALUATION INFRASTRUCTURE
│   ├── unified_evaluator/
│   │   ├── evaluator.py                            # Single source of truth for evaluation
│   │   ├── metrics.py                              # Retrieval, Answer, E2E metrics
│   │   ├── mmesgbench_eval_logic.py               # Import their exact eval_score()
│   │   └── comparison_reporter.py                  # Generate comparison tables
│   │
│   └── README_EVALUATOR.md                         # Usage guide
│
├── 🗄️ SHARED INFRASTRUCTURE
│   ├── src/
│   │   ├── models/qwen_api.py                      # Qwen API client
│   │   ├── retrieval/colbert_retriever.py          # ColBERT retrieval module
│   │   ├── database/pgvector_manager.py            # PostgreSQL + pgvector
│   │   └── processing/pdf_processor.py             # Document processing
│   │
│   └── configs/
│       ├── phase1_config.yaml                      # MMESGBench exact config
│       ├── phase2_config.yaml                      # Our baseline config
│       └── phase3_config.yaml                      # DSPy optimization config
│
├── 📈 RESULTS & ANALYSIS
│   ├── results/
│   │   ├── phase1_mmesgbench_exact_results.json
│   │   ├── phase2_qwen_pgvector_results.json
│   │   ├── phase3_dspy_optimized_results.json
│   │   └── unified_comparison.json                 # Master comparison table
│   │
│   └── analysis/
│       ├── error_analysis.md
│       └── performance_breakdown.md
│
└── 🗂️ ARCHIVE (Old Work)
    ├── archive_old_project/
    │   ├── dspy_implementation/                    # Old DSPy work
    │   ├── colbert_text_only_evaluation.py        # Previous ColBERT
    │   └── [all previous scripts]
    │
    └── README_ARCHIVE.md                           # What was archived and why
```

---

## 📐 Phase Breakdown

### **PHASE 1: MMESGBench Exact Replication** 🎯
**Goal**: Establish true baseline by replicating their approach exactly

**Implementation**:
```python
# phase1_mmesgbench_exact/colbert_exact_replication.py

class MMESGBenchExactReplication:
    """
    Exact replication of MMESGBench ColBERT approach
    - Sentence Transformer for chunking/parsing
    - ColBERT for retrieval with k=5
    - Qwen-max for two-stage extraction
    - Their exact prompt templates
    """

    def __init__(self):
        self.chunker = SentenceTransformerChunker()  # Their parsing
        self.retriever = ColBERTRetriever(top_k=5)    # k=5 as they used
        self.llm = QwenAPIClient(model="qwen-max")

    def process_question(self, question: str) -> dict:
        # 1. Retrieve top-5 chunks with ColBERT
        chunks = self.retriever.retrieve(question, k=5)

        # 2. Two-stage extraction (their exact prompts)
        context = "\n\n".join(chunks)
        answer = self.llm.extract_answer(question, context)

        return {
            'question': question,
            'retrieved_chunks': chunks,
            'answer': answer
        }
```

**Key Configuration** (`configs/phase1_config.yaml`):
```yaml
phase: 1_mmesgbench_exact
retrieval:
  method: colbert
  top_k: 5
  model: colbert-ir/colbertv2.0
chunking:
  method: sentence_transformer
  model: sentence-transformers/all-MiniLM-L6-v2
  chunk_size: 512
llm:
  model: qwen-max
  temperature: 0.1
evaluation:
  metrics: [retrieval_accuracy, answer_accuracy, e2e_accuracy]
```

**Expected Results**:
- **Answer Accuracy**: ~40% (matching MMESGBench paper)
- **Retrieval Accuracy**: ~50-60% (our estimate)
- **E2E Accuracy**: ~35-40% (our estimate)

**Output**: `results/phase1_mmesgbench_exact_results.json`

---

### **PHASE 2: Our Qwen + PGvector Baseline** 🚀
**Goal**: Establish our infrastructure baseline using existing Qwen embeddings + PGvector

**Implementation**:
```python
# phase2_qwen_pgvector/qwen_semantic_baseline.py

class QwenSemanticBaseline:
    """
    Our baseline using existing infrastructure:
    - Qwen text-embedding-v4 (1024-dim) embeddings
    - PGvector semantic search (already populated with 54,608 chunks)
    - Top-5 retrieval for fair comparison
    - Qwen-max for two-stage extraction

    NOTE: We do NOT use ColBERT - just pure semantic search
    NOTE: Data is already parsed and indexed - no re-parsing needed
    """

    def __init__(self):
        # Use existing PGvector database (already populated)
        self.vector_store = PGVectorManager(
            embedding_model="text-embedding-v4",
            dimension=1024,
            collection_name="MMESG"  # Existing collection
        )
        self.llm = QwenAPIClient(model="qwen-max")

    def process_question(self, question: str) -> dict:
        # 1. Semantic search with Qwen embeddings (NO ColBERT)
        # Get top-5 chunks from existing PGvector index
        chunks = self.vector_store.semantic_search(
            query=question,
            top_k=5
        )

        # 2. Two-stage extraction
        context = "\n\n".join([c.text for c in chunks])
        answer = self.llm.extract_answer(question, context)

        return {
            'question': question,
            'retrieved_chunks': [c.text for c in chunks],
            'retrieved_pages': [c.page_num for c in chunks],
            'answer': answer,
            'similarity_scores': [c.score for c in chunks]
        }
```

**Key Configuration** (`configs/phase2_config.yaml`):
```yaml
phase: 2_qwen_pgvector
retrieval:
  method: semantic_search  # Pure Qwen embedding similarity (NOT ColBERT)
  top_k: 5
  embedding_model: text-embedding-v4
  vector_store: pgvector
  collection_name: MMESG  # Use existing collection (54,608 chunks)
data:
  use_existing: true  # Data already parsed and indexed
  no_reparse: true    # Do NOT re-parse documents
llm:
  model: qwen-max
  temperature: 0.1
evaluation:
  metrics: [retrieval_accuracy, answer_accuracy, e2e_accuracy]
  primary_comparison: answer_accuracy  # For MMESGBench comparison
```

**Expected Results**:
- **Answer Accuracy**: 40-45% (primary metric for MMESGBench comparison)
- **Retrieval Accuracy**: 55-65% (for our research)
- **E2E Accuracy**: 38-42% (for our research)

**Output**: `results/phase2_qwen_pgvector_results.json`

---

### **PHASE 3a: DSPy Prompt Optimization (No Query Gen)** 🧠
**Goal**: Optimize reasoning and extraction prompts WITHOUT query generation

**Implementation**:
```python
# phase3a_dspy_prompts/dspy_baseline_rag.py

import dspy

class ReasoningSignature(dspy.Signature):
    """Analyze question and context to reason about answer"""
    question = dspy.InputField(desc="Question to answer")
    context = dspy.InputField(desc="Retrieved context chunks")
    reasoning = dspy.OutputField(desc="Step-by-step reasoning")

class ExtractionSignature(dspy.Signature):
    """Extract precise answer from context based on reasoning"""
    question = dspy.InputField()
    context = dspy.InputField()
    reasoning = dspy.InputField()
    answer = dspy.OutputField(desc="Extracted answer in required format")

class DSPyBaselineRAG(dspy.Module):
    """
    DSPy RAG WITHOUT query generation
    - Use Phase 2 retrieval as-is (no query optimization)
    - Optimize reasoning prompts
    - Optimize extraction prompts
    - MIPROv2 for prompt optimization only
    """

    def __init__(self, baseline_retriever):
        super().__init__()
        self.baseline_retriever = baseline_retriever
        self.reason = dspy.ChainOfThought(ReasoningSignature)
        self.extract = dspy.ChainOfThought(ExtractionSignature)

    def forward(self, question: str) -> str:
        # 1. Retrieve with baseline (NO query generation)
        chunks = self.baseline_retriever.retrieve(question, k=5)
        context = "\n\n".join([c.text for c in chunks])

        # 2. Reason about answer (learnable)
        reasoning = self.reason(question=question, context=context).reasoning

        # 3. Extract answer (learnable)
        answer = self.extract(
            question=question,
            context=context,
            reasoning=reasoning
        ).answer

        return answer
```

**Optimization Script** (`phase3a_dspy_prompts/miprov2_optimizer.py`):
```python
# MIPROv2 optimization for prompts only (no query gen)
from dspy.teleprompt import MIPROv2

# Load Phase 2 baseline
baseline = QwenSemanticBaseline()

# Create DSPy module (no query generation)
dspy_rag = DSPyBaselineRAG(baseline_retriever=baseline.vector_store)

# Optimize with MIPROv2 (prompts only)
teleprompter = MIPROv2(
    metric=answer_accuracy_metric,  # Focus on answer accuracy
    num_candidates=10,
    init_temperature=1.0
)

optimized_rag = teleprompter.compile(
    dspy_rag,
    trainset=trainset,
    valset=devset,
    num_trials=100
)

# Evaluate
results = evaluate_on_full_dataset(optimized_rag)
```

**Key Configuration** (`configs/phase3a_config.yaml`):
```yaml
phase: 3a_dspy_prompts
base_phase: 2_qwen_pgvector  # Build on Phase 2
optimization:
  method: miprov2
  num_candidates: 10
  num_trials: 100
  metric: answer_accuracy  # Primary metric for MMESGBench comparison
  components:
    - reasoning_prompts: optimizable
    - extraction_prompts: optimizable
  exclude:
    - query_generation: disabled  # NO query generation in Phase 3a
llm:
  model: qwen-max
  temperature: 0.1
evaluation:
  metrics: [retrieval_accuracy, answer_accuracy, e2e_accuracy]
  primary_comparison: answer_accuracy  # For MMESGBench
```

**Expected Results**:
- **Answer Accuracy**: 43-47% (+3-5% over Phase 2) - PRIMARY METRIC
- **Retrieval Accuracy**: 55-65% (unchanged from Phase 2)
- **E2E Accuracy**: 40-44% (for our research)

**Output**: `results/phase3a_dspy_prompts_results.json`

---

### **PHASE 3b: DSPy Query Generation Optimization** 🚀
**Goal**: Add query generation optimization on top of Phase 3a

**Implementation**:
```python
# phase3b_dspy_query_gen/dspy_enhanced_rag.py

import dspy

class QueryGeneration(dspy.Signature):
    """Generate optimized retrieval query from question"""
    question = dspy.InputField(desc="Original question")
    optimized_query = dspy.OutputField(desc="Reformulated query for better retrieval")

class ReasoningSignature(dspy.Signature):
    """Analyze question and context to reason about answer"""
    question = dspy.InputField()
    context = dspy.InputField()
    reasoning = dspy.OutputField()

class ExtractionSignature(dspy.Signature):
    """Extract precise answer from context"""
    question = dspy.InputField()
    context = dspy.InputField()
    reasoning = dspy.InputField()
    answer = dspy.OutputField()

class DSPyEnhancedRAG(dspy.Module):
    """
    Full DSPy optimization with query generation
    - Optimizable query generation (NEW in Phase 3b)
    - Optimizable reasoning (from Phase 3a)
    - Optimizable extraction (from Phase 3a)
    - MIPROv2 for full pipeline optimization
    """

    def __init__(self, baseline_retriever):
        super().__init__()
        self.baseline_retriever = baseline_retriever
        self.query_gen = dspy.ChainOfThought(QueryGeneration)  # NEW
        self.reason = dspy.ChainOfThought(ReasoningSignature)
        self.extract = dspy.ChainOfThought(ExtractionSignature)

    def forward(self, question: str) -> str:
        # 1. Generate optimized query (NEW - learnable)
        optimized_query = self.query_gen(question=question).optimized_query

        # 2. Retrieve with optimized query
        chunks = self.baseline_retriever.retrieve(optimized_query, k=5)
        context = "\n\n".join([c.text for c in chunks])

        # 3. Reason about answer (learnable)
        reasoning = self.reason(question=question, context=context).reasoning

        # 4. Extract answer (learnable)
        answer = self.extract(
            question=question,
            context=context,
            reasoning=reasoning
        ).answer

        return answer
```

**Optimization Script** (`phase3b_dspy_query_gen/miprov2_optimizer.py`):
```python
# MIPROv2 optimization for full pipeline (including query gen)
from dspy.teleprompt import MIPROv2

# Load Phase 2 baseline
baseline = QwenSemanticBaseline()

# Load Phase 3a optimized prompts as starting point
phase3a_rag = load_checkpoint("phase3a_optimized.json")

# Create enhanced RAG with query generation
dspy_rag = DSPyEnhancedRAG(baseline_retriever=baseline.vector_store)
# Initialize reasoning + extraction from Phase 3a
dspy_rag.reason = phase3a_rag.reason
dspy_rag.extract = phase3a_rag.extract

# Optimize full pipeline (focus on query generation)
teleprompter = MIPROv2(
    metric=e2e_accuracy_metric,  # Use E2E since retrieval is now optimizable
    num_candidates=10,
    init_temperature=1.0
)

optimized_rag = teleprompter.compile(
    dspy_rag,
    trainset=trainset,
    valset=devset,
    num_trials=100
)

# Evaluate
results = evaluate_on_full_dataset(optimized_rag)
```

**Key Configuration** (`configs/phase3b_config.yaml`):
```yaml
phase: 3b_dspy_query_gen
base_phase: 3a_dspy_prompts  # Build on Phase 3a
optimization:
  method: miprov2
  num_candidates: 10
  num_trials: 100
  metric: e2e_accuracy  # Now include retrieval improvement
  components:
    - query_generation: optimizable  # NEW in Phase 3b
    - reasoning_prompts: optimizable  # Continued from Phase 3a
    - extraction_prompts: optimizable  # Continued from Phase 3a
  warm_start:
    from_phase: 3a  # Start with Phase 3a optimized prompts
llm:
  model: qwen-max
  temperature: 0.1
evaluation:
  metrics: [retrieval_accuracy, answer_accuracy, e2e_accuracy]
  primary_comparison: answer_accuracy  # For MMESGBench
```

**Expected Results**:
- **Answer Accuracy**: 45-50% (+2-3% over Phase 3a) - PRIMARY METRIC
- **Retrieval Accuracy**: 60-70% (+5-10% over Phase 2 via query optimization)
- **E2E Accuracy**: 43-48% (for our research)

**Output**: `results/phase3b_dspy_query_gen_results.json`

---

## 🔧 Unified Evaluator Implementation

### Core Evaluator (`unified_evaluator/evaluator.py`)

```python
class UnifiedEvaluator:
    """
    Single source of truth for all evaluations
    - Uses MMESGBench's exact eval_score() logic
    - Calculates retrieval, answer, and E2E accuracy
    - Handles all file formats (Phase 1/2/3 outputs)
    """

    def __init__(self, ground_truth_path: str):
        self.ground_truth = load_json(ground_truth_path)
        self.mmesgbench_eval = import_mmesgbench_eval_score()

    def evaluate(self, predictions: List[dict]) -> dict:
        """
        Evaluate predictions with comprehensive metrics

        Args:
            predictions: List of {question, answer, retrieved_pages, context}

        Returns:
            {
                'retrieval_accuracy': float,
                'answer_accuracy': float,
                'e2e_accuracy': float,
                'by_format': {...},
                'detailed_results': [...]
            }
        """
        results = {
            'total': len(predictions),
            'retrieval_correct': 0,
            'answer_correct': 0,
            'e2e_correct': 0,
            'by_format': {}
        }

        for pred in predictions:
            gt = self._find_ground_truth(pred['question'])

            # 1. Retrieval accuracy
            retrieval_ok = self._check_retrieval(
                pred.get('retrieved_pages', []),
                gt['evidence_pages']
            )

            # 2. Answer accuracy (MMESGBench exact logic)
            answer_score = self.mmesgbench_eval(
                gt['answer'],
                pred['answer'],
                gt['answer_format']
            )
            answer_ok = (answer_score >= 0.5)

            # 3. E2E accuracy
            e2e_ok = retrieval_ok and answer_ok

            # Update counters
            if retrieval_ok:
                results['retrieval_correct'] += 1
            if answer_ok:
                results['answer_correct'] += 1
            if e2e_ok:
                results['e2e_correct'] += 1

        # Calculate percentages
        total = results['total']
        results['retrieval_accuracy'] = results['retrieval_correct'] / total
        results['answer_accuracy'] = results['answer_correct'] / total
        results['e2e_accuracy'] = results['e2e_correct'] / total

        return results
```

### Comparison Reporter (`unified_evaluator/comparison_reporter.py`)

```python
class ComparisonReporter:
    """Generate comparison tables across all phases"""

    def generate_comparison(self, all_results: dict):
        """
        Create unified comparison table
        PRIMARY METRIC: Answer Accuracy (for MMESGBench comparison)
        RESEARCH METRICS: Retrieval & E2E (for our own analysis)

        Input:
            {
                'Phase 1 - MMESGBench Exact': {...},
                'Phase 2 - Qwen + PGvector': {...},
                'Phase 3a - DSPy Prompts': {...},
                'Phase 3b - DSPy Query Gen': {...}
            }
        """
        print("=" * 110)
        print("📊 UNIFIED COMPARISON - All Phases")
        print("PRIMARY METRIC: Answer Accuracy (MMESGBench comparison)")
        print("RESEARCH METRICS: Retrieval & E2E (our analysis)")
        print("=" * 110)
        print(f"{'Phase':<35} {'Answer (PRIMARY)':<20} {'Retrieval':<15} {'E2E':<15} {'Notes':<20}")
        print("-" * 110)

        for phase_name, results in all_results.items():
            retr = results['retrieval_accuracy']
            ans = results['answer_accuracy']
            e2e = results['e2e_accuracy']

            # Highlight answer accuracy as primary metric
            print(f"{phase_name:<35} {ans:>15.1%} ⭐  {retr:>12.1%}  {e2e:>12.1%}  {notes}")
```

---

## 🚀 Implementation Sequence

### **Step 1: Archive Old Work** (Day 1)
```bash
# Create archive directory
mkdir -p archive_old_project

# Move old implementation files
mv dspy_implementation/ archive_old_project/
mv colbert_text_only_evaluation.py archive_old_project/
mv robust_colpali_evaluation.py archive_old_project/
mv enhanced_rag_evaluation.py archive_old_project/
mv [other old scripts] archive_old_project/

# Keep only essential files
# - mmesgbench_dataset_corrected.json
# - source_documents/
# - src/ (core infrastructure)
# - MMESGBench/ (reference repo)
```

### **Step 2: Build Unified Evaluator** (Day 1)
```bash
# Create evaluator infrastructure
mkdir -p unified_evaluator
cd unified_evaluator

# Implement core evaluator
# - evaluator.py (main evaluation logic)
# - metrics.py (retrieval, answer, E2E metrics)
# - mmesgbench_eval_logic.py (import their eval_score)
# - comparison_reporter.py (generate tables)

# Test evaluator on existing results
python test_evaluator.py
```

### **Step 3: Implement Phase 1** (Day 2)
```bash
# Create Phase 1 directory
mkdir -p phase1_mmesgbench_exact

# Implement exact replication
# - colbert_exact_replication.py
# - sentence_transformer_chunker.py
# - configs/phase1_config.yaml

# Run Phase 1 evaluation
python phase1_mmesgbench_exact/colbert_exact_replication.py

# Evaluate with unified evaluator
python unified_evaluator/evaluator.py \
  --predictions results/phase1_mmesgbench_exact_results.json \
  --output results/phase1_evaluation.json
```

**Expected Output**:
```
Phase 1 - MMESGBench Exact Replication
Retrieval Accuracy: ~55%
Answer Accuracy: ~40%
E2E Accuracy: ~35%
```

### **Step 4: Implement Phase 2** (Day 3)
```bash
# Create Phase 2 directory
mkdir -p phase2_qwen_pgvector

# Implement Qwen + PGvector baseline
# - qwen_semantic_baseline.py (use existing PGvector data)
# - vector_store_manager.py
# - configs/phase2_config.yaml

# NO need to index - use existing PGvector database (54,608 chunks)

# Run Phase 2 evaluation
python phase2_qwen_pgvector/qwen_semantic_baseline.py

# Evaluate with unified evaluator
python unified_evaluator/evaluator.py \
  --predictions results/phase2_qwen_pgvector_results.json \
  --output results/phase2_evaluation.json
```

**Expected Output**:
```
Phase 2 - Qwen + PGvector Baseline
Answer Accuracy: ~42% ⭐ (PRIMARY - for MMESGBench comparison)
Retrieval Accuracy: ~60% (research metric)
E2E Accuracy: ~38% (research metric)
```

### **Step 5: Implement Phase 3a** (Day 4)
```bash
# Create Phase 3a directory
mkdir -p phase3a_dspy_prompts

# Implement DSPy prompt optimization (NO query generation)
# - dspy_baseline_rag.py
# - miprov2_optimizer.py
# - dspy_signatures.py (Reasoning + Extraction only)
# - configs/phase3a_config.yaml

# Run MIPROv2 optimization (45-90 minutes)
python phase3a_dspy_prompts/miprov2_optimizer.py

# Evaluate with unified evaluator
python unified_evaluator/evaluator.py \
  --predictions results/phase3a_dspy_prompts_results.json \
  --output results/phase3a_evaluation.json
```

**Expected Output**:
```
Phase 3a - DSPy Prompt Optimization (No Query Gen)
Answer Accuracy: ~45% ⭐ (PRIMARY - +3% over Phase 2)
Retrieval Accuracy: ~60% (unchanged - no query optimization)
E2E Accuracy: ~41% (research metric)
```

### **Step 6: Implement Phase 3b** (Day 5)
```bash
# Create Phase 3b directory
mkdir -p phase3b_dspy_query_gen

# Implement DSPy query generation optimization
# - dspy_enhanced_rag.py (add query generation)
# - miprov2_optimizer.py
# - dspy_signatures.py (QueryGen + Reasoning + Extraction)
# - configs/phase3b_config.yaml

# Run MIPROv2 optimization (45-90 minutes)
# Start from Phase 3a optimized prompts
python phase3b_dspy_query_gen/miprov2_optimizer.py

# Evaluate with unified evaluator
python unified_evaluator/evaluator.py \
  --predictions results/phase3b_dspy_query_gen_results.json \
  --output results/phase3b_evaluation.json
```

**Expected Output**:
```
Phase 3b - DSPy Query Generation Optimization
Answer Accuracy: ~47% ⭐ (PRIMARY - +2% over Phase 3a, +7% over Phase 1)
Retrieval Accuracy: ~65% (improved via query optimization)
E2E Accuracy: ~43% (research metric)
```

### **Step 7: Generate Final Comparison** (Day 5)
```bash
# Generate unified comparison table
python unified_evaluator/comparison_reporter.py \
  --phase1 results/phase1_evaluation.json \
  --phase2 results/phase2_evaluation.json \
  --phase3a results/phase3a_evaluation.json \
  --phase3b results/phase3b_evaluation.json \
  --output results/unified_comparison.json
```

**Expected Final Table**:
```
==============================================================================================================
📊 UNIFIED COMPARISON - All Phases
PRIMARY METRIC: Answer Accuracy (MMESGBench comparison)
RESEARCH METRICS: Retrieval & E2E (our analysis)
==============================================================================================================
Phase                               Answer (PRIMARY)     Retrieval       E2E             Notes
--------------------------------------------------------------------------------------------------------------
Phase 1 - MMESGBench Exact              40.0% ⭐             55.0%          35.0%  ✅ Baseline replication
Phase 2 - Qwen + PGvector               42.0% ⭐             60.0%          38.0%  ✅ +2% answer via embeddings
Phase 3a - DSPy Prompts                 45.0% ⭐             60.0%          41.0%  ✅ +3% answer via prompts
Phase 3b - DSPy Query Gen               47.0% ⭐             65.0%          43.0%  ✅ +2% answer via queries
==============================================================================================================
TOTAL IMPROVEMENT: 40% → 47% (+7% answer accuracy for MMESGBench comparison)
==============================================================================================================
```

---

## 📊 Key Metrics to Track

### PRIMARY METRIC (for MMESGBench comparison):
1. **Answer Accuracy**: % of questions with correct answer (ignoring retrieval)
   - This is the metric reported in MMESGBench paper
   - Used for fair comparison with their baselines

### RESEARCH METRICS (for our own analysis):
2. **Retrieval Accuracy**: % of questions where all evidence pages retrieved
3. **E2E Accuracy**: % of questions with both correct retrieval AND answer
4. **By Format**: Breakdown by answer type (Int, Float, List, etc.)
5. **By Document**: Breakdown by source document

### Comparison Metrics:
1. **Phase 1 → Phase 2**: Improvement from Sentence Transformer → Qwen embeddings (~+2% answer)
2. **Phase 2 → Phase 3a**: Improvement from DSPy prompt optimization (~+3% answer)
3. **Phase 3a → Phase 3b**: Improvement from DSPy query generation (~+2% answer)
4. **Phase 1 → Phase 3b**: Total improvement from baseline to fully optimized (~+7% answer)

---

## 🎯 Success Criteria

### Phase 1 Success:
- ✅ Achieve ~40% **answer accuracy** (matching MMESGBench paper) - PRIMARY
- ✅ Exact replication of their ColBERT + Sentence Transformer approach
- ✅ Unified evaluator produces consistent metrics

### Phase 2 Success:
- ✅ Achieve 40-45% **answer accuracy** (≥ Phase 1) - PRIMARY
- ✅ Leverage existing Qwen + PGvector infrastructure (no re-parsing)
- ✅ Establish solid baseline for DSPy optimization

### Phase 3a Success:
- ✅ Achieve 43-47% **answer accuracy** (+3-5% over Phase 2) - PRIMARY
- ✅ Optimize reasoning + extraction prompts (NO query generation)
- ✅ Demonstrate DSPy prompt optimization effectiveness

### Phase 3b Success:
- ✅ Achieve 45-50% **answer accuracy** (+2-3% over Phase 3a) - PRIMARY
- ✅ Add query generation optimization
- ✅ Show retrieval improvement via query reformulation

### Overall Success:
- ✅ Clear MMESGBench baseline established (Phase 1: **40% answer**)
- ✅ Infrastructure improvement validated (Phase 2: **42% answer** via embeddings)
- ✅ Prompt optimization validated (Phase 3a: **45% answer** via DSPy)
- ✅ Query optimization validated (Phase 3b: **47% answer** via query gen)
- ✅ **Total improvement: +7% answer accuracy (40% → 47%) for MMESGBench comparison**

---

## 🗂️ File Management

### Keep:
- `mmesgbench_dataset_corrected.json` - Authoritative dataset
- `source_documents/` - 45 corrected PDF documents
- `src/` - Core infrastructure (Qwen API, database, processing)
- `MMESGBench/` - Reference repository
- `.env` - Environment configuration

### Archive:
- All old evaluation scripts → `archive_old_project/`
- Previous DSPy implementation → `archive_old_project/dspy_implementation/`
- Old prediction files → `archive_old_project/old_predictions/`
- Previous analysis docs → `archive_old_project/old_analysis/`

### New Structure:
- `phase1_mmesgbench_exact/` - Phase 1 implementation (MMESGBench exact replication)
- `phase2_qwen_pgvector/` - Phase 2 implementation (Qwen semantic search baseline)
- `phase3a_dspy_prompts/` - Phase 3a implementation (DSPy prompt optimization, no query gen)
- `phase3b_dspy_query_gen/` - Phase 3b implementation (DSPy with query generation)
- `unified_evaluator/` - Shared evaluation infrastructure
- `results/` - All evaluation results
- `configs/` - Configuration files

---

## 📝 Documentation Requirements

### For Each Phase:
1. **README_PHASE{N}.md**:
   - Implementation approach
   - Key design decisions
   - Configuration details
   - Expected results
   - How to run

2. **Implementation Code**:
   - Clear docstrings
   - Type hints
   - Example usage
   - Error handling

3. **Results File**:
   - Timestamp
   - Configuration used
   - Full evaluation metrics
   - Detailed results per question

### Master Documentation:
1. **PROJECT_README.md**: Overview of entire project
2. **UNIFIED_EVALUATOR.md**: How to use evaluator
3. **RESULTS_COMPARISON.md**: Analysis of all phases
4. **LESSONS_LEARNED.md**: Key insights and discoveries

---

## 🚀 Next Steps

### Immediate Actions (This Session):
1. ✅ Review and approve this refactoring plan
2. Create archive directory and move old files
3. Create new directory structure
4. Implement unified evaluator (core infrastructure)

### Short-term Actions (Next Session):
5. Implement Phase 1 (MMESGBench exact replication)
6. Implement Phase 2 (Qwen + PGvector baseline - use existing data)
7. Implement Phase 3a (DSPy prompt optimization - no query gen)
8. Implement Phase 3b (DSPy query generation optimization)
9. Generate final comparison table

### Long-term Actions:
10. Write comprehensive documentation
11. Create reproducible run scripts
12. Publish results and analysis

---

## ✅ Approval Checklist

Before proceeding, confirm:
- [ ] Directory structure makes sense
- [ ] Three phases clearly defined
- [ ] Unified evaluator approach is correct
- [ ] Success criteria are reasonable
- [ ] Implementation sequence is logical
- [ ] Ready to archive old work and start fresh

---

**Ready to begin refactoring? Confirm to proceed with Step 1 (Archive old work).**
