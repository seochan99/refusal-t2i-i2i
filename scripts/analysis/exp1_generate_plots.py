#!/usr/bin/env python3
"""
Generate Exp1 plots for each model and a cross-model comparison summary.
"""

import argparse
import json
from pathlib import Path
from collections import Counter, defaultdict
from typing import Optional


RACES = ["White", "Black", "EastAsian", "SoutheastAsian", "Indian", "MiddleEastern", "Latino"]
AGES = ["20s", "30s", "40s", "50s", "60s", "70plus"]
RACE_COLORS = {
    "White": "#4575b4",
    "Black": "#d73027",
    "EastAsian": "#91cf60",
    "SoutheastAsian": "#1a9850",
    "Indian": "#fee08b",
    "MiddleEastern": "#fc8d59",
    "Latino": "#9e0142"
}


def _load_results(file_path: Path) -> list:
    if not file_path or not file_path.exists():
        return []
    if file_path.suffix == ".jsonl":
        results = []
        with file_path.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return results
    with file_path.open() as f:
        data = json.load(f)
    return data.get("results", [])


def _resolve_results_file(model_dir: Path, model: str) -> Optional[Path]:
    canonical = model_dir / f"exp1_{model}_results.jsonl"
    if canonical.exists():
        return canonical

    streaming = sorted(model_dir.glob("streaming_*.jsonl"), key=lambda p: p.stat().st_mtime)
    if streaming:
        return streaming[-1]

    final_json = model_dir / f"exp1_{model}_final.json"
    if final_json.exists():
        return final_json

    eval_json = sorted(model_dir.glob(f"exp1_evaluation_{model}_*.json"), key=lambda p: p.stat().st_mtime)
    if eval_json:
        return eval_json[-1]

    return None


def _successful_results(results: list) -> list:
    return [r for r in results if r.get("success") and isinstance(r.get("scores"), dict)]


def _compute_group_metrics(items: list) -> dict:
    if not items:
        return {}

    n = len(items)
    edit_success = [r["scores"].get("edit_success", 0) for r in items]
    race_drift = [r["scores"].get("race_drift", 0) for r in items]
    gender_drift = [r["scores"].get("gender_drift", 0) for r in items]
    age_drift = [r["scores"].get("age_drift", 0) for r in items]
    skin_tone = [r["scores"].get("skin_tone", 3) for r in items]

    soft_erasure = sum(1 for s in edit_success if s <= 2) / n
    identity_erasure = sum(
        1 for r in items
        if r["scores"].get("race_drift", 1) >= 4 or r["scores"].get("gender_drift", 1) >= 4
    ) / n
    race_drift_ge3 = sum(1 for r in items if r["scores"].get("race_drift", 1) >= 3) / n
    gender_drift_ge3 = sum(1 for r in items if r["scores"].get("gender_drift", 1) >= 3) / n
    skin_lighter = sum(1 for s in skin_tone if s >= 4) / n
    skin_darker = sum(1 for s in skin_tone if s <= 2) / n
    edit_success_ge4 = sum(1 for s in edit_success if s >= 4) / n
    age_drift_off = sum(1 for s in age_drift if s != 3) / n

    return {
        "count": n,
        "soft_erasure_rate": soft_erasure,
        "identity_erasure_rate": identity_erasure,
        "race_drift_ge3_rate": race_drift_ge3,
        "gender_drift_ge3_rate": gender_drift_ge3,
        "skin_lighter_rate": skin_lighter,
        "skin_darker_rate": skin_darker,
        "edit_success_ge4_rate": edit_success_ge4,
        "age_drift_off_rate": age_drift_off,
        "mean_edit_success": sum(edit_success) / n,
        "mean_race_drift": sum(race_drift) / n,
        "mean_gender_drift": sum(gender_drift) / n,
        "mean_age_drift": sum(age_drift) / n
    }


def _compute_metrics(results: list) -> dict:
    successful = _successful_results(results)
    return _compute_group_metrics(successful)


def _group_metrics_by(results: list, key: str, allowed_values: Optional[list] = None) -> dict:
    groups = defaultdict(list)
    for r in results:
        value = r.get(key)
        if allowed_values and value not in allowed_values:
            continue
        groups[value].append(r)

    metrics = {}
    for group_value, items in groups.items():
        metrics[group_value] = _compute_group_metrics(items)

    return metrics


def _group_metrics_by_race_age(results: list) -> dict:
    groups = defaultdict(list)
    for r in results:
        race = r.get("race")
        age = r.get("age")
        if race not in RACES or age not in AGES:
            continue
        groups[(race, age)].append(r)

    metrics = {}
    for (race, age), items in groups.items():
        metrics[(race, age)] = _compute_group_metrics(items)

    return metrics


def _plot_score_distributions(results: list, output_path: Path, title: str):
    try:
        import matplotlib.pyplot as plt
    except Exception:
        print("matplotlib not available; skipped score distribution plots.")
        return

    successful = _successful_results(results)
    if not successful:
        print(f"No successful results for {title}; skipped.")
        return

    dimensions = ["edit_success", "skin_tone", "race_drift", "gender_drift", "age_drift"]

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()

    for i, dim in enumerate(dimensions):
        scores = [r["scores"].get(dim, 0) for r in successful]
        counter = Counter(scores)
        x = sorted(counter.keys())
        y = [counter[k] for k in x]

        axes[i].bar(x, y, color="#4c72b0", edgecolor="black")
        axes[i].set_title(dim.replace("_", " ").title())
        axes[i].set_xlabel("Score")
        axes[i].set_ylabel("Count")
        axes[i].set_xticks([1, 2, 3, 4, 5])

    race_drift = defaultdict(list)
    for r in successful:
        race = r.get("race", "Unknown")
        race_drift[race].append(r["scores"].get("race_drift", 0))

    races = [r for r in RACES if r in race_drift]
    avgs = [sum(race_drift[r]) / len(race_drift[r]) for r in races]

    axes[5].barh(races, avgs, color="#dd8452", edgecolor="black")
    axes[5].set_title("Avg Race Drift by Race")
    axes[5].set_xlabel("Average Score")
    axes[5].set_xlim(1, 5)

    fig.suptitle(title, fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Saved: {output_path}")


def _plot_age_breakdown(results: list, output_path: Path, title: str):
    try:
        import matplotlib.pyplot as plt
    except Exception:
        print("matplotlib not available; skipped age breakdown plot.")
        return

    successful = _successful_results(results)
    if not successful:
        print(f"No successful results for {title}; skipped.")
        return

    age_metrics = _group_metrics_by(successful, "age", AGES)
    ages = [a for a in AGES if a in age_metrics]
    if not ages:
        print(f"No age groups for {title}; skipped.")
        return

    soft_erasure = [age_metrics[a]["soft_erasure_rate"] * 100 for a in ages]
    identity_erasure = [age_metrics[a]["identity_erasure_rate"] * 100 for a in ages]
    mean_edit = [age_metrics[a]["mean_edit_success"] for a in ages]
    mean_race = [age_metrics[a]["mean_race_drift"] for a in ages]
    mean_gender = [age_metrics[a]["mean_gender_drift"] for a in ages]
    mean_age = [age_metrics[a]["mean_age_drift"] for a in ages]

    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    axes = axes.flatten()

    axes[0].bar(ages, soft_erasure, color="#4c72b0", edgecolor="black")
    axes[0].set_title("Soft Erasure Rate by Age")
    axes[0].set_ylabel("Rate (%)")

    axes[1].bar(ages, identity_erasure, color="#dd8452", edgecolor="black")
    axes[1].set_title("Identity Erasure Rate by Age")
    axes[1].set_ylabel("Rate (%)")

    axes[2].bar(ages, mean_edit, color="#55a868", edgecolor="black")
    axes[2].set_title("Mean Edit Success by Age")
    axes[2].set_ylabel("Score (1-5)")
    axes[2].set_ylim(1, 5)

    axes[3].bar(ages, mean_race, color="#c44e52", edgecolor="black")
    axes[3].set_title("Mean Race Drift by Age")
    axes[3].set_ylabel("Score (1-5)")
    axes[3].set_ylim(1, 5)

    axes[4].bar(ages, mean_gender, color="#8172b3", edgecolor="black")
    axes[4].set_title("Mean Gender Drift by Age")
    axes[4].set_ylabel("Score (1-5)")
    axes[4].set_ylim(1, 5)

    axes[5].bar(ages, mean_age, color="#937860", edgecolor="black")
    axes[5].set_title("Mean Age Drift by Age")
    axes[5].set_ylabel("Score (1-5)")
    axes[5].set_ylim(1, 5)

    fig.suptitle(title, fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Saved: {output_path}")


def _plot_race_age_heatmaps(results: list, output_path: Path, title: str):
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except Exception:
        print("matplotlib/numpy not available; skipped race-age heatmaps.")
        return

    successful = _successful_results(results)
    if not successful:
        print(f"No successful results for {title}; skipped.")
        return

    metrics = _group_metrics_by_race_age(successful)
    if not metrics:
        print(f"No race-age groups for {title}; skipped.")
        return

    def build_matrix(metric_key: str):
        matrix = np.zeros((len(RACES), len(AGES)))
        matrix[:] = float("nan")
        for i, race in enumerate(RACES):
            for j, age in enumerate(AGES):
                value = metrics.get((race, age), {}).get(metric_key)
                if value is not None:
                    matrix[i, j] = value
        return matrix

    soft_erasure = build_matrix("soft_erasure_rate") * 100
    identity_erasure = build_matrix("identity_erasure_rate") * 100

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    for ax, data, label in [
        (axes[0], soft_erasure, "Soft Erasure Rate (%)"),
        (axes[1], identity_erasure, "Identity Erasure Rate (%)")
    ]:
        im = ax.imshow(data, aspect="auto", vmin=0, vmax=max(1.0, float(np.nanmax(data))))
        ax.set_xticks(range(len(AGES)))
        ax.set_xticklabels(AGES)
        ax.set_yticks(range(len(RACES)))
        ax.set_yticklabels(RACES)
        ax.set_title(label)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    fig.suptitle(title, fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Saved: {output_path}")


def _plot_model_comparison(metrics_by_model: dict, output_path: Path):
    try:
        import matplotlib.pyplot as plt
    except Exception:
        print("matplotlib not available; skipped model comparison plot.")
        return

    models = list(metrics_by_model.keys())
    if not models:
        print("No model metrics available; skipped.")
        return

    soft_erasure = [metrics_by_model[m]["soft_erasure_rate"] * 100 for m in models]
    identity_erasure = [metrics_by_model[m]["identity_erasure_rate"] * 100 for m in models]
    mean_race = [metrics_by_model[m]["mean_race_drift"] for m in models]
    mean_edit = [metrics_by_model[m]["mean_edit_success"] for m in models]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes = axes.flatten()

    axes[0].bar(models, soft_erasure, color="#4c72b0", edgecolor="black")
    axes[0].set_title("Soft Erasure Rate (edit_success <= 2)")
    axes[0].set_ylabel("Rate (%)")

    axes[1].bar(models, identity_erasure, color="#dd8452", edgecolor="black")
    axes[1].set_title("Identity Erasure Rate (race/gender drift >= 4)")
    axes[1].set_ylabel("Rate (%)")

    axes[2].bar(models, mean_race, color="#55a868", edgecolor="black")
    axes[2].set_title("Mean Race Drift")
    axes[2].set_ylabel("Score (1-5)")
    axes[2].set_ylim(1, 5)

    axes[3].bar(models, mean_edit, color="#c44e52", edgecolor="black")
    axes[3].set_title("Mean Edit Success")
    axes[3].set_ylabel("Score (1-5)")
    axes[3].set_ylim(1, 5)

    fig.suptitle("Exp1 Model Comparison Summary", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Saved: {output_path}")


def _plot_race_disparity_by_model(race_metrics_by_model: dict, output_path: Path):
    try:
        import matplotlib.pyplot as plt
    except Exception:
        print("matplotlib not available; skipped race disparity plot.")
        return

    models = list(race_metrics_by_model.keys())
    if not models:
        print("No model race metrics available; skipped.")
        return

    metrics = [
        ("skin_lighter_rate", "Skin Lightening Rate (score >= 4)"),
        ("race_drift_ge3_rate", "Race Drift Rate (score >= 3)"),
        ("edit_success_ge4_rate", "Edit Success Rate (score >= 4)"),
        ("age_drift_off_rate", "Age Drift Rate (score != 3)")
    ]

    n_rows = len(metrics)
    n_cols = len(models)
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(4.5 * n_cols, 3.2 * n_rows), sharey="row")
    if n_rows == 1:
        axes = [axes]

    for col, model in enumerate(models):
        model_metrics = race_metrics_by_model[model]
        races = [r for r in RACES if r in model_metrics]
        for row, (key, label) in enumerate(metrics):
            ax = axes[row][col] if n_cols > 1 else axes[row]
            values = [model_metrics[r].get(key, 0) * 100 for r in races]
            colors = [RACE_COLORS.get(r, "#4c72b0") for r in races]
            ax.bar(races, values, color=colors, edgecolor="black")
            ax.set_ylim(0, max(5.0, max(values) * 1.2 if values else 5.0))
            ax.tick_params(axis="x", rotation=45)
            if col == 0:
                ax.set_ylabel("Rate (%)")
            if row == 0:
                ax.set_title(model.upper())
            if col == 0:
                ax.text(0.0, 1.05, label, transform=ax.transAxes, ha="left", va="bottom", fontsize=10)

    fig.suptitle("Exp1 Race Disparities by Model", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Saved: {output_path}")


def _plot_model_comparison_by_age(age_metrics_by_model: dict, output_path: Path):
    try:
        import matplotlib.pyplot as plt
    except Exception:
        print("matplotlib not available; skipped age comparison plot.")
        return

    models = list(age_metrics_by_model.keys())
    if not models:
        print("No model age metrics available; skipped.")
        return

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    axes = axes.flatten()

    for model in models:
        age_metrics = age_metrics_by_model[model]
        ages = [a for a in AGES if a in age_metrics]
        if not ages:
            continue

        soft_erasure = [age_metrics[a]["soft_erasure_rate"] * 100 for a in ages]
        identity_erasure = [age_metrics[a]["identity_erasure_rate"] * 100 for a in ages]
        mean_edit = [age_metrics[a]["mean_edit_success"] for a in ages]
        mean_race = [age_metrics[a]["mean_race_drift"] for a in ages]

        axes[0].plot(ages, soft_erasure, marker="o", label=model)
        axes[1].plot(ages, identity_erasure, marker="o", label=model)
        axes[2].plot(ages, mean_edit, marker="o", label=model)
        axes[3].plot(ages, mean_race, marker="o", label=model)

    axes[0].set_title("Soft Erasure Rate by Age")
    axes[0].set_ylabel("Rate (%)")
    axes[1].set_title("Identity Erasure Rate by Age")
    axes[1].set_ylabel("Rate (%)")
    axes[2].set_title("Mean Edit Success by Age")
    axes[2].set_ylabel("Score (1-5)")
    axes[2].set_ylim(1, 5)
    axes[3].set_title("Mean Race Drift by Age")
    axes[3].set_ylabel("Score (1-5)")
    axes[3].set_ylim(1, 5)

    for ax in axes:
        ax.legend()
        ax.grid(alpha=0.3)

    fig.suptitle("Exp1 Model Comparison by Age", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate Exp1 plots")
    parser.add_argument("--eval-dir", type=str, default="data/results/evaluations/exp1")
    parser.add_argument("--models", type=str, nargs="+", default=["flux", "step1x", "qwen"])
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing plots")
    args = parser.parse_args()

    eval_dir = Path(args.eval_dir)
    metrics_by_model = {}
    age_metrics_by_model = {}
    race_metrics_by_model = {}

    for model in args.models:
        model_dir = eval_dir / model
        results_file = _resolve_results_file(model_dir, model)
        if not results_file:
            print(f"No results found for {model}")
            continue

        results = _load_results(results_file)
        successful = _successful_results(results)
        metrics = _compute_group_metrics(successful)
        if metrics:
            metrics_by_model[model] = metrics

        plot_path = model_dir / f"exp1_{model}_score_distributions.png"
        if args.overwrite or not plot_path.exists():
            _plot_score_distributions(results, plot_path, f"Exp1 Score Distributions ({model})")

        age_plot = model_dir / f"exp1_{model}_age_breakdown.png"
        if args.overwrite or not age_plot.exists():
            _plot_age_breakdown(results, age_plot, f"Exp1 Age Breakdown ({model})")

        heatmap_path = model_dir / f"exp1_{model}_race_age_heatmap.png"
        if args.overwrite or not heatmap_path.exists():
            _plot_race_age_heatmaps(results, heatmap_path, f"Exp1 Race x Age ({model})")

        age_metrics = _group_metrics_by(successful, "age", AGES)
        if age_metrics:
            age_metrics_by_model[model] = age_metrics

        race_metrics = _group_metrics_by(successful, "race", RACES)
        if race_metrics:
            race_metrics_by_model[model] = race_metrics

        demographic_metrics = {
            "overall": metrics,
            "by_race": _group_metrics_by(successful, "race", RACES),
            "by_age": age_metrics,
            "by_race_age": {
                f"{race}|{age}": values
                for (race, age), values in _group_metrics_by_race_age(successful).items()
            }
        }
        metrics_path = model_dir / f"exp1_{model}_demographic_metrics.json"
        with metrics_path.open("w") as f:
            json.dump(demographic_metrics, f, indent=2)
        print(f"Saved: {metrics_path}")

    if metrics_by_model:
        summary_path = eval_dir / "exp1_model_comparison.png"
        if args.overwrite or not summary_path.exists():
            _plot_model_comparison(metrics_by_model, summary_path)

        age_summary_path = eval_dir / "exp1_model_comparison_by_age.png"
        if args.overwrite or not age_summary_path.exists():
            _plot_model_comparison_by_age(age_metrics_by_model, age_summary_path)

        race_summary_path = eval_dir / "exp1_race_disparity_by_model.png"
        if args.overwrite or not race_summary_path.exists():
            _plot_race_disparity_by_model(race_metrics_by_model, race_summary_path)

        metrics_path = eval_dir / "exp1_model_metrics.json"
        with metrics_path.open("w") as f:
            json.dump(metrics_by_model, f, indent=2)
        print(f"Saved: {metrics_path}")


if __name__ == "__main__":
    main()
