# Dynamic Cheatsheet - Final Content

**Generated**: November 9, 2025  
**Purpose**: Display the actual cheatsheet content stored after test set evaluations

---

## Test 2: Cold Start Cheatsheet (Test Set Only)

**Source**: 654 test questions, starting from empty  
**File**: `test_cold_cheatsheet_20251101.txt`  
**Accuracy**: 35.6% (233/654)  
**Size**: 53 lines, 3.9 KB

---

## Updated Cheatsheet

### Calculation Patterns:
- **Distance-Based Emissions Calculation**: Calculate emissions from travel by multiplying the total distance traveled by the emission factor.
  - Example: "Total air travel Scope 3 emissions = Total miles traveled by air × Emission factor (kg CO2e/mile)."
- **Unit Conversion**: Convert emissions from kg CO2e to tCO2e by dividing by 1000.
  - Example: "Convert kg CO2e to tCO2e by dividing by 1000."

### ESG Terminology:
- **GHG = Greenhouse Gas**
- **Scope 1, 2, 3 Hierarchy for Emissions Reporting**:
  - **Scope 1**: Direct emissions from owned or controlled sources.
  - **Scope 2**: Indirect emissions from the generation of purchased electricity, steam, heating, and cooling consumed by the reporting company.
  - **Scope 3**: All other indirect emissions that occur in a company's value chain.
  - Example: "Scope 3 emissions include those from employee air travel."

### Format-Specific Tips:
- **List Answers**: Use exact company/division names from context.
  - Example: "Use 'Apple' as mentioned in the context."
- **Float Answers**: Match the precision level from the source data.
  - Example: "For float answers, match the precision level from the source data, e.g., 45.0 tCO2e."

### Document Navigation:
- **Emissions Data**: Typically found in tables with column headers indicating units like EJ or USD.
  - Example: "Emissions data usually in tables with column headers."
- **Date Ranges**: Date ranges often appear in report headers or footers.
  - Example: "Date ranges often in report headers or footers."
- **Specific Information**: Look for detailed breakdowns or specific scenarios in designated pages or sections.
  - Example: "Information on specific scenarios (e.g., Net-Zero Ambition Scenario) is typically detailed on pages like 111-114."

### Common Pitfalls:
- **Don't Confuse Financial Figures**: Be cautious with large numbers and ensure correct unit conversion (e.g., million vs. billion).
  - Example: "Don't confuse 'million' vs 'billion' in financial figures."
- **Check If Percentages Are Already Calculated**: Avoid redundant calculations if percentages are already provided.
  - Example: "Ensure percentages are not unnecessarily recalculated if already given."

### Additional Insights:
- **Identify Sensitivity Trends**: Look for information on how different technologies are affected by changes in discount rates or other economic factors.
  - Example: "Identify technologies with lower sensitivity to WACC increases."
- **Focus on Specific Categories**: Pay attention to detailed breakdowns provided in the document to identify the largest share of emissions within specific categories.
  - Example: "To identify the largest share of emissions within a specific category, focus on detailed breakdowns provided in the document."
- **Review Relevant Sections**: When integrating multiple ESG disclosures, ensure all relevant sections are reviewed.
  - Example: "Review all relevant sections for integrated ESG disclosures."
- **Participant Identification**: Look for specific affiliations or names listed in the document to identify participants from particular organizations.
  - Example: "Participants from specific organizations can be identified by their affiliation in the document."

### New Insights:
- **Risk Identification**: Look for specific pages or sections where risks and challenges are discussed.
  - Example: "Risks and challenges are typically detailed in feedback or discussion sections."
- **Country/Area Listing**: Countries/areas listed in specific sections (like C0.3) are often found in the context of operational locations.
  - Example: "Countries/areas in which a company operates are typically listed in response to specific disclosure codes like C0.3."

These updates further enhance the cheatsheet's utility for future ESG questions by providing more comprehensive guidance on handling various types of information and avoiding common pitfalls.

---

## Test 3: Bootstrap Cheatsheet (Dev + Test Set)

**Source**: 93 dev questions + 654 test questions  
**File**: `test_bootstrap_cheatsheet_20251101.txt`  
**Accuracy**: 34.7% (227/654)  
**Size**: 27 lines, 2.4 KB

---

## Updated Cheatsheet

- **Calculation Patterns**:
  - **Total Calculation**: "Total = Sum of individual parts."
  - **Unit Conversion**: "Convert miles to kilometers using 1 mile = 1.60934 km."
  - **Emission Factor Calculation**: "Emissions (tCO2e) = Total distance (km) × Emission factor (kg CO2e/km) ÷ 1000."
  - **Percentage Calculation**: "Percentage = (Part / Whole) × 100"
  - **Outcome Promotion**: "Promotion of outcomes = Identifying key phrases in context and listing them directly."

- **ESG Terminology**:
  - **GHG (Greenhouse Gas)**: "Greenhouse gas emissions are categorized into three scopes: Scope 1 (direct emissions from owned or controlled sources), Scope 2 (indirect emissions from the generation of purchased electricity, steam, heating, and cooling), and Scope 3 (all other indirect emissions, such as those from upstream and downstream value chains)."
  - **Scope 1, 2, 3 Hierarchy**: "Scope 1 emissions are direct, Scope 2 emissions are indirect from purchased energy, and Scope 3 emissions include all other indirect emissions."

- **Format-Specific Tips**:
  - **List Answers**: "Use exact company/division names from context."
  - **Float Answers**: "Match precision level from source data; for example, if the emission factor is given to two decimal places, ensure your final answer is also precise to two decimal places."

- **Document Navigation**:
  - **Emissions Data**: "Emissions data is usually found in tables with column headers. Look for specific scopes (1, 2, 3) in these tables."
  - **Date Ranges**: "Date ranges for data (e.g., 2021 and 2022) are often mentioned in report headers or footers."
  - **Trend Information**: "Trends and reductions are typically discussed in sections like 'Sustainable Products' or 'ESG Highlights'."

- **Common Pitfalls**:
  - **Don't Mix Up Million vs Billion**: "Be mindful of the scale when dealing with large numbers, ensuring you correctly interpret 'million' vs 'billion'."
  - **Check Calculation Status**: "Ensure that percentages provided in the context are already calculated and do not need further computation."
  - **Avoid Confusion with Scope Levels**: "Do not confuse the different scopes of emissions reporting (1, 2, and 3) as they refer to distinct categories of emissions."
  - **Technical Uncertainty in Integration**: "Understand that technical uncertainty can arise when integrating project-based accounting into GHG inventories, particularly regarding the feasibility and consistency of the approaches."

---

## Quick Comparison

| Aspect | Cold Start | Bootstrap |
|--------|------------|-----------|
| **Questions** | 654 test only | 93 dev + 654 test |
| **Accuracy** | 35.6% | 34.7% |
| **Size** | 53 lines (3.9 KB) | 27 lines (2.4 KB) |
| **Structure** | More sections | More concise |
| **Examples** | More inline examples | Fewer examples |
| **Detail Level** | Verbose | Condensed |

**Key Observation**: Bootstrap cheatsheet is ~50% shorter despite processing more questions (747 vs 654), suggesting the curator compressed/consolidated knowledge rather than accumulating it.

---

**Files Location**: `/Users/victoryim/Local_Git/CC/results/dc_experiments/`

