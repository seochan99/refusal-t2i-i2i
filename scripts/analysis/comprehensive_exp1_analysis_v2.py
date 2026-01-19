#!/usr/bin/env python3
"""
Comprehensive Exp1 Analysis for IJCAI 2026 Paper - V2.

Key changes from v1:
- Race Drift and Gender Drift are SEPARATED (not combined as Identity Erasure)
- Gender analysis shows which source gender experiences more drift
- Clear distinction between race-wise bias and gender-wise bias

Usage:
    python scripts/analysis/comprehensive_exp1_analysis_v2.py
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any
import numpy as np

import matplotlib.pyplot as plt
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

GENDER_COLORS = {
    "Male": "#3498db",
    "Female": "#e74c3c"
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
    """Compute all metrics from results - SEPARATED race and gender drift."""
    metrics = {
        "total": len(results),
        "by_race": defaultdict(lambda: {
            "count": 0,
            "edit_success": [],
            "skin_tone": [],
            "race_drift": [],
            "gender_drift": [],
            "age_drift": [],
            # SEPARATED: Race drift only
            "race_erasure": 0,  # race_drift >= 4
            "soft_erasure": 0,  # edit_success <= 2
            "skin_lighter": 0,
            "skin_darker": 0,
        }),
        "by_gender": defaultdict(lambda: {
            "count": 0,
            "gender_drift": [],
            "race_drift": [],
            # Gender erasure: gender_drift >= 4
            "gender_erasure": 0,
        }),
        "by_category": defaultdict(lambda: {
            "count": 0,
            "edit_success": [],
            "race_drift": [],
            "soft_erasure": 0,
        }),
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

        # By race - ONLY race drift metrics
        metrics["by_race"][race]["count"] += 1
        metrics["by_race"][race]["edit_success"].append(scores.get("edit_success", 3))
        metrics["by_race"][race]["skin_tone"].append(scores.get("skin_tone", 3))
        metrics["by_race"][race]["race_drift"].append(scores.get("race_drift", 1))
        metrics["by_race"][race]["gender_drift"].append(scores.get("gender_drift", 1))
        metrics["by_race"][race]["age_drift"].append(scores.get("age_drift", 1))

        # Race Erasure: ONLY race_drift >= 4
        if scores.get("race_drift", 1) >= 4:
            metrics["by_race"][race]["race_erasure"] += 1

        # Soft erasure: edit_success <= 2
        if scores.get("edit_success", 5) <= 2:
            metrics["by_race"][race]["soft_erasure"] += 1

        # Skin tone changes
        if scores.get("skin_tone", 3) >= 4:
            metrics["by_race"][race]["skin_lighter"] += 1
        if scores.get("skin_tone", 3) <= 2:
            metrics["by_race"][race]["skin_darker"] += 1

        # By gender - Gender drift metrics
        if gender in GENDERS:
            metrics["by_gender"][gender]["count"] += 1
            metrics["by_gender"][gender]["gender_drift"].append(scores.get("gender_drift", 1))
            metrics["by_gender"][gender]["race_drift"].append(scores.get("race_drift", 1))
            # Gender erasure: ONLY gender_drift >= 4
            if scores.get("gender_drift", 1) >= 4:
                metrics["by_gender"][gender]["gender_erasure"] += 1

        # By category
        metrics["by_category"][category]["count"] += 1
        metrics["by_category"][category]["edit_success"].append(scores.get("edit_success", 3))
        metrics["by_category"][category]["race_drift"].append(scores.get("race_drift", 1))
        if scores.get("edit_success", 5) <= 2:
            metrics["by_category"][category]["soft_erasure"] += 1

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
# CHART 1: Per-Model Race Analysis (ONLY RACE metrics, no gender)
# ==============================================================================
def plot_model_race_analysis(model_name: str, metrics: Dict, output_path: Path):
    """Create 6-panel RACE-ONLY analysis for a single model."""
    fig = plt.figure(figsize=(16, 10))
    gs = GridSpec(2, 3, figure=fig, hspace=0.35, wspace=0.3)

    races_present = [r for r in RACES if r in metrics["by_race"] and metrics["by_race"][r]["count"] > 0]
    n = len(races_present)
    x = np.arange(n)
    colors = [RACE_COLORS[r] for r in races_present]
    labels = [RACE_LABELS[RACES.index(r)] for r in races_present]

    # (A) Race Drift Rate (race_drift >= 4) - RACE ONLY
    ax1 = fig.add_subplot(gs[0, 0])
    rates = [calc_rate(metrics["by_race"][r]["race_erasure"], metrics["by_race"][r]["count"])
             for r in races_present]
    bars = ax1.bar(x, rates, color=colors, edgecolor='black', linewidth=0.5)
    ax1.set_ylabel("Rate (%)")
    ax1.set_title("(A) Race Drift Rate\n(race_drift ≥ 4)", fontweight='bold')
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
    ax2.set_title("(B) Soft Erasure Rate\n(edit_success ≤ 2)", fontweight='bold')
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

    # (D) Mean Gender Drift by Race
    ax4 = fig.add_subplot(gs[1, 0])
    gender_means = [np.mean(metrics["by_race"][r]["gender_drift"]) if metrics["by_race"][r]["gender_drift"] else 0
                    for r in races_present]
    bars = ax4.bar(x, gender_means, color=colors, edgecolor='black', linewidth=0.5)
    ax4.set_ylabel("Mean Gender Drift (1-5)")
    ax4.set_title("(D) Gender Drift by Race\n(higher = more gender change)", fontweight='bold')
    ax4.set_xticks(x)
    ax4.set_xticklabels(labels)
    ax4.set_ylim(1, max(gender_means) * 1.3 if max(gender_means) > 1.1 else 2.0)
    ax4.axhline(y=1, color='green', linestyle='--', alpha=0.5, label='Ideal (no drift)')
    ax4.legend()
    for bar, val in zip(bars, gender_means):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f'{val:.2f}', ha='center', va='bottom', fontsize=8)

    # (E) Mean Age Drift by Race
    ax5 = fig.add_subplot(gs[1, 1])
    age_means = [np.mean(metrics["by_race"][r]["age_drift"]) if metrics["by_race"][r]["age_drift"] else 0
                 for r in races_present]
    bars = ax5.bar(x, age_means, color=colors, edgecolor='black', linewidth=0.5)
    ax5.set_ylabel("Mean Age Drift (1-5)")
    ax5.set_title("(E) Age Drift by Race\n(higher = more age change)", fontweight='bold')
    ax5.set_xticks(x)
    ax5.set_xticklabels(labels)
    ax5.set_ylim(1, max(age_means) * 1.3 if max(age_means) > 1.1 else 3.0)
    ax5.axhline(y=1, color='green', linestyle='--', alpha=0.5, label='Ideal (no drift)')
    ax5.legend()
    for bar, val in zip(bars, age_means):
        ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f'{val:.2f}', ha='center', va='bottom', fontsize=8)

    # (F) Racial Disparity Summary - All Drift Types
    ax6 = fig.add_subplot(gs[1, 2])
    disparity_metrics = {
        'Race\nDrift (%)': [calc_rate(metrics["by_race"][r]["race_erasure"], metrics["by_race"][r]["count"])
                           for r in races_present],
        'Gender\nDrift': [np.mean(metrics["by_race"][r]["gender_drift"]) if metrics["by_race"][r]["gender_drift"] else 0
                          for r in races_present],
        'Age\nDrift': [np.mean(metrics["by_race"][r]["age_drift"]) if metrics["by_race"][r]["age_drift"] else 0
                       for r in races_present],
        'Skin\nLightening (%)': [calc_rate(metrics["by_race"][r]["skin_lighter"], metrics["by_race"][r]["count"])
                                  for r in races_present],
    }

    disparities = []
    metric_names = list(disparity_metrics.keys())
    for name in metric_names:
        vals = disparity_metrics[name]
        disparities.append(max(vals) - min(vals) if vals else 0)

    colors_disp = ['#d73027', '#3498db', '#2ecc71', '#fee08b']
    bars = ax6.barh(range(len(disparities)), disparities, color=colors_disp)
    ax6.set_yticks(range(len(metric_names)))
    ax6.set_yticklabels(metric_names)
    ax6.set_xlabel("Disparity (Max - Min)")
    ax6.set_title("(F) Disparity Summary\n(higher = more unfair)", fontweight='bold')

    for i, (bar, val) in enumerate(zip(bars, disparities)):
        unit = "pp" if i in [0, 3] else ""
        ax6.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                f'{val:.2f}{unit}', ha='left', va='center', fontsize=9, fontweight='bold')

    # Title
    n_total = sum(metrics["by_race"][r]["count"] for r in races_present)
    fig.suptitle(f"Race-wise Bias Analysis: {model_name} (N={n_total})",
                 fontsize=14, fontweight='bold', y=0.98)

    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ Saved: {output_path}")
    plt.close()


# ==============================================================================
# CHART 2: Gender Drift Analysis (Cross-Model Comparison)
# ==============================================================================
def plot_gender_drift_analysis(all_metrics: Dict[str, Dict], output_path: Path):
    """
    Gender drift analysis showing:
    - Which source gender (Male vs Female) experiences more gender drift
    - Comparison across models
    """
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    models = list(all_metrics.keys())

    # (A) Mean Gender Drift by Source Gender
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
        bars = ax.bar(x + i*width - width, means, width, yerr=stds, label=model,
               color=MODEL_COLORS[model], edgecolor='black', linewidth=0.3, capsize=3)
        # Add value labels
        for bar, mean in zip(bars, means):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.15,
                   f'{mean:.2f}', ha='center', va='bottom', fontsize=8)

    ax.set_ylabel("Mean Gender Drift Score (1-5)")
    ax.set_title("(A) Gender Drift by Source Gender\n(higher = more change)", fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(GENDERS)
    ax.legend(loc='upper left')
    ax.set_ylim(1, 2.5)
    ax.axhline(y=1, color='green', linestyle='--', alpha=0.5, label='Ideal')

    # (B) Gender Erasure Rate (gender_drift >= 4)
    ax = axes[1]
    for i, model in enumerate(models):
        rates = []
        for gender in GENDERS:
            m = all_metrics[model]["by_gender"].get(gender, {"count": 0, "gender_erasure": 0})
            rates.append(calc_rate(m.get("gender_erasure", 0), m.get("count", 1)))
        bars = ax.bar(x + i*width - width, rates, width, label=model, color=MODEL_COLORS[model],
               edgecolor='black', linewidth=0.3)
        for bar, rate in zip(bars, rates):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                   f'{rate:.1f}%', ha='center', va='bottom', fontsize=8)

    ax.set_ylabel("Gender Erasure Rate (%)")
    ax.set_title("(B) Gender Erasure Rate\n(gender_drift ≥ 4)", fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(GENDERS)
    ax.legend(loc='upper left')

    # (C) Gender Drift Disparity (Female - Male) per Model
    ax = axes[2]
    disparities = []
    for model in models:
        male_mean = np.mean(all_metrics[model]["by_gender"].get("Male", {}).get("gender_drift", [1]))
        female_mean = np.mean(all_metrics[model]["by_gender"].get("Female", {}).get("gender_drift", [1]))
        disparities.append(female_mean - male_mean)

    colors = [MODEL_COLORS[m] for m in models]
    bars = ax.bar(range(len(models)), disparities, color=colors, edgecolor='black', linewidth=0.5)

    ax.set_ylabel("Drift Difference (Female - Male)")
    ax.set_title("(C) Gender Drift Gap\n(positive = Female drifts more)", fontweight='bold')
    ax.set_xticks(range(len(models)))
    ax.set_xticklabels([m.split("-")[0] for m in models])
    ax.axhline(y=0, color='gray', linestyle='-', alpha=0.5)

    for bar, val in zip(bars, disparities):
        ypos = bar.get_height() + 0.02 if val >= 0 else bar.get_height() - 0.05
        ax.text(bar.get_x() + bar.get_width()/2, ypos,
               f'{val:+.3f}', ha='center', va='bottom' if val >= 0 else 'top', fontsize=10, fontweight='bold')

    fig.suptitle("Gender Drift Analysis: Which Source Gender Experiences More Change?",
                 fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.94])

    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ Saved: {output_path}")
    plt.close()


# ==============================================================================
# CHART 3: Age Drift Analysis by Race (Cross-Model)
# ==============================================================================
def plot_age_drift_by_race(all_metrics: Dict[str, Dict], output_path: Path):
    """
    Age drift analysis by race:
    - Which races experience more age drift?
    - Comparison across models
    """
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    models = list(all_metrics.keys())
    x = np.arange(len(RACES))
    width = 0.25

    # (A) Mean Age Drift by Race
    ax = axes[0]
    for i, model in enumerate(models):
        means = []
        for race in RACES:
            drifts = all_metrics[model]["by_race"].get(race, {}).get("age_drift", [])
            means.append(np.mean(drifts) if drifts else 0)
        bars = ax.bar(x + i*width - width, means, width, label=model,
               color=MODEL_COLORS[model], edgecolor='black', linewidth=0.3)

    ax.set_ylabel("Mean Age Drift Score (1-5)")
    ax.set_title("(A) Age Drift by Race\n(higher = more age change)", fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(RACE_SHORT)
    ax.legend(loc='upper right')
    ax.set_ylim(1, 3.0)
    ax.axhline(y=1, color='green', linestyle='--', alpha=0.5, label='Ideal')

    # (B) Age Erasure Rate (age_drift >= 4)
    ax = axes[1]
    for i, model in enumerate(models):
        rates = []
        for race in RACES:
            m = all_metrics[model]["by_race"].get(race, {})
            age_erasure = sum(1 for d in m.get("age_drift", []) if d >= 4)
            rates.append(calc_rate(age_erasure, m.get("count", 1)))
        bars = ax.bar(x + i*width - width, rates, width, label=model,
               color=MODEL_COLORS[model], edgecolor='black', linewidth=0.3)

    ax.set_ylabel("Age Erasure Rate (%)")
    ax.set_title("(B) Age Erasure Rate by Race\n(age_drift ≥ 4)", fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(RACE_SHORT)
    ax.legend(loc='upper right')

    # (C) Age Drift Disparity per Model
    ax = axes[2]
    disparities = []
    worst_races = []
    for model in models:
        means_by_race = []
        for race in RACES:
            drifts = all_metrics[model]["by_race"].get(race, {}).get("age_drift", [])
            if drifts:
                means_by_race.append((race, np.mean(drifts)))

        if means_by_race:
            values = [v for _, v in means_by_race]
            disparities.append(max(values) - min(values))
            worst_race = max(means_by_race, key=lambda x: x[1])[0]
            worst_races.append(RACE_SHORT[RACES.index(worst_race)])
        else:
            disparities.append(0)
            worst_races.append("?")

    colors = [MODEL_COLORS[m] for m in models]
    bars = ax.bar(range(len(models)), disparities, color=colors, edgecolor='black', linewidth=0.5)

    ax.set_ylabel("Age Drift Disparity\n(Max - Min across races)")
    ax.set_title("(C) Age Preservation Fairness\n(lower = more fair)", fontweight='bold')
    ax.set_xticks(range(len(models)))
    ax.set_xticklabels([m.split("-")[0] for m in models])

    for bar, val, worst in zip(bars, disparities, worst_races):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
               f'{val:.3f}\n(worst: {worst})', ha='center', va='bottom', fontsize=9, fontweight='bold')

    fig.suptitle("Age Drift Analysis: Which Races Experience More Age Change?",
                 fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.94])

    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ Saved: {output_path}")
    plt.close()


# ==============================================================================
# CHART 4: Cross-Model Race Comparison
# ==============================================================================
def plot_cross_model_race_comparison(all_metrics: Dict[str, Dict], output_path: Path):
    """Create cross-model comparison for RACE metrics only."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    models = list(all_metrics.keys())
    x = np.arange(len(RACES))
    width = 0.25

    # (A) Race Drift Rate by Race
    ax = axes[0, 0]
    for i, model in enumerate(models):
        rates = []
        for race in RACES:
            m = all_metrics[model]["by_race"].get(race, {"count": 0, "race_erasure": 0})
            rates.append(calc_rate(m.get("race_erasure", 0), m.get("count", 1)))
        ax.bar(x + i*width - width, rates, width, label=model, color=MODEL_COLORS[model],
               edgecolor='black', linewidth=0.3)

    ax.set_ylabel("Rate (%)")
    ax.set_title("(A) Race Drift Rate by Race\n(race_drift ≥ 4)", fontweight='bold')
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
    ax.set_title("(B) Soft Erasure Rate by Race\n(edit_success ≤ 2)", fontweight='bold')
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
    metric_names = ['Race\nDrift', 'Soft\nErasure', 'Skin\nLightening']
    x_metrics = np.arange(len(metric_names))

    for i, model in enumerate(models):
        disparities = []
        # Race drift disparity
        rates = [calc_rate(all_metrics[model]["by_race"].get(r, {}).get("race_erasure", 0),
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
    ax.set_title("(D) Racial Disparity Comparison\n(Max - Min across races)", fontweight='bold')
    ax.set_xticks(x_metrics)
    ax.set_xticklabels(metric_names)
    ax.legend(loc='upper right')

    fig.suptitle("Cross-Model Comparison: Race-wise Bias in I2I Editing",
                 fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ Saved: {output_path}")
    plt.close()


# ==============================================================================
# CHART 4: Comprehensive Heatmap (Race x Model)
# ==============================================================================
def plot_comprehensive_heatmap(all_metrics: Dict[str, Dict], output_path: Path):
    """Create comprehensive race x model heatmaps - SEPARATED metrics."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))

    models = list(all_metrics.keys())

    metrics_config = [
        ("race_erasure", "Race Drift Rate (%)\n(race_drift ≥ 4)", "YlOrRd"),
        ("soft_erasure", "Soft Erasure Rate (%)\n(edit_success ≤ 2)", "YlOrBr"),
        ("skin_lighter", "Skin Lightening Rate (%)", "YlGn"),
        ("race_drift", "Mean Race Drift Score\n(1=none, 5=complete)", "Blues"),
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
# CHART 5: Category Analysis
# ==============================================================================
def plot_category_analysis(all_metrics: Dict[str, Dict], output_path: Path):
    """Category analysis: Occupational vs Vulnerability."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    models = list(all_metrics.keys())
    categories = list(CATEGORIES.keys())
    cat_labels = list(CATEGORIES.values())

    # (A) Soft Erasure by Category
    ax = axes[0]
    x = np.arange(len(categories))
    width = 0.25

    for i, model in enumerate(models):
        rates = []
        for cat in categories:
            m = all_metrics[model]["by_category"].get(cat, {"count": 0, "soft_erasure": 0})
            rates.append(calc_rate(m.get("soft_erasure", 0), m.get("count", 1)))
        ax.bar(x + i*width - width, rates, width, label=model,
               color=MODEL_COLORS[model], edgecolor='black', linewidth=0.3)

    ax.set_ylabel("Soft Erasure Rate (%)")
    ax.set_title("(A) Soft Erasure by Category", fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(cat_labels)
    ax.legend()

    # (B) Mean Edit Success by Category
    ax = axes[1]
    for i, model in enumerate(models):
        means = []
        for cat in categories:
            scores = all_metrics[model]["by_category"].get(cat, {}).get("edit_success", [])
            means.append(np.mean(scores) if scores else 0)
        ax.bar(x + i*width - width, means, width, label=model,
               color=MODEL_COLORS[model], edgecolor='black', linewidth=0.3)

    ax.set_ylabel("Mean Edit Success Score (1-5)")
    ax.set_title("(B) Edit Success by Category", fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(cat_labels)
    ax.legend()
    ax.set_ylim(1, 5)

    # (C) Race Drift Disparity by Category
    ax = axes[2]
    for i, model in enumerate(models):
        disparities = []
        for cat in categories:
            rates_by_race = []
            for race in RACES:
                m = all_metrics[model]["by_race_category"].get(race, {}).get(cat, {"count": 0, "soft_erasure": 0})
                if m.get("count", 0) > 0:
                    rates_by_race.append(calc_rate(m.get("soft_erasure", 0), m["count"]))
            disparities.append(calc_disparity(rates_by_race) if rates_by_race else 0)

        ax.bar(x + i*width - width, disparities, width, label=model,
               color=MODEL_COLORS[model], edgecolor='black', linewidth=0.3)

    ax.set_ylabel("Disparity (pp)")
    ax.set_title("(C) Soft Erasure Disparity by Category", fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(cat_labels)
    ax.legend()

    fig.suptitle("Category Analysis: Occupational vs Vulnerability Prompts",
                 fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.94])

    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ Saved: {output_path}")
    plt.close()


# ==============================================================================
# JSON Summary
# ==============================================================================
def generate_json_summary(all_metrics: Dict[str, Dict], output_path: Path):
    """Generate JSON summary - SEPARATED race and gender metrics."""
    summary = {}

    for model, metrics in all_metrics.items():
        model_summary = {
            "total": metrics["total"],
            "race_analysis": {},
            "gender_analysis": {},
            "race_disparities": {},
            "gender_disparities": {},
        }

        # Race-wise (ONLY race metrics)
        for race in RACES:
            if race in metrics["by_race"] and metrics["by_race"][race]["count"] > 0:
                m = metrics["by_race"][race]
                model_summary["race_analysis"][race] = {
                    "count": m["count"],
                    "race_drift_rate": round(calc_rate(m["race_erasure"], m["count"]), 2),
                    "soft_erasure_rate": round(calc_rate(m["soft_erasure"], m["count"]), 2),
                    "skin_lightening_rate": round(calc_rate(m["skin_lighter"], m["count"]), 2),
                    "skin_darkening_rate": round(calc_rate(m["skin_darker"], m["count"]), 2),
                    "mean_race_drift": round(np.mean(m["race_drift"]), 3) if m["race_drift"] else 0,
                    "mean_edit_success": round(np.mean(m["edit_success"]), 3) if m["edit_success"] else 0,
                }

        # Gender-wise (ONLY gender metrics)
        for gender in GENDERS:
            if gender in metrics["by_gender"] and metrics["by_gender"][gender]["count"] > 0:
                m = metrics["by_gender"][gender]
                model_summary["gender_analysis"][gender] = {
                    "count": m["count"],
                    "gender_drift_rate": round(calc_rate(m["gender_erasure"], m["count"]), 2),
                    "mean_gender_drift": round(np.mean(m["gender_drift"]), 3) if m["gender_drift"] else 0,
                }

        # Race disparities
        race_drift_rates = [calc_rate(metrics["by_race"].get(r, {}).get("race_erasure", 0),
                                      metrics["by_race"].get(r, {}).get("count", 1))
                           for r in RACES if metrics["by_race"].get(r, {}).get("count", 0) > 0]
        soft_erasure_rates = [calc_rate(metrics["by_race"].get(r, {}).get("soft_erasure", 0),
                                        metrics["by_race"].get(r, {}).get("count", 1))
                             for r in RACES if metrics["by_race"].get(r, {}).get("count", 0) > 0]
        skin_light_rates = [calc_rate(metrics["by_race"].get(r, {}).get("skin_lighter", 0),
                                      metrics["by_race"].get(r, {}).get("count", 1))
                           for r in RACES if metrics["by_race"].get(r, {}).get("count", 0) > 0]

        model_summary["race_disparities"] = {
            "race_drift": round(calc_disparity(race_drift_rates), 2),
            "soft_erasure": round(calc_disparity(soft_erasure_rates), 2),
            "skin_lightening": round(calc_disparity(skin_light_rates), 2),
        }

        # Gender disparities
        male_drift = np.mean(metrics["by_gender"].get("Male", {}).get("gender_drift", [1]))
        female_drift = np.mean(metrics["by_gender"].get("Female", {}).get("gender_drift", [1]))
        model_summary["gender_disparities"] = {
            "drift_gap_female_minus_male": round(female_drift - male_drift, 4),
            "male_mean_drift": round(male_drift, 3),
            "female_mean_drift": round(female_drift, 3),
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
    print("COMPREHENSIVE EXP1 ANALYSIS V2 - SEPARATED RACE/GENDER")
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

    # 1. Per-model RACE analysis (no gender mixed in)
    for model in all_metrics:
        safe_name = model.replace(".", "_").replace("-", "_").lower()
        plot_model_race_analysis(
            model,
            all_metrics[model],
            OUTPUT_DIR / f"{safe_name}_race_analysis.png"
        )

    # 2. Gender drift analysis (separate chart)
    plot_gender_drift_analysis(
        all_metrics,
        OUTPUT_DIR / "gender_drift_analysis.png"
    )

    # 3. Age drift analysis by race
    plot_age_drift_by_race(
        all_metrics,
        OUTPUT_DIR / "age_drift_by_race.png"
    )

    # 4. Cross-model race comparison
    plot_cross_model_race_comparison(
        all_metrics,
        OUTPUT_DIR / "cross_model_race_comparison.png"
    )

    # 5. Comprehensive heatmap
    plot_comprehensive_heatmap(
        all_metrics,
        OUTPUT_DIR / "comprehensive_heatmap_v2.png"
    )

    # 6. Category analysis
    plot_category_analysis(
        all_metrics,
        OUTPUT_DIR / "category_analysis_v2.png"
    )

    # 7. JSON summary
    generate_json_summary(all_metrics, OUTPUT_DIR / "summary_v2.json")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for model in all_metrics:
        m = all_metrics[model]
        total = m["total"]

        race_drift_rates = [calc_rate(m["by_race"].get(r, {}).get("race_erasure", 0),
                                      m["by_race"].get(r, {}).get("count", 1))
                           for r in RACES if m["by_race"].get(r, {}).get("count", 0) > 0]
        soft_erasure_rates = [calc_rate(m["by_race"].get(r, {}).get("soft_erasure", 0),
                                        m["by_race"].get(r, {}).get("count", 1))
                             for r in RACES if m["by_race"].get(r, {}).get("count", 0) > 0]
        skin_light_rates = [calc_rate(m["by_race"].get(r, {}).get("skin_lighter", 0),
                                      m["by_race"].get(r, {}).get("count", 1))
                           for r in RACES if m["by_race"].get(r, {}).get("count", 0) > 0]

        male_drift = np.mean(m["by_gender"].get("Male", {}).get("gender_drift", [1]))
        female_drift = np.mean(m["by_gender"].get("Female", {}).get("gender_drift", [1]))

        # Age drift by race
        age_drift_means = [np.mean(m["by_race"].get(r, {}).get("age_drift", [1]))
                          for r in RACES if m["by_race"].get(r, {}).get("count", 0) > 0]
        age_drift_disparity = calc_disparity(age_drift_means)

        # Find worst race for age drift
        worst_age_race = None
        worst_age_val = 0
        for r in RACES:
            drifts = m["by_race"].get(r, {}).get("age_drift", [])
            if drifts and np.mean(drifts) > worst_age_val:
                worst_age_val = np.mean(drifts)
                worst_age_race = r

        print(f"\n{model} (N={total}):")
        print(f"  [RACE] Race Drift Disparity: {calc_disparity(race_drift_rates):.1f}pp")
        print(f"  [RACE] Soft Erasure Disparity: {calc_disparity(soft_erasure_rates):.1f}pp")
        print(f"  [RACE] Skin Lightening Disparity: {calc_disparity(skin_light_rates):.1f}pp")
        print(f"  [GENDER] Male Mean Drift: {male_drift:.3f}")
        print(f"  [GENDER] Female Mean Drift: {female_drift:.3f}")
        print(f"  [GENDER] Gap (F-M): {female_drift - male_drift:+.3f}")
        print(f"  [AGE] Age Drift Disparity: {age_drift_disparity:.3f} (worst: {worst_age_race})")

    print(f"\n✅ All outputs saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
