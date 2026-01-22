#!/usr/bin/env python3
"""Generate Figure 6: human evaluation summary and VLM comparison."""

import json
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

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

OUTPUT_DIR = Path("paper/IJCAI__ECAI_26___I2I_Bias_Refusall/assets")


def load_json(path):
    with open(path) as f:
        return json.load(f)


def load_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f]


def mean(values):
    return float(np.mean(values)) if values else float("nan")


# Load data
vlm_full = load_jsonl("data/final/REAL_FINAL/exp1_vlm_scores_5040.jsonl")
sample_items = load_json("data/final/REAL_FINAL/500sample_edited_vlm_score_result.json")
human_baseline = load_json("data/final/REAL_FINAL/500sample_edited_human_survey_score_result.json")
human_preserved = load_json("data/final/REAL_FINAL/500sample_preserved_human_survey_score_result.json")

# Sample keys for the 500 baseline images
sample_keys = set()
for item in sample_items:
    filename = item["amt_item"]["filename"]
    image_id = filename.replace(".png", "")
    sample_keys.add((item["model"], image_id))

# VLM skin tone by race for the same 500 images
vlm_by_race = defaultdict(list)
for item in vlm_full:
    key = (item["model"], item["image_id"])
    if key not in sample_keys:
        continue
    scores = item.get("scores")
    if not scores:
        continue
    vlm_by_race[item["race"]].append(scores["skin_tone"])

# Human skin tone by race (average per item, then mean by race)
human_by_item = defaultdict(lambda: {"race": None, "scores": []})
for record in human_baseline:
    item_id = record["originalItemId"]
    human_by_item[item_id]["race"] = record["race"]
    human_by_item[item_id]["scores"].append(record["skin_tone"])

human_by_race = defaultdict(list)
for item_id, data in human_by_item.items():
    race = data["race"]
    if race and data["scores"]:
        human_by_race[race].append(np.mean(data["scores"]))

races = ["White", "EastAsian", "SoutheastAsian", "Latino", "MiddleEastern", "Indian", "Black"]
race_labels = ["White", "E Asian", "SE Asian", "Latino", "Mid East", "Indian", "Black"]

vlm_skin_means = [mean(vlm_by_race[r]) for r in races]
human_skin_means = [mean(human_by_race[r]) for r in races]

# Human preserved - baseline deltas (per item)
metrics = ["edit_success", "skin_tone", "race_drift", "gender_drift", "age_drift"]


def per_item_means(records):
    per_item = defaultdict(lambda: defaultdict(list))
    for record in records:
        item_id = record["originalItemId"]
        for metric in metrics:
            per_item[item_id][metric].append(record[metric])
    return {
        item_id: {metric: mean(values) for metric, values in metric_lists.items()}
        for item_id, metric_lists in per_item.items()
    }


baseline_means = per_item_means(human_baseline)
preserved_means = per_item_means(human_preserved)

deltas = defaultdict(list)
for item_id, base_scores in baseline_means.items():
    if item_id not in preserved_means:
        continue
    pres_scores = preserved_means[item_id]
    for metric in metrics:
        if metric in base_scores and metric in pres_scores:
            deltas[metric].append(pres_scores[metric] - base_scores[metric])

edit_delta = mean(deltas["edit_success"])
change_improvements = [
    -mean(deltas["skin_tone"]),
    -mean(deltas["race_drift"]),
    -mean(deltas["gender_drift"]),
    -mean(deltas["age_drift"]),
]

# Figure layout
fig = plt.figure(figsize=(9, 3.6))
gs = fig.add_gridspec(
    2,
    2,
    width_ratios=[1.6, 1.0],
    height_ratios=[1, 1],
    wspace=0.35,
    hspace=0.6,
)

ax1 = fig.add_subplot(gs[:, 0])
ax2 = fig.add_subplot(gs[0, 1])
ax3 = fig.add_subplot(gs[1, 1])

# (a) Skin Tone by Race
x = np.arange(len(races))
width = 0.35
ax1.bar(x - width / 2, human_skin_means, width, label="Human",
        color="#e74c3c", edgecolor="black", linewidth=0.5)
ax1.bar(x + width / 2, vlm_skin_means, width, label="VLM",
        color="#3498db", edgecolor="black", linewidth=0.5)

ax1.set_ylabel("Mean Skin Tone Score")
ax1.set_xlabel("Racial Group (Source Image)")
ax1.set_xticks(x)
ax1.set_xticklabels(race_labels, rotation=15, ha="right")
ax1.legend(loc="upper left", framealpha=0.9)
ax1.set_ylim(2.2, 4.4)
ax1.axhline(y=3.0, color="gray", linestyle="--", linewidth=1, alpha=0.7)
ax1.text(6.3, 3.05, "No change", fontsize=8, color="gray", ha="right")
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)
ax1.set_title("(a) Skin Tone by Race", fontweight="bold", fontsize=11)

# (b1) Edit Success change
ax2.bar([0], [edit_delta], color="#e74c3c", edgecolor="black", linewidth=0.5)
ax2.axhline(0, color="gray", linestyle="--", linewidth=1, alpha=0.7)
ax2.set_ylim(-0.55, 0.1)
ax2.set_xticks([0])
ax2.set_xticklabels(["Edit Success"], fontsize=9)
ax2.tick_params(axis="x", pad=2)
ax2.set_ylabel("Ours - Baseline", labelpad=2)
ax2.set_title("(b1) Edit Success", fontweight="bold", fontsize=11)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

# (b2) Change reduction (improvement = lower change)
labels = ["Skin\nTone", "Race\nChange", "Gender\nChange", "Age\nChange"]
x3 = np.arange(len(labels))
ax3.bar(x3, change_improvements, color="#2ecc71", edgecolor="black", linewidth=0.5)
ax3.axhline(0, color="gray", linestyle="--", linewidth=1, alpha=0.7)
ax3.set_xticks(x3)
ax3.set_xticklabels(labels)
ax3.set_ylabel("Change Reduction", labelpad=2)
ax3.set_title("(b2) Change Reduction", fontweight="bold", fontsize=11)
ax3.spines["top"].set_visible(False)
ax3.spines["right"].set_visible(False)

fig.subplots_adjust(left=0.06, right=0.98, top=0.92, bottom=0.18)
plt.savefig(OUTPUT_DIR / "vlm_human_validation.pdf", bbox_inches="tight")
plt.savefig(OUTPUT_DIR / "vlm_human_validation.png", bbox_inches="tight", dpi=300)
print(f"Saved: {OUTPUT_DIR / 'vlm_human_validation.pdf'}")
