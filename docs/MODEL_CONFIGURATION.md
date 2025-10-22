# Model Configuration Summary

**Last Updated**: 2025-10-19

## Qwen Models Used in This Project

We are using **Alibaba Cloud's Qwen (通义千问) models** via DashScope API.

### Model Names and Usage

| Component | Model Name | Full Identifier | Purpose |
|-----------|------------|-----------------|---------|
| **Baseline Evaluation** | `qwen-max` (default) | `openai/qwen-max` | Default baseline RAG (can override with `QWEN_MODEL` env var) |
| **MIPROv2 Student** | `qwen2.5-7b-instruct` | `openai/qwen2.5-7b-instruct` | Task execution after optimization |
| **MIPROv2 Teacher** | `qwen-max` | `openai/qwen-max` | Generates optimized prompts |
| **GEPA Student** | `qwen2.5-7b-instruct` | `openai/qwen2.5-7b-instruct` | Task execution with evolved prompts |
| **GEPA Reflection** | `qwen-max` | `openai/qwen-max` | Analyzes failures and proposes improvements |

### Primary Models in Detail

#### 1. **qwen-max**
- **Official Name**: Qwen-Max (通义千问-Max)
- **Type**: Alibaba's flagship large language model
- **Use Case**: High-quality baseline, teacher model, reflection model
- **API Identifier**: `openai/qwen-max`
- **Characteristics**:
  - Highest capability model in Qwen family
  - Used when quality is more important than cost
  - Default for baseline evaluation

#### 2. **qwen2.5-7b-instruct**
- **Official Name**: Qwen2.5-7B-Instruct
- **Type**: 7 billion parameter instruction-tuned model
- **Use Case**: Student model for optimization experiments (MIPROv2, GEPA)
- **API Identifier**: `openai/qwen2.5-7b-instruct`
- **Characteristics**:
  - Smaller, faster, cheaper than qwen-max
  - Good balance of performance and efficiency
  - Represents target deployment model (cost-effective)

### API Configuration

All models are accessed via **DashScope API** (Alibaba Cloud's LLM service):

```python
# From dspy_setup.py
lm = dspy.LM(
    model=f'openai/{model_name}',  # e.g., 'openai/qwen-max'
    api_key=DASHSCOPE_API_KEY,
    api_base='https://dashscope.aliyuncs.com/compatible-mode/v1',
    temperature=0.0,      # Deterministic for evaluation
    max_tokens=1024
)
```

### API Endpoint
- **Base URL**: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- **Protocol**: OpenAI-compatible API
- **Authentication**: API key via `DASHSCOPE_API_KEY` environment variable

### Rate Limiting & Connection Issues

**Current Observations**:
- Connection errors during evaluation: `DashscopeException - Connection error`
- API rate limiting: Automatic retries with exponential backoff
- Average time per question: ~86 seconds (includes retries)

**Root Causes**:
1. **API Rate Limits**: DashScope imposes request rate limits
2. **Service Instability**: Intermittent connection errors on DashScope side
3. **NOT database connection limits** (PostgreSQL: 6/60 connections used)

**Mitigation**:
- Built-in retry logic with exponential backoff
- Connection pooling for database
- Consider upgrading DashScope plan if issues persist (NOT Supabase)

### Model Selection Strategy

| Scenario | Model Choice | Rationale |
|----------|--------------|-----------|
| Baseline evaluation | `qwen-max` | Highest quality for comparison |
| Optimization teacher | `qwen-max` | Generate best quality prompts |
| Optimization student | `qwen2.5-7b-instruct` | Target deployment model |
| Production inference | `qwen2.5-7b-instruct` | Cost-effective with optimized prompts |

### Performance Expectations

Based on our results:

| Approach | Model(s) Used | Dev Set Accuracy |
|----------|---------------|------------------|
| **Baseline** | qwen2.5-7b-instruct (stated as baseline) | 58.1% (54/93) |
| **MIPROv2** | Teacher: qwen-max<br>Student: qwen2.5-7b-instruct | 57.0% (53/93) |
| **GEPA** | Reflection: qwen-max<br>Student: qwen2.5-7b-instruct | 54.8% (51/93) |

**Note**: All three use the same student model (`qwen2.5-7b-instruct`) for final execution. The optimization process uses `qwen-max` to improve the prompts, but final inference runs on the 7B model.

### Environment Variables

```bash
# Required in .env file
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional override for baseline evaluation
QWEN_MODEL=qwen2.5-7b-instruct  # Default: qwen-max
```

### Cost Considerations

**DashScope Pricing** (approximate, check current rates):
- `qwen-max`: Higher cost per token, best quality
- `qwen2.5-7b-instruct`: Lower cost per token, good quality

**Optimization vs Inference**:
- Optimization (one-time): Uses qwen-max extensively (~$$$)
- Inference (ongoing): Uses qwen2.5-7b-instruct (lower cost)
- Goal: Spend on optimization to reduce ongoing inference costs

### Related Documentation

- **DashScope Docs**: https://help.aliyun.com/zh/dashscope/
- **Qwen Models**: https://github.com/QwenLM/Qwen
- **OpenAI-Compatible API**: https://help.aliyun.com/zh/dashscope/developer-reference/compatibility-of-openai-with-dashscope

---

**Summary**: We use **qwen-max** for high-quality baselines and optimization, then deploy optimized prompts on **qwen2.5-7b-instruct** for cost-effective inference. All models accessed via DashScope's OpenAI-compatible API.
