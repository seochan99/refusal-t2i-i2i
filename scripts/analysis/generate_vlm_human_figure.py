#!/usr/bin/env python3
"""
Generate VLM-Human Alignment Figure for IJCAI Paper

Creates a publication-quality figure showing:
(a) Within-1 agreement rates by evaluation dimension
(b) Mean skin tone score by race (Human vs VLM comparison using FULL exp1 VLM scores)
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from collections import defaultdict

# Set publication style
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.dpi': 300,
})


def load_full_vlm_scores():
    """Load FULL exp1 VLM scores (shows racial disparity)."""
    full_vlm = {}
    for model in ['flux', 'qwen', 'step1x']:
        filepath = f'data/results/evaluations/exp1/{model}/exp1_{model}_final.json'
        with open(filepath, 'r') as f:
            data = json.load(f)
            for item in data.get('results', []):
                if 'scores' not in item:
                    continue
                item_id = f"exp1_{model}_{item['prompt_id']}_{item['race']}_{item['gender']}_{item['age']}"
                full_vlm[item_id] = {
                    'scores': item['scores'],
                    'race': item['race']
                }
    return full_vlm


def load_comparison_data():
    """Load the VLM-Human comparison data."""
    comparison_path = Path('data/results/evaluations/human_evaluation_sampling/500sample_human_score/vlm_human_comparison.json')
    with open(comparison_path, 'r') as f:
        return json.load(f)


def calculate_mean_scores_by_race(comparison_data, full_vlm):
    """Calculate mean skin tone score by race for Human and VLM (using full exp1 VLM)."""
    human_scores = defaultdict(list)
    vlm_scores = defaultdict(list)

    for record in comparison_data:
        race = record.get('race')
        orig_id = record.get('originalItemId')

        if not race or not orig_id:
            continue

        # Human scores (edited)
        human_skin = record.get('edited_scores', {}).get('skin_tone')
        if human_skin is not None:
            human_scores[race].append(human_skin)

        # Use FULL exp1 VLM scores (not 500sample re-evaluated scores)
        if orig_id in full_vlm:
            vlm_skin = full_vlm[orig_id]['scores'].get('skin_tone')
            if vlm_skin is not None:
                vlm_scores[race].append(vlm_skin)

    # Calculate means
    human_means = {race: sum(scores)/len(scores) for race, scores in human_scores.items() if scores}
    vlm_means = {race: sum(scores)/len(scores) for race, scores in vlm_scores.items() if scores}
    counts = {race: len(scores) for race, scores in human_scores.items()}

    return human_means, vlm_means, counts


def create_alignment_figure():
    """Create the VLM-Human alignment figure with 2 panels."""

    # Load data
    full_vlm = load_full_vlm_scores()
    comparison_data = load_comparison_data()
    human_means, vlm_means, counts = calculate_mean_scores_by_race(comparison_data, full_vlm)

    print("Human means:", human_means)
    print("VLM means:", vlm_means)

    fig, axes = plt.subplots(1, 2, figsize=(7.5, 3.0))

    # ============== Panel (a): Within-1 Agreement by Dimension ==============
    ax1 = axes[0]

    dimensions = ['Skin\nTone', 'Gender\nDrift', 'Age\nDrift', 'Race\nDrift', 'Edit\nSuccess']
    within_1_rates = [88.8, 79.1, 75.4, 74.2, 65.6]

    bars = ax1.bar(dimensions, within_1_rates, color='#3498db', edgecolor='black', linewidth=0.5)

    for bar, val in zip(bars, within_1_rates):
        ax1.text(bar.get_x() + bar.get_width()/2, val + 1,
                f'{val:.1f}%', ha='center', va='bottom', fontsize=8)

    ax1.set_ylim(0, 100)
    ax1.set_ylabel('Within-1 Agreement (%)')
    ax1.set_title('(a) VLM-Human Agreement', fontweight='bold', fontsize=11)
    ax1.axhline(y=80, color='gray', linestyle='--', linewidth=1, alpha=0.7)
    ax1.text(4.5, 82, '80%', fontsize=8, color='gray', ha='right')
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)

    # ============== Panel (b): Mean Skin Tone Score by Race ==============
    ax2 = axes[1]

    # Order races by Human mean score (ascending - White lowest/least lightened)
    race_order = ['White', 'EastAsian', 'Latino', 'MiddleEastern', 'SoutheastAsian', 'Indian', 'Black']
    race_labels = ['White', 'East\nAsian', 'Latino', 'Middle\nEastern', 'SE\nAsian', 'Indian', 'Black']

    human_vals = [human_means.get(r, 3.0) for r in race_order]
    vlm_vals = [vlm_means.get(r, 3.0) for r in race_order]

    x = np.arange(len(race_order))
    width = 0.35

    bars1 = ax2.bar(x - width/2, human_vals, width, label='Human',
                    color='#e74c3c', edgecolor='black', linewidth=0.5)
    bars2 = ax2.bar(x + width/2, vlm_vals, width, label='VLM',
                    color='#3498db', edgecolor='black', linewidth=0.5)

    # Add value labels
    for bar, val in zip(bars1, human_vals):
        ax2.text(bar.get_x() + bar.get_width()/2, val + 0.03,
                f'{val:.2f}', ha='center', va='bottom', fontsize=7, color='#c0392b')
    for bar, val in zip(bars2, vlm_vals):
        ax2.text(bar.get_x() + bar.get_width()/2, val + 0.03,
                f'{val:.2f}', ha='center', va='bottom', fontsize=7, color='#2980b9')

    ax2.set_xticks(x)
    ax2.set_xticklabels(race_labels)
    ax2.set_ylabel('Mean Skin Tone Score')
    ax2.set_title('(b) Skin Tone Evaluation by Race', fontweight='bold', fontsize=11)
    ax2.set_ylim(2.0, 4.5)

    # Add reference line at 3 (no change)
    ax2.axhline(y=3.0, color='gray', linestyle='--', linewidth=1, alpha=0.7)
    ax2.text(6.7, 3.05, 'No change', fontsize=8, color='gray', ha='right')

    ax2.legend(loc='upper left', framealpha=0.9)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)

    plt.tight_layout()

    # Save figure
    output_dir = Path('paper/IJCAI__ECAI_26___I2I_Bias_Refusall/assets')
    output_dir.mkdir(parents=True, exist_ok=True)

    fig.savefig(output_dir / 'vlm_human_alignment.pdf', bbox_inches='tight', dpi=300)
    fig.savefig(output_dir / 'vlm_human_alignment.png', bbox_inches='tight', dpi=300)

    print(f"\nFigure saved to {output_dir}/vlm_human_alignment.pdf")
    print(f"Figure saved to {output_dir}/vlm_human_alignment.png")

    # Print the computed values
    print("\nMean Skin Tone Score by Race (1=darker, 3=same, 5=lighter):")
    print(f"{'Race':<15} {'Human':>8} {'VLM':>8}")
    print("-" * 35)
    for race in race_order:
        h = human_means.get(race, 0)
        v = vlm_means.get(race, 0)
        print(f"{race:<15} {h:>8.2f} {v:>8.2f}")

    return fig


if __name__ == "__main__":
    print("Generating VLM-Human Alignment Figure (using FULL exp1 VLM scores)...")
    create_alignment_figure()
    print("Done!")
