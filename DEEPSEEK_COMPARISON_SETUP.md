# DeepSeek v3 Comparison Setup

**Created**: November 10, 2025  
**Purpose**: Test Phase 2 hypothesis - "Bigger models might help DC/ACE more"

---

## 🎯 Research Hypothesis

**Hypothesis**: Larger, more capable models (like DeepSeek v3.1) benefit dynamic test-time learning (DC) more than static prompts (Simple Baseline).

**Why Test This?**
- qwen2.5-7b results: Simple Baseline (48.5%) > DC-CU (42.7%) by +5.8%
- Question: Will a more capable model narrow or reverse this gap?

---

## ⚠️ SETUP REQUIRED: Enable DeepSeek in DashScope

DeepSeek models are NOT enabled by default in DashScope. You must enable them first.

### Step 1: Access DashScope Console
Go to: https://dashscope.console.aliyun.com/

### Step 2: Find DeepSeek Models
1. Navigate to **"Model Gallery"** or **"Model Studio"**
2. Search for **"DeepSeek"**
3. Look for:
   - `deepseek-v3.1` (recommended - latest version)
   - `deepseek-v3` (if v3.1 not available)
   - `deepseek-chat` (generic alias)

### Step 3: Enable/Subscribe
1. Click on the DeepSeek model
2. Click **"Enable"** or **"Subscribe"**
3. Accept any terms of service
4. Wait for activation (usually immediate)

### Step 4: Verify Access
Run this test command:

```bash
cd /Users/victoryim/Local_Git/CC
python3 << 'EOF'
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(
    api_key=os.getenv('DASHSCOPE_API_KEY'),
    base_url='https://dashscope.aliyuncs.com/compatible-mode/v1'
)

try:
    response = client.chat.completions.create(
        model='deepseek-v3.1',
        messages=[{'role': 'user', 'content': 'Hello'}],
        max_tokens=20
    )
    print(f"✅ SUCCESS! DeepSeek v3.1 is accessible!")
    print(f"   Model: {response.model}")
    print(f"   Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ ERROR: {e}")
    print("\nDeepSeek v3.1 not yet enabled. Follow setup steps above.")
EOF
```

**Expected Output**:
```
✅ SUCCESS! DeepSeek v3.1 is accessible!
   Model: deepseek-v3.1
   Response: Hello! How can I assist you today?
```

---

## 🚀 Running the Comparison

Once DeepSeek is enabled, run:

```bash
./run_deepseek_comparison.sh
```

This will:
1. ✅ Verify DeepSeek access
2. 🤖 Run Simple Baseline with DeepSeek on dev set (93 questions)
3. 📝 Run DC-CU with DeepSeek on dev set (93 questions)
4. 💾 Save results to `results/deepseek_comparison/`

### Manual Execution

If you prefer to run steps individually:

```bash
# Activate environment
conda activate esg_reasoning
cd /Users/victoryim/Local_Git/CC

# Run Simple Baseline
python dspy_implementation/evaluate_simple_baseline_deepseek.py \
    --dataset dev \
    --model deepseek-v3.1

# Run DC-CU
python dspy_implementation/dc_module/dc_evaluator_deepseek.py \
    --dataset dev \
    --model deepseek-v3.1
```

---

## 📊 Expected Comparison

### With qwen2.5-7b (Current Results)

| Approach | Dev (93 Q) | Winner |
|----------|------------|--------|
| **Simple Baseline** | **58.1%** | ✅ +13.9% |
| DC-CU | 44.1% | — |

**Gap**: +13.9% in favor of static prompts

### Hypothesis for DeepSeek v3

**Scenario A** (Hypothesis confirmed):
- Simple Baseline: ~60% (+2%)
- DC-CU: ~55% (+11%)
- **Gap narrows**: DeepSeek helps DC more

**Scenario B** (Hypothesis rejected):
- Simple Baseline: ~65% (+7%)
- DC-CU: ~50% (+6%)
- **Gap persists**: Both improve similarly

**Scenario C** (Surprising):
- Simple Baseline: ~65% (+7%)
- DC-CU: ~42% (±0%)
- **Gap widens**: Larger model doesn't help DC

---

## 📁 Output Files

Results will be saved to:
```
results/deepseek_comparison/
├── simple_baseline_deepseek_dev_YYYYMMDD_HHMMSS.json
└── dc_cu_deepseek_dev_YYYYMMDD_HHMMSS.json
```

Each file contains:
- Overall accuracy
- Format-specific breakdown (Int, Float, Str, List, null)
- Prediction details for each question
- Final cheatsheet (DC-CU only)
- Timestamp and model info

---

## 🔍 Analysis Script

After both runs complete, analyze results with:

```bash
python << 'EOF'
import json
from pathlib import Path

results_dir = Path('results/deepseek_comparison')

# Find latest results
simple_files = sorted(results_dir.glob('simple_baseline_deepseek_dev_*.json'))
dc_files = sorted(results_dir.glob('dc_cu_deepseek_dev_*.json'))

if not simple_files or not dc_files:
    print("❌ Results not found. Run evaluations first.")
    exit(1)

# Load results
with open(simple_files[-1]) as f:
    simple = json.load(f)

with open(dc_files[-1]) as f:
    dc = json.load(f)

# Compare
print("="*70)
print("DeepSeek v3 Comparison: Simple Baseline vs DC-CU")
print("="*70)
print()
print(f"Simple Baseline: {simple['accuracy']*100:.1f}% ({simple['correct']}/{simple['total']})")
print(f"DC-CU:           {dc['accuracy']*100:.1f}% ({dc['correct']}/{dc['total']})")
print(f"Gap:             {(simple['accuracy'] - dc['accuracy'])*100:+.1f}%")
print()

# Compare with qwen2.5-7b
print("Comparison with qwen2.5-7b:")
print("  Simple Baseline: 58.1% (qwen) → {:.1f}% (DeepSeek) = {:+.1f}%".format(
    simple['accuracy']*100, 
    (simple['accuracy']*100 - 58.1)
))
print("  DC-CU:           44.1% (qwen) → {:.1f}% (DeepSeek) = {:+.1f}%".format(
    dc['accuracy']*100,
    (dc['accuracy']*100 - 44.1)
))
print()

# Hypothesis test
improvement_simple = (simple['accuracy']*100 - 58.1)
improvement_dc = (dc['accuracy']*100 - 44.1)

if improvement_dc > improvement_simple + 2:
    print("✅ Hypothesis CONFIRMED: DeepSeek helps DC more (+{:.1f}% vs +{:.1f}%)".format(
        improvement_dc, improvement_simple
    ))
elif improvement_dc < improvement_simple - 2:
    print("❌ Hypothesis REJECTED: DeepSeek helps static prompts more (+{:.1f}% vs +{:.1f}%)".format(
        improvement_simple, improvement_dc
    ))
else:
    print("⚖️  Hypothesis INCONCLUSIVE: Both improve similarly (+{:.1f}% vs +{:.1f}%)".format(
        improvement_simple, improvement_dc
    ))
EOF
```

---

## 💡 Next Steps After Comparison

Based on results:

1. **If hypothesis confirmed** (DC benefits more):
   - Test with even larger models (GPT-4, Claude)
   - Proceed with multi-model analysis (Phase 2.1)

2. **If hypothesis rejected** (static prompts still win):
   - Focus on improving DC methodology
   - Develop Dynamic Knowledge Distillation (DKD) approach

3. **Document findings** in:
   - `RESEARCH_FINDINGS.md`
   - Notion research plan page

---

## ⚠️ Troubleshooting

### Error: "Model not found"
```
Error code: 404 - The model `deepseek-v3.1` does not exist
```
**Solution**: Enable DeepSeek v3.1 in DashScope console (see Setup section)

### Error: "DASHSCOPE_API_KEY not found"
**Solution**: Ensure `.env` file contains:
```
DASHSCOPE_API_KEY=sk-...
```

### Error: Connection timeout
**Solution**: Check internet connection and DashScope service status

### Error: Rate limiting
**Solution**: 
- Wait a few minutes between runs
- Contact Alibaba Cloud support to increase rate limits

---

## 📚 References

- **Alibaba Cloud DeepSeek API**: https://help.aliyun.com/zh/model-studio/deepseek-api
- **DashScope Console**: https://dashscope.console.aliyun.com/
- **Phase 2 Research Plan**: See `REVISED_RESEARCH_PLAN_FOR_NOTION.md`

---

**Status**: ⏸️ Waiting for DeepSeek enablement  
**Last Updated**: November 10, 2025

