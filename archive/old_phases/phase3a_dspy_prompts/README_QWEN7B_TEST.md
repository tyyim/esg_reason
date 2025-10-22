# Qwen 2.5 7B Model Test - Phase 3a

## Hypothesis
The current Qwen Max model may be too strong, limiting DSPy's optimization effectiveness. Testing with a smaller model (qwen2.5-7b-instruct) to see if:
1. **Lower baseline accuracy** provides more room for improvement
2. **Optimization gains** are more significant with weaker model
3. **Cost-performance tradeoff** is better for this task

## Setup Complete ✅

### Modified Files
1. **dspy_implementation/dspy_setup.py**
   - Added `model_name` parameter to `setup_dspy_qwen()`
   - Supports any Qwen model: qwen-max, qwen2.5-7b-instruct, qwen2.5-14b-instruct, etc.

2. **dspy_implementation/enhanced_miprov2_optimization.py**
   - Added `--model` command-line argument
   - Reads model from environment variable `QWEN_MODEL`

3. **phase3a_dspy_prompts/config_phase3a_qwen7b.yaml**
   - Variant config for qwen2.5-7b testing
   - Separate experiment name: "Phase3a_Qwen7B_Test"
   - Separate output dirs to avoid conflicts

### API Test
✅ Qwen 2.5 7B API connection verified successfully

## How to Run

### Quick Test (10 questions)
```bash
# Test with first 10 dev questions to verify everything works
python dspy_implementation/evaluate_baseline.py \
  --use-dev-set \
  --max-questions 10 \
  --model qwen2.5-7b-instruct
```

### Full Baseline Evaluation (Dev Set - 93 questions)
```bash
# Get baseline accuracy before optimization
python dspy_implementation/evaluate_baseline.py \
  --use-dev-set \
  --model qwen2.5-7b-instruct
```

Expected: ~30-40% (lower than qwen-max's 45.1%)

### Run Optimization (Light Mode, ~20-30 min)
```bash
python dspy_implementation/enhanced_miprov2_optimization.py \
  --model qwen2.5-7b-instruct \
  --num-candidates 10
```

### Monitor with MLFlow
```bash
# In separate terminal
mlflow ui
# Open http://localhost:5000
# Look for experiment: "Phase3a_Qwen7B_Test"
```

## Expected Results

### Qwen Max (ACTUAL results from phase3a_optimization_run.log)
- Baseline: 51.6% end-to-end accuracy
- After optimization: 48.4% (**-3.2%**) ❌
- **NEGATIVE gain** - optimization made it worse!
- **Root cause**: Model too strong → overfitting to 186 train examples

### Qwen 2.5 7B (Hypothesis - NOW MORE IMPORTANT!)
- Baseline: ~35-45% (weaker starting point)
- After optimization: ~40-50% (+5-10%)
- **Should avoid overfitting** - weaker model needs optimization
- **May show POSITIVE gains** unlike qwen-max

## Output Files
- `phase3a_dspy_prompts/results_qwen7b/` - Evaluation results
- `phase3a_dspy_prompts/checkpoints_qwen7b/` - Training checkpoints
- `phase3a_dspy_prompts/optimized_module_qwen7b.json` - Optimized DSPy module
- `baseline_rag_results_*.json` - Timestamped result files

## Cost Estimates
- **Qwen Max**: ~$0.02/1K tokens (input), ~$0.06/1K tokens (output)
- **Qwen 2.5 7B**: ~$0.0002/1K tokens (input), ~$0.0006/1K tokens (output)
- **100x cheaper** for 7B model!

For 93-question dev set:
- Qwen Max: ~$5-10
- Qwen 2.5 7B: ~$0.05-0.10

## Next Steps After Results

1. **Compare accuracies**: qwen-max vs qwen2.5-7b
2. **Analyze optimization delta**: Did 7B improve more?
3. **Cost-benefit analysis**: Is 7B good enough at 1/100th the cost?
4. **Document in Research Plan**: Update Notion with findings
5. **Consider other models**: qwen2.5-14b-instruct as middle ground?

## Files Created
- `test_qwen7b_model.sh` - API connection test
- `phase3a_dspy_prompts/config_phase3a_qwen7b.yaml` - Config variant
- `phase3a_dspy_prompts/README_QWEN7B_TEST.md` - This file

## Rollback if Needed
All changes are backwards compatible:
- `setup_dspy_qwen()` defaults to 'qwen-max' if no parameter given
- `enhanced_miprov2_optimization.py` defaults to 'qwen-max' if --model not specified
- Original config `config_phase3a.yaml` unchanged

Just don't pass `--model` parameter to use qwen-max.
