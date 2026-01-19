#!/usr/bin/env python3
"""Generate paper figures for VLM evaluation results."""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Set style
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.dpi': 300,
})

OUTPUT_DIR = Path("/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/paper/I2I_Bias_Refusal/assets")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def figure_exp1_model_comparison():
    """EXP1: Model comparison across 4 metrics."""

    models = ['FLUX.2-dev', 'Step1X-Edit', 'Qwen-Edit']

    # Data from VLM evaluation
    edit_success = [92.4, 74.3, 93.9]
    race_drift = [13.4, 8.1, 9.2]
    skin_lighter = [70.7, 62.3, 67.2]
    gender_drift = [10.8, 7.2, 5.2]

    x = np.arange(len(models))
    width = 0.2

    fig, ax = plt.subplots(figsize=(6, 4))

    colors = ['#2ecc71', '#e74c3c', '#f39c12', '#9b59b6']

    bars1 = ax.bar(x - 1.5*width, edit_success, width, label='Edit Success (>=4)', color=colors[0])
    bars2 = ax.bar(x - 0.5*width, race_drift, width, label='Race Drift (>=3)', color=colors[1])
    bars3 = ax.bar(x + 0.5*width, skin_lighter, width, label='Skin Lighter (>=4)', color=colors[2])
    bars4 = ax.bar(x + 1.5*width, gender_drift, width, label='Gender Drift (>=3)', color=colors[3])

    ax.set_ylabel('Percentage (%)')
    ax.set_xticks(x)
    ax.set_xticklabels(models)
    ax.legend(loc='upper right', framealpha=0.9)
    ax.set_ylim(0, 100)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.yaxis.grid(True, linestyle='--', alpha=0.3)

    # Add value labels
    for bars in [bars1, bars2, bars3, bars4]:
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.1f}',
                       xy=(bar.get_x() + bar.get_width()/2, height),
                       xytext=(0, 2), textcoords="offset points",
                       ha='center', va='bottom', fontsize=7)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "exp1_model_comparison.pdf", bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / "exp1_model_comparison.png", bbox_inches='tight', dpi=300)
    print(f"Saved: {OUTPUT_DIR / 'exp1_model_comparison.pdf'}")
    plt.close()


def figure_exp2_feature_prompt_mitigation():
    """EXP2: Feature prompt mitigation effect by race."""

    # Data: Race drift reduction (Baseline - Feature), sorted by improvement
    races = ['Black', 'Indian', 'Latino', 'SE Asian', 'Mid East', 'E Asian', 'White']
    improvements = [1.48, 1.23, 1.08, 0.88, 0.79, 0.56, 0.06]

    fig, ax = plt.subplots(figsize=(5, 4))

    # Color gradient: darker = more improvement
    colors = plt.cm.Greens(np.linspace(0.3, 0.9, len(races)))[::-1]

    bars = ax.barh(races, improvements, color=colors, edgecolor='darkgreen', linewidth=0.5)

    ax.set_xlabel('Race Drift Reduction (Baseline - Feature Prompt)')
    ax.set_xlim(0, 1.7)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.xaxis.grid(True, linestyle='--', alpha=0.3)

    # Add value labels
    for bar, val in zip(bars, improvements):
        ax.annotate(f'+{val:.2f}',
                   xy=(val, bar.get_y() + bar.get_height()/2),
                   xytext=(3, 0), textcoords="offset points",
                   ha='left', va='center', fontsize=9, fontweight='bold')

    # Add annotation
    ax.annotate('Feature prompts benefit\nnon-White groups most',
               xy=(1.2, 0.5), fontsize=8, style='italic',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "exp2_feature_prompt_effect.pdf", bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / "exp2_feature_prompt_effect.png", bbox_inches='tight', dpi=300)
    print(f"Saved: {OUTPUT_DIR / 'exp2_feature_prompt_effect.pdf'}")
    plt.close()


def figure_combined_overview():
    """Combined figure with EXP1 (left) and EXP2 (right)."""

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    # === Left: EXP1 Model Comparison ===
    models = ['FLUX.2-dev', 'Step1X-Edit', 'Qwen-Edit']
    edit_success = [92.4, 74.3, 93.9]
    race_drift = [13.4, 8.1, 9.2]
    skin_lighter = [70.7, 62.3, 67.2]
    gender_drift = [10.8, 7.2, 5.2]

    x = np.arange(len(models))
    width = 0.2
    colors = ['#2ecc71', '#e74c3c', '#f39c12', '#9b59b6']

    ax1.bar(x - 1.5*width, edit_success, width, label='Edit Success', color=colors[0])
    ax1.bar(x - 0.5*width, race_drift, width, label='Race Drift', color=colors[1])
    ax1.bar(x + 0.5*width, skin_lighter, width, label='Skin Lighter', color=colors[2])
    ax1.bar(x + 1.5*width, gender_drift, width, label='Gender Drift', color=colors[3])

    ax1.set_ylabel('Percentage (%)')
    ax1.set_xticks(x)
    ax1.set_xticklabels(models, rotation=15)
    ax1.legend(loc='upper right', fontsize=8)
    ax1.set_ylim(0, 100)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.yaxis.grid(True, linestyle='--', alpha=0.3)
    ax1.set_title('(a) EXP1: Model Comparison', fontweight='bold')

    # === Right: EXP2 Feature Prompt Effect ===
    races = ['Black', 'Indian', 'Latino', 'SE Asian', 'Mid East', 'E Asian', 'White']
    improvements = [1.48, 1.23, 1.08, 0.88, 0.79, 0.56, 0.06]

    bar_colors = plt.cm.Greens(np.linspace(0.3, 0.9, len(races)))[::-1]
    bars = ax2.barh(races, improvements, color=bar_colors, edgecolor='darkgreen', linewidth=0.5)

    ax2.set_xlabel('Race Drift Reduction')
    ax2.set_xlim(0, 1.8)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.xaxis.grid(True, linestyle='--', alpha=0.3)
    ax2.set_title('(b) EXP2: Feature Prompt Mitigation', fontweight='bold')

    for bar, val in zip(bars, improvements):
        ax2.annotate(f'+{val:.2f}',
                    xy=(val, bar.get_y() + bar.get_height()/2),
                    xytext=(3, 0), textcoords="offset points",
                    ha='left', va='center', fontsize=8)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "exp_combined_overview.pdf", bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / "exp_combined_overview.png", bbox_inches='tight', dpi=300)
    print(f"Saved: {OUTPUT_DIR / 'exp_combined_overview.pdf'}")
    plt.close()


if __name__ == "__main__":
    print("Generating paper figures...")
    figure_exp1_model_comparison()
    figure_exp2_feature_prompt_mitigation()
    figure_combined_overview()
    print("Done!")
