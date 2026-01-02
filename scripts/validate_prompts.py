#!/usr/bin/env python3
"""
Validate and analyze generated prompt dataset

Usage:
    python scripts/validate_prompts.py
"""

import json
from pathlib import Path
from collections import Counter, defaultdict


def load_dataset():
    """Load all dataset files."""
    data_dir = Path(__file__).parent.parent / "data" / "prompts"

    with open(data_dir / "base_prompts.json") as f:
        base_prompts = json.load(f)

    with open(data_dir / "expanded_prompts.json") as f:
        expanded_prompts = json.load(f)

    with open(data_dir / "attributes.json") as f:
        attributes = json.load(f)

    with open(data_dir / "dataset_stats.json") as f:
        stats = json.load(f)

    return base_prompts, expanded_prompts, attributes, stats


def analyze_base_prompts(base_prompts):
    """Analyze base prompt distribution."""
    print("\n" + "="*70)
    print("BASE PROMPTS ANALYSIS")
    print("="*70)

    # Count by domain
    domain_counts = Counter(bp["domain"] for bp in base_prompts)

    print(f"\nTotal base prompts: {len(base_prompts)}")
    print("\nDistribution by domain:")
    for domain, count in sorted(domain_counts.items()):
        pct = (count / len(base_prompts)) * 100
        bar = "█" * (count // 2)
        print(f"  {domain:25s} {count:3d} ({pct:5.1f}%) {bar}")

    # Analyze trigger words
    with_triggers = sum(1 for bp in base_prompts if bp["trigger_words"])
    without_triggers = len(base_prompts) - with_triggers

    print(f"\nTrigger word coverage:")
    print(f"  With trigger words: {with_triggers} ({with_triggers/len(base_prompts)*100:.1f}%)")
    print(f"  Without trigger words: {without_triggers} ({without_triggers/len(base_prompts)*100:.1f}%)")

    # Most common trigger words
    all_triggers = []
    for bp in base_prompts:
        all_triggers.extend(bp["trigger_words"])

    trigger_counts = Counter(all_triggers)
    print(f"\nMost common trigger words:")
    for word, count in trigger_counts.most_common(10):
        print(f"  {word:20s} {count:3d}")


def analyze_expanded_prompts(expanded_prompts):
    """Analyze expanded prompt distribution."""
    print("\n" + "="*70)
    print("EXPANDED PROMPTS ANALYSIS")
    print("="*70)

    print(f"\nTotal expanded prompts: {len(expanded_prompts)}")

    # Count by attribute type
    attr_counts = Counter(ep["attribute_type"] for ep in expanded_prompts)

    print("\nDistribution by attribute type:")
    for attr_type, count in sorted(attr_counts.items()):
        pct = (count / len(expanded_prompts)) * 100
        bar = "█" * int(pct // 2)
        print(f"  {attr_type:15s} {count:4d} ({pct:5.1f}%) {bar}")

    # Count by attribute value
    print("\nDistribution by specific attributes:")

    attr_value_counts = defaultdict(lambda: Counter())
    for ep in expanded_prompts:
        if ep["attribute_type"] != "neutral":
            attr_value_counts[ep["attribute_type"]][ep["attribute_value"]] += 1

    for attr_type in sorted(attr_value_counts.keys()):
        print(f"\n  {attr_type.upper()}:")
        for value, count in sorted(attr_value_counts[attr_type].items()):
            print(f"    {value:20s} {count:4d}")

    # Count by domain
    domain_counts = Counter(ep["domain"] for ep in expanded_prompts)
    print("\nDistribution by domain:")
    for domain, count in sorted(domain_counts.items()):
        print(f"  {domain:25s} {count:4d}")


def check_quality(base_prompts, expanded_prompts):
    """Check dataset quality."""
    print("\n" + "="*70)
    print("QUALITY CHECKS")
    print("="*70)

    issues = []

    # Check 1: All prompts are benign
    non_benign_base = [bp for bp in base_prompts if not bp["is_benign"]]
    non_benign_expanded = [ep for ep in expanded_prompts if not ep["is_benign"]]

    if non_benign_base or non_benign_expanded:
        issues.append(f"Found non-benign prompts: {len(non_benign_base)} base, {len(non_benign_expanded)} expanded")
    else:
        print("✓ All prompts are marked as benign")

    # Check 2: No duplicate IDs
    base_ids = [bp["prompt_id"] for bp in base_prompts]
    expanded_ids = [ep["expanded_id"] for ep in expanded_prompts]

    if len(base_ids) != len(set(base_ids)):
        issues.append(f"Duplicate base prompt IDs detected")
    else:
        print("✓ No duplicate base prompt IDs")

    if len(expanded_ids) != len(set(expanded_ids)):
        issues.append(f"Duplicate expanded prompt IDs detected")
    else:
        print("✓ No duplicate expanded prompt IDs")

    # Check 3: Each base prompt has correct number of expansions
    base_to_expanded = defaultdict(list)
    for ep in expanded_prompts:
        base_to_expanded[ep["base_prompt_id"]].append(ep)

    incorrect_expansions = []
    for bp_id, expansions in base_to_expanded.items():
        if len(expansions) != 24:  # 1 neutral + 23 attributes
            incorrect_expansions.append((bp_id, len(expansions)))

    if incorrect_expansions:
        issues.append(f"Base prompts with incorrect expansion count: {len(incorrect_expansions)}")
        for bp_id, count in incorrect_expansions[:5]:
            print(f"  {bp_id}: {count} expansions (expected 24)")
    else:
        print("✓ All base prompts have 24 expansions")

    # Check 4: Attribute markers are present in expanded text
    missing_markers = []
    for ep in expanded_prompts:
        if ep["attribute_type"] != "neutral" and ep["attribute_marker"]:
            # Check if marker appears in expanded text (case-insensitive)
            if ep["attribute_marker"].lower() not in ep["expanded_text"].lower():
                missing_markers.append(ep["expanded_id"])

    if missing_markers:
        issues.append(f"Expanded prompts missing attribute markers: {len(missing_markers)}")
        for ep_id in missing_markers[:5]:
            print(f"  {ep_id}")
    else:
        print("✓ All attribute markers present in expanded text")

    # Check 5: No empty prompts
    empty_base = [bp for bp in base_prompts if not bp["text"].strip()]
    empty_expanded = [ep for ep in expanded_prompts if not ep["expanded_text"].strip()]

    if empty_base or empty_expanded:
        issues.append(f"Empty prompts: {len(empty_base)} base, {len(empty_expanded)} expanded")
    else:
        print("✓ No empty prompts")

    # Summary
    if issues:
        print("\n⚠ ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✓ ALL QUALITY CHECKS PASSED")


def show_samples(expanded_prompts):
    """Show sample prompts from each domain."""
    print("\n" + "="*70)
    print("SAMPLE PROMPTS")
    print("="*70)

    # Group by domain
    by_domain = defaultdict(list)
    for ep in expanded_prompts:
        by_domain[ep["domain"]].append(ep)

    # Show 2 samples per domain
    for domain in sorted(by_domain.keys()):
        print(f"\n{domain.upper()}:")
        samples = by_domain[domain][:2]
        for ep in samples:
            print(f"\n  [{ep['expanded_id']}]")
            print(f"  Attribute: {ep['attribute_type']}:{ep['attribute_value']}")
            print(f"  Text: {ep['expanded_text']}")


def generate_summary_report(base_prompts, expanded_prompts, attributes, stats):
    """Generate summary statistics."""
    print("\n" + "="*70)
    print("DATASET SUMMARY")
    print("="*70)

    print(f"""
Dataset Statistics:
  - Total base prompts: {stats['total_base_prompts']}
  - Total expanded prompts: {stats['total_expanded_prompts']}
  - Number of domains: {stats['num_domains']}
  - Prompts per domain: {stats['prompts_per_domain']}
  - Attributes per prompt: {stats['attributes_per_prompt']}

Attribute Breakdown:
  - Neutral: {stats['attribute_breakdown']['neutral']}
  - Culture: {stats['attribute_breakdown']['culture']}
  - Gender: {stats['attribute_breakdown']['gender']}
  - Disability: {stats['attribute_breakdown']['disability']}
  - Religion: {stats['attribute_breakdown']['religion']}
  - Age: {stats['attribute_breakdown']['age']}
  - Total: {sum(stats['attribute_breakdown'].values())}

Domains:
""")
    for i, domain in enumerate(stats['domains'], 1):
        print(f"  {i}. {domain}")

    print(f"""
Expected for full experiment:
  - T2I models (6 models × 2,592 prompts): 15,552 images
  - I2I models (3 models × 500 images × 24 attributes): 36,000 edited images
  - Human evaluation samples (150-200 pairs): ~300-400 annotations
  - Estimated API cost: $200-400
""")


def main():
    """Run all validation checks."""
    print("="*70)
    print("PROMPT DATASET VALIDATION REPORT")
    print("="*70)

    # Load data
    print("\nLoading dataset...")
    base_prompts, expanded_prompts, attributes, stats = load_dataset()
    print(f"✓ Loaded {len(base_prompts)} base prompts")
    print(f"✓ Loaded {len(expanded_prompts)} expanded prompts")

    # Run analyses
    analyze_base_prompts(base_prompts)
    analyze_expanded_prompts(expanded_prompts)
    check_quality(base_prompts, expanded_prompts)
    show_samples(expanded_prompts)
    generate_summary_report(base_prompts, expanded_prompts, attributes, stats)

    print("\n" + "="*70)
    print("VALIDATION COMPLETE")
    print("="*70)
    print()


if __name__ == "__main__":
    main()
