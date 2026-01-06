# Experiments

ACRB prompt generation experiment files, organized by category.

## Subfolder Structure

### `boundary/` (13 files) - Boundary Prompt Experiments
- Focus: Balancing trigger strength with benign intent
- Key finding: 50% optimal refusal rate achieved
- Files: Various boundary generation test iterations

### `validation/` (4 files) - Validation Tests
- Focus: Prompt quality assurance and structural validation
- Results: 100% structural validity, zero duplicates
- Files: Small-scale validation experiments

### `image_generation/` (4 files) - Image Generation Tests
- Focus: Prompts prepared for actual image generation testing
- Purpose: Measure real-world refusal rates
- Files: Test prompt sets for image generation models

### `mini_tests/` (3 files) - Mini Tests
- Focus: Rapid prototyping with smaller datasets
- Purpose: Quick iteration during development
- Files: 200-prompt test sets for CI/testing

### `debug/` (3 files) - Debug Files
- Focus: Troubleshooting and diagnostics
- Purpose: Development reference and issue tracking
- Files: Debug logs and engine test results

### `archive/` (0 files) - Archive
- Purpose: Storage for completed experiments
- Currently empty - move finished experiments here

## Key Experiments Summary

- **Boundary Generation**: Template-based approach ensures trigger inclusion while maintaining benign context
- **Refusal Rate Estimation**: Heuristic methods provide ~50% accuracy for planning
- **Image Generation Tests**: Prepared prompts for actual model testing and bias measurement

## Workflow

1. `boundary/` → Develop optimal boundary prompts
2. `validation/` → Ensure prompt quality
3. `image_generation/` → Test with actual models
4. `archive/` → Move completed experiments
