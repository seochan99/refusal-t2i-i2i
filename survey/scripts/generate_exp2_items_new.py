#!/usr/bin/env python3
"""
Generate exp2_items_new.json from AMT sampling data.

This script creates Exp2 items (Source + Edited + Preserved comparison)
by matching AMT sampled items with available preserved images.
"""

import json
import os
from pathlib import Path
from collections import defaultdict

# Paths
AMT_SAMPLING_PATH = "/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/data/amt_sampling/exp1_amt_sampled.json"
PRESERVED_BASE_PATH = "/Users/chan/Downloads/exp2_pairwise"
OUTPUT_PATH = "/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/survey/public/data/exp2_items_new.json"


def check_preserved_image_exists(model: str, prompt_id: str, race: str, gender: str, age: str) -> bool:
    """
    Check if preserved image exists for given parameters.

    Args:
        model: Model name (qwen, step1x, flux)
        prompt_id: Prompt ID (e.g., B01)
        race: Race code (e.g., Latino)
        gender: Gender (Male/Female)
        age: Age code (e.g., 40s)

    Returns:
        True if preserved image exists, False otherwise
    """
    if model == "flux":
        # Skip flux for now (no preserved images available)
        return False

    preserved_path = Path(PRESERVED_BASE_PATH) / model / "preserved" / f"{prompt_id}_{race}_{gender}_{age}.png"
    return preserved_path.exists()


def generate_exp2_items():
    """Generate exp2_items_new.json from AMT sampling data."""

    # Read AMT sampling data
    print(f"Reading AMT sampling data from: {AMT_SAMPLING_PATH}")
    with open(AMT_SAMPLING_PATH, 'r') as f:
        amt_data = json.load(f)

    print(f"Total AMT items: {amt_data['total_items']}")

    # Process items
    exp2_items = []
    stats = defaultdict(int)
    skipped_stats = defaultdict(int)

    for item in amt_data['items']:
        model = item['model']
        prompt_id = item['promptId']
        race = item['race']
        gender = item['gender']
        age = item['age']
        category = item['category']
        category_name = item['categoryName']

        # Check if preserved image exists
        if not check_preserved_image_exists(model, prompt_id, race, gender, age):
            skipped_stats[model] += 1
            skipped_stats['total'] += 1
            continue

        # Create exp2 item
        exp2_item = {
            "id": f"exp2_{model}_{prompt_id}_{race}_{gender}_{age}",
            "model": model,
            "promptId": prompt_id,
            "category": category,
            "categoryName": category_name,
            "race": race,
            "gender": gender,
            "age": age,
            "sourceImageUrl": item['sourceImageUrl'],
            "editedImageUrl": item['outputImageUrl'],
            "preservedImageUrl": f"/images/exp2_preserved/{model}/{prompt_id}_{race}_{gender}_{age}.png"
        }

        exp2_items.append(exp2_item)
        stats[model] += 1
        stats['total'] += 1

    # Create output structure
    output_data = {
        "experiment": "exp2_pairwise_new",
        "description": "Source + Edited + Preserved comparison",
        "total_items": stats['total'],
        "items": exp2_items
    }

    # Save to file
    print(f"\nSaving to: {OUTPUT_PATH}")
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(output_data, f, indent=2)

    # Print statistics
    print("\n" + "="*60)
    print("GENERATION STATISTICS")
    print("="*60)
    print(f"\nTotal items generated: {stats['total']}")
    print("\nItems per model:")
    for model in ['qwen', 'step1x', 'flux']:
        if model in stats:
            print(f"  {model:10s}: {stats[model]:4d} items")

    print("\nSkipped items (no preserved image):")
    print(f"  Total skipped: {skipped_stats['total']}")
    for model in ['qwen', 'step1x', 'flux']:
        if model in skipped_stats:
            print(f"  {model:10s}: {skipped_stats[model]:4d} items")

    print("\n" + "="*60)
    print(f"Output saved to: {OUTPUT_PATH}")
    print("="*60)

    return output_data


if __name__ == "__main__":
    generate_exp2_items()
