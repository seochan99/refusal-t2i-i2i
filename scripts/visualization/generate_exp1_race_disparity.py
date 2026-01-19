#!/usr/bin/env python3
"""Generate Experiment 1 figure showing racial disparities across all 3 models."""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.dpi': 300,
})

OUTPUT_DIR = Path("/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/paper/I2I_Bias_Refusal/assets")

# ACTUAL VLM EVALUATION DATA from demographic_metrics.json files
races = ['White', 'E Asian', 'SE Asian', 'Latino', 'Black', 'Mid East', 'Indian']

# Skin Lightening Rate (%) - main finding
skin_lighter_flux = [47.3, 55.8, 76.6, 79.4, 78.8, 77.5, 79.8]
skin_lighter_step1x = [40.6, 51.0, 68.8, 70.4, 72.4, 67.5, 65.0]
skin_lighter_qwen = [45.4, 54.2, 70.8, 72.0, 73.8, 76.7, 77.5]

# Race Drift Rate (%) >= 3
race_drift_flux = [1.3, 9.6, 15.1, 15.1, 16.7, 17.9, 18.5]
race_drift_step1x = [0.0, 1.7, 3.8, 11.7, 15.1, 10.0, 14.2]
race_drift_qwen = [1.7, 5.4, 15.8, 14.2, 6.7, 12.1, 8.8]

# Create figure with 2 subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

x = np.arange(len(races))
width = 0.25

# Left: Skin Lightening
bars1 = ax1.bar(x - width, skin_lighter_flux, width, label='FLUX.2-dev', color='#e74c3c', alpha=0.85)
bars2 = ax1.bar(x, skin_lighter_step1x, width, label='Step1X-Edit', color='#3498db', alpha=0.85)
bars3 = ax1.bar(x + width, skin_lighter_qwen, width, label='Qwen-Edit', color='#2ecc71', alpha=0.85)

ax1.set_ylabel('Skin Lightening Rate (%)')
ax1.set_xlabel('Racial Group (Source Image)')
ax1.set_xticks(x)
ax1.set_xticklabels(races, rotation=15, ha='right')
ax1.legend(loc='upper left', fontsize=8)
ax1.set_ylim(0, 100)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.yaxis.grid(True, linestyle='--', alpha=0.3)
ax1.set_title('(a) Skin Lightening by Race', fontweight='bold')

# Add disparity annotation
ax1.axhline(y=47, color='gray', linestyle='--', alpha=0.5, linewidth=1)
ax1.text(5.5, 50, 'White baseline\n(47%)', fontsize=7, ha='center', color='gray')

# Right: Race Drift
bars4 = ax2.bar(x - width, race_drift_flux, width, label='FLUX.2-dev', color='#e74c3c', alpha=0.85)
bars5 = ax2.bar(x, race_drift_step1x, width, label='Step1X-Edit', color='#3498db', alpha=0.85)
bars6 = ax2.bar(x + width, race_drift_qwen, width, label='Qwen-Edit', color='#2ecc71', alpha=0.85)

ax2.set_ylabel('Race Drift Rate (score $\geq$ 3) (%)')
ax2.set_xlabel('Racial Group (Source Image)')
ax2.set_xticks(x)
ax2.set_xticklabels(races, rotation=15, ha='right')
ax2.legend(loc='upper left', fontsize=8)
ax2.set_ylim(0, 25)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
ax2.yaxis.grid(True, linestyle='--', alpha=0.3)
ax2.set_title('(b) Race Drift by Race', fontweight='bold')

# Add disparity annotation
ax2.axhline(y=1.3, color='gray', linestyle='--', alpha=0.5, linewidth=1)
ax2.text(5.5, 3, 'White baseline\n(1.3%)', fontsize=7, ha='center', color='gray')

plt.tight_layout()
plt.savefig(OUTPUT_DIR / "exp1_race_disparity.pdf", bbox_inches='tight')
plt.savefig(OUTPUT_DIR / "exp1_race_disparity.png", bbox_inches='tight', dpi=300)
print(f"Saved: {OUTPUT_DIR / 'exp1_race_disparity.pdf'}")
plt.close()


if __name__ == "__main__":
    print("Generating Experiment 1 race disparity figure with ALL 3 models...")
