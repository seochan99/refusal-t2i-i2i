#!/usr/bin/env python3
"""
Quick analysis of Exp1 evaluation results.

Usage:
    python scripts/evaluation/exp1/quick_analysis.py
    python scripts/evaluation/exp1/quick_analysis.py --file path/to/checkpoint.json
"""

import json
import argparse
from pathlib import Path
from collections import Counter, defaultdict

# Try importing optional dependencies
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

def load_results(file_path: Path):
    """Load results from JSON or JSONL file."""
    results = []

    if file_path.suffix == ".jsonl":
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        results.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    else:
        with open(file_path, "r") as f:
            data = json.load(f)
            results = data.get("results", [])

    return results


def print_summary(results: list):
    """Print summary statistics."""
    successful = [r for r in results if r.get("success", False)]
    failed = [r for r in results if not r.get("success", False)]

    print("\n" + "="*60)
    print("EVALUATION SUMMARY")
    print("="*60)
    print(f"Total: {len(results)}")
    print(f"Successful: {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
    print(f"Failed: {len(failed)} ({len(failed)/len(results)*100:.1f}%)")

    if not successful:
        print("No successful results to analyze!")
        return

    # Score distributions
    print("\n" + "-"*60)
    print("SCORE DISTRIBUTIONS")
    print("-"*60)

    dimensions = ["edit_success", "skin_tone", "race_drift", "gender_drift", "age_drift"]

    for dim in dimensions:
        scores = [r["scores"].get(dim, 0) for r in successful if "scores" in r]
        if scores:
            counter = Counter(scores)
            avg = sum(scores) / len(scores)
            print(f"\n{dim}:")
            print(f"  Average: {avg:.2f}")
            for score in sorted(counter.keys()):
                pct = counter[score] / len(scores) * 100
                bar = "█" * int(pct / 2)
                print(f"  {score}: {counter[score]:4d} ({pct:5.1f}%) {bar}")

    # By race
    print("\n" + "-"*60)
    print("BY RACE")
    print("-"*60)

    race_stats = defaultdict(lambda: {"count": 0, "race_drift_high": 0, "edit_success_low": 0})
    for r in successful:
        race = r.get("race", "Unknown")
        race_stats[race]["count"] += 1
        if r.get("scores", {}).get("race_drift", 1) >= 4:
            race_stats[race]["race_drift_high"] += 1
        if r.get("scores", {}).get("edit_success", 5) <= 2:
            race_stats[race]["edit_success_low"] += 1

    print(f"\n{'Race':<15} {'Count':>6} {'Race Drift≥4':>12} {'Soft Erasure':>12}")
    print("-" * 50)
    for race in sorted(race_stats.keys()):
        stats = race_stats[race]
        drift_pct = stats["race_drift_high"] / stats["count"] * 100 if stats["count"] > 0 else 0
        erasure_pct = stats["edit_success_low"] / stats["count"] * 100 if stats["count"] > 0 else 0
        print(f"{race:<15} {stats['count']:>6} {drift_pct:>11.1f}% {erasure_pct:>11.1f}%")

    # By category
    print("\n" + "-"*60)
    print("BY CATEGORY")
    print("-"*60)

    cat_stats = defaultdict(lambda: {"count": 0, "scores": []})
    for r in successful:
        cat = r.get("category", "Unknown")
        cat_stats[cat]["count"] += 1
        if "scores" in r:
            cat_stats[cat]["scores"].append(r["scores"])

    print(f"\n{'Category':<20} {'Count':>6} {'Avg Edit':>10} {'Avg Race':>10}")
    print("-" * 50)
    for cat in sorted(cat_stats.keys()):
        stats = cat_stats[cat]
        if stats["scores"]:
            avg_edit = sum(s.get("edit_success", 0) for s in stats["scores"]) / len(stats["scores"])
            avg_race = sum(s.get("race_drift", 0) for s in stats["scores"]) / len(stats["scores"])
            print(f"{cat:<20} {stats['count']:>6} {avg_edit:>10.2f} {avg_race:>10.2f}")

    # Ensemble stats
    print("\n" + "-"*60)
    print("ENSEMBLE STATS")
    print("-"*60)

    ensemble_used = sum(1 for r in successful if r.get("ensemble", False))
    needs_review = sum(1 for r in successful if r.get("needs_review", False))

    print(f"Ensemble used: {ensemble_used}/{len(successful)} ({ensemble_used/len(successful)*100:.1f}%)")
    print(f"Needs review: {needs_review}/{len(successful)} ({needs_review/len(successful)*100:.1f}%)")

    # Human eval priority
    priority_counts = Counter(r.get("human_eval_priority", "Unknown") for r in successful)
    print(f"\nHuman Eval Priority:")
    for priority in ["HIGH", "MEDIUM", "LOW"]:
        count = priority_counts.get(priority, 0)
        pct = count / len(successful) * 100
        print(f"  {priority}: {count} ({pct:.1f}%)")


def plot_distributions(results: list, output_dir: Path):
    """Generate distribution plots."""
    if not HAS_MATPLOTLIB:
        print("\nMatplotlib not installed. Skipping plots.")
        print("Install with: pip install matplotlib")
        return

    successful = [r for r in results if r.get("success", False) and "scores" in r]
    if not successful:
        return

    dimensions = ["edit_success", "skin_tone", "race_drift", "gender_drift", "age_drift"]

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()

    for i, dim in enumerate(dimensions):
        scores = [r["scores"].get(dim, 0) for r in successful]
        counter = Counter(scores)

        x = sorted(counter.keys())
        y = [counter[k] for k in x]

        axes[i].bar(x, y, color='steelblue', edgecolor='black')
        axes[i].set_title(dim.replace("_", " ").title())
        axes[i].set_xlabel("Score")
        axes[i].set_ylabel("Count")
        axes[i].set_xticks([1, 2, 3, 4, 5])

    # Race drift by race
    race_drift = defaultdict(list)
    for r in successful:
        race = r.get("race", "Unknown")
        race_drift[race].append(r["scores"].get("race_drift", 0))

    races = sorted(race_drift.keys())
    avgs = [sum(race_drift[r])/len(race_drift[r]) for r in races]

    axes[5].barh(races, avgs, color='coral', edgecolor='black')
    axes[5].set_title("Avg Race Drift by Race")
    axes[5].set_xlabel("Average Score")
    axes[5].set_xlim(1, 5)

    plt.tight_layout()

    plot_file = output_dir / "score_distributions.png"
    plt.savefig(plot_file, dpi=150)
    print(f"\nPlot saved: {plot_file}")
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Quick analysis of evaluation results")
    parser.add_argument("--file", type=str, help="Path to checkpoint JSON or streaming JSONL")
    parser.add_argument("--no-plot", action="store_true", help="Skip plot generation")

    args = parser.parse_args()

    # Find latest results file
    if args.file:
        file_path = Path(args.file)
    else:
        eval_dir = Path("/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/data/results/evaluations/exp1/flux")

        # Try checkpoint first, then JSONL
        checkpoints = list(eval_dir.glob("checkpoint_*.json"))
        jsonl_files = list(eval_dir.glob("streaming_*.jsonl"))

        if checkpoints:
            file_path = max(checkpoints, key=lambda p: p.stat().st_mtime)
        elif jsonl_files:
            file_path = max(jsonl_files, key=lambda p: p.stat().st_mtime)
        else:
            print("No results files found!")
            return

    print(f"Loading: {file_path}")
    results = load_results(file_path)

    if not results:
        print("No results found!")
        return

    print_summary(results)

    if not args.no_plot:
        plot_distributions(results, file_path.parent)


if __name__ == "__main__":
    main()
