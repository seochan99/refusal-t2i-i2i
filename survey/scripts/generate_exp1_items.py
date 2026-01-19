#!/usr/bin/env python3
"""Generate exp1_items.json for all models with local image paths."""

import json
import os
from pathlib import Path

BASE_DIR = Path("/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/survey/public/images")
OUTPUT_FILE = Path("/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/survey/public/data/exp1_items.json")

MODELS = ["flux", "qwen", "step1x"]
CATEGORIES = {
    "B_occupation": "B",
    "D_vulnerability": "D"
}

def parse_filename(filename):
    """Parse filename like B01_Black_Female_20s_success.png"""
    name = filename.replace(".png", "")
    # Remove suffix (_success, _unchanged, etc.)
    for suffix in ["_success", "_unchanged", "_partial", "_failed"]:
        name = name.replace(suffix, "")

    parts = name.split("_")
    if len(parts) >= 4:
        prompt_id = parts[0]
        race = parts[1]
        gender = parts[2]
        age = parts[3]
        return prompt_id, race, gender, age
    return None, None, None, None

def main():
    items = []

    for model in MODELS:
        exp1_dir = BASE_DIR / "exp1_sampling_b_d" / model
        if not exp1_dir.exists():
            print(f"Skipping {model}: directory not found at {exp1_dir}")
            continue

        # Iterate through category folders
        for cat_folder, cat_key in CATEGORIES.items():
            cat_dir = exp1_dir / cat_folder
            if not cat_dir.exists():
                print(f"  Skipping {model}/{cat_folder}: not found")
                continue

            # Process each image in the folder
            for img_file in sorted(cat_dir.glob("*.png")):
                prompt_id, race, gender, age = parse_filename(img_file.name)
                if not prompt_id:
                    continue

                # Build URLs
                output_url = f"/images/exp1_sampling_b_d/{model}/{cat_folder}/{img_file.name}"
                source_url = f"/images/source/{race}/{race}_{gender}_{age}.jpg"

                item = {
                    "id": f"exp1_{model}_{prompt_id}_{race}_{gender}_{age}",
                    "model": model,
                    "promptId": prompt_id,
                    "category": cat_key,
                    "categoryName": cat_folder,
                    "race": race,
                    "gender": gender,
                    "age": age,
                    "filename": img_file.name,
                    "sourceImageUrl": source_url,
                    "outputImageUrl": output_url
                }
                items.append(item)

    # Count per model
    model_counts = {}
    for item in items:
        m = item["model"]
        model_counts[m] = model_counts.get(m, 0) + 1

    output = {
        "experiment": "exp1_identity_drift",
        "description": "Evaluate edit quality, identity preservation, and attribute drift",
        "categories": ["B (Occupation)", "D (Vulnerability)"],
        "totalItems": len(items),
        "models": MODELS,
        "modelCounts": model_counts,
        "items": items
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Generated {len(items)} items")
    for m, c in model_counts.items():
        print(f"  {m}: {c}")
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
