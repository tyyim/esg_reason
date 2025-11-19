# How to Run the Simple Baseline

Quick reference for `dspy_implementation/baseline/evaluate_baseline.py`.

## 1. Prerequisites

Set the API credentials in `.env` (or your shell):
```bash
API_KEY=your_api_key
API_BASE=your_base_url
```

## 2. Run Examples

### Dev split (default 100% of dev questions)
```bash
python dspy_implementation/baseline/evaluate_baseline.py \
  --dataset dev \
  --model deepseek-v3.1
```

### Test split
```bash
python dspy_implementation/baseline/evaluate_baseline.py \
  --dataset test \
  --model deepseek-v3.1
```

Optional flags:
- `--max-questions 50` — run only the first 50 questions (useful for smoke tests).

## 3. Outputs

- Results JSON: `results/<model>_baseline/simple_baseline_<dataset>_<timestamp>.json`
- Progress + status logs: printed to stdout
