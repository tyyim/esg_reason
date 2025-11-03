# Dynamic Cheatsheet Module for MMESGBench

Implementation of Dynamic Cheatsheet test-time learning for ESG question answering.

## Setup

### Step 1: Clone Dynamic Cheatsheet Repository

```bash
cd /Users/victoryim/Local_Git/CC
git clone https://github.com/suzgunmirac/dynamic-cheatsheet.git dc_repo
```

### Step 2: Install Dependencies

```bash
pip install -r dc_repo/requirements.txt
```

### Step 3: Verify Setup

```bash
python -c "
import sys
sys.path.insert(0, 'dc_repo')
from dynamic_cheatsheet.language_model import LanguageModel
print('✅ DC setup successful!')
"
```

## Architecture

DC is a **separate approach** from DSPy. It does NOT use the DSPy framework.

```
Question -> PostgreSQL Retrieval -> DC Generator (with cheatsheet) -> Answer
                                         |
                                         v
                                    DC Curator (updates cheatsheet for next Q)
```

**Key Difference**:
- **DSPy**: Learns BEFORE test (train/dev) -> static prompts
- **DC**: Learns DURING test -> evolving cheatsheet

## Usage

### Quick Test (10 dev questions)

```bash
python dspy_implementation/dc_module/dc_evaluator.py \
  --dataset dev \
  --max-questions 10 \
  --variant cumulative
```

Expected runtime: ~2-3 minutes

### Dev Set Evaluation (93 questions)

```bash
python dspy_implementation/dc_module/dc_evaluator.py \
  --dataset dev \
  --variant cumulative
```

Expected runtime: ~15-20 minutes

### Test Set - Cold Start (654 questions)

**Fair comparison to DSPy**

```bash
python dspy_implementation/dc_module/dc_evaluator.py \
  --dataset test \
  --variant cumulative
```

Expected runtime: ~3-4 hours  
Expected cost: ~$0.80  
Expected accuracy: 48-50% (similar to baseline 47.4%)

### Test Set - Warm Start (933 questions)

**Test-time learning advantage (NOT fair to compare with DSPy)**

```bash
python dspy_implementation/dc_module/dc_evaluator.py \
  --dataset test \
  --variant cumulative \
  --warmup
```

Expected runtime: ~5-6 hours  
Expected cost: ~$1.12  
Expected accuracy: 52-56% (learns from train+dev+test)

## Module Files

- `dc_wrapper.py` - Wrapper around DC's LanguageModel
- `dc_prompts.py` - ESG-specific generator & curator prompts
- `dc_rag_module.py` - DC + RAG integration
- `dc_evaluator.py` - Evaluation with checkpointing & logging

## Results Location

Results are saved to: `results/dc_experiments/`

Format: `dc_{variant}_{cold|warm}_{dataset}_{timestamp}.json`

## Checkpointing

Checkpoints are automatically saved every 10 questions to:
- `results/dc_experiments/dc_{variant}_{cold|warm}_{dataset}_checkpoint.json`

To resume a stopped evaluation, simply run the same command again.

## Logging

Logs are saved to: `logs/dc_evaluation/dc_eval_{timestamp}.log`

Both console and file logging are enabled.

## Comparison Guidelines

### Fair Comparisons

✅ **DC-Cold vs DSPy Baseline** - Both use no training data  
✅ **DC-Cold vs DSPy GEPA/MIPROv2** - Both optimize on train/dev only

### Unfair Comparisons

❌ **DC-Warm vs ANY DSPy** - DC learns FROM test set  

DC-Warm shows the upper bound of test-time learning but should be clearly labeled as unfair.

## Troubleshooting

### Import Error: dynamic_cheatsheet not found

```bash
# Clone DC repo if not already done
git clone https://github.com/suzgunmirac/dynamic-cheatsheet.git dc_repo

# Verify path
ls dc_repo/dynamic_cheatsheet/
```

### Retrieval Errors

```bash
# Check PostgreSQL connection
echo $PG_URL

# Test retrieval
python -c "
from dspy_implementation.dspy_postgres_retriever import DSPyPostgresRetriever
r = DSPyPostgresRetriever()
print('✅ Retrieval works')
"
```

### API Errors

```bash
# Check DashScope API key
echo $DASHSCOPE_API_KEY
```

## References

- **DC Paper**: https://arxiv.org/abs/2504.07952
- **DC GitHub**: https://github.com/suzgunmirac/dynamic-cheatsheet
- **MMESGBench**: https://github.com/microsoft/Multimodal-ESG-Benchmark

