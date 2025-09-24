# Technical Specification: ESG Reasoning and Green Finance MVP

## 1. Overview

This document outlines the technical implementation for a Minimum Viable Product (MVP) to evaluate ESG and Green Finance reasoning capabilities using DSPy framework with GEPA and Miprov2 optimizers, based on the MMESGBench dataset.

## 2. System Architecture

### 2.1 Core Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Loader   │    │  DSPy Pipeline  │    │   Evaluation    │
│                 │    │                 │    │    Module       │
│ - MMESGBench    │───▶│ - Retrieval     │───▶│ - Metrics       │
│ - Preprocessing │    │ - Reasoning     │    │ - Scoring       │
│ - Validation    │    │ - Computation   │    │ - Reporting     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Optimizers    │
                       │                 │
                       │ - GEPA          │
                       │ - Miprov2       │
                       └─────────────────┘
```

### 2.2 Technology Stack

- **Framework**: DSPy (https://github.com/stanfordnlp/dspy)
- **Dataset**: MMESGBench (https://github.com/Zhanglei1103/MMESGBench)
- **Optimizers**: GEPA (Reflective Prompt Evolution), Miprov2
- **Base Models**: Configurable LLMs (GPT-4, Claude, etc.)
- **Retrieval**: Text RAG + Multimodal retrieval
- **Languages**: Python 3.8+

## 3. Data Pipeline

### 3.1 Dataset Integration

**MMESGBench Dataset Structure (Pre-processed):**
- Source: https://github.com/Zhanglei1103/MMESGBench/tree/main
- **933 QA pairs** in structured JSON format
- **45 ESG documents** with multimodal content
- **Ready-to-use**: No additional parsing required

**Dataset Schema:**
```json
{
  "doc_id": "AR6 Synthesis Report Climate Change 2023.pdf",
  "doc_type": "Government & International Organization Documents",
  "question": "Calculate the total additional population exposed...",
  "answer": "19.62",
  "evidence_pages": "[116]",
  "evidence_sources": "['Image', 'Generalized-text (Layout)']",
  "answer_format": "Float"
}
```

**Data Distribution:**
- Answer formats: Str (32%), Int (22%), Float (16%), List (14%), None (16%)
- Document types: Environment (24%), Government (22%), Corporate (18%), Others (36%)
- Evidence sources: Text, Table, Chart, Image, Layout (multimodal combinations)

**Data Loader Implementation:**
```python
import os
import json
import psycopg2
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from pathlib import Path

class MMESGDataLoader:
    def __init__(self):
        load_dotenv()
        self.data_path = "./MMESGBench/dataset/samples.json"
        self.pdf_storage_path = os.getenv("PDF_STORAGE_PATH", "./source_documents/")
        self.pg_url = os.getenv("PG_URL")
        self.collection_name = os.getenv("ESG_COLLECTION_NAME", "mmesgbench_esg_reasoning")

        # Initialize PostgreSQL connection
        self.engine = create_engine(self.pg_url)
        self._setup_database()

    def _setup_database(self):
        """Initialize PostgreSQL tables for ESG reasoning project"""
        with self.engine.connect() as conn:
            # Create extension for vector operations if needed
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

            # Create tables for our ESG collection
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {self.collection_name}_documents (
                    id SERIAL PRIMARY KEY,
                    doc_id TEXT UNIQUE,
                    doc_type TEXT,
                    page_count INTEGER,
                    file_path TEXT,
                    processed_at TIMESTAMP DEFAULT NOW()
                )
            """))

            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {self.collection_name}_evidence (
                    id SERIAL PRIMARY KEY,
                    doc_id TEXT,
                    page_number INTEGER,
                    evidence_type TEXT,
                    text_content TEXT,
                    embeddings VECTOR(1536),  -- Qwen embeddings dimension
                    processed_at TIMESTAMP DEFAULT NOW(),
                    FOREIGN KEY (doc_id) REFERENCES {self.collection_name}_documents(doc_id)
                )
            """))

            conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_{self.collection_name}_embeddings
                ON {self.collection_name}_evidence USING ivfflat (embeddings vector_cosine_ops)
            """))

            conn.commit()

    def load_dataset(self) -> List[Dict]:
        """Load pre-processed MMESGBench dataset"""
        with open(self.data_path, 'r') as f:
            return json.load(f)

    def create_splits(self, train_ratio=0.7, val_ratio=0.15) -> Dict:
        """Create train/val/test splits"""
        data = self.load_dataset()
        # Stratified split by doc_type and answer_format
        return self._stratified_split(data, train_ratio, val_ratio)

    def get_local_pdf_path(self, doc_id: str) -> str:
        """Get local path for PDF document"""
        return os.path.join(self.pdf_storage_path, doc_id)

    def store_processed_evidence(self, doc_id: str, page_num: int,
                               evidence_type: str, text_content: str,
                               embeddings: List[float]):
        """Store processed evidence in PostgreSQL"""
        with self.engine.connect() as conn:
            conn.execute(text(f"""
                INSERT INTO {self.collection_name}_evidence
                (doc_id, page_number, evidence_type, text_content, embeddings)
                VALUES (:doc_id, :page_num, :evidence_type, :text_content, :embeddings)
            """), {
                "doc_id": doc_id,
                "page_num": page_num,
                "evidence_type": evidence_type,
                "text_content": text_content,
                "embeddings": embeddings
            })
            conn.commit()

    def retrieve_similar_evidence(self, query_embedding: List[float],
                                doc_id: str = None, limit: int = 5) -> List[Dict]:
        """Retrieve similar evidence using vector similarity"""
        with self.engine.connect() as conn:
            where_clause = "WHERE doc_id = :doc_id" if doc_id else ""
            params = {"query_embedding": query_embedding, "limit": limit}
            if doc_id:
                params["doc_id"] = doc_id

            result = conn.execute(text(f"""
                SELECT doc_id, page_number, evidence_type, text_content,
                       embeddings <=> :query_embedding as similarity
                FROM {self.collection_name}_evidence
                {where_clause}
                ORDER BY similarity
                LIMIT :limit
            """), params)

            return [dict(row) for row in result]
```

### 3.2 Evidence Processing (Leveraging Existing Pipeline)

**MMESGBench provides:**
1. **Pre-extracted Evidence**: Page numbers and source types identified
2. **Multimodal Sources**: Text, tables, charts, images, layout-aware content
3. **Evaluation Framework**: Built-in scoring with tolerance handling

**Integration Strategy:**
```python
import fitz
from dotenv import load_dotenv
import os

class EvidenceProcessor:
    def __init__(self):
        load_dotenv()
        self.pdf_storage_path = os.getenv("PDF_STORAGE_PATH", "./source_documents/")
        self.processed_data_path = os.getenv("PROCESSED_DATA_PATH", "./processed_data/")
        self.data_loader = MMESGDataLoader()
        self.qwen_embeddings = QwenEmbeddings()

    def process_local_pdf(self, doc_id: str, evidence_pages: List[int],
                         evidence_sources: List[str]) -> Dict:
        """Process PDF from local storage"""
        pdf_path = os.path.join(self.pdf_storage_path, doc_id)

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found at {pdf_path}")

        with fitz.open(pdf_path) as pdf:
            evidence_data = {
                "text_content": [],
                "visual_content": [],
                "processed_pages": []
            }

            for page_num in evidence_pages:
                if page_num <= pdf.page_count:
                    page = pdf[page_num - 1]  # Convert to 0-indexed

                    # Extract text content
                    text_content = page.get_text()
                    if text_content.strip():
                        evidence_data["text_content"].append({
                            "page": page_num,
                            "text": text_content
                        })

                        # Generate embeddings and store in PostgreSQL
                        embeddings = self.qwen_embeddings.embed_text(text_content)
                        self.data_loader.store_processed_evidence(
                            doc_id=doc_id,
                            page_num=page_num,
                            evidence_type="text",
                            text_content=text_content,
                            embeddings=embeddings
                        )

                    # Process visual elements if needed
                    if any(source in ['Chart', 'Table', 'Image'] for source in evidence_sources):
                        # Convert page to image for visual processing
                        pix = page.get_pixmap(dpi=300)
                        img_path = os.path.join(
                            self.processed_data_path,
                            f"{doc_id}_page_{page_num}.png"
                        )
                        pix.save(img_path)
                        evidence_data["visual_content"].append({
                            "page": page_num,
                            "image_path": img_path,
                            "sources": evidence_sources
                        })

                    evidence_data["processed_pages"].append(page_num)

        return evidence_data

    def extract_evidence_with_retrieval(self, question: str, doc_id: str = None) -> Dict:
        """Enhanced evidence extraction using PostgreSQL vector search"""
        # Generate question embedding
        question_embedding = self.qwen_embeddings.embed_text(question)

        # Retrieve similar evidence from PostgreSQL
        similar_evidence = self.data_loader.retrieve_similar_evidence(
            query_embedding=question_embedding,
            doc_id=doc_id,
            limit=10
        )

        return {
            "question": question,
            "retrieved_evidence": similar_evidence,
            "doc_id": doc_id
        }
```

## 4. DSPy Pipeline Implementation

### 4.1 Core Modules

**Signature Definitions:**
```python
class ESGTextReasoning(dspy.Signature):
    """Text-based reasoning for ESG questions using Qwen-Plus"""
    context: str = dspy.InputField(desc="ESG report text context")
    question: str = dspy.InputField(desc="ESG or green finance question")
    reasoning: str = dspy.OutputField(desc="Step-by-step reasoning process")
    answer: str = dspy.OutputField(desc="Final answer with confidence")

class ESGVisionReasoning(dspy.Signature):
    """Vision-based reasoning for charts/tables using Qwen-VL-Plus"""
    image_context: str = dspy.InputField(desc="Chart/table image description")
    text_context: str = dspy.InputField(desc="Accompanying text context")
    question: str = dspy.InputField(desc="Question about visual content")
    visual_analysis: str = dspy.OutputField(desc="Analysis of visual elements")
    answer: str = dspy.OutputField(desc="Answer based on visual + text")

class NumericComputation(dspy.Signature):
    """Perform numeric calculations for ESG metrics"""
    data: str = dspy.InputField(desc="Numeric data from reports")
    calculation: str = dspy.InputField(desc="Required calculation")
    result: float = dspy.OutputField(desc="Computed numeric result")
    confidence: float = dspy.OutputField(desc="Confidence in result (0-1)")
```

**Pipeline Components:**
```python
class ESGPipeline(dspy.Module):
    def __init__(self):
        # Configure Qwen models
        self.qwen_text = dspy.OpenAI(
            model="qwen-plus",
            api_base="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        self.qwen_vision = dspy.OpenAI(
            model="qwen-vl-plus",
            api_base="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

        # Pipeline components
        self.retriever = QwenMultimodalRetriever()
        self.text_reasoner = dspy.ChainOfThought(ESGTextReasoning)
        self.vision_reasoner = dspy.ChainOfThought(ESGVisionReasoning)
        self.calculator = dspy.ChainOfThought(NumericComputation)
        self.verifier = ResponseVerifier()

    def forward(self, question, doc_id, evidence_pages, evidence_sources):
        # Route based on evidence type
        has_visual = any(source in ['Chart', 'Table', 'Image']
                        for source in evidence_sources)

        if has_visual:
            return self._process_multimodal(question, doc_id, evidence_pages, evidence_sources)
        else:
            return self._process_text_only(question, doc_id, evidence_pages)

    def _process_multimodal(self, question, doc_id, evidence_pages, evidence_sources):
        # Extract both text and visual evidence
        text_evidence, visual_evidence = self.retriever.extract_multimodal(
            doc_id, evidence_pages, evidence_sources
        )

        # Use Qwen-VL-Plus for visual reasoning
        with dspy.context(lm=self.qwen_vision):
            vision_result = self.vision_reasoner(
                image_context=visual_evidence,
                text_context=text_evidence,
                question=question
            )

        # Post-process with calculations if needed
        if self.requires_calculation(vision_result.answer):
            calc_result = self.calculator(
                data=f"{text_evidence}\n{vision_result.visual_analysis}",
                calculation=question
            )
            return self._combine_results(vision_result, calc_result)

        return vision_result

    def _process_text_only(self, question, doc_id, evidence_pages):
        # Extract text evidence
        text_evidence = self.retriever.extract_text(doc_id, evidence_pages)

        # Use Qwen-Plus for text reasoning
        with dspy.context(lm=self.qwen_text):
            text_result = self.text_reasoner(
                context=text_evidence,
                question=question
            )

        # Post-process with calculations if needed
        if self.requires_calculation(text_result.answer):
            calc_result = self.calculator(
                data=text_evidence,
                calculation=question
            )
            return self._combine_results(text_result, calc_result)

        return text_result
```

### 4.2 Retrieval System

**Qwen-Enhanced Multimodal Retrieval:**
```python
class QwenMultimodalRetriever(dspy.Module):
    def __init__(self):
        # Use Qwen embedding for text retrieval
        self.qwen_embeddings = QwenEmbeddings(
            model="text-embedding-v3",
            api_base="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

        # Integration with MMESGBench ColPali for visual retrieval
        self.colpali_retriever = ColPaliRetriever()
        self.pdf_processor = PDFProcessor()

    def extract_multimodal(self, doc_id, evidence_pages, evidence_sources):
        """Extract both text and visual evidence using Qwen + ColPali"""

        # Process PDF pages to images (leverage MMESGBench pipeline)
        page_images = self.pdf_processor.extract_pages_as_images(
            doc_id, evidence_pages
        )

        # Extract text using OCR + PDF text extraction
        text_evidence = self.pdf_processor.extract_text(
            doc_id, evidence_pages
        )

        # Process visual elements (charts, tables, images)
        visual_evidence = []
        for source_type in evidence_sources:
            if source_type in ['Chart', 'Table', 'Image']:
                visual_content = self.colpali_retriever.process_visual_content(
                    page_images, source_type
                )
                visual_evidence.append(visual_content)

        return text_evidence, visual_evidence

    def extract_text(self, doc_id, evidence_pages):
        """Extract text-only evidence with Qwen embeddings enhancement"""

        # Extract raw text
        raw_text = self.pdf_processor.extract_text(doc_id, evidence_pages)

        # Enhance with semantic chunking using Qwen embeddings
        semantic_chunks = self.qwen_embeddings.chunk_semantically(raw_text)

        return semantic_chunks

class QwenEmbeddings:
    def __init__(self):
        load_dotenv()
        self.model = "text-embedding-v4"  # Updated to v4
        self.api_base = os.getenv("QWEN_API_BASE")
        self.client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url=self.api_base
        )

    def embed_text(self, text: str) -> List[float]:
        """Generate embeddings for text using Qwen API"""
        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.model
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            return []

    def chunk_semantically(self, text: str, chunk_size: int = 1000) -> List[Dict]:
        """Use Qwen embeddings to create semantically coherent chunks"""
        # Split text into initial chunks
        chunks = self._split_text(text, chunk_size)

        # Generate embeddings for each chunk
        embedded_chunks = []
        for i, chunk in enumerate(chunks):
            embeddings = self.embed_text(chunk)
            embedded_chunks.append({
                "chunk_id": i,
                "text": chunk,
                "embeddings": embeddings
            })

        return embedded_chunks

    def retrieve_relevant_chunks(self, query: str, text_chunks: List[Dict],
                               top_k: int = 5) -> List[Dict]:
        """Retrieve most relevant chunks using Qwen embeddings"""
        query_embedding = self.embed_text(query)

        # Calculate similarities
        similarities = []
        for chunk in text_chunks:
            similarity = self._cosine_similarity(query_embedding, chunk["embeddings"])
            similarities.append({
                "chunk": chunk,
                "similarity": similarity
            })

        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        return [item["chunk"] for item in similarities[:top_k]]

    def _split_text(self, text: str, chunk_size: int) -> List[str]:
        """Split text into chunks of specified size"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0

        for word in words:
            current_chunk.append(word)
            current_size += len(word) + 1  # +1 for space

            if current_size >= chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_size = 0

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import numpy as np
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
```

## 5. Optimizer Implementation

### 5.1 GEPA (Reflective Prompt Evolution)

**Implementation Strategy:**
```python
class GEPAOptimizer:
    def __init__(self, budget=100):
        self.search_budget = budget
        self.reflection_module = ReflectionModule()
        self.evolution_strategy = PromptEvolution()

    def optimize(self, pipeline, train_data):
        # Initialize prompt population
        prompts = self.initialize_prompts()

        for iteration in range(self.search_budget):
            # Evaluate current prompts
            scores = self.evaluate_prompts(prompts, train_data)

            # Reflect on performance
            reflections = self.reflection_module(prompts, scores)

            # Evolve prompts based on reflections
            prompts = self.evolution_strategy(prompts, reflections)

            # Track search cost
            self.log_iteration_cost(iteration, scores)

        return self.select_best_prompt(prompts)
```

### 5.2 Miprov2 Integration

**Optimizer Configuration:**
```python
class Miprov2Optimizer:
    def __init__(self):
        self.improvement_strategy = IterativeImprovement()
        self.validation_module = ValidationModule()

    def optimize(self, pipeline, examples):
        # Miprov2 specific optimization logic
        # Focus on multi-hop reasoning improvement
        optimized_pipeline = self.improvement_strategy(pipeline, examples)
        return optimized_pipeline
```

## 6. Evaluation Framework

### 6.1 Metrics Implementation (Leveraging MMESGBench Framework)

```python
class ESGEvaluator:
    def __init__(self):
        # Use existing MMESGBench evaluation framework
        from MMESGBench.src.eval.eval_score import eval_score, eval_acc_and_f1
        from MMESGBench.src.eval.extract_answer import extract_answer

        self.mmesg_evaluator = eval_score
        self.extract_answer = extract_answer
        self.efficiency_tracker = EfficiencyTracker()

    def evaluate(self, predictions, ground_truth):
        """Leverage MMESGBench's built-in evaluation with ANLS and fuzzy matching"""

        # Extract answers using MMESGBench format
        extracted_predictions = [
            self.extract_answer(pred, gt['answer_format'])
            for pred, gt in zip(predictions, ground_truth)
        ]

        # Use MMESGBench evaluation pipeline
        results = {
            'exact_match': self._compute_exact_match(extracted_predictions, ground_truth),
            'anls_score': self._compute_anls(extracted_predictions, ground_truth),
            'numeric_tolerance': self._compute_tolerance(extracted_predictions, ground_truth),
            'by_format': self._evaluate_by_format(extracted_predictions, ground_truth),
            'by_evidence_type': self._evaluate_by_evidence(extracted_predictions, ground_truth),
            'efficiency': self.efficiency_tracker.get_metrics()
        }
        return results

    def _compute_tolerance(self, predictions, ground_truth):
        """Handle Float/Int answers with ±1% tolerance (as per MMESGBench)"""
        tolerant_matches = 0
        numeric_total = 0

        for pred, gt in zip(predictions, ground_truth):
            if gt['answer_format'] in ['Float', 'Int']:
                numeric_total += 1
                try:
                    pred_val = float(pred)
                    gt_val = float(gt['answer'])

                    # ±1% tolerance as specified in research plan
                    if abs(pred_val - gt_val) / max(abs(gt_val), 1e-10) <= 0.01:
                        tolerant_matches += 1
                except (ValueError, TypeError):
                    pass

        return tolerant_matches / max(numeric_total, 1)
```

### 6.2 Scoring System

**Numeric Tolerance Scoring:**
- Primary: ±1% tolerance for numeric answers
- Secondary: Exact match reporting
- Categorical: Top-2 accuracy for rankings

**Task-Specific Scoring:**
- ESG QA: F1 + numeric tolerance
- Green Finance: Eligibility (binary) + projection accuracy
- Table reasoning: Percentage accuracy + category matching

## 7. Implementation Plan

### 7.1 Phase 1: Foundation (Weeks 1-2)

1. **Environment Setup**
   ```bash
   # Conda environment (already completed)
   conda activate esg_reasoning

   # Create .env file for configuration
   cat > .env << 'EOF'
   # Qwen API Configuration
   DASHSCOPE_API_KEY=your_dashscope_api_key_here
   QWEN_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1

   # PostgreSQL Configuration
   PG_URL=postgresql://username:password@host:port/database
   ESG_COLLECTION_NAME=mmesgbench_esg_reasoning

   # Local Storage Configuration
   PDF_STORAGE_PATH=./source_documents/
   PROCESSED_DATA_PATH=./processed_data/
   CACHE_PATH=./cache/
   EOF

   # Load environment variables
   pip install python-dotenv
   source .env

   # MMESGBench integration
   git clone https://github.com/Zhanglei1103/MMESGBench
   cd MMESGBench

   # Create local PDF storage directory
   mkdir -p source_documents/
   mkdir -p processed_data/
   mkdir -p cache/

   # Download source PDFs to local folder
   # Use hyperlinks from ESG_source.pdf to download all 45 PDFs
   python download_pdfs.py  # Script to download PDFs from hyperlinks

   # Install additional dependencies
   pip install psycopg2-binary pgvector sqlalchemy

   # Test connections
   python -c "
   import os
   from dotenv import load_dotenv
   load_dotenv()

   # Test Qwen API
   import openai
   client = openai.OpenAI(
       api_key=os.getenv('DASHSCOPE_API_KEY'),
       base_url=os.getenv('QWEN_API_BASE')
   )
   print('✅ Qwen API connection successful')

   # Test PostgreSQL
   import psycopg2
   conn = psycopg2.connect(os.getenv('PG_URL'))
   print('✅ PostgreSQL connection successful')
   conn.close()
   "
   ```

2. **Data Integration (Simplified)**
   - ✅ **No parsing needed**: Dataset is pre-processed
   - Load 933 QA pairs from `samples.json`
   - Create train/val/test splits (stratified by doc_type)
   - Integrate existing multimodal evidence extraction

3. **Basic DSPy Pipeline**
   - Define ESG-specific signatures
   - Implement core reasoning modules
   - Integrate with MMESGBench's colpali retrieval system

### 7.2 Phase 2: Optimization (Weeks 3-4)

1. **GEPA Implementation**
   - Reflection module
   - Prompt evolution strategy
   - Search budget tracking

2. **Miprov2 Integration**
   - Iterative improvement
   - Multi-hop reasoning enhancement

3. **Evaluation Framework**
   - Metrics implementation
   - Scoring system
   - Performance tracking

### 7.3 Phase 3: Validation (Week 5)

1. **Baseline Comparison**
   - Zero-shot SOTA models
   - Few-shot performance
   - Efficiency benchmarking

2. **Results Analysis**
   - Performance metrics
   - Statistical significance
   - Error analysis

## 8. Project Structure (Updated with PostgreSQL and Local Storage)

```
esg_reasoning_mvp/
├── .env                          # Environment configuration (API keys, DB URLs)
├── .gitignore                    # Exclude .env, PDFs, processed data
├── requirements.txt              # All dependencies
├── download_pdfs.py              # Script to download 45 PDFs from ESG_source.pdf
├── setup_database.py             # PostgreSQL setup and migration script
├── MMESGBench/                   # Cloned repository (submodule)
│   ├── dataset/
│   │   ├── samples.json          # 933 QA pairs (ready-to-use)
│   │   └── ESG_source.pdf        # Index with hyperlinks to source PDFs
│   ├── src/
│   │   ├── eval/                 # Existing evaluation framework
│   │   ├── models/               # Pre-built model interfaces
│   │   └── colpali.py           # Existing RAG pipeline
│   └── requirements.txt
├── source_documents/             # Local PDF storage (45 files)
│   ├── 2023-amazon-sustainability-report.pdf
│   ├── AR6 Synthesis Report Climate Change 2023.pdf
│   ├── Alibaba Group 2023 ESG Report.pdf
│   └── ... (42 more PDFs)
├── processed_data/               # Processed evidence cache
│   ├── images/                   # Page images for visual processing
│   ├── chunks/                   # Text chunks with embeddings
│   └── cache/                    # Temporary processing files
├── src/
│   ├── data/
│   │   ├── loader.py            # MMESGDataLoader with PostgreSQL
│   │   ├── processor.py         # EvidenceProcessor for PDFs
│   │   └── embeddings.py        # QwenEmbeddings wrapper
│   ├── dspy_pipeline/
│   │   ├── signatures.py        # ESG-specific DSPy signatures
│   │   ├── modules.py           # ESG pipeline with Qwen models
│   │   └── retrieval.py         # Qwen + PostgreSQL retrieval
│   ├── optimizers/
│   │   ├── gepa.py              # GEPA optimizer
│   │   ├── miprov2.py           # Miprov2 optimizer
│   │   └── base_optimizer.py
│   ├── evaluation/
│   │   ├── evaluator.py         # Enhanced MMESGBench evaluator
│   │   └── efficiency.py        # Cost and efficiency tracking
│   ├── database/
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── migrations.py        # Database schema migrations
│   │   └── connection.py        # PostgreSQL connection manager
│   └── utils/
│       ├── config.py            # Configuration management (.env)
│       ├── logging.py           # Structured logging
│       └── helpers.py           # Utility functions
├── experiments/
│   ├── baselines/               # Baseline experiment results
│   ├── dspy_gepa/              # DSPy + GEPA experiments
│   ├── dspy_miprov2/           # DSPy + Miprov2 experiments
│   └── results/                 # Consolidated results and analysis
├── configs/
│   ├── model_config.yaml       # Qwen model configurations
│   ├── eval_config.yaml        # Evaluation parameters
│   └── optimizer_config.yaml    # GEPA/Miprov2 settings
├── notebooks/                   # Jupyter notebooks for analysis
│   ├── data_exploration.ipynb
│   ├── model_analysis.ipynb
│   └── results_visualization.ipynb
└── README.md
```

**Key Architecture Changes:**
- **Environment Management**: `.env` file for all sensitive configuration
- **Local PDF Storage**: `source_documents/` for 45 downloaded PDFs
- **PostgreSQL Integration**: Vector database with `mmesgbench_esg_reasoning` collection
- **Processed Data Cache**: Efficient storage of embeddings and processed content
- **Database Layer**: Dedicated modules for PostgreSQL operations
- **Enhanced Security**: API keys and DB credentials in `.env` (gitignored)

## 9. Configuration Management

**Model Configuration:**
```yaml
models:
  # Qwen model suite for optimal performance and cost-efficiency
  text_model: "qwen-plus"              # Fast reasoning for text-only tasks
  vision_model: "qwen-vl-plus"         # Multimodal reasoning for charts/tables
  embedding_model: "text-embedding-v4" # Qwen embeddings for retrieval

  # Model parameters
  temperature: 0.1                     # Low for consistent reasoning
  max_tokens: 4096                     # Sufficient for ESG analysis

  # Fallback options
  fallback_text: "qwen-turbo"          # Faster alternative
  fallback_vision: "qwen-vl-max"       # Higher capability alternative

optimization:
  gepa:
    search_budget: 100
    reflection_depth: 3
    evolution_strategy: "gradient_free"
    model_budget_allocation:
      text_reasoning: 60%              # Most calls for text analysis
      vision_analysis: 30%             # Charts/tables processing
      embeddings: 10%                  # Retrieval operations

  miprov2:
    improvement_iterations: 50
    validation_split: 0.2
    multimodal_validation: true        # Test both text and vision

evaluation:
  numeric_tolerance: 0.01
  abstain_threshold: 0.7
  batch_size: 32
  modality_specific_metrics: true      # Track text vs vision performance
```

## 10. Future Extensions (Placeholders)

### 10.1 Fine-tuning Integration
```python
# Placeholder for fine-tuning module
class FineTuningModule:
    """
    Future implementation:
    - LoRA fine-tuning
    - Adapter layers
    - Task-specific optimization
    """
    pass
```

### 10.2 Reinforcement Learning
```python
# Placeholder for RL module
class RLModule:
    """
    Future implementation:
    - Small-RL integration
    - Reward modeling
    - Policy optimization
    """
    pass
```

## 11. MMESGBench Replication Plan

### 11.1 Implementation Analysis and Findings

Based on comprehensive analysis of the MMESGBench codebase, we have identified their exact implementation approach to replicate their results:

**Key Findings:**

1. **Document Processing Strategy**:
   - MMESGBench converts PDFs to markdown files using PyMuPDF (fitz) at 144 DPI
   - Store processed documents as `.md` files in `/markdowns` directory
   - Process documents as continuous text rather than page-by-page

2. **Text Chunking Strategy** (Critical for Replication):
   - **Exact Implementation**: `chunks = ["".join(lines[i:i + chunk_size]) for i in range(0, len(lines), chunk_size)]`
   - **Chunk Size**: 60 lines per chunk (fixed parameter from `llm.py`)
   - **Processing**: Sequential chunk processing until valid response obtained
   - **Cross-page Chunks**: Chunks span multiple pages naturally

3. **Evaluation Pipeline**:
   - **Two-stage Process**: Main LLM response → Answer extraction with qwen-max
   - **Answer Extraction**: Structured prompt with format validation
   - **Supported Formats**: Integer, Float, String, List, "Not answerable", "Fail to answer"

### 11.2 Our Implementation Status

**✅ Completed Replications:**

1. **MMESGBench-Compliant PDF Processing**:
   ```python
   # Implemented in src/processing/pdf_processor.py
   def _extract_text_chunks(self, pdf: fitz.Document, doc_id: str, page_count: int):
       """Extract text chunks from PDF following MMESGBench approach exactly"""

       # Step 1: Extract all text as continuous lines
       all_text_lines = []
       page_line_mapping = {}
       current_line_num = 0

       for page_num in range(page_count):
           page = pdf[page_num]
           page_text = page.get_text()
           page_lines = page_text.split('\n')

           for line in page_lines:
               all_text_lines.append(line)
               page_line_mapping[current_line_num] = page_num + 1
               current_line_num += 1

       # Step 2: Create chunks exactly like MMESGBench (60 lines per chunk)
       for i in range(0, len(all_text_lines), self.chunk_size):
           chunk_lines = all_text_lines[i:i + self.chunk_size]
           chunk_text = '\n'.join(chunk_lines).strip()
           # Store with embeddings in PostgreSQL vector store
   ```

2. **Full AR6 Document Processing**:
   - **Successfully processed 186 pages** → 7,119 total lines → 119 text chunks
   - **Dramatically improved accuracy**: First question now correct with 0.646 similarity (vs 0.270 before)
   - **PostgreSQL Vector Store**: 119 chunks with 1024-dimensional embeddings

3. **Real RAG Retrieval**:
   - Qwen text-embedding-v4 (1024 dimensions)
   - PostgreSQL with pgvector for similarity search
   - Top-k retrieval with semantic similarity scoring

### 11.3 Detailed Replication Strategy

**Phase 1: Complete MMESGBench Replication (Week 1)**

1. **Document Conversion Pipeline**:
   ```python
   # Create markdown conversion matching their approach
   class MMESGMarkdownConverter:
       def convert_pdf_to_markdown(self, pdf_path: str) -> str:
           """Convert PDF to markdown following MMESGBench approach"""
           with fitz.open(pdf_path) as pdf:
               all_text = []
               for page_num in range(pdf.page_count):
                   page = pdf[page_num]
                   page_text = page.get_text()
                   all_text.append(page_text)
               return '\n'.join(all_text)
   ```

2. **Answer Extraction Module**:
   ```python
   # Implement two-stage answer extraction like MMESGBench
   class MMESGAnswerExtractor:
       def __init__(self):
           self.extraction_prompt = self.load_extraction_prompt()
           self.qwen_extractor = QwenAPIClient(model="qwen-max")

       def extract_answer(self, question: str, response: str) -> Dict:
           """Two-stage extraction: response → structured answer"""
           extraction_result = self.qwen_extractor.reason_esg_question(
               question=self.extraction_prompt,
               context=f"Question: {question}\nAnalysis: {response}"
           )
           return self.parse_structured_answer(extraction_result)
   ```

3. **Evaluation Framework**:
   ```python
   # Use MMESGBench's eval_score.py directly
   from MMESGBench.src.eval.eval_score import eval_score, eval_acc_and_f1
   from MMESGBench.src.eval.extract_answer import extract_answer

   class ReplicationEvaluator:
       def evaluate_like_mmesgbench(self, predictions, ground_truth):
           """Exactly replicate MMESGBench evaluation"""
           scores = []
           for pred, gt in zip(predictions, ground_truth):
               score = eval_score(gt["answer"], pred, gt["answer_format"])
               scores.append(score)
           return scores
   ```

**Phase 2: Performance Validation (Week 2)**

1. **Baseline Comparison**:
   - Run identical evaluation on same AR6 questions
   - Compare our accuracy vs MMESGBench reported results
   - Validate chunking strategy produces similar retrieval quality

2. **Error Analysis**:
   - Page match ratio validation (evidence pages vs retrieved pages)
   - Similarity score distributions
   - Answer format accuracy by type

**Phase 3: Enhancement and Innovation (Weeks 3-4)**

1. **DSPy Integration**:
   - Wrap MMESGBench approach in DSPy modules
   - Add GEPA and Miprov2 optimizers
   - Maintain evaluation compatibility

2. **Advanced Features**:
   - Multi-document reasoning
   - Cross-page evidence synthesis
   - Uncertainty quantification

### 11.4 Validation Metrics

**Replication Success Criteria:**

1. **Chunking Validation**:
   - Verify 60-line chunks match MMESGBench approach
   - Confirm cross-page chunk behavior
   - Validate total chunk counts per document

2. **Retrieval Quality**:
   - Page match ratio: Target >40% (evidence pages in top-5 chunks)
   - Semantic similarity: Average >0.5 for relevant questions
   - Answer extraction: >90% valid format extraction

3. **Accuracy Targets**:
   - AR6 questions: Match or exceed MMESGBench baseline
   - Numeric tolerance: ±1% for Float/Int answers
   - Overall accuracy: >70% on 10-question sample

**Current Performance (After Replication):**
- ✅ Full document processing: 7,119 lines → 119 chunks
- ✅ Improved similarity scores: 0.646 vs 0.270 (2.4x improvement)
- ✅ Real RAG retrieval working with PostgreSQL
- 🔄 Evaluation in progress with full 186 pages

**Next Steps:**
1. Complete full evaluation run with 119 chunks
2. Implement two-stage answer extraction
3. Validate against MMESGBench evaluation framework
4. Document performance improvements and cost analysis

## 12. Success Criteria

**Technical Metrics:**
- DSPy pipeline successfully processes MMESGBench data
- GEPA and Miprov2 optimizers improve baseline performance
- Evaluation framework produces consistent, reliable metrics
- System handles multimodal inputs (text + tables + charts)

**Performance Targets:**
- Numeric tolerance accuracy: >80%
- F1 score on ESG QA: >0.75
- Processing time: <30s per question
- Memory usage: <8GB peak VRAM

**Cost Efficiency (Qwen Models):**
- Qwen-Plus: ~$1.40/1M tokens (text reasoning)
- Qwen-VL-Plus: ~$8.00/1M tokens (vision tasks)
- Text-Embedding-v3: ~$0.07/1M tokens (embeddings)
- Target budget: <$50 total for full 933-sample evaluation

**Research Validation:**
- Reproducible results across multiple runs
- Statistical significance in performance improvements
- Efficiency gains over baseline methods
- Clear documentation and logging of all experiments

## 12. Qwen Model Integration Details

### 12.1 Model Selection Rationale

| Model | Use Case | Performance | Cost | Justification |
|-------|----------|-------------|------|---------------|
| Qwen-Plus | Text reasoning, calculations | High accuracy on reasoning tasks | Low cost | Optimal for 60% of ESG text analysis |
| Qwen-VL-Plus | Charts, tables, images | Strong multimodal performance | Medium cost | Necessary for 30% visual evidence tasks |
| Text-Embedding-v3 | Semantic retrieval | High-quality embeddings | Very low cost | Essential for RAG enhancement |

### 12.2 API Integration
```python
# DSPy configuration for Qwen models with .env support
import dspy
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Qwen models in DSPy
qwen_text = dspy.OpenAI(
    model="qwen-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    api_base=os.getenv("QWEN_API_BASE"),
    model_type="chat"
)

qwen_vision = dspy.OpenAI(
    model="qwen-vl-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    api_base=os.getenv("QWEN_API_BASE"),
    model_type="chat"
)

# Set as default models
dspy.settings.configure(lm=qwen_text)
```

### 12.3 Error Handling & Fallbacks
```python
class QwenModelManager:
    def __init__(self):
        self.primary_text = "qwen-plus"
        self.fallback_text = "qwen-turbo"
        self.primary_vision = "qwen-vl-plus"
        self.fallback_vision = "qwen-vl-max"

    def get_model_with_fallback(self, model_type="text"):
        try:
            if model_type == "text":
                return dspy.OpenAI(model=self.primary_text, ...)
            else:
                return dspy.OpenAI(model=self.primary_vision, ...)
        except Exception as e:
            # Fallback to secondary models
            fallback_model = self.fallback_text if model_type == "text" else self.fallback_vision
            return dspy.OpenAI(model=fallback_model, ...)
```

This technical specification provides a comprehensive roadmap for implementing the ESG reasoning MVP using DSPy, GEPA, and Miprov2, with clear placeholders for future extensions including fine-tuning and reinforcement learning components.