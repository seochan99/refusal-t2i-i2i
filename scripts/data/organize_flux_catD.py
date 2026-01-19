#!/usr/bin/env python3
"""
Organize Flux Category D images into flux_organized structure.

Source: /Users/chan/Downloads/flux/catD/images/{Race}/D*_{Race}_{Gender}_{Age}_{status}.png
Target: /Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/data/results/exp1_sampling/flux_organized/
        - by_race/{Race}/D*_...
        - by_category/D_vulnerability/D*_...
"""

import os
import shutil
from pathlib import Path

# Paths
SOURCE_DIR = Path("/Users/chan/Downloads/flux/catD/images")
TARGET_DIR = Path("/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/data/results/exp1_sampling/flux_organized")

# Race folders
RACES = ["Black", "EastAsian", "Indian", "Latino", "MiddleEastern", "SoutheastAsian", "White"]

def organize_catD():
    """Copy Category D images to flux_organized."""

    # Create target directories
    by_race_dir = TARGET_DIR / "by_race"
    by_category_dir = TARGET_DIR / "by_category" / "D_vulnerability"

    # Create D_vulnerability folder
    by_category_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created: {by_category_dir}")

    # Create by_race folders if they don't exist
    for race in RACES:
        race_dir = by_race_dir / race
        race_dir.mkdir(parents=True, exist_ok=True)

    # Count statistics
    copied_to_race = 0
    copied_to_category = 0
    skipped = 0

    # Process each race folder in source
    for race in RACES:
        source_race_dir = SOURCE_DIR / race
        if not source_race_dir.exists():
            print(f"Warning: Source race dir not found: {source_race_dir}")
            continue

        # Find all D*.png files
        for img_file in source_race_dir.glob("D*.png"):
            filename = img_file.name

            # Copy to by_race/{Race}/
            target_race_file = by_race_dir / race / filename
            if not target_race_file.exists():
                shutil.copy2(img_file, target_race_file)
                copied_to_race += 1
            else:
                skipped += 1

            # Copy to by_category/D_vulnerability/
            target_category_file = by_category_dir / filename
            if not target_category_file.exists():
                shutil.copy2(img_file, target_category_file)
                copied_to_category += 1

    print(f"\n=== Organization Complete ===")
    print(f"Copied to by_race: {copied_to_race}")
    print(f"Copied to by_category/D_vulnerability: {copied_to_category}")
    print(f"Skipped (already exists): {skipped}")

    # Verify counts
    race_total = sum(1 for f in by_race_dir.rglob("D*.png"))
    cat_total = sum(1 for f in by_category_dir.glob("D*.png"))
    print(f"\nVerification:")
    print(f"  D images in by_race/*: {race_total}")
    print(f"  D images in D_vulnerability: {cat_total}")

if __name__ == "__main__":
    organize_catD()
