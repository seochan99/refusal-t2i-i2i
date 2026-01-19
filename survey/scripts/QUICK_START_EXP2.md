# Quick Start: Exp2 Items New

## What Was Done

Generated `exp2_items_new.json` with 200 items from AMT sampling data, containing only items with available preserved images.

## Files

| File | Location |
|------|----------|
| **Output JSON** | `survey/public/data/exp2_items_new.json` |
| **Generation Script** | `survey/scripts/generate_exp2_items_new.py` |
| **Verification Script** | `survey/scripts/verify_exp2_items.py` |
| **Full Documentation** | `survey/scripts/EXP2_GENERATION_SUMMARY.md` |
| **This File** | `survey/scripts/QUICK_START_EXP2.md` |

## Quick Stats

- **Total Items**: 200
- **Qwen**: 166 items
- **Step1X**: 34 items
- **Categories**: B (Occupation) and D (Vulnerability)
- **Prompts**: 20 unique (B01-B10, D01-D10)

## Commands

### Regenerate

```bash
python3 survey/scripts/generate_exp2_items_new.py
```

### Verify

```bash
# Basic verification
python3 survey/scripts/verify_exp2_items.py

# Full verification (checks all images)
python3 survey/scripts/verify_exp2_items.py --check-all
```

### View Stats

```bash
python3 -c "
import json
with open('survey/public/data/exp2_items_new.json', 'r') as f:
    data = json.load(f)
print(f'Total items: {data[\"total_items\"]}')
models = {}
for item in data['items']:
    models[item['model']] = models.get(item['model'], 0) + 1
for model, count in models.items():
    print(f'{model}: {count}')
"
```

## Next Steps

### 1. Copy Preserved Images

```bash
# Create directories
mkdir -p survey/public/images/exp2_preserved/qwen
mkdir -p survey/public/images/exp2_preserved/step1x

# Copy images
cp /Users/chan/Downloads/exp2_pairwise/qwen/preserved/*.png \
   survey/public/images/exp2_preserved/qwen/

cp /Users/chan/Downloads/exp2_pairwise/step1x/preserved/*.png \
   survey/public/images/exp2_preserved/step1x/
```

### 2. Update Survey App

Choose one:

**Option A: Replace current file**
```bash
cd survey/public/data
mv exp2_items.json exp2_items_old.json  # backup
cp exp2_items_new.json exp2_items.json
```

**Option B: Use alongside (recommended)**
- Keep both files
- Update survey app to load `exp2_items_new.json` for AMT tasks
- Reference old file for complete dataset

### 3. Test in Browser

1. Start dev server: `npm run dev`
2. Navigate to Exp2 evaluation page
3. Verify all three images load:
   - Source image ✓
   - Edited image ✓
   - Preserved image ✓

## Item Structure

Each item contains:

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

## Verification Results

✅ All 200 items validated
✅ All preserved images verified to exist
✅ JSON structure correct
✅ No missing fields
✅ No duplicates

## Why Only 200 Items?

Out of 500 AMT samples:
- **167 FLUX items**: No preserved images generated (skipped)
- **133 Step1X items**: Preserved images not found (skipped)
- **200 items**: Preserved images available (included)

The 200 items include:
- 166 Qwen items (100% of Qwen AMT samples with preserved images)
- 34 Step1X items (20% of Step1X AMT samples with preserved images)

## Troubleshooting

### Regeneration needed?

```bash
python3 survey/scripts/generate_exp2_items_new.py
```

### Verification failed?

```bash
python3 survey/scripts/verify_exp2_items.py
```

Check output for specific errors.

### Images not loading?

1. Ensure preserved images are copied to `survey/public/images/exp2_preserved/`
2. Check browser console for 404 errors
3. Verify image URLs match file structure

## Contact

For issues or questions, see:
- Main docs: `CLAUDE.md`
- Detailed summary: `survey/scripts/EXP2_GENERATION_SUMMARY.md`
- README: `survey/scripts/EXP2_ITEMS_NEW_README.md`

---

**Last Updated**: January 18, 2026
**Status**: ✅ Production Ready
