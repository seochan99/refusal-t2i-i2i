#!/usr/bin/env python3
"""
Reorganize FLUX and Qwen results to match Step1X format.

Target structure:
  data/results/{model}/{experiment_id}/
  ├── images/{Race}/{PromptID}_{Race}_{Gender}_{Age}_{status}.png
  ├── config.json
  ├── results.json
  └── summary.json

Usage:
  python scripts/data/reorganize_model_results.py --flux /path/to/flux
  python scripts/data/reorganize_model_results.py --qwen /path/to/qwen
  python scripts/data/reorganize_model_results.py --all
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent.parent
TARGET_DIR = PROJECT_ROOT / "data" / "results"

RACES = ["Black", "EastAsian", "Indian", "Latino", "MiddleEastern", "SoutheastAsian", "White"]
CATEGORIES = ["A", "B", "C", "D", "E"]


def reorganize_flux(source_dir: Path, dry_run: bool = False):
    """
    Reorganize FLUX results from category-based to unified structure.

    Source: flux/catA/images/{Race}/, flux/catB/images/{Race}/, ...
    Target: data/results/flux/{exp_id}/images/{Race}/
    """
    print("=" * 60)
    print("Reorganizing FLUX Results")
    print("=" * 60)

    source_dir = Path(source_dir)
    if not source_dir.exists():
        print(f"ERROR: Source directory not found: {source_dir}")
        return False

    # Create experiment ID from earliest config
    exp_id = None
    for cat in CATEGORIES:
        config_file = source_dir / f"cat{cat}" / "config.json"
        if config_file.exists():
            with open(config_file) as f:
                config = json.load(f)
                if "experiment_id" in config:
                    exp_id = config["experiment_id"]
                    break

    if not exp_id:
        exp_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    target_dir = TARGET_DIR / "flux" / exp_id
    images_dir = target_dir / "images"

    print(f"Source: {source_dir}")
    print(f"Target: {target_dir}")
    print(f"Experiment ID: {exp_id}")

    if not dry_run:
        images_dir.mkdir(parents=True, exist_ok=True)
        for race in RACES:
            (images_dir / race).mkdir(exist_ok=True)

    # Merge all results.json files
    all_results = []
    all_configs = []
    stats = defaultdict(int)

    # Copy images and collect results
    for cat in CATEGORIES:
        cat_dir = source_dir / f"cat{cat}"
        if not cat_dir.exists():
            print(f"  SKIP: cat{cat} not found")
            continue

        # Load results
        results_file = cat_dir / "results.json"
        if results_file.exists():
            with open(results_file) as f:
                results = json.load(f)
                all_results.extend(results)
                print(f"  cat{cat}: {len(results)} results loaded")

        # Load config
        config_file = cat_dir / "config.json"
        if config_file.exists():
            with open(config_file) as f:
                all_configs.append(json.load(f))

        # Copy images
        cat_images = cat_dir / "images"
        if cat_images.exists():
            for race in RACES:
                race_dir = cat_images / race
                if not race_dir.exists():
                    continue

                for img_file in race_dir.glob("*.png"):
                    target_file = images_dir / race / img_file.name
                    stats[f"cat{cat}"] += 1
                    stats["total"] += 1

                    if not dry_run:
                        if not target_file.exists():
                            shutil.copy2(img_file, target_file)

    # Update output paths in results
    for r in all_results:
        if "output_image" in r and r["output_image"]:
            old_path = Path(r["output_image"])
            race = r.get("race_code", "Unknown")
            new_path = str(images_dir / race / old_path.name)
            r["output_image"] = new_path

    # Save merged results
    if not dry_run:
        # Results
        with open(target_dir / "results.json", "w") as f:
            json.dump(all_results, f, indent=2)

        # Config (merged)
        merged_config = {
            "experiment_name": "i2i_refusal_bias",
            "experiment_id": exp_id,
            "model_name": "flux",
            "source_configs": all_configs
        }
        with open(target_dir / "config.json", "w") as f:
            json.dump(merged_config, f, indent=2)

        # Summary
        summary = {
            "experiment_id": exp_id,
            "model_name": "flux",
            "total_results": len(all_results),
            "total_images": stats["total"],
            "by_category": {f"cat{c}": stats[f"cat{c}"] for c in CATEGORIES},
            "reorganized_at": datetime.now().isoformat()
        }
        with open(target_dir / "summary.json", "w") as f:
            json.dump(summary, f, indent=2)

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Summary:")
    print(f"  Total images: {stats['total']}")
    for cat in CATEGORIES:
        print(f"  cat{cat}: {stats[f'cat{cat}']}")
    print(f"  Results: {len(all_results)}")
    print(f"  Output: {target_dir}")

    return True


def reorganize_qwen(source_dir: Path, dry_run: bool = False):
    """
    Reorganize Qwen results (already in good format, just copy).

    Source: results_qwen/qwen/{exp_id}/images/{Race}/
    Target: data/results/qwen/{exp_id}/images/{Race}/
    """
    print("=" * 60)
    print("Reorganizing Qwen Results")
    print("=" * 60)

    source_dir = Path(source_dir)
    if not source_dir.exists():
        print(f"ERROR: Source directory not found: {source_dir}")
        return False

    # Find experiment directory
    qwen_dir = source_dir / "qwen" if (source_dir / "qwen").exists() else source_dir

    # Find experiment ID folder
    exp_dirs = [d for d in qwen_dir.iterdir() if d.is_dir() and d.name[0].isdigit()]
    if not exp_dirs:
        print(f"ERROR: No experiment directories found in {qwen_dir}")
        return False

    exp_dir = exp_dirs[0]  # Use first experiment
    exp_id = exp_dir.name

    target_dir = TARGET_DIR / "qwen" / exp_id

    print(f"Source: {exp_dir}")
    print(f"Target: {target_dir}")
    print(f"Experiment ID: {exp_id}")

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)

    stats = defaultdict(int)

    # Copy images
    source_images = exp_dir / "images"
    if source_images.exists():
        for race in RACES:
            race_dir = source_images / race
            if not race_dir.exists():
                continue

            target_race_dir = target_dir / "images" / race
            if not dry_run:
                target_race_dir.mkdir(parents=True, exist_ok=True)

            for img_file in race_dir.glob("*.png"):
                stats[race] += 1
                stats["total"] += 1

                if not dry_run:
                    target_file = target_race_dir / img_file.name
                    if not target_file.exists():
                        shutil.copy2(img_file, target_file)

    # Copy metadata files
    for meta_file in ["config.json", "results.json", "summary.json"]:
        src = exp_dir / meta_file
        if src.exists() and not dry_run:
            shutil.copy2(src, target_dir / meta_file)

    # Copy logs
    logs_dir = exp_dir / "logs"
    if logs_dir.exists() and not dry_run:
        target_logs = target_dir / "logs"
        if not target_logs.exists():
            shutil.copytree(logs_dir, target_logs)

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Summary:")
    print(f"  Total images: {stats['total']}")
    for race in RACES:
        if stats[race] > 0:
            print(f"  {race}: {stats[race]}")
    print(f"  Output: {target_dir}")

    return True


def filter_bd_only(results_dir: Path):
    """
    Filter results to only include B and D categories.
    Creates a separate 'bd_only' folder with filtered data.
    """
    print("=" * 60)
    print("Filtering B/D Categories Only")
    print("=" * 60)

    for model in ["flux", "qwen", "step1x"]:
        model_dir = results_dir / model
        if not model_dir.exists():
            continue

        for exp_dir in model_dir.iterdir():
            if not exp_dir.is_dir():
                continue

            results_file = exp_dir / "results.json"
            if not results_file.exists():
                continue

            with open(results_file) as f:
                results = json.load(f)

            # Filter B and D only
            bd_results = [r for r in results if r.get("category") in ["B", "D"]]

            # Save filtered results
            bd_file = exp_dir / "results_bd_only.json"
            with open(bd_file, "w") as f:
                json.dump(bd_results, f, indent=2)

            print(f"  {model}/{exp_dir.name}: {len(bd_results)}/{len(results)} (B+D only)")


def main():
    parser = argparse.ArgumentParser(description="Reorganize model results")
    parser.add_argument("--flux", type=str, help="Path to FLUX results")
    parser.add_argument("--qwen", type=str, help="Path to Qwen results")
    parser.add_argument("--all", action="store_true", help="Process all with default paths")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--filter-bd", action="store_true", help="Filter B/D categories only")
    args = parser.parse_args()

    if args.all:
        args.flux = "/Users/chan/Downloads/flux"
        args.qwen = "/Users/chan/Downloads/results_qwen"

    if args.flux:
        reorganize_flux(Path(args.flux), dry_run=args.dry_run)
        print()

    if args.qwen:
        reorganize_qwen(Path(args.qwen), dry_run=args.dry_run)
        print()

    if args.filter_bd:
        filter_bd_only(TARGET_DIR)

    if not any([args.flux, args.qwen, args.filter_bd]):
        parser.print_help()


if __name__ == "__main__":
    main()
