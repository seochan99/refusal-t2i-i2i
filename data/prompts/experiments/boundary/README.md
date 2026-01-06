# Boundary Experiments

Experiments focused on generating boundary prompts that balance trigger strength with benign intent.

## Overview

Boundary prompts are designed to:
- Include trigger words that may activate safety filters
- Maintain educational/hypothetical context to avoid actual harm
- Achieve 20-60% refusal rate for meaningful bias measurement

## Files

- `boundary_test.json` - Initial boundary generation tests
- `boundary_test_v2.json` - Improved template-based generation
- `boundary_test_v3.json` - Enhanced trigger word inclusion
- `boundary_test_strong.json` - Maximum trigger strength tests
- `boundary_template_test.json` - Template validation experiments
- `boundary_balanced.json` - Optimized balance experiments
- `boundary_final.json` - Final boundary configurations
- `boundary_perfect.json` - Best performing boundaries

## Key Findings

- Template-based generation ensures consistent trigger inclusion
- LLM safety filters affect boundary prompt creation
- Optimal balance: strong triggers + benign context
- Target refusal rate: 50% (achieved in final experiments)
