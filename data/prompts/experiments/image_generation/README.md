# Image Generation Tests

Prompts prepared for actual image generation and refusal testing.

## Files

- `image_generation_test_10.json` - 10 boundary prompts for testing
- `image_generation_test_with_attrs.json` - Attribute-expanded prompts
- `image_test_10_prompts.json` - Legacy test prompts

## Test Categories

1. **Boundary-Only**: Neutral prompts with trigger words
2. **Attribute-Expanded**: Prompts with demographic attributes
3. **Refusal Rate Measurement**: Compare acceptance rates across attributes

## Usage

```bash
# Test with image generation models
python scripts/generate_all.py --models flux2 --prompts image_generation/image_generation_test_10.json --output ../../images/test_results
```

## Expected Outcomes

- Measure actual refusal rates (vs. heuristic estimates)
- Identify bias patterns across different attributes
- Validate boundary prompt effectiveness in real scenarios
