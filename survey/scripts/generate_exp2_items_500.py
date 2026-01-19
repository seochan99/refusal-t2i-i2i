#!/usr/bin/env python3
"""
Generate exp2_items.json with 500 items for AMT HIT evaluation.

Data sources:
- qwen: B01-B10, D01-D10 (20 prompts × 84 demographics = 1680, but we have ~472 preserved)
- step1x: B01, B05, B09, D03 (4 prompts × 84 demographics = 336, we have ~340)

We need to select 500 items total that have:
1. Source image
2. Edited image (from exp1_sampling_b_d)
3. Preserved image (from exp2_preserved)
"""

import json
import os
from pathlib import Path
from collections import defaultdict

# Configuration
SURVEY_DIR = Path("/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/survey")
PUBLIC_DIR = SURVEY_DIR / "public"
IMAGES_DIR = PUBLIC_DIR / "images"

# Image directories
SOURCE_DIR = IMAGES_DIR / "source"
EXP1_DIR = IMAGES_DIR / "exp1_sampling_b_d"
EXP2_PRESERVED_DIR = IMAGES_DIR / "exp2_preserved"

# Demographics
RACES = ['Black', 'EastAsian', 'Indian', 'Latino', 'MiddleEastern', 'SoutheastAsian', 'White']
GENDERS = ['Female', 'Male']
AGES = ['20s', '30s', '40s', '50s', '60s', '70plus']

# Categories
CATEGORIES = {
    'B': 'B_occupation',
    'D': 'D_vulnerability'
}

def get_preserved_images(model: str) -> dict:
    """Get all preserved images for a model."""
    preserved_dir = EXP2_PRESERVED_DIR / model
    images = {}

    if not preserved_dir.exists():
        print(f"Warning: {preserved_dir} does not exist")
        return images

    for f in preserved_dir.glob("*.png"):
        # Parse filename: B01_Black_Female_20s.png
        name = f.stem
        images[name] = f"/images/exp2_preserved/{model}/{f.name}"

    return images

def get_edited_images(model: str, category: str) -> dict:
    """Get all edited images for a model and category."""
    cat_name = CATEGORIES.get(category, f"{category}_unknown")
    edited_dir = EXP1_DIR / model / cat_name
    images = {}

    if not edited_dir.exists():
        print(f"Warning: {edited_dir} does not exist")
        return images

    for f in edited_dir.glob("*.png"):
        # Parse filename: B01_Black_Female_20s_success.png or B01_Black_Female_20s_unchanged.png
        name = f.stem
        # Remove _success or _unchanged suffix to get base name
        if name.endswith('_success') or name.endswith('_unchanged'):
            base_name = '_'.join(name.rsplit('_', 1)[:-1])
        else:
            base_name = name
        images[base_name] = f"/images/exp1_sampling_b_d/{model}/{cat_name}/{f.name}"

    return images

def get_source_image(race: str, gender: str, age: str) -> str:
    """Get source image path."""
    return f"/images/source/{race}/{race}_{gender}_{age}.jpg"

def parse_filename(filename: str) -> dict:
    """Parse preserved image filename into components."""
    # B01_Black_Female_20s
    parts = filename.split('_')
    if len(parts) < 4:
        return None

    prompt_id = parts[0]
    race = parts[1]
    gender = parts[2]
    age = parts[3]

    category = prompt_id[0]

    return {
        'promptId': prompt_id,
        'category': category,
        'race': race,
        'gender': gender,
        'age': age
    }

def generate_items():
    """Generate exp2 items list."""
    items = []

    # Process each model
    for model in ['qwen', 'step1x']:
        print(f"\nProcessing {model}...")

        # Get preserved images
        preserved = get_preserved_images(model)
        print(f"  Found {len(preserved)} preserved images")

        # Get edited images by category
        edited_b = get_edited_images(model, 'B')
        edited_d = get_edited_images(model, 'D')
        edited = {**edited_b, **edited_d}
        print(f"  Found {len(edited)} edited images")

        # Match preserved with edited
        matched = 0
        for preserved_name, preserved_url in preserved.items():
            parsed = parse_filename(preserved_name)
            if not parsed:
                continue

            # Check if we have corresponding edited image
            if preserved_name not in edited:
                continue

            edited_url = edited[preserved_name]
            source_url = get_source_image(parsed['race'], parsed['gender'], parsed['age'])

            item = {
                'id': f"exp2_{model}_{preserved_name}",
                'model': model,
                'promptId': parsed['promptId'],
                'category': parsed['category'],
                'categoryName': CATEGORIES.get(parsed['category'], parsed['category']),
                'race': parsed['race'],
                'gender': parsed['gender'],
                'age': parsed['age'],
                'sourceImageUrl': source_url,
                'editedImageUrl': edited_url,
                'preservedImageUrl': preserved_url
            }
            items.append(item)
            matched += 1

        print(f"  Matched {matched} items")

    return items

def balance_items(items: list, target: int = 500) -> list:
    """Balance items to reach target count with good distribution."""

    # Group by model
    by_model = defaultdict(list)
    for item in items:
        by_model[item['model']].append(item)

    print(f"\nItems by model:")
    for model, model_items in by_model.items():
        print(f"  {model}: {len(model_items)}")

    # Group by model and category
    by_model_cat = defaultdict(list)
    for item in items:
        key = (item['model'], item['category'])
        by_model_cat[key].append(item)

    print(f"\nItems by model and category:")
    for key, cat_items in sorted(by_model_cat.items()):
        print(f"  {key}: {len(cat_items)}")

    # For 500 items, we want balanced distribution
    # qwen: B01-B10, D01-D10 = 20 prompts
    # step1x: B01, B05, B09, D03 = 4 prompts

    # Strategy: Take all step1x items (they're fewer), fill rest with qwen
    selected = []

    # Take all step1x items first
    step1x_items = by_model['step1x']
    selected.extend(step1x_items)
    print(f"\nSelected all {len(step1x_items)} step1x items")

    # Need remaining from qwen
    remaining = target - len(selected)
    qwen_items = by_model['qwen']

    # Sort qwen items by prompt to get balanced distribution
    qwen_by_prompt = defaultdict(list)
    for item in qwen_items:
        qwen_by_prompt[item['promptId']].append(item)

    # Round-robin selection from each prompt
    qwen_selected = []
    prompts = sorted(qwen_by_prompt.keys())

    while len(qwen_selected) < remaining:
        added = False
        for prompt in prompts:
            if qwen_by_prompt[prompt] and len(qwen_selected) < remaining:
                qwen_selected.append(qwen_by_prompt[prompt].pop(0))
                added = True
        if not added:
            break

    selected.extend(qwen_selected)
    print(f"Selected {len(qwen_selected)} qwen items")

    # Sort final list for consistent ordering
    # Sort by: model, category, promptId, race, gender, age
    selected.sort(key=lambda x: (
        x['model'],
        x['category'],
        x['promptId'],
        RACES.index(x['race']) if x['race'] in RACES else 99,
        GENDERS.index(x['gender']) if x['gender'] in GENDERS else 99,
        AGES.index(x['age']) if x['age'] in AGES else 99
    ))

    return selected

def main():
    print("=" * 60)
    print("Generating exp2_items.json for AMT HIT evaluation")
    print("=" * 60)

    # Generate all available items
    items = generate_items()
    print(f"\nTotal available items: {len(items)}")

    # Balance to 500 items
    balanced = balance_items(items, target=500)
    print(f"\nFinal selected items: {len(balanced)}")

    # Verify distribution
    print("\nFinal distribution:")
    by_model = defaultdict(int)
    by_cat = defaultdict(int)
    by_model_cat = defaultdict(int)

    for item in balanced:
        by_model[item['model']] += 1
        by_cat[item['category']] += 1
        by_model_cat[(item['model'], item['category'])] += 1

    print(f"  By model: {dict(by_model)}")
    print(f"  By category: {dict(by_cat)}")
    print(f"  By model+category: {dict(by_model_cat)}")

    # Create output
    output = {
        'experiment': 'exp2_amt_500',
        'description': 'Source + Edited + Preserved comparison for AMT HIT evaluation',
        'total_items': len(balanced),
        'items_per_hit': 10,
        'total_hits': len(balanced) // 10,
        'items': balanced
    }

    # Write output
    output_path = PUBLIC_DIR / "data" / "exp2_items.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nWritten to: {output_path}")
    print(f"Total HITs: {len(balanced) // 10}")

if __name__ == '__main__':
    main()
