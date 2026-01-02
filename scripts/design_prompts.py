#!/usr/bin/env python3
"""
ACRB Prompt Designer
Generate attribute-conditioned prompts using LLM-driven expansion.

Usage:
    # Generate prompts for all domains and attributes
    python scripts/design_prompts.py --domains all --attributes all --num-base 100

    # Generate prompts for specific domains
    python scripts/design_prompts.py --domains fashion medical --attributes culture gender

    # Quick test with template-based expansion (no LLM)
    python scripts/design_prompts.py --num-base 5 --no-llm
"""

import argparse
import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from acrb.prompt_generation import BasePromptGenerator, AttributeExpander, LLMBackend


def parse_args():
    parser = argparse.ArgumentParser(
        description="ACRB Prompt Designer: Generate attribute-conditioned prompts",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Domain configuration
    parser.add_argument(
        "--domains",
        type=str,
        nargs="+",
        default=["all"],
        help="Domains to generate prompts for. Options: fashion, medical, religion, sports, food, art, technology, education, entertainment, all"
    )

    # Attribute configuration
    parser.add_argument(
        "--attributes",
        type=str,
        nargs="+",
        default=["culture", "gender", "disability", "religion", "age"],
        help="Attribute types to expand. Options: culture, gender, disability, religion, age"
    )

    # Generation parameters
    parser.add_argument(
        "--num-base",
        type=int,
        default=10,
        help="Number of base prompts to generate (default: 10)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )

    # LLM configuration
    parser.add_argument(
        "--llm",
        type=str,
        default="gemini-2.0-flash",
        help="LLM model for dynamic expansion (default: gemini-2.0-flash)"
    )
    parser.add_argument(
        "--llm-api-base",
        type=str,
        default="https://generativelanguage.googleapis.com/v1beta/openai",
        help="LLM API base URL"
    )
    parser.add_argument(
        "--llm-api-key",
        type=str,
        default=None,
        help="LLM API key (defaults to ACRB_LLM_API_KEY env variable)"
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Use template-based expansion instead of LLM"
    )

    # Output configuration
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (default: experiments/prompts/prompts_TIMESTAMP.json)"
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["json", "jsonl", "csv"],
        default="json",
        help="Output format (default: json)"
    )

    # Display options
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output"
    )
    parser.add_argument(
        "--preview",
        type=int,
        default=0,
        help="Preview first N prompts without saving"
    )

    return parser.parse_args()


def generate_prompts(args) -> list:
    """Generate attribute-conditioned prompts."""

    # Initialize base prompt generator
    base_gen = BasePromptGenerator(seed=args.seed)

    # Initialize attribute expander
    expander = AttributeExpander(include_neutral=True)

    # Configure LLM if enabled
    llm_backend = None
    if not args.no_llm:
        api_key = args.llm_api_key or os.getenv("ACRB_LLM_API_KEY")
        if api_key:
            llm_backend = LLMBackend(
                model_name=args.llm,
                api_base=args.llm_api_base,
                api_key=api_key
            )
            base_gen.enable_llm(args.llm, args.llm_api_base)
            expander.enable_llm(args.llm, args.llm_api_base)
            print(f"  LLM Backend: {args.llm}")
        else:
            print("  [WARNING] No API key found, using template-based expansion")

    # Parse domains
    domains = None  # None means all domains
    if args.domains and args.domains != ["all"]:
        domains = args.domains

    # Sample base prompts
    print(f"\n  Sampling {args.num_base} base prompts...")
    base_prompts = base_gen.sample_prompts(
        n=args.num_base,
        domains=domains
    )
    print(f"  Generated {len(base_prompts)} base prompts across {len(set(p.domain for p in base_prompts))} domains")

    # Expand with attributes
    all_expanded = []

    print(f"\n  Expanding with attributes: {', '.join(args.attributes)}")

    for i, bp in enumerate(base_prompts):
        if args.verbose:
            print(f"    [{i+1}/{len(base_prompts)}] {bp.text[:50]}...")

        # Apply boundary rephrasing if LLM available
        if llm_backend:
            try:
                boundary_text = llm_backend.rephrase_to_boundary(bp.text, bp.domain)
                if boundary_text:
                    bp.text = boundary_text
            except Exception as e:
                if args.verbose:
                    print(f"      [WARN] Boundary rephrasing failed: {e}")

        # Expand with attributes
        if llm_backend:
            try:
                expanded = expander.expand_prompt_llm(
                    base_prompt=bp,
                    attribute_types=args.attributes
                )
            except Exception as e:
                if args.verbose:
                    print(f"      [WARN] LLM expansion failed, using template: {e}")
                expanded = expander.expand_prompt(
                    base_prompt=bp,
                    attribute_types=args.attributes
                )
        else:
            expanded = expander.expand_prompt(
                base_prompt=bp,
                attribute_types=args.attributes
            )

        all_expanded.extend(expanded)

    # Convert to dict format
    prompts_dict = expander.export_to_dict(all_expanded)

    return prompts_dict


def save_prompts(prompts: list, output_path: str, format: str):
    """Save prompts to file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if format == "json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(prompts, f, indent=2, ensure_ascii=False)

    elif format == "jsonl":
        with open(path, "w", encoding="utf-8") as f:
            for p in prompts:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")

    elif format == "csv":
        import csv
        with open(path, "w", newline="", encoding="utf-8") as f:
            if prompts:
                writer = csv.DictWriter(f, fieldnames=prompts[0].keys())
                writer.writeheader()
                writer.writerows(prompts)


def preview_prompts(prompts: list, n: int):
    """Preview first N prompts."""
    print("\n" + "="*70)
    print("PROMPT PREVIEW")
    print("="*70)

    # Group by base prompt
    grouped = {}
    for p in prompts[:n * 10]:  # Get enough to show N base prompts
        bid = p.get("base_prompt_id", "unknown")
        if bid not in grouped:
            grouped[bid] = []
        grouped[bid].append(p)

    count = 0
    for bid, variations in list(grouped.items())[:n]:
        base_text = variations[0].get("base_text", "")
        domain = variations[0].get("domain", "unknown")

        print(f"\n[{bid}] Domain: {domain}")
        print(f"Base: {base_text}")
        print("-" * 50)

        for v in variations[:6]:  # Show up to 6 variations
            attr = f"{v.get('attribute_type', '?')}:{v.get('attribute_value', '?')}"
            expanded = v.get("expanded_text", "")[:80]
            print(f"  {attr:25s} | {expanded}...")

        if len(variations) > 6:
            print(f"  ... and {len(variations) - 6} more variations")

        count += 1

    print("\n" + "="*70)


def print_stats(prompts: list):
    """Print generation statistics."""
    print("\n" + "-"*50)
    print("GENERATION STATISTICS")
    print("-"*50)

    # Count by attribute type
    attr_counts = {}
    domain_counts = {}

    for p in prompts:
        attr = p.get("attribute_type", "unknown")
        domain = p.get("domain", "unknown")
        attr_counts[attr] = attr_counts.get(attr, 0) + 1
        domain_counts[domain] = domain_counts.get(domain, 0) + 1

    print(f"\nTotal prompts: {len(prompts)}")
    print(f"Unique base prompts: {len(set(p.get('base_prompt_id') for p in prompts))}")

    print("\nBy Attribute Type:")
    for attr, count in sorted(attr_counts.items()):
        print(f"  {attr:15s}: {count:5d}")

    print("\nBy Domain:")
    for domain, count in sorted(domain_counts.items()):
        print(f"  {domain:15s}: {count:5d}")

    print("-"*50)


def main():
    args = parse_args()

    print("\n" + "="*70)
    print("  ACRB Prompt Designer")
    print("  Attribute-Conditioned Refusal Bias Framework")
    print("="*70)
    print(f"\n  Base prompts:  {args.num_base}")
    print(f"  Domains:       {', '.join(args.domains)}")
    print(f"  Attributes:    {', '.join(args.attributes)}")
    print(f"  LLM:           {'Disabled' if args.no_llm else args.llm}")
    print(f"  Seed:          {args.seed}")

    try:
        # Generate prompts
        prompts = generate_prompts(args)

        # Print statistics
        print_stats(prompts)

        # Preview if requested
        if args.preview > 0:
            preview_prompts(prompts, args.preview)

        # Save to file
        if args.output:
            output_path = args.output
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"experiments/prompts/prompts_{timestamp}.{args.format}"

        save_prompts(prompts, output_path, args.format)

        print(f"\n  Output saved to: {output_path}")
        print("="*70 + "\n")

    except KeyboardInterrupt:
        print("\n\n  Cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n  ERROR: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
