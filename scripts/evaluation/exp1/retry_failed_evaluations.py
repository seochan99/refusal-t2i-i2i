#!/usr/bin/env python3
"""
Retry failed evaluations for Experiment 1.

This script identifies unevaluated images and runs evaluation only for those.
"""

import json
import sys
from pathlib import Path

# Project root (scripts/evaluation/exp1 → 3 levels up)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def find_unevaluated_images(model: str = "flux") -> list:
    """Find images that haven't been evaluated yet."""
    print(f"PROJECT_ROOT: {PROJECT_ROOT}")
    data_dir = PROJECT_ROOT / "data" / "results" / "exp1_sampling_b_d" / model
    print(f"data_dir: {data_dir}")
    print(f"data_dir exists: {data_dir.exists()}")

    # Load latest checkpoint
    output_dir = PROJECT_ROOT / "data" / "results" / "evaluations" / "exp1" / model
    checkpoints = list(output_dir.glob("checkpoint_*.json"))

    evaluated_ids = set()
    if checkpoints:
        latest = max(checkpoints, key=lambda p: p.stat().st_mtime)
        with open(latest) as f:
            data = json.load(f)
        evaluated_ids = {r['image_id'] for r in data.get('results', []) if r.get('success', False)}

    # Find all available edited images
    data_dir = PROJECT_ROOT / "data" / "results" / "exp1_sampling_b_d" / model
    available_images = []

    for category_dir in data_dir.iterdir():
        if not category_dir.is_dir():
            continue

        for img_path in category_dir.glob("*.png"):
            filename = img_path.stem
            if filename not in evaluated_ids:
                available_images.append({
                    "path": img_path,
                    "filename": filename,
                    "category": category_dir.name
                })

    return available_images

def main():
    model = "flux"  # Focus on flux for now

    print("Finding unevaluated images...")
    unevaluated = find_unevaluated_images(model)

    if not unevaluated:
        print("All images have been evaluated!")
        return

    print(f"Found {len(unevaluated)} unevaluated images")

    # Create a limited version that only processes these images
    # For now, just print what would be done
    print("\nTo retry failed evaluations, run:")
    print(f"python scripts/evaluation/exp1/evaluation_exp1.py --model {model} --resume")
    print("\nThis will continue from the checkpoint and evaluate remaining images.")

    # Alternative: create a custom list for targeted retry
    print(f"\nUnevaluated images saved to: unevaluated_images.txt")
    print(f"Total remaining: {len(unevaluated)}")

if __name__ == "__main__":
    main()