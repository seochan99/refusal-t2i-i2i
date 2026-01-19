#!/usr/bin/env python3
"""Generate exp3_items.json for all models with local image paths."""

import json
from pathlib import Path

BASE_DIR = Path("/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/survey/public/images")
OUTPUT_FILE = Path("/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/survey/public/data/exp3_items.json")
PROMPTS_FILE = Path("/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/data/prompts/winobias_prompts_with_stereotype.json")

MODELS = ["flux", "qwen"]

def main():
    # Load prompts metadata (it's an array directly)
    with open(PROMPTS_FILE) as f:
        prompts_list = json.load(f)

    prompts_meta = {}
    for item in prompts_list:
        prompts_meta[item["id"]] = item

    items = []

    for model in MODELS:
        winobias_dir = BASE_DIR / "exp3_winobias" / model
        if not winobias_dir.exists():
            print(f"Skipping {model}: directory not found")
            continue

        # Process each image
        for img_file in sorted(winobias_dir.glob("*.png")):
            # Parse filename: prompt_001_20260115_144816.png
            name_parts = img_file.stem.split("_")
            if len(name_parts) < 2:
                continue

            try:
                prompt_num = int(name_parts[1])
            except ValueError:
                continue

            # Get prompt metadata
            meta = prompts_meta.get(prompt_num, {})

            # Build source image URLs (from metadata)
            input1 = meta.get("input_image_1", "").replace(".jpg", "")
            input2 = meta.get("input_image_2", "").replace(".jpg", "")

            # Parse input image format: "Black_Male_40s"
            def make_source_url(input_name):
                if not input_name:
                    return None
                parts = input_name.split("_")
                if len(parts) >= 1:
                    race = parts[0]
                    return f"/images/source/{race}/{input_name}.jpg"
                return None

            source1_url = make_source_url(input1)
            source2_url = make_source_url(input2)

            item = {
                "id": f"exp3_{model}_{prompt_num:03d}",
                "model": model,
                "promptId": prompt_num,
                "promptText": meta.get("prompt", ""),
                "stereotype": meta.get("gender_stereotype", ""),
                "inputImage1": input1,
                "inputImage2": input2,
                "filename": img_file.name,
                "outputImageUrl": f"/images/exp3_winobias/{model}/{img_file.name}",
                "sourceInput1Url": source1_url,
                "sourceInput2Url": source2_url
            }
            items.append(item)

    # Count per model
    model_counts = {}
    for item in items:
        m = item["model"]
        model_counts[m] = model_counts.get(m, 0) + 1

    output = {
        "experiment": "exp3_winobias_evaluation",
        "description": "WinoBias gender stereotype evaluation - determine if model preserved stereotype",
        "totalPrompts": 50,
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
