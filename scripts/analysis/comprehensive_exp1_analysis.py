#!/usr/bin/env python3
"""
Comprehensive Exp1 Analysis for IJCAI 2026 Paper.

Generates publication-ready charts and tables for:
1. Per-model analysis (FLUX, Qwen, Step1X)
2. Cross-model comparison
3. Race-wise and Gender-wise breakdowns
4. Soft erasure, race drift, skin tone metrics

Usage:
    python scripts/analysis/comprehensive_exp1_analysis.py
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Any, Optional
import numpy as np

# Scientific plotting
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "results" / "evaluations" / "exp1"
OUTPUT_DIR = PROJECT_ROOT / "paper" / "figures" / "exp1_analysis"

# Constants
RACES = ["White", "Black", "EastAsian", "SoutheastAsian", "Indian", "MiddleEastern", "Latino"]
RACE_LABELS = ["White", "Black", "East\nAsian", "SE\nAsian", "Indian", "Middle\nEastern", "Latino"]
RACE_SHORT = ["W", "B", "EA", "SEA", "I", "ME", "L"]

GENDERS = ["Male", "Female"]
AGES = ["20s", "30s", "40s", "50s", "60s", "70+"]

MODELS = ["FLUX.2-dev", "Qwen-Edit", "Step1X-Edit"]
MODEL_FILES = {
    "FLUX.2-dev": "flux/exp1_flux_results.jsonl",
    "Qwen-Edit": "qwen/exp1_qwen_results.jsonl",
    "Step1X-Edit": "step1x/exp1_step1x_results.jsonl"
}

CATEGORIES = {
    "B_occupation": "Occupational",
    "D_vulnerability": "Vulnerability"
}

# Color palettes
RACE_COLORS = {
    "White": "#4575b4",
    "Black": "#d73027",
    "EastAsian": "#91cf60",
    "SoutheastAsian": "#1a9850",
    "Indian": "#fee08b",
    "MiddleEastern": "#fc8d59",
    "Latino": "#9e0142"
}

MODEL_COLORS = {
    "FLUX.2-dev": "#1f77b4",
    "Qwen-Edit": "#ff7f0e",
    "Step1X-Edit": "#2ca02c"
}

CATEGORY_COLORS = {
    "B_occupation": "#3498db",
    "D_vulnerability": "#e74c3c"
}

# Matplotlib style
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 10,
    'axes.titlesize': 12,
    'axes.labelsize': 11,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.dpi': 150
})


def load_results(model_name: str) -> List[Dict]:
    """Load results for a model."""
    file_path = DATA_DIR / MODEL_FILES[model_name]
    results = []

    if not file_path.exists():
        print(f"⚠️  File not found: {file_path}")
        return results

    with open(file_path, "r") as f:
        for line in f:
            if line.strip():
                try:
                    r = json.loads(line)
                    if r.get("success", False) and "scores" in r:
                        results.append(r)
                except json.JSONDecodeError:
                    continue

    return results


def compute_metrics(results: List[Dict]) -> Dict[str, Any]:
    """Compute all metrics from results."""
    metrics = {
        "total": len(results),
        "by_race": defaultdict(lambda: {
            "count": 0,
            "edit_success": [],
            "skin_tone": [],
            "race_drift": [],
            "gender_drift": [],
            "age_drift": [],
            "identity_erasure": 0,
            "soft_erasure": 0,
            "skin_lighter": 0,
            "skin_darker": 0,
        }),
        "by_gender": defaultdict(lambda: {
            "count": 0,
            "gender_drift": [],
            "race_drift": [],
            "identity_erasure": 0,
        }),
        "by_category": defaultdict(lambda: {
            "count": 0,
            "edit_success": [],
            "race_drift": [],
        }),
        "by_race_gender": defaultdict(lambda: defaultdict(lambda: {
            "count": 0,
            "race_drift": [],
            "gender_drift": [],
            "identity_erasure": 0,
        })),
        "by_race_category": defaultdict(lambda: defaultdict(lambda: {
            "count": 0,
            "edit_success": [],
            "race_drift": [],
            "soft_erasure": 0,
        })),
    }

    for r in results:
        race = r.get("race", "Unknown")
        gender = r.get("gender", "Unknown")
        category = r.get("category", "Unknown")
        scores = r["scores"]

        if race not in RACES:
            continue

        # By race
        metrics["by_race"][race]["count"] += 1
        metrics["by_race"][race]["edit_success"].append(scores.get("edit_success", 3))
        metrics["by_race"][race]["skin_tone"].append(scores.get("skin_tone", 3))
        metrics["by_race"][race]["race_drift"].append(scores.get("race_drift", 1))
        metrics["by_race"][race]["gender_drift"].append(scores.get("gender_drift", 1))
        metrics["by_race"][race]["age_drift"].append(scores.get("age_drift", 1))

        # Identity erasure: race_drift >= 4 OR gender_drift >= 4
        if scores.get("race_drift", 1) >= 4 or scores.get("gender_drift", 1) >= 4:
            metrics["by_race"][race]["identity_erasure"] += 1

        # Soft erasure: edit_success <= 2
        if scores.get("edit_success", 5) <= 2:
            metrics["by_race"][race]["soft_erasure"] += 1

        # Skin tone changes
        if scores.get("skin_tone", 3) >= 4:
            metrics["by_race"][race]["skin_lighter"] += 1
        if scores.get("skin_tone", 3) <= 2:
            metrics["by_race"][race]["skin_darker"] += 1

        # By gender
        if gender in GENDERS:
            metrics["by_gender"][gender]["count"] += 1
            metrics["by_gender"][gender]["gender_drift"].append(scores.get("gender_drift", 1))
            metrics["by_gender"][gender]["race_drift"].append(scores.get("race_drift", 1))
            if scores.get("race_drift", 1) >= 4 or scores.get("gender_drift", 1) >= 4:
                metrics["by_gender"][gender]["identity_erasure"] += 1

        # By category
        metrics["by_category"][category]["count"] += 1
        metrics["by_category"][category]["edit_success"].append(scores.get("edit_success", 3))
        metrics["by_category"][category]["race_drift"].append(scores.get("race_drift", 1))

        # By race x gender
        if gender in GENDERS:
            metrics["by_race_gender"][race][gender]["count"] += 1
            metrics["by_race_gender"][race][gender]["race_drift"].append(scores.get("race_drift", 1))
            metrics["by_race_gender"][race][gender]["gender_drift"].append(scores.get("gender_drift", 1))
            if scores.get("race_drift", 1) >= 4 or scores.get("gender_drift", 1) >= 4:
                metrics["by_race_gender"][race][gender]["identity_erasure"] += 1

        # By race x category
        metrics["by_race_category"][race][category]["count"] += 1
        metrics["by_race_category"][race][category]["edit_success"].append(scores.get("edit_success", 3))
        metrics["by_race_category"][race][category]["race_drift"].append(scores.get("race_drift", 1))
        if scores.get("edit_success", 5) <= 2:
            metrics["by_race_category"][race][category]["soft_erasure"] += 1

    return metrics


def calc_rate(count: int, total: int) -> float:
    """Calculate percentage rate."""
    return (count / total * 100) if total > 0 else 0.0


def calc_disparity(values: List[float]) -> float:
    """Calculate max-min disparity."""
    if not values:
        return 0.0
    return max(values) - min(values)


# ==============================================================================
# CHART 1: Per-Model Race Disparity Summary (6-panel figure)
# ==============================================================================
def plot_model_race_summary(model_name: str, metrics: Dict, output_path: Path):
    """Create 6-panel race disparity summary for a single model."""
    fig = plt.figure(figsize=(16, 10))
    gs = GridSpec(2, 3, figure=fig, hspace=0.35, wspace=0.3)

    races_present = [r for r in RACES if r in metrics["by_race"] and metrics["by_race"][r]["count"] > 0]
    n = len(races_present)
    x = np.arange(n)
    colors = [RACE_COLORS[r] for r in races_present]
    labels = [RACE_LABELS[RACES.index(r)] for r in races_present]

    # (A) Identity Erasure Rate
    ax1 = fig.add_subplot(gs[0, 0])
    rates = [calc_rate(metrics["by_race"][r]["identity_erasure"], metrics["by_race"][r]["count"])
             for r in races_present]
    bars = ax1.bar(x, rates, color=colors, edgecolor='black', linewidth=0.5)
    ax1.set_ylabel("Rate (%)")
    ax1.set_title("(A) Identity Erasure Rate\n(race/gender drift ≥ 4)", fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.set_ylim(0, max(rates) * 1.3 if max(rates) > 0 else 20)
    mean_rate = np.mean(rates)
    ax1.axhline(y=mean_rate, color='gray', linestyle='--', alpha=0.7, label=f'Mean: {mean_rate:.1f}%')
    ax1.legend()
    for bar, val in zip(bars, rates):
        if val > 0:
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    f'{val:.1f}%', ha='center', va='bottom', fontsize=8)

    # (B) Soft Erasure Rate
    ax2 = fig.add_subplot(gs[0, 1])
    rates = [calc_rate(metrics["by_race"][r]["soft_erasure"], metrics["by_race"][r]["count"])
             for r in races_present]
    bars = ax2.bar(x, rates, color=colors, edgecolor='black', linewidth=0.5)
    ax2.set_ylabel("Rate (%)")
    ax2.set_title("(B) Soft Erasure Rate\n(edit success ≤ 2)", fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels)
    ax2.set_ylim(0, max(rates) * 1.3 if max(rates) > 0 else 10)
    mean_rate = np.mean(rates)
    ax2.axhline(y=mean_rate, color='gray', linestyle='--', alpha=0.7, label=f'Mean: {mean_rate:.1f}%')
    ax2.legend()
    for bar, val in zip(bars, rates):
        if val > 0:
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                    f'{val:.1f}%', ha='center', va='bottom', fontsize=8)

    # (C) Skin Tone Changes
    ax3 = fig.add_subplot(gs[0, 2])
    lighter = [calc_rate(metrics["by_race"][r]["skin_lighter"], metrics["by_race"][r]["count"])
               for r in races_present]
    darker = [calc_rate(metrics["by_race"][r]["skin_darker"], metrics["by_race"][r]["count"])
              for r in races_present]
    width = 0.35
    ax3.bar(x - width/2, lighter, width, label='Lightened (≥4)', color='#fee090', edgecolor='black', linewidth=0.5)
    ax3.bar(x + width/2, darker, width, label='Darkened (≤2)', color='#4575b4', edgecolor='black', linewidth=0.5)
    ax3.set_ylabel("Rate (%)")
    ax3.set_title("(C) Skin Tone Changes", fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels(labels)
    ax3.legend()
    max_val = max(max(lighter) if lighter else 0, max(darker) if darker else 0)
    ax3.set_ylim(0, max_val * 1.2 if max_val > 0 else 10)

    # (D) Race Drift Distribution
    ax4 = fig.add_subplot(gs[1, 0])
    data = [metrics["by_race"][r]["race_drift"] for r in races_present]
    bp = ax4.boxplot(data, tick_labels=labels, patch_artist=True)
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax4.set_ylabel("Score (1-5)")
    ax4.set_title("(D) Race Drift Distribution\n(1=none, 5=complete change)", fontweight='bold')
    ax4.axhline(y=1, color='green', linestyle='--', alpha=0.5, label='Ideal (no drift)')
    ax4.legend()
    ax4.set_ylim(0.5, 5.5)

    # (E) Edit Success Distribution
    ax5 = fig.add_subplot(gs[1, 1])
    data = [metrics["by_race"][r]["edit_success"] for r in races_present]
    bp = ax5.boxplot(data, tick_labels=labels, patch_artist=True)
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax5.set_ylabel("Score (1-5)")
    ax5.set_title("(E) Edit Success Distribution\n(1=failed, 5=perfect)", fontweight='bold')
    ax5.axhline(y=3, color='orange', linestyle='--', alpha=0.5, label='Threshold')
    ax5.legend()
    ax5.set_ylim(0.5, 5.5)

    # (F) Disparity Summary
    ax6 = fig.add_subplot(gs[1, 2])
    disparity_metrics = {
        'Identity\nErasure': [calc_rate(metrics["by_race"][r]["identity_erasure"], metrics["by_race"][r]["count"])
                              for r in races_present],
        'Soft\nErasure': [calc_rate(metrics["by_race"][r]["soft_erasure"], metrics["by_race"][r]["count"])
                          for r in races_present],
        'Skin\nLightening': [calc_rate(metrics["by_race"][r]["skin_lighter"], metrics["by_race"][r]["count"])
                             for r in races_present],
        'Race\nDrift (avg)': [np.mean(metrics["by_race"][r]["race_drift"]) if metrics["by_race"][r]["race_drift"] else 0
                              for r in races_present],
    }

    disparities = []
    metric_names = list(disparity_metrics.keys())
    for name in metric_names:
        vals = disparity_metrics[name]
        disparities.append(max(vals) - min(vals) if vals else 0)

    bars = ax6.barh(range(len(disparities)), disparities, color=['#d73027', '#fc8d59', '#fee08b', '#91cf60'])
    ax6.set_yticks(range(len(metric_names)))
    ax6.set_yticklabels(metric_names)
    ax6.set_xlabel("Disparity (Max - Min)")
    ax6.set_title("(F) Racial Disparity Summary\n(higher = more unfair)", fontweight='bold')

    for i, (bar, val) in enumerate(zip(bars, disparities)):
        unit = "pp" if i < 3 else ""
        ax6.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                f'{val:.1f}{unit}', ha='left', va='center', fontsize=9, fontweight='bold')

    # Title
    n_total = sum(metrics["by_race"][r]["count"] for r in races_present)
    fig.suptitle(f"Racial Disparity in I2I Editing: {model_name} (N={n_total})",
                 fontsize=14, fontweight='bold', y=0.98)

    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ Saved: {output_path}")
    plt.close()


# ==============================================================================
# CHART 2: Cross-Model Comparison
# ==============================================================================
def plot_cross_model_comparison(all_metrics: Dict[str, Dict], output_path: Path):
    """Create cross-model comparison figure."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    models = list(all_metrics.keys())
    x = np.arange(len(RACES))
    width = 0.25

    # (A) Identity Erasure by Race
    ax = axes[0, 0]
    for i, model in enumerate(models):
        rates = []
        for race in RACES:
            m = all_metrics[model]["by_race"].get(race, {"count": 0, "identity_erasure": 0})
            rates.append(calc_rate(m.get("identity_erasure", 0), m.get("count", 1)))
        ax.bar(x + i*width - width, rates, width, label=model, color=MODEL_COLORS[model],
               edgecolor='black', linewidth=0.3)

    ax.set_ylabel("Rate (%)")
    ax.set_title("(A) Identity Erasure Rate by Race", fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(RACE_SHORT)
    ax.legend(loc='upper right')
    ax.set_ylim(0, None)

    # (B) Soft Erasure by Race
    ax = axes[0, 1]
    for i, model in enumerate(models):
        rates = []
        for race in RACES:
            m = all_metrics[model]["by_race"].get(race, {"count": 0, "soft_erasure": 0})
            rates.append(calc_rate(m.get("soft_erasure", 0), m.get("count", 1)))
        ax.bar(x + i*width - width, rates, width, label=model, color=MODEL_COLORS[model],
               edgecolor='black', linewidth=0.3)

    ax.set_ylabel("Rate (%)")
    ax.set_title("(B) Soft Erasure Rate by Race", fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(RACE_SHORT)
    ax.legend(loc='upper right')

    # (C) Skin Lightening by Race
    ax = axes[1, 0]
    for i, model in enumerate(models):
        rates = []
        for race in RACES:
            m = all_metrics[model]["by_race"].get(race, {"count": 0, "skin_lighter": 0})
            rates.append(calc_rate(m.get("skin_lighter", 0), m.get("count", 1)))
        ax.bar(x + i*width - width, rates, width, label=model, color=MODEL_COLORS[model],
               edgecolor='black', linewidth=0.3)

    ax.set_ylabel("Rate (%)")
    ax.set_title("(C) Skin Lightening Rate by Race", fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(RACE_SHORT)
    ax.legend(loc='upper right')

    # (D) Model Summary (Disparity comparison)
    ax = axes[1, 1]
    metric_names = ['Identity\nErasure', 'Soft\nErasure', 'Skin\nLightening']
    x_metrics = np.arange(len(metric_names))

    for i, model in enumerate(models):
        disparities = []
        # Identity erasure disparity
        rates = [calc_rate(all_metrics[model]["by_race"].get(r, {}).get("identity_erasure", 0),
                          all_metrics[model]["by_race"].get(r, {}).get("count", 1))
                for r in RACES if all_metrics[model]["by_race"].get(r, {}).get("count", 0) > 0]
        disparities.append(calc_disparity(rates))

        # Soft erasure disparity
        rates = [calc_rate(all_metrics[model]["by_race"].get(r, {}).get("soft_erasure", 0),
                          all_metrics[model]["by_race"].get(r, {}).get("count", 1))
                for r in RACES if all_metrics[model]["by_race"].get(r, {}).get("count", 0) > 0]
        disparities.append(calc_disparity(rates))

        # Skin lightening disparity
        rates = [calc_rate(all_metrics[model]["by_race"].get(r, {}).get("skin_lighter", 0),
                          all_metrics[model]["by_race"].get(r, {}).get("count", 1))
                for r in RACES if all_metrics[model]["by_race"].get(r, {}).get("count", 0) > 0]
        disparities.append(calc_disparity(rates))

        ax.bar(x_metrics + i*width - width, disparities, width, label=model,
               color=MODEL_COLORS[model], edgecolor='black', linewidth=0.3)

    ax.set_ylabel("Disparity (pp)")
    ax.set_title("(D) Racial Disparity Comparison", fontweight='bold')
    ax.set_xticks(x_metrics)
    ax.set_xticklabels(metric_names)
    ax.legend(loc='upper right')

    fig.suptitle("Cross-Model Comparison: Racial Bias in I2I Editing",
                 fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ Saved: {output_path}")
    plt.close()


# ==============================================================================
# CHART 3: Gender Analysis
# ==============================================================================
def plot_gender_analysis(all_metrics: Dict[str, Dict], output_path: Path):
    """Create gender drift analysis figure."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    models = list(all_metrics.keys())

    # (A) Gender Drift by Gender across models
    ax = axes[0]
    x = np.arange(len(GENDERS))
    width = 0.25

    for i, model in enumerate(models):
        means = []
        stds = []
        for gender in GENDERS:
            drifts = all_metrics[model]["by_gender"].get(gender, {}).get("gender_drift", [])
            means.append(np.mean(drifts) if drifts else 0)
            stds.append(np.std(drifts) if drifts else 0)
        ax.bar(x + i*width - width, means, width, yerr=stds, label=model,
               color=MODEL_COLORS[model], edgecolor='black', linewidth=0.3, capsize=3)

    ax.set_ylabel("Mean Gender Drift Score")
    ax.set_title("(A) Gender Drift by Source Gender", fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(GENDERS)
    ax.legend()
    ax.set_ylim(1, 5)
    ax.axhline(y=1, color='green', linestyle='--', alpha=0.5)

    # (B) Identity Erasure by Gender
    ax = axes[1]
    for i, model in enumerate(models):
        rates = []
        for gender in GENDERS:
            m = all_metrics[model]["by_gender"].get(gender, {"count": 0, "identity_erasure": 0})
            rates.append(calc_rate(m.get("identity_erasure", 0), m.get("count", 1)))
        ax.bar(x + i*width - width, rates, width, label=model, color=MODEL_COLORS[model],
               edgecolor='black', linewidth=0.3)

    ax.set_ylabel("Identity Erasure Rate (%)")
    ax.set_title("(B) Identity Erasure by Source Gender", fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(GENDERS)
    ax.legend()

    # (C) Race x Gender Heatmap (using first model as example)
    ax = axes[2]
    model = models[0]  # FLUX

    data = np.zeros((len(RACES), len(GENDERS)))
    for i, race in enumerate(RACES):
        for j, gender in enumerate(GENDERS):
            m = all_metrics[model]["by_race_gender"].get(race, {}).get(gender, {"count": 0, "identity_erasure": 0})
            data[i, j] = calc_rate(m.get("identity_erasure", 0), m.get("count", 1))

    im = ax.imshow(data, cmap='YlOrRd', aspect='auto')
    ax.set_xticks(np.arange(len(GENDERS)))
    ax.set_yticks(np.arange(len(RACES)))
    ax.set_xticklabels(GENDERS)
    ax.set_yticklabels(RACE_SHORT)
    ax.set_title(f"(C) Identity Erasure: Race × Gender\n({model})", fontweight='bold')

    # Add text annotations
    for i in range(len(RACES)):
        for j in range(len(GENDERS)):
            text = ax.text(j, i, f'{data[i, j]:.1f}%',
                          ha="center", va="center", color="black" if data[i, j] < 50 else "white",
                          fontsize=9)

    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Rate (%)')

    fig.suptitle("Gender Analysis in I2I Editing", fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.94])

    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ Saved: {output_path}")
    plt.close()


# ==============================================================================
# CHART 4: Category Analysis (Occupational vs Vulnerability)
# ==============================================================================
def plot_category_analysis(all_metrics: Dict[str, Dict], output_path: Path):
    """Create category-wise analysis figure."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    models = list(all_metrics.keys())
    categories = list(CATEGORIES.keys())
    cat_labels = list(CATEGORIES.values())

    # (A) Edit Success by Category
    ax = axes[0]
    x = np.arange(len(categories))
    width = 0.25

    for i, model in enumerate(models):
        means = []
        for cat in categories:
            scores = all_metrics[model]["by_category"].get(cat, {}).get("edit_success", [])
            means.append(np.mean(scores) if scores else 0)
        ax.bar(x + i*width - width, means, width, label=model,
               color=MODEL_COLORS[model], edgecolor='black', linewidth=0.3)

    ax.set_ylabel("Mean Edit Success Score")
    ax.set_title("(A) Edit Success by Category", fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(cat_labels)
    ax.legend()
    ax.set_ylim(1, 5)

    # (B) Soft Erasure by Category x Race (Heatmap for first model)
    ax = axes[1]
    model = models[0]

    data = np.zeros((len(RACES), len(categories)))
    for i, race in enumerate(RACES):
        for j, cat in enumerate(categories):
            m = all_metrics[model]["by_race_category"].get(race, {}).get(cat, {"count": 0, "soft_erasure": 0})
            data[i, j] = calc_rate(m.get("soft_erasure", 0), m.get("count", 1))

    im = ax.imshow(data, cmap='YlOrRd', aspect='auto')
    ax.set_xticks(np.arange(len(categories)))
    ax.set_yticks(np.arange(len(RACES)))
    ax.set_xticklabels(cat_labels)
    ax.set_yticklabels(RACE_SHORT)
    ax.set_title(f"(B) Soft Erasure: Race × Category\n({model})", fontweight='bold')

    for i in range(len(RACES)):
        for j in range(len(categories)):
            text = ax.text(j, i, f'{data[i, j]:.1f}%',
                          ha="center", va="center", color="black" if data[i, j] < 30 else "white",
                          fontsize=9)

    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Rate (%)')

    # (C) Race Drift Comparison by Category
    ax = axes[2]
    for i, model in enumerate(models):
        for j, cat in enumerate(categories):
            drifts_by_race = []
            for race in RACES:
                drifts = all_metrics[model]["by_race_category"].get(race, {}).get(cat, {}).get("race_drift", [])
                if drifts:
                    drifts_by_race.append(np.mean(drifts))

            if drifts_by_race:
                disparity = max(drifts_by_race) - min(drifts_by_race)
                ax.bar(j + i*width - width, disparity, width,
                      color=MODEL_COLORS[model], edgecolor='black', linewidth=0.3,
                      label=model if j == 0 else "")

    ax.set_ylabel("Race Drift Disparity")
    ax.set_title("(C) Race Drift Disparity by Category", fontweight='bold')
    ax.set_xticks(range(len(categories)))
    ax.set_xticklabels(cat_labels)
    ax.legend()

    fig.suptitle("Category Analysis: Occupational vs Vulnerability Prompts", fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.94])

    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ Saved: {output_path}")
    plt.close()


# ==============================================================================
# CHART 5: Comprehensive Heatmap
# ==============================================================================
def plot_comprehensive_heatmap(all_metrics: Dict[str, Dict], output_path: Path):
    """Create comprehensive race x model heatmaps."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))

    models = list(all_metrics.keys())

    metrics_config = [
        ("identity_erasure", "Identity Erasure Rate (%)", "YlOrRd"),
        ("soft_erasure", "Soft Erasure Rate (%)", "YlOrBr"),
        ("skin_lighter", "Skin Lightening Rate (%)", "YlGn"),
        ("race_drift", "Mean Race Drift Score", "Blues"),
    ]

    for idx, (metric_key, title, cmap) in enumerate(metrics_config):
        ax = axes[idx // 2, idx % 2]

        data = np.zeros((len(RACES), len(models)))
        for i, race in enumerate(RACES):
            for j, model in enumerate(models):
                m = all_metrics[model]["by_race"].get(race, {})
                if metric_key == "race_drift":
                    vals = m.get(metric_key, [])
                    data[i, j] = np.mean(vals) if vals else 0
                else:
                    data[i, j] = calc_rate(m.get(metric_key, 0), m.get("count", 1))

        im = ax.imshow(data, cmap=cmap, aspect='auto')
        ax.set_xticks(np.arange(len(models)))
        ax.set_yticks(np.arange(len(RACES)))
        ax.set_xticklabels([m.replace("-", "\n") for m in models], fontsize=9)
        ax.set_yticklabels(RACE_SHORT)
        ax.set_title(title, fontweight='bold')

        # Add annotations
        for i in range(len(RACES)):
            for j in range(len(models)):
                fmt = f'{data[i, j]:.1f}' if metric_key != "race_drift" else f'{data[i, j]:.2f}'
                text_color = "black" if data[i, j] < np.mean(data) else "white"
                ax.text(j, i, fmt, ha="center", va="center", color=text_color, fontsize=8)

        cbar = fig.colorbar(im, ax=ax, shrink=0.8)

    fig.suptitle("Comprehensive Race × Model Analysis", fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ Saved: {output_path}")
    plt.close()


# ==============================================================================
# TABLE: Publication-ready summary tables
# ==============================================================================
def generate_latex_tables(all_metrics: Dict[str, Dict], output_path: Path):
    """Generate LaTeX tables for paper."""
    models = list(all_metrics.keys())

    lines = []
    lines.append("% Auto-generated from comprehensive_exp1_analysis.py")
    lines.append("")

    # Table 1: Per-Race Metrics Summary
    lines.append("% Table 1: Race-wise Metrics Summary")
    lines.append("\\begin{table}[h]")
    lines.append("\\centering")
    lines.append("\\caption{Race-wise Bias Metrics Across Models}")
    lines.append("\\label{tab:race-metrics}")
    lines.append("\\small")
    lines.append("\\begin{tabular}{l" + "ccc" * len(models) + "}")
    lines.append("\\toprule")

    # Header
    header = "Race"
    for model in models:
        short_name = model.split("-")[0]
        header += f" & \\multicolumn{{3}}{{c}}{{{short_name}}}"
    lines.append(header + " \\\\")

    subheader = ""
    for _ in models:
        subheader += " & IE & SE & SL"
    lines.append(subheader + " \\\\")
    lines.append("\\midrule")

    # Data rows
    for race in RACES:
        row = race.replace("East", "E.").replace("South", "S.").replace("Middle", "M.")
        for model in models:
            m = all_metrics[model]["by_race"].get(race, {"count": 0})
            ie = calc_rate(m.get("identity_erasure", 0), m.get("count", 1))
            se = calc_rate(m.get("soft_erasure", 0), m.get("count", 1))
            sl = calc_rate(m.get("skin_lighter", 0), m.get("count", 1))
            row += f" & {ie:.1f} & {se:.1f} & {sl:.1f}"
        lines.append(row + " \\\\")

    # Disparity row
    lines.append("\\midrule")
    row = "\\textbf{Disparity}"
    for model in models:
        ie_rates = [calc_rate(all_metrics[model]["by_race"].get(r, {}).get("identity_erasure", 0),
                             all_metrics[model]["by_race"].get(r, {}).get("count", 1))
                   for r in RACES if all_metrics[model]["by_race"].get(r, {}).get("count", 0) > 0]
        se_rates = [calc_rate(all_metrics[model]["by_race"].get(r, {}).get("soft_erasure", 0),
                             all_metrics[model]["by_race"].get(r, {}).get("count", 1))
                   for r in RACES if all_metrics[model]["by_race"].get(r, {}).get("count", 0) > 0]
        sl_rates = [calc_rate(all_metrics[model]["by_race"].get(r, {}).get("skin_lighter", 0),
                             all_metrics[model]["by_race"].get(r, {}).get("count", 1))
                   for r in RACES if all_metrics[model]["by_race"].get(r, {}).get("count", 0) > 0]

        ie_disp = calc_disparity(ie_rates)
        se_disp = calc_disparity(se_rates)
        sl_disp = calc_disparity(sl_rates)
        row += f" & {ie_disp:.1f} & {se_disp:.1f} & {sl_disp:.1f}"
    lines.append(row + " \\\\")

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\vspace{0.5em}")
    lines.append("\\\\\\footnotesize IE: Identity Erasure (\\%), SE: Soft Erasure (\\%), SL: Skin Lightening (\\%)")
    lines.append("\\end{table}")
    lines.append("")

    # Table 2: Model Comparison Summary
    lines.append("% Table 2: Model Comparison Summary")
    lines.append("\\begin{table}[h]")
    lines.append("\\centering")
    lines.append("\\caption{Cross-Model Comparison Summary}")
    lines.append("\\label{tab:model-comparison}")
    lines.append("\\begin{tabular}{lccc}")
    lines.append("\\toprule")
    lines.append("Metric & FLUX & Qwen & Step1X \\\\")
    lines.append("\\midrule")

    metric_labels = [
        ("Identity Erasure (\\%)", "identity_erasure"),
        ("Soft Erasure (\\%)", "soft_erasure"),
        ("Skin Lightening (\\%)", "skin_lighter"),
    ]

    for label, key in metric_labels:
        row = label
        for model in models:
            total = sum(all_metrics[model]["by_race"].get(r, {}).get("count", 0) for r in RACES)
            total_metric = sum(all_metrics[model]["by_race"].get(r, {}).get(key, 0) for r in RACES)
            rate = calc_rate(total_metric, total)
            row += f" & {rate:.1f}"
        lines.append(row + " \\\\")

    # Disparity rows
    lines.append("\\midrule")
    for label, key in metric_labels:
        row = f"\\quad Disparity"
        for model in models:
            rates = [calc_rate(all_metrics[model]["by_race"].get(r, {}).get(key, 0),
                              all_metrics[model]["by_race"].get(r, {}).get("count", 1))
                    for r in RACES if all_metrics[model]["by_race"].get(r, {}).get("count", 0) > 0]
            disp = calc_disparity(rates)
            row += f" & {disp:.1f}"
        lines.append(row + " \\\\")
        break  # Only show one disparity row as example

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table}")

    # Write to file
    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    print(f"✅ Saved: {output_path}")


# ==============================================================================
# JSON Summary for further processing
# ==============================================================================
def generate_json_summary(all_metrics: Dict[str, Dict], output_path: Path):
    """Generate JSON summary for further processing."""
    summary = {}

    for model, metrics in all_metrics.items():
        model_summary = {
            "total": metrics["total"],
            "by_race": {},
            "by_gender": {},
            "disparities": {},
        }

        # Race-wise
        for race in RACES:
            if race in metrics["by_race"] and metrics["by_race"][race]["count"] > 0:
                m = metrics["by_race"][race]
                model_summary["by_race"][race] = {
                    "count": m["count"],
                    "identity_erasure_rate": round(calc_rate(m["identity_erasure"], m["count"]), 2),
                    "soft_erasure_rate": round(calc_rate(m["soft_erasure"], m["count"]), 2),
                    "skin_lightening_rate": round(calc_rate(m["skin_lighter"], m["count"]), 2),
                    "skin_darkening_rate": round(calc_rate(m["skin_darker"], m["count"]), 2),
                    "mean_race_drift": round(np.mean(m["race_drift"]), 3) if m["race_drift"] else 0,
                    "mean_gender_drift": round(np.mean(m["gender_drift"]), 3) if m["gender_drift"] else 0,
                    "mean_edit_success": round(np.mean(m["edit_success"]), 3) if m["edit_success"] else 0,
                }

        # Gender-wise
        for gender in GENDERS:
            if gender in metrics["by_gender"] and metrics["by_gender"][gender]["count"] > 0:
                m = metrics["by_gender"][gender]
                model_summary["by_gender"][gender] = {
                    "count": m["count"],
                    "identity_erasure_rate": round(calc_rate(m["identity_erasure"], m["count"]), 2),
                    "mean_gender_drift": round(np.mean(m["gender_drift"]), 3) if m["gender_drift"] else 0,
                }

        # Disparities
        ie_rates = [calc_rate(metrics["by_race"].get(r, {}).get("identity_erasure", 0),
                             metrics["by_race"].get(r, {}).get("count", 1))
                   for r in RACES if metrics["by_race"].get(r, {}).get("count", 0) > 0]
        se_rates = [calc_rate(metrics["by_race"].get(r, {}).get("soft_erasure", 0),
                             metrics["by_race"].get(r, {}).get("count", 1))
                   for r in RACES if metrics["by_race"].get(r, {}).get("count", 0) > 0]
        sl_rates = [calc_rate(metrics["by_race"].get(r, {}).get("skin_lighter", 0),
                             metrics["by_race"].get(r, {}).get("count", 1))
                   for r in RACES if metrics["by_race"].get(r, {}).get("count", 0) > 0]

        model_summary["disparities"] = {
            "identity_erasure": round(calc_disparity(ie_rates), 2),
            "soft_erasure": round(calc_disparity(se_rates), 2),
            "skin_lightening": round(calc_disparity(sl_rates), 2),
        }

        summary[model] = model_summary

    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"✅ Saved: {output_path}")


# ==============================================================================
# MAIN
# ==============================================================================
def main():
    """Main function."""
    print("=" * 60)
    print("COMPREHENSIVE EXP1 ANALYSIS FOR IJCAI 2026")
    print("=" * 60)

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load all model results
    all_metrics = {}
    for model in MODELS:
        print(f"\n📂 Loading {model}...")
        results = load_results(model)
        print(f"   Loaded {len(results)} results")

        if results:
            metrics = compute_metrics(results)
            all_metrics[model] = metrics

    if not all_metrics:
        print("❌ No results loaded!")
        return

    print("\n" + "=" * 60)
    print("GENERATING CHARTS")
    print("=" * 60)

    # 1. Per-model race summary
    for model in all_metrics:
        safe_name = model.replace(".", "_").replace("-", "_").lower()
        plot_model_race_summary(
            model,
            all_metrics[model],
            OUTPUT_DIR / f"{safe_name}_race_summary.png"
        )

    # 2. Cross-model comparison
    plot_cross_model_comparison(
        all_metrics,
        OUTPUT_DIR / "cross_model_comparison.png"
    )

    # 3. Gender analysis
    plot_gender_analysis(
        all_metrics,
        OUTPUT_DIR / "gender_analysis.png"
    )

    # 4. Category analysis
    plot_category_analysis(
        all_metrics,
        OUTPUT_DIR / "category_analysis.png"
    )

    # 5. Comprehensive heatmap
    plot_comprehensive_heatmap(
        all_metrics,
        OUTPUT_DIR / "comprehensive_heatmap.png"
    )

    print("\n" + "=" * 60)
    print("GENERATING TABLES")
    print("=" * 60)

    # LaTeX tables
    generate_latex_tables(all_metrics, OUTPUT_DIR / "tables.tex")

    # JSON summary
    generate_json_summary(all_metrics, OUTPUT_DIR / "summary.json")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for model in all_metrics:
        m = all_metrics[model]
        total = m["total"]

        ie_rates = [calc_rate(m["by_race"].get(r, {}).get("identity_erasure", 0),
                             m["by_race"].get(r, {}).get("count", 1))
                   for r in RACES if m["by_race"].get(r, {}).get("count", 0) > 0]
        se_rates = [calc_rate(m["by_race"].get(r, {}).get("soft_erasure", 0),
                             m["by_race"].get(r, {}).get("count", 1))
                   for r in RACES if m["by_race"].get(r, {}).get("count", 0) > 0]
        sl_rates = [calc_rate(m["by_race"].get(r, {}).get("skin_lighter", 0),
                             m["by_race"].get(r, {}).get("count", 1))
                   for r in RACES if m["by_race"].get(r, {}).get("count", 0) > 0]

        print(f"\n{model} (N={total}):")
        print(f"  Identity Erasure Disparity: {calc_disparity(ie_rates):.1f}pp")
        print(f"  Soft Erasure Disparity: {calc_disparity(se_rates):.1f}pp")
        print(f"  Skin Lightening Disparity: {calc_disparity(sl_rates):.1f}pp")

    print(f"\n✅ All outputs saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
