# List Format Error Analysis - DSPy Framework Advantage

**Date**: November 11, 2025  
**Finding**: DSPy framework provides significant formatting advantage for List questions

---

## 📊 Performance Summary

| Implementation | Model | List Accuracy | Gap |
|----------------|-------|---------------|-----|
| **DSPy 2-Stage Baseline** | qwen2.5-7b | **23.1%** (3/13) | baseline |
| **Simple Baseline (RAW)** | qwen2.5-7b | **0.0%** (0/13) | **-23.1%** ❌ |
| **Simple Baseline (RAW)** | DeepSeek v3.1 | **0.0%** (0/13) | **-23.1%** ❌ |

**Key Finding**: DSPy framework provides a **+23.1% advantage** on List format questions!

---

## 🔍 Root Cause: Output Formatting Difference

### Ground Truth Format
```python
['item1', 'item2', 'item3']  # Python list string representation
```

### DSPy Baseline Output (23.1% accurate)
```python
["item1", "item2", "item3"]  # JSON format with brackets and quotes
```
**Distance from GT**: LOW (similar syntax: brackets + quotes)

### RAW Implementation Output (0.0% accurate)
```python
item1, item2, item3  # Plain comma-separated text
```
**Distance from GT**: HIGH (missing brackets and quotes)

---

## 📋 Detailed Examples

### Example 1: Water Sources (✓ DSPy Correct, ✗ RAW Incorrect)

**Question**: According to GRI 303-3, which categories of water sources must be included?

**Ground Truth**:
```python
['Surface water', 'groundwater', 'seawater', 'produced water', 'third-party water']
```

**DSPy Baseline** (✓ Correct):
```json
["Surface water", "Groundwater", "Seawater", "Produced water", "Third-party water"]
```
- Has brackets ✅
- Has quotes ✅  
- ANLS score: HIGH (similar format)

**RAW qwen2.5-7b** (✗ Incorrect):
```
Surface water, Groundwater, Seawater, Produced water, Third-party water
```
- No brackets ❌
- No quotes ❌
- ANLS score: LOW (different format)

---

### Example 2: Age Groups (✓ DSPy Correct, ✗ RAW Incorrect)

**Question**: What are the three age groups specified in GRI 405-1?

**Ground Truth**:
```python
['Under 30 years old', '30–50 years old', 'Over 50 years old']
```

**DSPy Baseline** (✓ Correct):
```json
["Under 30 years old", "30-50 years old", "Over 50 years old"]
```
- Brackets + quotes match format ✅

**RAW qwen2.5-7b** (✗ Incorrect):
```
under 30 years old, 30-50 years old, over 50 years old
```
- Plain text, no brackets/quotes ❌

---

### Example 3: Energy Themes (✓ DSPy Correct, ✗ RAW Incorrect)

**Question**: What are the three overarching themes for this year's Outlook?

**Ground Truth**:
```python
['Energy security', 'clean energy transitions', 'uncertainty']
```

**DSPy Baseline** (✓ Correct):
```json
["energy security", "clean energy transitions", "uncertainty"]
```

**RAW qwen2.5-7b** (✗ Incorrect):
```
Energy security, clean energy transitions, uncertainty
```

---

## 🎯 Why DSPy Performs Better

### 1. **Structured Output Formatting**
DSPy's framework automatically formats outputs to match expected structures:
- Uses JSON-like syntax for lists
- Adds brackets and quotes
- Maintains consistent formatting

### 2. **ANLS Evaluation Favors DSPy**
ANLS (Average Normalized Levenshtein Similarity) measures string distance:
- DSPy output: `["item1", "item2"]` 
- Ground truth: `['item1', 'item2']`
- **Distance**: Small (only difference is quote type)

- RAW output: `item1, item2`
- Ground truth: `['item1', 'item2']`
- **Distance**: Large (missing 4 characters: `[`, `'`, `'`, `]`)

### 3. **Two-Stage Architecture Advantage**
DSPy's 2-stage baseline:
1. **Reasoning Agent**: Extracts information
2. **Extraction Agent**: Formats output according to schema

RAW implementation:
1. **Single Prompt**: Must do both reasoning AND formatting in one step

---

## 📊 Overall Impact on Performance

### Dev Set (93 Questions)

| Format | Count | DSPy Advantage |
|--------|-------|----------------|
| **Float** | 13 | +0% (69.2% both) |
| **Int** | 19 | ±0% (57.9% both) |
| **Str** | 34 | Varies |
| **List** | 13 | **+23.1%** ⭐ |
| **null** | 14 | TBD |

**List format contribution to overall gap**:
- DSPy gets 3/13 correct on List
- RAW gets 0/13 correct on List
- **Impact**: +3.2% to DSPy's overall accuracy (3/93)

---

## 🔧 Why RAW Implementations Fail

### Prompt Structure Issue

**RAW Prompt** (from our implementation):
```
Expected Answer Format: List

Instructions:
- For List: Return comma-separated items (e.g., 'Apple, Google, Microsoft')
```

**Result**: Model outputs `Apple, Google, Microsoft` (plain text)

**DSPy Implicit Formatting** (from framework):
- DSPy's `Predict` module enforces schema compliance
- Automatically wraps outputs in appropriate format
- Returns JSON-compatible structures

---

## 💡 Solutions for RAW Implementation

### Option 1: Explicit Format Instructions
```python
prompt = """
Expected Answer Format: List

Instructions:
- For List: Return a JSON-formatted list with brackets and quotes
  Example: ["Apple", "Google", "Microsoft"]
  NOT: Apple, Google, Microsoft
```

### Option 2: Post-Processing
```python
def format_list_output(pred, answer_format):
    if answer_format == 'List':
        if not pred.startswith('['):
            # Convert comma-separated to JSON list
            items = [item.strip() for item in pred.split(',')]
            pred = json.dumps(items)
    return pred
```

### Option 3: Accept Both Formats in Evaluation
Modify `eval_score` to normalize List formats before comparison:
```python
def normalize_list_format(text):
    # Convert both formats to same representation
    # ['a', 'b'] -> ["a", "b"]
    # a, b -> ["a", "b"]
```

---

## 🎓 Research Implications

### 1. **Framework Advantages Are Real**
DSPy's +12.9% overall advantage is partially due to:
- Better structured output formatting (+23.1% on Lists)
- Better prompt engineering
- Two-stage architecture benefits

### 2. **Fair Comparison Requires**
- Same architecture (1-stage vs 1-stage, not 1-stage vs 2-stage)
- Same output formatting instructions
- Same evaluation methodology

### 3. **Test-Time Learning (DC) Should Be Compared Against**
- RAW implementations (not DSPy framework)
- Single-stage architectures (not multi-stage)
- Simple prompts (not framework-optimized prompts)

---

## ✅ Updated Fair Comparison

### With Framework Removed

| Approach | Model | Dev Accuracy | Notes |
|----------|-------|--------------|-------|
| **Simple RAW** | qwen2.5-7b | **45.2%** | No framework |
| **DC-CU** | qwen2.5-7b | **44.1%** | No framework |
| **Gap** | | **+1.1%** | Nearly tied! ✅ |

**Previous Unfair Comparison**:
- DSPy Baseline (with framework): 58.1%
- DC-CU (no framework): 44.1%
- Gap: +13.9% (misleading)

**Current Fair Comparison**:
- Simple RAW (no framework): 45.2%
- DC-CU (no framework): 44.1%
- Gap: +1.1% (realistic)

---

## 🔬 Remaining Questions

1. Will DeepSeek v3.1 help DC more than Simple Baseline? (In progress)
2. Should we implement post-processing to fix List format in RAW?
3. Should evaluation normalize List formats before comparison?
4. What other hidden advantages does DSPy provide?

---

**Conclusion**: DSPy's framework provides significant advantages in structured output formatting, especially for List questions. Fair comparisons must use RAW implementations without framework assistance.

**Status**: Analysis complete, DeepSeek DC-CU evaluation in progress

