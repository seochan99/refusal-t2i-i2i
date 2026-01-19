#!/usr/bin/env python3
"""Generate final paper figures using CORRECT survey image paths.

Figure 1: EXP1+EXP2 comparison (3 rows: Source, Baseline, Ours)
Figure 2: EXP3 WinoBias stereotypes
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

# CORRECT PATHS
SOURCE_DIR = BASE_DIR / "data/source_images/final"
EXP1_B_DIR = BASE_DIR / "survey/public/images/exp1_sampling_b_d/flux/B_occupation"
EXP1_D_DIR = BASE_DIR / "survey/public/images/exp1_sampling_b_d/flux/D_vulnerability"
EXP2_DIR = BASE_DIR / "survey/public/images/exp2_pairwise/flux"
EXP3_DIR = BASE_DIR / "survey/public/images/exp3_winobias/flux"


def load_image(path):
    """Load image or return red placeholder if missing."""
    if path.exists():
        return mpimg.imread(str(path))
    print(f"MISSING: {path}")
    # Return red placeholder to make missing images obvious
    placeholder = np.ones((256, 256, 3)) * 0.8
    placeholder[:, :, 0] = 1.0  # Red tint
    return placeholder


def create_exp1_exp2_figure():
    """
    Create main figure: 3 rows (Source, Baseline, Ours) x 6 columns
    Using diverse prompts: B01(CEO), B05(Housekeeper), B09(Model), D03(Wheelchair)
    """

    # Diverse examples: (Race, Gender, Age, PromptID, PromptName, Category)
    # Mix different races, genders, ages, and prompts
    examples = [
        ('Black', 'Female', '20s', 'B01', 'CEO', 'B'),
        ('Indian', 'Male', '40s', 'B05', 'Housekeeper', 'B'),
        ('Latino', 'Female', '30s', 'B09', 'Model', 'B'),
        ('EastAsian', 'Female', '50s', 'B01', 'CEO', 'B'),
        ('MiddleEastern', 'Male', '30s', 'B05', 'Housekeeper', 'B'),
        ('SoutheastAsian', 'Female', '40s', 'D03', 'Wheelchair', 'D'),
    ]

    fig, axes = plt.subplots(3, 6, figsize=(14, 7))

    row_labels = ['Source', 'Baseline\n(EXP1)', 'Ours\n(+Feature)']

    for col, (race, gender, age, prompt_id, prompt_name, cat) in enumerate(examples):
        # Row 0: Source Image
        source_path = SOURCE_DIR / race / f"{race}_{gender}_{age}.jpg"
        axes[0, col].imshow(load_image(source_path))
        axes[0, col].axis('off')

        # Row 1: Baseline (EXP1)
        if cat == 'B':
            exp1_path = EXP1_B_DIR / f"{prompt_id}_{race}_{gender}_{age}_success.png"
        else:
            exp1_path = EXP1_D_DIR / f"{prompt_id}_{race}_{gender}_{age}_success.png"
        axes[1, col].imshow(load_image(exp1_path))
        axes[1, col].axis('off')

        # Row 2: Ours (EXP2 Feature Prompt)
        exp2_path = EXP2_DIR / f"preserved_{prompt_id}" / f"{prompt_id}_{race}_{gender}_{age}.png"
        axes[2, col].imshow(load_image(exp2_path))
        axes[2, col].axis('off')

        # Column label at bottom
        label = f'{race}\n{gender}, {age}\n"{prompt_name}"'
        axes[2, col].text(0.5, -0.15, label, transform=axes[2, col].transAxes,
                         ha='center', va='top', fontsize=8)

    # Row labels on left side
    for row, label in enumerate(row_labels):
        axes[row, 0].text(-0.15, 0.5, label, transform=axes[row, 0].transAxes,
                         rotation=90, va='center', ha='center', fontsize=10, fontweight='bold')

    fig.suptitle('Feature Prompt Mitigates Identity Drift Across Diverse Demographics',
                fontsize=12, fontweight='bold', y=0.98)

    plt.tight_layout(rect=[0.05, 0.08, 1, 0.95])
    plt.savefig(OUTPUT_DIR / "exp1_exp2_comparison.pdf", bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / "exp1_exp2_comparison.png", bbox_inches='tight', dpi=300)
    print(f"Saved: {OUTPUT_DIR / 'exp1_exp2_comparison.pdf'}")
    plt.close()


def create_exp3_figure():
    """
    Create EXP3 WinoBias figure showing stereotype following.
    """

    # Get available WinoBias images
    exp3_images = sorted(EXP3_DIR.glob("prompt_*.png"))[:8]  # Take first 8

    if len(exp3_images) < 4:
        print("Not enough EXP3 images found!")
        return

    # Create 2x4 grid
    fig, axes = plt.subplots(2, 4, figsize=(12, 6))

    for idx, img_path in enumerate(exp3_images[:8]):
        row = idx // 4
        col = idx % 4
        axes[row, col].imshow(load_image(img_path))
        axes[row, col].axis('off')

        # Extract prompt number from filename
        prompt_num = img_path.stem.split('_')[1]
        axes[row, col].set_title(f'Prompt {prompt_num}', fontsize=9)

    fig.suptitle('EXP3: Gender-Occupation Stereotype Following (WinoBias)',
                fontsize=12, fontweight='bold')

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(OUTPUT_DIR / "exp3_winobias.pdf", bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / "exp3_winobias.png", bbox_inches='tight', dpi=300)
    print(f"Saved: {OUTPUT_DIR / 'exp3_winobias.pdf'}")
    plt.close()


def create_compact_3row_figure():
    """
    Create compact 3-row figure with 4 examples for paper main figure.
    """

    # 4 diverse examples
    examples = [
        ('Black', 'Female', '20s', 'B01', 'CEO', 'B', '+1.48'),
        ('Indian', 'Female', '30s', 'B05', 'Housekeeper', 'B', '+1.23'),
        ('Latino', 'Male', '40s', 'B09', 'Model', 'B', '+1.08'),
        ('EastAsian', 'Female', '50s', 'B01', 'CEO', 'B', '+0.56'),
    ]

    fig, axes = plt.subplots(3, 4, figsize=(10, 7.5))

    for col, (race, gender, age, prompt_id, prompt_name, cat, improvement) in enumerate(examples):
        # Row 0: Source
        source_path = SOURCE_DIR / race / f"{race}_{gender}_{age}.jpg"
        axes[0, col].imshow(load_image(source_path))
        axes[0, col].axis('off')
        if col == 0:
            axes[0, col].text(-0.15, 0.5, 'Source', transform=axes[0, col].transAxes,
                             rotation=90, va='center', ha='center', fontsize=10, fontweight='bold')

        # Row 1: Baseline (EXP1)
        if cat == 'B':
            exp1_path = EXP1_B_DIR / f"{prompt_id}_{race}_{gender}_{age}_success.png"
        else:
            exp1_path = EXP1_D_DIR / f"{prompt_id}_{race}_{gender}_{age}_success.png"
        axes[1, col].imshow(load_image(exp1_path))
        axes[1, col].axis('off')
        if col == 0:
            axes[1, col].text(-0.15, 0.5, 'Baseline', transform=axes[1, col].transAxes,
                             rotation=90, va='center', ha='center', fontsize=10, fontweight='bold')

        # Row 2: Ours (EXP2)
        exp2_path = EXP2_DIR / f"preserved_{prompt_id}" / f"{prompt_id}_{race}_{gender}_{age}.png"
        axes[2, col].imshow(load_image(exp2_path))
        axes[2, col].axis('off')
        if col == 0:
            axes[2, col].text(-0.15, 0.5, '+Feature\nPrompt', transform=axes[2, col].transAxes,
                             rotation=90, va='center', ha='center', fontsize=10, fontweight='bold')

        # Improvement badge on Ours row
        axes[2, col].text(0.95, 0.05, f'{improvement}pt',
                         transform=axes[2, col].transAxes, ha='right', va='bottom',
                         fontsize=9, fontweight='bold', color='white',
                         bbox=dict(boxstyle='round,pad=0.3', facecolor='#27ae60', alpha=0.9))

        # Column label
        axes[2, col].text(0.5, -0.12, f'{race}\n{gender}, {age}\n"{prompt_name}"',
                         transform=axes[2, col].transAxes, ha='center', va='top', fontsize=8)

    plt.tight_layout(rect=[0.06, 0.06, 1, 0.98])
    plt.savefig(OUTPUT_DIR / "main_3row_comparison.pdf", bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / "main_3row_comparison.png", bbox_inches='tight', dpi=300)
    print(f"Saved: {OUTPUT_DIR / 'main_3row_comparison.pdf'}")
    plt.close()


if __name__ == "__main__":
    print("Generating final paper figures with CORRECT paths...")
    print(f"Source: {SOURCE_DIR}")
    print(f"EXP1 B: {EXP1_B_DIR}")
    print(f"EXP1 D: {EXP1_D_DIR}")
    print(f"EXP2: {EXP2_DIR}")
    print(f"EXP3: {EXP3_DIR}")
    print()

    create_exp1_exp2_figure()
    create_compact_3row_figure()
    create_exp3_figure()

    print("\nDone! Generated:")
    print("  - exp1_exp2_comparison.pdf: 6 examples, 3 rows")
    print("  - main_3row_comparison.pdf: 4 examples, 3 rows (compact)")
    print("  - exp3_winobias.pdf: WinoBias stereotypes")
