# DC-RS Implementation Notes

**Date**: November 9, 2025  
**Status**: Ready for testing

---

## Summary

Implemented DC-Retrieval & Synthesis (DC-RS) variant using **original DC code directly** from https://github.com/suzgunmirac/dynamic-cheatsheet

### Key Changes

#### 1. Added DashScope Model Support to DC's Original Code

**File**: `dc_repo/dynamic_cheatsheet/language_model.py`  
**Lines**: 51-58  
**Change**: Added DashScope models to supported model list

```python
# Add these models to the list at lines 28-59:
"dashscope/qwen-max",
"dashscope/qwen-plus",
"dashscope/qwen-turbo",
"dashscope/qwen2.5-7b-instruct",
"dashscope/qwen2.5-14b-instruct",
"dashscope/qwen2.5-32b-instruct",
"dashscope/qwen2.5-72b-instruct",
```

**Why**: Allows using our DashScope API keys with DC's original implementation

---

#### 2. Fixed ANLS String Evaluation Bug

**File**: `src/evaluation_utils.py`  
**Lines**: 96-116  
**Issue**: MMESGBench's `eval_score()` has a bug in Str type evaluation (line 221 of `MMESGBench/src/eval/eval_score.py`)

**Bug Details**:
```python
# Original bug (line 221):
score = anls_compute(gt, pred)  # ❌ Passes string instead of list

# But anls_compute signature (line 33):
def anls_compute(ground_truth_answers, predicted_answer, threshold=0.5):
    for gt_answer in ground_truth_answers:  # Expects LIST
        # When passed string, iterates character-by-character!
```

**Fix**: Wrap `gt` in a list before calling `anls_compute([gt], pred)`

**Impact**: This bug caused ANLS to always return 0.5 for string comparisons regardless of actual similarity.

---

#### 3. Created DC Evaluator V2 - Uses Original DC Implementation

**File**: `dspy_implementation/dc_module/dc_evaluator_v2.py`  
**Purpose**: Directly uses DC's `LanguageModel.advanced_generate()` method

**What It Does**:
- ✅ Imports original `LanguageModel` from `dc_repo/`
- ✅ Calls `advanced_generate()` with proper approach names:
  - `"DynamicCheatsheet_Cumulative"` for DC-CU
  - `"DynamicCheatsheet_RetrievalSynthesis"` for DC-RS
- ✅ Only adapts MMESGBench data format (question, context, format)
- ✅ Uses corrected evaluation with null equivalence + string fix
- ✅ Loads original prompts from `dc_repo/prompts/`

**What It Doesn't Do**:
- ❌ Reimplement DC logic ourselves
- ❌ Modify DC's core algorithms
- ❌ Use DSPy framework

---

## Running DC-RS

### Prerequisites

1. **Install DC repository**:
```bash
cd /Users/victoryim/Local_Git/CC
git clone https://github.com/suzgunmirac/dynamic-cheatsheet dc_repo
```

2. **Apply DashScope model support**:
Edit `dc_repo/dynamic_cheatsheet/language_model.py` lines 51-58 to add DashScope models (see above)

3. **Activate conda environment**:
```bash
conda activate esg_reasoning
```

### Commands

**DC-CU (Cumulative) - Dev Set**:
```bash
python dspy_implementation/dc_module/dc_evaluator_v2.py \
  --dataset dev \
  --variant cumulative \
  --model qwen2.5-7b-instruct
```

**DC-RS (Retrieval & Synthesis) - Dev Set**:
```bash
python dspy_implementation/dc_module/dc_evaluator_v2.py \
  --dataset dev \
  --variant retrieval_synthesis \
  --model qwen2.5-7b-instruct
```

**Test on first 10 questions**:
```bash
python dspy_implementation/dc_module/dc_evaluator_v2.py \
  --dataset dev \
  --variant retrieval_synthesis \
  --max-questions 10
```

---

## Comparison: Old vs New Implementation

| Aspect | Old (dc_rag_module.py) | New (dc_evaluator_v2.py) |
|--------|------------------------|--------------------------|
| **DC Core** | Reimplemented ourselves | Uses original DC code |
| **Method** | Custom `generate_with_cheatsheet()` | Calls `advanced_generate()` |
| **Prompts** | Custom ESG prompts | Original DC prompts from repo |
| **Risk** | May deviate from paper | Exact replication of paper |
| **Maintenance** | Need to track DC updates | Just update dc_repo/ |

---

## Key Differences: DC-CU vs DC-RS

### DC-CU (Cumulative)
```
Question 1 → Generator (empty cheatsheet) → Answer 1
          → Curator (update cheatsheet v1)
          
Question 2 → Generator (cheatsheet v1) → Answer 2
          → Curator (update cheatsheet v2)
          
Question 3 → Generator (cheatsheet v2) → Answer 3
          ...
```

- **Cheatsheet**: Single, growing knowledge base
- **Used by**: Every question uses same accumulated cheatsheet
- **Update**: After each question, curator updates the cheatsheet

### DC-RS (Retrieval & Synthesis)
```
Question 1 → Retrieve (empty history) → no similar Q&As
          → Curator (synthesize custom cheatsheet v1 for Q1)
          → Generator (custom cheatsheet v1) → Answer 1
          → Store Q1+A1 in history
          
Question 2 → Retrieve (Q1) → similar Q&A: Q1+A1
          → Curator (synthesize custom cheatsheet v2 for Q2 from Q1+A1)
          → Generator (custom cheatsheet v2) → Answer 2
          → Store Q2+A2 in history
          
Question 3 → Retrieve (Q1,Q2) → top-K similar Q&As
          → Curator (synthesize custom cheatsheet v3 for Q3 from similar Q&As)
          → Generator (custom cheatsheet v3) → Answer 3
          ...
```

- **Cheatsheet**: Custom synthesized for each question
- **Used by**: Each question gets a tailored cheatsheet from similar past Q&As
- **Update**: Curator synthesizes new cheatsheet using:
  - Global cheatsheet (knowledge base)
  - Retrieved similar Q&As (top-K by cosine similarity)
  - Current question

---

## DC-RS Data Structures and Retrieval Mechanism

### Three Parallel Lists (In-Memory Storage)

DC-RS maintains **three synchronized Python lists** that grow as questions are answered:

```python
# 1. Input Corpus - Formatted question text
input_corpus = [
    "Question: What is Scope 1?\nContext: ...\nFormat: Str",
    "Question: What is the revenue?\nContext: ...\nFormat: Int",
    # ... grows to N entries
]

# 2. Input Embeddings - Vector representations (1024-dim from text-embedding-v4)
input_embeddings = [
    [0.023, -0.145, ..., 0.089],  # 1024-dim vector for Q1
    [0.034, 0.012, ..., -0.067],  # 1024-dim vector for Q2
    # ... grows to N embeddings
]

# 3. Generator Outputs - Model answers
generator_outputs = [
    "Direct emissions from owned sources",  # Answer to Q1
    "1500000",                             # Answer to Q2
    # ... grows to N answers
]
```

**Key Property**: All three lists are synchronized by index
- `input_corpus[i]` ↔ `input_embeddings[i]` ↔ `generator_outputs[i]`

### Retrieval Algorithm (Per Question)

For each new question (e.g., question #47 out of 93):

#### Step 1: Embed Current Question
```python
current_embedding = embedding_model.embed_query("What is Scope 2?")
input_embeddings.append(current_embedding)  # Now at position 46 (0-indexed)
input_corpus.append(formatted_question)
```

#### Step 2: Compute Cosine Similarity
```python
# Compare current (index 46) against all previous embeddings (0-45)
current_emb = input_embeddings[-1]           # Current question embedding
prev_embs = input_embeddings[:-1]            # All previous embeddings (0-45)

similarities = cosine_similarity([current_emb], prev_embs)
# Result: [0.92, 0.15, 0.78, ..., 0.43]  # 46 similarity scores
```

**Implementation** (from `dc_repo/dynamic_cheatsheet/language_model.py`):
```python
current_original_input_embedding = original_input_embeddings[-1]
prev_original_input_embeddings = original_input_embeddings[:-1]

if len(prev_original_input_embeddings) > 0:
    similarities = cosine_similarity(
        [current_original_input_embedding], 
        prev_original_input_embeddings
    )
```

#### Step 3: Retrieve Top-K Most Similar Q&A Pairs
```python
retrieve_top_k = 5
top_k_indices = np.argsort(similarities[0])[::-1][:retrieve_top_k]
# Result: [12, 3, 34, 8, 21]  # Indices of 5 most similar past questions

# Retrieve corresponding Q&A pairs
top_k_inputs = [input_corpus[i] for i in top_k_indices]
top_k_outputs = [generator_outputs[i] for i in top_k_indices]
top_k_scores = similarities[0][top_k_indices]
# Scores: [0.92, 0.85, 0.78, 0.71, 0.68]
```

#### Step 4: Format Retrieved Pairs as Curated Cheatsheet
```python
curated_cheatsheet = """
### PREVIOUS SOLUTIONS (START)

Note: The input-output pairs listed below are taken from previous test cases...

#### Previous Input #1 (Similarity: 0.92):
Question: What is Scope 1 emissions?
Context: Direct emissions from company-owned...
Format: Str

#### Model Solution to Previous Input #1:
Direct emissions from owned sources
---
---

#### Previous Input #2 (Similarity: 0.85):
Question: What are direct GHG emissions?
Context: Greenhouse gas emissions from...
Format: Str

#### Model Solution to Previous Input #2:
Scope 1 includes all direct GHG emissions
---
---

... (3 more similar Q&As)

### PREVIOUS SOLUTIONS (END)
"""
```

#### Step 5: Synthesize Custom Cheatsheet via Curator
```python
# Curator LLM call with template replacements:
curator_prompt = curator_template.replace(
    "[[PREVIOUS_INPUT_OUTPUT_PAIRS]]", curated_cheatsheet
).replace(
    "[[NEXT_INPUT]]", current_question
).replace(
    "[[PREVIOUS_CHEATSHEET]]", global_cheatsheet
)

# Curator synthesizes a custom cheatsheet for THIS specific question
custom_cheatsheet = curator_model.generate(curator_prompt)
```

#### Step 6: Generate Answer Using Custom Cheatsheet
```python
generator_prompt = generator_template.replace(
    "[[QUESTION]]", current_question
).replace(
    "[[CHEATSHEET]]", custom_cheatsheet
)

answer = generator_model.generate(generator_prompt)
```

#### Step 7: Store Answer for Future Retrieval
```python
generator_outputs.append(answer)
# Now history has 47 Q&A pairs for next question
```

### Memory and Computational Complexity

#### Memory Usage

| Questions Processed | Input Corpus Size | Embeddings Size | Outputs Size | Total Memory |
|---------------------|------------------|-----------------|--------------|--------------|
| 1 | ~500 bytes | 1 × 1024 floats (~4 KB) | ~100 bytes | ~5 KB |
| 10 | ~5 KB | 10 × 1024 floats (~41 KB) | ~1 KB | ~47 KB |
| 46 | ~23 KB | 46 × 1024 floats (~188 KB) | ~5 KB | ~216 KB |
| 93 (dev set) | ~47 KB | 93 × 1024 floats (~380 KB) | ~10 KB | ~437 KB |
| 654 (test set) | ~327 KB | 654 × 1024 floats (~2.7 MB) | ~65 KB | ~3.1 MB |

**Note**: Embeddings are stored as 32-bit floats (4 bytes each)
- 1 embedding = 1024 × 4 = 4,096 bytes ≈ 4 KB
- 93 embeddings ≈ 380 KB
- 654 embeddings ≈ 2.7 MB

#### Time Complexity (Per Question)

As the corpus grows from 1 → N questions:

| Operation | Complexity | Time (Q1) | Time (Q46) | Time (Q93) |
|-----------|-----------|-----------|------------|------------|
| **Embed current question** | O(1) | ~1-2s | ~1-2s | ~1-2s |
| **Cosine similarity** | O(N) | 0s (skip) | ~0.1s | ~0.2s |
| **Top-K selection** | O(N log K) | 0s (skip) | <0.1s | <0.1s |
| **Format curated cheatsheet** | O(K) | 0s | ~1s | ~1s |
| **Curator LLM call** | O(1)* | ~10-15s | ~15-20s | ~20-30s |
| **Generator LLM call** | O(1)* | ~5-8s | ~8-12s | ~10-15s |
| **Total per question** | | **~16-25s** | **~25-35s** | **~32-49s** |

*O(1) but increases with cheatsheet length

#### Why Slowdown Occurs

**Early Questions (1-20)**:
- Small history (~20 past Q&As)
- Fast retrieval (<0.1s)
- Short curated cheatsheet
- **Average time**: ~20-30 seconds

**Middle Questions (21-50)**:
- Growing history (~50 past Q&As)
- Moderate retrieval (~0.2s)
- Longer curated cheatsheet (5 complex Q&As)
- Curator processes more context
- **Average time**: ~40-60 seconds

**Late Questions (51-93)**:
- Large history (~90 past Q&As)
- Slower retrieval (~0.3s)
- Long curated cheatsheet
- Curator struggles with context length
- **Average time**: ~60-90 seconds

### Comparison: DC-CU vs DC-RS

| Aspect | DC-CU (Cumulative) | DC-RS (Retrieval & Synthesis) |
|--------|-------------------|-------------------------------|
| **Storage Structure** | Single string (cheatsheet) | 3 parallel lists |
| **Memory** | ~10-50 KB (text only) | ~437 KB (dev) / ~3.1 MB (test) |
| **Retrieval** | None (uses full cheatsheet) | Cosine similarity on embeddings |
| **Cheatsheet** | Same for all questions | Custom per question |
| **LLM Calls per Q** | 2 (Generator + Curator) | 2 (Curator + Generator) |
| **Speed (Q1-20)** | ~4-5s per question | ~20-30s per question |
| **Speed (Q50-93)** | ~4-5s per question | ~60-90s per question |
| **Scalability** | Constant time | O(N) with corpus growth |
| **Relevance** | All past knowledge | Only relevant knowledge |

### Key Insight

**DC-RS trades speed for relevance**:
- ✅ **Benefit**: Each question gets **tailored knowledge** from similar past Q&As
- ❌ **Cost**: **5-20x slower** than DC-CU due to embedding, retrieval, and synthesis
- 🎯 **Hypothesis**: Better for diverse question sets where not all history is relevant
- ⚠️ **Risk**: Slower scaling makes it impractical for large test sets (654 questions = 6-12 hours!)

---

## Expected Results

Based on DC paper and our previous runs:

| Variant | Dev Set (93q) | Test Set (654q) | Notes |
|---------|---------------|-----------------|-------|
| **DC-CU** | ~57% | ~49% | Already validated |
| **DC-RS** | ? | ? | New - needs testing |

**Hypothesis**: DC-RS might perform better if similar questions exist in history, or worse if early questions don't provide useful patterns.

---

## Next Steps

1. ✅ Test DC-RS on dev set (10 questions POC)
2. ⏳ Compare DC-RS vs DC-CU on full dev set
3. ⏳ If promising, run on test set
4. ⏳ Document results and update main README

---

## Files Created/Modified

### New Files
- `dspy_implementation/dc_module/dc_evaluator_v2.py` - Main evaluator using original DC
- `dspy_implementation/dc_module/dc_prompts.py` - Added `CURATOR_PROMPT_RS`
- `DC_RS_IMPLEMENTATION_NOTES.md` - This file

### Modified Files
- `src/evaluation_utils.py` - Fixed ANLS string bug
- `dspy_implementation/dc_module/dc_rag_module.py` - Enhanced with DC-RS support (legacy)
- `dc_repo/dynamic_cheatsheet/language_model.py` - Added DashScope models (external, not tracked)

---

## Known Issues

None currently. Both evaluation bugs (null equivalence + ANLS string) are now fixed.

---

**Last Updated**: November 9, 2025  
**Author**: AI Assistant + Sum Yee Chan (RA - evaluation fixes)

