# Corrected Evaluation Summary

## Documents Evaluated

### 1. Microsoft CDP Climate Change Response 2024.pdf
- **Ground Truth**: `corrected_ground_truth_answers.json` (31 questions relabeled)
- **Actual File**: `Microsoft-CDP-2024-Response.pdf` in `source_documents/`
- **Note**: Originally samples.json had "2023.pdf" but corrected GT uses "2024.pdf"

### 2. Gender 2024.pdf
- **Ground Truth**: Original `samples.json` (16 questions)
- **Actual File**: `Gender 2024.pdf` in `source_documents/` (correct file downloaded)
- **Note**: Previously had wrong `UNESCO-GEM-Report-2024.pdf`, now fixed

### 3. ISO-14001-2015.pdf
- **Status**: NOT re-evaluated (kept old results)
- **Note**: Still using wrong document `ISO-14001-2015.pdf` instead of `ISO 14001.pdf`

## ColBERT Text RAG Results

### Overall Performance (47 questions)
- **Accuracy**: 46.8% (22/47 correct)
- **MMESGBench Accuracy**: 46.8%
- **MMESGBench F1 Score**: 38.5%
- **Avg Processing Time**: 4.0s per question

### Per-Document Breakdown

#### Microsoft CDP (31 questions with corrected GT)
- **Accuracy**: 38.7% (12/31)
- **F1 Score**: 38.7%

**Correct Answers (12):**
1. When does Microsoft aim to be carbon negative? → **2030** ✅
2. Microsoft's mission → **"to empower every person..."** ✅
3. TCFD Report frequency → **"Not answerable"** ✅
4. Average emissions per device → **"Not answerable"** ✅
5. Fleet electrification in Redmond → **"Fleet electrification"** ✅
6. Carbon neutrality achieved? → **"Yes"** ✅
7. Scope 3 categories revised? → **"Not answerable"** ✅
8. Top greenhouse gas → **"CO2"** ✅
9. Total Scope 1 emissions → **144960** ✅
10. Land-related emissions? → **"No"** ✅
11. Illinois solar gardens → **"Not answerable"** ✅
12. Korea renewable electricity → **"Not answerable"** ✅

**Failed Answers (19):**
- Scope 3 emissions totals
- Percentage-based calculations
- List-based questions (0% accuracy on Lists)
- Float values (14.3% accuracy)

#### Gender 2024.pdf (16 questions with original GT)
- **Accuracy**: 62.5% (10/16)
- **F1 Score**: 62.5%

**Correct Answers (10):**
1. Gender parity in tertiary education → **1998** ✅
2. Fewer women using Internet → **244000000** ✅
3. Women in STEM jobs → **25%** ✅
4. Mobile phone ownership barrier → **"Lack of family approval"** ✅
5. Spreadsheet skills factor → **"2 times"** ✅
6. Female STEM graduates countries → **9** ✅
7. Women graduated STEM 2022 → **"Not answerable"** ✅
8. Advanced programming proficiency → **"Not answerable"** ✅
9. Reading performance → **"Reading"** ✅
10. Highest out-of-school rates → **"Sub-Saharan Africa"** ✅

### Per-Format Breakdown (47 questions total)

| Format | Accuracy | Correct | Total | Avg F1 |
|--------|----------|---------|-------|--------|
| **Int** | 55.6% | 5 | 9 | 55.6% |
| **Str** | 50.0% | 9 | 18 | 50.0% |
| **null** | 83.3% | 5 | 6 | 83.3% |
| **Float** | 14.3% | 1 | 7 | 14.3% |
| **List** | 0.0% | 0 | 5 | 0.0% |
| **None** | 100.0% | 2 | 2 | 100.0% |

## Key Findings

### Strengths
1. **"Not answerable" Detection**: 83.3% accuracy (5/6 correct)
2. **Integer Values**: 55.6% accuracy - good for simple numerical questions
3. **String Matching**: 50.0% accuracy - decent for text-based answers
4. **Gender 2024 Performance**: 62.5% shows the correct document helps significantly

### Weaknesses
1. **List Format**: 0% accuracy - complete failure on list-based questions
2. **Float Precision**: 14.3% accuracy - struggles with decimal/percentage values
3. **Microsoft CDP**: 38.7% vs Gender's 62.5% - document complexity affects performance

### Comparison with Previous Results
- **Previous (all 3 substituted docs)**: 40.4% accuracy (19/47)
- **Current (corrected Gender 2024)**: 46.8% accuracy (22/47)
- **Improvement**: +6.4% absolute (+3 correct answers)

The corrected Gender 2024.pdf contributed to the improvement!

## Recommendations

1. **List Extraction**: Needs improvement - currently 0% accuracy
2. **Float Parsing**: Better precision handling for percentages and decimals
3. **ISO 14001**: Need to download correct document and re-evaluate
4. **Document Quality**: Gender 2024 (62.5%) vs Microsoft (38.7%) suggests simpler documents perform better

## Next Steps

1. ✅ Complete Microsoft + Gender 2024 corrected evaluation
2. ⏳ Download correct ISO 14001.pdf
3. ⏳ Re-run ISO 14001 evaluation with correct document
4. ⏳ Aggregate all 3 corrected documents for final accuracy/F1
5. ⏳ Compare final metrics with MMESGBench paper targets
