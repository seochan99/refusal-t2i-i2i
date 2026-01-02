#!/usr/bin/env python3
"""
ACRB Audit CLI - Algorithm 1 Implementation

Professional entry point for running complete Attribute-Conditioned Refusal Bias audits
following the exact pipeline specified in Algorithm 1 of the paper.

Usage:
    # T2I audit with LLM-driven expansion
    python scripts/run_audit.py --model flux-2-dev --mode t2i --samples 100 --llm gemini-3-flash-preview

    # I2I audit with real FFHQ images
    python scripts/run_audit.py --model qwen-image-edit-2511 --mode i2i --dataset data/ffhq --samples 50

    # Quick test run (template-based, no LLM)
    python scripts/run_audit.py --model flux-2-dev --mode t2i --samples 5 --attributes culture gender
"""

import argparse
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from acrb.pipeline import ACRBPipeline, ACRBConfig


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="ACRB: Attribute-Conditioned Refusal Bias Audit (Algorithm 1)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full T2I audit with dynamic LLM expansion
  %(prog)s --model flux-2-dev --mode t2i --samples 100 --llm gemini-3-flash-preview

  # I2I audit with FFHQ source images
  %(prog)s --model qwen-image-edit-2511 --mode i2i --dataset /path/to/ffhq --samples 50

  # Quick test (5 base prompts, 2 attributes, no LLM)
  %(prog)s --model flux-2-dev --samples 5 --attributes culture gender

Output:
  Results are saved to experiments/results/{model}/{run_id}/ including:
    - stage1_prompts.json: All generated prompts
    - stage2_generation.json: Generation results
    - stage3_evaluation.json: Full evaluation with metrics
    - acrb_summary.json: Final disparity metrics
    - images/: All generated/edited images
        """
    )

    # Model configuration
    parser.add_argument(
        "--model",
        type=str,
        default="flux-2-dev",
        help="Model to audit (e.g., flux-2-dev, qwen-image-edit-2511, gpt-image-1.5)"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["t2i", "i2i"],
        default="t2i",
        help="Audit mode: t2i (Text-to-Image) or i2i (Image-to-Image)"
    )

    # Prompt generation
    parser.add_argument(
        "--samples",
        type=int,
        default=10,
        help="Number of base prompts to sample from 9 domains (default: 10)"
    )
    parser.add_argument(
        "--attributes",
        type=str,
        nargs="+",
        default=None,
        help="Attribute types to evaluate (default: all 5). Options: culture gender disability religion age"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )

    # LLM configuration (Stage I: Boundary Rephrasing + Attribute Expansion)
    parser.add_argument(
        "--llm",
        type=str,
        default=None,
        help="LLM model for dynamic prompt expansion (e.g., gemini-3-flash-preview, gpt-4o-mini). If not specified, uses template-based expansion."
    )
    parser.add_argument(
        "--llm-api-key",
        type=str,
        default=None,
        help="API key for LLM (defaults to ACRB_LLM_API_KEY env variable)"
    )
    parser.add_argument(
        "--llm-api-base",
        type=str,
        default="https://generativelanguage.googleapis.com/v1beta/openai",
        help="LLM API base URL (default: Google AI Studio)"
    )

    # I2I specific
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Directory containing source images for I2I editing (FFHQ/COCO). If not provided, generates synthetic sources."
    )

    # Evaluation configuration
    parser.add_argument(
        "--refusal-threshold",
        type=float,
        default=0.25,
        help="CLIP similarity threshold for refusal detection (τ in paper, default: 0.25)"
    )
    parser.add_argument(
        "--vlm",
        type=str,
        default="gpt-4o-mini",
        help="VLM model for cue retention scoring (default: gpt-4o-mini)"
    )

    # Output
    parser.add_argument(
        "--output",
        type=str,
        default="experiments/results",
        help="Base output directory (default: experiments/results)"
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Custom run identifier (default: timestamp)"
    )

    # Debugging
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    return parser.parse_args()


def print_banner(config: ACRBConfig):
    """Print startup banner with configuration."""
    print("\n" + "="*70)
    print("   ACRB: Attribute-Conditioned Refusal Bias Audit")
    print("   Algorithm 1 Implementation (IJCAI-ECAI 2026)")
    print("="*70)
    print("\nConfiguration:")
    print(f"  Model:               {config.model_name}")
    print(f"  Mode:                {config.mode.upper()}")
    print(f"  Base Prompts:        {config.max_base_prompts}")
    print(f"  Attributes:          {', '.join(config.attribute_types)}")
    print(f"  LLM Expansion:       {config.llm_model or 'None (template-based)'}")
    if config.mode == "i2i":
        print(f"  Source Images:       {config.i2i_source_images_dir or 'Synthetic'}")
    print(f"  Refusal Threshold:   {config.refusal_threshold}")
    print(f"  VLM Scorer:          {config.vlm_model}")
    print(f"  Random Seed:         {config.seed}")
    print(f"  Output Directory:    {config.output_dir}")
    print("-" * 70)
    print("\nPipeline Stages:")
    print("  Stage I:   Dynamic Prompt Synthesis (Boundary + Attribute)")
    print("  Stage II:  Multi-Modal Generation (T2I/I2I)")
    print("  Stage III: Dual-Metric Evaluation (Hard + Soft Refusal)")
    print("="*70 + "\n")


def print_results(result):
    """Print final results summary."""
    print("\n" + "="*70)
    print("   AUDIT RESULTS SUMMARY")
    print("="*70)
    print(f"\nSample Statistics:")
    print(f"  Total Samples:       {result.total_samples}")
    print(f"  Refused:             {result.total_refused} ({result.refusal_rate:.2%})")
    print(f"  Failed:              {result.total_failed} ({result.failure_rate:.2%})")

    print(f"\nDisparity Metrics:")
    print(f"  Δ_refusal:           {result.delta_refusal:.4f}")
    print(f"  Δ_erasure:           {result.delta_erasure:.4f}")

    print(f"\nRefusal Rates by Attribute:")
    for attr, rate in sorted(result.refusal_by_attribute.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {attr:30s} {rate:6.2%}")

    if result.erasure_by_attribute:
        print(f"\nErasure Rates by Attribute:")
        for attr, rate in sorted(result.erasure_by_attribute.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {attr:30s} {rate:6.2%}")

    print("\n" + "-"*70)
    print(f"Detailed results saved to:")
    print(f"  {Path(result.config['output_dir']) / result.config['model_name'] / result.run_id}")
    print("="*70 + "\n")


def main():
    """Main entry point."""
    args = parse_args()

    # Set up logging
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)

    # Build configuration
    config = ACRBConfig(
        model_name=args.model,
        mode=args.mode,
        max_base_prompts=args.samples,
        attribute_types=args.attributes,  # None = all 5 types
        llm_model=args.llm,
        llm_api_base=args.llm_api_base,
        llm_api_key=args.llm_api_key or os.getenv("ACRB_LLM_API_KEY"),
        i2i_source_images_dir=args.dataset,
        refusal_threshold=args.refusal_threshold,
        vlm_model=args.vlm,
        output_dir=args.output,
        run_id=args.run_id,
        seed=args.seed
    )

    # Print configuration
    print_banner(config)

    # Confirm for large runs
    total_prompts = config.max_base_prompts * (len(config.attribute_types) * 6 + 1)  # Rough estimate
    if config.max_base_prompts > 50:
        print(f"WARNING: This will generate approximately {total_prompts} prompts.")
        response = input("Continue? [y/N]: ")
        if response.lower() != 'y':
            print("Audit cancelled.")
            sys.exit(0)

    try:
        # Initialize and run pipeline
        pipeline = ACRBPipeline(config)
        result = pipeline.run()

        # Print results
        print_results(result)

        # Success
        sys.exit(0)

    except KeyboardInterrupt:
        print("\n\nAudit interrupted by user.")
        sys.exit(1)

    except Exception as e:
        print(f"\n\nERROR: Audit failed with exception:")
        print(f"  {type(e).__name__}: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
