# Dynamic Cheatsheet Implementation Guide

**Step-by-step instructions for implementing DC baseline**

---

## Quick Start (5 Minutes)

### Clone & Test DC Repository

```bash
cd /Users/victoryim/Local_Git/CC
git clone https://github.com/suzgunmirac/dynamic-cheatsheet.git dc_repo
pip install -r dc_repo/requirements.txt

# Test basic functionality
python -c "
from dc_repo.dynamic_cheatsheet.language_model import LanguageModel
model = LanguageModel(model_name='dashscope/qwen2.5-7b-instruct')
print('DC works!')
"
```

---

## Week 1: POC Implementation

### Day 1-2: Create Module Structure

```bash
# Create directory
mkdir -p dspy_implementation/dc_module
cd dspy_implementation/dc_module

# Create files
touch __init__.py
touch dc_wrapper.py
touch dc_rag_module.py
touch dc_prompts.py
```

### Day 3: Implement DC Wrapper

**File:** `dspy_implementation/dc_module/dc_wrapper.py`

```python
"""Wrapper around Dynamic Cheatsheet for Qwen models"""
import sys
sys.path.append('dc_repo')

from dc_repo.dynamic_cheatsheet.language_model import LanguageModel

class DCWrapper:
    """Wraps DC functionality for MMESGBench"""
    
    def __init__(self, model_name="qwen2.5-7b-instruct"):
        self.model = LanguageModel(
            model_name=f"dashscope/{model_name}"
        )
    
    def generate_with_cheatsheet(self, prompt, cheatsheet, 
                                 generator_template, curator_template):
        """
        Generate answer using DC approach
        
        Args:
            prompt: Input text (question + context + format)
            cheatsheet: Current cheatsheet string
            generator_template: Prompt template for generation
            curator_template: Prompt template for curation
        
        Returns:
            dict with 'final_answer' and 'final_cheatsheet'
        """
        result = self.model.advanced_generate(
            approach_name="DynamicCheatsheet_Cumulative",
            input_txt=prompt,
            cheatsheet=cheatsheet,
            generator_template=generator_template,
            cheatsheet_template=curator_template
        )
        return result
```

### Day 4: Create ESG Prompts

**File:** `dspy_implementation/dc_module/dc_prompts.py`

```python
"""ESG-specific prompts for Dynamic Cheatsheet"""

GENERATOR_PROMPT = """You are an ESG reasoning assistant.

## Resources

### Retrieved Context
{context}

### Cheatsheet (Past Insights)
{cheatsheet}

### Question
{question}

### Expected Answer Format
{answer_format}

## Instructions
1. Review cheatsheet for relevant patterns
2. Analyze the retrieved context
3. Apply insights from cheatsheet
4. Extract answer in specified format

## Format Guidelines
- Int: Integer only (e.g., "42")
- Float: Number with decimals (e.g., "3.14")
- Str: Text string (e.g., "Scope 1 emissions")
- List: JSON array (e.g., ["item1", "item2"])
- null: Return "null" if not answerable

## Response
Provide ONLY the final answer. No explanation.
"""

CURATOR_PROMPT = """You are a curator maintaining an ESG reasoning cheatsheet.

## Current Cheatsheet
{current_cheatsheet}

## Recent Question & Answer
Question: {question}
Format: {answer_format}
Your Answer: {answer}
Context: {context}

## Task
Update the cheatsheet with new insights. Focus on:

1. Calculations: Formulas, unit conversions, percentages
2. Terminology: ESG terms, scope definitions, acronyms
3. Format Tips: Best practices for each answer type
4. Patterns: Common answer patterns
5. Pitfalls: Mistakes to avoid

Keep entries concise. Remove redundant items.

## Updated Cheatsheet
"""
```

### Day 5: Implement DC + RAG Integration

**File:** `dspy_implementation/dc_module/dc_rag_module.py`

```python
"""DC + RAG integration for MMESGBench"""
import sys
sys.path.append('..')

from dspy_implementation.dspy_postgres_retriever import DSPyPostgresRetriever
from dspy_implementation.dc_module.dc_wrapper import DCWrapper
from dspy_implementation.dc_module.dc_prompts import GENERATOR_PROMPT, CURATOR_PROMPT

class DCRAGModule:
    """Combines RAG retrieval with Dynamic Cheatsheet"""
    
    def __init__(self, model_name="qwen2.5-7b-instruct"):
        self.retriever = DSPyPostgresRetriever()
        self.dc = DCWrapper(model_name)
        self.cheatsheet = "(empty)"
        print(f"DC-RAG module initialized")
    
    def _format_input(self, question, context, answer_format):
        """Format input for DC generator"""
        return GENERATOR_PROMPT.format(
            context=context,
            cheatsheet=self.cheatsheet,
            question=question,
            answer_format=answer_format
        )
    
    def forward(self, question, doc_id, answer_format):
        """Process question with DC + RAG"""
        # Step 1: RAG retrieval
        context = self.retriever.retrieve(doc_id, question, top_k=5)
        
        if not context:
            return "ERROR: Retrieval failed"
        
        # Step 2: DC generation + curation
        try:
            input_prompt = self._format_input(question, context, answer_format)
            
            result = self.dc.generate_with_cheatsheet(
                prompt=input_prompt,
                cheatsheet=self.cheatsheet,
                generator_template=GENERATOR_PROMPT,
                cheatsheet_template=CURATOR_PROMPT
            )
            
            # Step 3: Update cheatsheet
            self.cheatsheet = result.get('final_cheatsheet', self.cheatsheet)
            
            return result.get('final_answer', 'ERROR: No answer')
            
        except Exception as e:
            print(f"DC error: {e}")
            return "ERROR: Generation failed"
    
    def __call__(self, question, doc_id, answer_format):
        return self.forward(question, doc_id, answer_format)
```

### Test POC (10 Dev Questions)

**File:** `test_dc_poc.py`

```python
#!/usr/bin/env python3
"""Test DC on 10 dev questions"""
import sys
sys.path.append('.')

from dspy_implementation.dspy_setup import setup_dspy_qwen
from dspy_implementation.dspy_dataset import MMESGBenchDataset
from dspy_implementation.dc_module.dc_rag_module import DCRAGModule
from MMESGBench.src.eval.eval_score import eval_score

# Setup
setup_dspy_qwen()
dataset = MMESGBenchDataset()
dc_module = DCRAGModule()

# Test on 10 questions
correct = 0
total = 10

print("Testing DC on 10 Dev Questions")

for i, example in enumerate(dataset.dev_set[:10]):
    pred = dc_module(
        question=example.question,
        doc_id=example.doc_id,
        answer_format=example.answer_format
    )
    
    score = eval_score(example.answer, pred, example.answer_format)
    is_correct = (score >= 0.5)
    
    if is_correct:
        correct += 1
    
    print(f"Q{i+1}: {example.answer_format} | {'PASS' if is_correct else 'FAIL'}")
    print(f"  GT: {example.answer}")
    print(f"  Pred: {pred}")
    print(f"  Cheatsheet length: {len(dc_module.cheatsheet)} chars")

print(f"Accuracy: {correct}/{total} = {correct/total:.1%}")
```

Run POC:

```bash
python test_dc_poc.py
```

**CHECKPOINT:** If accuracy < 40% or crashes -> STOP, document issues

---

## Week 2: Full Implementation

### Add Checkpointing

**File:** `dspy_implementation/dc_module/dc_evaluator.py`

```python
#!/usr/bin/env python3
"""DC Evaluator with checkpointing"""
import json
import os
from tqdm import tqdm

class DCEvaluator:
    """Evaluate DC with checkpoint support"""
    
    def __init__(self, checkpoint_file="dc_checkpoint.json"):
        self.checkpoint_file = checkpoint_file
    
    def evaluate(self, dc_module, dataset, save_file):
        """Evaluate DC on dataset with checkpointing"""
        # Load checkpoint if exists
        if os.path.exists(self.checkpoint_file):
            print(f"Loading checkpoint: {self.checkpoint_file}")
            with open(self.checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
            predictions = checkpoint['predictions']
            dc_module.cheatsheet = checkpoint.get('cheatsheet', '(empty)')
            start_idx = len(predictions)
        else:
            predictions = []
            start_idx = 0
        
        # Evaluate
        print(f"Evaluating from question {start_idx+1}/{len(dataset)}...")
        
        for i, example in enumerate(tqdm(dataset[start_idx:], 
                                         initial=start_idx, 
                                         total=len(dataset))):
            try:
                pred = dc_module(
                    question=example.question,
                    doc_id=example.doc_id,
                    answer_format=example.answer_format
                )
                
                predictions.append({
                    'question': example.question,
                    'doc_id': example.doc_id,
                    'answer_format': example.answer_format,
                    'ground_truth': example.answer,
                    'prediction': pred
                })
                
                # Save checkpoint every 10 questions
                if len(predictions) % 10 == 0:
                    with open(self.checkpoint_file, 'w') as f:
                        json.dump({
                            'predictions': predictions,
                            'cheatsheet': dc_module.cheatsheet
                        }, f, indent=2)
            
            except Exception as e:
                print(f"Error on Q{start_idx+i+1}: {e}")
                predictions.append({
                    'question': example.question,
                    'prediction': 'ERROR'
                })
        
        # Save final results
        print(f"Saving results to {save_file}")
        with open(save_file, 'w') as f:
            json.dump({
                'predictions': predictions,
                'final_cheatsheet': dc_module.cheatsheet,
                'total_questions': len(predictions)
            }, f, indent=2)
        
        # Remove checkpoint
        if os.path.exists(self.checkpoint_file):
            os.remove(self.checkpoint_file)
        
        return predictions
```

### Test on Dev Set (93 Questions)

```bash
python -c "
from dspy_implementation.dspy_setup import setup_dspy_qwen
from dspy_implementation.dspy_dataset import MMESGBenchDataset
from dspy_implementation.dc_module.dc_rag_module import DCRAGModule
from dspy_implementation.dc_module.dc_evaluator import DCEvaluator

setup_dspy_qwen()
dataset = MMESGBenchDataset()
dc_module = DCRAGModule()
evaluator = DCEvaluator('dc_dev_checkpoint.json')

predictions = evaluator.evaluate(
    dc_module, 
    dataset.dev_set, 
    'results/dev_set/dc_dev_93.json'
)
print(f'Complete: {len(predictions)} predictions')
"
```

**CHECKPOINT:** If accuracy < 45% -> Consider stopping

---

## Week 3: Test Set Evaluation

### Run DC-Cumulative Cold Start (654 Questions)

```bash
python -c "
from dspy_implementation.dspy_setup import setup_dspy_qwen
from dspy_implementation.dspy_dataset import MMESGBenchDataset
from dspy_implementation.dc_module.dc_rag_module import DCRAGModule
from dspy_implementation.dc_module.dc_evaluator import DCEvaluator

setup_dspy_qwen()
dataset = MMESGBenchDataset()
dc_module = DCRAGModule()
evaluator = DCEvaluator('dc_test_cold_checkpoint.json')

predictions = evaluator.evaluate(
    dc_module,
    dataset.test_set,
    'results/test_set/dc_cumulative_cold_test_654.json'
)
"
```

**Expected:** 3-4 hours runtime, $0.80 cost

### Run DC-Cumulative Warm Start (933 Questions)

```bash
python -c "
from dspy_implementation.dspy_setup import setup_dspy_qwen
from dspy_implementation.dspy_dataset import MMESGBenchDataset
from dspy_implementation.dc_module.dc_rag_module import DCRAGModule
from dspy_implementation.dc_module.dc_evaluator import DCEvaluator

setup_dspy_qwen()
dataset = MMESGBenchDataset()
dc_module = DCRAGModule()
evaluator = DCEvaluator('dc_test_warm_checkpoint.json')

# Warm up on train + dev
all_data = dataset.train_set + dataset.dev_set + dataset.test_set

predictions = evaluator.evaluate(
    dc_module,
    all_data,
    'results/test_set/dc_cumulative_warm_test_933.json'
)
"
```

**Expected:** 5-6 hours runtime, $1.12 cost

---

## Week 4: Analysis

### Compute Metrics

```python
from MMESGBench.src.eval.eval_score import eval_score
import json

def compute_metrics(results_file):
    """Compute accuracy from results file"""
    with open(results_file, 'r') as f:
        data = json.load(f)
    
    predictions = data['predictions']
    correct = 0
    total = len(predictions)
    
    format_breakdown = {
        'Int': {'correct': 0, 'total': 0},
        'Float': {'correct': 0, 'total': 0},
        'Str': {'correct': 0, 'total': 0},
        'List': {'correct': 0, 'total': 0},
        'null': {'correct': 0, 'total': 0}
    }
    
    for pred in predictions:
        if pred['prediction'] == 'ERROR':
            continue
        
        score = eval_score(
            pred['ground_truth'],
            pred['prediction'],
            pred['answer_format']
        )
        is_correct = (score >= 0.5)
        
        if is_correct:
            correct += 1
            format_breakdown[pred['answer_format']]['correct'] += 1
        
        format_breakdown[pred['answer_format']]['total'] += 1
    
    print(f"Results: {results_file}")
    print(f"Overall: {correct}/{total} = {correct/total:.1%}")
    print("Format Breakdown:")
    for fmt, stats in format_breakdown.items():
        if stats['total'] > 0:
            acc = stats['correct'] / stats['total']
            print(f"  {fmt}: {acc:.1%} ({stats['correct']}/{stats['total']})")

# Run on all results
compute_metrics('results/test_set/dc_cumulative_cold_test_654.json')
compute_metrics('results/test_set/dc_cumulative_warm_test_933.json')
```

---

## Final Checklist

### Week 1: POC

- [ ] DC repository cloned
- [ ] Basic wrapper implemented
- [ ] ESG prompts created
- [ ] DC + RAG integration working
- [ ] Tested on 10 dev questions
- [ ] Decision: Continue or stop?

### Week 2: Full Implementation

- [ ] Checkpointing added
- [ ] Error handling robust
- [ ] Dev set validation (93 Q) complete
- [ ] Accuracy >= 45%
- [ ] Decision: Continue to test set?

### Week 3: Evaluation

- [ ] DC-Cold test run complete
- [ ] DC-Warm test run complete
- [ ] All results saved
- [ ] No data loss

### Week 4: Analysis

- [ ] Metrics computed
- [ ] Comparison table created
- [ ] Format breakdown analyzed
- [ ] Findings report written
- [ ] Main docs updated

---

## Troubleshooting

### DC Import Errors

```bash
# Add DC repo to Python path
export PYTHONPATH="${PYTHONPATH}:/Users/victoryim/Local_Git/CC/dc_repo"
```

### Model API Errors

```bash
# Check DashScope API key
echo $DASHSCOPE_API_KEY

# Test model directly
python -c "from dashscope import Generation; print('API works')"
```

### Retrieval Errors

```bash
# Check PostgreSQL connection
echo $PG_URL

# Test retrieval
python -c "
from dspy_implementation.dspy_postgres_retriever import DSPyPostgresRetriever
r = DSPyPostgresRetriever()
print('Retrieval works')
"
```

---

**Next:** Follow this guide week-by-week. Good luck!
