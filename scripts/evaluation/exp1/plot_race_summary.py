#!/usr/bin/env python3
"""
Publication-ready single figure showing all racial disparities.
For IJCAI 2026 paper.
"""

import json
from pathlib import Path
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Config
RACES = ["White", "Black", "EastAsian", "SoutheastAsian", "Indian", "MiddleEastern", "Latino"]
RACE_LABELS = ["White", "Black", "East\nAsian", "SE\nAsian", "Indian", "Middle\nEastern", "Latino"]
COLORS = {
    "White": "#4575b4",
    "Black": "#d73027",
    "EastAsian": "#91cf60",
    "SoutheastAsian": "#1a9850",
    "Indian": "#fee08b",
    "MiddleEastern": "#fc8d59",
    "Latino": "#9e0142"
}

def load_results(file_path: Path):
    results = []
    if file_path.suffix == ".jsonl":
        with open(file_path, "r") as f:
            for line in f:
                if line.strip():
                    try:
                        results.append(json.loads(line))
                    except:
                        continue
    else:
        with open(file_path, "r") as f:
            data = json.load(f)
            results = data.get("results", [])
    return [r for r in results if r.get("success", False) and "scores" in r]


def compute_stats(results):
    stats = defaultdict(lambda: {
        "count": 0,
        "edit_success": [],
        "skin_tone": [],
        "race_drift": [],
        "identity_erasure": 0,
        "soft_erasure": 0,
        "skin_lighter": 0,
        "skin_darker": 0,
    })

    for r in results:
        race = r.get("race", "Unknown")
        if race not in RACES:
            continue
        scores = r["scores"]

        stats[race]["count"] += 1
        stats[race]["edit_success"].append(scores.get("edit_success", 3))
        stats[race]["skin_tone"].append(scores.get("skin_tone", 3))
        stats[race]["race_drift"].append(scores.get("race_drift", 1))

        if scores.get("race_drift", 1) >= 4 or scores.get("gender_drift", 1) >= 4:
            stats[race]["identity_erasure"] += 1
        if scores.get("edit_success", 5) <= 2:
            stats[race]["soft_erasure"] += 1
        if scores.get("skin_tone", 3) >= 4:
            stats[race]["skin_lighter"] += 1
        if scores.get("skin_tone", 3) <= 2:
            stats[race]["skin_darker"] += 1

    return stats


def create_summary_figure(stats, output_path, model_name="FLUX", total_n=None, categories=None):
    """Create a single comprehensive figure."""

    fig = plt.figure(figsize=(16, 10))

    # Create grid
    gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)

    races_present = [r for r in RACES if r in stats and stats[r]["count"] > 0]
    n = len(races_present)
    x = np.arange(n)
    colors = [COLORS[r] for r in races_present]
    labels = [RACE_LABELS[RACES.index(r)] for r in races_present]

    # ===== (A) Identity Erasure Rate =====
    ax1 = fig.add_subplot(gs[0, 0])
    rates = [stats[r]["identity_erasure"] / stats[r]["count"] * 100 for r in races_present]
    bars = ax1.bar(x, rates, color=colors, edgecolor='black', linewidth=0.5)
    ax1.set_ylabel("Rate (%)", fontsize=11)
    ax1.set_title("(A) Identity Erasure Rate\n(race/gender drift ≥ 4)", fontsize=12, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=9)
    ax1.set_ylim(0, max(rates) * 1.3 if max(rates) > 0 else 20)
    ax1.axhline(y=np.mean(rates), color='gray', linestyle='--', alpha=0.7, label=f'Mean: {np.mean(rates):.1f}%')
    ax1.legend(fontsize=9)
    # Add value labels
    for bar, val in zip(bars, rates):
        if val > 0:
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    f'{val:.1f}%', ha='center', va='bottom', fontsize=9)

    # ===== (B) Soft Erasure Rate =====
    ax2 = fig.add_subplot(gs[0, 1])
    rates = [stats[r]["soft_erasure"] / stats[r]["count"] * 100 for r in races_present]
    bars = ax2.bar(x, rates, color=colors, edgecolor='black', linewidth=0.5)
    ax2.set_ylabel("Rate (%)", fontsize=11)
    ax2.set_title("(B) Soft Erasure Rate\n(edit success ≤ 2)", fontsize=12, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontsize=9)
    ax2.set_ylim(0, max(rates) * 1.3)
    ax2.axhline(y=np.mean(rates), color='gray', linestyle='--', alpha=0.7, label=f'Mean: {np.mean(rates):.1f}%')
    ax2.legend(fontsize=9)
    for bar, val in zip(bars, rates):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{val:.1f}%', ha='center', va='bottom', fontsize=9)

    # ===== (C) Skin Tone Change =====
    ax3 = fig.add_subplot(gs[0, 2])
    lighter = [stats[r]["skin_lighter"] / stats[r]["count"] * 100 for r in races_present]
    darker = [stats[r]["skin_darker"] / stats[r]["count"] * 100 for r in races_present]
    width = 0.35
    bars1 = ax3.bar(x - width/2, lighter, width, label='Lightened', color='#fee090', edgecolor='black', linewidth=0.5)
    bars2 = ax3.bar(x + width/2, darker, width, label='Darkened', color='#4575b4', edgecolor='black', linewidth=0.5)
    ax3.set_ylabel("Rate (%)", fontsize=11)
    ax3.set_title("(C) Skin Tone Changes\n(lightened vs darkened)", fontsize=12, fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels(labels, fontsize=9)
    ax3.legend(fontsize=9)
    ax3.set_ylim(0, max(max(lighter), max(darker)) * 1.2)

    # ===== (D) Race Drift Distribution =====
    ax4 = fig.add_subplot(gs[1, 0])
    data = [stats[r]["race_drift"] for r in races_present]
    bp = ax4.boxplot(data, tick_labels=labels, patch_artist=True)
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax4.set_ylabel("Score (1-5)", fontsize=11)
    ax4.set_title("(D) Race Drift Distribution\n(1=none, 5=complete change)", fontsize=12, fontweight='bold')
    ax4.axhline(y=1, color='green', linestyle='--', alpha=0.5, label='Ideal (no drift)')
    ax4.legend(fontsize=9)
    ax4.set_ylim(0.5, 5.5)

    # ===== (E) Edit Success Distribution =====
    ax5 = fig.add_subplot(gs[1, 1])
    data = [stats[r]["edit_success"] for r in races_present]
    bp = ax5.boxplot(data, tick_labels=labels, patch_artist=True)
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax5.set_ylabel("Score (1-5)", fontsize=11)
    ax5.set_title("(E) Edit Success Distribution\n(1=failed, 5=perfect)", fontsize=12, fontweight='bold')
    ax5.axhline(y=3, color='orange', linestyle='--', alpha=0.5, label='Threshold')
    ax5.legend(fontsize=9)
    ax5.set_ylim(0.5, 5.5)

    # ===== (F) Disparity Summary =====
    ax6 = fig.add_subplot(gs[1, 2])

    # Calculate disparities
    metrics = {
        'Identity\nErasure': [stats[r]["identity_erasure"] / stats[r]["count"] * 100 for r in races_present],
        'Soft\nErasure': [stats[r]["soft_erasure"] / stats[r]["count"] * 100 for r in races_present],
        'Skin\nLightening': [stats[r]["skin_lighter"] / stats[r]["count"] * 100 for r in races_present],
        'Race\nDrift': [np.mean(stats[r]["race_drift"]) for r in races_present],
    }

    disparities = []
    metric_names = []
    for name, values in metrics.items():
        disparities.append(max(values) - min(values))
        metric_names.append(name)

    bars = ax6.barh(range(len(disparities)), disparities, color=['#d73027', '#fc8d59', '#fee08b', '#91cf60'])
    ax6.set_yticks(range(len(metric_names)))
    ax6.set_yticklabels(metric_names, fontsize=10)
    ax6.set_xlabel("Disparity (Max - Min across races)", fontsize=11)
    ax6.set_title("(F) Racial Disparity Summary\n(higher = more unfair)", fontsize=12, fontweight='bold')

    # Add value labels
    for bar, val in zip(bars, disparities):
        unit = "pp" if "Erasure" in metric_names[bars.index(bar)] or "Light" in metric_names[bars.index(bar)] else ""
        ax6.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                f'{val:.1f}{unit}', ha='left', va='center', fontsize=10, fontweight='bold')

    # Main title
    n_total = total_n if total_n else sum(stats[r]["count"] for r in stats if r in RACES)
    cat_str = categories if categories else "Category D: Vulnerability Prompts"
    fig.suptitle(f"Racial Disparity in I2I Image Editing ({model_name}, N={n_total})\n{cat_str}",
                 fontsize=14, fontweight='bold', y=0.98)

    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ Saved: {output_path}")
    plt.close()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, default="data/results/evaluations/exp1/flux/exp1_flux_results.jsonl")
    parser.add_argument("--output", type=str, default="data/results/evaluations/exp1/flux/exp1_flux_race_disparity.png")
    parser.add_argument("--model", type=str, default="FLUX.2-dev", help="Model name for title")
    parser.add_argument("--categories", type=str, default=None, help="Category description for subtitle")
    args = parser.parse_args()

    file_path = Path(args.file)
    output_path = Path(args.output)

    print(f"📂 Loading: {file_path}")
    results = load_results(file_path)
    print(f"📊 Loaded {len(results)} results")

    stats = compute_stats(results)
    create_summary_figure(stats, output_path, model_name=args.model, categories=args.categories)


if __name__ == "__main__":
    main()
