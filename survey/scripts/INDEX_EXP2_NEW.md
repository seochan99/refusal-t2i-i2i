# Exp2 Items New - Complete Index

**Generated**: January 18, 2026
**Status**: ✅ Production Ready
**Total Items**: 200 (from 500 AMT samples)

---

## Quick Access

| What | Where |
|------|-------|
| 🎯 **Start Here** | [QUICK_START_EXP2.md](QUICK_START_EXP2.md) |
| 📊 **Stats & Details** | [EXP2_GENERATION_SUMMARY.md](EXP2_GENERATION_SUMMARY.md) |
| 📖 **Full Documentation** | [EXP2_ITEMS_NEW_README.md](EXP2_ITEMS_NEW_README.md) |
| 📁 **File Structure** | [EXP2_FILE_STRUCTURE.txt](EXP2_FILE_STRUCTURE.txt) |
| 🔧 **Generator Script** | [generate_exp2_items_new.py](generate_exp2_items_new.py) |
| ✅ **Verification Script** | [verify_exp2_items.py](verify_exp2_items.py) |

---

## Output File

**Location**: `/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/survey/public/data/exp2_items_new.json`

**Contents**:
- 200 items (40% of 500 AMT samples)
- Qwen: 166 items (84 B-category, 82 D-category)
- Step1X: 34 items (24 B-category, 10 D-category)
- FLUX: 0 items (no preserved images available)

---

## Key Statistics

### Items by Model
| Model | Total | Category B | Category D | % of AMT Samples |
|-------|-------|------------|------------|------------------|
| Qwen | 166 | 84 | 82 | 100% (with preserved) |
| Step1X | 34 | 24 | 10 | 20% (with preserved) |
| FLUX | 0 | 0 | 0 | 0% (no preserved) |
| **TOTAL** | **200** | **108** | **92** | **40%** |

### Prompts Covered
- **Total**: 20 unique prompts
- **B-category**: B01, B02, B03, B04, B05, B06, B07, B08, B09, B10
- **D-category**: D01, D02, D03, D04, D05, D06, D07, D08, D09, D10

---

## Usage

### Regenerate

```bash
python3 survey/scripts/generate_exp2_items_new.py
```

### Verify

```bash
# Basic verification
python3 survey/scripts/verify_exp2_items.py

# Full verification (also checks source/edited images)
python3 survey/scripts/verify_exp2_items.py --check-all
```

---

## Deployment Steps

### 1. Copy Preserved Images

```bash
# Create directories
mkdir -p survey/public/images/exp2_preserved/qwen
mkdir -p survey/public/images/exp2_preserved/step1x

# Copy images (from Downloads to survey)
cp /Users/chan/Downloads/exp2_pairwise/qwen/preserved/*.png \
   survey/public/images/exp2_preserved/qwen/

cp /Users/chan/Downloads/exp2_pairwise/step1x/preserved/*.png \
   survey/public/images/exp2_preserved/step1x/
```

### 2. Update Survey App

Choose your integration strategy:

**Option A: Replace current file (not recommended)**
```bash
cd survey/public/data
mv exp2_items.json exp2_items_old.json
cp exp2_items_new.json exp2_items.json
```

**Option B: Use alongside (recommended)**
- Keep both `exp2_items.json` (961 items) and `exp2_items_new.json` (200 items)
- Update survey code to load `exp2_items_new.json` for AMT tasks
- Use `exp2_items.json` for full dataset browsing

### 3. Test

1. Start dev server: `npm run dev`
2. Navigate to Exp2 page
3. Verify all images load correctly

---

## Item Structure

Each item contains 3 image URLs:

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

---

## Documentation Files

### Quick Reference
- **[QUICK_START_EXP2.md](QUICK_START_EXP2.md)** - Commands and quick info
- **[EXP2_FILE_STRUCTURE.txt](EXP2_FILE_STRUCTURE.txt)** - File locations and structure

### Detailed Information
- **[EXP2_GENERATION_SUMMARY.md](EXP2_GENERATION_SUMMARY.md)** - Generation statistics
- **[EXP2_ITEMS_NEW_README.md](EXP2_ITEMS_NEW_README.md)** - Comprehensive guide

### Scripts
- **[generate_exp2_items_new.py](generate_exp2_items_new.py)** - Generation script
- **[verify_exp2_items.py](verify_exp2_items.py)** - Verification script

---

## Validation Status

✅ **All Checks Passed**

- [x] JSON structure valid
- [x] Total items: 200
- [x] All required fields present
- [x] All preserved images exist (200/200)
- [x] No duplicates
- [x] Consistent naming convention
- [x] URLs match file structure

---

## File Sizes

| File | Size |
|------|------|
| `exp2_items_new.json` | 101 KB |
| `exp2_items.json` (old) | 521 KB |
| `generate_exp2_items_new.py` | 4.0 KB |
| `verify_exp2_items.py` | 6.7 KB |

---

## Comparison: Old vs New

| Metric | Old File | New File |
|--------|----------|----------|
| Total Items | 961 | 200 |
| Experiment ID | exp2_pairwise_comparison | exp2_pairwise_new |
| Source | All generated images | AMT-sampled only |
| Models | flux, qwen, step1x | qwen, step1x |
| Purpose | Full dataset | AMT evaluation |
| Preserved Images | Not verified | All verified ✓ |

---

## Why This Approach?

1. **Quality over Quantity**: 200 high-quality AMT-sampled items vs 961 unsampled items
2. **Verified Images**: All preserved images confirmed to exist
3. **Representative**: Maintains demographic balance from AMT sampling
4. **Practical**: Focuses on models with preserved images (qwen, step1x)
5. **Traceable**: Direct mapping to AMT sampling data

---

## Troubleshooting

### Issue: JSON file not found
**Solution**: Run generation script
```bash
python3 survey/scripts/generate_exp2_items_new.py
```

### Issue: Verification fails
**Solution**: Check specific errors in output
```bash
python3 survey/scripts/verify_exp2_items.py
```

### Issue: Images not loading
**Solution**:
1. Verify preserved images copied to `survey/public/images/exp2_preserved/`
2. Check browser console for 404 errors
3. Confirm URL paths match file structure

### Issue: Need to regenerate
**Solution**: Simply re-run the generator
```bash
python3 survey/scripts/generate_exp2_items_new.py
python3 survey/scripts/verify_exp2_items.py  # verify after
```

---

## Contact & Support

For questions or issues:
1. Check [QUICK_START_EXP2.md](QUICK_START_EXP2.md) for common tasks
2. See [EXP2_GENERATION_SUMMARY.md](EXP2_GENERATION_SUMMARY.md) for details
3. Review [EXP2_ITEMS_NEW_README.md](EXP2_ITEMS_NEW_README.md) for comprehensive info
4. Refer to main project docs in `CLAUDE.md`

---

**Last Updated**: January 18, 2026
**Version**: 1.0
**Maintainer**: Research Team
**Status**: ✅ Production Ready
