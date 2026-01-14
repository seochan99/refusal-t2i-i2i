#!/usr/bin/env python3
"""
Compare: Source vs Original Step1X vs Identity-Preserved Step1X
D03 (30 years older) - 7 races, Male 20s
Shows effectiveness of identity preservation prompts
"""

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from pathlib import Path
import numpy as np

# Paths
SOURCE_DIR = Path("/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/data/source_images/final")
ORIGINAL_RESULTS = Path("/Users/chan/Downloads/t2i-bias-refusal-result-image/step1x_organized/by_category/D_vulnerability")
IDENTITY_RESULTS = Path("/Users/chan/Downloads/step1x_identity_preserved")
OUTPUT_DIR = Path("/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/data/results/vlm_safety_eval")

RACES = ["White", "Black", "EastAsian", "SoutheastAsian", "Indian", "MiddleEastern", "Latino"]
DISPLAY_NAMES = {
    "White": "White",
    "Black": "Black",
    "EastAsian": "East Asian",
    "SoutheastAsian": "SE Asian",
    "Indian": "Indian",
    "MiddleEastern": "Middle Eastern",
    "Latino": "Latino"
}

GENDER = "Male"
AGE = "20s"


def load_image_safe(path):
    """Load image or return None if not found."""
    if path.exists():
        return mpimg.imread(str(path))
    return None


def main():
    fig = plt.figure(figsize=(24, 10))

    # Title
    fig.suptitle('Identity Preservation Comparison: "30 years older" (D03)\n'
                 'Source vs Original Step1X vs Identity-Preserved Step1X',
                 fontsize=16, fontweight='bold', y=0.98)

    n_races = len(RACES)
    img_width = 0.12
    img_height = 0.25
    x_start = 0.04
    x_gap = 0.135

    rows = [
        ("SOURCE\n(Original)", 0.68, "#4CAF50"),
        ("ORIGINAL\n(No ID Prompt)", 0.38, "#F44336"),
        ("PRESERVED\n(+ID Prompt)", 0.08, "#2196F3")
    ]

    for i, race in enumerate(RACES):
        x_pos = x_start + i * x_gap

        # Source image
        source_path = SOURCE_DIR / race / f"{race}_{GENDER}_{AGE}.jpg"
        source_img = load_image_safe(source_path)

        # Original Step1X result
        orig_path = ORIGINAL_RESULTS / f"D03_{race}_{GENDER}_{AGE}_success.png"
        orig_img = load_image_safe(orig_path)

        # Identity-preserved result
        identity_path = IDENTITY_RESULTS / f"D03_{race}_{GENDER}_{AGE}_identity.png"
        identity_img = load_image_safe(identity_path)

        images = [source_img, orig_img, identity_img]

        for j, (row_label, y_pos, border_color) in enumerate(rows):
            ax = fig.add_axes([x_pos, y_pos, img_width, img_height])

            if images[j] is not None:
                ax.imshow(images[j])
            else:
                ax.text(0.5, 0.5, 'NOT\nFOUND', ha='center', va='center',
                       fontsize=10, transform=ax.transAxes)
                ax.set_facecolor('#f0f0f0')

            ax.axis('off')

            # Border
            for spine in ax.spines.values():
                spine.set_visible(True)
                spine.set_color(border_color)
                spine.set_linewidth(3)

            # Race label (top row only)
            if j == 0:
                ax.set_title(DISPLAY_NAMES[race], fontsize=11, fontweight='bold', pad=5)

            # Row label (first column only)
            if i == 0:
                fig.text(0.01, y_pos + img_height/2, row_label,
                        fontsize=10, fontweight='bold', va='center', rotation=90)

    # Arrows between rows
    fig.text(0.5, 0.65, '▼ Step1X Edit (Original Prompt Only) ▼',
            fontsize=11, ha='center', color='#666')
    fig.text(0.5, 0.35, '▼ Step1X Edit (+ Identity Preservation Prompt) ▼',
            fontsize=11, ha='center', color='#666')

    # Legend
    legend_y = 0.02
    colors = [("#4CAF50", "Source (Ground Truth)"),
              ("#F44336", "Original (Potential Whitewashing)"),
              ("#2196F3", "Identity Preserved")]

    for k, (color, label) in enumerate(colors):
        x = 0.25 + k * 0.22
        fig.patches.append(plt.Rectangle((x, legend_y), 0.02, 0.015,
                                         facecolor=color, transform=fig.transFigure))
        fig.text(x + 0.025, legend_y + 0.0075, label, fontsize=10, va='center')

    # Save
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "D03_IDENTITY_COMPARISON_MALE_20s.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"Saved: {output_path}")
    plt.close()


if __name__ == "__main__":
    main()
