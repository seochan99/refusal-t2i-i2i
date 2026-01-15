#!/usr/bin/env python3
"""
Run WinoBias Gender Stereotype Experiment with Multi-Image I2I Models

Usage:
  python scripts/experiment/run_winobias_experiment.py \
    --model flux2 \
    --output-dir data/results/winobias/flux2 \
    --start-id 1 --end-id 50
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
import time
from PIL import Image

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.flux_wrapper import FluxWrapper
from src.models.qwen_wrapper import QwenImageEditWrapper
from src.models.step1x_wrapper import Step1XWrapper


def image_filename_to_path(filename: str, base_dir: Path) -> Path:
    """Convert image filename to full path."""
    # filename format: Race_Gender_Age.jpg (e.g., Black_Male_40s.jpg)
    parts = filename.replace('.jpg', '').split('_')
    if len(parts) < 3:
        raise ValueError(f"Invalid image filename: {filename}")
    race = parts[0]
    return base_dir / race / filename


def load_prompts(prompts_file: Path) -> list:
    """Load WinoBias prompts from JSON."""
    with open(prompts_file, 'r') as f:
        return json.load(f)


def run_experiment(args):
    """Run WinoBias experiment with specified model."""
    
    # Load prompts (new format: list of dicts with id, prompt, input_image_1, input_image_2)
    prompts = load_prompts(args.prompts_file)
    
    # Filter prompts by ID range
    prompts = [p for p in prompts if args.start_id <= p['id'] <= args.end_id]
    
    # Initialize model
    print(f"\n{'='*70}")
    print(f"WinoBias Gender Stereotype Experiment")
    print(f"{'='*70}")
    print(f"Model: {args.model}")
    print(f"Prompts: {args.start_id} to {args.end_id} ({len(prompts)} total)")
    print(f"Output directory: {args.output_dir}")
    print(f"{'='*70}\n")
    
    if args.model == "flux2":
        model = FluxWrapper(
            device=args.device,
            use_quantized=args.quantized,
            use_remote_text_encoder=args.remote_encoder
        )
    elif args.model == "qwen":
        model = QwenImageEditWrapper(device=args.device)
    elif args.model == "step1x":
        model = Step1XWrapper(
            device=args.device,
            enable_thinking=args.thinking,
            enable_reflection=args.reflection
        )
    else:
        raise ValueError(f"Unknown model: {args.model}")
    
    # Load model
    print("Loading model...")
    model.load()
    print("✓ Model loaded\n")
    
    # Setup output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Run experiments
    results = []
    success_count = 0
    error_count = 0
    
    for idx, prompt_entry in enumerate(prompts, 1):
        prompt_id = prompt_entry['id']
        prompt_text = prompt_entry['prompt']
        image_1_filename = prompt_entry['input_image_1']
        image_2_filename = prompt_entry['input_image_2']
        
        print(f"\n[{idx}/{len(prompts)}] Prompt {prompt_id}")
        print(f"  Text: {prompt_text}")
        print(f"  Image 1: {image_1_filename}")
        print(f"  Image 2: {image_2_filename}")
        
        try:
            # Load source images
            img_a_path = image_filename_to_path(image_1_filename, args.base_dir)
            img_b_path = image_filename_to_path(image_2_filename, args.base_dir)
            
            if not img_a_path.exists():
                raise FileNotFoundError(f"Image A not found: {img_a_path}")
            if not img_b_path.exists():
                raise FileNotFoundError(f"Image B not found: {img_b_path}")
            
            img_a = Image.open(img_a_path)
            img_b = Image.open(img_b_path)
            
            print(f"  ✓ Loaded images: {img_a_path.name}, {img_b_path.name}")
            
            # Run inference
            print(f"  Generating with {args.model}...", end=" ", flush=True)
            start_time = time.time()
            
            result = model.edit(
                source_image=[img_a, img_b],
                prompt=prompt_text,
                seed=args.seed,
                num_inference_steps=args.steps,
            )
            
            elapsed = time.time() - start_time
            
            if result.success:
                # Save output image
                output_filename = f"prompt_{prompt_id:03d}_{timestamp}.png"
                output_path = output_dir / output_filename
                result.output_image.save(output_path)
                
                print(f"✓ ({elapsed:.1f}s)")
                print(f"  Saved: {output_filename}")
                
                results.append({
                    "prompt_id": prompt_id,
                    "prompt": prompt_text,
                    "input_image_1": image_1_filename,
                    "input_image_2": image_2_filename,
                    "success": True,
                    "output_file": output_filename,
                    "latency_ms": result.latency_ms,
                    "elapsed_sec": elapsed
                })
                success_count += 1
            else:
                print(f"✗ FAILED")
                print(f"  Error: {result.error_message}")
                
                results.append({
                    "prompt_id": prompt_id,
                    "prompt": prompt_text,
                    "input_image_1": image_1_filename,
                    "input_image_2": image_2_filename,
                    "success": False,
                    "error": result.error_message,
                    "refusal_type": result.refusal_type.value,
                    "latency_ms": result.latency_ms
                })
                error_count += 1
        
        except Exception as e:
            print(f"✗ EXCEPTION: {e}")
            results.append({
                "prompt_id": prompt_id,
                "prompt": prompt_text,
                "input_image_1": image_1_filename,
                "input_image_2": image_2_filename,
                "success": False,
                "error": str(e)
            })
            error_count += 1
    
    # Save results
    results_file = output_dir / f"results_{args.model}_{timestamp}.json"
    with open(results_file, 'w') as f:
        json.dump({
            "model": args.model,
            "timestamp": timestamp,
            "total_prompts": len(prompts),
            "success_count": success_count,
            "error_count": error_count,
            "config": {
                "device": args.device,
                "steps": args.steps,
                "seed": args.seed,
                "quantized": args.quantized if args.model == "flux2" else None,
                "thinking": args.thinking if args.model == "step1x" else None,
                "reflection": args.reflection if args.model == "step1x" else None,
            },
            "results": results
        }, f, indent=2)
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"Experiment Complete")
    print(f"{'='*70}")
    print(f"Model: {args.model}")
    print(f"Total prompts: {len(prompts)}")
    print(f"Success: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Results saved: {results_file}")
    print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Run WinoBias experiment with multi-image I2I models"
    )
    
    # Model selection
    parser.add_argument(
        "--model",
        required=True,
        choices=["flux2", "qwen", "step1x"],
        help="Model to use for experiment"
    )
    
    # Input/Output
    parser.add_argument(
        "--prompts-file",
        default="data/prompts/winobias_prompts.json",
        help="Path to WinoBias prompts JSON"
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path("data/source_images/final"),
        help="Base directory for identity images"
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output directory for results"
    )
    
    # Experiment parameters
    parser.add_argument(
        "--start-id",
        type=int,
        default=1,
        help="First prompt ID to run"
    )
    parser.add_argument(
        "--end-id",
        type=int,
        default=50,
        help="Last prompt ID to run"
    )
    parser.add_argument(
        "--device",
        default="cuda",
        help="Device to run model on"
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=50,
        help="Number of inference steps"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed"
    )
    
    # Flux2-specific options
    parser.add_argument(
        "--quantized",
        action="store_true",
        help="Use 4-bit quantized Flux2 model"
    )
    parser.add_argument(
        "--remote-encoder",
        action="store_true",
        help="Use remote text encoder for Flux2"
    )
    
    # Step1X-specific options
    parser.add_argument(
        "--thinking",
        action="store_true",
        help="Enable thinking mode for Step1X"
    )
    parser.add_argument(
        "--reflection",
        action="store_true",
        help="Enable reflection mode for Step1X"
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    args.prompts_file = Path(args.prompts_file).resolve()
    args.base_dir = args.base_dir.resolve()
    args.output_dir = Path(args.output_dir).resolve()
    
    # Check files exist
    if not args.prompts_file.exists():
        print(f"Error: Prompts file not found: {args.prompts_file}")
        sys.exit(1)
    
    if not args.base_dir.exists():
        print(f"Error: Base directory not found: {args.base_dir}")
        sys.exit(1)
    
    run_experiment(args)


if __name__ == "__main__":
    main()
