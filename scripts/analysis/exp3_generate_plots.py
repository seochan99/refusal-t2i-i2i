#!/usr/bin/env python3
"""
Generate Exp3 plots (stereotype followed/resisted) across models.
"""

import argparse
import json
from pathlib import Path
from typing import Optional


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = PROJECT_ROOT / "data" / "results" / "evaluations" / "exp3"


def _latest_file(folder: Path, pattern: str) -> Optional[Path]:
    files = list(folder.glob(pattern))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def _load_stats(model: str) -> dict:
    model_dir = EVAL_DIR / model
    if not model_dir.exists():
        return {}

    latest = _latest_file(model_dir, f"exp3_evaluation_{model}_*.json")
    if not latest:
        return {}

    with latest.open() as f:
        data = json.load(f)
    return data.get("stats", {})


def _plot_exp3_summary(stats_by_model: dict, output_path: Path):
    try:
        import matplotlib.pyplot as plt
    except Exception:
        print("matplotlib not available; skipped exp3 plot.")
        return

    models = list(stats_by_model.keys())
    if not models:
        print("No exp3 stats found; skipped.")
        return

    followed = []
    resisted = []
    totals = []
    agreement = []
    disagreement = []

    for model in models:
        stats = stats_by_model[model]
        analysis = stats.get("stereotype_analysis", {})
        vlm = stats.get("vlm_stats", {})
        f = analysis.get("followed", 0)
        r = analysis.get("resisted", 0)
        followed.append(f)
        resisted.append(r)
        totals.append(f + r)
        agreement.append(vlm.get("ensemble_agreement", 0))
        disagreement.append(vlm.get("ensemble_disagreement", 0))

    def safe_rate(values, totals_list):
        return [v / t * 100 if t else 0 for v, t in zip(values, totals_list)]

    follow_rate = safe_rate(followed, totals)
    resist_rate = safe_rate(resisted, totals)
    agree_rate = safe_rate(agreement, [a + d for a, d in zip(agreement, disagreement)])
    disagree_rate = safe_rate(disagreement, [a + d for a, d in zip(agreement, disagreement)])

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))

    x = list(range(len(models)))

    # Left: stereotype outcomes
    axes[0].bar(x, follow_rate, label="Followed", color="#4c72b0", edgecolor="black")
    axes[0].bar(x, resist_rate, bottom=follow_rate, label="Resisted", color="#dd8452", edgecolor="black")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels([m.upper() for m in models])
    axes[0].set_ylabel("Rate (%)")
    axes[0].set_title("Stereotype Outcomes (Exp3)")
    axes[0].set_ylim(0, 100)
    axes[0].legend()

    for i, total in enumerate(totals):
        axes[0].text(i, 102, f"n={total}", ha="center", va="bottom", fontsize=9)

    # Right: ensemble agreement
    axes[1].bar(x, agree_rate, label="Agreement", color="#55a868", edgecolor="black")
    axes[1].bar(x, disagree_rate, bottom=agree_rate, label="Disagreement", color="#c44e52", edgecolor="black")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels([m.upper() for m in models])
    axes[1].set_ylabel("Rate (%)")
    axes[1].set_title("Ensemble Agreement")
    axes[1].set_ylim(0, 100)
    axes[1].legend()

    fig.suptitle("Exp3: WinoBias Stereotype Evaluation", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate Exp3 plots")
    parser.add_argument("--models", type=str, nargs="+", default=["flux", "qwen"])
    parser.add_argument("--output", type=str, default="data/results/evaluations/exp3/exp3_stereotype_summary.png")
    args = parser.parse_args()

    stats_by_model = {}
    for model in args.models:
        stats = _load_stats(model)
        if stats:
            stats_by_model[model] = stats

    output_path = PROJECT_ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _plot_exp3_summary(stats_by_model, output_path)


if __name__ == "__main__":
    main()
