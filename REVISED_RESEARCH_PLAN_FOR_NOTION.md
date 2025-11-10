# Research Plan - ESG Reasoning (REVISED)

**Last Updated**: November 9, 2025  
**Status**: Phase 1 Complete → Phase 2 In Progress

---

## Evolution of Research Direction

### Original Plan (Sep - Oct 2025)
- Dataset: MMESGBench (933 ESG Q&A pairs)
- Approach: DSPy baseline + prompt optimization techniques
- Tested: GEPA, MIPROv2
- Finding: **Prompt optimization alone has limited impact** (~2-5% improvement)

### Current Direction (Nov 2025 onwards)
- **Key Insight**: Static prompts insufficient for complex ESG reasoning
- **New Focus**: Dynamic test-time learning approaches (DC, ACE)
- **Goal**: Develop novel methodology that outperforms existing dynamic techniques
- **Paper Angle**: Improved dynamic reasoning for ESG question answering

---

## Research Question (REVISED)

**Original**: Can DSPy prompt optimization match fine-tuning performance?

**Revised**: Can dynamic test-time learning with improved knowledge accumulation outperform existing approaches (DC/ACE) for ESG question answering?

### Sub-Questions
1. What are the fundamental limitations of static prompt optimization?
2. How do dynamic approaches (DC/ACE) compare to static optimization?
3. Can we improve upon DC/ACE by optimizing knowledge accumulation strategies?
4. How do model sizes affect the effectiveness of different approaches?
5. Do these findings generalize across multiple ESG datasets?

---

## Three-Phase Research Plan

## Phase 1: Establish Bug-Free Baselines ✅ **COMPLETE**

**Status**: 100% Complete - All baselines evaluated

### Objectives
- Fix all evaluation bugs (null equivalence, ANLS string)
- Establish fair architectural comparisons
- Understand current performance ceiling

### Completed (Nov 9-10, 2025)
✅ Fixed evaluation bugs affecting all approaches
✅ Re-scored all predictions with corrected evaluator
✅ Identified DSPy outperforms DC by 3-4%
✅ Hybrid format-based routing: 50.2% (best overall)
✅ Simple Single-Stage Baseline: **COMPLETE**
  - Dev set: 58.1% (54/93)
  - Test set: 48.5% (317/654)
  - **Beats 2-stage architecture by +1.6%**
  - **Beats DC by +5.8%**
✅ DC-RS (Retrieval & Synthesis) Evaluation: **COMPLETE**
  - Dev set: 44.1% (41/93)
  - **Same accuracy as DC-CU but 10x slower**
  - Test set skipped (not worth computational cost)

### Key Findings
1. **Simple 1-stage > Complex 2-stage** (48.5% vs 46.9%) ⭐
2. **Static prompts > Test-time learning** (48.5% vs 42.7%) ⭐
3. **DSPy optimization > DC test-time learning** (46.9% vs 42.7%)
4. **DC-RS = DC-CU in accuracy** but 10x slower - retrieval adds no value ⭐ NEW
5. **Evaluation methodology critical** (bugs masked true performance)
6. **Hybrid approach best** (format-specific routing: 50.2%)

### Baseline Results (Corrected Nov 9, 2025)

| Approach | Architecture | Dev (93 Q) | Test (654 Q) | Notes |
|----------|--------------|------------|--------------|-------|
| **DSPy Hybrid** | Format-specific | — | **50.2%** | 🏆 Best overall |
| **Simple Baseline** | 1-stage (Direct) | **58.1%** | **48.5%** | ⭐ Beats 2-stage! Fair to DC |
| **DSPy MIPROv2** | 2-stage (CoT + Extract) | 52.7% | 47.4% | Competitive |
| **DSPy Baseline** | 2-stage (CoT + Extract) | 53.8% | 46.9% | Solid |
| **DSPy GEPA** | 2-stage (CoT + Extract) | 61.3% | 46.3% | Best dev, overfits |
| **DC-Bootstrap** | 1-stage + learning | — | 43.7% | Test-time learning |
| **DC-Cold (CU)** | 1-stage + learning | 44.1% | 42.7% | Test-time learning, underperforms |
| **DC-RS** | 1-stage + retrieval + learning | 44.1% | — | Same as DC-CU, 10x slower ⚠️ |

---

## Phase 2: Multi-Model + Multi-Dataset Analysis 🔄 (Next)

**Status**: Ready to Start (After Simple Baseline completes)

### 2.1 Model Size Analysis

**Hypothesis 1**: Larger models may not benefit much from prompt optimization
- **Rationale**: Large models already have strong reasoning, so additional prompts add limited value
- **Test**: Compare prompt optimization gains across model sizes

**Hypothesis 2**: Bigger models might help DC/ACE more
- **Rationale**: Better instruction following + reasoning → better cheatsheet utilization
- **Test**: Compare DC/ACE performance across model sizes

#### Models to Test

| Model | Size | Cost ($/1M tok) | Use Case |
|-------|------|-----------------|----------|
| **qwen2.5-7b-instruct** | 7B | $0.0006 | Baseline (current) |
| **qwen2.5-14b-instruct** | 14B | $0.0012 | Mid-size |
| **qwen2.5-32b-instruct** | 32B | $0.0024 | Large |
| **qwen2.5-72b-instruct** | 72B | $0.004 | Very large |
| **qwen-max** | ~? | $0.06 | Proprietary (reference) |

#### Test Matrix

```
For each model:
1. Simple Baseline (1-stage direct)
2. DSPy Baseline (2-stage)
3. DSPy GEPA (2-stage + optimization)
4. DC-Cold (1-stage + learning)

Dataset: Dev set (93 Q) for cost efficiency
Budget: ~$50-100 for full model comparison
```

#### Expected Insights

**If Hypothesis 1 is correct** (large models don't benefit from prompt optimization):
- 7B: GEPA +7.5% vs Baseline
- 14B: GEPA +5% vs Baseline
- 32B: GEPA +3% vs Baseline
- 72B: GEPA +1% vs Baseline
→ Diminishing returns with model size

**If Hypothesis 2 is correct** (large models help DC/ACE):
- 7B: DC at 44.1%
- 14B: DC at 47%
- 32B: DC at 50%
- 72B: DC at 52%
→ DC scales better with model size

### 2.2 Multi-Dataset Validation

**Objective**: Ensure findings generalize beyond MMESGBench

#### Candidate Datasets

**1. GRI QA** (Global Reporting Initiative)
- Focus: Sustainability reporting standards
- Format: Q&A based on GRI standards
- **Status**: Need to assess availability and format
- **Reason**: Different ESG reporting framework

**2. SusGen-GPT**
- Focus: Sustainability reports
- Format: Question-answering
- **Status**: Need to assess availability and format
- **Reason**: Broader sustainability context

**3. FinanceESG** (if available)
- Focus: Financial ESG metrics
- Format: Numerical + textual Q&A
- **Reason**: Different domain emphasis

#### Dataset Assessment Criteria

For each dataset, evaluate:
1. ✅ **Size**: >500 Q&A pairs preferred
2. ✅ **Quality**: Human-annotated ground truth
3. ✅ **Diversity**: Multiple answer formats (Int, Float, Str, List)
4. ✅ **Complexity**: Requires reasoning, not just extraction
5. ✅ **License**: Open or research-friendly
6. ✅ **Documents**: Access to source ESG reports

#### Next Actions (Phase 2.2)
- [ ] Assess GRI QA dataset (availability, format, size)
- [ ] Assess SusGen-GPT dataset (availability, format, size)
- [ ] Identify additional ESG datasets
- [ ] Pilot test (10-20 questions) on each dataset
- [ ] Select 2-3 datasets for full evaluation

---

## Phase 3: Novel Methodology Development 🎯 (Core Contribution)

**Status**: Planning (After Phase 2 insights)

### 3.1 Identified Weaknesses in Existing Approaches

#### DC (Dynamic Cheatsheet) Weaknesses
1. **Raw Q&A pairs as context** → May contain noise and irrelevant details
2. **Linear accumulation** → No pruning or refinement of cheatsheet
3. **No structured knowledge** → Free-form text, hard to retrieve specific patterns
4. **Retrieval quality** → Semantic similarity may miss relevant patterns
5. **Limited abstraction** → Stores instances, not generalizable rules

#### ACE (Adaptive Contextualization Engine) Weaknesses
*To be assessed after testing ACE*

### 3.2 Proposed Improvements: Dynamic Knowledge Distillation (DKD)

**Core Idea**: Like DC's dynamic prompts, but with **accumulated knowledge** instead of raw Q&A pairs

#### Key Innovations

**1. Structured Knowledge Accumulation**
```
Instead of:
Q: "What is Scope 1?" → A: "Direct emissions"
Q: "What is Scope 2?" → A: "Indirect emissions"

Store as:
RULE: "Scope classifications: 1=Direct, 2=Indirect (purchased), 3=Value chain"
```

**2. Pattern Abstraction**
```
Instead of:
Q: "Calculate 10% of 50" → A: "5"
Q: "Calculate 20% of 100" → A: "20"

Store as:
PATTERN: "Percentage calculation: (part/whole) × 100"
```

**3. Hierarchical Knowledge Base**
```
Level 1: Universal ESG terminology
Level 2: Format-specific extraction patterns
Level 3: Document-specific conventions
Level 4: Company-specific metrics
```

**4. Active Knowledge Refinement**
- Prune contradictory or low-confidence knowledge
- Merge redundant patterns
- Promote frequently useful rules
- Demote rarely helpful information

**5. Retrieval-Augmented Knowledge Access**
- Query: "Calculate emissions reduction percentage"
- Retrieve: Percentage formulas + Emissions terminology + Similar Q&A
- Combine: Construct optimal prompt for this specific question

#### Architecture

```
┌─────────────────────────────────────────────────┐
│                  Question                        │
└───────────────────┬─────────────────────────────┘
                    ↓
    ┌───────────────────────────────────┐
    │  Knowledge Retrieval              │
    │  - Relevant rules                 │
    │  - Similar patterns               │
    │  - Format-specific tips           │
    └──────────────┬────────────────────┘
                   ↓
    ┌───────────────────────────────────┐
    │  Document Retrieval (RAG)         │
    │  - Top-5 relevant chunks          │
    └──────────────┬────────────────────┘
                   ↓
    ┌───────────────────────────────────┐
    │  Dynamic Prompt Construction      │
    │  - Question                       │
    │  - Retrieved knowledge            │
    │  - Document context               │
    └──────────────┬────────────────────┘
                   ↓
    ┌───────────────────────────────────┐
    │  LLM Generation                   │
    │  - Answer                         │
    └──────────────┬────────────────────┘
                   ↓
    ┌───────────────────────────────────┐
    │  Knowledge Extraction & Update    │
    │  - Extract new patterns           │
    │  - Refine existing knowledge      │
    │  - Update knowledge base          │
    └───────────────────────────────────┘
```

### 3.3 Evaluation Plan

**Metrics**:
1. **Accuracy** (primary): Correct answers vs. baseline
2. **Knowledge Quality**: Human evaluation of extracted patterns
3. **Retrieval Efficiency**: Relevant knowledge retrieval rate
4. **Scalability**: Performance over time (early vs. late questions)
5. **Generalization**: Cross-dataset transfer

**Comparison**:
- vs. Simple Baseline (no learning)
- vs. DC (raw Q&A accumulation)
- vs. ACE (adaptive contextualization)
- vs. DSPy GEPA (static optimization)
- vs. Hybrid (format-specific routing)

**Target**: Beat current best (Hybrid: 50.2%) by ≥3% → **53%+**

### 3.4 Success Criteria for Paper

**Minimum Viable Contribution**:
1. ✅ Rigorous evaluation of DC/ACE on ESG datasets
2. ✅ Identification of specific weaknesses
3. ✅ Novel methodology (DKD) with clear improvements
4. ✅ +3% accuracy over best baseline (50.2% → 53%+)
5. ✅ Validated on 2+ ESG datasets
6. ✅ Model-size analysis insights

**Ideal Contribution**:
1. ✅ All minimum criteria
2. ✅ +5% accuracy over best baseline (50.2% → 55%+)
3. ✅ Demonstrated on 3+ datasets
4. ✅ Theoretical framework for dynamic knowledge accumulation
5. ✅ Open-source implementation + benchmarks

---

## Timeline

### November 2025 (Current)
- [x] Fix evaluation bugs
- [x] Re-score all predictions
- [x] Complete Simple Baseline evaluation ✅
- [x] Analyze Simple vs. DC comparison ✅
  - **Finding**: Simple 1-stage beats 2-stage by +1.6%
  - **Finding**: Simple static prompts beat DC learning by +5.8%
- [x] Phase 1 COMPLETE ✅

### December 2025
- [ ] Phase 2.1: Multi-model analysis (qwen2.5-7b/14b/32b/72b)
- [ ] Phase 2.2: Assess and pilot GRI QA + SusGen-GPT
- [ ] Begin ACE evaluation on MMESGBench

### January 2026
- [ ] Complete Phase 2 analysis
- [ ] Design DKD (Dynamic Knowledge Distillation) methodology
- [ ] Implement DKD prototype

### February 2026
- [ ] Evaluate DKD on MMESGBench
- [ ] Evaluate DKD on 2nd dataset (GRI QA or SusGen-GPT)
- [ ] Iterate on DKD based on results

### March 2026
- [ ] Final evaluations across all datasets
- [ ] Statistical significance testing
- [ ] Begin paper writing

### April 2026
- [ ] Complete paper draft
- [ ] Internal review
- [ ] Prepare for submission

**Target Conference**: ACL/EMNLP 2026 (submission deadlines vary)

---

## Budget Estimation

### Compute Costs

**Phase 1 (Completed)**: ~$50
- Dev set evaluations (93 Q × 5 approaches × $0.0006/Q) ≈ $0.30
- Test set evaluations (654 Q × 6 approaches × $0.0006/Q) ≈ $2.40
- Iterations and debugging: ~$50

**Phase 2.1 (Multi-model)**: ~$100
- 4 models × 4 approaches × 93 Q × avg $0.01/Q ≈ $150
- (Using dev set to save cost)

**Phase 2.2 (Multi-dataset pilot)**: ~$50
- 3 datasets × 20 Q pilot × 3 approaches × $0.0006/Q ≈ $0.10
- Full evaluation: 3 datasets × 500 Q × 3 approaches × $0.0006/Q ≈ $3

**Phase 3 (DKD development)**: ~$200
- Prototyping and iterations: ~$100
- Final evaluations: ~$100

**Total Estimated**: ~$400-500

### Human Resources
- Research lead: Design, implementation, analysis
- RA support: Evaluation, dataset preparation, bug fixing
- Advisor: Strategic direction, paper review

---

## Expected Contributions

### 1. Empirical Contributions
- **Comprehensive evaluation** of dynamic learning approaches (DC, ACE) on ESG QA
- **Multi-model analysis** revealing how model size affects optimization strategies
- **Multi-dataset validation** ensuring generalizability beyond single benchmark
- **Fair architectural comparisons** isolating learning effects from architecture

### 2. Methodological Contributions
- **Dynamic Knowledge Distillation (DKD)**: Novel approach to test-time learning
- **Structured knowledge accumulation** vs. raw Q&A storage
- **Active knowledge refinement** mechanisms
- **Retrieval-augmented knowledge access** for dynamic prompting

### 3. Practical Contributions
- **Open-source implementation** of DKD
- **Benchmark suite** for ESG question answering
- **Best practices** for dynamic learning in domain-specific QA

### 4. Theoretical Contributions
- **Framework** for understanding trade-offs: architecture vs. optimization vs. learning
- **Insights** on when dynamic learning outperforms static optimization
- **Guidelines** for selecting approaches based on model size and dataset characteristics

---

## Paper Structure (Tentative)

### Title Options
1. "Dynamic Knowledge Distillation for ESG Question Answering"
2. "Beyond Static Prompts: Structured Knowledge Accumulation for Domain QA"
3. "Improving Test-Time Learning Through Hierarchical Knowledge Distillation"

### Outline

**1. Introduction**
- ESG reporting importance
- Question answering challenges in ESG domain
- Limitations of static prompts
- Our contribution: DKD

**2. Related Work**
- ESG question answering
- Prompt optimization (DSPy, GEPA, MIPROv2)
- Test-time learning (DC, ACE)
- Knowledge distillation

**3. Problem Setting**
- Task definition
- Datasets (MMESGBench, GRI QA, SusGen-GPT)
- Evaluation metrics
- Baseline approaches

**4. Analysis of Existing Approaches**
- Static prompt optimization (DSPy)
- Dynamic learning (DC, ACE)
- Architectural effects (1-stage vs. 2-stage)
- Model size effects
- Identified limitations

**5. Dynamic Knowledge Distillation (DKD)**
- Motivation
- Architecture
- Knowledge representation
- Retrieval mechanism
- Active refinement
- Implementation details

**6. Experiments**
- Setup (models, datasets, baselines)
- Main results (DKD vs. all baselines)
- Ablation studies
- Analysis (knowledge quality, scalability)
- Cross-dataset generalization

**7. Discussion**
- When does dynamic learning help?
- Trade-offs: architecture vs. optimization vs. learning
- Model size considerations
- Limitations and future work

**8. Conclusion**
- Summary of contributions
- Broader implications for domain-specific QA

---

## Risk Mitigation

### Risk 1: DKD doesn't beat baselines
**Mitigation**: Paper focuses on comprehensive analysis of dynamic learning approaches, with DKD as one explored direction. Empirical contributions still valuable.

### Risk 2: Datasets unavailable or unsuitable
**Mitigation**: Prioritize MMESGBench (already have). Pilot test alternatives early. Consider creating new dataset from public ESG reports if needed.

### Risk 3: Budget constraints
**Mitigation**: Use smaller models for iterations. Focus on dev set for development. Run full test set only for final comparisons.

### Risk 4: Limited improvements
**Mitigation**: Even small but consistent improvements across datasets and models make a contribution. Focus on understanding *why* improvements occur.

---

## Key Decisions to Make

### Immediate (This Week)
- [ ] Confirm GRI QA and SusGen-GPT dataset suitability
- [ ] Decide on model sizes for Phase 2.1 (all 4 or subset?)
- [ ] Prioritize: Multi-model first or multi-dataset first?

### Short-term (This Month)
- [ ] Test ACE on MMESGBench
- [ ] Design DKD knowledge representation format
- [ ] Decide on knowledge extraction strategy

### Long-term (Next 2 Months)
- [ ] Target conference (ACL vs. EMNLP vs. NAACL)
- [ ] Collaboration opportunities (other ESG researchers?)
- [ ] Open-source release plan

---

## References to Review

### Dynamic Learning
- Dynamic Cheatsheet (Suzgun et al.)
- ACE paper (to be reviewed)
- In-context learning surveys

### ESG QA
- MMESGBench paper (Microsoft)
- GRI standards documentation
- SusGen-GPT paper (if published)

### Prompt Optimization
- DSPy (Khattab et al.)
- GEPA, MIPROv2
- Chain-of-Thought prompting

### Knowledge Distillation
- Original knowledge distillation (Hinton et al.)
- Self-distillation approaches
- Dynamic knowledge bases

---

## Success Indicators

### Phase 1 ✅
- [x] Bug-free evaluation pipeline
- [x] Fair architectural comparisons
- [x] Clear understanding of current SOTA (50.2%)

### Phase 2 🎯
- [ ] Multi-model insights published (internal report)
- [ ] 2+ additional datasets evaluated
- [ ] ACE baseline established

### Phase 3 🎯
- [ ] DKD prototype working
- [ ] ≥53% accuracy on MMESGBench
- [ ] Validated on 2+ datasets
- [ ] Paper draft complete

### Publication 🎯
- [ ] Conference submission
- [ ] Open-source code release
- [ ] Benchmark leaderboard established

---

**Last Updated**: November 9, 2025  
**Next Review**: December 1, 2025  
**Status**: Phase 1 → Phase 2 transition

