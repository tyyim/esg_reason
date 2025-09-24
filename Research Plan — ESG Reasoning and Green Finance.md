# Research Plan — ESG Reasoning and Green Finance Benchmark

## 📋 **Research Methodology & Implementation History**

### Core Research Question
Can DSPy/GEPA match or exceed lightweight parameter tuning (LoRA + small-RL) on ESG QA and green finance numeric reasoning with lower compute and fewer labels, building upon a properly replicated MMESGBench baseline?

### Implementation Evolution

**Phase 0A - Sequential Replication (Completed)**
- Successfully replicated MMESGBench's primitive sequential approach (20% accuracy)
- Discovered content accessibility limitations (evidence on pages 61+)
- Established two-stage extraction pipeline (basic → qwen-max)

**Phase 0B - Retrieval Implementation (Current)**
- Implementing ColBERT text RAG (target: 41.5% accuracy)
- Implementing ColPali visual RAG (target: 51.8% accuracy)
- Focus shifted from primitive to sophisticated MMESGBench approaches

**Phase 1 - DSPy Enhancement (Next)**
- Wrap retrieval approaches in DSPy modules
- Apply GEPA optimizer on working baseline
- Maintain MMESGBench evaluation compatibility

**Phase 2 - Comparative Analysis (Future)**
- LoRA + small-RL implementation
- Statistical significance validation
- Efficiency comparison

## 🎯 **Research Hypotheses**

- **H1 Replication**: MMESGBench retrieval approaches (41.5%/51.8%) significantly outperform sequential (20%/40%)
- **H2a Efficiency**: DSPy/GEPA ≥ retrieval baseline accuracy with fewer labels and lower compute cost
- **H2b Robustness**: DSPy/GEPA > zero/few-shot on cross-page and visual evidence tasks
- **H2c Stability**: DSPy/GEPA lower variance across seeds than fine-tuning on numeric tasks
- **H2d Multimodal**: Visual RAG (ColPali) > text-only RAG on chart/table questions

## 📊 **Experimental Design**

### Dataset & Evaluation Framework
- **Dataset**: MMESGBench (933 QA pairs, 45 ESG documents)
- **Test Focus**: AR6 Synthesis Report (186 pages, 10 sample questions)
- **Answer Formats**: String (32%), Integer (22%), Float (16%), List (14%), Unanswerable (16%)
- **Evidence Types**: Text, tables, charts, images, layout-aware content

### Metrics & Scoring
- **Primary**: Answer accuracy with ±1% numeric tolerance
- **Secondary**: Exact match, F1 score, evidence page retrieval
- **Efficiency**: GPU hours, API cost, processing time
- **Robustness**: Cross-page reasoning, visual content analysis

### Evaluation Pipeline (Replicated from MMESGBench)
1. **Document Processing**: PDF → chunks/images (MMESGBench-compliant)
2. **Retrieval**: ColBERT (text) or ColPali (visual) top-5 selection
3. **Generation**: Qwen models with two-stage extraction
4. **Scoring**: MMESGBench evaluation framework with tolerance handling

## 🔬 **Detailed Implementation History**

### Sequential Approach Replication (Phase 0A - Completed)

**Implementation Process:**
1. **Codebase Analysis**: Reverse-engineered MMESGBench's llm.py and colpali.py implementations
2. **Document Processing**: Implemented exact 60-line chunking strategy from their markdown approach
3. **Two-Stage Pipeline**: Replicated basic response → qwen-max extraction methodology
4. **Evaluation Framework**: Integrated their eval_score.py and answer parsing logic

**Key Findings:**
- **Perfect Methodology Replication**: Achieved 20% accuracy matching their sequential baseline
- **Content Accessibility Issue**: Questions requiring evidence from pages 61+, 116+, 25+ answered "Not answerable"
- **Early Chunk Bias**: Sequential processing stops at successful front matter chunks
- **Design Limitation**: Sequential approach inherently cannot access later document evidence

**Technical Achievements:**
- AR6 processing: 186 pages → 7,119 lines → 119 chunks
- PostgreSQL integration: 1024-dim embeddings with pgvector similarity search
- 2.4x retrieval improvement: 0.646 vs 0.270 similarity scores
- Production API setup: Qwen models with rate limiting and error handling

### Retrieval Approach Implementation (Phase 0B - Current)

**Strategic Pivot Decision:**
- **Analysis**: MMESGBench has dual pipelines - primitive sequential (20%/40%) and sophisticated RAG (41.5%/51.8%)
- **Decision**: Ignore primitive approaches, implement their best-performing retrieval methods
- **Target**: ColBERT Text RAG (41.5%) and ColPali Visual RAG (51.8%) accuracy

**Critical Discovery - Paper vs Codebase Gap:**
- **MMESGBench Paper**: Reports ColBERT Text RAG (41.5%) as distinct from sequential LLM approaches
- **MMESGBench Codebase**: Only contains sequential processing (llm.py), no ColBERT text retrieval implementation
- **Our Assumption**: Paper results require proper ColBERT retrieval with top-5 chunks/pages (matching ColPali approach)
- **Implementation Strategy**: Build true ColBERT text RAG using top-5 retrieval to match paper specifications

**Implementation Plan:**
1. **ColBERT Text Pipeline**: Sentence-transformers embedding → similarity search → **top-5 chunks** → Qwen Max
2. **ColPali Visual Pipeline**: PDF→images→visual embeddings → **top-5 pages** → Qwen-VL Max
3. **Evidence Validation**: Verify pages 61, 116, 25 retrieved for failed questions
4. **Performance Comparison**: Document accuracy improvement vs sequential baseline

**Current Results:**
- **Our ColBERT Text RAG**: 40.0% accuracy (very close to 41.5% target)
- **Sequential Baseline**: 20% accuracy (matches MMESGBench codebase)
- **Performance Gap Closed**: Our proper text RAG bridges sequential (20%) and visual (51.8%) approaches

**File Created**: `colbert_text_only_evaluation.py` with working ColBERT text retrieval approach

## 📚 **Key References & Resources**

### Primary Sources
- **MMESGBench Repository**: [Zhanglei1103/MMESGBench](https://github.com/Zhanglei1103/MMESGBench) - Multimodal ESG QA benchmark
- **DSPy Framework**: [stanfordnlp/dspy](https://github.com/stanfordnlp/dspy) - Programming with foundation models
- **GEPA Paper**: Reflective Prompt Evolution approach (literature reference)
- **ColPali**: Visual retrieval model integrated in MMESGBench approach

### Technical Documentation
- **Qwen API**: Dashscope compatible mode for text and vision models
- **PostgreSQL + pgvector**: Production vector database for embeddings
- **MMESGBench Paper**: Detailed methodology and performance baselines

## 🎯 **Next Phase Planning**

### Phase 1: DSPy Integration (Upcoming)
1. **Module Definition**: Wrap ColBERT and ColPali approaches in DSPy signatures
2. **Pipeline Assembly**: Create unified ESG reasoning pipeline with retrieval
3. **GEPA Optimization**: Apply reflective prompt evolution on working baseline
4. **Performance Tracking**: Maintain compatibility with MMESGBench evaluation

### Phase 2: Comparative Analysis (Future)
1. **Fine-tuning Baseline**: Implement LoRA + small-RL approaches
2. **Statistical Validation**: Multi-seed evaluation with significance testing
3. **Efficiency Analysis**: Cost, compute, and label usage comparison
4. **Publication Preparation**: Document findings and methodology

## 📊 **Success Metrics Summary**

### Replication Validation (Phase 0)
- Sequential approach: 20% accuracy ✅ (matches MMESGBench baseline)
- Retrieval approach: Target 41.5% (text) and 51.8% (multimodal)
- Evidence accessibility: Pages 61, 116, 25 retrieved in top-5 results

### Enhancement Validation (Phase 1)
- DSPy optimization: Exceed retrieval baseline with lower compute cost
- GEPA effectiveness: Demonstrate prompt evolution improvements
- Production readiness: Scalable pipeline with cost tracking

### Research Contribution (Phase 2)
- Methodology comparison: DSPy/GEPA vs fine-tuning trade-offs
- Multimodal effectiveness: Visual RAG performance on ESG documents
- Practical deployment: Real-world ESG reasoning system demonstration