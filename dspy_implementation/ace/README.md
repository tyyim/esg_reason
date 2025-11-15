# ACE Module for MMESGBench

Implementation of the ACE (Agentic Context Engineering) framework on MMESGBench using the existing RAG pipeline and DashScope/Qwen models.

- Paper: [Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models](https://arxiv.org/abs/2510.04618)
- Source (integrated): `ACE-open/ace/*`

## Setup

1) Ensure `ACE-open` is present at project root (already included here):
```
ACE-open/ace/
```

2) Provide DashScope API key:
```bash
export DASHSCOPE_API_KEY=...
```

3) Verify retrieval works (same as baseline/DC modules).

## Files
- `ace_llm.py` — DashScope-backed `LLMClient` compatible with `ACE-open`.
- `ace_module.py` — RAG + ACE online adapter (playbook evolves per question).
- `ace_evaluator.py` — Evaluator with checkpointing and MMESGBench scoring.

## Usage

### Quick dev run (10 questions)
```bash
python dspy_implementation/ace/ace_evaluator.py \
  --dataset dev \
  --model qwen2.5-7b-instruct \
  --max-questions 10
```

### Full dev set
```bash
python dspy_implementation/ace/ace_evaluator.py --dataset dev
```

### Test set (cold)
```bash
python dspy_implementation/ace/ace_evaluator.py --dataset test
```

Results are saved to `results/ace_experiments/` and logs under `logs/ace_evaluation/`.

### Use baseline contexts instead of retrieval
```bash
python dspy_implementation/ace/ace_evaluator.py \
  --dataset dev \
  --model qwen2.5-7b-instruct \
  --no-retrieval \
  --baseline-context-file "results/dev_set/baseline_dev_predictions_20251019_130401.json"
```

You can adjust checkpoint frequency (default 10):
```bash
python dspy_implementation/ace/ace_evaluator.py --dataset dev --checkpoint-interval 5
```

### Cold-start workflow: offline pretrain then evaluate

1) Offline pretrain on a split (dev/train) for N epochs to warm up the playbook, then evaluate:
```bash
python dspy_implementation/ace/ace_evaluator.py \
  --dataset test \
  --model qwen2.5-7b-instruct \
  --offline-pretrain \
  --offline-train-split dev \
  --offline-epochs 1 \
  --offline-max-questions 200 \
  --freeze-playbook
```

- `--offline-pretrain`: run OfflineAdapter over the chosen split to evolve playbook before evaluation
- `--offline-train-split {dev|train}`: which split to use for offline pretrain (falls back to dev if train is unavailable)
- `--offline-epochs N`: number of epochs for offline pretrain
- `--offline-max-questions K`: limit pretrain questions for faster runs
- `--freeze-playbook`: during evaluation, disable reflection/curation (no playbook updates)

### Load a previously pretrained playbook (skip pretrain)
```bash
python dspy_implementation/ace/ace_evaluator.py \
  --dataset test \
  --model qwen2.5-7b-instruct \
  --load-playbook "results/ace_experiments/ace_pretrained_playbook_dev_20251105_174728.json" \
  --freeze-playbook
```
This loads the given JSON into the evaluator and evaluates immediately. If both `--load-playbook` and `--offline-pretrain` are provided, the loader takes precedence and pretrain is skipped.

If you want to continue online adaptation during evaluation (starting from the offline-pretrained playbook), omit `--freeze-playbook`.

## Notes
- This integration uses ACE online adaptation (`OnlineAdapter`) with a feedback signal derived from MMESGBench ANLS (as environment feedback) and incremental playbook updates via the ACE curator.
- Prompts default to `ACE-open/ace/prompts.py` templates; you can further specialize for ESG if needed.
- Offline pretraining will save a file like `results/ace_experiments/ace_pretrained_playbook_<split>_<timestamp>.json`.


