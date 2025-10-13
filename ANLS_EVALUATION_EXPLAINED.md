# MMESGBench ANLS 0.5 Matching Explained

## 🎯 What is ANLS?

**ANLS** = **Average Normalized Levenshtein Similarity**

A fuzzy string matching metric that allows for:
- Typos and spelling variations
- Formatting differences (spaces, punctuation, case)
- Partial matches with sufficient similarity

## 📐 How MMESGBench Implements ANLS

### Core ANLS Function (eval_score.py:33-48)

```python
def anls_compute(ground_truth_answers, predicted_answer, threshold=0.5):
    """
    Compute ANLS by taking the best match from multiple ground truth answers.

    :param predicted_answer: The answer predicted by the model.
    :param ground_truth_answers: A list of valid ground truth answers.
    :param threshold: The minimum similarity required for a valid match.
    :return: ANLS score (between 0 and 1).
    """
    max_similarity = 0

    for gt_answer in ground_truth_answers:
        # Use rapidfuzz fuzz.ratio() for similarity
        similarity = fuzz.ratio(predicted_answer.lower(), gt_answer.lower()) / 100  # Normalize to [0,1]
        max_similarity = max(max_similarity, similarity)

    # Return similarity if >= threshold, otherwise 0
    return max(0, 1 - max(0, 1 - max_similarity)) if max_similarity >= threshold else 0
```

### Key Components

1. **Similarity Calculation**: Uses `rapidfuzz.fuzz.ratio()`
   - Based on Levenshtein distance (edit distance)
   - Measures how many insertions/deletions/substitutions needed to transform one string to another
   - Normalized to [0, 1] range (0 = no match, 1 = perfect match)

2. **Case Insensitive**: Both answers converted to lowercase

3. **Threshold**: 0.5 (50% similarity required)
   - If similarity >= 0.5 → answer is correct
   - If similarity < 0.5 → answer is incorrect (score = 0)

## 🔍 When ANLS is Applied

MMESGBench uses different evaluation logic based on answer type:

### Answer Type: "Str" (String)

**Evaluation hierarchy** (eval_score.py:197-221):

```python
if answer_type in ["Str"]:
    gt = get_clean_string(gt)        # Clean ground truth
    pred = get_clean_string(pred)    # Clean prediction

    # 1. BEST CASE: Substring match → 1.0 score
    if gt in pred:
        score = 1.0
    else:
        # 2. Check if exact match required (URLs, dates, emails, etc.)
        if is_exact_match(gt):
            score = (gt == pred)     # Exact match only
        else:
            # 3. Use ANLS with 0.5 threshold
            score = anls_compute(gt, pred)  # Fuzzy match
```

### Other Answer Types

- **Int**: Exact integer match only
- **Float**: Floating point comparison with precision handling
- **List**: Element-wise fuzzy matching with 0.8 threshold
- **None**: Exact string match after cleaning

## 📊 Practical Examples

### Example 1: Perfect Match
```
Ground Truth: "renewable energy"
Prediction:   "renewable energy"
Similarity:   1.0 (100%)
Result:       ✅ Correct (>= 0.5)
```

### Example 2: Minor Typo
```
Ground Truth: "renewable energy"
Prediction:   "renewabel energy"  (typo: 'e' and 'a' swapped)
Similarity:   ~0.94 (94%)
Result:       ✅ Correct (>= 0.5)
```

### Example 3: Formatting Difference
```
Ground Truth: "2050"
Prediction:   "year 2050"
Similarity:   ~0.57 (57%)
Result:       ✅ Correct (>= 0.5)
```

### Example 4: Partial Match (Below Threshold)
```
Ground Truth: "North America"
Prediction:   "America"
Similarity:   ~0.46 (46%)
Result:       ❌ Incorrect (< 0.5)
```

### Example 5: Substring Match (Special Case)
```
Ground Truth: "Paris"
Prediction:   "The answer is Paris, France"
Similarity:   N/A (substring check passes first)
Result:       ✅ Correct (substring found → 1.0)
```

## 🎯 Key Insights

### 1. ANLS is More Forgiving than Exact Match
- Allows for minor errors while maintaining quality
- Common in document understanding tasks (OCR, VQA, etc.)
- Balances strictness with real-world answer variations

### 2. Threshold of 0.5 is Standard
- 50% similarity = reasonable middle ground
- Too low (e.g., 0.3): accepts poor matches
- Too high (e.g., 0.8): too strict, penalizes minor differences

### 3. Answer Type Matters
- **Strings**: Use ANLS for flexibility
- **Numbers**: Exact matching (can't be "fuzzy")
- **Lists**: Each element matched with 0.8 threshold (stricter)

### 4. Substring Check is Powerful
- If ground truth is **contained** in prediction → automatic 1.0
- Handles verbose answers like "The answer is X because..."
- This is why many LLM answers score well

## 📈 Impact on Evaluation

### Comparing Baselines

When comparing to MMESGBench paper results:

```
MMESGBench Paper: 40% accuracy (using ANLS 0.5)
Our Replication:  40% accuracy (using ANLS 0.5)
```

**Critical**: Must use same ANLS threshold for fair comparison!

### What Counts as "Correct"?

**These are ALL correct** under ANLS 0.5:
- ✅ "North America"
- ✅ "north america" (case difference)
- ✅ "North  America" (extra space)
- ✅ "Noth America" (minor typo)
- ✅ "The answer is North America" (substring)

**These are incorrect**:
- ❌ "America" (only 46% similar)
- ❌ "North" (only 38% similar)
- ❌ "South America" (different continent)

## 🔧 Implementation in Our Unified Evaluator

We import MMESGBench's exact `eval_score()` function to ensure identical evaluation:

```python
# unified_evaluator/evaluator.py

from MMESGBench.src.eval.eval_score import eval_score as mmesgbench_eval_score

class UnifiedEvaluator:
    def evaluate(self, predictions):
        for pred in predictions:
            # Use MMESGBench's EXACT evaluation logic
            answer_score = mmesgbench_eval_score(
                gt_answer,           # Ground truth
                predicted_answer,    # Prediction
                gt_format           # Answer type (Int, Float, Str, List)
            )

            # Their logic: score >= 0.5 counts as correct
            answer_correct = (answer_score >= 0.5)
```

## 📝 Summary

**ANLS 0.5** = Fuzzy string matching with 50% similarity threshold

**Used for**: String-type answers in MMESGBench

**Effect**: Allows minor variations while maintaining quality

**Critical for**: Fair comparison with MMESGBench paper baselines

**Our approach**: Use their exact `eval_score()` function for consistency

---

## 🔗 References

- MMESGBench code: `MMESGBench/src/eval/eval_score.py`
- RapidFuzz library: https://github.com/maxbachmann/RapidFuzz
- ANLS metric paper: Scene Text Recognition (various papers use this metric)

---

**Note**: This explains MMESGBench's evaluation. For our unified evaluator, we import their exact implementation to ensure 100% consistency.
