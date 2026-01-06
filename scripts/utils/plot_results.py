#!/usr/bin/env python3
"""
ACRB Plotting Utility
Generates paper-ready figures from ACRB audit results.

Usage:
    python scripts/plot_results.py --input experiments/results --output figs
    python scripts/plot_results.py --input experiments/results --run-id 20241230_120000
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import seaborn as sns

# Set publication-quality defaults
plt.rcParams.update({
    'font.size': 10,
    'font.family': 'serif',
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.1
})


def parse_args():
    parser = argparse.ArgumentParser(description="Generate ACRB result visualizations")
    parser.add_argument("--input", type=str, default="experiments/results",
                        help="Input directory containing model results")
    parser.add_argument("--output", type=str, default="figs",
                        help="Output directory for figures")
    parser.add_argument("--run-id", type=str, default=None,
                        help="Specific run ID to plot (default: latest)")
    parser.add_argument("--format", type=str, default="pdf",
                        choices=["pdf", "png", "svg"],
                        help="Output format (default: pdf)")
    return parser.parse_args()


def load_results(input_dir: Path, run_id: Optional[str] = None) -> List[Dict]:
    """Load all ACRB results from the input directory."""
    results = []

    for model_dir in input_dir.iterdir():
        if not model_dir.is_dir():
            continue

        # Find run directories
        run_dirs = sorted(model_dir.iterdir())
        if run_id:
            run_dirs = [d for d in run_dirs if run_id in d.name]

        for run_dir in run_dirs:
            summary_file = run_dir / "acrb_summary.json"
            if summary_file.exists():
                with open(summary_file) as f:
                    data = json.load(f)
                    results.append(data)

    return results


def plot_model_comparison_bar(results: List[Dict], output_path: Path):
    """
    Figure 1: Model comparison bar chart
    Shows refusal rate and disparity metrics for each model.
    """
    if not results:
        print("No results to plot for model comparison")
        return

    # Prepare data
    models = [r["model_name"] for r in results]
    refusal_rates = [r["refusal_rate"] * 100 for r in results]
    delta_refusals = [r["delta_refusal"] for r in results]
    modes = [r["mode"] for r in results]

    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Colors by mode
    colors = ['#2ecc71' if m == 't2i' else '#e74c3c' for m in modes]

    # Left: Refusal Rate
    x = np.arange(len(models))
    bars1 = ax1.bar(x, refusal_rates, color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
    ax1.set_xlabel("Model")
    ax1.set_ylabel("Refusal Rate (%)")
    ax1.set_title("(a) Overall Refusal Rate by Model")
    ax1.set_xticks(x)
    ax1.set_xticklabels(models, rotation=45, ha='right')
    ax1.set_ylim(0, max(refusal_rates) * 1.2 if refusal_rates else 100)

    # Add value labels
    for bar, val in zip(bars1, refusal_rates):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{val:.1f}%', ha='center', va='bottom', fontsize=8)

    # Right: Delta Refusal
    bars2 = ax2.bar(x, delta_refusals, color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
    ax2.set_xlabel("Model")
    ax2.set_ylabel(r"$\Delta_{refusal}$")
    ax2.set_title(r"(b) Refusal Disparity ($\Delta_{refusal}$) by Model")
    ax2.set_xticks(x)
    ax2.set_xticklabels(models, rotation=45, ha='right')
    ax2.axhline(y=0.1, color='red', linestyle='--', alpha=0.5, label='Threshold')

    # Legend for mode
    t2i_patch = mpatches.Patch(color='#2ecc71', label='T2I')
    i2i_patch = mpatches.Patch(color='#e74c3c', label='I2I')
    ax2.legend(handles=[t2i_patch, i2i_patch], loc='upper right')

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"Saved: {output_path}")


def plot_refusal_heatmap(results: List[Dict], output_path: Path):
    """
    Figure 2: Refusal rate heatmap by attribute and model.
    """
    if not results:
        print("No results to plot for heatmap")
        return

    # Collect all attribute refusal rates
    all_data = []
    for r in results:
        model = r["model_name"]
        for attr, rate in r.get("refusal_by_attribute", {}).items():
            attr_type, attr_value = attr.split(":", 1) if ":" in attr else (attr, "unknown")
            all_data.append({
                "model": model,
                "attribute_type": attr_type,
                "attribute_value": attr_value,
                "refusal_rate": rate * 100
            })

    if not all_data:
        print("No attribute data for heatmap")
        return

    df = pd.DataFrame(all_data)

    # Pivot for heatmap (attribute_value vs model)
    pivot = df.pivot_table(
        values="refusal_rate",
        index="attribute_value",
        columns="model",
        aggfunc="mean"
    )

    # Create heatmap
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(
        pivot,
        annot=True,
        fmt=".1f",
        cmap="RdYlGn_r",
        ax=ax,
        cbar_kws={"label": "Refusal Rate (%)"},
        linewidths=0.5
    )
    ax.set_xlabel("Model")
    ax.set_ylabel("Attribute Value")
    ax.set_title("Refusal Rate (%) by Attribute Value and Model")

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"Saved: {output_path}")


def plot_attribute_disparity(results: List[Dict], output_path: Path):
    """
    Figure 3: Attribute-level disparity analysis.
    Shows max-min disparity within each attribute type.
    """
    if not results:
        print("No results to plot for disparity")
        return

    # Aggregate by attribute type
    attr_type_rates = {}
    for r in results:
        for attr, rate in r.get("refusal_by_attribute", {}).items():
            attr_type = attr.split(":")[0] if ":" in attr else attr
            if attr_type not in attr_type_rates:
                attr_type_rates[attr_type] = []
            attr_type_rates[attr_type].append(rate * 100)

    # Compute statistics
    attr_types = []
    means = []
    stds = []
    ranges = []

    for attr_type, rates in sorted(attr_type_rates.items()):
        if rates:
            attr_types.append(attr_type.capitalize())
            means.append(np.mean(rates))
            stds.append(np.std(rates))
            ranges.append(max(rates) - min(rates))

    if not attr_types:
        print("No attribute types found for disparity plot")
        return

    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    x = np.arange(len(attr_types))
    width = 0.6

    # Left: Mean refusal rate with std
    bars = ax1.bar(x, means, width, yerr=stds, capsize=3,
                   color='#3498db', alpha=0.8, edgecolor='black', linewidth=0.5)
    ax1.set_xlabel("Attribute Type")
    ax1.set_ylabel("Refusal Rate (%)")
    ax1.set_title("(a) Mean Refusal Rate by Attribute Type")
    ax1.set_xticks(x)
    ax1.set_xticklabels(attr_types)

    # Right: Disparity range
    bars2 = ax2.bar(x, ranges, width, color='#e74c3c', alpha=0.8,
                    edgecolor='black', linewidth=0.5)
    ax2.set_xlabel("Attribute Type")
    ax2.set_ylabel("Disparity Range (%)")
    ax2.set_title("(b) Within-Attribute Disparity (Max - Min)")
    ax2.set_xticks(x)
    ax2.set_xticklabels(attr_types)

    # Add value labels
    for bar, val in zip(bars2, ranges):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{val:.1f}%', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"Saved: {output_path}")


def plot_t2i_vs_i2i(results: List[Dict], output_path: Path):
    """
    Figure 4: T2I vs I2I comparison.
    """
    t2i_results = [r for r in results if r["mode"] == "t2i"]
    i2i_results = [r for r in results if r["mode"] == "i2i"]

    if not t2i_results and not i2i_results:
        print("No T2I/I2I results to compare")
        return

    fig, axes = plt.subplots(1, 3, figsize=(14, 4))

    # Prepare data
    t2i_refusal = [r["refusal_rate"] * 100 for r in t2i_results]
    i2i_refusal = [r["refusal_rate"] * 100 for r in i2i_results]
    t2i_delta_r = [r["delta_refusal"] for r in t2i_results]
    i2i_delta_r = [r["delta_refusal"] for r in i2i_results]
    t2i_delta_e = [r["delta_erasure"] for r in t2i_results]
    i2i_delta_e = [r["delta_erasure"] for r in i2i_results]

    # Subplot 1: Box plot of refusal rates
    ax1 = axes[0]
    data = []
    labels = []
    if t2i_refusal:
        data.append(t2i_refusal)
        labels.append("T2I")
    if i2i_refusal:
        data.append(i2i_refusal)
        labels.append("I2I")

    if data:
        bp = ax1.boxplot(data, labels=labels, patch_artist=True)
        colors = ['#2ecc71', '#e74c3c'][:len(data)]
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
    ax1.set_ylabel("Refusal Rate (%)")
    ax1.set_title("(a) Refusal Rate Distribution")

    # Subplot 2: Delta_refusal comparison
    ax2 = axes[1]
    data = []
    if t2i_delta_r:
        data.append(t2i_delta_r)
    if i2i_delta_r:
        data.append(i2i_delta_r)

    if data:
        bp = ax2.boxplot(data, labels=labels[:len(data)], patch_artist=True)
        for patch, color in zip(bp['boxes'], colors[:len(data)]):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
    ax2.set_ylabel(r"$\Delta_{refusal}$")
    ax2.set_title(r"(b) Refusal Disparity ($\Delta_R$)")

    # Subplot 3: Delta_erasure comparison
    ax3 = axes[2]
    data = []
    if t2i_delta_e:
        data.append(t2i_delta_e)
    if i2i_delta_e:
        data.append(i2i_delta_e)

    if data:
        bp = ax3.boxplot(data, labels=labels[:len(data)], patch_artist=True)
        for patch, color in zip(bp['boxes'], colors[:len(data)]):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
    ax3.set_ylabel(r"$\Delta_{erasure}$")
    ax3.set_title(r"(c) Erasure Disparity ($\Delta_E$)")

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"Saved: {output_path}")


def plot_erasure_analysis(results: List[Dict], output_path: Path):
    """
    Figure 5: Cue erasure analysis for I2I models.
    """
    i2i_results = [r for r in results if r["mode"] == "i2i"]

    if not i2i_results:
        print("No I2I results for erasure analysis")
        return

    # Collect erasure data
    all_data = []
    for r in i2i_results:
        model = r["model_name"]
        for attr, rate in r.get("erasure_by_attribute", {}).items():
            attr_type, attr_value = attr.split(":", 1) if ":" in attr else (attr, "unknown")
            all_data.append({
                "model": model,
                "attribute_type": attr_type,
                "attribute_value": attr_value,
                "erasure_rate": rate * 100
            })

    if not all_data:
        print("No erasure data available")
        return

    df = pd.DataFrame(all_data)

    # Create grouped bar chart by attribute type
    fig, ax = plt.subplots(figsize=(12, 6))

    attr_types = df["attribute_type"].unique()
    models = df["model"].unique()
    x = np.arange(len(attr_types))
    width = 0.8 / len(models)

    colors = plt.cm.Set2(np.linspace(0, 1, len(models)))

    for i, model in enumerate(models):
        model_data = df[df["model"] == model]
        means = [model_data[model_data["attribute_type"] == at]["erasure_rate"].mean()
                for at in attr_types]
        ax.bar(x + i * width, means, width, label=model, color=colors[i], alpha=0.8)

    ax.set_xlabel("Attribute Type")
    ax.set_ylabel("Cue Erasure Rate (%)")
    ax.set_title("Cue Erasure Rate by Attribute Type (I2I Models)")
    ax.set_xticks(x + width * (len(models) - 1) / 2)
    ax.set_xticklabels([at.capitalize() for at in attr_types])
    ax.legend(title="Model")

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"Saved: {output_path}")


def plot_radar_chart(results: List[Dict], output_path: Path):
    """
    Figure 6: Radar chart comparing models across dimensions.
    """
    if len(results) < 2:
        print("Need at least 2 models for radar chart")
        return

    # Select top models
    results = sorted(results, key=lambda x: x["total_samples"], reverse=True)[:6]

    # Metrics to compare
    metrics = ["Refusal Rate", "Delta_R", "Delta_E", "Sample Size"]

    # Normalize data
    data = []
    for r in results:
        values = [
            r["refusal_rate"] * 100,
            r["delta_refusal"] * 100,  # Scale for visibility
            r["delta_erasure"] * 100,
            min(r["total_samples"] / 100, 100)  # Normalize to 100
        ]
        data.append(values)

    # Create radar chart
    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]  # Close the polygon

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

    colors = plt.cm.tab10(np.linspace(0, 1, len(results)))

    for i, (r, d) in enumerate(zip(results, data)):
        values = d + d[:1]  # Close the polygon
        ax.plot(angles, values, 'o-', linewidth=2, label=r["model_name"], color=colors[i])
        ax.fill(angles, values, alpha=0.1, color=colors[i])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics)
    ax.set_title("Model Comparison Radar Chart")
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"Saved: {output_path}")


def generate_summary_table(results: List[Dict], output_path: Path):
    """Generate a summary CSV table."""
    if not results:
        print("No results for summary table")
        return

    summary = []
    for r in results:
        summary.append({
            "Model": r["model_name"],
            "Mode": r["mode"].upper(),
            "Samples": r["total_samples"],
            "Refusal Rate (%)": round(r["refusal_rate"] * 100, 2),
            "Delta_R": round(r["delta_refusal"], 4),
            "Delta_E": round(r["delta_erasure"], 4),
            "Run ID": r["run_id"]
        })

    df = pd.DataFrame(summary)
    df.to_csv(output_path, index=False)
    print(f"Saved: {output_path}")


def main():
    args = parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*60)
    print("  ACRB Results Visualization")
    print("="*60)
    print(f"  Input:  {input_dir}")
    print(f"  Output: {output_dir}")
    print(f"  Format: {args.format}")
    if args.run_id:
        print(f"  Run ID: {args.run_id}")
    print("="*60 + "\n")

    # Load results
    results = load_results(input_dir, args.run_id)
    print(f"Loaded {len(results)} result files\n")

    if not results:
        print("No results found. Please run experiments first.")
        sys.exit(1)

    # Generate all figures
    fmt = args.format

    # Figure 1: Model comparison
    plot_model_comparison_bar(results, output_dir / f"fig1_model_comparison.{fmt}")

    # Figure 2: Refusal heatmap
    plot_refusal_heatmap(results, output_dir / f"fig2_refusal_heatmap.{fmt}")

    # Figure 3: Attribute disparity
    plot_attribute_disparity(results, output_dir / f"fig3_attribute_disparity.{fmt}")

    # Figure 4: T2I vs I2I
    plot_t2i_vs_i2i(results, output_dir / f"fig4_t2i_vs_i2i.{fmt}")

    # Figure 5: Erasure analysis
    plot_erasure_analysis(results, output_dir / f"fig5_erasure_analysis.{fmt}")

    # Figure 6: Radar chart
    plot_radar_chart(results, output_dir / f"fig6_radar_chart.{fmt}")

    # Summary table
    generate_summary_table(results, output_dir / "summary_table.csv")

    print("\n" + "="*60)
    print("  All figures generated successfully!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
