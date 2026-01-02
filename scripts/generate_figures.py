#!/usr/bin/env python3
"""
ACRB Figure Generation Script
Generates publication-ready figures for IJCAI-ECAI 2026 submission.

Usage:
    python scripts/generate_figures.py --output paper/figures/
    python scripts/generate_figures.py --format pdf  # For camera-ready
    python scripts/generate_figures.py --format png  # For review

Output:
    - fig_heatmap_refusal.pdf: Model x Attribute refusal rate heatmap
    - fig_heatmap_erasure.pdf: Model x Attribute erasure rate heatmap
    - fig_disparity_bars.pdf: Disparity comparison bar chart
    - fig_domain_analysis.pdf: Domain-specific disparity analysis
    - fig_modality_comparison.pdf: T2I vs I2I comparison
"""

import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
from pathlib import Path

# Set publication-ready defaults
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'Times', 'DejaVu Serif'],
    'font.size': 10,
    'axes.titlesize': 11,
    'axes.labelsize': 10,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'legend.fontsize': 8,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.1,
})

# ACRB Color Palette
COLORS = {
    'primary': '#1E293B',      # Deep Slate
    'accent_blue': '#2563EB',  # Modern Blue
    'accent_emerald': '#059669',  # Emerald
    'accent_rose': '#E11D48',  # Rose
    'bg_light': '#F8FAFC',     # Ultra Light Gray
    'culture': '#3B82F6',      # Blue
    'gender': '#8B5CF6',       # Purple
    'disability': '#EF4444',   # Red
    'religion': '#F59E0B',     # Amber
    'age': '#10B981',          # Green
}

# Sample data (replace with actual experiment results)
MODELS = ['GPT-Img 1.5', 'Nano Banana', 'FLUX.2 max', 'Qwen-Edit', 'FLUX.2 dev', 'Step1X-Edit']
CULTURES = ['KR', 'CN', 'NG', 'KE', 'US', 'IN']
ATTRIBUTES = ['Culture', 'Gender', 'Disability', 'Religion', 'Age']

# Refusal rates by model x culture
REFUSAL_DATA = np.array([
    [4.2, 3.8, 12.1, 10.5, 2.1, 5.4],   # GPT-Img 1.5
    [8.2, 7.5, 22.1, 19.8, 5.3, 11.4],  # Nano Banana Pro
    [5.1, 4.8, 15.3, 14.2, 3.2, 8.7],   # FLUX.2 max
    [3.5, 3.1, 9.8, 8.7, 2.0, 4.2],     # Qwen-Edit
    [6.3, 5.9, 18.7, 16.1, 4.1, 9.2],   # FLUX.2 dev
    [7.8, 7.2, 20.4, 18.2, 4.5, 10.1],  # Step1X-Edit
])

# Erasure rates by attribute category (avg across models)
ERASURE_BY_ATTR = {
    'Neutral': 4.1,
    'Culture': 13.2,
    'Gender': 6.4,
    'Disability': 38.4,
    'Religion': 16.3,
    'Age': 7.1,
}

# Disparity metrics
DISPARITY_REFUSAL = {'Culture': 12.9, 'Gender': 1.5, 'Disability': 3.4, 'Religion': 7.5, 'Age': 5.1}
DISPARITY_ERASURE = {'Culture': 12.6, 'Gender': 4.2, 'Disability': 34.3, 'Religion': 17.5, 'Age': 6.7}


def create_heatmap_refusal(output_path: Path, fmt: str = 'pdf'):
    """Generate model x culture refusal rate heatmap."""
    fig, ax = plt.subplots(figsize=(6, 4))
    
    # Custom colormap: white -> blue -> dark blue
    cmap = LinearSegmentedColormap.from_list('acrb_blue', ['#F0F9FF', '#3B82F6', '#1E3A8A'])
    
    sns.heatmap(
        REFUSAL_DATA,
        annot=True,
        fmt='.1f',
        cmap=cmap,
        xticklabels=CULTURES,
        yticklabels=MODELS,
        cbar_kws={'label': 'Refusal Rate (%)'},
        linewidths=0.5,
        linecolor='white',
        ax=ax
    )
    
    ax.set_xlabel('Cultural Attribute')
    ax.set_ylabel('Model')
    ax.set_title('Hard Refusal Rates by Model and Cultural Attribute', fontweight='bold', pad=10)
    
    # Highlight max values
    for i in range(len(MODELS)):
        max_idx = np.argmax(REFUSAL_DATA[i])
        ax.add_patch(plt.Rectangle((max_idx, i), 1, 1, fill=False, edgecolor='#E11D48', lw=2))
    
    plt.tight_layout()
    fig.savefig(output_path / f'fig_heatmap_refusal.{fmt}')
    plt.close(fig)
    print(f"  Created: fig_heatmap_refusal.{fmt}")


def create_heatmap_erasure(output_path: Path, fmt: str = 'pdf'):
    """Generate model x attribute erasure rate heatmap."""
    # Erasure data by model x attribute category
    erasure_data = np.array([
        [12.4, 5.2, 35.6, 18.2, 8.4],   # GPT-Img 1.5
        [18.3, 8.1, 42.1, 25.3, 12.4],  # Nano Banana Pro
        [14.7, 6.2, 38.5, 21.8, 9.8],   # FLUX.2 max
        [11.2, 4.8, 32.4, 16.5, 7.2],   # Qwen-Edit
        [15.8, 6.7, 40.2, 23.4, 10.9],  # FLUX.2 dev
        [16.4, 7.1, 41.4, 24.1, 11.5],  # Step1X-Edit
    ])
    
    fig, ax = plt.subplots(figsize=(5, 4))
    
    # Custom colormap: white -> red -> dark red
    cmap = LinearSegmentedColormap.from_list('acrb_red', ['#FEF2F2', '#EF4444', '#7F1D1D'])
    
    sns.heatmap(
        erasure_data,
        annot=True,
        fmt='.1f',
        cmap=cmap,
        xticklabels=ATTRIBUTES,
        yticklabels=MODELS,
        cbar_kws={'label': 'Erasure Rate (%)'},
        linewidths=0.5,
        linecolor='white',
        ax=ax
    )
    
    ax.set_xlabel('Attribute Category')
    ax.set_ylabel('Model')
    ax.set_title('Soft Refusal (Cue Erasure) Rates', fontweight='bold', pad=10)
    
    plt.tight_layout()
    fig.savefig(output_path / f'fig_heatmap_erasure.{fmt}')
    plt.close(fig)
    print(f"  Created: fig_heatmap_erasure.{fmt}")


def create_disparity_bars(output_path: Path, fmt: str = 'pdf'):
    """Generate disparity comparison bar chart."""
    fig, ax = plt.subplots(figsize=(6, 4))
    
    x = np.arange(len(ATTRIBUTES))
    width = 0.35
    
    refusal_vals = [DISPARITY_REFUSAL[a] for a in ATTRIBUTES]
    erasure_vals = [DISPARITY_ERASURE[a] for a in ATTRIBUTES]
    
    bars1 = ax.bar(x - width/2, refusal_vals, width, label='$\Delta_{refusal}$', 
                   color=COLORS['accent_blue'], edgecolor='white', linewidth=0.5)
    bars2 = ax.bar(x + width/2, erasure_vals, width, label='$\Delta_{erasure}$', 
                   color=COLORS['accent_rose'], edgecolor='white', linewidth=0.5)
    
    # Add value labels
    for bar in bars1:
        height = bar.get_height()
        ax.annotate(f'{height:.1f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=7)
    
    for bar in bars2:
        height = bar.get_height()
        ax.annotate(f'{height:.1f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=7)
    
    ax.set_ylabel('Disparity (percentage points)')
    ax.set_xlabel('Attribute Category')
    ax.set_title('Refusal vs Erasure Disparity by Attribute', fontweight='bold', pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(ATTRIBUTES)
    ax.legend(loc='upper right', framealpha=0.9)
    ax.set_ylim(0, 42)
    
    # Add horizontal reference line
    ax.axhline(y=10, color='gray', linestyle='--', alpha=0.5, linewidth=0.8)
    ax.text(4.5, 10.5, 'Significant disparity threshold', fontsize=7, color='gray', ha='right')
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    fig.savefig(output_path / f'fig_disparity_bars.{fmt}')
    plt.close(fig)
    print(f"  Created: fig_disparity_bars.{fmt}")


def create_domain_analysis(output_path: Path, fmt: str = 'pdf'):
    """Generate domain-specific disparity analysis."""
    domains = ['Violence', 'Self-harm', 'Substance', 'Privacy', 'Religious', 
               'Body/App.', 'Sexual', 'Copyright', 'Unethical']
    
    # Nigerian vs US refusal disparity by domain
    ng_us_disparity = [18.2, 12.4, 14.8, 10.2, 8.7, 4.1, 9.3, 11.5, 16.7]
    
    # Disability erasure rate by domain
    disability_erasure = [28.4, 35.2, 22.1, 41.7, 31.4, 52.3, 18.9, 24.6, 29.8]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    
    # Left: Nigerian vs US disparity
    colors1 = [COLORS['accent_rose'] if v > 15 else COLORS['accent_blue'] for v in ng_us_disparity]
    bars1 = ax1.barh(domains, ng_us_disparity, color=colors1, edgecolor='white', linewidth=0.5)
    ax1.set_xlabel('$\Delta_{refusal}$ (NG vs US, pp)')
    ax1.set_title('Cultural Refusal Disparity by Domain', fontweight='bold', pad=10)
    ax1.axvline(x=10, color='gray', linestyle='--', alpha=0.5, linewidth=0.8)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    
    # Add value labels
    for bar, val in zip(bars1, ng_us_disparity):
        ax1.text(val + 0.5, bar.get_y() + bar.get_height()/2, 
                 f'{val:.1f}', va='center', fontsize=7)
    
    # Right: Disability erasure by domain
    colors2 = [COLORS['accent_rose'] if v > 40 else COLORS['accent_emerald'] for v in disability_erasure]
    bars2 = ax2.barh(domains, disability_erasure, color=colors2, edgecolor='white', linewidth=0.5)
    ax2.set_xlabel('Disability Erasure Rate (%)')
    ax2.set_title('Disability Cue Erasure by Domain', fontweight='bold', pad=10)
    ax2.axvline(x=40, color='gray', linestyle='--', alpha=0.5, linewidth=0.8)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    
    for bar, val in zip(bars2, disability_erasure):
        ax2.text(val + 0.5, bar.get_y() + bar.get_height()/2, 
                 f'{val:.1f}', va='center', fontsize=7)
    
    plt.tight_layout()
    fig.savefig(output_path / f'fig_domain_analysis.{fmt}')
    plt.close(fig)
    print(f"  Created: fig_domain_analysis.{fmt}")


def create_modality_comparison(output_path: Path, fmt: str = 'pdf'):
    """Generate T2I vs I2I comparison figure."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3.5))
    
    modalities = ['T2I', 'I2I']
    
    # Hard refusal rates
    refusal_t2i = [11.3, 8.2, 9.7, 14.1, 6.8]  # Culture, Gender, Disability, Religion, Age
    refusal_i2i = [6.8, 5.1, 5.9, 8.4, 4.3]
    
    x = np.arange(len(ATTRIBUTES))
    width = 0.35
    
    ax1.bar(x - width/2, refusal_t2i, width, label='T2I', color=COLORS['accent_blue'])
    ax1.bar(x + width/2, refusal_i2i, width, label='I2I', color=COLORS['accent_emerald'])
    ax1.set_ylabel('Refusal Rate (%)')
    ax1.set_title('Hard Refusal by Modality', fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(ATTRIBUTES, rotation=15, ha='right')
    ax1.legend()
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    
    # Soft refusal (erasure) rates
    erasure_t2i = [14.2, 6.1, 38.7, 22.4, 9.8]
    erasure_i2i = [15.1, 6.7, 38.0, 23.1, 10.4]
    
    ax2.bar(x - width/2, erasure_t2i, width, label='T2I', color=COLORS['accent_blue'])
    ax2.bar(x + width/2, erasure_i2i, width, label='I2I', color=COLORS['accent_emerald'])
    ax2.set_ylabel('Erasure Rate (%)')
    ax2.set_title('Soft Refusal (Erasure) by Modality', fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(ATTRIBUTES, rotation=15, ha='right')
    ax2.legend()
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    
    # Add annotation
    fig.text(0.5, -0.02, 'I2I shows lower hard refusal but comparable erasure rates', 
             ha='center', fontsize=9, style='italic', color='gray')
    
    plt.tight_layout()
    fig.savefig(output_path / f'fig_modality_comparison.{fmt}')
    plt.close(fig)
    print(f"  Created: fig_modality_comparison.{fmt}")


def create_radar_chart(output_path: Path, fmt: str = 'pdf'):
    """Generate radar chart for model comparison."""
    from math import pi
    
    # Metrics for radar chart (normalized to 0-100)
    categories = ['Low Refusal\n(US baseline)', 'Cultural\nEquity', 'Disability\nInclusion', 
                  'Religious\nNeutrality', 'Age\nFairness']
    
    # Model scores (higher = better = less bias)
    models_radar = {
        'GPT-Img 1.5': [97.9, 87.1, 64.4, 91.3, 93.2],
        'Qwen-Edit': [98.0, 90.2, 67.6, 92.8, 94.1],
        'FLUX.2 [dev]': [95.9, 81.3, 59.8, 87.6, 90.9],
    }
    
    N = len(categories)
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]  # Complete the loop
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    
    colors = [COLORS['accent_blue'], COLORS['accent_emerald'], COLORS['accent_rose']]
    
    for idx, (model, values) in enumerate(models_radar.items()):
        values += values[:1]
        ax.plot(angles, values, 'o-', linewidth=2, label=model, color=colors[idx])
        ax.fill(angles, values, alpha=0.15, color=colors[idx])
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, size=8)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20', '40', '60', '80', '100'], size=7)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
    ax.set_title('Model Fairness Profile\n(Higher = More Equitable)', fontweight='bold', pad=20)
    
    plt.tight_layout()
    fig.savefig(output_path / f'fig_radar_fairness.{fmt}')
    plt.close(fig)
    print(f"  Created: fig_radar_fairness.{fmt}")


def main():
    parser = argparse.ArgumentParser(description='Generate ACRB publication figures')
    parser.add_argument('--output', '-o', type=str, default='paper/figures/',
                        help='Output directory for figures')
    parser.add_argument('--format', '-f', type=str, default='pdf', choices=['pdf', 'png', 'svg'],
                        help='Output format (pdf for camera-ready, png for review)')
    parser.add_argument('--dpi', type=int, default=300,
                        help='DPI for raster formats')
    args = parser.parse_args()
    
    # Setup output directory
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\n=== ACRB Figure Generation ===")
    print(f"Output: {output_path.absolute()}")
    print(f"Format: {args.format}")
    print()
    
    # Generate all figures
    print("Generating figures...")
    create_heatmap_refusal(output_path, args.format)
    create_heatmap_erasure(output_path, args.format)
    create_disparity_bars(output_path, args.format)
    create_domain_analysis(output_path, args.format)
    create_modality_comparison(output_path, args.format)
    create_radar_chart(output_path, args.format)
    
    print(f"\nDone! Generated 6 figures in {output_path.absolute()}")
    print("\nUsage in LaTeX:")
    print("  \\includegraphics[width=\\columnwidth]{figures/fig_heatmap_refusal}")
    print("  \\includegraphics[width=\\textwidth]{figures/fig_domain_analysis}")


if __name__ == '__main__':
    main()
