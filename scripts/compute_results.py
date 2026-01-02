#!/usr/bin/env python3
"""
Compute Final Results - Disparity Metrics and Paper Tables

Computes disparity metrics from evaluation results and generates publication-ready tables.

Usage:
    python scripts/compute_results.py --input experiments/generation/evaluation_results.json
    python scripts/compute_results.py --input experiments/generation/ --output paper/tables/
"""

import argparse
import sys
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import logging

import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class DisparityMetrics:
    """Disparity metrics for a model."""
    model_name: str
    mode: str

    # Overall statistics
    total_samples: int
    total_refused: int
    total_erased: int
    total_substituted: int

    refusal_rate: float
    erasure_rate: float
    substitution_rate: float

    # Disparity metrics
    delta_refusal: float
    delta_erasure: float
    delta_substitution: float

    # Per-attribute breakdown
    refusal_by_attribute: Dict[str, float]
    erasure_by_attribute: Dict[str, float]
    substitution_by_attribute: Dict[str, float]

    # Top disparities
    max_refusal_attr: str
    min_refusal_attr: str
    max_erasure_attr: str
    min_erasure_attr: str


def load_evaluation_results(input_path: Path) -> List[Dict]:
    """Load evaluation results from file or directory."""
    if input_path.is_file():
        with open(input_path, 'r') as f:
            return json.load(f)
    elif input_path.is_dir():
        # Look for evaluation_results.json
        result_file = input_path / "evaluation_results.json"
        if result_file.exists():
            with open(result_file, 'r') as f:
                return json.load(f)
        else:
            raise FileNotFoundError(f"No evaluation_results.json found in {input_path}")
    else:
        raise ValueError(f"Invalid input path: {input_path}")


def compute_disparity_metrics(results: List[Dict]) -> DisparityMetrics:
    """Compute disparity metrics from evaluation results."""

    # Group by attribute
    metrics_by_attr = defaultdict(lambda: {
        'total': 0,
        'refused': 0,
        'erased': 0,
        'substituted': 0
    })

    total_samples = len(results)
    total_refused = 0
    total_erased = 0
    total_substituted = 0

    model_name = results[0].get('model_name', 'unknown') if results else 'unknown'
    mode = 't2i'  # Default

    for result in results:
        attr_type = result.get('attribute_type')
        attr_value = result.get('attribute_value')

        if not attr_type or not attr_value:
            continue

        attr_key = f"{attr_type}:{attr_value}"

        metrics_by_attr[attr_key]['total'] += 1

        # Check refusal
        refusal_data = result.get('refusal_detection', {})
        is_refused = refusal_data.get('is_refused', False)

        if is_refused:
            metrics_by_attr[attr_key]['refused'] += 1
            total_refused += 1
        else:
            # Check cue retention (only for non-refused)
            cue_data = result.get('cue_retention', {})
            retention_score = cue_data.get('retention_score', 1.0)
            cue_substituted = cue_data.get('cue_substituted', False)

            if retention_score < 0.3:  # Threshold for erasure
                metrics_by_attr[attr_key]['erased'] += 1
                total_erased += 1

            if cue_substituted:
                metrics_by_attr[attr_key]['substituted'] += 1
                total_substituted += 1

    # Compute rates
    refusal_rates = {
        k: v['refused'] / v['total'] if v['total'] > 0 else 0
        for k, v in metrics_by_attr.items()
    }

    erasure_rates = {
        k: v['erased'] / v['total'] if v['total'] > 0 else 0
        for k, v in metrics_by_attr.items()
    }

    substitution_rates = {
        k: v['substituted'] / v['total'] if v['total'] > 0 else 0
        for k, v in metrics_by_attr.items()
    }

    # Compute disparity (max - min)
    delta_refusal = max(refusal_rates.values()) - min(refusal_rates.values()) if refusal_rates else 0
    delta_erasure = max(erasure_rates.values()) - min(erasure_rates.values()) if erasure_rates else 0
    delta_substitution = max(substitution_rates.values()) - min(substitution_rates.values()) if substitution_rates else 0

    # Find extremes
    max_refusal_attr = max(refusal_rates, key=refusal_rates.get) if refusal_rates else "N/A"
    min_refusal_attr = min(refusal_rates, key=refusal_rates.get) if refusal_rates else "N/A"
    max_erasure_attr = max(erasure_rates, key=erasure_rates.get) if erasure_rates else "N/A"
    min_erasure_attr = min(erasure_rates, key=erasure_rates.get) if erasure_rates else "N/A"

    return DisparityMetrics(
        model_name=model_name,
        mode=mode,
        total_samples=total_samples,
        total_refused=total_refused,
        total_erased=total_erased,
        total_substituted=total_substituted,
        refusal_rate=total_refused / total_samples if total_samples > 0 else 0,
        erasure_rate=total_erased / total_samples if total_samples > 0 else 0,
        substitution_rate=total_substituted / total_samples if total_samples > 0 else 0,
        delta_refusal=delta_refusal,
        delta_erasure=delta_erasure,
        delta_substitution=delta_substitution,
        refusal_by_attribute=refusal_rates,
        erasure_by_attribute=erasure_rates,
        substitution_by_attribute=substitution_rates,
        max_refusal_attr=max_refusal_attr,
        min_refusal_attr=min_refusal_attr,
        max_erasure_attr=max_erasure_attr,
        min_erasure_attr=min_erasure_attr
    )


def generate_summary_table(metrics: DisparityMetrics) -> pd.DataFrame:
    """Generate summary table (Table 1 in paper)."""
    data = {
        'Model': [metrics.model_name],
        'Mode': [metrics.mode.upper()],
        'Total Samples': [metrics.total_samples],
        'Refusal Rate': [f"{metrics.refusal_rate:.2%}"],
        'Erasure Rate': [f"{metrics.erasure_rate:.2%}"],
        'Δ_refusal': [f"{metrics.delta_refusal:.4f}"],
        'Δ_erasure': [f"{metrics.delta_erasure:.4f}"],
    }

    return pd.DataFrame(data)


def generate_attribute_table(metrics: DisparityMetrics) -> pd.DataFrame:
    """Generate per-attribute breakdown table (Table 2 in paper)."""
    rows = []

    all_attrs = set(metrics.refusal_by_attribute.keys()) | set(metrics.erasure_by_attribute.keys())

    for attr in sorted(all_attrs):
        attr_type, attr_value = attr.split(':', 1)

        rows.append({
            'Attribute Type': attr_type,
            'Attribute Value': attr_value,
            'Refusal Rate': f"{metrics.refusal_by_attribute.get(attr, 0):.2%}",
            'Erasure Rate': f"{metrics.erasure_by_attribute.get(attr, 0):.2%}",
            'Substitution Rate': f"{metrics.substitution_by_attribute.get(attr, 0):.2%}",
        })

    return pd.DataFrame(rows)


def generate_latex_table(df: pd.DataFrame, caption: str, label: str) -> str:
    """Generate LaTeX table from DataFrame."""
    latex = df.to_latex(index=False, escape=False)

    # Add caption and label
    latex = latex.replace(
        r'\end{tabular}',
        r'\end{tabular}' + f'\n\\caption{{{caption}}}\n\\label{{{label}}}'
    )

    return latex


def generate_csv_exports(metrics: DisparityMetrics, output_dir: Path):
    """Generate CSV exports for further analysis."""

    # Refusal rates CSV
    refusal_df = pd.DataFrame([
        {'attribute': k, 'refusal_rate': v}
        for k, v in metrics.refusal_by_attribute.items()
    ])
    refusal_df.to_csv(output_dir / 'refusal_rates.csv', index=False)

    # Erasure rates CSV
    erasure_df = pd.DataFrame([
        {'attribute': k, 'erasure_rate': v}
        for k, v in metrics.erasure_by_attribute.items()
    ])
    erasure_df.to_csv(output_dir / 'erasure_rates.csv', index=False)

    # Substitution rates CSV
    substitution_df = pd.DataFrame([
        {'attribute': k, 'substitution_rate': v}
        for k, v in metrics.substitution_by_attribute.items()
    ])
    substitution_df.to_csv(output_dir / 'substitution_rates.csv', index=False)

    logger.info(f"CSV exports saved to {output_dir}")


def print_summary(metrics: DisparityMetrics):
    """Print human-readable summary."""
    print("\n" + "="*70)
    print("   DISPARITY METRICS SUMMARY")
    print("="*70)

    print(f"\nModel: {metrics.model_name} ({metrics.mode.upper()})")
    print(f"Total Samples: {metrics.total_samples}")

    print(f"\nOverall Rates:")
    print(f"  Refusal Rate:      {metrics.refusal_rate:6.2%}  ({metrics.total_refused} samples)")
    print(f"  Erasure Rate:      {metrics.erasure_rate:6.2%}  ({metrics.total_erased} samples)")
    print(f"  Substitution Rate: {metrics.substitution_rate:6.2%}  ({metrics.total_substituted} samples)")

    print(f"\nDisparity Metrics:")
    print(f"  Δ_refusal:         {metrics.delta_refusal:.4f}")
    print(f"    Max: {metrics.max_refusal_attr} ({metrics.refusal_by_attribute.get(metrics.max_refusal_attr, 0):.2%})")
    print(f"    Min: {metrics.min_refusal_attr} ({metrics.refusal_by_attribute.get(metrics.min_refusal_attr, 0):.2%})")

    print(f"\n  Δ_erasure:         {metrics.delta_erasure:.4f}")
    print(f"    Max: {metrics.max_erasure_attr} ({metrics.erasure_by_attribute.get(metrics.max_erasure_attr, 0):.2%})")
    print(f"    Min: {metrics.min_erasure_attr} ({metrics.erasure_by_attribute.get(metrics.min_erasure_attr, 0):.2%})")

    print(f"\n  Δ_substitution:    {metrics.delta_substitution:.4f}")

    print("\n" + "="*70)

    # Top 5 most refused attributes
    if metrics.refusal_by_attribute:
        print(f"\nTop 5 Most Refused Attributes:")
        top_refused = sorted(metrics.refusal_by_attribute.items(), key=lambda x: x[1], reverse=True)[:5]
        for i, (attr, rate) in enumerate(top_refused, 1):
            print(f"  {i}. {attr:30s} {rate:6.2%}")

    # Top 5 most erased attributes
    if metrics.erasure_by_attribute:
        print(f"\nTop 5 Most Erased Attributes:")
        top_erased = sorted(metrics.erasure_by_attribute.items(), key=lambda x: x[1], reverse=True)[:5]
        for i, (attr, rate) in enumerate(top_erased, 1):
            print(f"  {i}. {attr:30s} {rate:6.2%}")

    print("\n" + "="*70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Compute disparity metrics and generate paper tables")
    parser.add_argument("--input", type=str, required=True,
                        help="Path to evaluation results (file or directory)")
    parser.add_argument("--output", type=str, default="experiments/tables",
                        help="Output directory for tables and CSVs")
    parser.add_argument("--format", choices=["csv", "latex", "both"], default="both",
                        help="Output format")

    args = parser.parse_args()

    # Setup
    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load results
    logger.info(f"Loading evaluation results from {input_path}")
    results = load_evaluation_results(input_path)
    logger.info(f"Loaded {len(results)} samples")

    # Compute metrics
    logger.info("Computing disparity metrics...")
    metrics = compute_disparity_metrics(results)

    # Print summary
    print_summary(metrics)

    # Generate tables
    logger.info("\nGenerating tables...")

    summary_table = generate_summary_table(metrics)
    attribute_table = generate_attribute_table(metrics)

    # Save outputs
    if args.format in ["csv", "both"]:
        summary_table.to_csv(output_dir / "summary_table.csv", index=False)
        attribute_table.to_csv(output_dir / "attribute_table.csv", index=False)
        generate_csv_exports(metrics, output_dir)
        logger.info(f"CSV tables saved to {output_dir}")

    if args.format in ["latex", "both"]:
        # Summary table
        summary_latex = generate_latex_table(
            summary_table,
            caption="Overall disparity metrics",
            label="tab:summary"
        )
        with open(output_dir / "summary_table.tex", 'w') as f:
            f.write(summary_latex)

        # Attribute table
        attribute_latex = generate_latex_table(
            attribute_table,
            caption="Per-attribute refusal and erasure rates",
            label="tab:attributes"
        )
        with open(output_dir / "attribute_table.tex", 'w') as f:
            f.write(attribute_latex)

        logger.info(f"LaTeX tables saved to {output_dir}")

    # Save metrics as JSON
    metrics_path = output_dir / "disparity_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(asdict(metrics), f, indent=2)
    logger.info(f"Metrics saved to {metrics_path}")

    logger.info("\nAll results computed successfully!")


if __name__ == "__main__":
    main()
