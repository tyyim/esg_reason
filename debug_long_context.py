#!/usr/bin/env python3
"""
Test cheatsheet generation with LONG ESG context
Simulates actual evaluation conditions
"""

import os
import sys
from pathlib import Path

# Add paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'dc_repo'))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from dynamic_cheatsheet.language_model import LanguageModel
from dynamic_cheatsheet.utils.extractor import extract_cheatsheet
from dspy_implementation.dspy_dataset import MMESGBenchDataset
from dspy_implementation.dspy_postgres_retriever import DSPyPostgresRetriever

# Load curator prompt
with open(project_root / 'dc_repo/prompts/curator_prompt_for_dc_cumulative.txt', 'r') as f:
    curator_template = f.read()

# Load generator prompt
with open(project_root / 'dc_repo/prompts/generator_prompt.txt', 'r') as f:
    generator_template = f.read()

# Initialize retriever and dataset
retriever = DSPyPostgresRetriever()
dataset = MMESGBenchDataset()

print("="*70)
print("Testing with REAL ESG Data (Long Context)")
print("="*70)

# Take first 3 questions from dev set
test_questions = dataset.dev_set[:3]

for model_name in ['qwen2.5-7b-instruct', 'deepseek-v3.1']:
    print(f"\n{'='*70}")
    print(f"Model: {model_name}")
    print("="*70)
    
    try:
        lm = LanguageModel(f"dashscope/{model_name}")
        cheatsheet = ""
        
        for i, item in enumerate(test_questions, 1):
            print(f"\n--- Question {i} ---")
            question = item['question']
            doc_id = item['doc_id']
            answer_format = item['answer_format']
            
            # Get real context
            context = retriever.retrieve(doc_id, question, top_k=5)
            
            # Format as in actual evaluation
            input_txt = f"""Question: {question}

Context from ESG Report:
{context}

Expected Answer Format: {answer_format}"""
            
            print(f"Question: {question[:60]}...")
            print(f"Context length: {len(context)} chars")
            print(f"Input length: {len(input_txt)} chars")
            print(f"Previous cheatsheet: {len(cheatsheet)} chars")
            
            # Call generator (simulate full process)
            generator_prompt = generator_template.replace("[[QUESTION]]", input_txt).replace("[[CHEATSHEET]]", cheatsheet or "(empty)")
            print(f"Generator prompt: {len(generator_prompt)} chars")
            
            generator_history = [{"role": "user", "content": generator_prompt}]
            generator_output = lm.generate(
                history=generator_history,
                temperature=0.1,
                max_tokens=512,
                allow_code_execution=False,
            )
            print(f"Generator output: {len(generator_output)} chars")
            
            # Call curator
            curator_prompt = curator_template.replace("[[PREVIOUS_CHEATSHEET]]", cheatsheet or "(empty)")
            curator_prompt = curator_prompt.replace("[[QUESTION]]", input_txt)
            curator_prompt = curator_prompt.replace("[[MODEL_ANSWER]]", generator_output)
            
            print(f"Curator prompt: {len(curator_prompt)} chars")
            
            curator_history = [{"role": "user", "content": curator_prompt}]
            curator_output = lm.generate(
                history=curator_history,
                temperature=0.1,
                max_tokens=2048,
                allow_code_execution=False,
            )
            
            print(f"Curator output: {len(curator_output)} chars")
            print(f"Has <cheatsheet> tag: {'<cheatsheet>' in curator_output}")
            
            # Extract
            new_cheatsheet = extract_cheatsheet(curator_output, cheatsheet)
            print(f"New cheatsheet: {len(new_cheatsheet)} chars")
            
            if new_cheatsheet == cheatsheet:
                print("⚠️  WARNING: Cheatsheet NOT updated!")
                if len(cheatsheet) == 0:
                    print("   Starting from empty and stayed empty!")
                    print(f"   Curator output preview:\n{curator_output[:500]}")
            else:
                print("✅ Cheatsheet updated")
            
            cheatsheet = new_cheatsheet
        
        print(f"\n{'='*70}")
        print(f"FINAL for {model_name}: {len(cheatsheet)} chars")
        print("="*70)
        
    except Exception as e:
        import traceback
        print(f"\n❌ Error: {e}")
        traceback.print_exc()

print("\nTest Complete")

