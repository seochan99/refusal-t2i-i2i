#!/usr/bin/env python3
"""Generate VLM-Human Agreement Figure with Statistical Tests."""

import json
import numpy as np
from scipy import stats
from collections import defaultdict
import matplotlib.pyplot as plt

# Set publication style
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.dpi': 300,
})

# Load data
with open('data/final/REAL_FINAL/500sample_edited_vlm_score_result.json') as f:
    vlm_edited = json.load(f)
with open('data/final/REAL_FINAL/500sample_edited_human_survey_score_result.json') as f:
    human_edited = json.load(f)

# Build lookups
vlm_lookup = {}
for item in vlm_edited:
    item_id = item['amt_item']['id']
    vlm_lookup[item_id] = {
        'scores': item['vlm_scores'],
        'race': item['amt_item']['race']
    }

human_by_item = defaultdict(lambda: {'scores': defaultdict(list), 'race': None})
for record in human_edited:
    item_id = record['originalItemId']
    human_by_item[item_id]['race'] = record['race']
    for dim in ['edit_success', 'skin_tone', 'race_drift', 'gender_drift', 'age_drift']:
        if dim in record:
            human_by_item[item_id]['scores'][dim].append(record[dim])

# Calculate statistics
dimensions = ['skin_tone', 'race_drift', 'gender_drift', 'age_drift', 'edit_success']
dim_labels = ['Skin\nTone', 'Race\nChange', 'Gender\nChange', 'Age\nChange', 'Edit\nSuccess']

within1_rates = []
spearman_rhos = []
spearman_ps = []

for dim in dimensions:
    vlm_scores = []
    human_scores = []

    for item_id in vlm_lookup:
        if item_id not in human_by_item:
            continue
        vlm_s = vlm_lookup[item_id]['scores'].get(dim)
        human_s = human_by_item[item_id]['scores'].get(dim)
        if vlm_s is not None and human_s:
            vlm_scores.append(vlm_s)
            human_scores.append(np.mean(human_s))

    vlm_arr = np.array(vlm_scores)
    human_arr = np.array(human_scores)

    # Within-1 agreement
    within1 = np.mean(np.abs(vlm_arr - human_arr) <= 1) * 100
    within1_rates.append(within1)

    # Spearman correlation
    rho, p = stats.spearmanr(vlm_arr, human_arr)
    spearman_rhos.append(rho)
    spearman_ps.append(p)

# Create figure
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3.5))

# Panel (a): Within-1 Agreement
colors = ['#3498db'] * 5
bars1 = ax1.bar(dim_labels, within1_rates, color=colors, edgecolor='black', linewidth=0.5)

for bar, val in zip(bars1, within1_rates):
    ax1.text(bar.get_x() + bar.get_width()/2, val + 1,
            f'{val:.1f}%', ha='center', va='bottom', fontsize=9)

ax1.set_ylim(0, 100)
ax1.set_ylabel('Within-1 Agreement (%)')
ax1.set_title('(a) VLM-Human Agreement Rate', fontweight='bold', fontsize=11)
ax1.axhline(y=80, color='gray', linestyle='--', linewidth=1, alpha=0.7)
ax1.text(4.5, 82, '80%', fontsize=8, color='gray')
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)

# Panel (b): Spearman Correlation
colors2 = ['#e74c3c' if p < 0.05 else '#95a5a6' for p in spearman_ps]
bars2 = ax2.bar(dim_labels, spearman_rhos, color=colors2, edgecolor='black', linewidth=0.5)

for bar, rho, p in zip(bars2, spearman_rhos, spearman_ps):
    sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else ''
    ax2.text(bar.get_x() + bar.get_width()/2, rho + 0.02,
            f'{rho:.2f}{sig}', ha='center', va='bottom', fontsize=8)

ax2.set_ylim(0, 0.5)
ax2.set_ylabel('Spearman ρ')
ax2.set_title('(b) VLM-Human Correlation', fontweight='bold', fontsize=11)
ax2.axhline(y=0.3, color='gray', linestyle='--', linewidth=1, alpha=0.7)
ax2.text(4.5, 0.31, 'ρ=0.3', fontsize=8, color='gray')
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)

# Add legend for significance
ax2.text(0.02, 0.95, '* p<0.05  ** p<0.01  *** p<0.001',
         transform=ax2.transAxes, fontsize=7, color='gray')

plt.tight_layout()

# Save
output_dir = 'paper/IJCAI__ECAI_26___I2I_Bias_Refusall/assets'
plt.savefig(f'{output_dir}/vlm_human_agreement_stats.pdf', bbox_inches='tight', dpi=300)
plt.savefig(f'{output_dir}/vlm_human_agreement_stats.png', bbox_inches='tight', dpi=300)

print("Saved figure to:", output_dir)
print("\nStatistics for paper:")
print(f"Within-1 Agreement: {np.mean(within1_rates):.1f}% (range: {min(within1_rates):.1f}%-{max(within1_rates):.1f}%)")
print(f"Spearman ρ range: {min(spearman_rhos):.2f}-{max(spearman_rhos):.2f}")

for dim, w1, rho, p in zip(dim_labels, within1_rates, spearman_rhos, spearman_ps):
    sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else 'ns'
    print(f"  {dim.replace(chr(10), ' ')}: Within-1={w1:.1f}%, ρ={rho:.2f} ({sig})")
