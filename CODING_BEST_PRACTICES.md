# Coding Best Practices for ESG Reasoning Project

## 🎯 Core Principles

All evaluation and optimization scripts MUST follow these patterns to ensure robustness, reproducibility, and efficiency.

## 1. ✅ Checkpoint/Resume Mechanism

**Always implement checkpoint/resume for long-running evaluations (>10 minutes)**

### Pattern from `colbert_full_dataset_evaluation.py`:

```python
def _save_checkpoint(self, results: List[Result], completed_idx: int, checkpoint_file: str):
    """Save evaluation checkpoint"""
    try:
        checkpoint_data = {
            "results": [asdict(r) for r in results],
            "completed_questions": completed_idx,
            "timestamp": datetime.now().isoformat()
        }
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
        logger.info(f"💾 Checkpoint saved: {completed_idx} questions completed")
    except Exception as e:
        logger.warning(f"Failed to save checkpoint: {e}")

def _load_checkpoint(self, checkpoint_file: str) -> Tuple[List[Result], int]:
    """Load evaluation checkpoint"""
    if not os.path.exists(checkpoint_file):
        return [], 0

    try:
        with open(checkpoint_file, 'r') as f:
            checkpoint_data = json.load(f)

        results = [Result(**r) for r in checkpoint_data.get("results", [])]
        completed_idx = checkpoint_data.get("completed_questions", 0)
        logger.info(f"📂 Loaded checkpoint: {completed_idx} questions completed")
        return results, completed_idx
    except Exception as e:
        logger.warning(f"Failed to load checkpoint: {e}")
        return [], 0

def run_evaluation(self, checkpoint_file: str = "checkpoint.json"):
    # Load checkpoint
    results, start_idx = self._load_checkpoint(checkpoint_file)

    # Continue from where we left off
    for i in range(start_idx, len(dataset)):
        result = self.evaluate_question(dataset[i])
        results.append(result)

        # Save checkpoint every N questions
        if (i + 1) % 10 == 0:
            self._save_checkpoint(results, i + 1, checkpoint_file)
```

**Why**:
- Prevents losing work from crashes/interruptions
- Allows resuming long evaluations
- Critical for 933-question full dataset evaluations

## 2. 📊 Proper Logging

**Use structured logging with levels and context**

### Pattern:

```python
import logging

# Setup at module level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/{script_name}_{timestamp}.log'),
        logging.StreamHandler()  # Also print to console
    ]
)
logger = logging.getLogger(__name__)

# Usage throughout code
logger.info(f"📊 Starting evaluation: {len(dataset)} questions")
logger.debug(f"Retrieved chunks: {len(chunks)}")
logger.warning(f"⚠️  API rate limit hit, retrying...")
logger.error(f"❌ Failed to process question {q_id}: {error}")
```

**Logging Guidelines**:
- ✅ `INFO`: Progress updates, key results
- ✅ `DEBUG`: Detailed execution info
- ✅ `WARNING`: Recoverable issues (retries, missing data)
- ✅ `ERROR`: Failures that prevent completion
- ✅ Use emojis for visual scanning: 📊 🎯 ⚠️ ❌ ✅ 💾 📂

## 3. 🔄 Retry Logic with Exponential Backoff

**Always implement retry logic for API calls**

### Pattern:

```python
def call_llm_with_retry(self, prompt: str, max_retries: int = 3) -> str:
    """Call LLM with exponential backoff retry"""
    for attempt in range(max_retries):
        try:
            response = self.client.chat.completions.create(
                model="qwen-max",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                timeout=60.0
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                logger.error(f"Failed after {max_retries} attempts: {e}")
                raise
            time.sleep(2 ** attempt)  # 1s, 2s, 4s backoff
```

**Why**:
- Handles transient API failures
- Prevents complete evaluation failure from single errors
- Exponential backoff reduces server load

## 4. 📈 MLFlow Experiment Tracking (Phase 2+)

**All Phase 2+ evaluations MUST log to MLFlow**

### Pattern from `mlflow_tracking.py`:

```python
from mlflow_tracking import DSPyMLFlowTracker

# Initialize tracker
tracker = DSPyMLFlowTracker(
    experiment_name="Phase2_Qwen_Baseline"
)

# Start run
tracker.start_run(
    run_name=f"baseline_{timestamp}",
    tags={
        "phase": "2",
        "method": "qwen_pgvector",
        "optimizer": "none"
    }
)

# Log configuration
tracker.log_params({
    "embedding_model": "text-embedding-v4",
    "top_k": 5,
    "llm_model": "qwen-max",
    "temperature": 0.0,
    "dataset_size": 933
})

# Log baseline metrics
tracker.log_baseline(
    metrics={
        "retrieval_accuracy": 0.37,
        "answer_accuracy": 0.42,
        "e2e_accuracy": 0.30
    },
    config=config
)

# For optimization (Phase 3+): log each trial
for trial_num in range(num_trials):
    tracker.log_optimization_step(
        step=trial_num,
        metrics={
            "trial_accuracy": accuracy,
            "trial_retrieval": retrieval
        }
    )

# Log final results
tracker.log_final_results(
    metrics={
        "final_retrieval": 0.45,
        "final_answer": 0.47,
        "final_e2e": 0.38
    },
    artifacts={
        "predictions": "predictions.json",
        "optimized_module": "optimized_module.json"
    }
)

# End run
tracker.end_run()
```

**Required Metrics**:
- **Retrieval Accuracy**: % questions with all evidence pages in top-k (RESEARCH metric)
- **Answer Accuracy**: % questions with correct answer using ANLS 0.5 (PRIMARY metric)
- **E2E Accuracy**: Both retrieval AND answer correct (RESEARCH metric)

**MLFlow Best Practices**:
- Tag runs with phase, method, optimizer
- Log ALL hyperparameters as params
- Log metrics at each optimization step
- Save artifacts (predictions, modules, configs)
- Use descriptive run names with timestamps

## 5. ⚡ Parallelism (When Applicable)

**Use parallel processing for independent operations**

### Pattern:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def process_questions_parallel(questions: List[Dict], max_workers: int = 4):
    """Process questions in parallel"""
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_question = {
            executor.submit(self.evaluate_question, q): q
            for q in questions
        }

        # Collect results as they complete
        for future in as_completed(future_to_question):
            question = future_to_question[future]
            try:
                result = future.result()
                results.append(result)
                logger.info(f"✅ Completed: {question['question_id']}")
            except Exception as e:
                logger.error(f"❌ Failed: {question['question_id']}: {e}")

    return results
```

**When to Use**:
- ✅ Document indexing (multiple PDFs)
- ✅ Batch embedding generation
- ✅ Independent question evaluations (if stateless)
- ❌ Sequential API calls with rate limits
- ❌ Optimization steps (DSPy handles this internally)

**Note**: For API-heavy workloads, use ThreadPoolExecutor. For CPU-heavy workloads, use ProcessPoolExecutor.

## 6. 📁 Structured Output

**Save results in consistent JSON format**

### Pattern:

```python
# Save detailed results
results_data = {
    "metadata": {
        "timestamp": datetime.now().isoformat(),
        "phase": "2",
        "method": "qwen_pgvector",
        "dataset_size": 933,
        "config": config
    },
    "summary": {
        "retrieval_accuracy": 0.37,
        "answer_accuracy": 0.42,
        "e2e_accuracy": 0.30,
        "total_questions": 933,
        "correct_answers": 392
    },
    "predictions": [
        {
            "question_id": 1,
            "question": "...",
            "predicted_answer": "...",
            "ground_truth": "...",
            "is_correct": True,
            "retrieval_successful": True,
            "retrieved_pages": [61, 62],
            "evidence_pages": [61],
            "processing_time": 3.2
        },
        # ...
    ]
}

# Save with timestamp
output_file = f"phase2_qwen_pgvector/results/baseline_{timestamp}.json"
with open(output_file, 'w') as f:
    json.dump(results_data, f, indent=2)

logger.info(f"💾 Results saved to: {output_file}")
```

**Required Fields**:
- `metadata`: Phase, method, timestamp, config
- `summary`: All three accuracy metrics
- `predictions`: Per-question results with retrieval info

## 7. 🧪 Progress Tracking with TQDM

**Use tqdm for long-running loops**

### Pattern:

```python
from tqdm import tqdm

for question in tqdm(dataset, desc="Evaluating questions"):
    result = self.evaluate(question)
    results.append(result)

    # Update progress bar with metrics
    if len(results) % 10 == 0:
        accuracy = sum(r.is_correct for r in results) / len(results)
        tqdm.write(f"Current accuracy: {accuracy:.1%}")
```

**Why**: Provides visual feedback and time estimates for long evaluations.

## 8. 🔍 Unified Evaluation Logic

**Always use MMESGBench's exact eval_score() function**

### Pattern:

```python
import sys
sys.path.append('MMESGBench/src/eval')
from eval_score import eval_score as mmesgbench_eval_score

def evaluate_answer(self, predicted: str, ground_truth: str, answer_format: str) -> bool:
    """Use MMESGBench's exact evaluation logic"""
    score = mmesgbench_eval_score(
        gt=ground_truth,
        pred=predicted,
        answer_type=answer_format
    )
    # Their logic: score >= 0.5 counts as correct (ANLS 0.5 threshold)
    return score >= 0.5
```

**Why**: Ensures exact replication of MMESGBench evaluation methodology.

## 9. 📋 Configuration Files (Phase 3+)

**Use YAML configs for reproducibility**

### Pattern:

```yaml
# phase3a_dspy_prompts/config.yaml
phase: 3a
method: dspy_prompt_optimization

optimization:
  query_optimization: false
  optimizer: MIPROv2
  num_trials: 10

retrieval:
  method: semantic_search
  top_k: 5
  embedding_model: text-embedding-v4

evaluation:
  metrics:
    - retrieval_accuracy
    - answer_accuracy
    - e2e_accuracy
```

**Load in code**:

```python
import yaml

with open("phase3a_dspy_prompts/config.yaml") as f:
    config = yaml.safe_load(f)
```

## 10. 🚨 Error Handling

**Graceful degradation, not silent failures**

### Pattern:

```python
try:
    result = self.evaluate_question(question)
except Exception as e:
    logger.error(f"❌ Failed to evaluate Q{question['id']}: {e}")
    # Create error result (don't skip)
    result = {
        "question_id": question['id'],
        "error": str(e),
        "is_correct": False,
        "predicted_answer": "ERROR"
    }
finally:
    results.append(result)
    # Always save checkpoint even after errors
    if (i + 1) % 10 == 0:
        self._save_checkpoint(results, i + 1, checkpoint_file)
```

**Why**: Track failures, don't hide them. Checkpoints ensure no data loss.

## ✅ Checklist for New Evaluation Scripts

Before committing new evaluation code, verify:

- [ ] Checkpoint/resume mechanism implemented
- [ ] Logging to both file and console
- [ ] Retry logic for API calls (3 attempts, exponential backoff)
- [ ] MLFlow tracking (Phase 2+)
- [ ] Progress bar with tqdm
- [ ] Structured JSON output with metadata
- [ ] Uses MMESGBench's exact eval_score()
- [ ] Error handling with graceful degradation
- [ ] Configuration externalized (YAML for Phase 3+)
- [ ] README with usage examples

## 📚 Reference Implementations

**Phase 1 (ColBERT)**:
- See: `archive_old_project/code_old/colbert_full_dataset_evaluation.py`
- Features: Checkpoint/resume, retry logic, structured output

**Phase 2 (Qwen Baseline)**:
- See: `archive_old_project/code_old/quick_dev_eval.py`
- Features: DSPy integration, MLFlow tracking

**Phase 3 (Optimization)**:
- See: `archive_old_project/code_old/dspy_implementation/enhanced_miprov2_optimization.py`
- Features: MLFlow trial tracking, YAML config, artifact logging

---

**Remember**: Good infrastructure code is the foundation for reliable research. Invest time upfront to save hours debugging later.
