#!/usr/bin/env python3
"""
Test cheatsheet accumulation over multiple questions
This simulates what happens in DC-CU during evaluation
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

# Load curator prompt
with open(project_root / 'dc_repo/prompts/curator_prompt_for_dc_cumulative.txt', 'r') as f:
    curator_template = f.read()

# Test with 3 questions
test_qa_pairs = [
    {
        "question": "Q1: What is Alibaba's GHG target?",
        "answer": "50% reduction by 2030 vs 2020 baseline"
    },
    {
        "question": "Q2: What is Microsoft's renewable energy commitment?",
        "answer": "100% renewable energy by 2025"
    },
    {
        "question": "Q3: What is Amazon's net-zero target year?",
        "answer": "2040"
    }
]

# Test both models
for model_name in ['qwen2.5-7b-instruct', 'deepseek-v3.1']:
    print("\n" + "="*70)
    print(f"Testing Accumulation: {model_name}")
    print("="*70)
    
    try:
        # Initialize model
        lm = LanguageModel(f"dashscope/{model_name}")
        
        # Start with empty cheatsheet
        cheatsheet = ""
        
        # Process each Q&A pair
        for i, qa in enumerate(test_qa_pairs, 1):
            print(f"\n--- Iteration {i} ---")
            print(f"Previous cheatsheet: {len(cheatsheet)} chars")
            
            # Prepare curator prompt
            curator_prompt = curator_template.replace("[[PREVIOUS_CHEATSHEET]]", cheatsheet or "(empty)")
            curator_prompt = curator_prompt.replace("[[QUESTION]]", qa['question'])
            curator_prompt = curator_prompt.replace("[[MODEL_ANSWER]]", qa['answer'])
            
            print(f"Curator prompt: {len(curator_prompt)} chars")
            
            # Call curator
            curator_history = [{"role": "user", "content": curator_prompt}]
            curator_output = lm.generate(
                history=curator_history,
                temperature=0.1,
                max_tokens=2048,
                allow_code_execution=False,
            )
            
            print(f"Curator output: {len(curator_output)} chars")
            print(f"Contains <cheatsheet>: {'<cheatsheet>' in curator_output}")
            print(f"Contains </cheatsheet>: {'</cheatsheet>' in curator_output}")
            
            # Extract new cheatsheet
            new_cheatsheet = extract_cheatsheet(curator_output, cheatsheet)
            
            print(f"New cheatsheet: {len(new_cheatsheet)} chars")
            
            if new_cheatsheet == cheatsheet:
                print("⚠️  WARNING: Cheatsheet NOT updated!")
                if "<cheatsheet>" not in curator_output:
                    print("   Reason: No <cheatsheet> tag in output")
                    print(f"   First 300 chars: {curator_output[:300]}")
            else:
                print("✅ Cheatsheet successfully updated")
                
            # Update for next iteration
            cheatsheet = new_cheatsheet
        
        # Final summary
        print(f"\n" + "="*70)
        print(f"FINAL RESULT for {model_name}:")
        print(f"  Final cheatsheet: {len(cheatsheet)} characters")
        print(f"  Success: {len(cheatsheet) > 0}")
        print("="*70)
        
    except Exception as e:
        import traceback
        print(f"\n❌ Error: {e}")
        traceback.print_exc()

print("\n" + "="*70)
print("Accumulation Test Complete")
print("="*70)

