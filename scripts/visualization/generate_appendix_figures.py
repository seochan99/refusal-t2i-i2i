#!/usr/bin/env python3
"""Generate Appendix Figures for IJCAI Paper.

Creates 4 types of figures:
1. Failure Case Gallery - high race drift cases
2. Per-Prompt Grid - same prompt across different races
3. Baseline vs Ours Comparison
4. Model Comparison - same input across 3 models
"""

import json
import random
from pathlib import Path
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

# Paths
PROJECT_ROOT = Path("/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal")
IMAGES_DIR = PROJECT_ROOT / "survey/public/images"
SOURCE_DIR = PROJECT_ROOT / "survey/public/images/source"  # Correct source path
OUTPUT_DIR = PROJECT_ROOT / "paper/IJCAI_ECAI_26_I2I_Bias___Appendix/assets"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Category mapping: B -> O, D -> V
CATEGORY_MAP = {
    'B': 'O',  # Occupational
    'D': 'V',  # Vulnerability
}

# Prompt descriptions (short) - accurate to i2i_prompts.json
PROMPT_NAMES = {
    'B01': 'CEO/Executive',
    'B02': 'Military Strategist',
    'B03': 'Medical Specialist',
    'B04': 'Kindergarten Teacher',
    'B05': 'Housekeeper',
    'B06': 'Security Supervisor',
    'B07': 'Politician',
    'B08': 'Professional Athlete',
    'B09': 'Fashion Model',
    'B10': 'Software Engineer',
    'D01': 'Wheelchair User',
    'D02': 'Blind/Cane',
    'D03': 'Aged (+30 years)',
    'D04': 'Hearing Aid',
    'D05': 'Homeless',
    'D06': 'Refugee',
    'D07': 'Malnourished',
    'D08': 'Exhausted Worker',
    'D09': 'Grief/Mourning',
    'D10': 'Poverty',
}

RACES = ['White', 'Black', 'EastAsian', 'SoutheastAsian', 'Indian', 'MiddleEastern', 'Latino']
RACE_SHORT = {
    'White': 'White',
    'Black': 'Black',
    'EastAsian': 'E.Asian',
    'SoutheastAsian': 'SE.Asian',
    'Indian': 'Indian',
    'MiddleEastern': 'Mid.East',
    'Latino': 'Latino'
}

def get_prompt_label(prompt_id):
    """Convert B01 -> O01, D03 -> V03"""
    cat = prompt_id[0]
    num = prompt_id[1:]
    new_cat = CATEGORY_MAP.get(cat, cat)
    return f"{new_cat}{num}"

def load_vlm_scores():
    """Load VLM scores for filtering."""
    scores = {}
    with open(PROJECT_ROOT / "data/final/REAL_FINAL/exp1_vlm_scores_5040.jsonl") as f:
        for line in f:
            item = json.loads(line)
            key = f"{item['model']}_{item['prompt_id']}_{item['race']}_{item['gender']}_{item['age']}"
            scores[key] = item.get('scores', {})
    return scores

def find_edited_image(model, prompt_id, race, gender, age):
    """Find edited image path."""
    cat = 'B_occupation' if prompt_id.startswith('B') else 'D_vulnerability'
    pattern = f"{prompt_id}_{race}_{gender}_{age}"

    base_dir = IMAGES_DIR / "exp1_sampling_b_d" / model / cat
    for suffix in ['_success.png', '_unchanged.png', '.png']:
        path = base_dir / f"{pattern}{suffix}"
        if path.exists():
            return path
    return None

def find_preserved_image(model, prompt_id, race, gender, age):
    """Find preserved image path."""
    pattern = f"{prompt_id}_{race}_{gender}_{age}.png"
    path = IMAGES_DIR / "exp1_amt_preserved_500" / model / pattern
    if path.exists():
        return path
    return None

def find_source_image(race, gender, age):
    """Find source image path from survey/public/images/source/{race}/"""
    for ext in ['.jpg', '.png', '.jpeg']:
        path = SOURCE_DIR / race / f"{race}_{gender}_{age}{ext}"
        if path.exists():
            return path
    # Also try without race prefix in filename
    for ext in ['.jpg', '.png', '.jpeg']:
        path = SOURCE_DIR / race / f"{gender}_{age}{ext}"
        if path.exists():
            return path
    return None

def load_and_resize(path, size=(150, 150)):
    """Load and resize image."""
    if path is None or not path.exists():
        # Return placeholder
        img = Image.new('RGB', size, (200, 200, 200))
        return img
    img = Image.open(path).convert('RGB')
    img = img.resize(size, Image.Resampling.LANCZOS)
    return img


# ============================================================
# Figure 1: Failure Case Gallery
# ============================================================
def generate_failure_gallery():
    """Generate failure case gallery showing worst race drift cases."""
    print("\n=== Generating Failure Case Gallery ===")

    vlm_scores = load_vlm_scores()

    # Find high drift cases (B and D only)
    failures = []
    for key, scores in vlm_scores.items():
        parts = key.split('_')
        model, prompt_id = parts[0], parts[1]

        if not (prompt_id.startswith('B') or prompt_id.startswith('D')):
            continue

        race_drift = scores.get('race_drift', 0)
        skin_tone = scores.get('skin_tone', 3)

        if race_drift >= 4:
            race, gender, age = parts[2], parts[3], parts[4]
            img_path = find_edited_image(model, prompt_id, race, gender, age)
            src_path = find_source_image(race, gender, age)

            if img_path and src_path:
                failures.append({
                    'model': model,
                    'prompt_id': prompt_id,
                    'race': race,
                    'gender': gender,
                    'age': age,
                    'race_drift': race_drift,
                    'skin_tone': skin_tone,
                    'edited_path': img_path,
                    'source_path': src_path
                })

    # Sort by severity and diversify
    failures.sort(key=lambda x: (-x['race_drift'], -x['skin_tone']))

    # Select diverse cases (different prompts, races, models)
    selected = []
    seen = set()
    for f in failures:
        key = (f['prompt_id'], f['race'])
        if key not in seen and len(selected) < 16:
            selected.append(f)
            seen.add(key)

    # Create figure: 4x4 grid, each cell has Source -> Output
    fig, axes = plt.subplots(4, 4, figsize=(12, 12))

    for idx, case in enumerate(selected[:16]):
        row, col = idx // 4, idx % 4
        ax = axes[row, col]

        # Load images
        src_img = load_and_resize(case['source_path'], (120, 120))
        out_img = load_and_resize(case['edited_path'], (120, 120))

        # Combine side by side
        combined = Image.new('RGB', (250, 120), (255, 255, 255))
        combined.paste(src_img, (0, 0))
        combined.paste(out_img, (130, 0))

        ax.imshow(combined)
        ax.axis('off')

        prompt_label = get_prompt_label(case['prompt_id'])
        title = f"{prompt_label} {RACE_SHORT[case['race']]}\nChange={case['race_drift']}, Skin={case['skin_tone']}"
        ax.set_title(title, fontsize=8)

    # Add column headers
    fig.text(0.25, 0.92, 'Source → Output (High Identity Change Cases)',
             ha='center', fontsize=14, fontweight='bold')

    plt.tight_layout(rect=[0, 0, 1, 0.90])

    # Save
    fig.savefig(OUTPUT_DIR / "appendix_failure_gallery.pdf", bbox_inches='tight', dpi=300)
    fig.savefig(OUTPUT_DIR / "appendix_failure_gallery.png", bbox_inches='tight', dpi=300)
    print(f"Saved: {OUTPUT_DIR}/appendix_failure_gallery.pdf")
    plt.close()


# ============================================================
# Figure 2: Per-Prompt Grid (Source + 7 Races) with Row Labels
# ============================================================
def generate_per_prompt_grid():
    """Generate grid showing Source + same prompt across all 7 races."""
    print("\n=== Generating Per-Prompt Grid ===")

    # Select representative prompts (O and V only)
    prompts = ['B01', 'B03', 'B05', 'B07', 'D01', 'D03']
    # All 7 races
    all_races = ['White', 'Black', 'EastAsian', 'SoutheastAsian', 'Indian', 'MiddleEastern', 'Latino']

    model = 'flux'  # Use FLUX as representative

    # 8 columns: Source + 7 races
    n_cols = 1 + len(all_races)  # Source + 7 races = 8
    n_rows = len(prompts)

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 11))
    plt.subplots_adjust(left=0.12, right=0.98, top=0.92, bottom=0.02, wspace=0.05, hspace=0.15)

    for row, prompt_id in enumerate(prompts):
        # Column 0: Source image (use White as reference source)
        ax = axes[row, 0]

        # Find source for this row
        src_path = None
        for gender in ['Male', 'Female']:
            for age in ['30s', '40s', '20s', '50s']:
                src_path = find_source_image('White', gender, age)
                if src_path:
                    break
            if src_path:
                break

        src_img = load_and_resize(src_path, (120, 120))
        ax.imshow(src_img)
        ax.axis('off')

        if row == 0:
            ax.set_title('Source', fontsize=10, fontweight='bold')

        # Row label using fig.text (left of the row)
        prompt_label = get_prompt_label(prompt_id)
        name = PROMPT_NAMES.get(prompt_id, prompt_id)

        # Calculate y position for this row
        row_y = 1.0 - (row + 0.5) / n_rows * 0.90 - 0.04
        fig.text(0.01, row_y, f"{prompt_label}\n{name}", fontsize=9,
                 ha='left', va='center', fontweight='bold')

        # Columns 1-7: Each race output
        for col_idx, race in enumerate(all_races, 1):
            ax = axes[row, col_idx]

            # Find edited image for this prompt/race
            img_path = None
            for gender in ['Male', 'Female']:
                for age in ['30s', '40s', '20s', '50s']:
                    img_path = find_edited_image(model, prompt_id, race, gender, age)
                    if img_path:
                        break
                if img_path:
                    break

            img = load_and_resize(img_path, (120, 120))
            ax.imshow(img)
            ax.axis('off')

            # Column headers (race)
            if row == 0:
                ax.set_title(RACE_SHORT[race], fontsize=9, fontweight='bold')

    fig.suptitle('Same Prompt Across Different Races (FLUX.2-dev)',
                 fontsize=14, fontweight='bold', y=0.98)

    fig.savefig(OUTPUT_DIR / "appendix_per_prompt_grid.pdf", bbox_inches='tight', dpi=300)
    fig.savefig(OUTPUT_DIR / "appendix_per_prompt_grid.png", bbox_inches='tight', dpi=300)
    print(f"Saved: {OUTPUT_DIR}/appendix_per_prompt_grid.pdf")
    plt.close()


# ============================================================
# Figure 3: Baseline vs Ours Comparison
# ============================================================
def generate_baseline_vs_ours():
    """Generate comparison grid: Source | Baseline | Ours (Preserved)."""
    print("\n=== Generating Baseline vs Ours Comparison ===")

    vlm_scores = load_vlm_scores()

    # Find cases where preserved exists and shows improvement
    comparisons = []

    preserved_dir = IMAGES_DIR / "exp1_amt_preserved_500"
    for model_dir in preserved_dir.iterdir():
        if not model_dir.is_dir():
            continue
        model = model_dir.name

        for img_path in model_dir.glob("*.png"):
            parts = img_path.stem.split('_')
            if len(parts) < 4:
                continue

            prompt_id, race, gender, age = parts[0], parts[1], parts[2], parts[3]

            if not (prompt_id.startswith('B') or prompt_id.startswith('D')):
                continue

            # Get VLM score for baseline
            key = f"{model}_{prompt_id}_{race}_{gender}_{age}"
            scores = vlm_scores.get(key, {})
            race_drift = scores.get('race_drift', 0)

            # We want cases with high baseline drift
            if race_drift >= 3:
                src_path = find_source_image(race, gender, age)
                baseline_path = find_edited_image(model, prompt_id, race, gender, age)

                if src_path and baseline_path:
                    comparisons.append({
                        'model': model,
                        'prompt_id': prompt_id,
                        'race': race,
                        'gender': gender,
                        'age': age,
                        'race_drift': race_drift,
                        'source_path': src_path,
                        'baseline_path': baseline_path,
                        'preserved_path': img_path
                    })

    # Sort by drift and select diverse cases
    comparisons.sort(key=lambda x: -x['race_drift'])

    selected = []
    seen = set()
    for c in comparisons:
        key = (c['prompt_id'], c['race'])
        if key not in seen and len(selected) < 12:
            selected.append(c)
            seen.add(key)

    # Create figure: 4 rows x 3 cols per case = 12 cases in 4x3 grid
    fig, axes = plt.subplots(4, 3, figsize=(10, 13))

    for idx, case in enumerate(selected[:12]):
        row, col = idx // 3, idx % 3
        ax = axes[row, col]

        # Load images
        src = load_and_resize(case['source_path'], (100, 100))
        baseline = load_and_resize(case['baseline_path'], (100, 100))
        preserved = load_and_resize(case['preserved_path'], (100, 100))

        # Combine: Source | Baseline | Ours
        combined = Image.new('RGB', (320, 100), (255, 255, 255))
        combined.paste(src, (0, 0))
        combined.paste(baseline, (110, 0))
        combined.paste(preserved, (220, 0))

        ax.imshow(combined)
        ax.axis('off')

        prompt_label = get_prompt_label(case['prompt_id'])
        ax.set_title(f"{prompt_label} {RACE_SHORT[case['race']]} ({case['model']})", fontsize=9)

    # Add header
    fig.text(0.5, 0.96, 'Source → Baseline → Ours (Feature Prompt)',
             ha='center', fontsize=14, fontweight='bold')
    fig.text(0.17, 0.93, 'Source', ha='center', fontsize=10)
    fig.text(0.5, 0.93, 'Baseline', ha='center', fontsize=10)
    fig.text(0.83, 0.93, 'Ours', ha='center', fontsize=10)

    plt.tight_layout(rect=[0, 0, 1, 0.92])

    fig.savefig(OUTPUT_DIR / "appendix_baseline_vs_ours.pdf", bbox_inches='tight', dpi=300)
    fig.savefig(OUTPUT_DIR / "appendix_baseline_vs_ours.png", bbox_inches='tight', dpi=300)
    print(f"Saved: {OUTPUT_DIR}/appendix_baseline_vs_ours.pdf")
    plt.close()


# ============================================================
# Figure 4: Model Comparison (More Square Layout)
# ============================================================
def generate_model_comparison():
    """Generate comparison across 3 models for same input. Square layout."""
    print("\n=== Generating Model Comparison ===")

    # Select diverse prompt/race combinations (6 cases for square layout)
    cases = [
        ('B01', 'Black', 'Female', '30s'),       # CEO - Black
        ('B01', 'Indian', 'Male', '40s'),        # CEO - Indian
        ('B03', 'Latino', 'Female', '30s'),      # Medical - Latino
        ('B05', 'EastAsian', 'Female', '40s'),   # Housekeeper - EastAsian
        ('B07', 'MiddleEastern', 'Male', '30s'), # Doctor - MiddleEastern
        ('D03', 'White', 'Female', '50s'),       # Aging - White
    ]

    models = ['flux', 'step1x', 'qwen']
    model_names = ['FLUX.2-dev', 'Step1X-Edit', 'Qwen-Edit']

    # Square-ish layout: 6 rows × 4 cols
    fig, axes = plt.subplots(len(cases), 4, figsize=(10, 12))

    for row, (prompt_id, race, gender, age) in enumerate(cases):
        # Source image
        src_path = find_source_image(race, gender, age)
        src_img = load_and_resize(src_path, (130, 130))

        axes[row, 0].imshow(src_img)
        axes[row, 0].axis('off')
        if row == 0:
            axes[row, 0].set_title('Source', fontsize=11, fontweight='bold')

        # Row label: Prompt + Race
        prompt_label = get_prompt_label(prompt_id)
        prompt_name = PROMPT_NAMES.get(prompt_id, '')
        race_label = RACE_SHORT[race]
        axes[row, 0].set_ylabel(f"{prompt_label}\n({race_label})",
                                fontsize=10, rotation=0, ha='right', va='center', labelpad=55)

        # Model outputs
        for col, (model, model_name) in enumerate(zip(models, model_names), 1):
            img_path = find_edited_image(model, prompt_id, race, gender, age)
            img = load_and_resize(img_path, (130, 130))

            axes[row, col].imshow(img)
            axes[row, col].axis('off')
            if row == 0:
                axes[row, col].set_title(model_name, fontsize=11, fontweight='bold')

    fig.suptitle('Same Input Across Three Models', fontsize=14, fontweight='bold', y=0.98)

    plt.tight_layout(rect=[0.1, 0, 1, 0.96])

    fig.savefig(OUTPUT_DIR / "appendix_model_comparison.pdf", bbox_inches='tight', dpi=300)
    fig.savefig(OUTPUT_DIR / "appendix_model_comparison.png", bbox_inches='tight', dpi=300)
    print(f"Saved: {OUTPUT_DIR}/appendix_model_comparison.pdf")
    plt.close()


if __name__ == "__main__":
    random.seed(42)

    print("Generating Appendix Figures...")
    print(f"Output directory: {OUTPUT_DIR}")

    generate_failure_gallery()
    generate_per_prompt_grid()
    generate_baseline_vs_ours()
    generate_model_comparison()

    print("\n=== All Done! ===")
