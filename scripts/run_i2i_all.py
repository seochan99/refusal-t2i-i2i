#!/usr/bin/env python3
"""
ACRB I2I Full Experiment Runner

Runs I2I experiments on models with I2I support (5 models).
Paper: IJCAI-ECAI 2026

Usage:
    # Run all I2I models with FFHQ dataset
    python scripts/run_i2i_all.py --dataset data/ffhq

    # Run only closed source models
    python scripts/run_i2i_all.py --closed-only --dataset data/ffhq

    # Run only open source models
    python scripts/run_i2i_all.py --open-only --dataset data/ffhq
"""

import argparse
import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import subprocess

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from acrb.config import MODELS, get_refusal_threshold


# I2I capable models (from config)
I2I_CLOSED_MODELS = ['gpt_image_1_5', 'imagen_3', 'seedream_4_5']
I2I_OPEN_MODELS = ['flux_2_dev', 'qwen_image_edit_2511', 'step1x_edit']


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run I2I experiments on all supported models"
    )
    parser.add_argument(
        "--dataset", type=str, required=True,
        help="Path to source images (FFHQ or COCO)"
    )
    parser.add_argument(
        "--samples", type=int, default=100,
        help="Number of source images to use (default: 100)"
    )
    parser.add_argument(
        "--closed-only", action="store_true",
        help="Run only closed source models"
    )
    parser.add_argument(
        "--open-only", action="store_true",
        help="Run only open source models"
    )
    parser.add_argument(
        "--models", type=str, nargs="+", default=None,
        help="Specific models to run"
    )
    parser.add_argument(
        "--llm", type=str, default="gemini-2.0-flash",
        help="LLM for dynamic prompt expansion"
    )
    parser.add_argument(
        "--output", type=str, default="experiments/results/i2i",
        help="Output directory"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed"
    )
    parser.add_argument(
        "--skip-existing", action="store_true",
        help="Skip models that already have results"
    )
    parser.add_argument(
        "--visibility-filter", action="store_true", default=True,
        help="Apply MediaPipe visibility filtering for disability markers"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print commands without executing"
    )
    return parser.parse_args()


def get_i2i_model_list(args) -> List[str]:
    """Get list of I2I models to run."""
    if args.models:
        # Validate models have I2I support
        valid = []
        for m in args.models:
            if MODELS['t2i'].get(m, {}).get('i2i_support', False):
                valid.append(m)
            else:
                print(f"WARNING: {m} does not support I2I, skipping")
        return valid
    elif args.closed_only:
        return I2I_CLOSED_MODELS
    elif args.open_only:
        return I2I_OPEN_MODELS
    else:
        return I2I_CLOSED_MODELS + I2I_OPEN_MODELS


def check_dataset(dataset_path: str) -> Dict:
    """Check dataset availability and count images."""
    path = Path(dataset_path)
    if not path.exists():
        return {"exists": False, "error": f"Path not found: {dataset_path}"}

    # Count images
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    images = [f for f in path.iterdir() if f.suffix.lower() in image_extensions]

    return {
        "exists": True,
        "path": str(path.absolute()),
        "image_count": len(images),
        "sample_files": [str(f.name) for f in images[:5]]
    }


def run_single_model(
    model: str,
    dataset: str,
    samples: int,
    llm: str,
    output_dir: str,
    seed: int,
    visibility_filter: bool,
    dry_run: bool = False
) -> Dict:
    """Run I2I experiment for a single model."""

    model_config = MODELS['t2i'].get(model, {})
    threshold = get_refusal_threshold(model)

    cmd = [
        "python", "scripts/run_audit.py",
        "--model", model.replace('_', '-'),
        "--mode", "i2i",
        "--dataset", dataset,
        "--samples", str(samples),
        "--llm", llm,
        "--refusal-threshold", str(threshold),
        "--output", output_dir,
        "--seed", str(seed),
    ]

    print(f"\n{'='*60}")
    print(f"Running I2I experiment: {model}")
    print(f"  Type: {model_config.get('type', 'unknown')}")
    print(f"  Dataset: {dataset}")
    print(f"  Samples: {samples}")
    print(f"  Visibility Filter: {visibility_filter}")
    print(f"{'='*60}")

    if dry_run:
        print(f"  Command: {' '.join(cmd)}")
        return {"model": model, "status": "dry_run", "command": cmd}

    start_time = time.time()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10800  # 3 hour timeout for I2I
        )

        elapsed = time.time() - start_time

        if result.returncode == 0:
            print(f"  Status: SUCCESS ({elapsed:.1f}s)")
            return {
                "model": model,
                "status": "success",
                "elapsed_seconds": elapsed
            }
        else:
            print(f"  Status: FAILED ({elapsed:.1f}s)")
            print(f"  Error: {result.stderr[-500:] if result.stderr else 'Unknown'}")
            return {
                "model": model,
                "status": "failed",
                "elapsed_seconds": elapsed,
                "error": result.stderr[-1000:] if result.stderr else ""
            }

    except subprocess.TimeoutExpired:
        print(f"  Status: TIMEOUT (>3h)")
        return {"model": model, "status": "timeout"}
    except Exception as e:
        print(f"  Status: ERROR - {e}")
        return {"model": model, "status": "error", "error": str(e)}


def main():
    args = parse_args()

    print("\n" + "="*70)
    print("   ACRB I2I Full Experiment Runner")
    print("   IJCAI-ECAI 2026")
    print("="*70)

    # Check dataset
    dataset_info = check_dataset(args.dataset)
    if not dataset_info["exists"]:
        print(f"\nERROR: {dataset_info['error']}")
        sys.exit(1)

    print(f"\nDataset: {dataset_info['path']}")
    print(f"  Images found: {dataset_info['image_count']}")
    print(f"  Sample files: {dataset_info['sample_files']}")

    if dataset_info['image_count'] < args.samples:
        print(f"\nWARNING: Requested {args.samples} samples but only {dataset_info['image_count']} available")
        args.samples = dataset_info['image_count']

    # Get models
    models = get_i2i_model_list(args)
    print(f"\nI2I Models to run ({len(models)}):")
    for m in models:
        model_type = "closed" if m in I2I_CLOSED_MODELS else "open"
        print(f"  - {m} ({model_type})")

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run experiments
    results = []
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    for i, model in enumerate(models):
        print(f"\n[{i+1}/{len(models)}] Processing {model}...")

        # Skip if results exist
        if args.skip_existing:
            model_output = output_dir / model.replace('_', '-')
            if model_output.exists() and any(model_output.iterdir()):
                print(f"  Skipping {model} - results exist")
                results.append({"model": model, "status": "skipped", "reason": "existing_results"})
                continue

        result = run_single_model(
            model=model,
            dataset=args.dataset,
            samples=args.samples,
            llm=args.llm,
            output_dir=str(output_dir),
            seed=args.seed,
            visibility_filter=args.visibility_filter,
            dry_run=args.dry_run
        )
        results.append(result)

    # Save summary
    summary = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "mode": "i2i",
        "dataset": dataset_info,
        "samples_per_model": args.samples,
        "visibility_filter": args.visibility_filter,
        "models_run": len(models),
        "results": results
    }

    summary_path = output_dir / f"run_summary_{run_id}.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    # Print summary
    print("\n" + "="*70)
    print("   I2I EXPERIMENT SUMMARY")
    print("="*70)

    success = sum(1 for r in results if r['status'] == 'success')
    failed = sum(1 for r in results if r['status'] == 'failed')
    skipped = sum(1 for r in results if r['status'] == 'skipped')

    print(f"\nResults:")
    print(f"  Success: {success}/{len(models)}")
    print(f"  Failed:  {failed}/{len(models)}")
    print(f"  Skipped: {skipped}/{len(models)}")
    print(f"\nSummary saved to: {summary_path}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
