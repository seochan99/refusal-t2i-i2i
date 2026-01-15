#!/usr/bin/env python3
"""
Visualize prompt-by-prompt comparison of base vs edited images
organized by race and gender for easy identification of severe changes
and racial disparities.

Purpose: Help identify candidate prompts for preservation experiment 2.
Shows all 84 images (7 races × 2 genders × 6 ages) per prompt.
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import Rectangle
from PIL import Image
import numpy as np
import multiprocessing as mp
from functools import partial
import os

PROJECT_ROOT = Path(__file__).parent.parent.parent
RESULTS_DIR = PROJECT_ROOT / "data" / "results" / "exp1_sampling" / "step1x_organized"
PROMPTS_FILE = PROJECT_ROOT / "data" / "prompts" / "i2i_prompts.json"
OUTPUT_DIR = PROJECT_ROOT / "data" / "analysis" / "prompt_comparisons"
SOURCE_IMAGES_DIR = PROJECT_ROOT / "data" / "source_images" / "final"

RACES = ["Black", "EastAsian", "Indian", "Latino", "MiddleEastern", "SoutheastAsian", "White"]
GENDERS = ["Male", "Female"]
AGES = ["20s", "30s", "40s", "50s", "60s", "70plus"]

CATEGORY_MAP = {
    "A": "A_neutral",
    "B": "B_occupation",
    "C": "C_cultural",
    "D": "D_vulnerability",
    "E": "E_harmful"
}


def load_prompts() -> Dict[str, Dict]:
    """Load prompt metadata."""
    with open(PROMPTS_FILE, 'r') as f:
        data = json.load(f)
    
    prompts = {}
    for prompt in data['prompts']:
        prompts[prompt['id']] = prompt
    
    return prompts


def find_source_image(race: str, gender: str, age: str) -> Optional[Path]:
    """Find source image file."""
    # Source image path: {Race}/{Race}_{Gender}_{Age}.jpg
    source_file = SOURCE_IMAGES_DIR / race / f"{race}_{gender}_{age}.jpg"
    if source_file.exists():
        return source_file
    
    # Try alternative path
    alt_file = SOURCE_IMAGES_DIR / race / f"{race}_{gender}_{age}.png"
    if alt_file.exists():
        return alt_file
    
    return None


def find_image_files(prompt_id: str, category: str, race: str, gender: str, age: str) -> Tuple[Optional[Path], Optional[Path], Optional[Path], bool]:
    """Find source, base (unchanged), and edited (success) image files for a given combination."""
    cat_dir = RESULTS_DIR / "by_category" / CATEGORY_MAP[category]
    
    if not cat_dir.exists():
        return None, None, None
    
    # Source image
    source_path = find_source_image(race, gender, age)
    
    # Try different status patterns for base (unchanged)
    base_patterns = [
        f"{prompt_id}_{race}_{gender}_{age}_unchanged.png",
        f"{prompt_id}_{race}_{gender}_{age}_base.png"
    ]
    
    base_path = None
    for pattern in base_patterns:
        base_file = cat_dir / pattern
        if base_file.exists():
            base_path = base_file
            break
    
    # Try different status patterns for edited (success)
    edited_patterns = [
        f"{prompt_id}_{race}_{gender}_{age}_success.png",
        f"{prompt_id}_{race}_{gender}_{age}_edited.png"
    ]
    
    edited_path = None
    edited_is_unchanged = False
    for pattern in edited_patterns:
        edited_file = cat_dir / pattern
        if edited_file.exists():
            edited_path = edited_file
            break
    
    # Check if edited is actually unchanged (refused/not edited)
    if edited_path is None:
        # Check for unchanged file as edited (means edit was refused)
        unchanged_as_edited = cat_dir / f"{prompt_id}_{race}_{gender}_{age}_unchanged.png"
        if unchanged_as_edited.exists():
            edited_path = unchanged_as_edited
            edited_is_unchanged = True
    
    return source_path, base_path, edited_path, edited_is_unchanged


def load_image_safe(path: Optional[Path], default_size=(512, 512)) -> np.ndarray:
    """Load image or return blank placeholder."""
    if path and path.exists():
        try:
            img = Image.open(path)
            img = img.convert('RGB')
            img = img.resize(default_size, Image.Resampling.LANCZOS)
            arr = np.array(img)
            # Verify image is not empty
            if arr.size > 0 and arr.max() > arr.min():
                return arr
            else:
                print(f"  Warning: Empty or invalid image at {path}")
        except Exception as e:
            print(f"  Warning: Error loading {path}: {e}")
    
    # Return blank white image with gray border to indicate missing
    img = np.ones((*default_size, 3), dtype=np.uint8) * 255
    # Add a subtle border to indicate missing image
    img[0:5, :] = 200
    img[-5:, :] = 200
    img[:, 0:5] = 200
    img[:, -5:] = 200
    return img


def create_prompt_comparison_plot(prompt_id: str, prompt_info: Dict, output_path: Path):
    """
    Create a comparison plot for a single prompt showing ALL 84 images:
    - Rows: 7 Races × 2 Genders = 14 rows
    - Columns: Source | Edited for each of 6 ages = 12 columns
    Note: Source and Base are the same, so we only show Source | Edited
    """
    category = prompt_info['category']
    prompt_text = prompt_info['prompt']
    
    # Use ALL ages (84 images total: 7 races × 2 genders × 6 ages)
    selected_ages = AGES  # All 6 ages
    selected_races = RACES  # All 7 races
    
    # Create figure with subplots
    # Layout: (races * genders) rows x (source + edited per age) columns
    n_rows = len(selected_races) * len(GENDERS)  # 7 × 2 = 14 rows
    n_cols = len(selected_ages) * 2  # 6 × 2 = 12 columns (Source | Edited for each age)
    
    # Adjust figure size for better readability
    fig = plt.figure(figsize=(n_cols * 2.0, n_rows * 2.0))
    gs = gridspec.GridSpec(n_rows, n_cols, figure=fig, hspace=0.12, wspace=0.08)
    
    fig.suptitle(
        f"{prompt_id} ({category}): {prompt_text[:100]}{'...' if len(prompt_text) > 100 else ''}",
        fontsize=12, fontweight='bold', y=0.998
    )
    
    row_idx = 0
    for race in selected_races:
        for gender in GENDERS:
            col_idx = 0
            for age in selected_ages:
                source_path, base_path, edited_path, edited_is_unchanged = find_image_files(prompt_id, category, race, gender, age)
                
                # Source image (same as base/unchanged)
                ax_source = fig.add_subplot(gs[row_idx, col_idx])
                # Prefer source, fallback to base (unchanged) if source not found
                display_path = source_path
                if source_path is None and base_path:
                    display_path = base_path
                
                source_img = load_image_safe(display_path)
                # Ensure image is properly formatted for imshow
                if source_img is not None and source_img.size > 0:
                    # Normalize to 0-1 range if needed
                    if source_img.dtype != np.uint8:
                        source_img = source_img.astype(np.uint8)
                    # Ensure 3 channels
                    if len(source_img.shape) == 2:
                        source_img = np.stack([source_img] * 3, axis=-1)
                    elif source_img.shape[2] == 4:  # RGBA
                        source_img = source_img[:, :, :3]
                    ax_source.imshow(source_img, interpolation='bilinear')
                else:
                    # Show placeholder text
                    ax_source.text(0.5, 0.5, 'No Source\n(unchanged)', 
                                  ha='center', va='center', 
                                  transform=ax_source.transAxes,
                                  fontsize=9, color='red', weight='bold')
                
                ax_source.axis('off')
                if col_idx == 0:
                    ax_source.set_ylabel(f"{race}\n{gender}", fontsize=9, fontweight='bold')
                if row_idx == 0:
                    ax_source.set_title(f"Source ({age})", fontsize=8, fontweight='bold')
                
                # Add red border if source or base is missing
                if source_path is None and base_path is None:
                    for spine in ax_source.spines.values():
                        spine.set_edgecolor('red')
                        spine.set_linewidth(3)
                
                # Edited image (success)
                ax_edited = fig.add_subplot(gs[row_idx, col_idx + 1])
                edited_img = load_image_safe(edited_path)
                # Ensure image is properly formatted for imshow
                if edited_img is not None and edited_img.size > 0:
                    # Normalize to 0-1 range if needed
                    if edited_img.dtype != np.uint8:
                        edited_img = edited_img.astype(np.uint8)
                    # Ensure 3 channels
                    if len(edited_img.shape) == 2:
                        edited_img = np.stack([edited_img] * 3, axis=-1)
                    elif edited_img.shape[2] == 4:  # RGBA
                        edited_img = edited_img[:, :, :3]
                    ax_edited.imshow(edited_img, interpolation='bilinear')
                else:
                    # If image is invalid, show placeholder
                    ax_edited.text(0.5, 0.5, 'No image', 
                                  ha='center', va='center', 
                                  transform=ax_edited.transAxes,
                                  fontsize=10, color='red')
                ax_edited.axis('off')
                if row_idx == 0:
                    ax_edited.set_title(f"Edited ({age})", fontsize=8, fontweight='bold')
                
                # Add red border if edited is unchanged (edit was refused) or missing
                if edited_is_unchanged or edited_path is None:
                    # Use Rectangle patch to draw red border (works even with axis('off'))
                    rect = Rectangle((0, 0), 1, 1, transform=ax_edited.transAxes,
                                    fill=False, edgecolor='red', linewidth=4, zorder=10)
                    ax_edited.add_patch(rect)
                
                col_idx += 2
            
            row_idx += 1
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    return output_path.name


def create_race_focused_plot(prompt_id: str, prompt_info: Dict, output_path: Path,
                             gender: str = "Male", age: str = "40s"):
    """
    Create a race-focused comparison showing all races side-by-side.
    Better for identifying racial disparities.
    Layout: 2 rows (Source, Edited) × 7 races
    Note: Source and Base are the same
    """
    category = prompt_info['category']
    prompt_text = prompt_info['prompt']
    
    n_races = len(RACES)
    fig, axes = plt.subplots(2, n_races, figsize=(n_races * 2.5, 5))
    
    fig.suptitle(
        f"{prompt_id} ({category}): {prompt_text[:100]}{'...' if len(prompt_text) > 100 else ''}\n"
        f"Gender: {gender}, Age: {age}",
        fontsize=12, fontweight='bold'
    )
    
    # Top row: Source images (same as base)
    for idx, race in enumerate(RACES):
        source_path, base_path, _, _ = find_image_files(prompt_id, category, race, gender, age)
        # Prefer source, fallback to base if source not found
        display_source_path = source_path
        if source_path is None and base_path:
            display_source_path = base_path
        source_img = load_image_safe(display_source_path)
        axes[0, idx].imshow(source_img)
        axes[0, idx].axis('off')
        axes[0, idx].set_title(f"{race}\nSource", fontsize=10, fontweight='bold')
        
        if source_path is None:
            for spine in axes[0, idx].spines.values():
                spine.set_edgecolor('red')
                spine.set_linewidth(2)
    
    # Bottom row: Edited images (success or unchanged if refused)
    for idx, race in enumerate(RACES):
        _, _, edited_path, edited_is_unchanged = find_image_files(prompt_id, category, race, gender, age)
        edited_img = load_image_safe(edited_path)
        axes[1, idx].imshow(edited_img)
        axes[1, idx].axis('off')
        axes[1, idx].set_title(f"{race}\nEdited", fontsize=10, fontweight='bold')
        
        # Add red border if edited is unchanged (edit was refused) or missing
        if edited_is_unchanged or edited_path is None:
            # Use Rectangle patch to draw red border (works even with axis('off'))
            rect = Rectangle((0, 0), 1, 1, transform=axes[1, idx].transAxes,
                            fill=False, edgecolor='red', linewidth=4, zorder=10)
            axes[1, idx].add_patch(rect)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    return output_path.name


def process_prompt_detailed(args_tuple):
    """Wrapper for parallel processing of detailed plots."""
    prompt_id, prompt_info, output_dir = args_tuple
    try:
        output_file = output_dir / f"{prompt_id}_detailed_comparison.png"
        result = create_prompt_comparison_plot(prompt_id, prompt_info, output_file)
        return f"  ✓ {prompt_id}: {result}"
    except Exception as e:
        return f"  ✗ {prompt_id}: Error - {e}"


def process_prompt_race_focused(args_tuple):
    """Wrapper for parallel processing of race-focused plots."""
    prompt_id, prompt_info, output_dir, gender, age = args_tuple
    try:
        output_file = output_dir / f"{prompt_id}_race_focused_{gender}_{age}.png"
        result = create_race_focused_plot(prompt_id, prompt_info, output_file, gender, age)
        return f"  ✓ {prompt_id}: {result}"
    except Exception as e:
        return f"  ✗ {prompt_id}: Error - {e}"


def main():
    parser = argparse.ArgumentParser(description="Visualize prompt comparisons for candidate selection")
    parser.add_argument("--categories", type=str, default="A,B,C,D,E",
                       help="Comma-separated list of categories (default: A,B,C,D,E)")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR,
                       help="Output directory for visualizations")
    parser.add_argument("--format", choices=["detailed", "race-focused", "both"], default="detailed",
                       help="Visualization format")
    parser.add_argument("--gender", choices=["Male", "Female"], default="Male",
                       help="Gender for race-focused plots")
    parser.add_argument("--age", choices=["20s", "30s", "40s", "50s", "60s", "70plus"], default="40s",
                       help="Age for race-focused plots")
    parser.add_argument("--workers", type=int, default=None,
                       help="Number of parallel workers (default: CPU count)")
    
    args = parser.parse_args()
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Set number of workers
    if args.workers is None:
        args.workers = 10  # Default to 10 workers
    else:
        args.workers = args.workers
    
    # Load prompts
    prompts = load_prompts()
    
    # Parse categories
    categories = [c.strip() for c in args.categories.split(",")]
    
    # Filter prompts by category
    prompts_to_process = {
        prompt_id: prompt_info
        for prompt_id, prompt_info in prompts.items()
        if prompt_info['category'] in categories
    }
    
    print(f"Generating visualizations for {len(prompts_to_process)} prompts")
    print(f"Categories: {categories}")
    print(f"Output directory: {args.output_dir}")
    print(f"Using {args.workers} parallel workers")
    print(f"Format: {args.format}")
    
    # Verify paths
    print(f"\nVerifying paths...")
    print(f"  Source images: {SOURCE_IMAGES_DIR} ({'✓' if SOURCE_IMAGES_DIR.exists() else '✗'})")
    print(f"  Results: {RESULTS_DIR} ({'✓' if RESULTS_DIR.exists() else '✗'})")
    
    # Process prompts
    if args.format in ["detailed", "both"]:
        print(f"\nGenerating detailed comparisons (all 84 images per prompt)...")
        
        tasks = [
            (prompt_id, prompt_info, args.output_dir)
            for prompt_id, prompt_info in prompts_to_process.items()
        ]
        
        with mp.Pool(processes=args.workers) as pool:
            results = pool.map(process_prompt_detailed, tasks)
        
        for result in results:
            print(result)
    
    if args.format in ["race-focused", "both"]:
        print(f"\nGenerating race-focused comparisons...")
        
        tasks = [
            (prompt_id, prompt_info, args.output_dir, args.gender, args.age)
            for prompt_id, prompt_info in prompts_to_process.items()
        ]
        
        with mp.Pool(processes=args.workers) as pool:
            results = pool.map(process_prompt_race_focused, tasks)
        
        for result in results:
            print(result)
    
    print(f"\n✓ All visualizations saved to: {args.output_dir}")


if __name__ == "__main__":
    main()
