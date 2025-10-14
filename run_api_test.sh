#!/bin/bash
# Test script for API content filter diagnosis

# Activate conda environment
source ~/anaconda3/etc/profile.d/conda.sh
conda activate esg_reasoning

# Export just the API key
export DASHSCOPE_API_KEY="sk-398b62f740a643458bf06c26f0324df1"

# Run test
python test_api_content_filter.py
