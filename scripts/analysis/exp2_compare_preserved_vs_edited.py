#!/usr/bin/env python3
"""
Compare Exp1 (edited) vs Exp2 (preserved) for the same prompts and subjects.
Generates a summary figure and JSON with improvements (preserved better -> positive).
"""

import argparse
import json
from pathlib import Path
from collections import defaultdict
from typing import Optional, Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXP1_DIR = PROJECT_ROOT / "data" / "results" / "evaluations" / "exp1"
EXP2_DIR = PROJECT_ROOT / "data" / "results" / "evaluations" / "exp2"

TARGET_PROMPTS = {"B01", "B05", "B09", "D03"}
RACES = ["White", "Black", "EastAsian", "SoutheastAsian", "Indian", "MiddleEastern", "Latino"]


def _load_jsonl(path: Path) -> List[Dict]:
    results = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return results


def _load_json_results(path: Path) -> List[Dict]:
    with path.open() as f:
        data = json.load(f)
    return data.get("results", [])


def _resolve_exp1_file(model: str) -> Optional[Path]:
    model_dir = EXP1_DIR / model
    candidate = model_dir / f"exp1_{model}_results.jsonl"
    if candidate.exists():
        return candidate
    candidate = model_dir / "final.jsonl"
    if candidate.exists():
        return candidate
    streaming = sorted(model_dir.glob("streaming_*.jsonl"), key=lambda p: p.stat().st_mtime)
    if streaming:
        return streaming[-1]
    return None


def _load_exp1(model: str) -> Dict[str, Dict]:
    path = _resolve_exp1_file(model)
    if not path:
        return {}
    results = _load_jsonl(path)
    records = {}
    for r in results:
        if not r.get("success") or not isinstance(r.get("scores"), dict):
            continue
        if r.get("prompt_id") not in TARGET_PROMPTS:
            continue
        key = f"{r.get('prompt_id')}_{r.get('race')}_{r.get('gender')}_{r.get('age')}"
        records[key] = r
    return records


def _load_exp2(model: str) -> Dict[str, Dict]:
    model_dir = EXP2_DIR / model
    if not model_dir.exists():
        return {}

    records = {}

    # Streaming JSONL files
    for jsonl in sorted(model_dir.glob("streaming_*.jsonl"), key=lambda p: p.stat().st_mtime):
        for r in _load_jsonl(jsonl):
            if not r.get("success") or not isinstance(r.get("scores"), dict):
                continue
            key = f"{r.get('prompt_id')}_{r.get('race')}_{r.get('gender')}_{r.get('age')}"
            records[key] = r

    # Final JSON files (may include last missing items)
    for json_path in sorted(model_dir.glob("exp2_evaluation_*.json"), key=lambda p: p.stat().st_mtime):
        for r in _load_json_results(json_path):
            if not r.get("success") or not isinstance(r.get("scores"), dict):
                continue
            key = f"{r.get('prompt_id')}_{r.get('race')}_{r.get('gender')}_{r.get('age')}"
            records[key] = r

    return records


def _skin_shift(score: int) -> float:
    return abs(score - 3)


def _age_shift(score: int) -> float:
    return abs(score - 3)


def _compute_improvements(exp1: Dict[str, Dict], exp2: Dict[str, Dict]):
    keys = sorted(set(exp1.keys()) & set(exp2.keys()))
    if not keys:
        return {}, {}

    overall = defaultdict(list)
    by_race = defaultdict(lambda: defaultdict(list))

    for key in keys:
        r1 = exp1[key]["scores"]
        r2 = exp2[key]["scores"]
        race = exp1[key].get("race")

        # Positive = preserved better
        overall["edit_success"].append(r2["edit_success"] - r1["edit_success"])
        overall["race_drift"].append(r1["race_drift"] - r2["race_drift"])
        overall["gender_drift"].append(r1["gender_drift"] - r2["gender_drift"])
        overall["skin_shift"].append(_skin_shift(r1["skin_tone"]) - _skin_shift(r2["skin_tone"]))
        overall["age_shift"].append(_age_shift(r1["age_drift"]) - _age_shift(r2["age_drift"]))

        if race in RACES:
            by_race[race]["race_drift"].append(r1["race_drift"] - r2["race_drift"])
            by_race[race]["skin_shift"].append(_skin_shift(r1["skin_tone"]) - _skin_shift(r2["skin_tone"]))
            by_race[race]["age_shift"].append(_age_shift(r1["age_drift"]) - _age_shift(r2["age_drift"]))

    def mean(vals: List[float]) -> float:
        return sum(vals) / len(vals) if vals else 0.0

    overall_means = {k: mean(v) for k, v in overall.items()}
    race_means = {
        race: {k: mean(v) for k, v in metrics.items()}
        for race, metrics in by_race.items()
    }

    return overall_means, race_means


def _plot_summary(overall_means: dict, race_means: dict, output_path: Path, title: str):
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except Exception:
        print("matplotlib/numpy not available; skipped plot.")
        return

    metrics = [
        ("edit_success", "Edit Success (higher = better)"),
        ("race_drift", "Race Drift (lower = better)"),
        ("gender_drift", "Gender Drift (lower = better)"),
        ("skin_shift", "Skin Tone Shift (|score-3|)"),
        ("age_shift", "Age Drift (|score-3|)")
    ]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Panel A: overall improvement
    ax = axes[0, 0]
    vals = [overall_means.get(k, 0) for k, _ in metrics]
    labels = [m[0].replace("_", " ").title() for m in metrics]
    ax.bar(labels, vals, color="#4c72b0", edgecolor="black")
    ax.axhline(0, color="gray", linewidth=1)
    ax.set_title("Overall Improvement (Preserved - Edited)")
    ax.set_ylabel("Delta (positive = preserved better)")
    ax.tick_params(axis="x", rotation=30)

    # Panel B: race drift improvement by race
    ax = axes[0, 1]
    races = [r for r in RACES if r in race_means]
    vals = [race_means[r].get("race_drift", 0) for r in races]
    ax.bar(races, vals, color="#dd8452", edgecolor="black")
    ax.axhline(0, color="gray", linewidth=1)
    ax.set_title("Race Drift Improvement by Race")
    ax.set_ylabel("Delta (positive = preserved better)")
    ax.tick_params(axis="x", rotation=45)

    # Panel C: skin shift improvement by race
    ax = axes[1, 0]
    vals = [race_means[r].get("skin_shift", 0) for r in races]
    ax.bar(races, vals, color="#55a868", edgecolor="black")
    ax.axhline(0, color="gray", linewidth=1)
    ax.set_title("Skin Tone Shift Improvement by Race")
    ax.set_ylabel("Delta (positive = preserved better)")
    ax.tick_params(axis="x", rotation=45)

    # Panel D: age shift improvement by race
    ax = axes[1, 1]
    vals = [race_means[r].get("age_shift", 0) for r in races]
    ax.bar(races, vals, color="#8172b3", edgecolor="black")
    ax.axhline(0, color="gray", linewidth=1)
    ax.set_title("Age Drift Improvement by Race")
    ax.set_ylabel("Delta (positive = preserved better)")
    ax.tick_params(axis="x", rotation=45)

    fig.suptitle(title, fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Compare Exp1 vs Exp2 results")
    parser.add_argument("--model", type=str, default="flux", choices=["flux", "step1x", "qwen"])
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    exp1 = _load_exp1(args.model)
    exp2 = _load_exp2(args.model)

    overall_means, race_means = _compute_improvements(exp1, exp2)
    if not overall_means:
        print("No overlapping results found.")
        return

    output_dir = EXP2_DIR / args.model
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = Path(args.output) if args.output else output_dir / f"exp2_{args.model}_preserved_vs_edited.png"

    _plot_summary(overall_means, race_means, output_path, f"Exp2 Preserved vs Exp1 Edited ({args.model})")

    summary_path = output_dir / f"exp2_{args.model}_preserved_vs_edited_summary.json"
    with summary_path.open("w") as f:
        json.dump({
            "model": args.model,
            "overall_improvement": overall_means,
            "race_improvement": race_means,
            "n_overlap": len(set(exp1.keys()) & set(exp2.keys()))
        }, f, indent=2)
    print(f"Saved: {summary_path}")


if __name__ == "__main__":
    main()
