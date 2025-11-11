#!/usr/bin/env python3
"""
Debug script to test DeepSeek's cheatsheet generation
Tests what DeepSeek actually outputs with the curator prompt
"""

import os
import sys
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Load environment
project_root = Path(__file__).parent
load_dotenv(project_root / ".env")

# Initialize OpenAI client for DashScope
api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    raise ValueError("DASHSCOPE_API_KEY not found")

client = OpenAI(
    api_key=api_key,
    base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
)

# Load curator prompt
with open(project_root / 'dc_repo/prompts/curator_prompt_for_dc_cumulative.txt', 'r') as f:
    curator_template = f.read()

# Test with a simple example
print("="*70)
print("Testing DeepSeek v3.1 Cheatsheet Generation")
print("="*70)

# Prepare test data
previous_cheatsheet = ""  # Empty, like first question
test_question = """Question: What is Alibaba Group's GHG emissions reduction target?

Context from ESG Report:
Alibaba Group aims to achieve carbon neutrality by 2030. The company has set a target to reduce Scope 1 and 2 GHG emissions by 50% by 2030 compared to 2020 baseline.

Expected Answer Format: Str"""

test_answer = """To answer this question, I need to look at the GHG emissions target mentioned in the context.

The context states: "The company has set a target to reduce Scope 1 and 2 GHG emissions by 50% by 2030 compared to 2020 baseline."

FINAL ANSWER:
```
50% reduction by 2030 compared to 2020 baseline
```"""

# Format curator prompt
curator_prompt = curator_template.replace("[[PREVIOUS_CHEATSHEET]]", previous_cheatsheet or "(empty)")
curator_prompt = curator_prompt.replace("[[QUESTION]]", test_question)
curator_prompt = curator_prompt.replace("[[MODEL_ANSWER]]", test_answer)

print("\n📝 Curator Prompt Summary:")
print(f"  Previous cheatsheet: {'(empty)' if not previous_cheatsheet else f'{len(previous_cheatsheet)} chars'}")
print(f"  Question: {test_question.split('Question:')[1].split('Context')[0].strip()[:70]}...")
print(f"  Answer length: {len(test_answer)} chars")
print()

# Test with both qwen and DeepSeek
for model_name in ['qwen2.5-7b-instruct', 'deepseek-v3.1']:
    print("\n" + "="*70)
    print(f"Testing with: {model_name}")
    print("="*70)
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": curator_prompt}
            ],
            temperature=0.1,
            max_tokens=2048
        )
        
        output = response.choices[0].message.content
        
        print(f"\n✅ Got response from {model_name}")
        print(f"   Output length: {len(output)} characters")
        print(f"   Contains <cheatsheet> tag: {'<cheatsheet>' in output}")
        print(f"   Contains </cheatsheet> tag: {'</cheatsheet>' in output}")
        
        # Extract cheatsheet
        if "<cheatsheet>" in output:
            try:
                cheatsheet = output.split("<cheatsheet>")[1].strip()
                cheatsheet = cheatsheet.split("</cheatsheet>")[0].strip()
                print(f"   ✅ Extracted cheatsheet: {len(cheatsheet)} characters")
                print(f"\n   Preview (first 500 chars):")
                print("   " + "-"*66)
                print("   " + cheatsheet[:500].replace("\n", "\n   "))
                if len(cheatsheet) > 500:
                    print("   ...")
            except Exception as e:
                print(f"   ❌ Failed to extract: {e}")
        else:
            print(f"   ❌ No <cheatsheet> tags found!")
            print(f"\n   Full output (first 1000 chars):")
            print("   " + "-"*66)
            print("   " + output[:1000].replace("\n", "\n   "))
            if len(output) > 1000:
                print("   ...")
        
    except Exception as e:
        import traceback
        print(f"❌ Error with {model_name}: {e}")
        print(f"   Traceback:")
        traceback.print_exc()

print("\n" + "="*70)
print("Debug Complete")
print("="*70)

