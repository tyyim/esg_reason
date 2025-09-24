# Prompt Comparison: Our Implementation vs MMESGBench

## 🔍 **Key Findings: Major Prompt Architecture Differences**

### **MMESGBench Architecture: Two-Stage Process**

**Stage 1: Main Response Generation (Simple Prompts)**
- **Very basic prompts** across all models
- **No ESG specialization** in system prompts
- **Minimal instructions** for reasoning

**Stage 2: Answer Extraction (Structured)**
- **Dedicated extraction prompt** with specific formatting
- **Format validation** and error handling
- **Examples-based learning** with few-shot examples

### **Our Current Architecture: Single-Stage Process**

**Single Stage: Direct Answer Generation**
- **Highly specialized ESG system prompt**
- **Detailed formatting instructions**
- **Direct answer generation** without extraction step

---

## 📊 **Detailed Comparison**

### **Stage 1: Main Response Generation**

#### **MMESGBench Text Models (Basic Approach)**

**Mixtral/ChatGLM:**
```
You are a helpful assistant. Answer the following question based on the context provided.

Context:
{context}

Question: {question}
Answer:
```

**DeepSeek:**
```
Please answer the question based on the context below.

Context:
{context}

Question: {question}
```

**Vision Models:**
- **MiniCPM**: `"Answer in detail."` (minimal system prompt)
- **InternVL/InternLM**: Standard multimodal instructions
- **DeepSeek-VL**: No specific system prompt for ESG

#### **Our Current Implementation (ESG-Specialized)**

**System Prompt:**
```
You are an expert ESG (Environmental, Social, and Governance) analyst with deep knowledge of climate science, sustainability reporting, and green finance.

Your task is to answer questions about ESG documents with accuracy and precision. When answering:

1. For numerical questions, provide exact numbers without additional text
2. For string questions, provide concise, direct answers
3. For list questions, format as a proper JSON list
4. Base your answers strictly on the provided context
5. If you cannot determine the answer from the context, respond with "Cannot determine from provided context"

Answer format guidelines:
- String answers: Direct response (e.g., "North America")
- Integer answers: Just the number (e.g., "2050")
- Float answers: Number with appropriate decimals (e.g., "19.62")
- List answers: JSON format (e.g., ["Africa", "Asia", "Central and South America"])
```

**User Prompt:**
```
Document: {doc_id}
Context: {retrieved_context}
Question: {question}
Please provide a direct, accurate answer:
```

### **Stage 2: Answer Extraction (MMESGBench Only)**

#### **MMESGBench Extraction Prompt (Critical Component)**

```
Given the question and analysis, you are tasked to extract answers with required formats from the free-form analysis.

- Your extracted answers should be one of the following formats: (1) Integer, (2) Float, (3) String and (4) List.
- If you find the analysis the question can not be answered from the given documents, type "Not answerable".
- Exception: If the analysis only tells you that it can not read/understand the images or documents, type "Fail to answer".
- Please make your response as concise as possible. Also note that your response should be formatted as below:

```
Extracted answer: [answer]
Answer format: [answer format]
```

**Few-Shot Examples:**
- **Integer extraction**: "10" from detailed regulation analysis
- **List extraction**: ['Is the service safe?', ...] from bullet points
- **Not answerable**: When insufficient information
- **Fail to answer**: When document/image unreadable

#### **Our Current Implementation**
❌ **Missing**: We don't have this extraction stage

---

## 🎯 **Critical Differences Analysis**

### **1. Prompt Philosophy**
| Aspect | MMESGBench | Our Implementation |
|--------|------------|-------------------|
| **Stage 1 Complexity** | Minimal, generic | Highly specialized ESG |
| **Domain Knowledge** | Generic assistant | ESG expert persona |
| **Format Instructions** | None (delegated to Stage 2) | Detailed in Stage 1 |
| **Error Handling** | Stage 2 extraction | Built into system prompt |

### **2. Answer Processing**
| Aspect | MMESGBench | Our Implementation |
|--------|------------|-------------------|
| **Response Style** | Free-form analysis | Direct formatted answers |
| **Answer Extraction** | Dedicated qwen-max stage | Single-stage generation |
| **Format Validation** | Post-processing with examples | Pre-instructed formatting |
| **Error Cases** | "Not answerable" / "Fail to answer" | "Cannot determine from provided context" |

### **3. Model Usage**
| Aspect | MMESGBench | Our Implementation |
|--------|------------|-------------------|
| **Main Response** | Various models (ChatGLM, Mixtral, DeepSeek, etc.) | qwen-plus |
| **Answer Extraction** | qwen-max | Not implemented |
| **Temperature** | Model-dependent (0.7, 1.0) | 0.1 (consistent) |
| **Specialization** | Generic reasoning | ESG-specialized from start |

---

## 🚨 **Why This Matters for Replication**

### **Performance Impact**

1. **MMESGBench Two-Stage Benefits**:
   - **Separation of Concerns**: Reasoning vs formatting
   - **Format Reliability**: Dedicated extraction ensures consistent output
   - **Error Handling**: Specific handling for document reading failures
   - **Model Optimization**: Use best model for each stage

2. **Our Single-Stage Limitations**:
   - **Format Inconsistency**: Model may not follow format instructions perfectly
   - **Mixed Objectives**: Reasoning and formatting in one step
   - **No Post-Processing**: Errors in generation aren't recoverable

### **Accuracy Implications**

**Potential Issues with Our Approach**:
- **Format Violations**: Model may add extra text, incorrect JSON, etc.
- **Reasoning vs Formatting**: Model splits attention between analysis and format
- **Error Recovery**: No mechanism to handle malformed responses

**MMESGBench Advantages**:
- **Robust Extraction**: Dedicated model ensures format compliance
- **Consistent Evaluation**: Standardized answer formats for scoring
- **Error Classification**: Clear distinction between "not answerable" vs "fail to answer"

---

## 🔧 **Replication Requirements**

### **High Priority: Implement Two-Stage Architecture**

1. **Stage 1: Keep Current ESG-Specialized Approach**
   ```python
   # Generate detailed analysis (keep our current system prompt)
   main_response = qwen_plus.generate(context, question)
   ```

2. **Stage 2: Add MMESGBench Extraction**
   ```python
   # Extract structured answer using their exact prompt
   extraction_prompt = load_mmesgbench_extraction_prompt()
   structured_answer = qwen_max.extract(question, main_response, extraction_prompt)
   ```

### **Implementation Plan**

```python
class MMESGBenchReplicationPipeline:
    def __init__(self):
        self.main_reasoner = QwenAPIClient(model="qwen-plus")  # Our current approach
        self.answer_extractor = QwenAPIClient(model="qwen-max")  # New extraction stage
        self.extraction_prompt = self.load_extraction_prompt()

    def reason_and_extract(self, question, context, doc_id):
        # Stage 1: Generate detailed analysis (our current approach)
        analysis_result = self.main_reasoner.reason_esg_question(
            question=question,
            context=context,
            doc_id=doc_id
        )

        # Stage 2: Extract structured answer (MMESGBench approach)
        extraction_result = self.answer_extractor.extract_answer(
            question=question,
            analysis=analysis_result["answer"],
            prompt=self.extraction_prompt
        )

        return {
            "analysis": analysis_result["answer"],
            "extracted_answer": extraction_result["extracted_answer"],
            "answer_format": extraction_result["answer_format"],
            "confidence": analysis_result.get("confidence", 0.0)
        }
```

---

## 💡 **Recommendations**

### **Immediate Actions for Replication**

1. **✅ Keep Our ESG-Specialized Stage 1**: Our domain expertise is superior
2. **🚀 Add MMESGBench Stage 2**: Implement their extraction methodology
3. **🔄 Compare Both Approaches**: Measure single-stage vs two-stage performance
4. **📊 Validate Format Compliance**: Ensure extraction produces consistent formats

### **Hybrid Approach Benefits**

**Best of Both Worlds**:
- **Stage 1**: Our ESG expertise + detailed reasoning
- **Stage 2**: MMESGBench's robust answer extraction
- **Result**: Superior domain knowledge with consistent formatting

This hybrid approach should give us the accuracy benefits of domain specialization while maintaining the format reliability needed for proper evaluation comparison.