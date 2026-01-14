#!/usr/bin/env python3
"""
Full Comparison Plot: Base vs Edited vs Preserved
D03 (30 years older) - 7 races × 2 genders
"""

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from pathlib import Path

SOURCE_DIR = Path("/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/data/source_images/final")
EDITED_DIR = Path("/Users/chan/Downloads/t2i-bias-refusal-result-image/step1x_organized/by_category/D_vulnerability")
PRESERVED_DIR = Path("/Users/chan/Downloads/step1x_identity_preserved")
OUTPUT_DIR = Path("/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/data/results/vlm_safety_eval")

RACES = ["White", "Black", "EastAsian", "SoutheastAsian", "Indian", "MiddleEastern", "Latino"]
DISPLAY = {"White": "White", "Black": "Black", "EastAsian": "E.Asian",
           "SoutheastAsian": "SE.Asian", "Indian": "Indian",
           "MiddleEastern": "M.East", "Latino": "Latino"}

AGE = "20s"


def load_img(path):
    if path.exists():
        return mpimg.imread(str(path))
    return None


def create_gender_plot(gender, output_name):
    """Create plot for one gender."""
    fig = plt.figure(figsize=(20, 9))

    fig.suptitle(f'D03 "30 years older" - {gender} 20s\nBase vs Edited (Original) vs Preserved (+Identity Prompt)',
                 fontsize=14, fontweight='bold', y=0.98)

    n = len(RACES)
    w, h = 0.12, 0.26
    x_start = 0.06
    gap = 0.13

    rows = [
        ("BASE\n(Source)", 0.68, "#4CAF50",
         lambda r: SOURCE_DIR / r / f"{r}_{gender}_{AGE}.jpg"),
        ("EDITED\n(Original)", 0.38, "#F44336",
         lambda r: EDITED_DIR / f"D03_{r}_{gender}_{AGE}_success.png"),
        ("PRESERVED\n(+ID Prompt)", 0.08, "#2196F3",
         lambda r: PRESERVED_DIR / f"D03_{r}_{gender}_{AGE}_identity.png"),
    ]

    for i, race in enumerate(RACES):
        x = x_start + i * gap

        for j, (label, y, color, path_fn) in enumerate(rows):
            ax = fig.add_axes([x, y, w, h])

            img = load_img(path_fn(race))
            if img is not None:
                ax.imshow(img)
            else:
                ax.text(0.5, 0.5, 'N/A', ha='center', va='center', fontsize=12)
                ax.set_facecolor('#f5f5f5')

            ax.axis('off')
            for spine in ax.spines.values():
                spine.set_visible(True)
                spine.set_color(color)
                spine.set_linewidth(2)

            if j == 0:
                ax.set_title(DISPLAY[race], fontsize=11, fontweight='bold', pad=3)
            if i == 0:
                fig.text(0.02, y + h/2, label, fontsize=10, fontweight='bold',
                        va='center', ha='center', rotation=90)

    # Arrows
    fig.text(0.5, 0.66, '▼ Step1X I2I Edit ▼', fontsize=10, ha='center', color='#888')
    fig.text(0.5, 0.36, '▼ + Identity Preservation Prompt ▼', fontsize=10, ha='center', color='#888')

    # Legend
    for k, (c, l) in enumerate([("#4CAF50", "Base"), ("#F44336", "Edited"), ("#2196F3", "Preserved")]):
        fig.patches.append(plt.Rectangle((0.30 + k*0.15, 0.02), 0.02, 0.015,
                                         facecolor=c, transform=fig.transFigure))
        fig.text(0.33 + k*0.15, 0.027, l, fontsize=10, va='center')

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUT_DIR / output_name
    plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"Saved: {out}")
    plt.close()


def create_combined_plot():
    """Create single plot with both Male and Female."""
    fig = plt.figure(figsize=(20, 16))

    fig.suptitle('D03 "30 years older" Comparison\nBase → Edited (Original) → Preserved (+Identity Prompt)',
                 fontsize=14, fontweight='bold', y=0.98)

    n = len(RACES)
    w, h = 0.115, 0.13
    x_start = 0.06
    gap = 0.125

    # Male section (top)
    male_rows = [
        ("MALE\nBase", 0.82, "#4CAF50",
         lambda r: SOURCE_DIR / r / f"{r}_Male_{AGE}.jpg"),
        ("MALE\nEdited", 0.67, "#F44336",
         lambda r: EDITED_DIR / f"D03_{r}_Male_{AGE}_success.png"),
        ("MALE\nPreserved", 0.52, "#2196F3",
         lambda r: PRESERVED_DIR / f"D03_{r}_Male_{AGE}_identity.png"),
    ]

    # Female section (bottom)
    female_rows = [
        ("FEMALE\nBase", 0.35, "#4CAF50",
         lambda r: SOURCE_DIR / r / f"{r}_Female_{AGE}.jpg"),
        ("FEMALE\nEdited", 0.20, "#F44336",
         lambda r: EDITED_DIR / f"D03_{r}_Female_{AGE}_success.png"),
        ("FEMALE\nPreserved", 0.05, "#2196F3",
         lambda r: PRESERVED_DIR / f"D03_{r}_Female_{AGE}_identity.png"),
    ]

    all_rows = male_rows + female_rows

    for i, race in enumerate(RACES):
        x = x_start + i * gap

        for j, (label, y, color, path_fn) in enumerate(all_rows):
            ax = fig.add_axes([x, y, w, h])

            img = load_img(path_fn(race))
            if img is not None:
                ax.imshow(img)
            else:
                ax.text(0.5, 0.5, 'N/A', ha='center', va='center', fontsize=9)
                ax.set_facecolor('#f5f5f5')

            ax.axis('off')
            for spine in ax.spines.values():
                spine.set_visible(True)
                spine.set_color(color)
                spine.set_linewidth(2)

            # Race label on top row only
            if j == 0:
                ax.set_title(DISPLAY[race], fontsize=10, fontweight='bold', pad=2)

            # Row labels
            if i == 0:
                fig.text(0.02, y + h/2, label, fontsize=8, fontweight='bold',
                        va='center', ha='center', rotation=90)

    # Section divider
    fig.text(0.5, 0.49, '─' * 60, fontsize=10, ha='center', color='#ccc')

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUT_DIR / "D03_FULL_COMPARISON_ALL.png"
    plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"Saved: {out}")
    plt.close()


if __name__ == "__main__":
    # Individual gender plots
    create_gender_plot("Male", "D03_COMPARISON_MALE.png")
    create_gender_plot("Female", "D03_COMPARISON_FEMALE.png")

    # Combined plot
    create_combined_plot()
