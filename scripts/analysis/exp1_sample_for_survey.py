#!/usr/bin/env python3
"""
Create balanced Exp1 samples for human survey.

Strategy (per model):
- Stratify by race x gender x age (84 cells)
- Sample 5 per cell (default) -> 420 per model
- Enforce B/D balance (2+2+1) and priority mix (HIGH/MEDIUM with LOW fallback)
"""

import argparse
import json
import random
from pathlib import Path
from collections import defaultdict, Counter
from typing import Optional, List, Dict


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = PROJECT_ROOT / "data" / "results" / "evaluations" / "exp1"
OUTPUT_DIR = EVAL_DIR / "sampling_for_survey"

RACES = ["White", "Black", "EastAsian", "SoutheastAsian", "Indian", "MiddleEastern", "Latino"]
GENDERS = ["Male", "Female"]
AGES = ["20s", "30s", "40s", "50s", "60s", "70plus"]


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
    final_jsonl = model_dir / "final.jsonl"
    if final_jsonl.exists():
        return final_jsonl
    streaming = sorted(model_dir.glob("streaming_*.jsonl"), key=lambda p: p.stat().st_mtime)
    if streaming:
        return streaming[-1]
    eval_json = sorted(model_dir.glob(f"exp1_evaluation_{model}_*.json"), key=lambda p: p.stat().st_mtime)
    if eval_json:
        return eval_json[-1]
    return None


def _compute_priority(item: Dict) -> str:
    scores = item.get("scores", {})
    if not isinstance(scores, dict):
        return "LOW"

    if scores.get("edit_success", 5) <= 2:
        return "HIGH"
    if scores.get("race_drift", 1) >= 4 or scores.get("gender_drift", 1) >= 4:
        return "HIGH"

    if scores.get("race_drift", 1) == 3 or scores.get("gender_drift", 1) == 3:
        return "MEDIUM"
    if scores.get("skin_tone", 3) != 3:
        return "MEDIUM"

    return "LOW"


def _category_group(category: str) -> str:
    if category.startswith("B"):
        return "B"
    if category.startswith("D"):
        return "D"
    return "OTHER"


def _pick_one(items: List[Dict], priority_order: List[str], rng: random.Random) -> Optional[Dict]:
    if not items:
        return None
    for prio in priority_order:
        idxs = [i for i, it in enumerate(items) if it.get("_priority") == prio]
        if idxs:
            idx = rng.choice(idxs)
            return items.pop(idx)
    idx = rng.randrange(len(items))
    return items.pop(idx)


def _sample_cell(items: List[Dict], per_cell: int, rng: random.Random) -> List[Dict]:
    if len(items) <= per_cell:
        return items

    selected = []
    remaining = items[:]

    # Split by category
    cat_items = {
        "B": [it for it in remaining if it.get("_cat_group") == "B"],
        "D": [it for it in remaining if it.get("_cat_group") == "D"],
    }

    # For B and D, pick 2 each with priority preference
    for cat in ["B", "D"]:
        pool = cat_items.get(cat, [])[:]
        pick1 = _pick_one(pool, ["HIGH", "MEDIUM", "LOW"], rng)
        if pick1:
            selected.append(pick1)
        pick2 = _pick_one(pool, ["MEDIUM", "HIGH", "LOW"], rng)
        if pick2:
            selected.append(pick2)

        # remove picked from remaining
        picked_ids = {it["image_id"] for it in selected}
        remaining = [it for it in remaining if it["image_id"] not in picked_ids]

    # Remainder pick: prefer LOW to ensure baseline coverage
    if len(selected) < per_cell and remaining:
        pick3 = _pick_one(remaining, ["LOW", "MEDIUM", "HIGH"], rng)
        if pick3:
            selected.append(pick3)

    # Fill any leftover slots randomly from remaining
    while len(selected) < per_cell and remaining:
        selected.append(remaining.pop(rng.randrange(len(remaining))))

    return selected


def _summarize(selected: List[Dict]) -> Dict:
    counts = {
        "total": len(selected),
        "by_race": Counter(),
        "by_gender": Counter(),
        "by_age": Counter(),
        "by_category": Counter(),
        "by_priority": Counter()
    }
    for it in selected:
        counts["by_race"][it.get("race", "Unknown")] += 1
        counts["by_gender"][it.get("gender", "Unknown")] += 1
        counts["by_age"][it.get("age", "Unknown")] += 1
        counts["by_category"][it.get("_cat_group", "OTHER")] += 1
        counts["by_priority"][it.get("_priority", "LOW")] += 1

    counts["by_race"] = dict(counts["by_race"])
    counts["by_gender"] = dict(counts["by_gender"])
    counts["by_age"] = dict(counts["by_age"])
    counts["by_category"] = dict(counts["by_category"])
    counts["by_priority"] = dict(counts["by_priority"])
    return counts


def sample_model(model: str, per_cell: int, seed: int) -> Dict:
    model_dir = EVAL_DIR / model
    results_path = _resolve_results_file(model_dir, model)
    if not results_path:
        raise FileNotFoundError(f"No results file found for {model}")

    results = _load_results(results_path)
    successful = [r for r in results if r.get("success") and isinstance(r.get("scores"), dict)]
    if not successful:
        raise ValueError(f"No successful results for {model}")

    for it in successful:
        it["_priority"] = it.get("human_eval_priority") or _compute_priority(it)
        it["_cat_group"] = _category_group(it.get("category", ""))

    rng = random.Random(seed)
    selected = []

    # Stratify by race x gender x age
    for race in RACES:
        for gender in GENDERS:
            for age in AGES:
                cell_items = [
                    it for it in successful
                    if it.get("race") == race and it.get("gender") == gender and it.get("age") == age
                ]
                sampled = _sample_cell(cell_items, per_cell, rng)
                selected.extend(sampled)

    summary = _summarize(selected)
    return {
        "model": model,
        "seed": seed,
        "per_cell": per_cell,
        "total_cells": len(RACES) * len(GENDERS) * len(AGES),
        "summary": summary,
        "results": selected
    }


def main():
    parser = argparse.ArgumentParser(description="Sample Exp1 results for survey")
    parser.add_argument("--models", type=str, nargs="+", default=["flux", "step1x", "qwen"])
    parser.add_argument("--per-cell", type=int, default=5)
    parser.add_argument("--seed", type=int, default=13)
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_models_summary = {}

    for model in args.models:
        payload = sample_model(model, args.per_cell, args.seed)
        json_path = OUTPUT_DIR / f"exp1_{model}_sampling_for_survey.json"
        jsonl_path = OUTPUT_DIR / f"exp1_{model}_sampling_for_survey.jsonl"

        with json_path.open("w") as f:
            json.dump(payload, f, indent=2)

        with jsonl_path.open("w") as f:
            for item in payload["results"]:
                f.write(json.dumps(item) + "\n")

        all_models_summary[model] = payload["summary"]

    summary_path = OUTPUT_DIR / "sampling_for_survey_summary.json"
    with summary_path.open("w") as f:
        json.dump({
            "per_cell": args.per_cell,
            "seed": args.seed,
            "models": all_models_summary
        }, f, indent=2)


if __name__ == "__main__":
    main()
