# MMESGBench Parameter Analysis - Exact Replication Requirements

## 🎯 **Critical Parameters for Exact Replication**

### **1. Model Parameters (Stage 1: Main Response)**

| Parameter | MMESGBench Value | Our Current | Impact | Replication Status |
|-----------|------------------|-------------|--------|--------------------|
| **temperature** | `0.0` (most models) | `0.1` | High - determinism | ❌ Need to fix |
| **max_tokens** | `1024` | `4096` | Medium - response length | ❌ Need to fix |
| **chunk_size** | `60` lines | `60` lines | High - content scope | ✅ Already correct |
| **do_sample** | `temperature > 0` | Not specified | Medium - sampling | ❌ Need to align |

**Model-Specific Temperature Settings:**
```python
# From llm.py line 104
args.temperature = 0.1 if args.model_name in ['deepseek_llm_chat'] else 0
```

**Critical Finding**: Most MMESGBench models use **temperature=0.0** for deterministic results!

### **2. Answer Extraction Parameters (Stage 2)**

| Parameter | MMESGBench Value | Our Current | Impact | Replication Status |
|-----------|------------------|-------------|--------|--------------------|
| **model** | `"qwen-max"` | Not implemented | Critical - accuracy | ❌ Missing stage |
| **temperature** | `0.0` | N/A | Critical - determinism | ❌ Missing stage |
| **max_tokens** | `256` | N/A | High - extraction length | ❌ Missing stage |
| **top_p** | `1` | N/A | Medium - nucleus sampling | ❌ Missing stage |
| **seed** | `42` | N/A | High - reproducibility | ❌ Missing stage |
| **frequency_penalty** | `0` | N/A | Low - repetition control | ❌ Missing stage |
| **presence_penalty** | `0` | N/A | Low - topic control | ❌ Missing stage |

### **3. Processing Flow Parameters**

| Aspect | MMESGBench Approach | Our Current | Impact | Replication Status |
|--------|---------------------|-------------|--------|--------------------|
| **Chunk Processing** | Sequential until success | Semantic retrieval top-k | Critical - different logic | ❌ Need sequential |
| **Failure Handling** | "Failed" → next chunk | Error handling | High - robustness | ❌ Need exact logic |
| **Context Selection** | First successful chunk | Top-k similarity | Critical - content selection | ❌ Major difference |
| **Response Validation** | Simple != "Failed" | Complex evaluation | Medium - reliability | ❌ Need simple check |

### **4. Exact Prompt Templates**

#### **Stage 1 Prompts (Basic, No ESG Specialization)**

**Mixtral/ChatGLM (Text Models):**
```
You are a helpful assistant. Answer the following question based on the context provided.

Context:
{context}

Question: {question}
Answer:
```

**DeepSeek LLM:**
```
Please answer the question based on the context below.

Context:
{context}

Question: {question}
```

**Vision Models:**
- **MiniCPM**: System: `"Answer in detail."`
- **InternLM/InternVL**: Standard multimodal instructions
- **DeepSeek-VL**: Minimal prompting with image placeholders

#### **Stage 2 Prompt (Answer Extraction)**
```
Given the question and analysis, you are tasked to extract answers with required formats from the free-form analysis.
- Your extracted answers should be one of the following formats: (1) Integer, (2) Float, (3) String and (4) List. If you find the analysis the question can not be answered from the given documents, type "Not answerable". Exception: If the analysis only tells you that it can not read/understand the images or documents, type "Fail to answer".
- Please make your response as concise as possible. Also note that your response should be formatted as below:
```
Extracted answer: [answer]
Answer format: [answer format]
```

[Followed by detailed few-shot examples...]
```

### **5. Critical Implementation Details**

#### **Sequential Chunk Processing (Critical Difference)**
```python
# MMESGBench approach (llm.py lines 58-62)
response = "Failed"
for chunk in chunks:
    response = get_response_concat(model, question, chunk, max_new_tokens, temperature)
    if response != "Failed":
        break  # Stop at first success

# Our current approach (WRONG for replication)
retrieved_chunks = retrieve_top_k_similar(question, chunks, k=5)
context = combine_chunks(retrieved_chunks)
response = generate_response(question, context)
```

#### **Exact Answer Parsing (Critical)**
```python
# MMESGBench exact parsing (llm.py line 69)
try:
    pred_ans = extracted_res.split("Answer format:")[0].split("Extracted answer:")[1].strip()
    score = eval_score(sample["answer"], pred_ans, sample["answer_format"])
except:
    pred_ans = "Failed to extract"
    score = 0.0
```

## 🚨 **Major Replication Issues Identified**

### **1. Processing Logic Completely Different**

**MMESGBench**: Sequential chunk processing until first success
**Our Current**: Semantic similarity-based top-k retrieval

**Impact**: This could completely change which content the model sees!

### **2. Missing Two-Stage Architecture**

**Critical Missing Components**:
- Stage 2 answer extraction with qwen-max
- Structured format validation
- Exact parameter alignment (seed=42, temperature=0.0)

### **3. Parameter Misalignment**

**High-Impact Differences**:
- Temperature: 0.0 vs 0.1 (affects determinism)
- Max tokens: 1024 vs 4096 (affects response length)
- Missing extraction stage entirely

## 🔧 **Exact Replication Implementation**

### **Priority 1: Fix Processing Logic**
```python
def replicate_mmesgbench_processing(question, chunks):
    """Exact replication of their sequential processing"""
    response = "Failed"

    # Sequential processing until success (their exact logic)
    for chunk in chunks:
        response = get_basic_response(question, chunk,
                                    max_tokens=1024,
                                    temperature=0.0)
        if response != "Failed":
            break

    # Two-stage extraction
    if response != "Failed":
        extracted = extract_answer_qwen_max(question, response)
        return parse_extracted_answer(extracted)

    return "Failed to extract", 0.0
```

### **Priority 2: Implement Exact Two-Stage Pipeline**
```python
class MMESGBenchExactReplicator:
    def __init__(self):
        self.stage1_models = {
            "qwen-plus": self.init_qwen_plus(),
            "temperature": 0.0,
            "max_tokens": 1024
        }

        self.stage2_extractor = {
            "model": "qwen-max",
            "temperature": 0.0,
            "max_tokens": 256,
            "seed": 42,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0
        }
```

### **Priority 3: Parameter Alignment**
```python
# Exact MMESGBench parameters
MMESGBENCH_PARAMS = {
    "chunk_size": 60,              # Lines per chunk
    "max_tokens": 1024,            # Stage 1 generation limit
    "temperature": 0.0,            # Deterministic (most models)
    "extraction_max_tokens": 256,  # Stage 2 limit
    "extraction_temperature": 0.0, # Deterministic extraction
    "seed": 42,                    # Reproducibility
    "sequential_processing": True,  # Not similarity-based
    "stop_on_first_success": True  # Key behavioral difference
}
```

## 📊 **Expected Impact of Exact Replication**

### **Accuracy Changes Expected**
1. **Sequential vs Similarity**: May find different content → different accuracy
2. **Temperature 0.0**: More deterministic → potentially more consistent
3. **Two-stage extraction**: Better format compliance → higher evaluation scores
4. **Shorter responses**: 1024 vs 4096 tokens → more focused answers

### **Performance Implications**
1. **Sequential processing**: Potentially slower (but more authentic)
2. **Two API calls**: Double the cost per question
3. **Deterministic results**: Better reproducibility

## 🎯 **Implementation Priority**

1. **✅ High Priority**: Implement two-stage architecture with exact parameters
2. **✅ High Priority**: Fix temperature (0.0) and max_tokens (1024)
3. **✅ Medium Priority**: Implement sequential chunk processing
4. **✅ Medium Priority**: Add exact prompt templates
5. **✅ Low Priority**: Fine-tune other parameters (top_p, penalties)

The most critical issue is the **processing logic difference**: sequential vs similarity-based. This could fundamentally change which content the model analyzes!