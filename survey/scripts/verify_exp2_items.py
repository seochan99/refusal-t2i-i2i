#!/usr/bin/env python3
"""
Verify exp2_items_new.json integrity and image availability.

This script checks:
1. JSON structure validity
2. Required fields presence
3. Preserved image existence
4. Source image existence (optional)
5. Edited image existence (optional)
"""

import json
import os
from pathlib import Path
from collections import defaultdict
import argparse


def check_file_exists(path: str, base_path: str = "") -> bool:
    """Check if file exists, optionally with base path."""
    if base_path:
        full_path = Path(base_path) / path.lstrip('/')
    else:
        full_path = Path(path)
    return full_path.exists()


def verify_exp2_items(json_path: str, check_all_images: bool = False):
    """
    Verify exp2_items_new.json file.

    Args:
        json_path: Path to exp2_items_new.json
        check_all_images: If True, check source and edited images too
    """
    print("="*70)
    print("EXP2 ITEMS VERIFICATION")
    print("="*70)
    print(f"\nFile: {json_path}")

    # 1. Load and validate JSON
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        print("\n✓ JSON is valid")
    except json.JSONDecodeError as e:
        print(f"\n✗ JSON parsing error: {e}")
        return False
    except FileNotFoundError:
        print(f"\n✗ File not found: {json_path}")
        return False

    # 2. Check structure
    required_top_keys = ['experiment', 'description', 'total_items', 'items']
    missing_keys = [k for k in required_top_keys if k not in data]
    if missing_keys:
        print(f"\n✗ Missing top-level keys: {missing_keys}")
        return False
    print("✓ Top-level structure is valid")

    # 3. Check items count
    total_items = data['total_items']
    actual_items = len(data['items'])
    if total_items != actual_items:
        print(f"\n✗ Item count mismatch: declared={total_items}, actual={actual_items}")
        return False
    print(f"✓ Item count matches: {total_items} items")

    # 4. Check required fields in each item
    required_item_keys = [
        'id', 'model', 'promptId', 'category', 'categoryName',
        'race', 'gender', 'age',
        'sourceImageUrl', 'editedImageUrl', 'preservedImageUrl'
    ]

    print(f"\n{'Checking required fields in items...'}")
    errors = []
    for i, item in enumerate(data['items']):
        missing = [k for k in required_item_keys if k not in item]
        if missing:
            errors.append(f"  Item {i} ({item.get('id', 'NO_ID')}): missing {missing}")

    if errors:
        print(f"✗ Found {len(errors)} items with missing fields:")
        for err in errors[:10]:
            print(err)
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
        return False
    print("✓ All items have required fields")

    # 5. Check preserved images exist
    print("\nChecking preserved images...")
    preserved_base = "/Users/chan/Downloads/exp2_pairwise"
    missing_preserved = []

    for item in data['items']:
        model = item['model']
        prompt_id = item['promptId']
        race = item['race']
        gender = item['gender']
        age = item['age']

        preserved_path = Path(preserved_base) / model / "preserved" / f"{prompt_id}_{race}_{gender}_{age}.png"
        if not preserved_path.exists():
            missing_preserved.append(str(preserved_path))

    if missing_preserved:
        print(f"✗ Found {len(missing_preserved)} missing preserved images:")
        for path in missing_preserved[:5]:
            print(f"  - {path}")
        if len(missing_preserved) > 5:
            print(f"  ... and {len(missing_preserved) - 5} more")
        return False
    print(f"✓ All {total_items} preserved images exist")

    # 6. Optional: Check source and edited images
    if check_all_images:
        survey_public = Path(json_path).parent.parent / "images"
        print(f"\nChecking source images in {survey_public}...")

        missing_source = []
        missing_edited = []

        for item in data['items']:
            # Check source
            source_path = survey_public / item['sourceImageUrl'].lstrip('/')
            if not source_path.exists():
                missing_source.append(str(source_path))

            # Check edited
            edited_path = survey_public / item['editedImageUrl'].lstrip('/')
            if not edited_path.exists():
                missing_edited.append(str(edited_path))

        if missing_source:
            print(f"⚠ Found {len(missing_source)} missing source images")
        else:
            print("✓ All source images exist")

        if missing_edited:
            print(f"⚠ Found {len(missing_edited)} missing edited images")
        else:
            print("✓ All edited images exist")

    # 7. Statistics
    print("\n" + "="*70)
    print("STATISTICS")
    print("="*70)

    # Count by model
    model_count = defaultdict(int)
    for item in data['items']:
        model_count[item['model']] += 1

    print("\nItems by model:")
    for model in sorted(model_count.keys()):
        print(f"  {model:10s}: {model_count[model]:4d} items")

    # Count by category
    category_count = defaultdict(int)
    for item in data['items']:
        category_count[item['categoryName']] += 1

    print("\nItems by category:")
    for cat in sorted(category_count.keys()):
        print(f"  {cat:20s}: {category_count[cat]:4d} items")

    # Count by model and category
    model_category_count = defaultdict(lambda: defaultdict(int))
    for item in data['items']:
        model_category_count[item['model']][item['categoryName']] += 1

    print("\nItems by model and category:")
    for model in sorted(model_category_count.keys()):
        print(f"  {model}:")
        for cat in sorted(model_category_count[model].keys()):
            print(f"    {cat:20s}: {model_category_count[model][cat]:4d} items")

    # Unique prompts
    prompts = set(item['promptId'] for item in data['items'])
    print(f"\nUnique prompts: {len(prompts)}")
    print(f"  {sorted(prompts)}")

    print("\n" + "="*70)
    print("✅ VERIFICATION PASSED")
    print("="*70)

    return True


def main():
    parser = argparse.ArgumentParser(
        description='Verify exp2_items_new.json integrity'
    )
    parser.add_argument(
        '--file',
        default='/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/survey/public/data/exp2_items_new.json',
        help='Path to exp2_items_new.json'
    )
    parser.add_argument(
        '--check-all',
        action='store_true',
        help='Also check source and edited images (requires images in survey/public/images/)'
    )

    args = parser.parse_args()

    success = verify_exp2_items(args.file, args.check_all)

    exit(0 if success else 1)


if __name__ == "__main__":
    main()
