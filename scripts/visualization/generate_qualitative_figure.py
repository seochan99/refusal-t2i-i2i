#!/usr/bin/env python3
"""Generate qualitative figures with CORRECT image mapping and DIVERSE prompts.

Mapping:
- Source: data/source_images/fairface_sample/V7/{Race}/{Race}_{Gender}_{Age}.jpg
- EXP1 (Baseline): data/results/exp1_all_dataset/flux_organized/by_category/B_occupation/{Prompt}_{Race}_{Gender}_{Age}_success.png
- EXP2 (Feature Prompt): data/results/exp2_pairwise/flux/preserved_{Prompt}/{Prompt}_{Race}_{Gender}_{Age}.png
- EXP3 (WinoBias): data/results/exp3_winobias/flux2/prompt_{ID}_{timestamp}.png
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
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'figure.dpi': 300,
})

BASE_DIR = Path("/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal")
OUTPUT_DIR = BASE_DIR / "paper/I2I_Bias_Refusal/assets"
SOURCE_DIR = BASE_DIR / "data/source_images/final"
EXP1_DIR = BASE_DIR / "data/results/exp1_all_dataset/flux_organized/by_category/B_occupation"
EXP2_DIR = BASE_DIR / "data/results/exp2_pairwise/flux"
EXP3_DIR = BASE_DIR / "data/results/exp3_winobias"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Prompt descriptions
PROMPTS = {
    'B01': 'CEO',
    'B02': 'Military Strategist',
    'B03': 'Medical Specialist',
    'B04': 'Kindergarten Teacher',
    'B05': 'Housekeeper',
    'B06': 'Security Supervisor',
    'B07': 'Politician',
    'B08': 'Athlete',
    'B09': 'Fashion Model',
    'B10': 'Janitor',
}


def load_image(path):
    """Load and return image array."""
    if path.exists():
        return mpimg.imread(str(path))
    else:
        print(f"Warning: Image not found: {path}")
        return np.ones((256, 256, 3)) * 0.9


def figure_exp1_diverse():
    """EXP1: Show diverse prompts across different races/genders/ages."""

    # Diverse examples across different prompts and demographics
    examples = [
        # (Race, Gender, Age, Prompt, PromptName)
        ('Black', 'Female', '20s', 'B01', 'CEO'),
        ('Indian', 'Male', '40s', 'B05', 'Housekeeper'),
        ('Latino', 'Female', '30s', 'B09', 'Fashion Model'),
        ('EastAsian', 'Male', '50s', 'B08', 'Athlete'),
    ]

    fig, axes = plt.subplots(2, 4, figsize=(10, 5))

    for col, (race, gender, age, prompt_id, prompt_name) in enumerate(examples):
        # Source
        source_path = SOURCE_DIR / race / f"{race}_{gender}_{age}.jpg"
        axes[0, col].imshow(load_image(source_path))
        axes[0, col].axis('off')
        if col == 0:
            axes[0, col].text(-0.15, 0.5, 'Source', transform=axes[0, col].transAxes,
                             rotation=90, va='center', ha='center', fontsize=10, fontweight='bold')

        # Edited (EXP1 Baseline)
        exp1_path = EXP1_DIR / f"{prompt_id}_{race}_{gender}_{age}_success.png"
        axes[1, col].imshow(load_image(exp1_path))
        axes[1, col].axis('off')
        if col == 0:
            axes[1, col].text(-0.15, 0.5, 'Edited', transform=axes[1, col].transAxes,
                             rotation=90, va='center', ha='center', fontsize=10, fontweight='bold')

        # Label
        axes[1, col].text(0.5, -0.12, f'{race}, {gender}, {age}\nPrompt: {prompt_name}',
                         transform=axes[1, col].transAxes, ha='center', va='top', fontsize=8)

    fig.suptitle('Experiment 1: Identity Drift Across Diverse Demographics and Prompts (FLUX.2-dev)',
                fontsize=11, fontweight='bold', y=0.98)

    plt.tight_layout(rect=[0.05, 0.08, 1, 0.95])
    plt.savefig(OUTPUT_DIR / "exp1_diverse.pdf", bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / "exp1_diverse.png", bbox_inches='tight', dpi=300)
    print(f"Saved: {OUTPUT_DIR / 'exp1_diverse.pdf'}")
    plt.close()


def figure_exp2_comparison():
    """EXP2: Source → EXP1 (Baseline) → EXP2 (Feature Prompt) comparison."""

    examples = [
        ('Black', 'Female', '20s', 'B01', 'CEO', '+1.48'),
        ('Indian', 'Female', '30s', 'B05', 'Housekeeper', '+1.23'),
    ]

    fig, axes = plt.subplots(2, 3, figsize=(9, 6))

    col_titles = ['Source Image', 'Experiment 1: Baseline\n(No identity cue)', 'Experiment 2: Feature Prompt\n(+identity cue)']

    for row, (race, gender, age, prompt_id, prompt_name, improvement) in enumerate(examples):
        # Source
        source_path = SOURCE_DIR / race / f"{race}_{gender}_{age}.jpg"
        axes[row, 0].imshow(load_image(source_path))
        axes[row, 0].axis('off')
        if row == 0:
            axes[row, 0].set_title(col_titles[0], fontsize=10, fontweight='bold', pad=8)
        axes[row, 0].text(-0.08, 0.5, f'{race}\n{gender}, {age}\n({prompt_name})',
                         transform=axes[row, 0].transAxes, rotation=90,
                         va='center', ha='center', fontsize=8, fontweight='bold')

        # EXP1: Baseline
        exp1_path = EXP1_DIR / f"{prompt_id}_{race}_{gender}_{age}_success.png"
        axes[row, 1].imshow(load_image(exp1_path))
        axes[row, 1].axis('off')
        if row == 0:
            axes[row, 1].set_title(col_titles[1], fontsize=10, fontweight='bold', pad=8)

        # EXP2: Feature Prompt
        exp2_path = EXP2_DIR / f"preserved_{prompt_id}" / f"{prompt_id}_{race}_{gender}_{age}.png"
        axes[row, 2].imshow(load_image(exp2_path))
        axes[row, 2].axis('off')
        if row == 0:
            axes[row, 2].set_title(col_titles[2], fontsize=10, fontweight='bold', pad=8)

        # Add improvement badge
        axes[row, 2].text(0.95, 0.95, f'Drift\n{improvement}',
                         transform=axes[row, 2].transAxes, ha='right', va='top',
                         fontsize=9, fontweight='bold', color='white',
                         bbox=dict(boxstyle='round', facecolor='green', alpha=0.8))

    fig.text(0.5, 0.02, 'Feature prompts reduce identity drift by prepending observable appearance features to the edit instruction.',
            ha='center', fontsize=9, style='italic')

    plt.tight_layout(rect=[0.06, 0.05, 1, 0.98])
    plt.savefig(OUTPUT_DIR / "exp2_comparison.pdf", bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / "exp2_comparison.png", bbox_inches='tight', dpi=300)
    print(f"Saved: {OUTPUT_DIR / 'exp2_comparison.pdf'}")
    plt.close()


def figure_exp3_winobias():
    """EXP3: WinoBias gender-occupation stereotype examples."""

    # WinoBias prompts and their stereotype occupations
    winobias_examples = [
        (1, "janitor", "Black Male 40s → White Female 20s"),
        (3, "carpenter", "Indian Male 50s → MiddleEastern Female 30s"),
        (5, "laborer", "Latino Male 40s → Black Female 30s"),
        (10, "supervisor", "White Male 50s → Indian Female 60s"),
    ]

    fig, axes = plt.subplots(2, 4, figsize=(10, 5))

    for col, (prompt_id, occupation, desc) in enumerate(winobias_examples):
        # FLUX result
        flux_path = EXP3_DIR / "flux2" / f"prompt_{prompt_id:03d}_20260115_131511.png"
        axes[0, col].imshow(load_image(flux_path))
        axes[0, col].axis('off')
        if col == 0:
            axes[0, col].text(-0.15, 0.5, 'FLUX.2-dev', transform=axes[0, col].transAxes,
                             rotation=90, va='center', ha='center', fontsize=10, fontweight='bold')

        # Qwen result
        qwen_path = EXP3_DIR / "qwen" / f"prompt_{prompt_id:03d}_20260115_144816.png"
        axes[1, col].imshow(load_image(qwen_path))
        axes[1, col].axis('off')
        if col == 0:
            axes[1, col].text(-0.15, 0.5, 'Qwen-Edit', transform=axes[1, col].transAxes,
                             rotation=90, va='center', ha='center', fontsize=10, fontweight='bold')

        # Label
        axes[1, col].text(0.5, -0.12, f'"{occupation}"\n{desc}',
                         transform=axes[1, col].transAxes, ha='center', va='top', fontsize=7)

    fig.suptitle('Supplementary Experiment: WinoBias Gender-Occupation Stereotypes (84-86% followed)',
                fontsize=11, fontweight='bold', y=0.98)

    plt.tight_layout(rect=[0.05, 0.10, 1, 0.95])
    plt.savefig(OUTPUT_DIR / "exp3_winobias.pdf", bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / "exp3_winobias.png", bbox_inches='tight', dpi=300)
    print(f"Saved: {OUTPUT_DIR / 'exp3_winobias.pdf'}")
    plt.close()


def figure_7races_proper():
    """Create 7-races figure with proper source image mapping."""

    races = ['White', 'EastAsian', 'SoutheastAsian', 'Latino', 'Black', 'MiddleEastern', 'Indian']
    short_names = ['White', 'E. Asian', 'SE Asian', 'Latino', 'Black', 'Mid East', 'Indian']
    lightening = [47.3, 55.8, 76.6, 79.4, 78.8, 77.5, 79.8]
    drift = [1.3, 9.6, 15.1, 15.1, 16.7, 17.9, 18.5]

    gender, age = 'Female', '30s'
    prompt_id = 'B01'

    fig, axes = plt.subplots(2, 7, figsize=(12, 4.5))

    for col, (race, name, light, dr) in enumerate(zip(races, short_names, lightening, drift)):
        # Source
        source_path = SOURCE_DIR / race / f"{race}_{gender}_{age}.jpg"
        axes[0, col].imshow(load_image(source_path))
        axes[0, col].axis('off')

        # Edited
        exp1_path = EXP1_DIR / f"{prompt_id}_{race}_{gender}_{age}_success.png"
        axes[1, col].imshow(load_image(exp1_path))
        axes[1, col].axis('off')

        # Label
        axes[1, col].text(0.5, -0.15, f'{name}\n{gender}, {age}\nLight: {light:.0f}%\nDrift: {dr:.1f}%',
                         transform=axes[1, col].transAxes, ha='center', va='top', fontsize=7)

    fig.text(0.02, 0.75, 'Source', rotation=90, va='center', fontsize=11, fontweight='bold')
    fig.text(0.02, 0.30, 'Edited', rotation=90, va='center', fontsize=11, fontweight='bold')

    fig.suptitle('Experiment 1: Identity Drift Across 7 Racial Groups (FLUX.2-dev, B01: CEO Prompt)',
                fontsize=12, fontweight='bold', y=0.98)

    plt.tight_layout(rect=[0.04, 0.12, 1, 0.95])
    plt.savefig(OUTPUT_DIR / "exp1_7races.pdf", bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / "exp1_7races.png", bbox_inches='tight', dpi=300)
    print(f"Saved: {OUTPUT_DIR / 'exp1_7races.pdf'}")
    plt.close()


def figure_combined_all():
    """Combined figure with all 3 experiments."""

    fig = plt.figure(figsize=(12, 12))

    # ====== Part A: EXP1 - 7 Races ======
    races = ['White', 'EastAsian', 'SoutheastAsian', 'Latino', 'Black', 'MiddleEastern', 'Indian']
    short_names = ['White', 'E.Asian', 'SE Asian', 'Latino', 'Black', 'MidEast', 'Indian']
    lightening = [47.3, 55.8, 76.6, 79.4, 78.8, 77.5, 79.8]
    drift = [1.3, 9.6, 15.1, 15.1, 16.7, 17.9, 18.5]
    gender, age = 'Female', '30s'

    for col, (race, name, light, dr) in enumerate(zip(races, short_names, lightening, drift)):
        # Source row
        ax = fig.add_axes([0.05 + col*0.13, 0.78, 0.11, 0.10])
        source_path = SOURCE_DIR / race / f"{race}_{gender}_{age}.jpg"
        ax.imshow(load_image(source_path))
        ax.axis('off')
        if col == 0:
            ax.text(-0.2, 0.5, 'Source', transform=ax.transAxes, rotation=90,
                   va='center', ha='center', fontsize=8, fontweight='bold')

        # Edited row
        ax = fig.add_axes([0.05 + col*0.13, 0.64, 0.11, 0.10])
        exp1_path = EXP1_DIR / f"B01_{race}_{gender}_{age}_success.png"
        ax.imshow(load_image(exp1_path))
        ax.axis('off')
        if col == 0:
            ax.text(-0.2, 0.5, 'Edited', transform=ax.transAxes, rotation=90,
                   va='center', ha='center', fontsize=8, fontweight='bold')
        ax.text(0.5, -0.12, f'{name}\n{gender},{age}\nL:{light:.0f}% D:{dr:.1f}%',
               transform=ax.transAxes, ha='center', va='top', fontsize=6)

    fig.text(0.5, 0.92, '(a) Experiment 1: Identity Drift Across 7 Racial Groups (FLUX.2-dev, CEO Prompt)',
            ha='center', fontsize=10, fontweight='bold')

    # ====== Part B: EXP2 - Feature Prompt Comparison ======
    examples = [
        ('Black', 'Female', '20s', 'B01', 'CEO', '+1.48'),
        ('Indian', 'Female', '30s', 'B05', 'Housekeeper', '+1.23'),
    ]

    for row, (race, gender, age, prompt_id, prompt_name, improvement) in enumerate(examples):
        y_base = 0.38 - row * 0.16

        # Source
        ax = fig.add_axes([0.08, y_base, 0.10, 0.10])
        source_path = SOURCE_DIR / race / f"{race}_{gender}_{age}.jpg"
        ax.imshow(load_image(source_path))
        ax.axis('off')
        if row == 0:
            ax.set_title('Source', fontsize=8, fontweight='bold')
        ax.text(-0.12, 0.5, f'{race}\n{gender},{age}\n({prompt_name})',
               transform=ax.transAxes, rotation=90, va='center', ha='center', fontsize=6, fontweight='bold')

        # EXP1: Baseline
        ax = fig.add_axes([0.25, y_base, 0.10, 0.10])
        exp1_path = EXP1_DIR / f"{prompt_id}_{race}_{gender}_{age}_success.png"
        ax.imshow(load_image(exp1_path))
        ax.axis('off')
        if row == 0:
            ax.set_title('EXP1: Baseline', fontsize=8, fontweight='bold')

        # EXP2: Feature Prompt
        ax = fig.add_axes([0.42, y_base, 0.10, 0.10])
        exp2_path = EXP2_DIR / f"preserved_{prompt_id}" / f"{prompt_id}_{race}_{gender}_{age}.png"
        ax.imshow(load_image(exp2_path))
        ax.axis('off')
        if row == 0:
            ax.set_title('EXP2: +Feature', fontsize=8, fontweight='bold')
        ax.text(0.95, 0.95, f'{improvement}', transform=ax.transAxes, ha='right', va='top',
               fontsize=8, fontweight='bold', color='white',
               bbox=dict(boxstyle='round', facecolor='green', alpha=0.85))

    fig.text(0.30, 0.56, '(b) Experiment 2: Feature Prompt Mitigates Identity Drift',
            ha='center', fontsize=10, fontweight='bold')

    # ====== Part C: EXP3 - WinoBias ======
    winobias_examples = [
        (1, "janitor"),
        (3, "carpenter"),
        (5, "laborer"),
    ]

    for col, (prompt_id, occupation) in enumerate(winobias_examples):
        ax = fig.add_axes([0.60 + col*0.13, 0.38, 0.11, 0.10])
        flux_path = EXP3_DIR / "flux2" / f"prompt_{prompt_id:03d}_20260115_131511.png"
        ax.imshow(load_image(flux_path))
        ax.axis('off')
        if col == 0:
            ax.text(-0.15, 0.5, 'FLUX', transform=ax.transAxes, rotation=90,
                   va='center', ha='center', fontsize=7, fontweight='bold')

        ax = fig.add_axes([0.60 + col*0.13, 0.24, 0.11, 0.10])
        qwen_path = EXP3_DIR / "qwen" / f"prompt_{prompt_id:03d}_20260115_144816.png"
        ax.imshow(load_image(qwen_path))
        ax.axis('off')
        if col == 0:
            ax.text(-0.15, 0.5, 'Qwen', transform=ax.transAxes, rotation=90,
                   va='center', ha='center', fontsize=7, fontweight='bold')
        ax.text(0.5, -0.1, f'"{occupation}"', transform=ax.transAxes, ha='center', va='top', fontsize=7)

    fig.text(0.73, 0.56, '(c) Supp: WinoBias\n(84-86% stereotype)',
            ha='center', fontsize=9, fontweight='bold')

    # ====== Part D: Summary Stats ======
    ax = fig.add_axes([0.15, 0.03, 0.70, 0.12])
    ax.axis('off')

    summary_text = """Key Findings:
• Skin Lightening: 47% (White) vs 80% (Indian/Latino) — up to 1.7× disparity
• Race Drift: 1.3% (White) vs 18.5% (Indian) — up to 14× disparity
• Feature Prompt reduces drift by 1.48pt (Black), 1.23pt (Indian), but only 0.06pt (White) — 25× asymmetry
• WinoBias: 84-86% of occupation edits follow gender stereotypes"""

    ax.text(0.5, 0.5, summary_text, transform=ax.transAxes, ha='center', va='center',
           fontsize=9, family='monospace',
           bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8, pad=0.5))

    plt.savefig(OUTPUT_DIR / "qualitative_combined.pdf", bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / "qualitative_combined.png", bbox_inches='tight', dpi=300)
    print(f"Saved: {OUTPUT_DIR / 'qualitative_combined.pdf'}")
    plt.close()


if __name__ == "__main__":
    print("Generating qualitative figures with CORRECT mapping and DIVERSE prompts...")

    # Individual figures
    figure_exp1_diverse()
    figure_exp2_comparison()
    figure_exp3_winobias()
    figure_7races_proper()

    # Combined figure
    figure_combined_all()

    print("\nDone! Generated figures:")
    print("  - exp1_diverse.pdf: Diverse prompts/demographics")
    print("  - exp2_comparison.pdf: Baseline vs Feature Prompt")
    print("  - exp3_winobias.pdf: WinoBias stereotypes")
    print("  - exp1_7races.pdf: 7 races comparison")
    print("  - qualitative_combined.pdf: All experiments combined")
