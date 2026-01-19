#!/usr/bin/env python3
"""
Evaluate only White B_occupation images for FLUX.
Fork of evaluation_exp1.py - only runs missing White B evaluations.

Usage:
    python scripts/evaluation/exp1/evaluate_white_b.py --workers 10
"""

import json
import os
import sys
from pathlib import Path

# Import everything from the main evaluation script
sys.path.insert(0, str(Path(__file__).parent))
from evaluation_exp1 import (
    PROJECT_ROOT, DATA_DIR, SOURCE_DIR, OUTPUT_DIR,
    EvalStats, load_prompts, find_source_image,
    Exp1Evaluator, _generate_human_eval_summary,
    CATEGORY_B_PROMPTS, AGE_MAPPING
)

import argparse
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from PIL import Image
from tqdm import tqdm


def setup_logging(output_dir: Path):
    """Setup logging."""
    log_file = output_dir / f"evaluation_white_b_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def load_existing_evaluations(results_file: Path) -> set:
    """Load already evaluated White B image keys."""
    existing = set()
    if results_file.exists():
        with open(results_file) as f:
            for line in f:
                if line.strip():
                    try:
                        r = json.loads(line)
                        if r.get("race") == "White" and r.get("category") == "B_occupation":
                            key = f"{r['prompt_id']}_{r['race']}_{r['gender']}_{r['age']}"
                            existing.add(key)
                    except:
                        pass
    return existing


def find_white_b_images(existing_keys: set) -> list:
    """Find White B images that haven't been evaluated."""
    b_dir = DATA_DIR / "flux" / "B_occupation"
    images = []

    for img_path in b_dir.glob("B*_White_*.png"):
        filename = img_path.stem
        parts = filename.split("_")

        if len(parts) < 4:
            continue

        prompt_id = parts[0]
        if prompt_id not in CATEGORY_B_PROMPTS:
            continue

        # Handle status suffix
        status = "success"
        if parts[-1] in ["success", "unchanged", "failed"]:
            status = parts[-1]
            parts = parts[:-1]

        if len(parts) < 4:
            continue

        race = parts[1]  # White
        gender = parts[2]
        age = parts[3]

        # Skip if already evaluated
        key = f"{prompt_id}_{race}_{gender}_{age}"
        if key in existing_keys:
            continue

        images.append({
            "path": img_path,
            "filename": filename,
            "prompt_id": prompt_id,
            "category": "B_occupation",
            "race": race,
            "gender": gender,
            "age": age,
            "status": status
        })

    return images


def main():
    parser = argparse.ArgumentParser(description="Evaluate White B_occupation images for FLUX")
    parser.add_argument("--workers", type=int, default=5, help="Parallel workers")
    parser.add_argument("--limit", type=int, default=None, help="Limit images")
    args = parser.parse_args()

    # Setup
    output_dir = OUTPUT_DIR / "flux"
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = setup_logging(output_dir)

    # Load existing evaluations
    existing_results = output_dir / "exp1_flux_results.jsonl"
    existing_keys = load_existing_evaluations(existing_results)
    logger.info(f"Already evaluated: {len(existing_keys)} White B images")

    # Find images to evaluate
    images = find_white_b_images(existing_keys)
    logger.info(f"Found {len(images)} White B images to evaluate")

    if not images:
        logger.info("All White B images already evaluated!")
        return

    if args.limit:
        images = images[:args.limit]
        logger.info(f"Limited to {len(images)} images")

    # Load prompts
    prompts = load_prompts()
    if not prompts:
        logger.error("No prompts loaded!")
        return

    # Initialize
    stats = EvalStats()
    stats_lock = threading.Lock()
    results = []
    results_lock = threading.Lock()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    streaming_file = output_dir / f"white_b_{timestamp}.jsonl"

    logger.info("="*60)
    logger.info("WHITE B EVALUATION FOR FLUX")
    logger.info("="*60)
    logger.info(f"Images to evaluate: {len(images)}")
    logger.info(f"Workers: {args.workers}")
    logger.info(f"Output: {streaming_file}")
    logger.info("="*60)

    def process_image(img_info: dict) -> dict:
        """Process single image."""
        prompt_id = img_info["prompt_id"]
        race = img_info["race"]
        gender = img_info["gender"]
        age = img_info["age"]

        if prompt_id not in prompts:
            return None

        source_path = find_source_image(race, gender, age)
        if source_path is None:
            with stats_lock:
                stats.source_not_found += 1
            return None

        try:
            with Image.open(source_path) as src:
                source_img = src.convert("RGB").copy()
            with Image.open(img_info["path"]) as edt:
                edited_img = edt.convert("RGB").copy()

            evaluator = Exp1Evaluator(stats=stats, logger=logger, stats_lock=stats_lock)

            result = evaluator.evaluate(
                source_img=source_img,
                edited_img=edited_img,
                edit_prompt=prompts[prompt_id]["prompt"],
                race=race,
                gender=gender,
                age=age,
                prompt_id=prompt_id,
                prompts_config=prompts[prompt_id]
            )

            return {
                "image_id": img_info["filename"],
                "prompt_id": prompt_id,
                "category": img_info["category"],
                "race": race,
                "gender": gender,
                "age": age,
                "status": img_info["status"],
                "source_path": str(source_path),
                "edited_path": str(img_info["path"]),
                **result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            with stats_lock:
                stats.other_errors += 1
            logger.error(f"Error: {img_info['filename']}: {e}")
            return {
                "image_id": img_info["filename"],
                "prompt_id": prompt_id,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    # Run evaluation
    with open(streaming_file, "w", buffering=1) as stream_f:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(process_image, img): img for img in images}
            pbar = tqdm(as_completed(futures), total=len(images), desc="White B")

            for future in pbar:
                result = future.result()
                if result:
                    with results_lock:
                        results.append(result)
                        stream_f.write(json.dumps(result) + "\n")
                        stream_f.flush()

                        if result.get("success") and result.get("scores"):
                            scores = result["scores"]
                            pbar.set_postfix({
                                "edit": scores.get("edit_success", "?"),
                                "race": scores.get("race_drift", "?"),
                                "done": len(results)
                            })

    # Summary
    logger.info("")
    logger.info("="*60)
    logger.info("COMPLETED")
    logger.info("="*60)
    logger.info(f"Total: {stats.total}")
    logger.info(f"Successful: {stats.successful}")
    logger.info(f"Output: {streaming_file}")
    logger.info("")
    logger.info("To merge with main results:")
    logger.info(f"  cat {streaming_file} >> {existing_results}")


if __name__ == "__main__":
    main()
