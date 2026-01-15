#!/usr/bin/env python3
"""
Upload FLUX and Qwen results to S3 in the same structure as Step1X.

S3 Structure:
  s3://i2i-refusal/{model}/
  ├── by_category/
  │   ├── A_neutral/
  │   ├── B_occupation/
  │   ├── C_cultural/
  │   ├── D_vulnerability/
  │   └── E_harmful/
  ├── by_race/
  │   ├── Black/
  │   ├── EastAsian/
  │   └── ...
  └── metadata/
      ├── results.json
      └── summary.json

Usage:
  python scripts/data/upload_to_s3.py --model flux
  python scripts/data/upload_to_s3.py --model qwen
  python scripts/data/upload_to_s3.py --all
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent.parent
RESULTS_DIR = PROJECT_ROOT / "data" / "results"

S3_BUCKET = "s3://i2i-refusal"

CATEGORY_NAMES = {
    "A": "A_neutral",
    "B": "B_occupation",
    "C": "C_cultural",
    "D": "D_vulnerability",
    "E": "E_harmful"
}

RACES = ["Black", "EastAsian", "Indian", "Latino", "MiddleEastern", "SoutheastAsian", "White"]


def organize_for_s3(model: str, source_dir: Path, output_dir: Path):
    """Organize images into S3 structure locally before upload."""

    print(f"Organizing {model} for S3...")

    images_dir = source_dir / "images"
    if not images_dir.exists():
        print(f"ERROR: Images directory not found: {images_dir}")
        return False

    # Create output directories
    by_category = output_dir / "by_category"
    by_race = output_dir / "by_race"
    metadata = output_dir / "metadata"

    for cat_code, cat_name in CATEGORY_NAMES.items():
        (by_category / cat_name).mkdir(parents=True, exist_ok=True)

    for race in RACES:
        (by_race / race).mkdir(parents=True, exist_ok=True)

    metadata.mkdir(parents=True, exist_ok=True)

    # Copy images to both structures
    stats = defaultdict(int)

    for race in RACES:
        race_dir = images_dir / race
        if not race_dir.exists():
            continue

        for img_file in race_dir.glob("*.png"):
            # Parse filename: {PromptID}_{Race}_{Gender}_{Age}_{status}.png
            parts = img_file.stem.split("_")
            if len(parts) < 5:
                continue

            prompt_id = parts[0]
            category = prompt_id[0]  # A, B, C, D, E

            if category not in CATEGORY_NAMES:
                continue

            cat_name = CATEGORY_NAMES[category]

            # Create symlinks (to save space) or copy
            cat_target = by_category / cat_name / img_file.name
            race_target = by_race / race / img_file.name

            if not cat_target.exists():
                os.link(img_file, cat_target)  # Hard link to save space
                stats[f"cat_{category}"] += 1

            if not race_target.exists():
                os.link(img_file, race_target)
                stats[f"race_{race}"] += 1

    # Copy metadata
    for meta_file in ["results.json", "summary.json", "config.json", "results_bd_only.json"]:
        src = source_dir / meta_file
        if src.exists():
            import shutil
            shutil.copy2(src, metadata / meta_file)

    print(f"  Categories: {sum(v for k, v in stats.items() if k.startswith('cat_'))}")
    print(f"  Races: {sum(v for k, v in stats.items() if k.startswith('race_'))}")

    return True


def upload_to_s3(model: str, local_dir: Path, dry_run: bool = False):
    """Upload organized directory to S3."""

    s3_path = f"{S3_BUCKET}/{model}/"

    print(f"\nUploading {model} to {s3_path}...")

    cmd = [
        "aws", "s3", "sync",
        str(local_dir),
        s3_path,
        "--exclude", ".DS_Store",
        "--exclude", "*.pyc",
    ]

    if dry_run:
        cmd.append("--dryrun")

    print(f"  Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"  SUCCESS: {model} uploaded to S3")
        if result.stdout:
            # Count uploaded files
            lines = result.stdout.strip().split('\n')
            print(f"  Files: {len([l for l in lines if l.strip()])}")
    else:
        print(f"  ERROR: {result.stderr}")
        return False

    return True


def process_model(model: str, dry_run: bool = False):
    """Process a single model: organize and upload."""

    # Find the model's results directory
    model_dir = RESULTS_DIR / model
    if not model_dir.exists():
        print(f"ERROR: Model directory not found: {model_dir}")
        return False

    # Find experiment directory (first one)
    exp_dirs = [d for d in model_dir.iterdir() if d.is_dir()]
    if not exp_dirs:
        print(f"ERROR: No experiment directories in {model_dir}")
        return False

    source_dir = exp_dirs[0]

    # Create organized output directory
    output_dir = RESULTS_DIR / f"{model}_s3_organized"

    print(f"\n{'='*60}")
    print(f"Processing {model}")
    print(f"{'='*60}")
    print(f"Source: {source_dir}")
    print(f"Output: {output_dir}")

    # Organize
    if not organize_for_s3(model, source_dir, output_dir):
        return False

    # Upload
    if not upload_to_s3(model, output_dir, dry_run=dry_run):
        return False

    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Upload model results to S3")
    parser.add_argument("--model", type=str, choices=["flux", "qwen"], help="Model to upload")
    parser.add_argument("--all", action="store_true", help="Upload all models")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--organize-only", action="store_true", help="Only organize, don't upload")
    args = parser.parse_args()

    models = []
    if args.all:
        models = ["flux", "qwen"]
    elif args.model:
        models = [args.model]
    else:
        parser.print_help()
        return

    for model in models:
        if args.organize_only:
            model_dir = RESULTS_DIR / model
            exp_dirs = [d for d in model_dir.iterdir() if d.is_dir()]
            if exp_dirs:
                output_dir = RESULTS_DIR / f"{model}_s3_organized"
                organize_for_s3(model, exp_dirs[0], output_dir)
        else:
            process_model(model, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
