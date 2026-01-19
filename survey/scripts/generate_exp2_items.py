#!/usr/bin/env python3
"""Generate exp2_items.json for all models with local image paths."""

import json
import os
from pathlib import Path

BASE_DIR = Path("/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/survey/public/images")
OUTPUT_FILE = Path("/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/survey/public/data/exp2_items.json")

MODELS = ["flux", "qwen", "step1x"]
CATEGORIES = {
    "B01": {"category": "B", "categoryName": "B_occupation"},
    "B05": {"category": "B", "categoryName": "B_occupation"},
    "B09": {"category": "B", "categoryName": "B_occupation"},
    "D03": {"category": "D", "categoryName": "D_vulnerability"},
}

def parse_filename(filename):
    """Parse filename like B01_Black_Female_50s.png"""
    name = filename.replace(".png", "")
    parts = name.split("_")
    if len(parts) >= 4:
        prompt_id = parts[0]
        race = parts[1]
        gender = parts[2]
        age = parts[3]
        return prompt_id, race, gender, age
    return None, None, None, None

def find_edited_image(model, prompt_id, race, gender, age):
    """Find corresponding edited image from exp1_sampling_b_d."""
    category_folder = "B_occupation" if prompt_id.startswith("B") else "D_vulnerability"
    exp1_dir = BASE_DIR / "exp1_sampling_b_d" / model / category_folder

    if not exp1_dir.exists():
        return None

    # Look for matching edited file (success or unchanged status)
    pattern = f"{prompt_id}_{race}_{gender}_{age}_"
    for f in exp1_dir.glob(f"{pattern}*.png"):
        return f"/images/exp1_sampling_b_d/{model}/{category_folder}/{f.name}"

    return None

def main():
    items = []

    for model in MODELS:
        pairwise_dir = BASE_DIR / "exp2_pairwise" / model
        if not pairwise_dir.exists():
            print(f"Skipping {model}: directory not found")
            continue

        # Iterate through prompt folders
        for prompt_dir in sorted(pairwise_dir.iterdir()):
            if not prompt_dir.is_dir() or not prompt_dir.name.startswith("preserved_"):
                continue

            prompt_id = prompt_dir.name.replace("preserved_", "")
            if prompt_id not in CATEGORIES:
                continue

            cat_info = CATEGORIES[prompt_id]

            # Process each image in the folder
            for img_file in sorted(prompt_dir.glob("*.png")):
                parsed_prompt_id, race, gender, age = parse_filename(img_file.name)
                if not race:
                    continue

                # Build URLs
                preserved_url = f"/images/exp2_pairwise/{model}/preserved_{prompt_id}/{img_file.name}"
                source_url = f"/images/source/{race}/{race}_{gender}_{age}.jpg"
                edited_url = find_edited_image(model, prompt_id, race, gender, age)

                item = {
                    "id": f"exp2_{model}_{prompt_id}_{race}_{gender}_{age}",
                    "model": model,
                    "promptId": prompt_id,
                    "category": cat_info["category"],
                    "categoryName": cat_info["categoryName"],
                    "race": race,
                    "gender": gender,
                    "age": age,
                    "sourceImageUrl": source_url,
                    "preservedImageUrl": preserved_url,
                    "editedImageUrl": edited_url,
                    "hasEditedPair": edited_url is not None
                }
                items.append(item)

    # Count per model
    model_counts = {}
    for item in items:
        m = item["model"]
        model_counts[m] = model_counts.get(m, 0) + 1

    output = {
        "experiment": "exp2_pairwise_comparison",
        "description": "Pairwise A/B comparison: preserved vs edited images for identity preservation evaluation",
        "purpose": "Evaluate which image better preserves the original person's identity after editing",
        "targetPrompts": ["B01", "B05", "B09", "D03"],
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
