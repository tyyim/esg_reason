# How to Run ACE Evaluation

## Prerequisites

Make sure the environment variables are set (in `.env`):
```bash
API_KEY=your_api_key
API_BASE=your_base_url
```

## Run Examples

### Dev dataset
```bash
python dspy_implementation/ace/ace_evaluator.py \
  --dataset dev \
  --model deepseek-v3.1
```

### Test dataset
```bash
python dspy_implementation/ace/ace_evaluator.py \
  --dataset test \
  --model deepseek-v3.1
```

## Output locations

- Results: `results/ace_experiments/`
- Logs: `logs/ace_evaluation/`

