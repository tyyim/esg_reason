# Dynamic Cheatsheet Integration for ESG Reasoning

This module integrates Dynamic Cheatsheet's core methods into the ESG Q&A evaluation framework, supporting two prompt types and two approaches.

## Features

- **Cumulative Approach**: Incrementally updates cheatsheet after each question
- **Retrieval Synthesis Approach**: Retrieves similar examples and synthesizes cheatsheet
- **Dual Prompt System**:
  - `original`: Uses DC original prompts (from `dc_repo/prompts`)
  - `custom`: Uses ESG-specific custom prompts (from `dc_prompts.py`)
- **Code Execution Support**: Optional Python code execution functionality
- **Embeddings Support**: Retrieval synthesis approach supports similarity-based retrieval

## Prerequisites

1. **Environment Variables**: Set in `.env` file at project root:
   ```bash
   API_KEY=your_api_key_here
   API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1  # Optional, has default value
   ```

2. **Dependencies**:
   - OpenAI-compatible API client
   - PostgreSQL retriever (via `DSPyPostgresRetriever`)
   - `langchain_community` (for embeddings)

## How to Run

### Command Line Usage

#### Basic Usage

```bash
# Use custom prompts and cumulative approach (default configuration)
python dspy_implementation.dc.evaluate_dc.py \
    --dataset dev \
    --model deepseek-v3.1

# Use original prompts and retrieval synthesis approach
python dspy_implementation.dc.evaluate_dc.py \
    --dataset dev \
    --model deepseek-v3.1 \
    --prompt-type original \
    --approach retrieval_synthesis \
    --retrieve-top-k 3

# Limit number of questions (for testing)
python dspy_implementation.dc.evaluate_dc.py \
    --dataset dev \
    --model deepseek-v3.1 \
    --max-questions 10

# Disable code execution (enabled by default)
python dspy_implementation.dc.evaluate_dc.py \
    --dataset dev \
    --model deepseek-v3.1 \
    --no-code-execution

# Multiple rounds for cumulative approach
python dspy_implementation.dc.evaluate_dc.py \
    --dataset dev \
    --model deepseek-v3.1 \
    --approach cumulative \
    --max-rounds 2
```

#### Complete Parameter Reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--dataset` | str | 'dev' | Dataset: 'dev' or 'test' |
| `--model` | str | 'deepseek-v3.1' | Model name |
| `--prompt-type` | str | 'custom' | Prompt type: 'original' or 'custom' |
| `--approach` | str | 'cumulative' | DC approach: 'cumulative' or 'retrieval_synthesis' |
| `--max-questions` | int | None | Limit number of questions (None means all) |
| `--max-rounds` | int | 1 | Maximum rounds for cumulative approach |
| `--retrieve-top-k` | int | 3 | Number of similar examples to retrieve for retrieval synthesis |
| `--no-code-execution` | flag | False | Disable Python code execution (enabled by default) |

### Python API Usage

```python
from dspy_implementation.dc import evaluate_dc

# Use custom prompts and cumulative approach
results = evaluate_dc(
    dataset_name='dev',
    model_name='deepseek-v3.1',
    prompt_type='custom',
    approach='cumulative',
    max_questions=10,
    max_num_rounds=1,
    allow_code_execution=True  # Default is True
)

# Use original prompts and retrieval synthesis approach
results = evaluate_dc(
    dataset_name='dev',
    model_name='deepseek-v3.1',
    prompt_type='original',
    approach='retrieval_synthesis',
    max_questions=10,
    retrieve_top_k=3,
    allow_code_execution=True
)

# Access results
print(f"Accuracy: {results['accuracy']:.1%}")
print(f"Correct: {results['correct']}/{results['total']}")
print(f"Final cheatsheet: {results['final_cheatsheet']}")
```

## Output Results

### Save Location

Results are saved to:
```
results/{model_name}_dc/{prompt_type}_{approach}_{dataset_name}_{timestamp}.json
```

### Output Structure

```json
{
  "model": "deepseek-v3.1",
  "implementation": "dynamic_cheatsheet",
  "prompt_type": "custom",
  "approach": "cumulative",
  "dataset": "dev",
  "total": 93,
  "completed": 93,
  "correct": 45,
  "accuracy": 0.4839,
  "format_breakdown": {
    "Int": {"correct": 10, "total": 20},
    "Float": {"correct": 15, "total": 30}
  },
  "final_cheatsheet": "...",
  "predictions": [
    {
      "question": "...",
      "doc_id": "...",
      "answer_format": "Int",
      "context": "...",
      "ground_truth": "...",
      "predicted_answer": "...",
      "analysis": "...",
      "correct": true,
      "score": 1.0,
      "cheatsheet_before": "...",
      "cheatsheet_after": "..."
    }
  ],
  "timestamp": "20251115_010930"
}
```

## Code Execution Feature

Code execution is **enabled by default**. When enabled, the model can include Python code blocks in its output, and code marked with `EXECUTE CODE!` will be automatically executed.

### Disable Code Execution

```bash
# Command line
python dspy_implementation.dc.evaluate_dc.py --no-code-execution

# Python API
evaluate_dc(allow_code_execution=False, ...)
```

### Code Execution Flow

1. Model output contains ````python ... ``` EXECUTE CODE!` format
2. System extracts and executes Python code
3. Execution results are added to conversation history
4. Model can continue generation based on execution results (supports multi-round recursion)

## Prompt Type Description

### `prompt_type='custom'` (Default)

- **Generator**: Uses ESG-specific prompts (`dc_prompts.py`)
- **Curator**: Uses ESG-specific prompts (`dc_prompts.py`)
- **Output Format**: JSON `{"reasoning": "...", "final_answer": "..."}`

### `prompt_type='original'`

- **Generator**: Uses ESG-specific prompts (`dc_prompts.py`)
- **Curator**: Uses DC original prompts (`dc_repo/prompts/`)
- **Output Format**: `<answer>...</answer>` or `FINAL ANSWER: ...`

## Approach Description

### Cumulative Approach

- Updates cheatsheet after each question
- Cheatsheet accumulates throughout the evaluation process
- Suitable for sequential problem-solving scenarios

### Retrieval Synthesis Approach

- Uses embeddings to retrieve similar historical question-answer pairs
- Synthesizes customized cheatsheet for each question
- Requires embeddings support (automatically uses DashScope text-embedding-v4)

## Notes

1. **Environment Variables**: Ensure `API_KEY` is set in `.env` file
2. **Database Connection**: Ensure PostgreSQL database is accessible and contains required embeddings
3. **Code Execution**: Code execution is enabled by default, use `--no-code-execution` to disable if needed
4. **Result Saving**: Results are automatically saved every 5 questions to prevent data loss

## File Structure

```
dc/
├── __init__.py              # Module exports
├── evaluate_dc.py           # Core evaluation script
├── prompt_manager.py        # Prompt management module
├── dc_prompts.py            # Custom ESG prompts
└── README.md                # This document

Note: Utility functions (answer extraction, cheatsheet extraction, code execution) 
are directly imported from dc_repo/dynamic_cheatsheet/utils/
```
