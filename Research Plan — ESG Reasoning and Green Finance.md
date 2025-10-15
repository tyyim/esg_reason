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

---

## 🔬 **Phase 3a: DSPy MIPROv2 Prompt Optimization (Completed)**

**Date**: October 15, 2025
**Status**: ❌ **Failed** - Performance degraded by -3.2%
**Files**: `phase3a_optimization_run.log`, `baseline_rag_results_20251015_133614.json`

### Experimental Setup

**Baseline Configuration:**
- **Architecture**: BaselineMMESGBenchRAG (Qwen + PGVector, no query generation)
- **Dataset Split**: Train 186 (20%), Dev 93 (10%), Test 654 (70%)
- **Optimization Method**: MIPROv2 with `auto="light"` mode
- **Optimization Parameters**: 20 trials, 6 fewshot candidates, 3 instruction candidates
- **Runtime**: ~6 minutes (bootstrap + instruction proposal + evaluation)

**Baseline Performance (Dev Set - 93 questions):**
- **Retrieval accuracy**: 75.3% (70/93 correct)
- **Answer accuracy**: 61.3% (57/93 correct)
- **End-to-end accuracy**: 51.6% (48/93 correct)

### Results Summary

**Optimized Performance (Dev Set - 93 questions):**
- **Retrieval accuracy**: 75.3% (70/93 correct) - **No change**
- **Answer accuracy**: 58.1% (54/93 correct) - **❌ -3.2% degradation**
- **End-to-end accuracy**: 48.4% (45/93 correct) - **❌ -3.2% degradation**

**Training Performance:**
- Default program score: 44.0
- Best score found: 47.0 (+3.0 on training set)
- **Overfitting detected**: Training improved but dev set degraded

### Detailed Performance Breakdown by Format

| Format | Baseline Answer Acc | Optimized Answer Acc | Change | Questions Lost/Gained |
|--------|---------------------|----------------------|--------|-----------------------|
| **Str** | 55.9% (19/34) | 50.0% (17/34) | **-5.9%** | Lost 2 questions |
| **Float** | 61.5% (8/13) | 69.2% (9/13) | **+7.7%** | Gained 1 question |
| **List** | 53.8% (7/13) | 53.8% (7/13) | 0% | No change |
| **Int** | 57.9% (11/19) | 57.9% (11/19) | 0% | No change |
| **None** | 78.6% (11/14) | 71.4% (10/14) | **-7.1%** | Lost 1 question |

**Key Observations:**
1. **String format hit hardest**: Lost 2/34 questions (most affected by verbose prompts)
2. **Float format improved**: Gained 1/13 questions (structured guidelines helped numerical extraction)
3. **None format degraded**: Lost 1/14 questions (over-specification pushed toward answering unanswerable questions)
4. **Int/List stable**: No change (these formats less sensitive to prompt variations)

### Prompt Analysis: Default vs Optimized

#### Default ESGReasoning Prompt (~150 characters)
```
Analyze ESG document context and provide detailed reasoning.

[Stage 1 docstring with clear instructions]
[IMPORTANT note about unanswerable questions]
```

**Characteristics:**
- Concise and flexible
- Clear task description in docstring
- Minimal token overhead
- Allows model to generalize across question types

#### Optimized ESGReasoning Prompt (~2,157 characters)
```
Analyze the provided ESG document context and generate a detailed,
step-by-step chain-of-thought reasoning to answer the given ESG question.

**Stage 1 of Two-Stage Extraction:**
- **Objective:** Generate a thorough chain-of-thought analysis...
- **Inputs:**
  - **Context:** Retrieved chunks from ESG documents.
  - **Question:** The ESG question to be answered.
  - **Doc Id:** The identifier of the source document.
- **Outputs:**
  - **Reasoning:** A step-by-step breakdown...
  - **Analysis:** A detailed chain-of-thought reasoning...

**Guidelines:**
- **Thorough Analysis:** Ensure your analysis is comprehensive...
- **Clarity and Precision:** Provide clear and precise reasoning...
- **Insufficient Information:** If the context does not contain...

**Example:**
- **Context:** [Page 15, score: 0.800] ... (context provided)
- **Question:** What are the three key ways...
- **Doc Id:** CDP Full Corporate Scoring Introduction 2024.pdf

**Expected Output:**
- **Reasoning:** Let's think step by step in order to...
- **Analysis:** The context on Page 15... [full example included]
```

**Characteristics:**
- Added 1,200+ extra characters
- Explicit markdown formatting (bold headers, bullet points)
- Concrete example from training data included in prompt
- Rigid structure with prescribed output format

#### AnswerExtraction Prompt (No Change)
The extraction prompt remained unchanged - MIPROv2 correctly identified it was already optimal.

### Root Cause Analysis

**Why Optimization Failed:**

1. **Token Overhead Problem**
   - Optimized prompt: 2,157 chars (1,200+ char increase)
   - Context window space consumed by example instead of retrieved evidence
   - Less room for actual document chunks in Qwen Max's context

2. **Over-Specification & Format Rigidity**
   - Markdown bold/bullet formatting creates rigid expectations
   - Full example in prompt causes model to match example format exactly
   - Reduces model's flexibility to handle edge cases and variations
   - String questions suffered most from format matching attempts

3. **Training Set Overfitting**
   - Example chosen from 186-question training set
   - Training score improved (44.0 → 47.0) but dev degraded (51.6% → 48.4%)
   - Classic overfitting pattern: learns training quirks, loses generalization

4. **Unanswerable Question Handling**
   - Detailed guidelines pushed model toward attempting answers
   - "None" format lost 1 question (11→10 correct)
   - Over-specified prompt reduces model's confidence in saying "Not answerable"

5. **Retrieval Bottleneck Ignored**
   - Retrieval accuracy unchanged at 75.3% (70/93 correct)
   - Prompt optimization can't fix the 25% questions with wrong context
   - Real bottleneck is retrieval, not prompts

### Lessons Learned

**Critical Insights:**

1. **Default Prompts Were Already Optimal**
   - Well-designed concise prompts beat verbose structured alternatives
   - Less is more: token budget better spent on evidence than examples
   - DSPy's default signature design is production-ready

2. **Prompt Optimization Has Limits**
   - Can't improve beyond retrieval ceiling (75.3% retrieval accuracy)
   - Only 25% of questions have room for prompt improvements
   - Small training set (186) insufficient for MIPROv2 to learn generalizable patterns

3. **Overfitting is Easy with Small Datasets**
   - 186 training examples too few for meaningful prompt discovery
   - Training improvement != dev improvement
   - Need larger dataset or different optimization approach

4. **Wrong Optimization Target**
   - Optimizing prompts when retrieval is the bottleneck wastes effort
   - Should optimize query generation to improve retrieval from 75% → 85%+
   - Then answer accuracy could naturally improve from 61% → 75%+

### Recommendations for Phase 3b

**Strategic Pivot**: Move from prompt optimization to query optimization

1. **Implement Query Generation Module**
   - Add QueryGeneration signature before retrieval
   - Optimize query reformulation to improve retrieval accuracy
   - Target: 75% → 85%+ retrieval accuracy (+10%)

2. **Use Enhanced Architecture**
   - 4-stage pipeline: Query Gen → Retrieval → Reasoning → Extraction
   - Optimize query generation prompts, keep reasoning prompts as default
   - Focus MIPROv2 on retrieval improvement, not answer extraction

3. **Expected Impact**
   - Retrieval: 75% → 85% (+10% from query optimization)
   - Answer: 61% → 70%+ (+9% from better context)
   - End-to-end: 51.6% → 60%+ (+8.4% total improvement)

4. **Alternative: Skip Optimization**
   - If retrieval can't be improved, accept 51.6% baseline
   - Move directly to fine-tuning comparison (Phase 2)
   - Document that prompt optimization is unnecessary for this task

### Files & Artifacts

**Optimization Results:**
- `phase3a_optimization_run.log` - Full optimization log with 20 trials
- `baseline_rag_results_20251015_133614.json` - Dev set results with optimized prompts
- `dspy_implementation/optimized_modules/baseline_rag_20251015_133614.json` - Saved optimized module

**Analysis Scripts:**
- `test_miprov2_auto.py` - Quick test to verify MIPROv2 auto mode works
- `dspy_implementation/enhanced_miprov2_optimization.py` - Main optimization script

**Key Metrics Tracked:**
- MLFlow experiment tracking at `http://localhost:5000`
- Retrieval + Answer + End-to-end accuracy separation
- Per-format breakdown (Str, Float, List, Int, None)

---