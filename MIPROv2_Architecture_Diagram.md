# MIPROv2 Optimization Architecture for MMESGBench

## 🎯 Overview

**Goal**: Optimize from 55.8% baseline (wrong 80% split) → Establish NEW baseline on 20% split → Optimize with MIPROv2

**Key Insight**: Qwen Max serves dual roles:
1. **Meta-optimizer** (MIPROv2): Proposes better prompts/instructions
2. **Student model** (RAG Pipeline): Executes reasoning with optimized prompts

---

## 📊 Phase 1: Baseline Architecture (CURRENT)

```
┌─────────────────────────────────────────────────────────────────┐
│                    MMESGBench Baseline RAG                       │
│                  (PostgreSQL + Qwen Embeddings)                  │
└─────────────────────────────────────────────────────────────────┘

INPUT: Question + Doc ID + Answer Format
  │
  ├─────────────────────────────────────────────────────────────┐
  │                                                              │
  ▼                                                              │
┌──────────────────────────────┐                                │
│  RETRIEVAL STAGE             │                                │
│  PostgreSQL + pgvector       │                                │
├──────────────────────────────┤                                │
│ • Query: Question            │                                │
│ • Embeddings: Qwen v4 (1024) │                                │
│ • Filter: doc_id             │                                │
│ • Top-K: 5 chunks            │                                │
└──────────────────────────────┘                                │
  │                                                              │
  │ Retrieved Context (5 chunks with similarity scores)         │
  │                                                              │
  ▼                                                              │
┌──────────────────────────────────────────────────────────────┐│
│  STAGE 1: REASONING (ChainOfThought)                         ││
│  Model: Qwen Max                                             ││
│  Temperature: 0.0                                            ││
├──────────────────────────────────────────────────────────────┤│
│  Signature: ESGReasoning                                     ││
│  ┌────────────────────────────────────────────────────────┐ ││
│  │ Inputs:                                                 │ ││
│  │ • context: Retrieved chunks                            │ ││
│  │ • question: User question                              │ ││
│  │ • doc_id: Source document                              │ ││
│  │                                                         │ ││
│  │ Instruction (DEFAULT - to be optimized):               │ ││
│  │ "Analyze the context and provide detailed reasoning    │ ││
│  │  to answer the question based on ESG documents."       │ ││
│  │                                                         │ ││
│  │ Output:                                                 │ ││
│  │ • analysis: Detailed chain-of-thought reasoning        │ ││
│  └────────────────────────────────────────────────────────┘ ││
└──────────────────────────────────────────────────────────────┘│
  │                                                              │
  │ Analysis with reasoning                                     │
  │                                                              │
  ▼                                                              │
┌──────────────────────────────────────────────────────────────┐│
│  STAGE 2: EXTRACTION (Predict)                               ││
│  Model: Qwen Max                                             ││
│  Temperature: 0.0                                            ││
├──────────────────────────────────────────────────────────────┤│
│  Signature: AnswerExtraction                                 ││
│  ┌────────────────────────────────────────────────────────┐ ││
│  │ Inputs:                                                 │ ││
│  │ • analysis: Chain-of-thought from Stage 1              │ ││
│  │ • answer_format: Expected format (Str/Int/Float/List)  │ ││
│  │                                                         │ ││
│  │ Instruction (DEFAULT - to be optimized):               │ ││
│  │ "Extract the final answer from the analysis in the     │ ││
│  │  specified format. Return ONLY the answer value."      │ ││
│  │                                                         │ ││
│  │ Output:                                                 │ ││
│  │ • answer: Extracted answer in specified format         │ ││
│  └────────────────────────────────────────────────────────┘ ││
└──────────────────────────────────────────────────────────────┘│
  │                                                              │
  │ Final Answer                                                │
  │                                                              │
  ▼                                                              │
OUTPUT: answer (evaluated against ground truth)                 │
                                                                 │
═════════════════════════════════════════════════════════════════
BASELINE PERFORMANCE (on wrong 80% split):                      │
• Accuracy: 55.8% (416/746 questions)                           │
• Issue: Used wrong train split (should be 20% not 80%)         │
═════════════════════════════════════════════════════════════════
```

---

## 🚀 Phase 2: MIPROv2 Optimization Process

```
┌─────────────────────────────────────────────────────────────────┐
│                    MIPROv2 Meta-Optimizer                        │
│                    (Qwen Max as Optimizer)                       │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  STEP 1: BASELINE EVALUATION (on correct 20% split)             │
├──────────────────────────────────────────────────────────────────┤
│  • Evaluate baseline RAG on 186 training questions (20%)        │
│  • Use DEFAULT instructions (shown above)                        │
│  • Measure: accuracy with MMESGBench fuzzy matching             │
│  • Expected: ~55-60% baseline (to be established)               │
└──────────────────────────────────────────────────────────────────┘
  │
  │ Baseline accuracy established
  │
  ▼
┌──────────────────────────────────────────────────────────────────┐
│  STEP 2: INSTRUCTION PROPOSAL (Qwen Max as Meta-Optimizer)      │
├──────────────────────────────────────────────────────────────────┤
│  MIPROv2 generates candidate instructions for:                  │
│  • ESGReasoning signature (Stage 1)                             │
│  • AnswerExtraction signature (Stage 2)                         │
│                                                                  │
│  Process:                                                        │
│  1. Analyze baseline failures                                   │
│  2. Generate num_candidates=10 alternative instructions         │
│  3. Each candidate proposes how to improve reasoning            │
│                                                                  │
│  Example candidate instructions:                                │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Candidate 1 (ESGReasoning):                                │ │
│  │ "First identify key ESG metrics mentioned. Then trace      │ │
│  │  evidence from tables/charts. Finally synthesize findings  │ │
│  │  with explicit citation to page numbers."                  │ │
│  │                                                             │ │
│  │ Candidate 2 (AnswerExtraction):                            │ │
│  │ "Locate the most specific numerical value or categorical  │ │
│  │  answer. If format is List, extract all items. Verify     │ │
│  │  format matches expected type before returning."           │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
  │
  │ Generated 10 candidate instruction sets
  │
  ▼
┌──────────────────────────────────────────────────────────────────┐
│  STEP 3: CANDIDATE EVALUATION (Qwen Max as Student)             │
├──────────────────────────────────────────────────────────────────┤
│  For each candidate instruction set:                             │
│  1. Create RAG module with candidate instructions                │
│  2. Evaluate on subset of training data (~20-50 questions)       │
│  3. Measure accuracy with MMESGBench fuzzy matching              │
│  4. Track which candidates perform best                          │
│                                                                  │
│  MIPROv2 trials: 20 iterations                                  │
│  • Each trial tests different instruction combinations           │
│  • Keeps best-performing instructions                            │
│  • Progressively refines based on failures                       │
└──────────────────────────────────────────────────────────────────┘
  │
  │ Best instruction set identified
  │
  ▼
┌──────────────────────────────────────────────────────────────────┐
│  STEP 4: FEW-SHOT DEMONSTRATIONS (Optional)                     │
├──────────────────────────────────────────────────────────────────┤
│  MIPROv2 can also optimize few-shot examples:                   │
│  • max_bootstrapped_demos: 4                                    │
│  • max_labeled_demos: 4                                         │
│  • Selects best examples that improve accuracy                  │
└──────────────────────────────────────────────────────────────────┘
  │
  │ Optimized instructions + few-shot examples
  │
  ▼
┌──────────────────────────────────────────────────────────────────┐
│  STEP 5: FINAL OPTIMIZED MODULE                                 │
├──────────────────────────────────────────────────────────────────┤
│  Output: MMESGBenchRAG with optimized:                          │
│  • ESGReasoning instruction (better than default)               │
│  • AnswerExtraction instruction (better than default)           │
│  • Optional: Few-shot demonstrations                            │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Phase 3: Optimized Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    OPTIMIZED MMESGBench RAG                      │
│              (Same architecture, BETTER prompts)                 │
└─────────────────────────────────────────────────────────────────┘

IDENTICAL PIPELINE STRUCTURE:
  Retrieval → Stage 1 (Reasoning) → Stage 2 (Extraction) → Answer

WHAT CHANGED:
┌──────────────────────────────────────────────────────────────────┐
│  ✨ OPTIMIZED ESGReasoning Instruction                          │
│  (Example - actual instruction generated by MIPROv2)             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ "When analyzing ESG documents:                             │ │
│  │  1. Scan context for tables, charts, and numerical data   │ │
│  │  2. Identify specific metrics related to the question     │ │
│  │  3. Cross-reference multiple sources if available         │ │
│  │  4. Cite page numbers and section references              │ │
│  │  5. Handle ambiguity by stating confidence levels"        │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  ✨ OPTIMIZED AnswerExtraction Instruction                      │
│  (Example - actual instruction generated by MIPROv2)             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ "Extract the final answer:                                 │ │
│  │  • For numbers: Use exact values from text, not ranges    │ │
│  │  • For strings: Match terminology from document           │ │
│  │  • For lists: Extract complete items, check completeness  │ │
│  │  • Format validation: Verify type before returning        │ │
│  │  • If uncertain: Return most specific answer found"       │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘

═════════════════════════════════════════════════════════════════
EXPECTED PERFORMANCE IMPROVEMENT:
• Baseline (20% split): TBD (to be established)
• Target: Baseline + 1-2% absolute improvement
• Method: Better prompts → better reasoning → higher accuracy
═════════════════════════════════════════════════════════════════
```

---

## 📊 Evaluation Strategy

### Dataset Splits (CORRECTED - 20/10/70)
```
┌─────────────────────────────────────────────────────────────────┐
│  Train Set: 186 questions (20%)                                 │
│  • Used for: MIPROv2 optimization                               │
│  • Role: Generate and test candidate instructions              │
│  • Baseline established on this set                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Dev Set: 93 questions (10%)                                    │
│  • Used for: Validation during optimization                     │
│  • Role: Prevent overfitting, tune hyperparameters             │
│  • Final optimized accuracy measured here                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Test Set: 654 questions (70%)                                  │
│  • Used for: Final evaluation (held out)                        │
│  • Role: Compare baseline vs optimized on unseen data          │
│  • Published results will come from this set                   │
└─────────────────────────────────────────────────────────────────┘
```

### Comparison Framework
```
                    TRAIN (186)      DEV (93)       TEST (654)
                    ─────────────    ──────────     ───────────
Baseline            Establish %      Measure %      Final eval
(default prompts)

MIPROv2 Optimized   Optimize here    Validate %     Final eval
(better prompts)

Target              N/A              +1-2% over     +1-2% over
                                     baseline       baseline
```

---

## 🔑 Key Architectural Decisions

### ✅ Same LLM for Meta-Optimizer and Student
**Decision**: Use Qwen Max for both roles
- **Meta-optimizer**: Proposes better instructions (MIPROv2)
- **Student model**: Executes RAG with those instructions
- **Rationale**: Common in DSPy, leverages model's understanding of its own capabilities

### ✅ Two-Stage Reasoning Preserved
**Decision**: Keep ChainOfThought → Extraction architecture
- **Stage 1**: Analyze context with reasoning (optimized instruction)
- **Stage 2**: Extract structured answer (optimized instruction)
- **Rationale**: Proven effective, allows targeted optimization of each stage

### ✅ PostgreSQL Retrieval Fixed
**Decision**: Do NOT optimize retrieval, only prompts
- **Retrieval**: PostgreSQL + pgvector (fixed at top-5)
- **Optimization**: Only ESGReasoning and AnswerExtraction signatures
- **Rationale**: Focus on prompt engineering, not retrieval architecture

### ✅ MMESGBench Evaluation Preserved
**Decision**: Use exact MMESGBench fuzzy matching
- **Metric**: ANLS fuzzy matching (threshold: 0.5)
- **Float tolerance**: ±1% relative tolerance
- **List matching**: 80% threshold
- **Rationale**: 100% compatibility with paper results

---

## 🎯 Success Criteria

### Baseline Establishment (First)
- [ ] Evaluate on correct 186 questions (20% split)
- [ ] Establish baseline accuracy with DEFAULT prompts
- [ ] Expected: Similar to previous results (~55-60%)

### MIPROv2 Optimization (Second)
- [ ] Generate 10 candidate instruction sets
- [ ] Run 20 optimization trials
- [ ] Achieve +1-2% improvement on dev set

### Final Validation (Third)
- [ ] Evaluate optimized model on dev set (93 questions)
- [ ] Measure improvement over baseline
- [ ] Save optimized module for test set evaluation

---

## 📝 Implementation Notes

### Configuration
```python
MIPROv2(
    metric=mmesgbench_accuracy,      # MMESGBench fuzzy matching
    num_candidates=10,               # Instruction variations
    init_temperature=1.0,            # Diversity in proposals
    verbose=True                     # Track optimization progress
)

optimizer.compile(
    student=baseline_rag,            # RAG module to optimize
    trainset=train_set,              # 186 questions (20%)
    num_trials=20,                   # Optimization iterations
    max_bootstrapped_demos=4,        # Auto-generated examples
    max_labeled_demos=4              # Human-labeled examples
)
```

### Estimated Runtime
- Baseline evaluation (186 questions): ~10-15 minutes
- MIPROv2 optimization (20 trials): ~30-60 minutes
- Dev set evaluation (93 questions): ~5-8 minutes
- **Total**: ~45-83 minutes

### Checkpoint Strategy
- MIPROv2 automatically saves progress
- Can resume if interrupted
- Final optimized module saved to disk

---

## 🚀 Next Steps

1. **Re-run baseline** on correct 186 questions (20% split)
2. **Launch MIPROv2** optimization with corrected splits
3. **Evaluate on dev set** (93 questions)
4. **Compare** baseline vs optimized performance
5. **Document** instruction improvements and accuracy gains

---

**Generated**: 2025-10-07
**Status**: Ready for execution with corrected 20/10/70 split
**Baseline**: TBD (to be established on 186 questions)
**Target**: Baseline + 1-2% improvement via optimized prompts
