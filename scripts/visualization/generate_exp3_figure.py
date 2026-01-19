#!/usr/bin/env python3
"""Generate Experiment 3 figure: WinoBias Gender-Occupation Stereotypes.

Layout: Input Image 1 + Input Image 2 + Prompt → Output Image
"""

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from pathlib import Path
import numpy as np
import json

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size': 10,
    'figure.dpi': 300,
})

BASE_DIR = Path("/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal")
OUTPUT_DIR = BASE_DIR / "paper/I2I_Bias_Refusal/assets"
SOURCE_DIR = BASE_DIR / "data/source_images/final"
EXP3_DIR = BASE_DIR / "survey/public/images/exp3_winobias/flux"
PROMPTS_FILE = BASE_DIR / "data/prompts/winobias_prompts_with_stereotype.json"


def load_image(path):
    """Load image."""
    if path.exists():
        return mpimg.imread(str(path))
    print(f"MISSING: {path}")
    return np.ones((256, 256, 3)) * 0.9


def get_source_path(filename):
    """Get full path from filename like 'Black_Male_40s.jpg'."""
    parts = filename.replace('.jpg', '').split('_')
    race = parts[0]
    return SOURCE_DIR / race / filename


def create_exp3_figure():
    """
    Create Experiment 3 figure.

    Layout per row:
    [Input 1] [Input 2] [Arrow + Prompt] [Output]
    """

    # Load prompts
    with open(PROMPTS_FILE, 'r') as f:
        prompts = json.load(f)

    # Select interesting examples (varied stereotypes)
    selected_ids = [1, 2, 5, 9]  # janitor, chief, laborer, CEO
    selected = [p for p in prompts if p['id'] in selected_ids]

    fig, axes = plt.subplots(len(selected), 4, figsize=(14, 3.5 * len(selected)),
                             gridspec_kw={'width_ratios': [1, 1, 1.5, 1]})

    # Colors
    badge_color = '#2c3e50'
    model_badge = '#e74c3c'
    prompt_bg = '#34495e'

    for row, item in enumerate(selected):
        prompt_id = item['id']
        prompt_text = item['prompt']
        img1_file = item['input_image_1']
        img2_file = item['input_image_2']
        stereotype = item['gender_stereotype']

        # Column 0: Input Image 1
        img1_path = get_source_path(img1_file)
        axes[row, 0].imshow(load_image(img1_path))
        axes[row, 0].axis('off')
        if row == 0:
            axes[row, 0].set_title('Input 1', fontsize=11, fontweight='bold', pad=8)
        # Badge with demographics
        demo1 = img1_file.replace('.jpg', '').replace('_', '/')
        axes[row, 0].text(0.5, 0.02, demo1, transform=axes[row, 0].transAxes,
                         ha='center', va='bottom', fontsize=8, color='white',
                         bbox=dict(boxstyle='round,pad=0.3', facecolor=badge_color, alpha=0.9))

        # Column 1: Input Image 2
        img2_path = get_source_path(img2_file)
        axes[row, 1].imshow(load_image(img2_path))
        axes[row, 1].axis('off')
        if row == 0:
            axes[row, 1].set_title('Input 2', fontsize=11, fontweight='bold', pad=8)
        # Badge with demographics
        demo2 = img2_file.replace('.jpg', '').replace('_', '/')
        axes[row, 1].text(0.5, 0.02, demo2, transform=axes[row, 1].transAxes,
                         ha='center', va='bottom', fontsize=8, color='white',
                         bbox=dict(boxstyle='round,pad=0.3', facecolor=badge_color, alpha=0.9))

        # Column 2: Prompt box
        axes[row, 2].set_facecolor(prompt_bg)
        axes[row, 2].set_xlim(0, 1)
        axes[row, 2].set_ylim(0, 1)
        axes[row, 2].axis('off')
        if row == 0:
            axes[row, 2].set_title('Prompt', fontsize=11, fontweight='bold', pad=8)

        # Prompt text with arrow
        axes[row, 2].text(0.05, 0.5, f'"{prompt_text}"',
                         transform=axes[row, 2].transAxes, ha='left', va='center',
                         fontsize=9, color='white', wrap=True, style='italic',
                         bbox=dict(boxstyle='round,pad=0.5', facecolor=prompt_bg, alpha=0.95))

        # Stereotype indicator
        axes[row, 2].text(0.95, 0.1, f'Stereotype: {stereotype} (male)',
                         transform=axes[row, 2].transAxes, ha='right', va='bottom',
                         fontsize=8, color='#f39c12', fontweight='bold')

        # Arrow
        axes[row, 2].annotate('', xy=(1.15, 0.5), xytext=(1.0, 0.5),
                             xycoords='axes fraction', textcoords='axes fraction',
                             arrowprops=dict(arrowstyle='->', color='white', lw=2))

        # Column 3: Output Image
        output_path = EXP3_DIR / f"prompt_{prompt_id:03d}_20260115_131511.png"
        if not output_path.exists():
            output_path = EXP3_DIR / f"prompt_{prompt_id:03d}_20260115_161352.png"
        axes[row, 3].imshow(load_image(output_path))
        axes[row, 3].axis('off')
        if row == 0:
            axes[row, 3].set_title('Output', fontsize=11, fontweight='bold', pad=8)
        # Model badge
        axes[row, 3].text(0.98, 0.98, 'FLUX.2-dev', transform=axes[row, 3].transAxes,
                         ha='right', va='top', fontsize=8, color='white',
                         bbox=dict(boxstyle='round,pad=0.3', facecolor=model_badge, alpha=0.9))

    fig.suptitle('Experiment 3: Gender-Occupation Stereotype Following (WinoBias)',
                fontsize=14, fontweight='bold', y=0.98)

    plt.tight_layout(rect=[0, 0.02, 1, 0.95])
    plt.savefig(OUTPUT_DIR / "exp3_winobias.pdf", bbox_inches='tight', dpi=300, facecolor='white')
    plt.savefig(OUTPUT_DIR / "exp3_winobias.png", bbox_inches='tight', dpi=300, facecolor='white')
    print(f"Saved: {OUTPUT_DIR / 'exp3_winobias.pdf'}")
    plt.close()


def create_exp3_compact():
    """Create compact version with 2 examples."""

    # Load prompts
    with open(PROMPTS_FILE, 'r') as f:
        prompts = json.load(f)

    # Select 2 clear examples
    selected_ids = [9, 2]  # CEO, chief - both male-stereotyped
    selected = [p for p in prompts if p['id'] in selected_ids]

    fig = plt.figure(figsize=(12, 8))

    badge_color = '#2c3e50'
    model_badge = '#e74c3c'
    prompt_bg = '#34495e'

    for idx, item in enumerate(selected):
        y_offset = 0.52 if idx == 0 else 0.02

        prompt_id = item['id']
        prompt_text = item['prompt']
        img1_file = item['input_image_1']
        img2_file = item['input_image_2']
        stereotype = item['gender_stereotype']

        # Input 1
        ax1 = fig.add_axes([0.02, y_offset + 0.15, 0.22, 0.32])
        img1_path = get_source_path(img1_file)
        ax1.imshow(load_image(img1_path))
        ax1.axis('off')
        demo1 = img1_file.replace('.jpg', '').replace('_', '/')
        ax1.text(0.5, -0.05, demo1, transform=ax1.transAxes,
                ha='center', va='top', fontsize=9, fontweight='bold')
        if idx == 0:
            ax1.set_title('Input 1', fontsize=10, fontweight='bold')

        # Input 2
        ax2 = fig.add_axes([0.26, y_offset + 0.15, 0.22, 0.32])
        img2_path = get_source_path(img2_file)
        ax2.imshow(load_image(img2_path))
        ax2.axis('off')
        demo2 = img2_file.replace('.jpg', '').replace('_', '/')
        ax2.text(0.5, -0.05, demo2, transform=ax2.transAxes,
                ha='center', va='top', fontsize=9, fontweight='bold')
        if idx == 0:
            ax2.set_title('Input 2', fontsize=10, fontweight='bold')

        # Prompt box + arrow
        ax3 = fig.add_axes([0.50, y_offset + 0.15, 0.24, 0.32])
        ax3.set_facecolor(prompt_bg)
        ax3.set_xlim(0, 1)
        ax3.set_ylim(0, 1)
        ax3.axis('off')
        if idx == 0:
            ax3.set_title('Prompt', fontsize=10, fontweight='bold')

        # Truncate prompt for display
        display_prompt = prompt_text if len(prompt_text) < 80 else prompt_text[:77] + '...'
        ax3.text(0.5, 0.5, f'"{display_prompt}"',
                transform=ax3.transAxes, ha='center', va='center',
                fontsize=8, color='white', wrap=True, style='italic')
        ax3.text(0.5, 0.1, f'[{stereotype} = male stereotype]',
                transform=ax3.transAxes, ha='center', va='bottom',
                fontsize=8, color='#f39c12', fontweight='bold')

        # Arrow using text
        fig.text(0.745, y_offset + 0.31, '-->', fontsize=16, ha='center', va='center',
                fontweight='bold', family='monospace')

        # Output
        ax4 = fig.add_axes([0.76, y_offset + 0.15, 0.22, 0.32])
        output_path = EXP3_DIR / f"prompt_{prompt_id:03d}_20260115_131511.png"
        if not output_path.exists():
            output_path = EXP3_DIR / f"prompt_{prompt_id:03d}_20260115_161352.png"
        ax4.imshow(load_image(output_path))
        ax4.axis('off')
        if idx == 0:
            ax4.set_title('Output', fontsize=10, fontweight='bold')
        ax4.text(0.98, 0.98, 'FLUX.2-dev', transform=ax4.transAxes,
                ha='right', va='top', fontsize=8, color='white',
                bbox=dict(boxstyle='round,pad=0.2', facecolor=model_badge, alpha=0.9))

    fig.suptitle('Experiment 3: Gender-Occupation Stereotype Following (WinoBias)',
                fontsize=14, fontweight='bold', y=0.98)

    plt.savefig(OUTPUT_DIR / "exp3_compact.pdf", bbox_inches='tight', dpi=300, facecolor='white')
    plt.savefig(OUTPUT_DIR / "exp3_compact.png", bbox_inches='tight', dpi=300, facecolor='white')
    print(f"Saved: {OUTPUT_DIR / 'exp3_compact.pdf'}")
    plt.close()


if __name__ == "__main__":
    print("Generating Experiment 3 figures...")
    create_exp3_figure()
    create_exp3_compact()
    print("Done!")
