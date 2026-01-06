#!/usr/bin/env python3
"""
ACRB T2I Full Experiment Runner

Runs T2I experiments on all 7 models (3 closed + 4 open source).
Paper: IJCAI-ECAI 2026

Usage:
    # Run all models
    python scripts/run_t2i_all.py

    # Run only closed source models
    python scripts/run_t2i_all.py --closed-only

    # Run only open source models
    python scripts/run_t2i_all.py --open-only

    # Custom sample size
    python scripts/run_t2i_all.py --samples 50
"""

import argparse
import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import subprocess

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from acrb.config import MODELS, DATASET_CONFIG, get_refusal_threshold


# Model groups
CLOSED_MODELS = ['gpt_image_1_5', 'imagen_3', 'seedream_4_5']
# T2I capable open source models (excludes I2I-only models like step1x_edit, qwen_image_edit)
OPEN_MODELS = ['flux_2_dev', 'sd_3_5_large']


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run T2I experiments on all models"
    )
    parser.add_argument(
        "--samples", type=int, default=100,
        help="Number of base prompts per model (default: 100)"
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
        help="Specific models to run (overrides --closed-only/--open-only)"
    )
    parser.add_argument(
        "--llm", type=str, default="gemini-2.0-flash",
        help="LLM for dynamic prompt expansion"
    )
    parser.add_argument(
        "--output", type=str, default="experiments/results/t2i",
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
        "--parallel", type=int, default=1,
        help="Number of parallel processes (default: 1)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print commands without executing"
    )
    return parser.parse_args()


def get_model_list(args) -> List[str]:
    """Get list of models to run based on arguments."""
    if args.models:
        return args.models
    elif args.closed_only:
        return CLOSED_MODELS
    elif args.open_only:
        return OPEN_MODELS
    else:
        return CLOSED_MODELS + OPEN_MODELS


def check_api_keys(models: List[str]) -> Dict[str, bool]:
    """Check if required API keys are available."""
    api_status = {}

    for model in models:
        if model in CLOSED_MODELS:
            if model == 'gpt_image_1_5':
                api_status[model] = bool(os.getenv('OPENAI_API_KEY'))
            elif model == 'imagen_3':
                api_status[model] = bool(os.getenv('GOOGLE_API_KEY'))
            elif model == 'seedream_4_5':
                api_status[model] = bool(os.getenv('BYTEPLUS_API_KEY'))
        else:
            # Open source models don't need API keys (use local inference)
            api_status[model] = True

    return api_status


def run_single_model(
    model: str,
    samples: int,
    llm: str,
    output_dir: str,
    seed: int,
    dry_run: bool = False
) -> Dict:
    """Run experiment for a single model."""

    model_config = MODELS['t2i'].get(model, {})
    threshold = get_refusal_threshold(model)

    cmd = [
        "python", "scripts/run_audit.py",
        "--model", model.replace('_', '-'),
        "--mode", "t2i",
        "--samples", str(samples),
        "--llm", llm,
        "--refusal-threshold", str(threshold),
        "--output", output_dir,
        "--seed", str(seed),
    ]

    print(f"\n{'='*60}")
    print(f"Running T2I experiment: {model}")
    print(f"  Type: {model_config.get('type', 'unknown')}")
    print(f"  Samples: {samples}")
    print(f"  Threshold: {threshold}")
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
            timeout=7200  # 2 hour timeout
        )

        elapsed = time.time() - start_time

        if result.returncode == 0:
            print(f"  Status: SUCCESS ({elapsed:.1f}s)")
            return {
                "model": model,
                "status": "success",
                "elapsed_seconds": elapsed,
                "stdout": result.stdout[-1000:] if result.stdout else ""
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
        print(f"  Status: TIMEOUT (>2h)")
        return {"model": model, "status": "timeout"}
    except Exception as e:
        print(f"  Status: ERROR - {e}")
        return {"model": model, "status": "error", "error": str(e)}


def main():
    args = parse_args()

    print("\n" + "="*70)
    print("   ACRB T2I Full Experiment Runner")
    print("   IJCAI-ECAI 2026")
    print("="*70)

    models = get_model_list(args)
    print(f"\nModels to run ({len(models)}):")
    for m in models:
        model_type = "closed" if m in CLOSED_MODELS else "open"
        print(f"  - {m} ({model_type})")

    # Check API keys
    api_status = check_api_keys(models)
    missing_keys = [m for m, ok in api_status.items() if not ok]
    if missing_keys:
        print(f"\nWARNING: Missing API keys for: {missing_keys}")
        print("  Set environment variables:")
        print("  - OPENAI_API_KEY for gpt_image_1_5")
        print("  - GOOGLE_API_KEY for imagen_3")
        print("  - BYTEPLUS_API_KEY for seedream_4_5")

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run experiments
    results = []
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    for i, model in enumerate(models):
        print(f"\n[{i+1}/{len(models)}] Processing {model}...")

        # Skip if missing API key
        if not api_status.get(model, True):
            print(f"  Skipping {model} - missing API key")
            results.append({"model": model, "status": "skipped", "reason": "missing_api_key"})
            continue

        # Skip if results exist
        if args.skip_existing:
            model_output = output_dir / model.replace('_', '-')
            if model_output.exists() and any(model_output.iterdir()):
                print(f"  Skipping {model} - results exist")
                results.append({"model": model, "status": "skipped", "reason": "existing_results"})
                continue

        result = run_single_model(
            model=model,
            samples=args.samples,
            llm=args.llm,
            output_dir=str(output_dir),
            seed=args.seed,
            dry_run=args.dry_run
        )
        results.append(result)

    # Save summary
    summary = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "mode": "t2i",
        "samples_per_model": args.samples,
        "models_run": len(models),
        "results": results
    }

    summary_path = output_dir / f"run_summary_{run_id}.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    # Print summary
    print("\n" + "="*70)
    print("   EXPERIMENT SUMMARY")
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
