#!/usr/bin/env python3
"""
Quick Test Script for I2I Models
Tests each model with 1 image × 1 prompt from each category (A-E)

Usage:
    python scripts/experiment/test/test_single_prompt.py --model flux
    python scripts/experiment/test/test_single_prompt.py --model step1x
    python scripts/experiment/test/test_single_prompt.py --model qwen
    python scripts/experiment/test/test_single_prompt.py --all  # Test all models
"""

import argparse
import json
from pathlib import Path
from datetime import datetime
from PIL import Image
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.config import PathConfig
from src.models import FluxWrapper, Step1XWrapper, QwenImageEditWrapper


def get_test_image(config: PathConfig) -> Path:
    """Get first available test image."""
    image_dir = config.source_images_dir
    for race_dir in sorted(image_dir.iterdir()):
        if race_dir.is_dir() and not race_dir.name.startswith('.'):
            for img in sorted(race_dir.glob("*.jpg")):
                return img
    raise FileNotFoundError("No test images found")


def get_test_prompts() -> list[dict]:
    """Get 1 prompt from each category (A-E)."""
    config = PathConfig()
    with open(config.prompts_file) as f:
        data = json.load(f)

    prompts = []
    seen_categories = set()
    for p in data["prompts"]:
        if p["category"] not in seen_categories:
            prompts.append(p)
            seen_categories.add(p["category"])
        if len(prompts) == 5:
            break
    return prompts


def test_model(model_name: str, device: str = "cuda"):
    """Test a single model with 5 prompts (1 per category)."""
    print(f"\n{'='*60}")
    print(f"Testing {model_name.upper()}")
    print(f"{'='*60}")

    config = PathConfig()
    test_image_path = get_test_image(config)
    test_prompts = get_test_prompts()

    print(f"Test image: {test_image_path.name}")
    print(f"Test prompts: {len(test_prompts)} (1 per category)")

    # Output directory
    output_dir = Path(__file__).parent / "outputs" / model_name / datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load model
    print(f"\nLoading {model_name} model...")
    try:
        if model_name == "flux":
            model = FluxWrapper(device=device)
        elif model_name == "step1x":
            model = Step1XWrapper(device=device)
        elif model_name == "qwen":
            model = QwenImageEditWrapper(device=device)
        else:
            raise ValueError(f"Unknown model: {model_name}")

        model.load()
        print(f"✓ Model loaded successfully")
    except Exception as e:
        print(f"✗ Failed to load model: {e}")
        return False

    # Load test image
    source_image = Image.open(test_image_path)
    print(f"✓ Image loaded: {source_image.size}")

    # Run tests
    results = []
    for i, prompt_data in enumerate(test_prompts):
        prompt_id = prompt_data["id"]
        category = prompt_data["category"]
        prompt = prompt_data["prompt"]

        print(f"\n[{i+1}/5] Category {category}: {prompt_id}")
        print(f"  Prompt: {prompt[:60]}...")

        try:
            result = model.edit(source_image, prompt)

            if result is not None:
                # Save output
                output_path = output_dir / f"{prompt_id}_{category}.png"
                result.save(output_path)
                print(f"  ✓ Success! Saved to {output_path.name}")
                results.append({"id": prompt_id, "category": category, "status": "success"})
            else:
                print(f"  ✗ Model returned None (possible refusal)")
                results.append({"id": prompt_id, "category": category, "status": "refusal"})

        except Exception as e:
            print(f"  ✗ Error: {e}")
            results.append({"id": prompt_id, "category": category, "status": "error", "error": str(e)})

    # Summary
    print(f"\n{'-'*40}")
    print(f"Results Summary for {model_name.upper()}:")
    success = sum(1 for r in results if r["status"] == "success")
    refusal = sum(1 for r in results if r["status"] == "refusal")
    error = sum(1 for r in results if r["status"] == "error")
    print(f"  Success: {success}/5")
    print(f"  Refusal: {refusal}/5")
    print(f"  Error: {error}/5")
    print(f"  Output: {output_dir}")

    # Save results
    with open(output_dir / "results.json", "w") as f:
        json.dump({"model": model_name, "results": results}, f, indent=2)

    # Cleanup
    model.unload()

    return error == 0


def main():
    parser = argparse.ArgumentParser(description="Quick test for I2I models")
    parser.add_argument("--model", choices=["flux", "step1x", "qwen"], help="Model to test")
    parser.add_argument("--all", action="store_true", help="Test all models")
    parser.add_argument("--device", default="cuda", help="Device (cuda/cpu/mps)")
    args = parser.parse_args()

    if not args.model and not args.all:
        parser.print_help()
        return

    print("="*60)
    print("I2I Model Quick Test")
    print("="*60)
    print(f"Device: {args.device}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    models_to_test = ["flux", "step1x", "qwen"] if args.all else [args.model]

    overall_results = {}
    for model_name in models_to_test:
        success = test_model(model_name, args.device)
        overall_results[model_name] = "PASS" if success else "FAIL"

    # Final summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    for model, status in overall_results.items():
        emoji = "✓" if status == "PASS" else "✗"
        print(f"  {emoji} {model.upper()}: {status}")


if __name__ == "__main__":
    main()
