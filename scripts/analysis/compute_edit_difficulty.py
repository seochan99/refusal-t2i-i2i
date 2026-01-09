#!/usr/bin/env python3
"""
Compute edit-difficulty metrics between source and edited images.

This script does NOT modify results.json. It writes a parallel
edit_difficulty.json alongside the results file.

Metrics:
- L1 mean absolute difference (normalized 0-1)
- L2 mean squared error (normalized 0-1)
- PSNR (dB)
- SSIM (if scikit-image is available)
- Average-hash Hamming distance (0-1)
"""

import argparse
import json
from pathlib import Path
from typing import Optional
import math

import numpy as np
from PIL import Image

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import PathConfig


try:
    from skimage.metrics import structural_similarity as ssim
except Exception:
    ssim = None


def _resolve_output_image_path(
    output_image_path: Optional[str],
    results_dir: Path,
    race_code: Optional[str],
    images_root: Optional[Path] = None
) -> Optional[Path]:
    if not output_image_path:
        return None

    candidate = Path(output_image_path)
    if candidate.exists():
        return candidate

    images_root = images_root or (results_dir / "images")
    parts = candidate.parts
    if "images" in parts:
        idx = parts.index("images")
        rel = Path(*parts[idx + 1 :])
        candidate = images_root / rel
        if candidate.exists():
            return candidate

    if race_code:
        candidate = images_root / race_code / Path(output_image_path).name
        if candidate.exists():
            return candidate

    if images_root.exists():
        matches = list(images_root.rglob(Path(output_image_path).name))
        if len(matches) == 1:
            return matches[0]

    return None


def _resolve_source_image_path(
    source_image_path: Optional[str],
    race_code: Optional[str],
    source_images_root: Optional[Path] = None
) -> Optional[Path]:
    if not source_image_path:
        return None

    candidate = Path(source_image_path)
    if candidate.exists():
        return candidate

    source_images_root = source_images_root or PathConfig().source_images_base
    parts = candidate.parts
    if "source_images" in parts:
        idx = parts.index("source_images")
        rel = Path(*parts[idx + 1 :])
        candidate = source_images_root / rel
        if candidate.exists():
            return candidate

    if race_code:
        candidate = (source_images_root / "final") / race_code / Path(source_image_path).name
        if candidate.exists():
            return candidate

    return None


def _average_hash(image: Image.Image, hash_size: int = 8) -> np.ndarray:
    """Compute average hash bit array."""
    resized = image.convert("L").resize((hash_size, hash_size), Image.Resampling.LANCZOS)
    pixels = np.asarray(resized, dtype=np.float32)
    avg = pixels.mean()
    return (pixels > avg).astype(np.uint8)


def _compute_metrics(source: Image.Image, edited: Image.Image) -> dict:
    """Compute edit-difficulty metrics."""
    if source.size != edited.size:
        edited = edited.resize(source.size, Image.Resampling.LANCZOS)

    src_arr = np.asarray(source.convert("RGB"), dtype=np.float32) / 255.0
    edt_arr = np.asarray(edited.convert("RGB"), dtype=np.float32) / 255.0

    diff = src_arr - edt_arr
    l1 = float(np.mean(np.abs(diff)))
    l2 = float(np.mean(diff ** 2))

    if l2 == 0:
        psnr = float("inf")
    else:
        psnr = 10.0 * math.log10(1.0 / l2)

    ssim_score = None
    if ssim is not None:
        ssim_score = float(
            ssim(
                (src_arr * 255).astype(np.uint8),
                (edt_arr * 255).astype(np.uint8),
                channel_axis=2
            )
        )

    ah_src = _average_hash(source)
    ah_edt = _average_hash(edited)
    hash_diff = float(np.mean(ah_src != ah_edt))

    return {
        "l1_mean": l1,
        "l2_mean": l2,
        "psnr": psnr,
        "ssim": ssim_score,
        "hash_diff": hash_diff
    }


def main():
    parser = argparse.ArgumentParser(
        description="Compute edit-difficulty metrics for an experiment folder"
    )
    parser.add_argument("--results-dir", type=str, required=True,
                       help="Experiment directory containing results.json")
    parser.add_argument("--images-root", type=str,
                       help="Override images root directory (default: results_dir/images)")
    parser.add_argument("--source-images-root", type=str,
                       help="Override source images root (default: data/source_images)")
    parser.add_argument("--output", type=str,
                       help="Output file (default: results_dir/edit_difficulty.json)")
    parser.add_argument("--max-items", type=int,
                       help="Optional cap on number of items to process")
    parser.add_argument("--overwrite", action="store_true",
                       help="Overwrite output if it already exists")

    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    results_file = results_dir / "results.json"
    if not results_file.exists():
        raise FileNotFoundError(f"results.json not found: {results_file}")

    output_path = Path(args.output) if args.output else results_dir / "edit_difficulty.json"
    if output_path.exists() and not args.overwrite:
        raise FileExistsError(f"Output already exists: {output_path} (use --overwrite)")

    images_root = Path(args.images_root) if args.images_root else None
    source_images_root = Path(args.source_images_root) if args.source_images_root else None

    with results_file.open() as f:
        results = json.load(f)

    items = []
    processed = 0
    skipped = 0

    for row in results:
        if args.max_items and processed >= args.max_items:
            break

        output_path_resolved = _resolve_output_image_path(
            output_image_path=row.get("output_image"),
            results_dir=results_dir,
            race_code=row.get("race_code"),
            images_root=images_root
        )
        source_path_resolved = _resolve_source_image_path(
            source_image_path=row.get("source_image"),
            race_code=row.get("race_code"),
            source_images_root=source_images_root
        )

        if not output_path_resolved or not source_path_resolved:
            skipped += 1
            continue

        if not output_path_resolved.exists() or not source_path_resolved.exists():
            skipped += 1
            continue

        source_img = Image.open(source_path_resolved)
        edited_img = Image.open(output_path_resolved)

        metrics = _compute_metrics(source_img, edited_img)
        items.append({
            "request_idx": row.get("request_idx"),
            "prompt_id": row.get("prompt_id"),
            "race_code": row.get("race_code"),
            "output_image": row.get("output_image"),
            "source_image": row.get("source_image"),
            "metrics": metrics
        })
        processed += 1

    payload = {
        "results_dir": str(results_dir),
        "processed": processed,
        "skipped": skipped,
        "metrics": items
    }

    with output_path.open("w") as f:
        json.dump(payload, f, indent=2)

    print(f"Saved edit difficulty metrics to: {output_path}")
    print(f"Processed: {processed}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
