# GEPA Optimized Prompts - Human Review

**File**: `dspy_implementation/optimized_programs/gepa_skip_baseline_20251018_150806.json`
**Optimization Date**: October 18, 2025
**Method**: GEPA (Genetic-Pareto) with qwen-max reflection
**Student Model**: qwen2.5-7b-instruct
**Performance**: 54.8% (51/93) on dev set

---

## Overview

GEPA optimized the prompts through reflection-based evolution:
- **Reflection LM**: qwen-max analyzed failures and proposed improvements
- **32 iterations** completed with 84 connection errors
- **Result**: Degraded by 3.3% vs baseline (58.1% → 54.8%)

---

## Stage 1: Reasoning Module (ChainOfThought)

### Optimized Instructions

```
### Instructions for ESG Document Analysis and Question Answering

**Task Description:**
- **Objective:** Analyze the context from an ESG (Environmental, Social, and
  Governance) document to answer specific questions.
- **Stages:** The task involves a two-stage extraction process:
  - **Stage 1:** Generate a chain-of-thought analysis over the retrieved context
    to answer ESG questions.
  - **Stage 2:** Provide a detailed reasoning and final answer based on the analysis.

**Input Format:**
- **Question:** A specific question related to the ESG document.
- **Context:** Extracts from the ESG document, each with a page number and
  relevance score.
- **doc_id:** The ID or name of the document.

**Output Format:**
- **reasoning:** A detailed explanation of your thought process and how you
  arrived at the answer.
- **analysis:** A clear and concise summary of the key points from the context
  that support your answer.
- **answer:** The final answer to the question. The answer should be one of the
  following types:
  - **Str (String):** For answers that are in text form.
  - **Float:** For answers that are numeric values, especially when precision
    is required.
  - **None:** If the context does not contain sufficient information to answer
    the question, clearly state that the question cannot be answered from the
    given context.

**Important Notes:**
- Ensure that the answer type matches the expected format (e.g., Str for text,
  Float for numbers, None for unanswerable questions).
- Be precise in extracting numeric values and verify the units and decimal places.
- Pay special attention to the units and format of the answer, especially when
  dealing with percentages, monetary values, and other specific metrics.

**General Strategy:**
- Carefully read and understand the context provided.
- Identify the relevant information that directly addresses the question.
- If the context does not provide enough information, clearly state that the
  question cannot be answered.
- Ensure that the answer type (Str, Float, or None) matches the expected format.
- Be precise in extracting and verifying numeric values, especially when dealing
  with units and decimal places.
```

### Domain-Specific Knowledge (Injected by GEPA)

```
**Niche and Domain-Specific Factual Information:**

- **SA8000 Clauses:**
  - **Clause 8.1:** The organization must ensure that wages for a normal work
    week, not including overtime, meet at least legal or industry minimum
    standards, or collective bargaining agreements. Wages should be sufficient
    to meet the basic needs of personnel and provide some discretionary income.

  - **Clause 8.4:** Overtime/premium rate requirements. Senior management who
    have a significant role in setting their own work schedules and a base
    remuneration that significantly exceeds the living wage may not be subject
    to SA8000 8.4 overtime/premium rate requirements.

  - **Clause 8.5:** Prohibits labor practices that reduce workers' wages or
    benefits or result in a precarious employment situation for a worker, such
    as certain contract and apprenticeship schemes.

- **Chief Sustainability Officer (CSO) Responsibilities:**
  - Managing annual budgets for climate mitigation activities.
  - Managing major capital and/or operational expenditures related to low-carbon
    products or services (including R&D).
  - Managing climate-related acquisitions, mergers, and divestitures.
  - Developing a climate transition plan.

- **Global STEM Graduates:**
  - On average, only 35% of STEM graduates are women globally, as of 2018–23.
  - The total number of STEM graduates globally is not provided, making it
    impossible to calculate the exact number of women who graduated with a STEM
    degree in 2022.
```

### Example Demonstrations (Injected by GEPA)

#### Example 1: SA8000 Clause Violation

```
**Question:**
If a worker needs to earn a living wage without working overtime, but company
wages are below living cost, which SA8000 clauses are breached?

**Context:**
- [Page 85, score: 0.794] "Legal and other requirements. Where permitted by law,
  senior management who have a significant role in setting their own work
  schedules and a base remuneration that significantly exceeds the living wage
  may not be subject to SA8000 8.4 overtime/premium rate requirements. Lastly,
  SA8000 8.5 is intended to specifically prohibit labour practices that reduce
  workers' wages or benefits or result in a precarious employment situation for
  a worker, such as certain contract and apprenticeship schemes."

- [Page 84, score: 0.787] "Forcing workers to work excessive overtime in order
  to earn enough to meet basic needs. INTENT OF THE STANDARD This requirement of
  SA8000 is intended to ensure that all workers at a SA8000 certified organisation
  are paid a living wage. As a basis, it also requires that the wage for a normal
  workweek (not inclusive of overtime) to meet at least legal or industry minimum
  standards, or wage rates stipulated in a collective bargaining agreement. As noted"

**Analysis:**
The context explicitly states that if wages are below the living cost, the
organization would be failing to meet the requirements set out in Clause 8.1
and Clause 8.4.

**Answer:**
8.1, 8.4
```

#### Example 2: CSO Responsibilities

```
**Question:**
What are the key responsibilities of the Chief Sustainability Officer?

**Context:**
- [Page 4, score: 0.767] "C1.2 (C1.2) Provide the highest management-level
  position(s) or committee(s) with responsibility for climate-related issues.
  Position or committee Chief Sustainability Officer (CSO) Climate-related
  responsibilities of this position Managing annual budgets for climate mitigation
  activities Managing major capital and/or operational expenditures related to
  low-carbon products or services (including R&D) Managing climate-related
  acquisitions, mergers, and divestitures Developing a climate transition plan"

**Analysis:**
The context provides detailed information about the CSO's responsibilities,
including managing budgets, expenditures, acquisitions, and developing a climate
transition plan.

**Answer:**
Managing annual budgets for climate mitigation activities, managing major capital
and/or operational expenditures related to low-carbon products or services
(including R&D), managing climate-related acquisitions, mergers, and divestitures,
developing a climate transition plan
```

#### Example 3: Unanswerable Question

```
**Question:**
What was the number of women who graduated with a STEM degree globally in 2022?

**Context:**
- [Page 52, score: 0.767] "FIGURE 23: On average, only 35% of STEM graduates are
  women Share of female STEM graduates, selected countries, 2022 or most recent
  year 0 10 20 30 40 50 60 70 Niger Chad Ghana Burkina Faso Lesotho Burundi
  Mozambique Benin Rwanda Seychelles Mauritania Madagascar Botswana Mauritius
  Namibia Cabo Verde South Africa U. R. Tanzania Belarus Ukraine Germany Austria
  Rep. Moldova Luxembourg France Canada Montenegro Bosnia/Herzeg. Afghanistan
  Bangladesh Uzbekistan Kazakhstan Maldives Turkmenistan Sri Lanka"

- [Page 52, score: 0.748] "In Italy, half of the gender gap in tertiary STEM
  graduation is attributed to gender differences in the mathematics and science
  content of the respective secondary school curricula (Granato, 2023). Globally,
  women are considerably less likely to choose STEM fields. In 2018–23, the share
  of STEM graduates who were female was 35% (Figure 23). In 12 out of 122 countries,
  at most one in four graduates were female. Of those, five were"

**Analysis:**
The context provides the global share of female STEM graduates as 35%, but the
total number of STEM graduates globally is not provided, making it impossible to
calculate the exact number of women who graduated with a STEM degree in 2022.

**Answer:**
Not answerable
```

### Input/Output Fields

```
Input Fields:
1. Context: Retrieved chunks from ESG documents
2. Question: ESG question to answer
3. Doc Id: Source document identifier

Output Fields:
1. Reasoning: Let's think step by step in order to ${reasoning}
2. Analysis: Detailed chain-of-thought reasoning analyzing the context to answer
   the question. If context lacks sufficient information, clearly state the
   question cannot be answered.
```

---

## Stage 2: Answer Extraction Module

### Optimized Instructions

```
Extract structured answer from analysis.

Stage 2 of two-stage extraction: Extract final answer in specified format
(Int, Float, Str, List) from the chain-of-thought analysis.

CRITICAL INSTRUCTIONS:
- Extract answer in the specified format: Int, Float, Str, or List
- If the analysis indicates the question cannot be answered from the context,
  respond with exactly: "Not answerable"
- If the analysis indicates it cannot read/understand images or documents,
  respond with exactly: "Fail to answer"
- Otherwise, provide only the answer value without explanation
```

### Input/Output Fields

```
Input Fields:
1. Question: Original ESG question
2. Analysis: Chain-of-thought reasoning from Stage 1
3. Answer Format: Required answer format: Int, Float, Str, or List

Output Fields:
1. Extracted Answer: Final answer in specified format, or "Not answerable" if
   context lacks information, or "Fail to answer" if documents cannot be read
```

---

## Metadata

```json
{
  "python": "3.10",
  "dspy": "3.0.3",
  "cloudpickle": "3.1"
}
```

---

## Analysis: Why GEPA May Have Failed

### 🔴 Potential Issues

1. **Over-Specification**
   - Added 3 detailed examples (SA8000, CSO, STEM)
   - These are very specific to certain questions
   - May bias the model toward these patterns
   - Original baseline had NO examples, letting model generalize

2. **Excessive Prompt Length**
   - Reasoning prompt: **7,749 characters** (very long!)
   - Baseline reasoning prompt: **0 characters** (used default DSPy signature)
   - Extraction prompt: Similar verbosity
   - Long prompts can confuse smaller models (7B)

3. **Domain Knowledge Injection**
   - Hard-coded facts about SA8000, CSO, STEM
   - Only helps ~3 question types
   - For other 90 questions, this is noise
   - May cause model to over-fit to these patterns

4. **Rigid Answer Format Constraints**
   - Very strict extraction rules
   - "CRITICAL INSTRUCTIONS" may intimidate the model
   - Baseline was more flexible

### ✅ What GEPA Did Well

1. **Clear Structure**
   - Two-stage reasoning → extraction is logical
   - Explicit instructions for "Not answerable" cases

2. **Format Awareness**
   - Emphasizes Int/Float/Str/List distinctions
   - Reminds about units and precision

3. **Error Handling**
   - Handles "Fail to answer" for unreadable content
   - Distinguishes "Not answerable" vs "Fail to answer"

### 🎯 Recommendations for Future Optimization

1. **Reduce Prompt Length**
   - Remove hard-coded examples
   - Use few-shot learning with dspy.Predict demos instead

2. **General Instructions Only**
   - Avoid domain-specific facts
   - Let model learn patterns from training data

3. **Test Iteratively**
   - Validate each GEPA iteration on dev set
   - Stop if performance degrades

4. **Consider Larger Model for Optimization**
   - GEPA used qwen-max for reflection (good!)
   - But student (qwen2.5-7b) may be too small for complex prompts
   - Try qwen2.5-14b or qwen2.5-32b as student

---

**Next Step**: Compare these prompts with baseline (no prompt) and MIPROv2 prompts to identify what works and what doesn't.
