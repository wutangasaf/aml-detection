#!/bin/bash
# Quick wrapper to call AML Expert Agent
# Usage: ./ask_aml.sh "What is trade-based money laundering?"
#
# Requires environment variables:
#   OPENAI_API_KEY - For embeddings
#   ANTHROPIC_API_KEY - For Claude reasoning

if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY not set"
    exit 1
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "Error: ANTHROPIC_API_KEY not set"
    exit 1
fi

cd /Users/asaferez/Projects/aml
python3 -m engines.expert.agent "$@"
