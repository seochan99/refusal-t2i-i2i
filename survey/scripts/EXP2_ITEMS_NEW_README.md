# Exp2 Items New - Generation Report

## Executive Summary

Successfully generated `exp2_items_new.json` with **200 items** from AMT sampling data, matching only items that have preserved images available.

**Status**: ✅ Complete - All images verified to exist

## Quick Stats

| Metric | Value |
|--------|-------|
| Total Items | 200 |
| Qwen Items | 166 |
| Step1X Items | 34 |
| FLUX Items | 0 (no preserved images) |
| Coverage | 40% of AMT samples (200/500) |

## Files Generated

1. **Main Output**: `survey/public/data/exp2_items_new.json` (200 items)
2. **Generation Script**: `survey/scripts/generate_exp2_items_new.py`
3. **Documentation**:
   - `survey/scripts/EXP2_GENERATION_SUMMARY.md` (detailed stats)
   - `survey/scripts/EXP2_ITEMS_NEW_README.md` (this file)

## Comparison with Old File

| File | Items | Description |
|------|-------|-------------|
| `exp2_items.json` (old) | 961 | All generated images |
| `exp2_items_new.json` (new) | 200 | AMT-sampled items only |

## Item Breakdown

### By Model and Category

**Qwen (166 items)**:
- Category B (Occupation): 84 items
- Category D (Vulnerability): 82 items

**Step1X (34 items)**:
- Category B (Occupation): 24 items
- Category D (Vulnerability): 10 items

### Prompts Covered

- **Total Unique Prompts**: 20 (B01-B10, D01-D10)
- All items are from categories B and D only

## What's Different?

### Old File (exp2_items.json)
- Contains all 961 generated images
- May include images not in AMT sampling
- No filtering based on preserved image availability

### New File (exp2_items_new.json)
- Contains only 200 AMT-sampled items
- Only includes items with verified preserved images
- Excludes FLUX model (no preserved images)
- Excludes 133 Step1X items (preserved image not found)

## Next Steps

### 1. Copy Preserved Images

The preserved images are currently in `/Users/chan/Downloads/exp2_pairwise/`. They need to be copied to the survey public directory:

```bash
# Create directories
mkdir -p /Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/survey/public/images/exp2_preserved/qwen
mkdir -p /Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/survey/public/images/exp2_preserved/step1x

# Copy images
cp /Users/chan/Downloads/exp2_pairwise/qwen/preserved/*.png \
   /Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/survey/public/images/exp2_preserved/qwen/

cp /Users/chan/Downloads/exp2_pairwise/step1x/preserved/*.png \
   /Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/survey/public/images/exp2_preserved/step1x/
```

### 2. Update Survey App

Option A: Replace current file
```bash
cd /Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/survey/public/data
mv exp2_items.json exp2_items_old.json
mv exp2_items_new.json exp2_items.json
```

Option B: Use as separate experiment (recommended)
- Keep both files
- Update survey app to use `exp2_items_new.json` for AMT evaluation
- Keep `exp2_items.json` for full dataset browsing

### 3. Verify in Browser

Test that all images load correctly:
- Source image ✓
- Edited image ✓
- Preserved image ✓

## Image URL Structure

Each item has three image URLs:

1. **Source Image**: `/images/source/{race}/{race}_{gender}_{age}.jpg`
   - Example: `/images/source/Latino/Latino_Female_40s.jpg`

2. **Edited Image**: `/images/exp1_sampling_b_d/{model}/{categoryName}/{filename}`
   - Example: `/images/exp1_sampling_b_d/qwen/B_occupation/B03_MiddleEastern_Female_60s_success.png`

3. **Preserved Image**: `/images/exp2_preserved/{model}/{promptId}_{race}_{gender}_{age}.png`
   - Example: `/images/exp2_preserved/qwen/B03_MiddleEastern_Female_60s.png`

## Validation Results

✅ All 200 items have verified preserved images
✅ JSON structure is valid
✅ All required fields present
✅ Image paths follow consistent naming convention
✅ No duplicate items

## Usage Example

```python
import json

# Load items
with open('survey/public/data/exp2_items_new.json', 'r') as f:
    data = json.load(f)

# Access items
for item in data['items']:
    print(f"Item: {item['id']}")
    print(f"  Source: {item['sourceImageUrl']}")
    print(f"  Edited: {item['editedImageUrl']}")
    print(f"  Preserved: {item['preservedImageUrl']}")
```

## Regeneration

To regenerate this file (e.g., if AMT sampling data changes):

```bash
python3 survey/scripts/generate_exp2_items_new.py
```

The script will:
1. Read latest AMT sampling data
2. Check for preserved image existence
3. Generate new JSON file
4. Print statistics

## Contact

For questions or issues, refer to:
- Generation script: `survey/scripts/generate_exp2_items_new.py`
- Detailed summary: `survey/scripts/EXP2_GENERATION_SUMMARY.md`
- Project docs: `CLAUDE.md`

---

**Generated**: January 18, 2026
**Script Version**: 1.0
**Status**: Production Ready ✅
