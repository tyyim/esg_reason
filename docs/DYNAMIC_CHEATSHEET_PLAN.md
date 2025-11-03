# Dynamic Cheatsheet Implementation Plan

**Date:** November 1, 2025  
**Status:** Planning - Decision Needed  
**Estimated Time:** 4 weeks  
**Cost:** $3,805

---

## Quick Summary (2 Minutes)

**What:** Add Dynamic Cheatsheet (DC) as test-time learning baseline to compare against DSPy optimization

**Why:**
- Novel research (first ESG application of DC)
- Potential +5-10% accuracy gain over current best (50.2%)
- Publishable regardless of outcome

**Cost:** $3,805 ($3,800 labor + $5 API)

**Recommendation:** YES - Research value justifies investment

---

## Current Results vs Proposed

### Current Results (654 Test Questions)

```
Baseline (qwen2.5-7b):  47.4%  (Zero-shot)
MIPROv2:                47.6%  (+0.2%, prompt optimization)
GEPA:                   45.7%  (-1.7%, reflection-based)
Hybrid (Format Router): 50.2%  (+2.6%, CURRENT BEST)
```

### Proposed: Dynamic Cheatsheet

```
DC-Cold (fair):    48-50%  (Empty cheatsheet, fair comparison)
DC-Warm (unfair):  52-56%  (Learns from test set, research only)
```

**Key Difference:**
- **DSPy:** Learns BEFORE test (train/dev) -> static prompts
- **DC:** Learns DURING test -> evolving "cheatsheet" memory

---

## How DC Works

### DSPy (Current Approach)

```
BEFORE Test:
Train (186 Q) + Dev (93 Q)  ->  Optimizer  ->  Static Prompt

DURING Test:
Q1   ->  [Same Prompt]  ->  Answer 1
Q2   ->  [Same Prompt]  ->  Answer 2
...
Q654 ->  [Same Prompt]  ->  Answer 654

- Fair: No test contamination
- No learning during test
```

### DC (Proposed)

```
DURING Test (learns as it goes):
Q1   ->  [Empty]         ->  Answer 1  ->  Extract insight
Q2   ->  [Insight Q1]    ->  Answer 2  ->  Extract insight
Q3   ->  [Insights Q1-2] ->  Answer 3  ->  Extract insight
...
Q654 ->  [Insights Q1-653] ->  Answer 654

- Accumulates domain knowledge
- Test contamination (learns FROM test, not just ON test)
```

**Example Cheatsheet Evolution:**

```
After Q1:   "(empty)"
After Q50:  "- Scope 1 = direct emissions
             - Lists need JSON array format"
After Q200: "- Scope 1 = direct, Scope 2 = indirect
             - Calculate %: (X/Y) x 100
             - null if 'not specified' in context"
```

---

## Architecture Integration

### Current Pipeline

```
Question -> PostgreSQL Retrieval -> DSPy Reasoning -> DSPy Extraction -> Answer
```

### DC-Enhanced Pipeline

```
Question -> PostgreSQL Retrieval -> Cheatsheet -> DC Generator -> Answer
                                        |
                                        v
                                   DC Curator (updates cheatsheet for next Q)
```

---

## Cost-Benefit Analysis

### Investment

**Week 1: POC & Setup** - $800  
**Week 2: Implementation** - $800  
**Week 3: Evaluation** - $200 + $3 API  
**Week 4: Analysis** - $800  
**Buffer (10%)** - $400  

**Total:** $3,805

### Expected Return

**1 Publishable Paper (ACL/EMNLP)** - ~$10,000 value  
**Reusable DC Framework** - ~$2,000 saved on future projects  

**Total Value:** ~$12,000  
**ROI:** 3.2x

### API Costs (Per Run)

- Dev set (93 Q): $0.11
- Test cold (654 Q): $0.80
- Test warm (933 Q): $1.12
- **Total experiments:** ~$5

---

## Expected Results & Hypotheses

### H1: DC-Cold Similar to Baseline (Fair Comparison)

- **Prediction:** 48-50% vs 47.4% baseline
- **Why:** Without prior knowledge, DC has no advantage
- **Fair?:** YES (both start from zero)

### H2: DC-Warm Exceeds Hybrid (Unfair but Insightful)

- **Prediction:** 52-56% vs 50.2% Hybrid
- **Why:** 654 questions worth of accumulated patterns
- **Fair?:** NO (learns from test set)
- **Value:** Shows upper bound of test-time learning

### H3: DC Helps Structured Formats (Int/Float/List)

- **Prediction:** +5-15% on Int/Float/List, +/-0-2% on Str/null
- **Why:** Patterns/formulas easier to learn than context-dependent text
- **Example:** Like Game of 24 (10% -> 99% with DC)

### H4: DC-Retrieval Better Than DC-Cumulative

- **Prediction:** +1-2% due to focused memory
- **Why:** ESG is diverse (45 docs, 5 formats) -> retrieval better than cumulative

---

## Implementation Timeline

### Week 1: POC ($800 labor)

**Goal:** Verify DC works with MMESGBench

**Tasks:**
- Clone DC repository
- Test with Qwen models
- Implement basic wrapper
- Test on 10 dev questions

**Deliverable:** POC working or documented failure

**CHECKPOINT:** Stop if POC fails (sunk cost: $800)

### Week 2: Implementation ($800 labor)

**Goal:** Full DC-Cumulative with RAG

**Tasks:**
- DC + RAG integration
- ESG-specific prompts (generator + curator)
- Checkpointing & error handling
- Dev set validation (93 Q)

**Deliverable:** DC working on full dev set

**CHECKPOINT:** Stop if dev set < 45% (not promising)

### Week 3: Evaluation ($200 labor + $3 API)

**Goal:** Test all 4 variants

**Tasks:**
- DC-Cumulative cold (654 Q) - $0.80
- DC-Cumulative warm (933 Q) - $1.12
- DC-Retrieval cold (654 Q) - $0.90
- DC-Retrieval warm (933 Q) - $1.30

**Deliverable:** Complete experimental results

### Week 4: Analysis ($800 labor)

**Goal:** Complete documentation

**Tasks:**
- Compare DC vs DSPy approaches
- Statistical significance testing
- Cost-performance analysis
- Write findings report
- Update main documentation

**Deliverable:** DYNAMIC_CHEATSHEET_FINDINGS.md

---

## Decision Framework

### Reasons to Implement

**1. Research Novelty (5/5 stars)**
- First DC application to ESG domain
- Novel comparison: test-time learning vs prompt optimization
- Publishable at ACL/EMNLP 2026

**2. Performance Upside (4/5 stars)**
- +5-10% potential over current best
- Even DC-Cold may match Hybrid (50.2%)

**3. Cost Efficiency (3/5 stars)**
- $3,805 total (reasonable for research)
- Still 100x cheaper than qwen-max baseline

**4. Low Risk (5/5 stars)**
- Clear off-ramps at Week 1 & Week 2
- Even negative results publishable
- 4-week timeline (not long-term)

### Reasons NOT to Implement

**1. Test Contamination (3/5 concern)**
- DC-Warm learns FROM test set
- Need careful documentation to avoid misleading claims

**2. Implementation Complexity (2/5 concern)**
- Integration with DC repo may have issues
- Two variants to implement

**3. Unclear Production Path (2/5 concern)**
- DC-Cold may not beat Hybrid
- DC-Warm can't be deployed (test contamination)

**4. Opportunity Cost (3/5 concern)**
- Could spend 4 weeks on Two-Stage Agentic (53-55% predicted)
- Or deploy Hybrid immediately (50.2%)

---

## Research Contribution

### Paper Outline

**Title:** "Test-Time Learning vs Prompt Optimization for ESG Question Answering"

**Research Question:** Does test-time learning (DC) outperform prompt optimization (DSPy) for specialized domain QA?

**Contributions:**
1. First ESG application of Dynamic Cheatsheet
2. Fair comparison of two emerging LM adaptation paradigms
3. Cost-performance tradeoffs quantified ($0.80 vs $0.39 for +1-3%)
4. When test-time learning helps vs hurts (format-specific analysis)

**Venue:** ACL/EMNLP 2026 or FinNLP/ESG workshop

**Impact:** Guides practitioners on when to use optimization vs adaptation

---

## Quick Start (If Approved)

### Step 1: Clone DC Repository

```bash
cd /Users/victoryim/Local_Git/CC
git clone https://github.com/suzgunmirac/dynamic-cheatsheet.git dc_repo
pip install -r dc_repo/requirements.txt
```

### Step 2: Test Basic Functionality

```python
from dc_repo.dynamic_cheatsheet.language_model import LanguageModel

model = LanguageModel(model_name="dashscope/qwen2.5-7b-instruct")
result = model.advanced_generate(
    approach_name="DynamicCheatsheet_Cumulative",
    input_txt="What is 2+2?",
    cheatsheet="(empty)",
    generator_template="Answer: {input}",
    cheatsheet_template="Update: {input}"
)
print(result['final_answer'])  # Should work
```

### Step 3: Follow Implementation Guide

See `DC_IMPLEMENTATION_GUIDE.md` for detailed steps.

---

## Success Criteria

### Minimum (Must Have)

- DC-Cumulative cold start implemented
- Test set evaluation complete (654 Q)
- Results compared to baseline
- Format-specific breakdown
- Findings documented

### Complete (Should Have)

- DC-Retrieval implemented
- Warm start experiments complete
- Statistical significance tested
- Cost-performance analyzed
- Paper draft started

---

## Decision Record

**Decision:** [ ] GO  |  [ ] NO-GO

**Rationale:** 

**If GO, Next Actions:**
1. Create GitHub issue: "Implement Dynamic Cheatsheet baseline"
2. Clone DC repository
3. Begin Week 1 POC
4. Update Notion roadmap

**If NO-GO, Alternative:**
- Pursue Two-Stage Agentic (53-55%, $2K, 3 weeks)
- Deploy Hybrid immediately (50.2%, $1K, 2 weeks)
- Move to Fine-Tuning (55-60%, $5K+, 6 weeks)

---

## Resources

### Dynamic Cheatsheet

- **Paper:** https://arxiv.org/abs/2504.07952
- **GitHub:** https://github.com/suzgunmirac/dynamic-cheatsheet
- **Example:** `dc_repo/ExampleUsage.ipynb`

### Your Project

- **Current Status:** `README.md` (Hybrid 50.2% best)
- **Research Findings:** `RESEARCH_FINDINGS.md`
- **Error Analysis:** `analysis/reports/COMPLETE_ERROR_ANALYSIS.md`

### Implementation

- **Implementation Guide:** `docs/DC_IMPLEMENTATION_GUIDE.md`
- **Baseline Code:** `dspy_implementation/evaluate_baseline.py`
- **RAG Module:** `dspy_implementation/dspy_rag_module.py`

---

**Status:** Awaiting decision  
**Recommendation:** YES - Implement DC  
**Last Updated:** November 1, 2025
