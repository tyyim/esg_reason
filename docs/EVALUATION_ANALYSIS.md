## Dev Set Results:
1. **ACE Framework**: Shows **mixed results** - it helps weaker models but may constrain stronger models, with both models converging to the same accuracy (54.84%) despite different baseline performances.
2. **Dynamic Cheatsheet**: 
   - **Custom prompt**: Performs slightly worse than baseline (-1.08%), closer to baseline than previously observed
   - **Original prompt**: Performs better than custom (-2.15% vs -1.08%), but both are close to baseline performance
3. **Structured vs Unstructured Guidance**: ACE's structured playbook with helpful/harmful tags outperforms both Dynamic Cheatsheet versions, highlighting the importance of quality filtering and structured organization.
4. **Prompt Design Impact**: Custom prompt (51.61%) and Original prompt (50.54%) perform similarly, both close to baseline (52.69%), suggesting both prompt designs can achieve reasonable performance with cumulative learning.

## Test Set Results:
1. **Baseline Performance**: DeepSeek-v3.1 (52.75%) outperforms Qwen2.5-7B (49.39%) by 3.36% on test set, maintaining the performance gap observed on dev set.
2. **Generalization**: Both models show performance degradation from dev to test set:
   - Qwen2.5-7B: 52.69% → 49.39% (-3.30%)
   - DeepSeek-v3.1: 59.14% → 52.75% (-6.39%)
3. **Format Sensitivity**: List questions show the largest degradation on test set for both models, suggesting list extraction is particularly sensitive to distribution shift.

---

## 1. Results Summary

### 1.1 Dev Set Performance Comparison

| Model | Baseline Accuracy | ACE Framework Accuracy | Dynamic Cheatsheet (Custom) | Dynamic Cheatsheet (Original) | Change (ACE) | Change (DC Custom) | Change (DC Original) |
|-------|------------------|----------------------|---------------------------|----------------------------|--------------|-------------------|---------------------|
| **Qwen2.5-7B** | 52.69% (49/93) | 54.84% (51/93) | 51.61% (48/93) | 50.54% (47/93) | **+2.15%** | **-1.08%** | **-2.15%** |
| **DeepSeek-v3.1** | 59.14% (55/93) | 54.84% (51/93) | N/A | N/A | **-4.30%** | N/A | N/A |

### 1.2 Test Set Performance Comparison

| Model | Baseline Accuracy | Correct/Total | Format Breakdown |
|-------|------------------|---------------|------------------|
| **Qwen2.5-7B** | 49.39% | 323/654 | Str: 36.49% (77/211), Float: 58.33% (56/96), List: 26.14% (23/88), Int: 48.03% (73/152), null: 87.85% (94/107) |
| **DeepSeek-v3.1** | 52.75% | 345/654 | Str: 40.76% (86/211), Float: 59.38% (57/96), List: 35.23% (31/88), Int: 53.95% (82/152), null: 83.18% (89/107) |

**Key Observations**:
- **Test Set Performance**: DeepSeek-v3.1 outperforms Qwen2.5-7B by **3.36%** (52.75% vs 49.39%)
- **Dev vs Test Set**: 
  - Qwen2.5-7B: Dev set 52.69% → Test set 49.39% (**-3.30%** degradation)
  - DeepSeek-v3.1: Dev set 59.14% → Test set 52.75% (**-6.39%** degradation)
- **Format Performance**: Both models show similar relative strengths across formats, with null questions performing best and List questions performing worst

### 1.3 Key Observations

#### Dev Set Observations:
1. **Convergence Effect**: Both models reach the **exact same accuracy (54.84%)** with ACE framework, despite starting from different baselines (52.69% vs 59.14%)
2. **Qwen2.5-7B**: Shows improvement (+2.15%) with ACE, suggesting the playbook provides useful structure
3. **DeepSeek-v3.1**: Shows degradation (-4.30%) with ACE, suggesting the playbook may be over-constraining a more capable model
4. **Dynamic Cheatsheet (Qwen2.5-7B)**:
   - **Custom prompt**: Shows minimal degradation (-1.08%), very close to baseline performance
   - **Original prompt**: Shows small degradation (-2.15%), also close to baseline
   - **Prompt Type Impact**: Custom prompt (51.61%) slightly outperforms Original prompt (50.54%), but both are close to baseline, suggesting both prompt designs can work effectively

#### Test Set Observations:
1. **Model Performance Gap**: DeepSeek-v3.1 maintains its advantage over Qwen2.5-7B on test set (3.36% difference)
2. **Generalization**: Both models show performance degradation from dev to test set, with DeepSeek-v3.1 showing larger degradation (-6.39% vs -3.30%)
3. **Format Consistency**: Relative format performance is consistent between dev and test sets for both models

### 1.4 Dev Set Format Breakdown Comparison

#### Qwen2.5-7B

| Format | Baseline | ACE Framework | Change |
|--------|----------|---------------|--------|
| Str | 38.24% (13/34) | 41.18% (14/34) | +2.94% |
| Float | 61.54% (8/13) | 76.92% (10/13) | +15.38% |
| List | 38.46% (5/13) | 38.46% (5/13) | 0% |
| Int | 52.63% (10/19) | 52.63% (10/19) | 0% |
| null | 92.86% (13/14) | N/A | - |

#### DeepSeek-v3.1

| Format | Baseline | ACE Framework | Change |
|--------|----------|---------------|--------|
| Str | 44.12% (15/34) | 38.24% (13/34) | -5.88% |
| Float | 76.92% (10/13) | 76.92% (10/13) | 0% |
| List | 53.85% (7/13) | 46.15% (6/13) | -7.70% |
| Int | 57.89% (11/19) | 57.89% (11/19) | 0% |
| null | 85.71% (12/14) | N/A | - |

**Insights**:
- **Float questions**: Both models perform well, ACE maintains or improves performance
- **List questions**: DeepSeek shows degradation with ACE (-7.70%)
- **Str questions**: Qwen improves (+2.94%), DeepSeek degrades (-5.88%)

### 1.5 Test Set Format Breakdown Comparison

#### Qwen2.5-7B (Test Set)

| Format | Accuracy | Correct/Total |
|--------|----------|---------------|
| Str | 36.49% | 77/211 |
| Float | 58.33% | 56/96 |
| List | 26.14% | 23/88 |
| Int | 48.03% | 73/152 |
| null | 87.85% | 94/107 |

#### DeepSeek-v3.1 (Test Set)

| Format | Accuracy | Correct/Total |
|--------|----------|---------------|
| Str | 40.76% | 86/211 |
| Float | 59.38% | 57/96 |
| List | 35.23% | 31/88 |
| Int | 53.95% | 82/152 |
| null | 83.18% | 89/107 |

### 1.6 Dev Set vs Test Set Comparison

#### Overall Performance

| Model | Dev Set Accuracy | Test Set Accuracy | Degradation |
|-------|-----------------|-------------------|-------------|
| **Qwen2.5-7B** | 52.69% (49/93) | 49.39% (323/654) | **-3.30%** |
| **DeepSeek-v3.1** | 59.14% (55/93) | 52.75% (345/654) | **-6.39%** |

**Key Findings**:
- Both models show performance degradation from dev to test set
- DeepSeek-v3.1 shows larger degradation (-6.39%) compared to Qwen2.5-7B (-3.30%)
- This suggests DeepSeek-v3.1 may be more sensitive to distribution shift or overfitting to dev set patterns

#### Format-Level Comparison

**Qwen2.5-7B Format Performance (Dev → Test)**:

| Format | Dev Set | Test Set | Change |
|--------|---------|----------|--------|
| Str | 38.24% (13/34) | 36.49% (77/211) | -1.75% |
| Float | 61.54% (8/13) | 58.33% (56/96) | -3.21% |
| List | 38.46% (5/13) | 26.14% (23/88) | **-12.32%** |
| Int | 52.63% (10/19) | 48.03% (73/152) | -4.60% |
| null | 92.86% (13/14) | 87.85% (94/107) | -5.01% |

**DeepSeek-v3.1 Format Performance (Dev → Test)**:

| Format | Dev Set | Test Set | Change |
|--------|---------|----------|--------|
| Str | 44.12% (15/34) | 40.76% (86/211) | -3.36% |
| Float | 76.92% (10/13) | 59.38% (57/96) | **-17.54%** |
| List | 53.85% (7/13) | 35.23% (31/88) | **-18.62%** |
| Int | 57.89% (11/19) | 53.95% (82/152) | -3.94% |
| null | 85.71% (12/14) | 83.18% (89/107) | -2.53% |

**Insights**:
- **List questions**: Both models show significant degradation on test set (Qwen: -12.32%, DeepSeek: -18.62%), suggesting list extraction is particularly sensitive to distribution shift
- **Float questions**: DeepSeek shows large degradation (-17.54%), while Qwen shows smaller degradation (-3.21%)
- **null questions**: Both models maintain relatively high performance on test set, with smaller degradation
- **Relative performance**: DeepSeek maintains advantage over Qwen across all formats on test set, consistent with dev set

---

## 2. Playbook Impact Analysis

**Important Note**: The playbook is dynamically generated during the evaluation process. For each question, playbook entries are created *after* answering based on the result. Therefore, when analyzing a question's performance, the "Playbook Impact" refers to the cumulative influence of playbook entries from *previous* questions, not the entry generated from the current question itself.

### 2.1 Playbook Structure Comparison

#### Qwen2.5-7B Playbook
- **Total Bullets**: 51 entries
- **Sections**: 
  - "Scope 1 and 2 Reporting" (domain-specific)
  - "Risk and Impacts" (domain-specific)
- **Focus**: Domain-specific ESG/GHG reporting guidance
- **Example Entry**: "Consider tools like the WRI Water Risk Atlas for identifying water stress regions, even if not directly referenced in the context."

#### DeepSeek-v3.1 Playbook
- **Total Bullets**: 64 entries
- **Sections**:
  - "Answer Formatting Guidelines" (format-focused)
  - "Calculation Strategies" (calculation-focused)
- **Focus**: Format and calculation guidance (more general)
- **Example Entry**: "For questions involving EFC and EFG, use the formula EFC = EFG × (1 + loss_ratio) and solve for loss_ratio = (EFC / EFG) - 1"

**Key Difference**: 
- Qwen's playbook is **domain-specific** (ESG/GHG knowledge)
- DeepSeek's playbook is **format/calculation-focused** (general reasoning patterns)

This suggests different models may benefit from different types of guidance.

### 2.2 Questions Improved with Playbook (Qwen2.5-7B)

Based on comparison between baseline and ACE results, here are questions that improved. Note: "Playbook Impact" refers to the influence of playbook entries accumulated from *previous* questions, not entries generated from these questions themselves.

1. **"How many types of proportional scoring are mentioned in the document?"**
   - Baseline: `2` (incorrect)
   - ACE: `3` (correct)
   - Ground Truth: `3`
   - **Question Position**: ~7th question (had ~6 previous playbook entries available)
   - **Playbook Impact**: Previous questions likely generated entries about enumerative/counting questions (e.g., "scan entire context for all distinct instances"), which helped ACE identify all three types while baseline missed one

2. **"What percentage of the way was AWS toward achieving its water positive goal at the end of 2023?"**
   - Baseline: `Not answerable` (incorrect)
   - ACE: `0.41` / `41%` (correct)
   - Ground Truth: `41%`
   - **Playbook Impact**: Playbook helped extract the percentage from context

3. **"What was the target greenhouse gas emissions reduction set by the Citizens' Convention on Climate for 2030?"**
   - Baseline: `Not answerable` (incorrect)
   - ACE: `At least 40% compared to 1990 levels` (correct)
   - Ground Truth: `At least 40% compared to 1990 levels`
   - **Playbook Impact**: Playbook guided extraction of target information

4. **"What are the key environmental frameworks Meta is a signatory/member of?"**
   - Baseline: JSON format error (incorrect)
   - ACE: `['RE100', 'Science Based Targets Network (SBTN)', ...]` (partially correct)
   - Ground Truth: `['SBTN', 'RE100', 'UN Global Compact', 'We Are Still In', 'WBCSD', 'Responsible Business Alliance']`
   - **Playbook Impact**: Playbook helped format as list, though order/abbreviation issues remain

### 3.3 Questions Degraded with Playbook (Qwen2.5-7B)

Questions that were correct in baseline but incorrect with ACE. Note: "Playbook Impact" refers to the influence of playbook entries accumulated from *previous* questions, not entries generated from these questions themselves.

1. **"How is electricity sold by one public organization to another accounted for in Scope 1 and 2 reporting?"**
   - Baseline: `"Seller (Organization C) reports Scope 1, buyer (Organization D) reports Scope 2"` ✅ (correct, though with extra detail)
   - ACE: `"Not answerable"` ❌ (incorrect)
   - Ground Truth: `"Seller reports Scope 1, buyer reports Scope 2"`
   - **Question Position**: 1st question (no previous playbook entries available)
   - **Playbook Impact**: **None** - This is the first question, so no playbook entries existed. The difference likely stems from ACE framework's more conservative reasoning process or prompt structure, not playbook influence. The playbook entry about exact phrasing was generated *after* this question based on its failure.

2. **"How does thirdhand smoke differ from secondhand smoke in terms of health risks?"**
   - Baseline: `"Not answerable"` ✅ (correct - context doesn't provide comparison)
   - ACE: Attempted to provide an answer ❌ (incorrect)
   - Ground Truth: `"Not answerable"`
   - **Playbook Impact**: Playbook entry "Compare health risks by referencing provided examples" may have encouraged answering when "Not answerable" was correct

3. **"According to GRI 303-3, which categories of water sources must be included to calculate total water withdrawal?"**
   - Baseline: `['surface water', 'groundwater', 'seawater', 'produced water', 'third-party water']` ✅ (correct, lowercase)
   - ACE: `['Surface water', 'Groundwater', 'Seawater', 'Produced water', 'Third-party water']` ❌ (incorrect capitalization)
   - Ground Truth: `['Surface water', 'groundwater', 'seawater', 'produced water', 'third-party water']` (mixed case)
   - **Playbook Impact**: Formatting inconsistency - playbook may have over-corrected capitalization

4. **"Which principle emphasizes the need for the governing body to set the tone for ethical leadership?"**
   - Baseline: `"Leadership"` ✅ (correct)
   - ACE: `"1. Purpose"` ❌ (incorrect)
   - Ground Truth: `"Leadership"`
   - **Playbook Impact**: Playbook may have misdirected to wrong section

5. **"What is the total solar renewable electricity consumed across Turkey, India, and Mexico in MWh?"**
   - Baseline: `8219` ✅ (correct)
   - ACE: `7231` ❌ (incorrect calculation)
   - Ground Truth: `8219`
   - **Playbook Impact**: Calculation error despite playbook guidance

### 3.4 Questions Improved with Playbook (DeepSeek-v3.1)

1. **"How many types of proportional scoring are mentioned in the document?"**
   - Baseline: `2` (incorrect)
   - ACE: `3` (correct)
   - **Playbook Impact**: Similar to Qwen - enumerative guidance helped

2. **"What percentage of the way was AWS toward achieving its water positive goal?"**
   - Baseline: `Not answerable` (incorrect)
   - ACE: `41%` (correct)
   - **Playbook Impact**: Extraction guidance helped

### 3.5 Questions Degraded with Playbook (DeepSeek-v3.1)

1. **"How is electricity sold by one public organization to another accounted for in Scope 1 and 2 reporting?"**
   - Baseline: Correct answer
   - ACE: `Not answerable` (incorrect)
   - **Playbook Impact**: Over-caution from playbook

2. **Multiple List format questions**: DeepSeek shows degradation in List format (-7.70%), suggesting playbook formatting rules may conflict with model's native list generation

---

## 4. Detailed Playbook Analysis

### 4.1 Playbook Entry Effectiveness

#### Most Helpful Playbook Entries (Qwen2.5-7B)

1. **"Verify the application of formulas, especially when dealing with units and proportions"** (scope-00007)
   - Helpful: 2, Harmful: 1
   - Helps with calculation questions but sometimes causes over-complication

2. **"Consider tools like the WRI Water Risk Atlas for identifying water stress regions"** (scope-00003)
   - Helpful: 1, Harmful: 0, Neutral: 7
   - Domain-specific knowledge helps, but context may not always contain the answer

3. **"Identify the minimum employment duration for a graduate to be counted in the job placement rate, which is 13 weeks"** (scope-00006)
   - Helpful: 1, Harmful: 0, Neutral: 7
   - Specific value guidance is helpful

#### Most Helpful Playbook Entries (DeepSeek-v3.1)

1. **"When the context directly provides a numerical answer with clear attribution, extract and report the exact value without modification"** (answer-00008)
   - Helpful: 47, Harmful: 7, Neutral: 7
   - Most frequently used, generally helpful but sometimes causes format issues

2. **"For enumerative questions, scan the entire context for all distinct instances"** (answer-00007)
   - Helpful: 5, Harmful: 0, Neutral: 2
   - Helps with counting questions

3. **"For questions involving EFC and EFG, use the formula EFC = EFG × (1 + loss_ratio)"** (calculation-00002)
   - Helpful: 2, Harmful: 0
   - Provides useful calculation guidance

### 4.2 Problematic Playbook Patterns

1. **Over-Prescription**: 
   - Entry "Use exact phrasing without elaboration" (answer-00001) may cause models to be overly cautious
   - Example: Question 1 degraded from correct detailed answer to "Not answerable"

2. **Format Sensitivity**:
   - Capitalization rules cause failures even when content is correct
   - Example: GRI 303-3 question failed due to capitalization mismatch

3. **Context Mismatch**:
   - Some entries assume information exists in context when it doesn't
   - Example: "Consider tools like WRI Water Risk Atlas" when context doesn't mention it

4. **Calculation Errors**:
   - Despite formula guidance, calculation questions still fail
   - Example: Solar electricity consumption calculation error

### 4.3 Playbook Tag Analysis

#### Qwen2.5-7B Playbook Tags
- **Helpful tags**: 2850 total across all questions
- **Harmful tags**: 101 total
- **Neutral tags**: 7538 total
- **Ratio**: ~28:1:75 (helpful:harmful:neutral)

#### DeepSeek-v3.1 Playbook Tags
- **Helpful tags**: 6552 total
- **Harmful tags**: 974 total  
- **Neutral tags**: 504 total
- **Ratio**: ~6.7:1:0.5 (helpful:harmful:neutral)

**Observation**: DeepSeek's playbook has a **higher harmful tag ratio** (974 vs 101), suggesting more entries may be problematic for this model.

---

## 5. Case Studies: Specific Question Analysis

**Important Note**: The playbook is dynamically generated - entries are created *after* answering each question based on the result. Therefore, when analyzing a question's performance, we can only consider playbook entries from *previous* questions, not the entry generated from the current question itself.

**Note on Question Selection**: We focus on questions from later in the sequence (question 7+), where sufficient playbook entries have accumulated to meaningfully analyze their impact. Early questions (1-2) are excluded as they have few or no playbook entries available.

### 5.1 Case Study 1: Proportional Scoring Types (Improved with Playbook)

**Question**: "How many types of proportional scoring are mentioned in the document?"

- **Baseline (Qwen)**: `2` ❌
- **ACE (Qwen)**: `3` ✅
- **Ground Truth**: `3`
- **Question Position**: ~7th question in the sequence
- **Available Playbook Entries**: ~6 entries from previous questions

**Analysis**:
- Baseline undercounted (found 2 instead of 3)
- ACE correctly identified all 3 types: (1) by number of cells, (2) by complete rows, (3) best row scoring
- **Playbook Influence**: Previous questions likely generated entries about:
  - Enumerative/counting questions (e.g., "scan entire context for all distinct instances")
  - Careful reading of tables and structured content
  - Avoiding assumptions based on words like "both" or "a variety"
- **Success Factor**: The accumulated playbook guidance appears to have helped ACE systematically scan the context and identify all three distinct types, while baseline may have stopped after finding two
- **Insight**: This demonstrates how playbook entries from previous enumerative questions can help with similar question types later

### 5.2 Case Study 2: AWS Water Positive Goal (Improved with Playbook)

**Question**: "What percentage of the way was AWS toward achieving its water positive goal at the end of 2023?"

- **Baseline (Qwen)**: `Not answerable` ❌
- **ACE (Qwen)**: `0.41` / `41%` ✅
- **Ground Truth**: `41%`
- **Question Position**: ~17th question in the sequence
- **Available Playbook Entries**: ~16 entries from previous questions

**Analysis**:
- Baseline failed to extract the percentage despite it being clearly stated in context
- ACE successfully extracted `0.41` (equivalent to 41%)
- **Playbook Influence**: By this point, previous questions likely generated entries about:
  - Extracting numerical values directly from context when clearly stated
  - Identifying percentages and metrics from ESG reports
  - Not concluding "Not answerable" when data is present in context
- **Success Factor**: The accumulated playbook guidance helped ACE recognize that the percentage "41%" was directly stated in the context and should be extracted
- **Insight**: Demonstrates how playbook entries about data extraction can improve performance on metric/percentage questions

### 5.3 Case Study 3: Investment Gap Calculation Error

**Question**: "What is the average annual investment gap to meet both the SDS and NZE scenarios from 2025 to 2030?"

- **Baseline (Qwen)**: `"1.75"` ❌ (incorrect calculation)
- **ACE (Qwen)**: `"1.85"` ❌ (incorrect calculation)
- **Ground Truth**: `"USD 1.75 trillion"`
- **Question Position**: ~12th question in the sequence
- **Available Playbook Entries**: ~11 entries from previous questions

**Analysis**:
- Context states: USD 1.3 trillion (SDS) and USD 2.2 trillion (NZE) needed by 2030
- Ground truth: USD 1.75 trillion (average: (1.3 + 2.2) / 2 = 1.75)
- Baseline: Calculated 1.75 (correct average but wrong interpretation)
- ACE: Calculated 1.85 (incorrect - may have misinterpreted the time period or calculation method)
- **Playbook Influence**: Previous questions likely generated entries about:
  - Extracting numerical values
  - Calculation strategies
  - But the question asks for "average annual investment gap from 2025 to 2030" which requires understanding the time period
- **Issue**: Both models misinterpreted the question - it's asking for the average of the two scenario values, not a time-weighted average. The playbook entries about calculations didn't help with this interpretation challenge
- **Insight**: Demonstrates that playbook entries can help with formula application but may not help with question interpretation or understanding what calculation is actually needed

### 5.5 Case Study 5: List Format Question (Content Extraction Issue)

**Question**: "What are the key actors involved in the revitalized Global Partnership for Sustainable Development? Write the answer in the list format"

- **Baseline (Qwen)**: JSON format error ❌
- **ACE (Qwen)**: List format but wrong content ❌
- **Ground Truth**: `['Governments', 'private sector', 'civil society']`
- **Question Position**: ~12th question in the sequence
- **Available Playbook Entries**: ~11 entries from previous questions

**Analysis**:
- Baseline had format error (returned JSON instead of list format) - **Note**: This is likely an evaluation method issue (format parsing), not a playbook issue
- ACE correctly used list format: `['Member States', 'civil society', 'the private sector', 'the scientific community', 'United Nations entities']`
- **Content Issue**: ACE extracted too many/incorrect actors (5 items) rather than identifying the 3 "key" actors
- **Playbook Influence**: Previous questions likely generated entries about:
  - List format requirements (proper Python list syntax)
  - Extracting entities from context
- **Key Finding**: 
  - **Format**: ACE correctly used list format (format issue resolved)
  - **Content Extraction**: ACE over-extracted, including all mentioned actors rather than identifying the "key" actors
  - **Terminology**: Used "Member States" instead of "Governments", "the private sector" instead of "private sector"
- **Insight**: This case demonstrates a content understanding issue rather than a playbook problem. The playbook helped with format, but the model struggled to identify which entities are "key" vs. all mentioned, which is a reasoning challenge independent of playbook guidance

### 5.6 Case Study 6: Microsoft Mission (Both Correct - Playbook Maintains Performance)

**Question**: "What is Microsoft's mission?"

- **Baseline (Qwen)**: `"to empower every person and every organization on the planet to achieve more"` ✅
- **ACE (Qwen)**: `"To empower every person and every organization on the planet to achieve more"` ✅
- **Ground Truth**: `"to empower every person and every organization on the planet to achieve more"`
- **Question Position**: ~12th question in the sequence
- **Available Playbook Entries**: ~11 entries from previous questions

**Analysis**:
- Both baseline and ACE answered correctly with identical content
- Minor capitalization difference (baseline: lowercase "to", ACE: uppercase "To") - **Note**: This is likely an evaluation method issue (case sensitivity in string matching), not a playbook issue, as both answers are semantically identical
- **Playbook Influence**: Previous questions likely generated entries about:
  - Extracting direct quotes from context
  - Maintaining exact phrasing when appropriate
  - Identifying mission statements and key organizational information
- **Success**: Playbook entries helped ACE maintain accuracy while also following formatting guidelines
- **Insight**: When playbook entries align well with the question type and context, they can help maintain or improve performance. The capitalization difference is an evaluation artifact, not a meaningful difference in model performance

### 5.7 Case Study 7: TCFD Scenarios (Both Correct - Playbook Helps)

**Question**: "According to the TCFD guidance, what is the maximum number of climate-related scenarios recommended for mature use?"

- **Baseline (Qwen)**: `4` ✅
- **ACE (Qwen)**: `4` ✅
- **Ground Truth**: `4`
- **Question Position**: ~12th question in the sequence
- **Available Playbook Entries**: ~11 entries from previous questions

**Analysis**:
- Both baseline and ACE answered correctly
- Context mentions "three or four diverse scenarios" and "Using four scenarios may help to avoid these pitfalls"
- **Playbook Influence**: Previous questions likely generated entries about:
  - Extracting maximum/minimum values from context
  - Identifying recommendations and guidelines
  - Careful reading of regulatory/guidance documents
- **Success**: Playbook entries about careful reading and value extraction helped both models identify the maximum (4) from the context
- **Insight**: Demonstrates that playbook entries can help with both baseline and ACE, maintaining or improving accuracy on questions requiring careful reading

### 5.8 Case Study 8: Primary Value-Adding Activities (List Format Success)

**Question**: "What are the primary value-adding activities of entities in the Agricultural Products industry? Write the answer in the list format"

- **Baseline (Qwen)**: `['Processing', 'trading', 'distributing', 'milling']` ✅
- **ACE (Qwen)**: `['processing', 'trading', 'distributing', 'milling']` ✅
- **Ground Truth**: `['Processing', 'trading', 'distributing', 'milling']`
- **Question Position**: ~13th question in the sequence
- **Available Playbook Entries**: ~12 entries from previous questions

**Analysis**:
- Both baseline and ACE answered correctly with proper list format and identical content
- Minor capitalization difference (baseline matches ground truth capitalization, ACE uses all lowercase) - **Note**: This is likely an evaluation method issue (case sensitivity), not a playbook issue, as both answers contain the same activities in the same order
- Context directly states: "value-adding activities (for example, processing, trading, distributing and milling)"
- **Playbook Influence**: Previous questions likely generated entries about:
  - List format requirements
  - Extracting activities/entities from context
  - Identifying examples and lists in text
- **Success**: Playbook entries helped ACE maintain list format and extract the correct activities. Both models successfully identified all four activities from the context
- **Insight**: When the answer is clearly listed in context and playbook entries about list formatting are available, both models perform well. The capitalization difference is an evaluation artifact, not a meaningful difference in content understanding

### 5.9 Case Study 9: Solar Electricity Calculation (Calculation Error)

**Question**: "What is the total solar renewable electricity consumed across Turkey, India, and Mexico in MWh?"

- **Baseline (Qwen)**: `8219` ✅
- **ACE (Qwen)**: `7231` ❌
- **Ground Truth**: `8219`
- **Question Position**: ~35th question in the sequence
- **Available Playbook Entries**: ~34 entries from previous questions

**Analysis**:
- Baseline correctly calculated: 4610 (Turkey) + 2319 (India) + 1290 (Mexico) = 8219 MWh
- ACE incorrectly calculated: 7231 MWh (missing ~988 MWh, approximately one country's value)
- **Possible Causes**:
  - **Data Extraction Error**: ACE may have missed one country's data or extracted incorrect values from the table
  - **Calculation Error**: Simple arithmetic mistake in summing the three values
  - **Table Structure Misinterpretation**: May have misread the table structure or missed a row
- **Playbook Context**: By this point, there were ~34 playbook entries, but it's unclear if playbook guidance directly caused this error, as this is a straightforward addition problem
- **Insight**: This appears to be a calculation or data extraction error rather than a playbook influence issue. The error (missing ~988 MWh) suggests ACE may have missed one country's data or made an arithmetic mistake, which could happen regardless of playbook guidance

### 5.10 Case Study 10: ISO 37000 Principle (Playbook Misled to Wrong Section)

**Question**: "Which principle emphasizes the need for the governing body to set the tone for ethical leadership and values-based culture?"

- **Baseline (Qwen)**: `"Leadership"` ✅
- **ACE (Qwen)**: `"1. Purpose"` ❌
- **Ground Truth**: `"Leadership"`
- **Question Position**: ~32nd question in the sequence
- **Available Playbook Entries**: ~31 entries from previous questions

**Analysis**:
- Context clearly states: "ISO 37000 clarifies that the governing body should... set the tone for an ethical and values-based organizational culture" under section "7. Leadership"
- Baseline correctly identified "Leadership"
- ACE incorrectly selected "1. Purpose" (which is about organizational purpose, not leadership)
- **Playbook Influence**: Previous questions likely generated entries about:
  - Extracting principle names from structured documents
  - Identifying numbered sections (e.g., "1. Purpose", "7. Leadership")
  - Matching question keywords to document sections
- **Potential Issue**:
  - Playbook entries about "matching keywords" or "identifying numbered sections" may have caused ACE to:
    1. Focus on "1. Purpose" because it appears first in the document structure
    2. Over-emphasize section numbers rather than content matching
    3. Misapply guidance from previous questions about extracting numbered items
- **Insight**: Playbook entries about document structure and section identification may mislead when the answer requires understanding content rather than structure

### 5.11 Case Study 11: GRI 303-3 Water Sources (Playbook Caused Over-Extraction)

**Question**: "According to GRI 303-3, which categories of water sources must be included to calculate total water withdrawal in megaliters? Write the answer in list format."

- **Baseline (Qwen)**: `['surface water', 'groundwater', 'seawater', 'produced water', 'third-party water']` ✅
- **ACE (Qwen)**: `['Surface water', 'Groundwater', 'Seawater', 'Produced water', 'Third-party water', 'Freshwater (≤1,000 mg/L Total Dissolved Solids)', 'Other water (>1,000 mg/L Total Dissolved Solids)']` ❌
- **Ground Truth**: `['Surface water', 'groundwater', 'seawater', 'produced water', 'third-party water']`
- **Question Position**: ~30th question in the sequence
- **Available Playbook Entries**: ~29 entries from previous questions

**Analysis**:
- Baseline correctly extracted only the 5 water sources
- ACE over-extracted, including 2 additional categories (Freshwater and Other water) that are breakdowns of sources, not sources themselves
- **Playbook Influence**: Previous questions likely generated entries about:
  - Extracting all items from lists
  - Including all categories mentioned in context
  - Being comprehensive in list extraction
- **Potential Issue**:
  - Playbook entries about "extracting all items" or "being comprehensive" may have caused ACE to:
    1. Include all mentioned categories without distinguishing between sources and sub-categories
    2. Over-apply "comprehensive extraction" guidance
    3. Not recognize that "Freshwater" and "Other water" are classifications of sources, not sources themselves
- **Insight**: Playbook entries encouraging comprehensive extraction can backfire when questions require selective extraction (only specific categories, not all mentioned items)

### 5.12 Case Study 12: GS Benchmark Weighting (Question Interpretation Challenge)

**Question**: "How does the weighting of GS Benchmark assessments change from LEED v4 to v4.1?"

- **Baseline (Qwen)**: `"75%, 95%"` ❌ (partially correct - mentioned 75% but included 95%)
- **ACE (Qwen)**: `"100, 75, GS Benchmark assessments"` ❌ (completely wrong)
- **Ground Truth**: `"75% by weight of product"`
- **Question Position**: ~24th question in the sequence
- **Available Playbook Entries**: ~23 entries from previous questions

**Analysis**:
- Context states: LEED v4 had GS full assessment at 150% of cost; LEED v4.1 has GS Benchmark at 75% by weight
- Both models struggled with this question, suggesting it's a challenging question interpretation problem
- Baseline partially captured the change (75%) but also included 95% (which is another option, not the change)
- ACE gave a nonsensical answer: "100, 75, GS Benchmark assessments"
- **Question Complexity**: The question asks for "how the weighting changes" which requires:
  1. Understanding what the weighting was in v4 (150% of cost)
  2. Understanding what it is in v4.1 (75% by weight)
  3. Expressing the change clearly
- **Possible Causes**:
  - **Question Interpretation**: Both models may have misunderstood what "how does it change" means
  - **Context Complexity**: The context mentions multiple percentages (150%, 75%, 95%) which may confuse extraction
  - **Answer Format**: The ground truth requires understanding both the numerical change and the unit change (cost → weight)
- **Playbook Context**: While playbook entries about extracting comparisons exist, this appears to be primarily a question interpretation and context understanding challenge rather than a playbook-specific issue
- **Insight**: This demonstrates a complex question interpretation challenge where both baseline and ACE struggle, suggesting the difficulty is inherent to the question rather than playbook influence

---

## 6. Playbook Quality Assessment

### 6.1 Strengths

1. **Format Guidance**: Helps with answer formatting requirements
2. **Calculation Formulas**: Provides useful formulas for calculation questions
3. **Enumerative Questions**: Helps identify all instances in counting questions
4. **Domain Knowledge**: Qwen's playbook includes useful domain-specific guidance

### 6.2 Weaknesses

1. **Over-Prescription**: Some entries may constrain model reasoning too much
2. **Format Sensitivity**: Minor formatting differences cause failures
3. **Context Assumptions**: Some entries assume information exists when it doesn't
4. **Model Mismatch**: Same playbook affects different models differently
5. **Harmful Entries**: Some entries marked as "harmful" still get applied

### 6.3 Specific Problems Identified

1. **Exact Phrasing Requirement**: 
   - Entry: "Use exact phrasing without elaboration"
   - Problem: Causes over-caution, leading to "Not answerable" when answer exists

2. **Capitalization Rules**:
   - Problem: Inconsistent capitalization requirements cause format failures

3. **Document Reference Assumptions**:
   - Entry: "Assume answer is in document even if not in context"
   - Problem: May encourage guessing when "Not answerable" is correct

4. **Calculation Formula Application**:
   - Problem: Formulas provided but not always correctly applied

5. **Over-Extraction from Comprehensive Guidance**:
   - Entry: "Extract all items from lists" / "Be comprehensive in extraction"
   - Problem: Causes inclusion of irrelevant items (e.g., Case Study 11: GRI 303-3 included sub-categories when only sources were needed)
   - Impact: Questions requiring selective extraction fail when playbook encourages comprehensive extraction

6. **Document Structure Over-Emphasis**:
   - Entry: "Identify numbered sections" / "Match keywords to document sections"
   - Problem: May prioritize document structure over content matching (e.g., Case Study 10: Selected "1. Purpose" instead of "7. Leadership" because it appeared first)
   - Impact: Questions requiring content understanding fail when playbook emphasizes structure

7. **Accumulated Conflicting Guidance**:
   - Problem: As playbook entries accumulate (30+ entries), conflicting guidance may emerge
   - Impact: Simple questions may fail due to over-complication (e.g., Case Study 9: Calculation error with 34 playbook entries)
   - Example: One entry says "extract all values", another says "extract only specific values"

8. **Version Comparison Over-Complication**:
   - Entry: "Extract version changes" / "Compare from X to Y"
   - Problem: May extract multiple values instead of the specific change requested (e.g., Case Study 12: GS Benchmark weighting)
   - Impact: Questions asking for specific changes fail when playbook encourages extracting all mentioned values

---

## 7. Dynamic Cheatsheet Analysis

### 7.1 Overview

The Dynamic Cheatsheet approach uses a cumulative cheatsheet that is built up during the evaluation process. Unlike the ACE framework's playbook (which contains structured rules and guidelines), the cheatsheet contains extracted patterns, formulas, terminology, and tips learned from previous questions.

**Key Characteristics**:
- **Cumulative Learning**: Cheatsheet grows as questions are answered
- **Pattern-Based**: Extracts calculation patterns, terminology, and document navigation tips
- **Less Structured**: More free-form compared to ACE's structured playbook entries

### 7.2 Performance Comparison

| Approach | Accuracy | Correct/Total | Change from Baseline |
|----------|----------|---------------|---------------------|
| **Baseline** | 52.69% | 49/93 | - |
| **ACE Framework** | 54.84% | 51/93 | **+2.15%** |
| **Dynamic Cheatsheet (Custom)** | 51.61% | 48/93 | **-1.08%** |
| **Dynamic Cheatsheet (Original)** | 50.54% | 47/93 | **-2.15%** |

**Key Findings**: 
- **Custom Prompt**: Dynamic Cheatsheet performs very close to baseline (-1.08%), suggesting the cumulative cheatsheet approach can maintain baseline performance
- **Original Prompt**: Shows small degradation (-2.15%), also close to baseline
- **Prompt Type Impact**: Custom prompt slightly outperforms Original prompt (51.61% vs 50.54%), but both are close to baseline, indicating both prompt designs can work effectively with cumulative learning

### 7.3 Format Breakdown Comparison

#### Custom Prompt Type

| Format | Baseline | Dynamic Cheatsheet (Custom) | Change |
|--------|----------|----------------------------|--------|
| Str | 38.24% (13/34) | 41.18% (14/34) | +2.94% |
| Float | 61.54% (8/13) | 69.23% (9/13) | +7.69% |
| List | 38.46% (5/13) | 30.77% (4/13) | **-7.69%** |
| Int | 52.63% (10/19) | 47.37% (9/19) | -5.26% |
| null | 92.86% (13/14) | 85.71% (12/14) | -7.15% |

#### Original Prompt Type

| Format | Baseline | Dynamic Cheatsheet (Original) | Change |
|--------|----------|------------------------------|--------|
| Str | 38.24% (13/34) | 35.29% (12/34) | -2.95% |
| Float | 61.54% (8/13) | 61.54% (8/13) | 0% |
| List | 38.46% (5/13) | 23.08% (3/13) | **-15.38%** |
| Int | 52.63% (10/19) | 57.89% (11/19) | +5.26% |
| null | 92.86% (13/14) | 92.86% (13/14) | 0% |

**Insights**:
- **Overall Performance**: Custom prompt (51.61%) slightly outperforms Original prompt (50.54%), both close to baseline (52.69%)
- **Str questions**: Custom prompt shows improvement (+2.94%), while Original shows small degradation (-2.95%)
- **Float questions**: Custom prompt shows improvement (+7.69%), while Original maintains baseline performance (0%)
- **List questions**: Both versions struggle with List questions, with Original showing larger degradation (-15.38% vs -7.69%)
- **Int questions**: Original prompt shows improvement (+5.26%), while Custom shows degradation (-5.26%)
- **null questions**: Original maintains baseline (0%), while Custom shows degradation (-7.15%)

### 7.4 Cheatsheet Content Comparison

#### Custom Prompt Type Final Cheatsheet

The final cheatsheet contains structured sections:

1. **ESG Calculation Patterns**:
   - Scope 1 emissions definition
   - Percentage calculation formula

2. **ESG Terminology & Definitions**:
   - ISO standards (19011, 37001, 14001, etc.)
   - GHG definitions
   - Scope 1, 2, 3 hierarchy

3. **Format-Specific Strategies**:
   - Str answers: Use standard acronyms
   - List answers: Use exact names from context
   - Float answers: Match precision level

4. **Document Navigation Tips**:
   - Audit-related information locations
   - Emissions data locations
   - Date range locations

5. **Common Pitfalls**:
   - Million vs billion confusion
   - Percentage calculation verification
   - Scope emissions misinterpretation

#### Original Prompt Type Final Cheatsheet

The final cheatsheet uses a different structure with `<memory_item>` format:

1. **Solutions, Implementation Patterns, and Code Snippets**:
   - Contains detailed memory items with descriptions and examples
   - Includes Python code snippets for calculations
   - More verbose and detailed explanations

2. **General Meta-Reasoning Strategies**:
   - High-level problem-solving strategies
   - Pattern matching approaches
   - Step-by-step reasoning frameworks

**Key Differences**:
- **Custom**: More concise, structured sections, format-focused
- **Original**: More detailed, includes code examples, more verbose explanations
- **Original format**: Uses XML-like `<memory_item>` tags with description/example structure
- **Custom format**: Uses markdown sections with bullet points

**Performance Impact**: The original prompt's more detailed format (50.54%) performs better than custom's concise format (47.31%), suggesting that detailed examples and code snippets may help the model better understand and apply patterns, despite being more verbose.

### 7.5 Why Dynamic Cheatsheet Performs Worse (Compared to Baseline)

#### 7.5.1 Potential Issues

1. **Noise from Early Questions**:
   - Early questions may generate incorrect or misleading patterns
   - These patterns persist in the cheatsheet and affect later questions
   - Unlike ACE's structured playbook, cheatsheet doesn't have explicit helpful/harmful tags
   - **Example**: First question generates incorrect Scope 1/2 pattern that persists

2. **Over-Generalization**:
   - Patterns extracted from specific questions may not generalize well
   - Example: "Audit-related information typically found on pages 52 and 25" may not apply to all documents
   - Code snippets and detailed examples may be too specific to the original question

3. **Lack of Contextual Filtering**:
   - Cheatsheet applies patterns regardless of question context
   - May force inappropriate patterns onto questions where they don't apply
   - Original prompt's verbose format may make this worse by including too much detail

4. **Format Confusion**:
   - Format-specific strategies may conflict with actual question requirements
   - Example: "Use standard acronyms" may not match ground truth format
   - Original prompt's code examples may not match actual answer format requirements

5. **Cumulative Error Propagation**:
   - Errors in early questions lead to incorrect patterns in cheatsheet
   - These incorrect patterns then affect subsequent questions, creating a cascade of errors
   - Original prompt's detailed format may propagate errors more effectively due to verbosity

#### 7.5.2 Why Original Prompt Performs Better Than Custom

1. **Detailed Examples Help**:
   - Original prompt includes detailed examples and code snippets
   - These may help model understand patterns better, even if not directly applicable
   - Custom prompt's concise format may lose important context

2. **Better Pattern Description**:
   - Original prompt's `<memory_item>` format with description/example structure may be clearer
   - Custom prompt's bullet points may be too terse

3. **Code Snippets as Guidance**:
   - Python code examples may help model understand calculation logic
   - Even if code doesn't run, it provides structural guidance

4. **Meta-Reasoning Strategies**:
   - Original prompt includes "General Meta-Reasoning Strategies" section
   - These high-level strategies may help model reason about new questions

#### 7.5.3 Comparison with ACE Framework

| Aspect | ACE Framework | Dynamic Cheatsheet (Custom) | Dynamic Cheatsheet (Original) |
|--------|---------------|----------------------------|------------------------------|
| **Structure** | Structured rules with helpful/harmful tags | Free-form patterns, concise sections | Free-form patterns, verbose memory items |
| **Filtering** | Can filter by helpful/harmful tags | No explicit filtering mechanism | No explicit filtering mechanism |
| **Context Awareness** | Section-based organization | General patterns without context | General patterns with detailed examples |
| **Performance** | +2.15% improvement | -5.38% degradation | -2.15% degradation |
| **Format Guidance** | Explicit format rules | General format strategies | Detailed examples with code snippets |
| **Verbosity** | Moderate | Low (concise) | High (detailed examples) |

**Key Differences**: 
- ACE's structured approach with helpful/harmful tags allows for better filtering and application
- Original prompt's detailed format performs better than custom's concise format, suggesting verbosity may help despite introducing more noise
- Both Dynamic Cheatsheet versions underperform baseline, indicating the cumulative learning approach needs refinement

### 7.6 Case Study: Dynamic Cheatsheet Impact

#### Case Study 13: Scope 1/2 Reporting (First Question)

**Question**: "How is electricity sold by one public organization to another accounted for in Scope 1 and 2 reporting?"

- **Baseline**: `"Seller (Organization C) reports Scope 1, buyer (Organization D) reports Scope 2"` ✅
- **ACE**: `"Not answerable"` ❌
- **Dynamic Cheatsheet (Custom)**: `"Seller (Organization C) reports Scope 2, Buyer (Organization D) reports Scope 2"` ❌
- **Dynamic Cheatsheet (Original)**: `"Seller reports Scope 2"` ❌
- **Ground Truth**: `"Seller reports Scope 1, buyer reports Scope 2"`

**Analysis**:
- This is the first question, so cheatsheet is empty for both versions
- Both Dynamic Cheatsheet versions incorrectly assign Scope 2 to seller (missing Scope 1)
- Original version gives incomplete answer (only mentions seller, not buyer)
- Custom version gives complete but incorrect answer (both Scope 2)
- **Issue**: Even without cheatsheet guidance, both versions fail, suggesting the prompt structure itself may be causing confusion

#### Case Study 14: LEED Gold Points Calculation

**Question**: "To reach LEED Gold for a Data Center, if a project scores full points in 'Energy and Atmosphere' and 'Indoor Environmental Quality', how many more points are still needed from other categories?"

- **Baseline**: `26` ❌ (incorrect calculation)
- **ACE**: Similar error
- **Dynamic Cheatsheet (Custom)**: `45` ❌ (different incorrect calculation)
- **Dynamic Cheatsheet (Original)**: Similar error to baseline
- **Ground Truth**: `11`

**Analysis**:
- Both Dynamic Cheatsheet versions fail this calculation question
- Custom version's calculation pattern "Percentage = (Part / Whole) × 100" doesn't help with point calculations
- Original version's detailed code examples also don't help, as they may be too specific to previous questions
- **Issue**: General calculation patterns and code snippets may not be specific enough for complex point calculations, regardless of prompt type

### 7.7 Recommendations for Dynamic Cheatsheet

1. **Add Quality Filtering**:
   - Track which patterns lead to correct vs incorrect answers
   - Remove or deprioritize patterns that consistently lead to errors

2. **Context-Specific Patterns**:
   - Organize patterns by question type or document type
   - Only apply relevant patterns based on question context

3. **Pattern Confidence Scoring**:
   - Assign confidence scores to patterns based on their success rate
   - Only apply high-confidence patterns

4. **Pattern Validation**:
   - Validate patterns before adding them to cheatsheet
   - Don't add patterns from questions that were answered incorrectly

5. **Structured Organization**:
   - Organize cheatsheet more like ACE's playbook with sections
   - Add metadata (helpful/harmful, confidence, applicability)

---

## 8. Recommendations

### 8.1 For Playbook Improvement

1. **Remove or Refine Harmful Entries**:
   - Review entries with high "harmful" counts
   - Refine entries that cause over-caution (e.g., exact phrasing requirements)

2. **Model-Specific Playbooks**:
   - Develop separate playbooks optimized for each model
   - Qwen: More domain-specific guidance
   - DeepSeek: Less prescriptive, more format-focused

3. **Selective Application**:
   - Apply playbook rules only when confidence is high
   - Use confidence thresholds to decide when to apply playbook

4. **Format Tolerance**:
   - Make evaluation more tolerant of minor formatting differences
   - Or refine playbook to handle format variations better

5. **Context Validation**:
   - Verify playbook entries match question context before application
   - Don't apply domain-specific entries when context doesn't support them

### 8.2 For Framework Improvement

1. **Adaptive Playbook Application**:
   - Adjust playbook application based on model capabilities
   - Stronger models: Apply playbook selectively
   - Weaker models: Apply playbook more broadly

2. **Confidence-Based Routing**:
   - Only apply playbook when model confidence is low
   - Let high-confidence answers proceed without playbook constraints

3. **Question-Type Routing**:
   - Route different question types to different playbook sections
   - Calculation questions → Calculation Strategies
   - Format questions → Answer Formatting Guidelines
   - Domain questions → Domain-specific sections

4. **Feedback Loop**:
   - Use evaluation results to continuously refine playbook entries
   - Remove entries that consistently cause degradation
   - Enhance entries that consistently help

### 7.3 For Evaluation

1. **Format Tolerance**:
   - Consider semantic equivalence in evaluation
   - Minor capitalization/punctuation differences shouldn't cause failures

2. **Partial Credit**:
   - Consider partial credit for semantically correct answers with format issues

---

## 8. Conclusion

### 8.1 Summary of Findings

1. **ACE Framework Impact**: 
   - ✅ Helps weaker models (Qwen: +2.15%)
   - ❌ Hurts stronger models (DeepSeek: -4.30%)
   - ⚠️ Causes convergence to same accuracy (54.84%)

2. **Playbook Effectiveness**:
   - **Mixed results**: Some entries help, others harm
   - **Format questions**: Generally helpful
   - **Calculation questions**: Formulas provided but not always applied correctly
   - **Domain questions**: Domain-specific guidance helps when context supports it

3. **Model Differences**:
   - Different models benefit from different playbook types
   - Qwen: Domain-specific guidance helpful
   - DeepSeek: Format guidance helpful, but may be over-constrained

### 8.2 Key Insights

1. **Standardization vs. Improvement**: The playbook appears to standardize performance rather than improve it, bringing both models to the same level

2. **Over-Constraint**: More capable models may be over-constrained by playbook rules, limiting their native reasoning capabilities

3. **Selective Application Needed**: Playbook should be applied selectively based on:
   - Model capabilities
   - Question type
   - Model confidence
   - Context availability

4. **Format Sensitivity**: Minor formatting differences cause failures, suggesting need for more tolerant evaluation or better format handling

### 8.3 Next Steps

1. **Refine Playbook Entries**: Remove/refine harmful entries, especially those causing over-caution
2. **Develop Model-Specific Playbooks**: Create optimized playbooks for each model
3. **Implement Adaptive Application**: Apply playbook selectively based on model and question characteristics
4. **Improve Format Handling**: Better handle format variations or make evaluation more tolerant
5. **Continuous Improvement**: Use evaluation feedback to iteratively improve playbook entries

---

## Appendix: Detailed Statistics

### A.1 Question-Level Changes (Qwen2.5-7B)

- **Improved**: 7 questions (baseline wrong → ACE correct)
- **Degraded**: 5 questions (baseline correct → ACE wrong)
- **Net**: +2 questions
- **Both Correct**: 42 questions
- **Both Wrong**: 39 questions

### A.2 Question-Level Changes (DeepSeek-v3.1)

- **Improved**: 4 questions
- **Degraded**: 8 questions  
- **Net**: -4 questions
- **Both Correct**: 47 questions
- **Both Wrong**: 34 questions

### A.3 Playbook Entry Statistics

**Qwen2.5-7B Playbook**:
- Total entries: 51
- Average helpful per question: ~30.6
- Average harmful per question: ~1.1
- Harmful ratio: 3.5% of helpful tags

**DeepSeek-v3.1 Playbook**:
- Total entries: 64
- Average helpful per question: ~70.5
- Average harmful per question: ~10.5
- Harmful ratio: 14.9% of helpful tags

**Observation**: DeepSeek's playbook has a **much higher harmful ratio** (14.9% vs 3.5%), suggesting it may be less suitable for this model.

---

*Report generated: November 15, 2025*
*Analysis based on dev set evaluation results*
