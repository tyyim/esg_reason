# 🔬 Replication Guide - MMESGBench ColBERT Evaluation

## 📋 Quick Start for Collaborators

This guide provides step-by-step instructions to replicate our ColBERT Text RAG evaluation results.

---

## 🎯 Expected Results

### Full Dataset (933 questions)
- **Accuracy**: 39.9% (372/933)
- **F1 Score**: 41.1%
- **Processing Time**: ~2.4s per question

### Corrected Subset (47 questions - Microsoft + Gender)
- **Accuracy**: 46.8% (22/47)
- **F1 Score**: 38.5%

---

## 📁 Golden Source Files

### Core Evaluation Scripts
```bash
# Main production evaluator
optimized_colbert_evaluator_mmesgbench.py

# Document retriever with substitution mappings
colbert_full_dataset_evaluation.py

# Exact MMESGBench evaluation logic
mmesgbench_exact_evaluation.py

# Corrected documents evaluator
colbert_corrected_evaluation.py

# Quick test/display scripts
run_colbert_evaluation.py
```

### Data Files
```bash
# Original benchmark dataset
MMESGBench/dataset/samples.json          # 933 questions across 45 documents

# Corrected ground truth
corrected_ground_truth_answers.json      # 31 Microsoft questions (relabeled)

# Source documents
source_documents/
├── AR6 Synthesis Report Climate Change 2023.pdf
├── Gender 2024.pdf                      # ✅ CORRECTED
├── Microsoft-CDP-2024-Response.pdf      # ✅ CORRECTED (mapped from 2024)
├── ISO-14001-2015.pdf                   # ⚠️ WRONG FILE (pending correction)
└── [42 other documents]
```

### Results Files
```bash
# Full dataset evaluation results
optimized_full_dataset_mmesgbench_with_f1.json

# Corrected subset results
corrected_evaluation_results/colbert_corrected_evaluation.json

# Analysis reports
evaluation_analysis_report.md
corrected_documents_impact_analysis.md
```

---

## 🔧 Environment Setup

### 1. Install Dependencies

```bash
# Activate conda environment
conda activate esg_reasoning

# Verify critical packages
pip list | grep -E "sentence-transformers|openai|PyMuPDF"
```

**Required packages:**
- `sentence-transformers` (for ColBERT embeddings)
- `openai` (for Qwen API client)
- `PyMuPDF` (fitz - for PDF processing)
- `numpy`, `torch`

### 2. API Configuration

Create `.env` file with:
```bash
DASHSCOPE_API_KEY="your_qwen_api_key_here"
QWEN_API_BASE="https://dashscope.aliyuncs.com/compatible-mode/v1"

# Optional: Reduce tokenizer warnings
TOKENIZERS_PARALLELISM=false
```

**Get API Key**: https://dashscope.console.aliyun.com/

### 3. Verify Setup

```bash
# Test API connection
python -c "from src.models.qwen_api import QwenAPIClient; QwenAPIClient().test_connection()"

# Expected output: ✅ API connection successful
```

---

## 🚀 Running Evaluations

### Option 1: Quick Test (View Results)

```bash
# Display existing full dataset results
python run_colbert_evaluation.py
```

**Output:**
```
📊 ColBERT Text RAG Results:
Accuracy: 39.9% (372/933)
F1 Score: 41.1%
```

### Option 2: Full Dataset Evaluation (~60 minutes)

```bash
# Set API key and run full evaluation
export DASHSCOPE_API_KEY="your_key"
export TOKENIZERS_PARALLELISM=false

# Run evaluation with progress tracking
python optimized_colbert_evaluator_mmesgbench.py
```

**Expected Progress:**
```
🔍 Pre-computing retrievals for 933 questions...
   Progress: 50/933 (5.4%) | ETA: 120s
   Progress: 100/933 (10.7%) | ETA: 100s
   ...
📦 Processing batch 1/94 (10 questions)
⏱️  Batch 1 completed in 25.3s
...
```

### Option 3: Corrected Subset Only (~3 minutes)

```bash
# Evaluate only Microsoft + Gender 2024 (47 questions)
export DASHSCOPE_API_KEY="your_key"

python colbert_corrected_evaluation.py
```

**Expected Output:**
```
📋 Prepared evaluation questions:
   Microsoft CDP: 31
   Gender 2024: 16
   Total: 47

📊 COLBERT EVALUATION RESULTS
Overall Performance:
  Accuracy: 46.8% (22/47)
  F1 Score: 38.5%
```

---

## 📊 Understanding the Results

### Result File Structure

```json
{
  "accuracy": 0.399,
  "mmesgbench_accuracy": 0.399,
  "mmesgbench_f1_score": 0.411,
  "total_questions": 933,
  "total_score": 372.0,

  "format_breakdown": {
    "Int": {"total": 207, "correct": 88, "accuracy": 0.425},
    "Str": {"total": 299, "correct": 115, "accuracy": 0.385},
    "Float": {"total": 148, "correct": 50, "accuracy": 0.338},
    ...
  },

  "document_breakdown": {
    "AR6 Synthesis Report Climate Change 2023.pdf": {
      "total": 68,
      "correct": 27,
      "accuracy": 0.397
    },
    ...
  },

  "detailed_results": [
    {
      "question": "...",
      "predicted_answer": "...",
      "ground_truth": "...",
      "score": 1.0,
      "exact_match": true,
      "f1_score": 1.0
    },
    ...
  ]
}
```

### Key Metrics Explained

- **accuracy**: Simple correct/total ratio
- **mmesgbench_accuracy**: Same as accuracy (for compatibility)
- **mmesgbench_f1_score**: Precision-recall harmonic mean
- **exact_match**: Boolean - exact string match
- **f1_score**: Token-level F1 for this question

---

## 🔍 Document Substitution Mappings

The evaluation automatically handles document substitutions:

```python
substitutions = {
    # Original samples.json → Actual file
    "Microsoft CDP Climate Change Response 2023.pdf": "Microsoft-CDP-2024-Response.pdf",
    "Microsoft CDP Climate Change Response 2024.pdf": "Microsoft-CDP-2024-Response.pdf",
    "ISO 14001.pdf": "ISO-14001-2015.pdf",  # ⚠️ Wrong file
    "Gender 2024.pdf": "Gender 2024.pdf"     # ✅ Correct
}
```

**Location**: `colbert_full_dataset_evaluation.py:130-135`

---

## 🐛 Troubleshooting

### Issue: API Key Not Found
```
ValueError: DASHSCOPE_API_KEY not found in environment variables
```

**Solution:**
```bash
export DASHSCOPE_API_KEY="your_key_here"
# Or source the .env file
source .env
```

### Issue: Document Not Found
```
Document not found: Microsoft CDP Climate Change Response 2024.pdf
```

**Solution:**
Verify file exists:
```bash
ls source_documents/ | grep -i microsoft
# Should show: Microsoft-CDP-2024-Response.pdf
```

### Issue: Low Performance on Specific Documents
```
Gender 2024.pdf: 25.0% (4/16)  # Wrong document
```

**Check if using correct file:**
```bash
# Verify Gender 2024.pdf exists (not UNESCO-GEM)
ls -lh source_documents/Gender\ 2024.pdf

# Re-run with corrected evaluator
python colbert_corrected_evaluation.py
```

---

## 📈 Performance Benchmarks

### By Document Type
- **Government/International Org**: 38-42% accuracy
- **Corporate ESG Reports**: 35-40% accuracy
- **Standards Documents**: 28-38% accuracy
- **Simple PDFs**: 50-65% accuracy

### By Answer Format
- **Integer**: 42.5% (best)
- **String**: 38.5% (good)
- **Float**: 33.8% (challenging)
- **List**: 36.6% (needs improvement)
- **None/Not answerable**: 48.0% (strong)

### Processing Speed
- **Document Indexing**: 2-5s per document
- **Retrieval**: 0.1-0.3s per question
- **Generation**: 2-3s per question
- **Total**: ~2.4s per question average

---

## 🔬 Verification Checklist

Before reporting results, verify:

- [ ] API key is set and valid
- [ ] Environment activated: `conda activate esg_reasoning`
- [ ] All source documents present (45 PDFs)
- [ ] MMESGBench dataset cloned: `MMESGBench/dataset/samples.json`
- [ ] Corrected ground truth available: `corrected_ground_truth_answers.json`
- [ ] Results match expected: ~39.9% accuracy on full dataset

---

## 📞 Support

### Common Questions

**Q: Why is my accuracy different from 39.9%?**
A: Check if you're using:
1. Exact MMESGBench evaluation logic (`mmesgbench_exact_evaluation.py`)
2. All 933 questions from `samples.json`
3. Correct document substitutions

**Q: How to run only a subset of documents?**
A: Use `colbert_corrected_evaluation.py` and modify the document list.

**Q: Where are intermediate results saved?**
A: Checkpoints in `colbert_checkpoint.json` (if implemented for that script).

### Reference Papers

- **MMESGBench**: "Evaluating Multimodal Models on ESG Understanding" (2024)
- **ColBERT**: "ColBERT: Efficient and Effective Passage Search via Contextualized Late Interaction over BERT"
- **Qwen Models**: Alibaba Cloud DashScope Documentation

---

## 📝 Citation

If using this evaluation pipeline, please cite:

```bibtex
@article{mmesgbench2024,
  title={MMESGBench: Evaluating Multimodal Models on ESG Understanding},
  author={...},
  year={2024}
}

@software{esg_reasoning_pipeline,
  title={ESG Reasoning and Green Finance Research Pipeline},
  author={Your Team},
  year={2025},
  note={ColBERT Text RAG implementation for MMESGBench}
}
```

---

## 🔄 Version History

- **v1.0 (Sept 2025)**: Initial full dataset evaluation (39.9%)
- **v1.1 (Oct 2025)**: Corrected document evaluation (Microsoft + Gender)
- **v1.2 (Pending)**: ISO 14001 correction + full re-evaluation

---

**Last Updated**: October 1, 2025
**Contact**: victoryim@example.com (update with actual contact)
