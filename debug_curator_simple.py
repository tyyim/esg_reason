#!/usr/bin/env python3
"""
Simple debug script to test curator cheatsheet generation
Uses DC's LanguageModel directly
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

# Verify API key
if not os.getenv("DASHSCOPE_API_KEY"):
    raise ValueError("DASHSCOPE_API_KEY not found")

from dynamic_cheatsheet.language_model import LanguageModel

# Load curator prompt
with open(project_root / 'dc_repo/prompts/curator_prompt_for_dc_cumulative.txt', 'r') as f:
    curator_template = f.read()

# Test data
previous_cheatsheet = ""  # Empty, like first question
test_question = """Question: What is Alibaba's GHG target?

Context: Alibaba aims to reduce Scope 1 and 2 GHG emissions by 50% by 2030 compared to 2020 baseline.

Expected Answer Format: Str"""

test_answer = """The context states that Alibaba aims to reduce Scope 1 and 2 GHG emissions by 50% by 2030 compared to 2020 baseline.

FINAL ANSWER:
```
50% reduction by 2030
```"""

# Test both models
for model_name in ['qwen2.5-7b-instruct', 'deepseek-v3.1']:
    print("\n" + "="*70)
    print(f"Testing: {model_name}")
    print("="*70)
    
    try:
        # Initialize model
        lm = LanguageModel(f"dashscope/{model_name}")
        
        # Prepare curator prompt
        curator_prompt = curator_template.replace("[[PREVIOUS_CHEATSHEET]]", previous_cheatsheet or "(empty)")
        curator_prompt = curator_prompt.replace("[[QUESTION]]", test_question)
        curator_prompt = curator_prompt.replace("[[MODEL_ANSWER]]", test_answer)
        
        print(f"\n📝 Calling curator with {model_name}...")
        print(f"   Prompt length: {len(curator_prompt)} chars")
        
        # Call curator
        curator_history = [{"role": "user", "content": curator_prompt}]
        curator_output = lm.generate(
            history=curator_history,
            temperature=0.1,
            max_tokens=2048,
            allow_code_execution=False,
        )
        
        print(f"\n✅ Got response")
        print(f"   Output length: {len(curator_output)} characters")
        print(f"   Contains <cheatsheet>: {'<cheatsheet>' in curator_output}")
        print(f"   Contains </cheatsheet>: {'</cheatsheet>' in curator_output}")
        
        # Try to extract cheatsheet
        if "<cheatsheet>" in curator_output:
            try:
                cheatsheet = curator_output.split("<cheatsheet>")[1].strip()
                cheatsheet = cheatsheet.split("</cheatsheet>")[0].strip()
                print(f"\n   ✅ Successfully extracted cheatsheet!")
                print(f"   Cheatsheet length: {len(cheatsheet)} characters")
                print(f"\n   First 500 characters:")
                print("   " + "-"*66)
                print("   " + cheatsheet[:500].replace("\n", "\n   "))
                if len(cheatsheet) > 500:
                    print("   ...")
            except Exception as e:
                print(f"   ❌ Failed to extract: {e}")
        else:
            print(f"\n   ❌ NO <cheatsheet> TAGS FOUND!")
            print(f"\n   First 1000 characters of output:")
            print("   " + "-"*66)
            print("   " + curator_output[:1000].replace("\n", "\n   "))
            if len(curator_output) > 1000:
                print("   ...")
                print(f"\n   Last 500 characters of output:")
                print("   " + "-"*66)
                print("   " + curator_output[-500:].replace("\n", "\n   "))
        
    except Exception as e:
        import traceback
        print(f"\n❌ Error: {e}")
        traceback.print_exc()

print("\n" + "="*70)
print("Debug Complete")
print("="*70)

