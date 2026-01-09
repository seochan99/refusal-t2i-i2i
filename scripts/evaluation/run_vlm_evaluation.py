#!/usr/bin/env python3
"""
Run VLM Evaluation on Generated Images
Evaluates soft erasure using Qwen3-VL + Gemini ensemble

Usage:
    # Production (30B model - default)
    python scripts/evaluation/run_vlm_evaluation.py --results-dir data/results/flux/20260109_120000

    # Local testing (8B model)
    python scripts/evaluation/run_vlm_evaluation.py --results-dir data/results/flux/20260109_120000 --qwen-model 8B

    # Specific model only
    python scripts/evaluation/run_vlm_evaluation.py --model flux --qwen-model 30B
"""

import argparse
import json
from pathlib import Path
from PIL import Image
import sys
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.evaluation.vlm_evaluator import VLMEvaluator
from src.data.prompt_loader import PromptLoader


def evaluate_results(results_dir: Path, evaluator: VLMEvaluator, prompts_file: Path) -> dict:
    """Run VLM evaluation on experiment results."""

    # Load experiment results
    results_file = results_dir / "results.json"
    if not results_file.exists():
        print(f"Results file not found: {results_file}")
        return {}

    with open(results_file) as f:
        results = json.load(f)

    # Load prompts for attribute extraction
    prompt_loader = PromptLoader(str(prompts_file))

    print(f"Evaluating {len(results)} results...")

    evaluated_results = []
    for i, result in enumerate(results):
        # Skip if already refused or errored
        if result.get("is_refused") or result.get("error"):
            result["vlm_evaluation"] = None
            evaluated_results.append(result)
            continue

        # Load generated image
        image_path = results_dir / "images" / result.get("output_path", "")
        if not image_path.exists():
            print(f"  [{i+1}] Image not found: {image_path}")
            result["vlm_evaluation"] = None
            evaluated_results.append(result)
            continue

        try:
            image = Image.open(image_path)

            # Get attribute to check from prompt
            prompt_id = result.get("prompt_id", "")
            prompt_data = prompt_loader.get_prompt_by_id(prompt_id)
            attribute = prompt_data.get("attribute", prompt_data.get("text", ""))

            # Run VLM evaluation
            vlm_result = evaluator.check_attribute(
                image=image,
                attribute=attribute,
                return_detailed=True
            )

            result["vlm_evaluation"] = vlm_result
            result["is_erased"] = vlm_result["final_result"] in ["NO", "PARTIAL"]

            status = "ERASED" if result["is_erased"] else "PRESENT"
            consensus = "consensus" if vlm_result["consensus"] else "DISAGREE"
            print(f"  [{i+1}/{len(results)}] {prompt_id}: {status} ({consensus})")

        except Exception as e:
            print(f"  [{i+1}] Error evaluating {image_path}: {e}")
            result["vlm_evaluation"] = {"error": str(e)}

        evaluated_results.append(result)

    return evaluated_results


def main():
    parser = argparse.ArgumentParser(
        description="Run VLM evaluation on generated images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Production (30B model)
  python scripts/evaluation/run_vlm_evaluation.py --results-dir data/results/flux/20260109_120000

  # Local testing (8B model)
  python scripts/evaluation/run_vlm_evaluation.py --results-dir data/results/flux/20260109_120000 --qwen-model 8B

  # All results for a model
  python scripts/evaluation/run_vlm_evaluation.py --model flux
        """
    )
    parser.add_argument("--results-dir", type=str,
                       help="Specific experiment results directory")
    parser.add_argument("--model", type=str,
                       help="I2I model name (flux, step1x, qwen) - evaluates latest experiment")
    parser.add_argument("--qwen-model", type=str, default="30B", choices=["30B", "8B"],
                       help="Qwen VLM model size: 30B (default) or 8B")
    parser.add_argument("--prompts", type=str,
                       default="data/prompts/i2i_prompts.json",
                       help="Path to prompts JSON")
    parser.add_argument("--no-ensemble", action="store_true",
                       help="Use Qwen only (no Gemini ensemble)")
    parser.add_argument("--output", type=str,
                       help="Output file path (default: vlm_results.json in results dir)")

    args = parser.parse_args()

    # Determine results directory
    if args.results_dir:
        results_dir = Path(args.results_dir)
    elif args.model:
        base_dir = Path("data/results") / args.model
        if not base_dir.exists():
            print(f"Model directory not found: {base_dir}")
            sys.exit(1)
        # Get latest experiment
        exp_dirs = sorted(base_dir.glob("*/"), key=lambda x: x.name, reverse=True)
        if not exp_dirs:
            print(f"No experiments found in {base_dir}")
            sys.exit(1)
        results_dir = exp_dirs[0]
    else:
        print("Error: Either --results-dir or --model must be specified")
        sys.exit(1)

    print(f"Results directory: {results_dir}")
    print(f"Qwen model: {args.qwen_model}")
    print(f"Ensemble: {not args.no_ensemble}")
    print()

    # Initialize evaluator
    evaluator = VLMEvaluator(
        use_ensemble=not args.no_ensemble,
        qwen_model_size=args.qwen_model
    )

    # Run evaluation
    evaluated_results = evaluate_results(
        results_dir=results_dir,
        evaluator=evaluator,
        prompts_file=Path(args.prompts)
    )

    # Save results
    output_path = Path(args.output) if args.output else results_dir / "vlm_results.json"
    with open(output_path, "w") as f:
        json.dump(evaluated_results, f, indent=2, default=str)

    # Summary
    total = len(evaluated_results)
    erased = sum(1 for r in evaluated_results if r.get("is_erased"))
    refused = sum(1 for r in evaluated_results if r.get("is_refused"))
    needs_review = sum(1 for r in evaluated_results
                      if r.get("vlm_evaluation") and not r["vlm_evaluation"].get("consensus", True))

    print()
    print("=" * 50)
    print("VLM EVALUATION COMPLETE")
    print("=" * 50)
    print(f"Total:          {total}")
    print(f"Hard Refused:   {refused} ({refused/total*100:.1f}%)")
    print(f"Soft Erased:    {erased} ({erased/total*100:.1f}%)")
    print(f"Needs Review:   {needs_review} ({needs_review/total*100:.1f}%)")
    print(f"Results saved:  {output_path}")


if __name__ == "__main__":
    main()
