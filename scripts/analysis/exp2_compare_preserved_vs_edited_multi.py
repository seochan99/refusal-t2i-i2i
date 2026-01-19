#!/usr/bin/env python3
"""
Create a multi-model comparison figure for Exp2 (preserved vs edited).
Reads per-model summary JSONs produced by exp2_compare_preserved_vs_edited.py.
"""

import argparse
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXP2_DIR = PROJECT_ROOT / "data" / "results" / "evaluations" / "exp2"

RACES = ["White", "Black", "EastAsian", "SoutheastAsian", "Indian", "MiddleEastern", "Latino"]
MODEL_LABELS = {
    "flux": "Flux",
    "step1x": "Step1X",
    "qwen": "Qwen"
}
MODEL_COLORS = {
    "flux": "#4c72b0",
    "step1x": "#dd8452",
    "qwen": "#55a868"
}


def _load_summary(model: str) -> dict:
    summary_path = EXP2_DIR / model / f"exp2_{model}_preserved_vs_edited_summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"Missing summary: {summary_path}")
    with summary_path.open() as f:
        return json.load(f)


def _plot(models, summaries, output_path: Path):
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except Exception:
        print("matplotlib/numpy not available; skipped plot.")
        return

    metrics = [
        ("edit_success", "Edit Success"),
        ("race_drift", "Race Drift"),
        ("gender_drift", "Gender Drift"),
        ("skin_shift", "Skin Tone Shift"),
        ("age_shift", "Age Drift")
    ]

    fig, axes = plt.subplots(2, 2, figsize=(16, 11))

    # Panel A: Overall improvements by model
    ax = axes[0, 0]
    x = np.arange(len(metrics))
    width = 0.25
    for i, model in enumerate(models):
        vals = [summaries[model]["overall_improvement"].get(k, 0) for k, _ in metrics]
        ax.bar(
            x + (i - (len(models) - 1) / 2) * width,
            vals,
            width,
            label=MODEL_LABELS.get(model, model),
            color=MODEL_COLORS.get(model, "#4c72b0"),
            edgecolor="black"
        )
    ax.axhline(0, color="gray", linewidth=1)
    ax.set_xticks(x)
    ax.set_xticklabels([m[1] for m in metrics], rotation=25, ha="right")
    ax.set_title("Overall Improvement (Preserved - Edited)")
    ax.set_ylabel("Delta (positive = preserved better)")
    ax.legend(frameon=False)

    # Panel B: Race drift improvement by race
    ax = axes[0, 1]
    x = np.arange(len(RACES))
    for i, model in enumerate(models):
        vals = [summaries[model]["race_improvement"].get(r, {}).get("race_drift", 0) for r in RACES]
        ax.bar(
            x + (i - (len(models) - 1) / 2) * width,
            vals,
            width,
            label=MODEL_LABELS.get(model, model),
            color=MODEL_COLORS.get(model, "#4c72b0"),
            edgecolor="black"
        )
    ax.axhline(0, color="gray", linewidth=1)
    ax.set_xticks(x)
    ax.set_xticklabels(RACES, rotation=35, ha="right")
    ax.set_title("Race Drift Improvement by Race")
    ax.set_ylabel("Delta (positive = preserved better)")

    # Panel C: Skin shift improvement by race
    ax = axes[1, 0]
    x = np.arange(len(RACES))
    for i, model in enumerate(models):
        vals = [summaries[model]["race_improvement"].get(r, {}).get("skin_shift", 0) for r in RACES]
        ax.bar(
            x + (i - (len(models) - 1) / 2) * width,
            vals,
            width,
            label=MODEL_LABELS.get(model, model),
            color=MODEL_COLORS.get(model, "#4c72b0"),
            edgecolor="black"
        )
    ax.axhline(0, color="gray", linewidth=1)
    ax.set_xticks(x)
    ax.set_xticklabels(RACES, rotation=35, ha="right")
    ax.set_title("Skin Tone Shift Improvement by Race")
    ax.set_ylabel("Delta (positive = preserved better)")

    # Panel D: Age shift improvement by race
    ax = axes[1, 1]
    x = np.arange(len(RACES))
    for i, model in enumerate(models):
        vals = [summaries[model]["race_improvement"].get(r, {}).get("age_shift", 0) for r in RACES]
        ax.bar(
            x + (i - (len(models) - 1) / 2) * width,
            vals,
            width,
            label=MODEL_LABELS.get(model, model),
            color=MODEL_COLORS.get(model, "#4c72b0"),
            edgecolor="black"
        )
    ax.axhline(0, color="gray", linewidth=1)
    ax.set_xticks(x)
    ax.set_xticklabels(RACES, rotation=35, ha="right")
    ax.set_title("Age Drift Improvement by Race")
    ax.set_ylabel("Delta (positive = preserved better)")

    n_text = ", ".join(
        f"{MODEL_LABELS.get(m, m)} n={summaries[m].get('n_overlap', 'NA')}"
        for m in models
    )
    fig.suptitle("Exp2 Preserved vs Edited: Model Comparison", fontsize=14, fontweight="bold")
    fig.text(0.5, 0.02, n_text, ha="center", va="center", fontsize=10)

    plt.tight_layout(rect=[0, 0.04, 1, 0.95])
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Exp2 model comparison plot (preserved vs edited)")
    parser.add_argument("--models", nargs="+", default=["flux", "step1x", "qwen"])
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    models = args.models
    summaries = {m: _load_summary(m) for m in models}

    output_path = Path(args.output) if args.output else EXP2_DIR / "exp2_preserved_vs_edited_model_comparison.png"
    _plot(models, summaries, output_path)


if __name__ == "__main__":
    main()
