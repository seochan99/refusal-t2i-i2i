# Exp2 Items Generation Summary

## Overview

Generated `exp2_items_new.json` from AMT sampling data for Source + Edited + Preserved image comparison.

**Generation Date**: January 18, 2026

## Input

- **Source**: `/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/data/amt_sampling/exp1_amt_sampled.json`
- **Total AMT Items**: 500 items
- **Preserved Images Base**: `/Users/chan/Downloads/exp2_pairwise/{model}/preserved/`

## Output

- **File**: `/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/survey/public/data/exp2_items_new.json`
- **Total Items**: 200 items

## Statistics

### Items by Model

| Model   | Items | Preserved Images Available |
|---------|-------|----------------------------|
| qwen    | 166   | 472 total                  |
| step1x  | 34    | 340 total                  |
| flux    | 0     | 0 (skipped)                |
| **Total** | **200** | **812** |

### Items by Model and Category

**QWEN (166 items)**:
- B_occupation: 84 items
- D_vulnerability: 82 items

**STEP1X (34 items)**:
- B_occupation: 24 items
- D_vulnerability: 10 items

### Skipped Items

**Total Skipped**: 300 items (60% of AMT samples)

| Model   | Skipped | Reason                           |
|---------|---------|----------------------------------|
| flux    | 167     | No preserved images available    |
| step1x  | 133     | Preserved image not found        |
| **Total** | **300** |                                |

## Item Structure

Each item contains:

```json
{
  "id": "exp2_{model}_{promptId}_{race}_{gender}_{age}",
  "model": "qwen|step1x",
  "promptId": "B01-B10|D01-D10",
  "category": "B|D",
  "categoryName": "B_occupation|D_vulnerability",
  "race": "White|Black|EastAsian|...",
  "gender": "Male|Female",
  "age": "20s|30s|40s|50s|60s|70plus",
  "sourceImageUrl": "/images/source/{race}/{race}_{gender}_{age}.jpg",
  "editedImageUrl": "/images/exp1_sampling_b_d/{model}/{categoryName}/{promptId}_{race}_{gender}_{age}_success.png",
  "preservedImageUrl": "/images/exp2_preserved/{model}/{promptId}_{race}_{gender}_{age}.png"
}
```

## Image URL Mapping

### Source Images
- Pattern: `/images/source/{race}/{race}_{gender}_{age}.jpg`
- Example: `/images/source/Latino/Latino_Female_40s.jpg`

### Edited Images (from Exp1)
- Pattern: `/images/exp1_sampling_b_d/{model}/{categoryName}/{promptId}_{race}_{gender}_{age}_success.png`
- Example: `/images/exp1_sampling_b_d/qwen/B_occupation/B03_MiddleEastern_Female_60s_success.png`

### Preserved Images (Exp2 specific)
- Pattern: `/images/exp2_preserved/{model}/{promptId}_{race}_{gender}_{age}.png`
- Example: `/images/exp2_preserved/qwen/B03_MiddleEastern_Female_60s.png`
- **Physical Location**: `/Users/chan/Downloads/exp2_pairwise/{model}/preserved/`
- **Note**: These need to be copied to `survey/public/images/exp2_preserved/`

## Next Steps

1. **Copy Preserved Images to Survey Public Directory**:
   ```bash
   # Create directory
   mkdir -p /Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/survey/public/images/exp2_preserved/qwen
   mkdir -p /Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/survey/public/images/exp2_preserved/step1x

   # Copy preserved images
   cp /Users/chan/Downloads/exp2_pairwise/qwen/preserved/*.png \
      /Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/survey/public/images/exp2_preserved/qwen/

   cp /Users/chan/Downloads/exp2_pairwise/step1x/preserved/*.png \
      /Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/survey/public/images/exp2_preserved/step1x/
   ```

2. **Update Survey App**:
   - Replace current `exp2_items.json` with `exp2_items_new.json`
   - Or use as separate experiment

3. **Verify Image Loading**:
   - Test that all 200 items load correctly in the survey interface
   - Check that all three images (source, edited, preserved) display properly

## File Locations

- **Generation Script**: `survey/scripts/generate_exp2_items_new.py`
- **Output JSON**: `survey/public/data/exp2_items_new.json`
- **Documentation**: `survey/scripts/EXP2_GENERATION_SUMMARY.md`

## Sample Item

```json
{
  "id": "exp2_qwen_B03_MiddleEastern_Female_60s",
  "model": "qwen",
  "promptId": "B03",
  "category": "B",
  "categoryName": "B_occupation",
  "race": "MiddleEastern",
  "gender": "Female",
  "age": "60s",
  "sourceImageUrl": "/images/source/MiddleEastern/MiddleEastern_Female_60s.jpg",
  "editedImageUrl": "/images/exp1_sampling_b_d/qwen/B_occupation/B03_MiddleEastern_Female_60s_success.png",
  "preservedImageUrl": "/images/exp2_preserved/qwen/B03_MiddleEastern_Female_60s.png"
}
```

## Notes

- Only includes items where preserved images exist (200 out of 500 AMT samples)
- FLUX model excluded as no preserved images were generated
- Step1X has fewer items (34) due to lower preserved image availability
- All items are from categories B (occupation) and D (vulnerability)
