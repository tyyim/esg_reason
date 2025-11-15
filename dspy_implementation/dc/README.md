# Dynamic Cheatsheet Integration for ESG Reasoning

This module integrates Dynamic Cheatsheet's core methods into the baseline evaluation framework, supporting two prompt types and two approaches for ESG (Environmental, Social, Governance) question answering.

## Features

### 1. Baseline-Compatible Evaluation
- **Dataset Loading**: Uses the same `MMESGBenchDataset` as baseline
- **Retrieval**: Uses the same `DSPyPostgresRetriever` for document retrieval
- **Answer Evaluation**: Uses the same `eval_score` function for evaluation
- **Storage Format**: Maintains the same JSON output format as baseline

### 2. Dynamic Cheatsheet Core Methods
- **Cumulative Approach**: Updates cheatsheet incrementally after each question
- **Retrieval Synthesis Approach**: Retrieves similar examples and synthesizes cheatsheet

### 3. Dual Prompt System
- **`original`**: Uses Dynamic Cheatsheet's original prompts (from `dc_repo/prompts`)
- **`custom`**: Uses ESG-specific custom prompts (from `dc_module/dc_prompts.py`)

## File Structure

```
dc/
├── __init__.py              # Module exports
├── evaluate_dc.py           # Core evaluation script
├── prompt_manager.py        # Prompt management module
├── dc_prompts.py            # Custom ESG prompts
├── utils.py                 # Utility functions (answer extraction, cheatsheet extraction, code execution)
└── README.md                # This file
```

## Installation

Ensure you have the required dependencies installed. The module uses:
- OpenAI-compatible API client
- PostgreSQL retriever (via `DSPyPostgresRetriever`)
- Standard Python libraries (json, pathlib, datetime, etc.)

## Usage

### Command Line Interface

```bash
# Custom prompts with cumulative approach
python -m dspy_implementation.dc.evaluate_dc \
    --dataset dev \
    --model deepseek-v3.1 \
    --prompt-type custom \
    --approach cumulative \
    --max-questions 10

# Original prompts with retrieval synthesis approach
python -m dspy_implementation.dc.evaluate_dc \
    --dataset dev \
    --model deepseek-v3.1 \
    --prompt-type original \
    --approach retrieval_synthesis \
    --retrieve-top-k 3

# Disable code execution
python -m dspy_implementation.dc.evaluate_dc \
    --dataset dev \
    --model deepseek-v3.1 \
    --prompt-type custom \
    --approach cumulative \
    --no-code-execution
```

### Python API

```python
from dspy_implementation.dc import evaluate_dc

# Evaluate with custom prompts and cumulative approach
results = evaluate_dc(
    dataset_name='dev',
    model_name='deepseek-v3.1',
    prompt_type='custom',
    approach='cumulative',
    max_questions=10,
    max_num_rounds=1,
    allow_code_execution=True
)

# Evaluate with original prompts and retrieval synthesis approach
results = evaluate_dc(
    dataset_name='dev',
    model_name='deepseek-v3.1',
    prompt_type='original',
    approach='retrieval_synthesis',
    max_questions=10,
    retrieve_top_k=3,
    allow_code_execution=True
)
```

## Parameters

### `evaluate_dc()` Function Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataset_name` | str | 'dev' | Dataset to evaluate ('dev' or 'test') |
| `model_name` | str | 'deepseek-v3.1' | Model name for API calls |
| `prompt_type` | str | 'custom' | Prompt type: 'original' or 'custom' |
| `approach` | str | 'cumulative' | DC approach: 'cumulative' or 'retrieval_synthesis' |
| `max_questions` | int | None | Maximum number of questions to evaluate (None for all) |
| `max_num_rounds` | int | 1 | Maximum rounds for cumulative approach |
| `retrieve_top_k` | int | 3 | Number of similar examples to retrieve for retrieval synthesis |
| `allow_code_execution` | bool | True | Whether to allow Python code execution |

### Prompt Type Behavior

**`prompt_type='custom'`**:
- **Generator**: Uses custom ESG prompts from `dc_prompts.py`
- **Curator**: Uses custom ESG prompts from `dc_prompts.py`

**`prompt_type='original'`**:
- **Generator**: Uses custom ESG prompts from `dc_prompts.py`
- **Curator**: Uses original DC prompts from `dc_repo/prompts/`

## Prompt Format Details

### Original Prompts (from `dc_repo/prompts/`)

**Generator** (`generator_prompt.txt`):
- Placeholders: `[[QUESTION]]`, `[[CHEATSHEET]]`
- Output format: `<answer>...</answer>` or `FINAL ANSWER: ...`

**Curator - Cumulative** (`curator_prompt_for_dc_cumulative.txt`):
- Placeholders: `[[PREVIOUS_CHEATSHEET]]`, `[[QUESTION]]`, `[[MODEL_ANSWER]]`
- Receives full generator output including reasoning steps

**Curator - Retrieval Synthesis** (`curator_prompt_for_dc_retrieval_synthesis.txt`):
- Placeholders: `[[PREVIOUS_CHEATSHEET]]`, `[[PREVIOUS_INPUT_OUTPUT_PAIRS]]`, `[[NEXT_INPUT]]`
- Synthesizes cheatsheet from retrieved similar examples

### Custom Prompts (from `dc_prompts.py`)

**Generator** (`GENERATOR_PROMPT`):
- Placeholders: `{context}`, `{cheatsheet}`, `{question}`, `{answer_format}`
- Output format: JSON with `{"reasoning": "...", "final_answer": "..."}`

**Curator - Cumulative** (`CURATOR_PROMPT`):
- Placeholders: `{current_cheatsheet}`, `{question}`, `{answer_format}`, `{answer}`, `{context}`
- Receives extracted answer and context separately

**Curator - Retrieval Synthesis** (`CURATOR_PROMPT_RS`):
- Placeholders: `{previous_cheatsheet}`, `{retrieved_qa_pairs}`, `{next_input}`
- Synthesizes cheatsheet from retrieved similar examples

## Output Format

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
    "Float": {"correct": 15, "total": 30},
    ...
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
    },
    ...
  ],
  "timestamp": "20251115_010930"
}
```

## Key Features

### Cheatsheet Evolution
- Each question's cheatsheet state (before and after) is saved
- Final cheatsheet state is preserved in the output
- Cheatsheet evolves incrementally with each question

### Answer Extraction
- **Original prompts**: Extracts from `<answer>` tags or `FINAL ANSWER:` sections
- **Custom prompts**: Parses JSON and extracts `final_answer` field
- Handles both direct JSON and markdown code block formats

### Code Execution
- Supports Python code execution when enabled
- Automatically executes code blocks marked with "EXECUTE CODE!"
- Captures execution output and includes it in the response

## Important Notes

1. **Retrieval Synthesis**: Currently requires embeddings for similarity search. If embeddings are unavailable, a simple retrieval approach is used.

2. **Code Execution**: Enabled by default. Models can output Python code blocks that will be automatically executed if marked with the execution flag.

3. **Cheatsheet Preservation**: The curator is instructed to preserve all relevant previous content when updating the cheatsheet. Each update should explicitly copy relevant information from the previous cheatsheet.

4. **Context Retrieval**: Uses the same retrieval mechanism as baseline (top_k=5 documents from PostgreSQL vector store).

## Comparison with Baseline

| Feature | Baseline | DC Integration |
|---------|----------|----------------|
| Dataset Loading | ✅ Same | ✅ Same |
| Retrieval Method | ✅ Same | ✅ Same |
| Evaluation Method | ✅ Same | ✅ Same |
| Storage Format | ✅ Same | ✅ Same |
| Cheatsheet | ❌ None | ✅ Supported |
| Prompt Types | Single | Two (original/custom) |
| Approaches | Single | Two (cumulative/retrieval_synthesis) |
| Test-time Learning | ❌ None | ✅ Incremental cheatsheet updates |

## Troubleshooting

### Common Issues

1. **Missing Prompts**: Ensure `dc_repo/prompts/` directory exists with all required prompt files.

2. **API Key**: Set `DASHSCOPE_API_KEY` in your `.env` file or environment variables.

3. **Database Connection**: Ensure PostgreSQL database is accessible and contains the required embeddings.

4. **Code Execution Errors**: If code execution fails, check Python 3 installation and required packages.

## License

See the main project license file.
