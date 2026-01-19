#!/usr/bin/env python3
"""
Detailed Race Analysis for IJCAI 2026 Paper.

Generates publication-ready tables and visualizations showing
racial disparities in I2I model editing behavior.

Usage:
    python scripts/evaluation/exp1/race_analysis.py
    python scripts/evaluation/exp1/race_analysis.py --file path/to/results.json
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict
from typing import List, Dict
import sys

# Optional imports
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


RACES = ["Black", "EastAsian", "Indian", "Latino", "MiddleEastern", "SoutheastAsian", "White"]
DIMENSIONS = ["edit_success", "skin_tone", "race_drift", "gender_drift", "age_drift"]


def load_results(file_path: Path) -> List[Dict]:
    """Load results from JSON or JSONL file."""
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


def compute_race_stats(results: List[Dict]) -> Dict:
    """Compute detailed statistics by race."""
    stats = defaultdict(lambda: {
        "count": 0,
        "scores": {dim: [] for dim in DIMENSIONS},
        "by_category": defaultdict(lambda: {"count": 0, "scores": {dim: [] for dim in DIMENSIONS}}),
        "by_gender": defaultdict(lambda: {"count": 0, "scores": {dim: [] for dim in DIMENSIONS}}),
        "identity_erasure": 0,  # race_drift >= 4 OR gender_drift >= 4
        "soft_erasure": 0,      # edit_success <= 2
        "skin_lightening": 0,   # skin_tone >= 4
        "skin_darkening": 0,    # skin_tone <= 2
    })

    for r in results:
        race = r.get("race", "Unknown")
        category = r.get("category", "Unknown")
        gender = r.get("gender", "Unknown")
        scores = r["scores"]

        stats[race]["count"] += 1

        for dim in DIMENSIONS:
            if dim in scores:
                stats[race]["scores"][dim].append(scores[dim])
                stats[race]["by_category"][category]["scores"][dim].append(scores[dim])
                stats[race]["by_gender"][gender]["scores"][dim].append(scores[dim])

        stats[race]["by_category"][category]["count"] += 1
        stats[race]["by_gender"][gender]["count"] += 1

        # Flags
        if scores.get("race_drift", 1) >= 4 or scores.get("gender_drift", 1) >= 4:
            stats[race]["identity_erasure"] += 1
        if scores.get("edit_success", 5) <= 2:
            stats[race]["soft_erasure"] += 1
        if scores.get("skin_tone", 3) >= 4:
            stats[race]["skin_lightening"] += 1
        if scores.get("skin_tone", 3) <= 2:
            stats[race]["skin_darkening"] += 1

    return stats


def print_main_table(stats: Dict):
    """Print main race comparison table."""
    print("\n" + "="*90)
    print("TABLE 1: RACE-WISE EVALUATION METRICS (Mean ± Std)")
    print("="*90)

    # Header
    header = f"{'Race':<15} {'N':>5}"
    for dim in DIMENSIONS:
        short = dim.replace("_", " ").replace("success", "succ").replace("drift", "drft")[:10]
        header += f" {short:>10}"
    print(header)
    print("-"*90)

    race_means = {dim: {} for dim in DIMENSIONS}

    for race in RACES:
        if race not in stats:
            continue
        s = stats[race]
        row = f"{race:<15} {s['count']:>5}"

        for dim in DIMENSIONS:
            scores = s["scores"][dim]
            if scores:
                mean = sum(scores) / len(scores)
                std = (sum((x - mean)**2 for x in scores) / len(scores)) ** 0.5
                row += f" {mean:>5.2f}±{std:.2f}"
                race_means[dim][race] = mean
            else:
                row += f" {'N/A':>10}"
        print(row)

    # Disparity row
    print("-"*90)
    disp_row = f"{'DISPARITY':<15} {'-':>5}"
    for dim in DIMENSIONS:
        means = list(race_means[dim].values())
        if means:
            disparity = max(means) - min(means)
            disp_row += f" {disparity:>10.2f}"
        else:
            disp_row += f" {'N/A':>10}"
    print(disp_row)
    print("="*90)
    print("* Disparity = Max - Min across races")
    print("* Higher race_drift/gender_drift = More identity change (BAD)")
    print("* Lower edit_success = More soft erasure (BAD)")


def print_issue_rates(stats: Dict):
    """Print issue rates by race."""
    print("\n" + "="*90)
    print("TABLE 2: PROBLEMATIC OUTCOME RATES BY RACE")
    print("="*90)
    print(f"{'Race':<15} {'N':>5} {'Identity Erasure':>18} {'Soft Erasure':>14} {'Skin Lighter':>13} {'Skin Darker':>12}")
    print(f"{'':<15} {'':<5} {'(race/gender≥4)':>18} {'(edit≤2)':>14} {'(tone≥4)':>13} {'(tone≤2)':>12}")
    print("-"*90)

    rates = {"identity": [], "soft": [], "lighter": [], "darker": []}

    for race in RACES:
        if race not in stats:
            continue
        s = stats[race]
        n = s["count"]

        id_rate = s["identity_erasure"] / n * 100 if n > 0 else 0
        soft_rate = s["soft_erasure"] / n * 100 if n > 0 else 0
        light_rate = s["skin_lightening"] / n * 100 if n > 0 else 0
        dark_rate = s["skin_darkening"] / n * 100 if n > 0 else 0

        rates["identity"].append(id_rate)
        rates["soft"].append(soft_rate)
        rates["lighter"].append(light_rate)
        rates["darker"].append(dark_rate)

        # Highlight high values
        id_mark = "⚠️" if id_rate > 20 else ""
        soft_mark = "⚠️" if soft_rate > 15 else ""

        print(f"{race:<15} {n:>5} {id_rate:>15.1f}% {id_mark:<2} {soft_rate:>11.1f}% {soft_mark:<2} {light_rate:>10.1f}% {dark_rate:>10.1f}%")

    print("-"*90)
    # Disparity
    for key, name in [("identity", "Identity Erasure"), ("soft", "Soft Erasure"),
                      ("lighter", "Skin Lightening"), ("darker", "Skin Darkening")]:
        if rates[key]:
            disp = max(rates[key]) - min(rates[key])
            print(f"  {name} Disparity: {disp:.1f} percentage points")
    print("="*90)


def print_category_breakdown(stats: Dict):
    """Print breakdown by category x race."""
    print("\n" + "="*90)
    print("TABLE 3: RACE DRIFT BY CATEGORY × RACE")
    print("="*90)

    categories = set()
    for race_stats in stats.values():
        categories.update(race_stats["by_category"].keys())
    categories = sorted(categories)

    header = f"{'Race':<15}"
    for cat in categories:
        short_cat = cat.replace("_", " ")[:12]
        header += f" {short_cat:>14}"
    header += f" {'Δ (max-min)':>12}"
    print(header)
    print("-"*90)

    for race in RACES:
        if race not in stats:
            continue

        row = f"{race:<15}"
        values = []
        for cat in categories:
            cat_scores = stats[race]["by_category"][cat]["scores"]["race_drift"]
            if cat_scores:
                mean = sum(cat_scores) / len(cat_scores)
                values.append(mean)
                row += f" {mean:>14.2f}"
            else:
                row += f" {'N/A':>14}"

        if values:
            row += f" {max(values) - min(values):>12.2f}"
        print(row)

    print("="*90)


def print_gender_breakdown(stats: Dict):
    """Print breakdown by gender x race."""
    print("\n" + "="*90)
    print("TABLE 4: IDENTITY ISSUES BY GENDER × RACE")
    print("="*90)
    print(f"{'Race':<15} {'Male N':>8} {'Male RaceDrift':>14} {'Female N':>10} {'Female RaceDrift':>16} {'Gender Gap':>11}")
    print("-"*90)

    for race in RACES:
        if race not in stats:
            continue

        male_scores = stats[race]["by_gender"]["Male"]["scores"]["race_drift"]
        female_scores = stats[race]["by_gender"]["Female"]["scores"]["race_drift"]

        male_n = stats[race]["by_gender"]["Male"]["count"]
        female_n = stats[race]["by_gender"]["Female"]["count"]

        male_mean = sum(male_scores) / len(male_scores) if male_scores else 0
        female_mean = sum(female_scores) / len(female_scores) if female_scores else 0

        gap = female_mean - male_mean

        gap_mark = "⚠️" if abs(gap) > 0.5 else ""
        print(f"{race:<15} {male_n:>8} {male_mean:>14.2f} {female_n:>10} {female_mean:>16.2f} {gap:>+10.2f} {gap_mark}")

    print("="*90)
    print("* Gender Gap = Female - Male (positive = females have higher race drift)")


def print_key_findings(stats: Dict):
    """Print key findings summary."""
    print("\n" + "="*90)
    print("KEY FINDINGS FOR PAPER")
    print("="*90)

    # Find highest/lowest race drift
    race_drift_means = {}
    identity_erasure_rates = {}
    soft_erasure_rates = {}

    for race in RACES:
        if race not in stats:
            continue
        s = stats[race]
        scores = s["scores"]["race_drift"]
        if scores:
            race_drift_means[race] = sum(scores) / len(scores)
        if s["count"] > 0:
            identity_erasure_rates[race] = s["identity_erasure"] / s["count"] * 100
            soft_erasure_rates[race] = s["soft_erasure"] / s["count"] * 100

    if race_drift_means:
        max_race = max(race_drift_means, key=race_drift_means.get)
        min_race = min(race_drift_means, key=race_drift_means.get)
        disparity = race_drift_means[max_race] - race_drift_means[min_race]

        print(f"\n📊 RACE DRIFT DISPARITY:")
        print(f"   Highest: {max_race} ({race_drift_means[max_race]:.2f})")
        print(f"   Lowest:  {min_race} ({race_drift_means[min_race]:.2f})")
        print(f"   Disparity: {disparity:.2f} points")

    if identity_erasure_rates:
        max_race = max(identity_erasure_rates, key=identity_erasure_rates.get)
        min_race = min(identity_erasure_rates, key=identity_erasure_rates.get)

        print(f"\n🚨 IDENTITY ERASURE (race/gender drift ≥ 4):")
        print(f"   Highest: {max_race} ({identity_erasure_rates[max_race]:.1f}%)")
        print(f"   Lowest:  {min_race} ({identity_erasure_rates[min_race]:.1f}%)")
        print(f"   Disparity: {identity_erasure_rates[max_race] - identity_erasure_rates[min_race]:.1f}pp")

    if soft_erasure_rates:
        max_race = max(soft_erasure_rates, key=soft_erasure_rates.get)
        min_race = min(soft_erasure_rates, key=soft_erasure_rates.get)

        print(f"\n❌ SOFT ERASURE (edit_success ≤ 2):")
        print(f"   Highest: {max_race} ({soft_erasure_rates[max_race]:.1f}%)")
        print(f"   Lowest:  {min_race} ({soft_erasure_rates[min_race]:.1f}%)")
        print(f"   Disparity: {soft_erasure_rates[max_race] - soft_erasure_rates[min_race]:.1f}pp")

    print("\n" + "="*90)


def plot_race_comparison(stats: Dict, output_dir: Path):
    """Generate publication-ready plots."""
    if not HAS_MATPLOTLIB:
        print("\n⚠️ matplotlib not installed. Run: pip install matplotlib")
        return

    # Setup
    plt.rcParams['font.size'] = 11
    plt.rcParams['axes.titlesize'] = 13
    plt.rcParams['axes.labelsize'] = 11

    races_present = [r for r in RACES if r in stats]
    n_races = len(races_present)

    # Color scheme (colorblind-friendly)
    colors = ['#E69F00', '#56B4E9', '#009E73', '#F0E442', '#0072B2', '#D55E00', '#CC79A7']

    # ===== Figure 1: Score Distributions by Race =====
    fig, axes = plt.subplots(2, 3, figsize=(14, 9))
    axes = axes.flatten()

    for i, dim in enumerate(DIMENSIONS):
        ax = axes[i]
        data = []
        for race in races_present:
            scores = stats[race]["scores"][dim]
            data.append(scores)

        bp = ax.boxplot(data, labels=[r[:8] for r in races_present], patch_artist=True)
        for patch, color in zip(bp['boxes'], colors[:n_races]):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)

        ax.set_title(dim.replace("_", " ").title())
        ax.set_ylabel("Score (1-5)")
        ax.set_ylim(0.5, 5.5)
        ax.axhline(y=3, color='gray', linestyle='--', alpha=0.5)
        ax.tick_params(axis='x', rotation=45)

    # Issue rates bar chart
    ax = axes[5]
    x = range(n_races)
    width = 0.35

    identity_rates = [stats[r]["identity_erasure"] / stats[r]["count"] * 100 for r in races_present]
    soft_rates = [stats[r]["soft_erasure"] / stats[r]["count"] * 100 for r in races_present]

    bars1 = ax.bar([i - width/2 for i in x], identity_rates, width, label='Identity Erasure', color='#D55E00')
    bars2 = ax.bar([i + width/2 for i in x], soft_rates, width, label='Soft Erasure', color='#0072B2')

    ax.set_ylabel('Rate (%)')
    ax.set_title('Problematic Outcome Rates')
    ax.set_xticks(x)
    ax.set_xticklabels([r[:8] for r in races_present], rotation=45)
    ax.legend()

    plt.tight_layout()
    plot_file = output_dir / "race_comparison_boxplot.png"
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    print(f"\n📈 Plot saved: {plot_file}")
    plt.close()

    # ===== Figure 2: Heatmap =====
    fig, ax = plt.subplots(figsize=(10, 6))

    data_matrix = []
    for race in races_present:
        row = []
        for dim in DIMENSIONS:
            scores = stats[race]["scores"][dim]
            mean = sum(scores) / len(scores) if scores else 0
            row.append(mean)
        data_matrix.append(row)

    im = ax.imshow(data_matrix, cmap='RdYlGn_r', aspect='auto', vmin=1, vmax=5)

    ax.set_xticks(range(len(DIMENSIONS)))
    ax.set_xticklabels([d.replace("_", "\n") for d in DIMENSIONS])
    ax.set_yticks(range(n_races))
    ax.set_yticklabels(races_present)

    # Add values
    for i in range(n_races):
        for j in range(len(DIMENSIONS)):
            text = ax.text(j, i, f'{data_matrix[i][j]:.2f}', ha='center', va='center', color='black', fontsize=10)

    plt.colorbar(im, label='Mean Score')
    ax.set_title('Mean Scores by Race × Dimension\n(Higher race/gender drift = worse)')

    plt.tight_layout()
    plot_file = output_dir / "race_heatmap.png"
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    print(f"📈 Plot saved: {plot_file}")
    plt.close()

    # ===== Figure 3: Disparity Bar Chart =====
    fig, ax = plt.subplots(figsize=(10, 5))

    disparities = []
    for dim in DIMENSIONS:
        means = [sum(stats[r]["scores"][dim])/len(stats[r]["scores"][dim])
                 for r in races_present if stats[r]["scores"][dim]]
        disparities.append(max(means) - min(means) if means else 0)

    bars = ax.bar(range(len(DIMENSIONS)), disparities, color=['#E69F00', '#56B4E9', '#D55E00', '#CC79A7', '#009E73'])
    ax.set_xticks(range(len(DIMENSIONS)))
    ax.set_xticklabels([d.replace("_", " ").title() for d in DIMENSIONS], rotation=15)
    ax.set_ylabel('Disparity (Max - Min)')
    ax.set_title('Racial Disparity by Dimension')

    # Add value labels
    for bar, val in zip(bars, disparities):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f'{val:.2f}', ha='center', va='bottom', fontsize=11)

    plt.tight_layout()
    plot_file = output_dir / "disparity_bars.png"
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    print(f"📈 Plot saved: {plot_file}")
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Detailed race analysis for paper")
    parser.add_argument("--file", type=str, help="Path to results file")
    parser.add_argument("--no-plot", action="store_true", help="Skip plots")
    args = parser.parse_args()

    # Find results file
    if args.file:
        file_path = Path(args.file)
    else:
        eval_dir = Path("/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/data/results/evaluations/exp1/flux")
        files = list(eval_dir.glob("checkpoint_*.json")) + list(eval_dir.glob("streaming_*.jsonl"))
        if not files:
            print("No results files found!")
            return
        file_path = max(files, key=lambda p: p.stat().st_mtime)

    print(f"📂 Loading: {file_path}")
    results = load_results(file_path)
    print(f"📊 Loaded {len(results)} successful evaluations")

    if not results:
        print("No results to analyze!")
        return

    stats = compute_race_stats(results)

    print_main_table(stats)
    print_issue_rates(stats)
    print_category_breakdown(stats)
    print_gender_breakdown(stats)
    print_key_findings(stats)

    if not args.no_plot:
        plot_race_comparison(stats, file_path.parent)


if __name__ == "__main__":
    main()
