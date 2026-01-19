#!/usr/bin/env python3
"""
Generate exp2_items.json from exp1_amt_sampled.json.

Takes the 500 sampled items from exp1 and matches them with preserved images.
"""

import json
from pathlib import Path

# Configuration
BASE_DIR = Path("/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal")
SURVEY_DIR = BASE_DIR / "survey"
PUBLIC_DIR = SURVEY_DIR / "public"
IMAGES_DIR = PUBLIC_DIR / "images"

# Input: sampled items from exp1
SAMPLED_FILE = BASE_DIR / "data" / "amt_sampling" / "exp1_amt_sampled.json"

# Preserved images directory
EXP2_PRESERVED_DIR = IMAGES_DIR / "exp2_preserved"

def get_preserved_images():
    """Get all available preserved images by model."""
    preserved = {}

    for model_dir in EXP2_PRESERVED_DIR.iterdir():
        if not model_dir.is_dir():
            continue
        model = model_dir.name
        preserved[model] = set()

        for f in model_dir.glob("*.png"):
            # B01_Black_Female_20s.png -> B01_Black_Female_20s
            preserved[model].add(f.stem)

    return preserved

def main():
    print("=" * 60)
    print("Generating exp2_items.json from exp1_amt_sampled.json")
    print("=" * 60)

    # Load sampled items
    with open(SAMPLED_FILE) as f:
        sampled_data = json.load(f)

    sampled_items = sampled_data['items']
    print(f"\nLoaded {len(sampled_items)} sampled items from exp1")

    # Get available preserved images
    preserved = get_preserved_images()
    for model, images in preserved.items():
        print(f"  {model}: {len(images)} preserved images")

    # Match sampled items with preserved images
    exp2_items = []
    matched = 0
    missing = []

    for item in sampled_items:
        model = item['model']
        prompt_id = item['promptId']
        race = item['race']
        gender = item['gender']
        age = item['age']

        # Build preserved image key: B01_Black_Female_20s
        preserved_key = f"{prompt_id}_{race}_{gender}_{age}"

        # Check if preserved image exists
        if model in preserved and preserved_key in preserved[model]:
            exp2_item = {
                'id': f"exp2_{model}_{preserved_key}",
                'model': model,
                'promptId': prompt_id,
                'category': item['category'],
                'categoryName': item['categoryName'],
                'race': race,
                'gender': gender,
                'age': age,
                'sourceImageUrl': item['sourceImageUrl'],
                'editedImageUrl': item['outputImageUrl'],
                'preservedImageUrl': f"/images/exp2_preserved/{model}/{preserved_key}.png"
            }
            exp2_items.append(exp2_item)
            matched += 1
        else:
            missing.append({
                'model': model,
                'key': preserved_key,
                'original_id': item['id']
            })

    print(f"\n결과:")
    print(f"  매칭 성공: {matched}")
    print(f"  매칭 실패 (preserved 없음): {len(missing)}")

    # Show missing breakdown by model
    if missing:
        print(f"\n매칭 실패 내역:")
        missing_by_model = {}
        for m in missing:
            model = m['model']
            if model not in missing_by_model:
                missing_by_model[model] = []
            missing_by_model[model].append(m['key'])

        for model, keys in missing_by_model.items():
            print(f"  {model}: {len(keys)}개")
            # Show first 5
            for key in keys[:5]:
                print(f"    - {key}")
            if len(keys) > 5:
                print(f"    ... 외 {len(keys) - 5}개")

    # Create output
    output = {
        'experiment': 'exp2_amt_500',
        'description': 'Source + Edited + Preserved comparison based on exp1_amt_sampled.json',
        'total_items': len(exp2_items),
        'items_per_hit': 10,
        'total_hits': len(exp2_items) // 10,
        'matched_from_sampled': matched,
        'missing_preserved': len(missing),
        'items': exp2_items
    }

    # Write output
    output_path = PUBLIC_DIR / "data" / "exp2_items.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n저장 완료: {output_path}")
    print(f"총 아이템: {len(exp2_items)}")
    print(f"총 HIT 수: {len(exp2_items) // 10}")

    # Save missing list for reference
    if missing:
        missing_path = BASE_DIR / "data" / "amt_sampling" / "exp2_missing_preserved.json"
        with open(missing_path, 'w') as f:
            json.dump(missing, f, indent=2)
        print(f"\n미싱 리스트 저장: {missing_path}")

if __name__ == '__main__':
    main()
