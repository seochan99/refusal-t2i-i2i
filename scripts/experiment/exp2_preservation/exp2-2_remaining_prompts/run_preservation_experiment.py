#!/usr/bin/env python3
"""
Experiment 2-2: Identity Preservation Evaluation (Remaining Prompts)
Uses AMT-sampled items directly - generates only items with remaining prompts

From 500 AMT sampled items:
- B01, B05, B09, D03 = 98 items (already done in exp2-1)
- Remaining 16 prompts = 402 items (to generate)

Per model:
- flux:   135 items
- qwen:   136 items
- step1x: 131 items
- Total:  402 items

Usage:
    python run_preservation_experiment.py --model flux --device cuda
    python run_preservation_experiment.py --model qwen --device cuda
    python run_preservation_experiment.py --model step1x --device cuda
"""

import os
os.environ["HF_HOME"] = "/scratch/chans/models/huggingface"
os.environ["HF_HUB_CACHE"] = "/scratch/chans/models/huggingface/hub"

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

from PIL import Image
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# AMT Sampled items
AMT_SAMPLED_FILE = PROJECT_ROOT / "data" / "amt_sampling" / "exp1_amt_sampled.json"

# Already completed prompts (from exp2-1)
COMPLETED_PROMPTS = ["B01", "B05", "B09", "D03"]


def load_tasks_for_model(model_name: str) -> List[Dict]:
    """Load tasks from AMT sampling for a specific model, excluding completed prompts."""
    if not AMT_SAMPLED_FILE.exists():
        print(f"ERROR: AMT sampled file not found: {AMT_SAMPLED_FILE}")
        sys.exit(1)

    with open(AMT_SAMPLED_FILE, "r") as f:
        data = json.load(f)

    tasks = []
    for item in data["items"]:
        # Filter by model
        if item["model"] != model_name:
            continue

        # Skip completed prompts
        if item["promptId"] in COMPLETED_PROMPTS:
            continue

        tasks.append({
            "id": item["id"],
            "prompt_id": item["promptId"],
            "category": item["category"],
            "race": item["race"],
            "gender": item["gender"],
            "age": item["age"],
            "source_url": item["sourceImageUrl"],  # e.g., /images/source/Black/Black_Female_20s.jpg
        })

    return tasks


def load_identity_prompts(identity_prompts_file: Path) -> dict:
    """Load pre-extracted identity preservation prompts (from Gemini VLM)."""
    if not identity_prompts_file.exists():
        print(f"Warning: Identity prompts file not found: {identity_prompts_file}")
        return {}

    with open(identity_prompts_file, "r") as f:
        return json.load(f)


def load_prompt_texts() -> Dict[str, str]:
    """Load prompt texts from i2i_prompts.json"""
    prompts_file = PROJECT_ROOT / "data" / "prompts" / "i2i_prompts.json"
    if not prompts_file.exists():
        print(f"ERROR: Prompts file not found: {prompts_file}")
        sys.exit(1)

    with open(prompts_file, "r") as f:
        data = json.load(f)

    return {p["id"]: p["prompt"] for p in data["prompts"]}


def get_model(model_name: str, device: str):
    """Initialize model wrapper."""
    if model_name == "step1x":
        from src.models.step1x_wrapper import Step1XWrapper
        return Step1XWrapper(device=device, enable_thinking=False, enable_reflection=False)
    elif model_name == "flux":
        from src.models.flux_wrapper import FluxWrapper
        return FluxWrapper(device=device)
    elif model_name == "qwen":
        from src.models.qwen_wrapper import QwenImageEditWrapper
        return QwenImageEditWrapper(device=device)
    else:
        raise ValueError(f"Unknown model: {model_name}")


def run_preservation_experiment(
    model_name: str,
    device: str = "cuda",
    experiment_id: Optional[str] = None,
    resume_from: int = 0,
    output_dir: Optional[Path] = None,
    gender_filter: Optional[str] = None
):
    """
    Run Experiment 2-2: Generate images for AMT-sampled items (excluding completed prompts).
    """
    # Setup paths
    source_dir = PROJECT_ROOT / "data" / "source_images" / "final"

    # Find latest identity prompts file
    identity_prompts_dir = PROJECT_ROOT / "data" / "identity_prompts"
    identity_prompts_files = list(identity_prompts_dir.glob("identity_prompt_mapping*.json"))
    if identity_prompts_files:
        identity_prompts_file = sorted(identity_prompts_files, key=lambda x: x.stat().st_mtime)[-1]
    else:
        identity_prompts_file = identity_prompts_dir / "identity_prompt_mapping.json"

    # Output directory
    if output_dir is None:
        output_dir = PROJECT_ROOT / "data" / "results" / "exp2_pairwise" / model_name / "preserved"
    output_dir.mkdir(parents=True, exist_ok=True)

    if experiment_id is None:
        experiment_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("=" * 80)
    print(f"EXPERIMENT 2-2: Identity Preservation - {model_name.upper()}")
    print("=" * 80)
    print(f"Model: {model_name}")
    print(f"Device: {device}")
    print(f"Experiment ID: {experiment_id}")
    print(f"Output: {output_dir}")
    print(f"Skipping prompts: {COMPLETED_PROMPTS}")
    if gender_filter:
        print(f"Gender Filter: {gender_filter}")
    print("=" * 80)

    # Load prompt texts
    prompt_texts = load_prompt_texts()
    print(f"Loaded {len(prompt_texts)} prompt texts")

    # Load identity prompts
    identity_prompts = load_identity_prompts(identity_prompts_file)
    print(f"Loaded {len(identity_prompts)} identity prompts")

    # Load tasks for this model
    tasks = load_tasks_for_model(model_name)

    # Apply gender filter if specified
    if gender_filter:
        tasks = [t for t in tasks if t["gender"] == gender_filter]

    total_tasks = len(tasks)
    print(f"Total tasks for {model_name}: {total_tasks}")

    # Initialize model
    print(f"\nLoading {model_name} model...")
    model = get_model(model_name, device)
    model.load()
    print("Model loaded")

    # Run experiment
    results = []
    pbar = tqdm(total=total_tasks, desc=f"{model_name} (preserved)", initial=resume_from)

    current_prompt_id = None

    try:
        for idx, task in enumerate(tasks):
            if idx < resume_from:
                continue

            prompt_id = task["prompt_id"]
            image_key = f"{task['race']}_{task['gender']}_{task['age']}"

            # Get prompt text
            if prompt_id not in prompt_texts:
                tqdm.write(f"  ✗ Unknown prompt: {prompt_id}")
                continue
            base_prompt = prompt_texts[prompt_id]

            # Log when switching to a new prompt
            if prompt_id != current_prompt_id:
                current_prompt_id = prompt_id
                print(f"\n{'='*60}")
                print(f"[{prompt_id}] {base_prompt[:80]}...")
                print(f"{'='*60}")

            pbar.set_postfix_str(f"{prompt_id} | {image_key}")

            # Build final prompt with identity preservation suffix
            if image_key in identity_prompts:
                identity_suffix = identity_prompts[image_key]
                final_prompt = f"{base_prompt}. {identity_suffix}"
            else:
                final_prompt = base_prompt

            # Load source image
            source_path = source_dir / task["race"] / f"{image_key}.jpg"
            if not source_path.exists():
                tqdm.write(f"  ✗ Source not found: {source_path}")
                continue

            source_image = Image.open(source_path)

            try:
                result = model.edit(
                    source_image=source_image,
                    prompt=final_prompt,
                    num_inference_steps=50,
                    seed=42
                )

                if result.success and result.output_image:
                    output_filename = f"{prompt_id}_{image_key}.png"
                    output_path = output_dir / output_filename
                    result.output_image.save(output_path)

                    results.append({
                        "idx": idx,
                        "id": task["id"],
                        "prompt_id": prompt_id,
                        "image_key": image_key,
                        "race": task["race"],
                        "gender": task["gender"],
                        "age": task["age"],
                        "category": task["category"],
                        "condition": "preserved",
                        "status": "success",
                        "output_path": str(output_path),
                        "latency_ms": result.latency_ms,
                        "timestamp": datetime.now().isoformat()
                    })
                    tqdm.write(f"  ✓ [{idx+1}/{total_tasks}] {prompt_id}_{image_key} ({result.latency_ms:.0f}ms)")
                else:
                    results.append({
                        "idx": idx,
                        "id": task["id"],
                        "prompt_id": prompt_id,
                        "image_key": image_key,
                        "status": "failed",
                        "error": result.error_message or "Unknown error",
                        "timestamp": datetime.now().isoformat()
                    })
                    tqdm.write(f"  ✗ [{idx+1}/{total_tasks}] {prompt_id}_{image_key} FAILED")

            except Exception as e:
                results.append({
                    "idx": idx,
                    "id": task["id"],
                    "prompt_id": prompt_id,
                    "image_key": image_key,
                    "status": "error",
                    "error": str(e)[:200],
                    "timestamp": datetime.now().isoformat()
                })
                tqdm.write(f"  ✗ [{idx+1}/{total_tasks}] {prompt_id}_{image_key} ERROR: {str(e)[:50]}")

            pbar.update(1)

            # Checkpoint every 50 tasks
            if (idx + 1) % 50 == 0:
                checkpoint_file = output_dir / f"results_checkpoint_{experiment_id}.json"
                with open(checkpoint_file, "w") as f:
                    json.dump(results, f, indent=2)

    except KeyboardInterrupt:
        print(f"\nInterrupted at task {idx}")
        print(f"To resume: --resume-from {idx}")

    finally:
        pbar.close()

        # Save final results
        results_file = output_dir / f"results_exp2-2_{experiment_id}.json"
        with open(results_file, "w") as f:
            json.dump({
                "experiment_id": experiment_id,
                "experiment": "exp2-2_amt_sampled",
                "model": model_name,
                "condition": "preserved",
                "total_tasks": total_tasks,
                "completed": len(results),
                "success": sum(1 for r in results if r.get("status") == "success"),
                "skipped_prompts": COMPLETED_PROMPTS,
                "results": results
            }, f, indent=2)

        print(f"\nResults saved: {results_file}")

        success = sum(1 for r in results if r.get("status") == "success")
        print(f"\n{'='*80}")
        print(f"SUMMARY: {success}/{len(results)} successful" + (f" ({100*success/len(results):.1f}%)" if results else ""))
        print(f"{'='*80}")

        model.cleanup()

    return results


def main():
    parser = argparse.ArgumentParser(description="Experiment 2-2: AMT Sampled Identity Preservation")

    parser.add_argument("--model", type=str, required=True, choices=["step1x", "flux", "qwen"])
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--experiment-id", type=str, default=None)
    parser.add_argument("--resume-from", type=int, default=0)
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--gender", type=str, default=None, choices=["Female", "Male"])

    args = parser.parse_args()
    output_dir = Path(args.output_dir) if args.output_dir else None

    run_preservation_experiment(
        model_name=args.model,
        device=args.device,
        experiment_id=args.experiment_id,
        resume_from=args.resume_from,
        output_dir=output_dir,
        gender_filter=args.gender
    )


if __name__ == "__main__":
    main()
