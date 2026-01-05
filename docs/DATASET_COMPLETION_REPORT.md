# Dataset Completion Report

**Project**: ACRB - Attribute-Conditioned Refusal Bias Framework
**Date**: 2025-12-30
**Status**: ✅ COMPLETE

## Summary

Successfully generated a comprehensive prompt dataset for evaluating attribute-conditioned refusal bias in T2I and I2I models for IJCAI-ECAI 2026 submission.

## Deliverables

### 1. Base Prompts Dataset
- **File**: `/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/data/prompts/base_prompts.json`
- **Count**: 108 prompts
- **Distribution**: 9 domains × 12 prompts each
- **Quality**: All benign, safety-adjacent content
- **Status**: ✅ Complete

### 2. Expanded Prompts Dataset
- **File**: `/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/data/prompts/expanded_prompts.json`
- **Count**: 2,592 prompts
- **Calculation**: 108 base × 24 attributes (1 neutral + 23 demographic)
- **Coverage**: 95.2% attribute marker presence
- **Status**: ✅ Complete

### 3. Attribute Definitions
- **File**: `/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/data/prompts/attributes.json`
- **Total Attributes**: 24 (including neutral)
- **Breakdown**:
  - Culture: 6 (Korean, Nigerian, Middle Eastern, South Asian, European, Latin American)
  - Gender: 3 (Male, Female, Non-binary)
  - Disability: 4 (Wheelchair user, Visually impaired, Hearing impaired, Limb difference)
  - Religion: 6 (Muslim, Jewish, Sikh, Hindu, Buddhist, Christian)
  - Age: 4 (Child, Young adult, Middle-aged, Elderly)
  - Neutral: 1
- **Status**: ✅ Complete

### 4. Updated Code
- **File**: `/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/acrb/prompt_generation/attribute_expansion.py`
- **Updates**: ATTRIBUTE_CATEGORIES updated with new definitions
- **Status**: ✅ Complete

### 5. Documentation
- **Files**:
  - `/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/data/prompts/README.md` (Full documentation)
  - `/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/data/prompts/dataset_stats.json` (Statistics)
- **Status**: ✅ Complete

## Dataset Characteristics

### Domain Distribution (9 domains, perfectly balanced)
```
violence_adjacent:          12 prompts (11.1%)
self_harm_adjacent:         12 prompts (11.1%)
substance_related:          12 prompts (11.1%)
privacy_sensitive:          12 prompts (11.1%)
religious_cultural:         12 prompts (11.1%)
body_appearance:            12 prompts (11.1%)
sexual_wellness:            12 prompts (11.1%)
copyright_violations:       12 prompts (11.1%)
unethical_unsafe_action:    12 prompts (11.1%)
```

### Attribute Distribution (perfectly balanced)
```
Culture (25.0%):        648 prompts (108 each × 6 cultures)
Religion (25.0%):       648 prompts (108 each × 6 religions)
Disability (16.7%):     432 prompts (108 each × 4 disabilities)
Age (16.7%):            432 prompts (108 each × 4 age groups)
Gender (12.5%):         324 prompts (108 each × 3 genders)
Neutral (4.2%):         108 prompts
```

## Quality Metrics

### Validation Results
✅ All prompts marked as benign (is_benign=true)
✅ No duplicate prompt IDs
✅ All base prompts have exactly 24 expansions
✅ 95.2% attribute marker coverage (2,365/2,484 attributed prompts)
✅ Balanced domain distribution (12 prompts each)
✅ Balanced attribute distribution (108 instances each)

### Coverage Analysis
- **Perfect Coverage**: 2,365 prompts (95.2%)
- **Missing Markers**: 119 prompts (4.8%) - primarily scene descriptions without people
- **Total Quality Score**: 95.2% ✅

## Scripts Generated

1. **generate_dataset_standalone.py** - Main dataset generation
2. **validate_prompts.py** - Comprehensive validation and analysis
3. **generate_final_dataset.py** - Final version with improved attribute insertion
4. **fix_expanded_prompts.py** - Intermediate fix script

## Usage Examples

### Load Dataset
```python
import json

with open('/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/data/prompts/expanded_prompts.json') as f:
    prompts = json.load(f)

# Filter by attribute
korean_prompts = [p for p in prompts if p['attribute_value'] == 'Korean']

# Filter by domain
violence_prompts = [p for p in prompts if p['domain'] == 'violence_adjacent']

# Get minimal pairs
base_id = 'BP_0001'
variations = [p for p in prompts if p['base_prompt_id'] == base_id]
```

### Experimental Setup
```python
# T2I Evaluation: Generate images for all 2,592 prompts
for prompt in prompts:
    image = model.generate(prompt['expanded_text'])
    refusal = detect_refusal(image)
    erasure = detect_attribute_erasure(image, prompt['attribute_marker'])

# I2I Evaluation: Edit 500 source images with 24 attribute variations
for source_image in source_images:
    for attribute in attributes:
        edited = model.edit(source_image, attribute_instruction)
        refusal = detect_refusal(edited)
        erasure = detect_attribute_erasure(edited, attribute)
```

## Expected Experimental Scale

### T2I Generation
- **Models**: 6 (DALL-E 3, Stable Diffusion 3, Flux.1, Midjourney, Firefly, Imagen 3)
- **Prompts per model**: 2,592
- **Total images**: 15,552
- **Estimated cost**: $100-150

### I2I Editing
- **Models**: 3 (InstructPix2Pix, Emu Edit, MGIE)
- **Source images**: 500 (250 FFHQ + 250 COCO)
- **Attributes per image**: 24
- **Total edits**: 36,000
- **Estimated cost**: $100-250

### Human Evaluation
- **Samples**: 150-200 pairs
- **Annotations**: 300-400
- **Estimated cost**: $75-225

### Total Budget: $275-625

## Next Steps

### Week 1: Data Collection (Complete ✅)
- [x] Generate base prompts (108)
- [x] Expand with attributes (2,592)
- [x] Validate dataset quality
- [x] Document dataset
- [ ] Download FFHQ subset (250 images)
- [ ] Download COCO subset (250 images)

### Week 2: Experiments
- [ ] Setup API access for 6 T2I models
- [ ] Run T2I generation (15,552 images)
- [ ] Setup I2I model pipelines
- [ ] Run I2I editing (36,000 edits)
- [ ] Automated refusal detection (VLM-based)
- [ ] Automated erasure detection (VLM-based)

### Week 3: Analysis & Writing
- [ ] Compute disparity metrics (Δ_refusal, Δ_erasure)
- [ ] Statistical significance testing
- [ ] Human evaluation (150-200 samples)
- [ ] Generate publication figures
- [ ] Write paper (7 pages + refs)
- [ ] Submit to IJCAI-ECAI 2026

## Files Generated

```
/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/
├── data/prompts/
│   ├── base_prompts.json              [108 prompts]
│   ├── expanded_prompts.json          [2,592 prompts]
│   ├── attributes.json                [24 attributes]
│   ├── dataset_stats.json             [statistics]
│   └── README.md                      [documentation]
├── scripts/
│   ├── generate_dataset_standalone.py [main generator]
│   ├── generate_final_dataset.py      [final version]
│   ├── validate_prompts.py            [validator]
│   └── fix_expanded_prompts.py        [fix script]
├── acrb/prompt_generation/
│   └── attribute_expansion.py         [updated attributes]
└── DATASET_COMPLETION_REPORT.md       [this file]
```

## Technical Notes

### Attribute Insertion Strategy

The dataset uses natural language insertion of demographic markers:

1. **Culture**: Prepends nationality/culture to person references
   - "A person" → "A Korean person"
   - "Student" → "Korean student"

2. **Gender**: Replaces neutral terms with gendered ones
   - "A person" → "A woman"
   - "Artist" → "Female artist"

3. **Disability**: Appends accessibility markers
   - "A person" → "A person in a wheelchair"
   - "Student" → "Student with a white cane"

4. **Religion**: Adds visible religious markers
   - "A person" → "A person wearing a hijab"
   - "Teacher" → "Teacher wearing a kippah"

5. **Age**: Modifies age descriptors
   - "A person" → "An elderly person"
   - "Student" → "Young student"

### Fallback Strategy

For prompts without person/role references (scenes, objects):
- Culture: Prepend cultural context or add ", {culture} cultural context"
- Gender: Add ", featuring a {gender}"
- Others: Add ", featuring a person {marker}"

## Known Limitations

1. **Missing Markers (4.8%)**: Some scene descriptions don't contain people and fallback additions may seem awkward
2. **Cultural Specificity**: Some activities may be culturally specific (e.g., "Korean traditional tea ceremony")
3. **Intersectionality**: Dataset tests one attribute at a time, not intersectional combinations

## Mitigation Strategies

1. Manual review of prompts with missing markers (optional)
2. Filter out awkward fallback prompts if needed
3. Future work: Intersectional attribute combinations

## Conclusion

✅ **Dataset generation is COMPLETE and ready for experimentation.**

The dataset provides a comprehensive, balanced, and well-documented foundation for evaluating attribute-conditioned refusal bias in T2I and I2I models. All deliverables have been generated, validated, and documented.

**Total Dataset Size**: 2,592 prompts across 9 domains with 24 attribute variations per base prompt.

**Quality Score**: 95.2% attribute coverage with perfect balance across domains and attributes.

**Next Action**: Download FFHQ and COCO source images to begin experimental phase.

---

**Generated**: 2025-12-30
**Author**: Claude Code (Sonnet 4.5)
**Project**: ACRB - IJCAI-ECAI 2026
