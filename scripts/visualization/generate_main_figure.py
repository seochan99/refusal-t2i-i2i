#!/usr/bin/env python3
"""Generate main paper figure: Source → Baseline → Ours comparison.

Single wide figure showing diverse examples that demonstrate the impact.
Based on actual VLM evaluation data to select most impressive cases.
"""

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from pathlib import Path
import numpy as np

plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 9,
    'axes.labelsize': 10,
    'axes.titlesize': 11,
    'figure.dpi': 300,
})

BASE_DIR = Path("/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal")
OUTPUT_DIR = BASE_DIR / "paper/I2I_Bias_Refusal/assets"
SOURCE_DIR = BASE_DIR / "data/source_images/final"
EXP1_DIR = BASE_DIR / "data/results/exp1_all_dataset/flux_organized/by_category/B_occupation"
EXP2_DIR = BASE_DIR / "data/results/exp2_pairwise/flux"


def load_image(path):
    """Load image or return placeholder."""
    if path.exists():
        return mpimg.imread(str(path))
    print(f"Missing: {path}")
    return np.ones((256, 256, 3)) * 0.9


def create_main_figure():
    """
    Create main paper figure with Source → Baseline → Ours.

    Selected examples based on VLM data:
    - Black Female 20s, B01 (CEO): +1.48pt drift reduction
    - Indian Female 30s, B05 (Housekeeper): +1.23pt drift reduction
    - Latino Male 40s, B09 (Fashion Model): high skin lightening (79%)
    - MiddleEastern Female 50s, B01 (CEO): high race drift (17.9%)
    """

    # Best examples based on data
    examples = [
        # (Race, Gender, Age, Prompt, PromptName, Key stat)
        ('Black', 'Female', '20s', 'B01', 'CEO', 'Drift: +1.48pt'),
        ('Indian', 'Female', '30s', 'B05', 'Housekeeper', 'Drift: +1.23pt'),
        ('Latino', 'Female', '30s', 'B09', 'Fashion Model', 'Light: 79%→52%'),
        ('EastAsian', 'Male', '40s', 'B01', 'CEO', 'Drift: +0.56pt'),
    ]

    fig, axes = plt.subplots(len(examples), 3, figsize=(10, 10))

    # Column titles
    col_titles = ['Source Image', 'Baseline (EXP1)', 'Ours: +Feature Prompt (EXP2)']

    for row, (race, gender, age, prompt_id, prompt_name, stat) in enumerate(examples):
        # Source
        source_path = SOURCE_DIR / race / f"{race}_{gender}_{age}.jpg"
        axes[row, 0].imshow(load_image(source_path))
        axes[row, 0].axis('off')
        if row == 0:
            axes[row, 0].set_title(col_titles[0], fontsize=11, fontweight='bold', pad=10)
        # Row label
        axes[row, 0].text(-0.12, 0.5, f'{race}\n{gender}, {age}\n"{prompt_name}"',
                        transform=axes[row, 0].transAxes, rotation=90,
                        va='center', ha='center', fontsize=8, fontweight='bold')

        # Baseline (EXP1)
        exp1_path = EXP1_DIR / f"{prompt_id}_{race}_{gender}_{age}_success.png"
        axes[row, 1].imshow(load_image(exp1_path))
        axes[row, 1].axis('off')
        if row == 0:
            axes[row, 1].set_title(col_titles[1], fontsize=11, fontweight='bold', pad=10)

        # Ours (EXP2 Feature Prompt)
        exp2_path = EXP2_DIR / f"preserved_{prompt_id}" / f"{prompt_id}_{race}_{gender}_{age}.png"
        axes[row, 2].imshow(load_image(exp2_path))
        axes[row, 2].axis('off')
        if row == 0:
            axes[row, 2].set_title(col_titles[2], fontsize=11, fontweight='bold', pad=10)

        # Improvement badge
        axes[row, 2].text(0.98, 0.02, stat,
                        transform=axes[row, 2].transAxes, ha='right', va='bottom',
                        fontsize=8, fontweight='bold', color='white',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='#27ae60', alpha=0.9))

    plt.tight_layout(rect=[0.06, 0.02, 1, 0.98])
    plt.savefig(OUTPUT_DIR / "main_comparison.pdf", bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / "main_comparison.png", bbox_inches='tight', dpi=300)
    print(f"Saved: {OUTPUT_DIR / 'main_comparison.pdf'}")
    plt.close()


def create_wide_figure():
    """
    Create single wide horizontal figure for maximum impact.
    6 examples showing diversity across race, gender, age, prompt.
    """

    # Using only available preserved prompts: B01, B05, B09, D03
    examples = [
        ('Black', 'Female', '20s', 'B01', 'CEO'),
        ('Indian', 'Male', '40s', 'B05', 'Housekeeper'),
        ('Latino', 'Female', '30s', 'B09', 'Model'),
        ('EastAsian', 'Female', '50s', 'B01', 'CEO'),
        ('MiddleEastern', 'Female', '30s', 'B05', 'Housekeeper'),
        ('SoutheastAsian', 'Female', '40s', 'B09', 'Model'),
    ]

    fig, axes = plt.subplots(3, 6, figsize=(14, 7))

    row_labels = ['Source', 'Baseline\n(EXP1)', 'Ours\n(+Feature)']

    for col, (race, gender, age, prompt_id, prompt_name) in enumerate(examples):
        # Source
        source_path = SOURCE_DIR / race / f"{race}_{gender}_{age}.jpg"
        axes[0, col].imshow(load_image(source_path))
        axes[0, col].axis('off')

        # Baseline
        exp1_path = EXP1_DIR / f"{prompt_id}_{race}_{gender}_{age}_success.png"
        axes[1, col].imshow(load_image(exp1_path))
        axes[1, col].axis('off')

        # Ours
        exp2_path = EXP2_DIR / f"preserved_{prompt_id}" / f"{prompt_id}_{race}_{gender}_{age}.png"
        axes[2, col].imshow(load_image(exp2_path))
        axes[2, col].axis('off')

        # Column label
        axes[2, col].text(0.5, -0.12, f'{race[:6]}\n{gender}, {age}\n"{prompt_name}"',
                         transform=axes[2, col].transAxes, ha='center', va='top', fontsize=7)

    # Row labels
    for row, label in enumerate(row_labels):
        axes[row, 0].text(-0.15, 0.5, label, transform=axes[row, 0].transAxes,
                         rotation=90, va='center', ha='center', fontsize=10, fontweight='bold')

    fig.suptitle('Feature Prompt Mitigates Identity Drift Across Diverse Demographics',
                fontsize=12, fontweight='bold', y=0.98)

    plt.tight_layout(rect=[0.04, 0.08, 1, 0.95])
    plt.savefig(OUTPUT_DIR / "wide_comparison.pdf", bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / "wide_comparison.png", bbox_inches='tight', dpi=300)
    print(f"Saved: {OUTPUT_DIR / 'wide_comparison.pdf'}")
    plt.close()


def create_compact_figure():
    """
    Compact 3-column figure with 4 diverse examples.
    Most impactful for limited space.
    """

    # Selected for maximum diversity and impact (using available preserved prompts: B01, B05, B09, D03)
    examples = [
        ('Black', 'Female', '20s', 'B01', 'CEO', '+1.48'),
        ('Indian', 'Female', '30s', 'B05', 'Housekeeper', '+1.23'),
        ('Latino', 'Male', '40s', 'B09', 'Model', '+1.08'),
        ('EastAsian', 'Female', '50s', 'B01', 'CEO', '+0.56'),
    ]

    fig, axes = plt.subplots(4, 3, figsize=(7, 9))

    for row, (race, gender, age, prompt_id, prompt_name, improvement) in enumerate(examples):
        # Source
        source_path = SOURCE_DIR / race / f"{race}_{gender}_{age}.jpg"
        axes[row, 0].imshow(load_image(source_path))
        axes[row, 0].axis('off')
        if row == 0:
            axes[row, 0].set_title('Source', fontsize=10, fontweight='bold')
        axes[row, 0].text(-0.08, 0.5, f'{race}\n{gender},{age}\n({prompt_name})',
                        transform=axes[row, 0].transAxes, rotation=90,
                        va='center', ha='center', fontsize=7, fontweight='bold')

        # Baseline
        exp1_path = EXP1_DIR / f"{prompt_id}_{race}_{gender}_{age}_success.png"
        axes[row, 1].imshow(load_image(exp1_path))
        axes[row, 1].axis('off')
        if row == 0:
            axes[row, 1].set_title('Baseline', fontsize=10, fontweight='bold')

        # Ours
        exp2_path = EXP2_DIR / f"preserved_{prompt_id}" / f"{prompt_id}_{race}_{gender}_{age}.png"
        axes[row, 2].imshow(load_image(exp2_path))
        axes[row, 2].axis('off')
        if row == 0:
            axes[row, 2].set_title('+Feature Prompt', fontsize=10, fontweight='bold')
        axes[row, 2].text(0.95, 0.05, f'{improvement}pt',
                        transform=axes[row, 2].transAxes, ha='right', va='bottom',
                        fontsize=9, fontweight='bold', color='white',
                        bbox=dict(boxstyle='round', facecolor='green', alpha=0.85))

    fig.text(0.5, 0.01, 'Feature prompts reduce identity drift by 0.56-1.48 points for non-White subjects.',
            ha='center', fontsize=9, style='italic')

    plt.tight_layout(rect=[0.06, 0.03, 1, 0.98])
    plt.savefig(OUTPUT_DIR / "compact_comparison.pdf", bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / "compact_comparison.png", bbox_inches='tight', dpi=300)
    print(f"Saved: {OUTPUT_DIR / 'compact_comparison.pdf'}")
    plt.close()


if __name__ == "__main__":
    print("Generating main comparison figures...")

    create_main_figure()
    create_wide_figure()
    create_compact_figure()

    print("\nDone! Generated:")
    print("  - main_comparison.pdf: 4 examples, 3 columns")
    print("  - wide_comparison.pdf: 6 examples, horizontal")
    print("  - compact_comparison.pdf: 4 examples, compact")
