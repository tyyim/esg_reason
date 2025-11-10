# Dynamic Cheatsheet Comparison: DC-RS vs DC-CU

**Generated**: November 10, 2025  
**Dataset**: Dev Set (93 Questions)

---

## Overview

| Metric | DC-RS | DC-CU | Difference |
|--------|-------|-------|------------|
| **Final Accuracy** | 44.1% (41/93) | 44.1% (41/93) | ±0.0% |
| **Cheatsheet Length** | 6670 chars | 3700 chars | DC-RS is 80.3% longer |
| **Avg Time/Question** | ~43 seconds | ~4 seconds | **DC-RS is 10x slower** |
| **Mechanism** | Retrieves top-5 similar Q&As, synthesizes custom cheatsheet per question | Single cumulative cheatsheet, updated after each question | Different approaches |

---

## DC-RS (Retrieval & Synthesis) - Final Cheatsheet

**Length**: 6670 characters  
**Mechanism**: This is the final "master" cheatsheet after processing all 93 questions. For each question, DC-RS retrieved top-5 similar past Q&As and synthesized a custom cheatsheet, which was then used to update this master cheatsheet.

```
Version: 1.45

## Reusable Code Snippets and Solution Strategies

<memory_item>
To determine the percentage of plastic used in Google's consumer hardware product portfolio that was recycled in 2023, follow these steps:
1. **Identify Relevant Data:** Locate the specific section in Google's ESG report that mentions the recycling of plastic in consumer hardware.
2. **Extract Recycling Data:** Extract the total amount of plastic used and the amount of recycled plastic.
3. **Calculate Percentage:** Compute the percentage of recycled plastic based on the total plastic used.

### Example:
Based on the context provided, the percentage of plastic used in Google's consumer hardware product portfolio that was recycled in 2023 can be determined as follows:

```python
def calculate_recycled_plastic_percentage(plastic_data):
    """
    Calculate the percentage of plastic used in Google's consumer hardware product portfolio that was recycled in 2023.
    
    :param plastic_data: Dictionary containing plastic usage and recycling data.
    :return: Percentage of recycled plastic.
    """
    total_plastic_used = plastic_data['total_plastic_used']
    recycled_plastic = plastic_data['recycled_plastic']
    
    if total_plastic_used == 0:
        return 0.0
    
    percentage = (recycled_plastic / total_plastic_used) * 100
    return percentage

# Example usage
plastic_data = {
    'total_plastic_used': 15000,
    'recycled_plastic': 6000
}

print(calculate_recycled_plastic_percentage(plastic_data))
```

** Count: 0

## General Problem-Solving Heuristics

<memory_item>
When dealing with ESG reports, look for specific sections that detail the recycling of materials in consumer hardware. These sections often provide the necessary data to extract and analyze.

### Example:
```python
def find_recycling_section(esg_report):
    """
    Find the section in the ESG report that details the recycling of plastic in consumer hardware.
    
    :param esg_report: String containing the ESG report text.
    :return: Section of the ESG report detailing the recycling of plastic in consumer hardware.
    """
    start_index = esg_report.find("recycling of plastic in consumer hardware")
    end_index = esg_report.find("Our approach to disclosure is informed by the following standards and frameworks:")
    
    if start_index != -1 and end_index != -1:
        return esg_report[start_index:end_index].strip()
    else:
        return "Section not found"

# Example usage
esg_report_text = """
[Page 13, score: 0.651]
Other Google initiatives 
•  Accessibility
•  Crisis response
•  Digital wellbeing
•  Belonging
•  Safety Center

[Page 14, score: 0.616]
•  Google for Health
•  Grow with Google
•  About Google
•  Google products
•  Privacy

[Page 7, score: 0.613]
•  Overview
Other Google initiatives

[Page 8, score: 0.604]
•  Accessibility
•  Crisis response
•  Digital wellbeing
•  Belonging
•  Safety Center
•  Google for Health

[Page 9, score: 0.597]
•  Grow with Google
Our research 
•  Overview
Tools
"""

recycling_section = find_recycling_section(esg_report_text)
print(recycling_section)
```

** Count: 0

## Optimization Techniques & Edge Cases

- **Optimization:** Directly reference the relevant sections of the ESG document for accurate and up-to-date information on plastic recycling in consumer hardware.
- **Edge Case Handling:** Ensure that the plastic data is correctly extracted and that the calculation handles zero-plastic scenarios gracefully.

## Specialized Knowledge & Theorems

- **Plastic Recycling Data:** Google's ESG reports typically contain detailed sections on material recycling, including plastic, in consumer hardware.
- **Percentage Calculation:** Use the formula `(recycled_plastic / total_plastic_used) * 100` to calculate the percentage of recycled plastic.

### Additional Insight from Previous Inputs

- **Material Recycling Data Extraction:** Look for specific keywords like "recycling of plastic in consumer hardware" and "2023" in the ESG document to locate the relevant data.
- **Data Consistency:** Ensure that the data extracted from the ESG document is consistent and accurately reflects the information provided.

#### Example:
```python
def extract_plastic_data(esg_report):
    """
    Extract the total amount of plastic used and the amount of recycled plastic in Google's consumer hardware.
    
    :param esg_report: String containing the ESG report text.
    :return: Tuple containing (total_plastic_used, recycled_plastic).
    """
    total_plastic_used = 0
    recycled_plastic = 0
    
    # Assuming the data is in a specific format
    if "total_plastic_used" in esg_report:
        total_plastic_used = int(esg_report.split("total_plastic_used: ")[1].split(",")[0])
    if "recycled_plastic" in esg_report:
        recycled_plastic = int(esg_report.split("recycled_plastic: ")[1].split(",")[0])
    
    return total_plastic_used, recycled_plastic

# Example usage
esg_report_text = """
[Page 13, score: 0.651]
Other Google initiatives 
•  Accessibility
•  Crisis response
•  Digital wellbeing
•  Belonging
•  Safety Center

[Page 14, score: 0.616]
•  Google for Health
•  Grow with Google
•  About Google
•  Google products
•  Privacy

[Page 7, score: 0.613]
•  Overview
Other Google initiatives

[Page 8, score: 0.604]
•  Accessibility
•  Crisis response
•  Digital wellbeing
•  Belonging
•  Safety Center
•  Google for Health

[Page 9, score: 0.597]
•  Grow with Google
Our research 
•  Overview
Tools
"""

total_plastic_used, recycled_plastic = extract_plastic_data(esg_report_text)
print(f"Total Plastic Used: {total_plastic_used}, Recycled Plastic: {recycled_plastic}")
```

** Count: 0

## Next Question Solution

From the provided context, the percentage of plastic used in Google's consumer hardware product portfolio that was recycled in 2023 can be determined as follows:

```python
def calculate_recycled_plastic_percentage(plastic_data):
    """
    Calculate the percentage of plastic used in Google's consumer hardware product portfolio that was recycled in 2023.
    
    :param plastic_data: Dictionary containing plastic usage and recycling data.
    :return: Percentage of recycled plastic.
    """
    total_plastic_used = plastic_data['total_plastic_used']
    recycled_plastic = plastic_data['recycled_plastic']
    
    if total_plastic_used == 0:
        return 0.0
    
    percentage = (recycled_plastic / total_plastic_used) * 100
    return percentage

# Example usage
plastic_data = {
    'total_plastic_used': 15000,
    'recycled_plastic': 6000
}

print(calculate_recycled_plastic_percentage(plastic_data))
```

** Count: 0
```

** Final Answer: **

40.0
---
---
```

---

## DC-CU (Cumulative) - Final Cheatsheet

**Length**: 3700 characters  
**Mechanism**: This is the single cheatsheet that was cumulatively updated after each question. Every new Q&A pair was used to refine and expand this cheatsheet.

```
## Updated Cheatsheet

- **ESG Terminology**:
  - **GHG (Greenhouse Gas)**: Refers to gases that trap heat in the atmosphere and contribute to global warming, including carbon dioxide, methane, and nitrous oxide.
  - **Scope 1, 2, 3 Hierarchy for Emissions Reporting**: Scope 1 emissions are direct emissions from owned or controlled sources; Scope 2 emissions are indirect emissions from the generation of purchased electricity consumed by the reporting organization; Scope 3 emissions are all other indirect emissions not included in Scope 2 that occur in the value chain of the reporting organization, including both upstream and downstream emissions.
  - **Direct Material Suppliers**: Companies that provide raw materials directly to the organization for use in its products or services.

- **Calculation Patterns**:
  - **Total Emissions Calculation**: Sum up the emissions reported under different scopes. For example, if Scope 1 and Scope 2 emissions are given, the total would be \( \text{Total Emissions} = \text{Scope 1 Emissions} + \text{Scope 2 Emissions} \).
  - **Percentage Calculation**: Compute percentages using the formula \( \text{Percentage} = \left( \frac{\text{Part}}{\text{Whole}} \right) \times 100 \). Note: Ensure to check if the given percentages are already calculated or need further processing.

- **Format-Specific Tips**:
  - **List Answers**: Use exact company/division names from context. For example, "Google is a signatory of RE100, Science Based Targets Network (SBTN), UN Global Compact, We Are Still In, and World Business Council for Sustainable Development (WBCSD)."
  - **Float Answers**: Match the precision level from the source data. For example, if the data is given to two decimal places, ensure your answer is also precise to two decimal places.

- **Document Navigation**:
  - **Emissions Data**: Typically found in tables with column headers specifying the scope of emissions.
  - **Themes and Findings**: Overarching themes and key findings are often mentioned in the overview or introduction sections.
  - **Signatory/Membership Information**: Usually listed in the "About Us" or "Partnerships" section of reports.
  - **Date Ranges**: Often found in report headers or footers.
  - **Tailings Facilities Information**: Found on pages dedicated to environmental impact assessments or specific operational sections, such as page 155 in the provided context.
  - **Direct Material Supplier Reporting**: Look for sections detailing supplier engagement and sustainability initiatives, often starting from page 15 in the provided context.

- **Common Pitfalls**:
  - **Don't confuse 'million' vs 'billion' in financial figures**: Double-check the scale of numbers provided.
  - **Check if percentages are already calculated or need computation**: Verify the context to determine if the given percentages are pre-calculated or need further processing.
  - **Avoid misinterpreting numerical values**: Ensure accurate extraction and formatting of numbers, especially when dealing with large quantities like survey responses.

- **Additional Insights**:
  - **Identifying Regions Based on Climate Change Impacts**: Look for sections discussing climate change impacts, such as heat-humidity mortality risk and maize yield loss, to identify affected regions.
  - **Principal Hazards and Risks**: Examine parts of the document that discuss principal hazards and associated risks expected at specific levels of global warming, such as 1.5°C or 4.2–5.4°C.

This update includes insights from the recent question-answer pair, focusing on identifying regions based on climate change impacts and ensuring accurate extraction and interpretation of numerical values.
```

---

## Key Differences in Cheatsheet Content

### 1. **Structure**

**DC-RS**:
- Versioned (e.g., "Version: 1.45")
- Organized into "Reusable Code Snippets and Solution Strategies"
- Uses `<memory_item>` tags
- More detailed step-by-step instructions for specific questions

**DC-CU**:
- Organized into categories (ESG Terminology, Metrics, etc.)
- Uses bullet points and hierarchical structure
- More general ESG domain knowledge
- Pattern-based guidance

### 2. **Content Focus**

**DC-RS**: 
- More question-specific (e.g., "To determine the percentage of plastic used in Google's consumer hardware...")
- Contains explicit calculation steps
- More concrete, example-driven

**DC-CU**:
- More domain-general (e.g., "GHG (Greenhouse Gas): Refers to gases that trap heat...")
- Contains terminology definitions
- More abstract, pattern-focused

### 3. **Length Trade-off**

- DC-RS is 80.3% longer
- More content ≠ better performance (both achieved 44.1%)
- DC-RS's retrieval mechanism adds verbosity without improving accuracy

---

## Performance Analysis

Despite DC-RS having a longer, more detailed cheatsheet with question-specific examples:

### Same Overall Accuracy (44.1%)
- Both approaches answered 41/93 questions correctly
- The additional detail in DC-RS's cheatsheet didn't translate to better performance

### Format-Specific Trade-offs

| Format | DC-RS | DC-CU | Winner |
|--------|-------|-------|--------|
| **String** | 44.1% | 17.6% | DC-RS (+26.5%) ✅ |
| **Null** | 35.7% | 85.7% | DC-CU (+50.0%) ✅ |
| **Float** | 69.2% | 69.2% | Tie |
| **Int** | 42.1% | 42.1% | Tie |
| **List** | 30.8% | 46.2% | DC-CU (+15.4%) ✅ |

### Why DC-RS's Cheatsheet Didn't Help

1. **Retrieval adds noise**: Retrieved Q&As sometimes mislead the model
2. **Overly specific**: Question-specific examples don't generalize well
3. **Null detection hurt**: Extra context confuses refusal decisions
4. **Computational cost**: 10x slower with no benefit

---

## Conclusion

**Winner**: DC-CU (Cumulative)

**Reasons**:
1. ✅ **Same accuracy** (44.1%)
2. ✅ **10x faster** (~4s vs ~43s per question)
3. ✅ **Better null detection** (85.7% vs 35.7%)
4. ✅ **Simpler, cleaner cheatsheet** (3.7K vs 6.7K chars)
5. ✅ **More generalizable patterns**

**DC-RS's longer, more detailed cheatsheet demonstrates that more content ≠ better performance.** The retrieval mechanism's computational overhead and noise outweigh any potential benefits from question-specific examples.

---

**Recommendation**: Use DC-CU for ESG question answering. DC-RS's retrieval adds no value.
