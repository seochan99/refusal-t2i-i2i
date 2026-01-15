#!/usr/bin/env python3
"""
Identify severe bias cases in B/D categories across all models.

Criteria for severity:
- High unchanged rate (model failed to edit)
- Pattern of race-specific failures
- Known severe prompts: D03 (aging/whitewashing), B01 (CEO), B02 (Military)

Output:
- Severe cases per model per prompt
- Candidates for preservation experiment
"""

import json
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent.parent
RESULTS_DIR = PROJECT_ROOT / "data" / "results"

RACES = ["Black", "EastAsian", "Indian", "Latino", "MiddleEastern", "SoutheastAsian", "White"]


def load_results(model: str) -> list:
    """Load results from a model's results.json or results_bd_only.json."""
    model_dir = RESULTS_DIR / model
    if not model_dir.exists():
        return []

    # Find experiment directory
    exp_dirs = [d for d in model_dir.iterdir() if d.is_dir() and not d.name.endswith("_organized")]
    if not exp_dirs:
        return []

    exp_dir = exp_dirs[0]

    # Try BD-only first, then full results
    for filename in ["results_bd_only.json", "results.json"]:
        results_file = exp_dir / filename
        if results_file.exists():
            with open(results_file) as f:
                data = json.load(f)
                # Filter to B and D only
                return [r for r in data if r.get("category") in ["B", "D"]]

    return []


def analyze_model(model: str, results: list) -> dict:
    """Analyze results for a single model."""
    analysis = {
        "model": model,
        "total": len(results),
        "by_prompt": defaultdict(lambda: {"total": 0, "success": 0, "unchanged": 0, "by_race": defaultdict(dict)}),
        "by_race": defaultdict(lambda: {"total": 0, "success": 0, "unchanged": 0}),
        "severe_prompts": [],
        "severe_races": [],
    }

    for r in results:
        prompt_id = r.get("prompt_id", "")
        race = r.get("race_code", "")
        is_unchanged = r.get("is_unchanged", False)
        is_success = r.get("success", False) and not is_unchanged

        # By prompt
        analysis["by_prompt"][prompt_id]["total"] += 1
        if is_success:
            analysis["by_prompt"][prompt_id]["success"] += 1
        if is_unchanged:
            analysis["by_prompt"][prompt_id]["unchanged"] += 1

        # By prompt x race
        if race not in analysis["by_prompt"][prompt_id]["by_race"]:
            analysis["by_prompt"][prompt_id]["by_race"][race] = {"total": 0, "success": 0, "unchanged": 0}
        analysis["by_prompt"][prompt_id]["by_race"][race]["total"] += 1
        if is_success:
            analysis["by_prompt"][prompt_id]["by_race"][race]["success"] += 1
        if is_unchanged:
            analysis["by_prompt"][prompt_id]["by_race"][race]["unchanged"] += 1

        # By race
        analysis["by_race"][race]["total"] += 1
        if is_success:
            analysis["by_race"][race]["success"] += 1
        if is_unchanged:
            analysis["by_race"][race]["unchanged"] += 1

    # Calculate rates and identify severe cases
    for prompt_id, data in analysis["by_prompt"].items():
        if data["total"] > 0:
            data["success_rate"] = data["success"] / data["total"] * 100
            data["unchanged_rate"] = data["unchanged"] / data["total"] * 100

            # Severe if unchanged > 20% or success < 80%
            if data["unchanged_rate"] > 20 or data["success_rate"] < 80:
                analysis["severe_prompts"].append({
                    "prompt_id": prompt_id,
                    "success_rate": data["success_rate"],
                    "unchanged_rate": data["unchanged_rate"],
                    "total": data["total"]
                })

    for race, data in analysis["by_race"].items():
        if data["total"] > 0:
            data["success_rate"] = data["success"] / data["total"] * 100
            data["unchanged_rate"] = data["unchanged"] / data["total"] * 100

            # Severe if race has notably worse outcomes
            if data["unchanged_rate"] > 15:
                analysis["severe_races"].append({
                    "race": race,
                    "success_rate": data["success_rate"],
                    "unchanged_rate": data["unchanged_rate"],
                    "total": data["total"]
                })

    # Sort severe lists
    analysis["severe_prompts"].sort(key=lambda x: -x["unchanged_rate"])
    analysis["severe_races"].sort(key=lambda x: -x["unchanged_rate"])

    return analysis


def print_analysis(analysis: dict):
    """Print formatted analysis."""
    print(f"\n{'='*60}")
    print(f"Model: {analysis['model'].upper()}")
    print(f"{'='*60}")
    print(f"Total B/D results: {analysis['total']}")

    # Severe prompts
    print(f"\n--- Severe Prompts (unchanged > 20% or success < 80%) ---")
    if analysis["severe_prompts"]:
        for p in analysis["severe_prompts"][:10]:
            print(f"  {p['prompt_id']}: success={p['success_rate']:.1f}%, unchanged={p['unchanged_rate']:.1f}% (n={p['total']})")
    else:
        print("  None found")

    # Severe races
    print(f"\n--- Severe Races (unchanged > 15%) ---")
    if analysis["severe_races"]:
        for r in analysis["severe_races"]:
            print(f"  {r['race']}: success={r['success_rate']:.1f}%, unchanged={r['unchanged_rate']:.1f}% (n={r['total']})")
    else:
        print("  None found")

    # Known problematic prompts
    print(f"\n--- Known Problematic Prompts ---")
    for prompt_id in ["B01", "B02", "D03"]:
        if prompt_id in analysis["by_prompt"]:
            data = analysis["by_prompt"][prompt_id]
            print(f"  {prompt_id}: success={data.get('success_rate', 0):.1f}%, unchanged={data.get('unchanged_rate', 0):.1f}%")

            # Race breakdown for this prompt
            print(f"    Race breakdown:")
            for race in RACES:
                if race in data["by_race"]:
                    rd = data["by_race"][race]
                    rate = rd["unchanged"] / rd["total"] * 100 if rd["total"] > 0 else 0
                    marker = " <-- SEVERE" if rate > 30 else ""
                    print(f"      {race}: {rd['success']}/{rd['total']} success, {rate:.0f}% unchanged{marker}")


def find_preservation_candidates(analyses: list) -> list:
    """Find prompt+race combinations that need preservation testing."""
    candidates = []

    # Known severe combinations from pilot
    known_severe = [
        ("D03", "Black"),
        ("D03", "Latino"),
        ("D03", "MiddleEastern"),
        ("D03", "Indian"),
        ("B01", "Black"),
        ("B01", "EastAsian"),
        ("B01", "Indian"),
        ("B01", "Latino"),
        ("B01", "MiddleEastern"),
        ("B01", "SoutheastAsian"),
        ("B02", "Black"),
        ("B02", "EastAsian"),
    ]

    for prompt_id, race in known_severe:
        candidates.append({
            "prompt_id": prompt_id,
            "race": race,
            "reason": "known_severe_from_pilot"
        })

    # Add from analysis
    for analysis in analyses:
        for prompt in analysis.get("severe_prompts", [])[:5]:
            prompt_id = prompt["prompt_id"]
            for race in analysis.get("severe_races", [])[:3]:
                race_name = race["race"]
                if (prompt_id, race_name) not in [(c["prompt_id"], c["race"]) for c in candidates]:
                    candidates.append({
                        "prompt_id": prompt_id,
                        "race": race_name,
                        "reason": f"severe_in_{analysis['model']}"
                    })

    return candidates


def main():
    print("=" * 60)
    print("Identifying Severe Bias Cases in B/D Categories")
    print("=" * 60)

    analyses = []

    for model in ["flux", "qwen", "step1x"]:
        results = load_results(model)
        if results:
            analysis = analyze_model(model, results)
            analyses.append(analysis)
            print_analysis(analysis)
        else:
            print(f"\n[SKIP] {model}: No results found")

    # Find candidates for preservation
    print("\n" + "=" * 60)
    print("PRESERVATION EXPERIMENT CANDIDATES")
    print("=" * 60)

    candidates = find_preservation_candidates(analyses)

    # Group by prompt
    by_prompt = defaultdict(list)
    for c in candidates:
        by_prompt[c["prompt_id"]].append(c["race"])

    for prompt_id in sorted(by_prompt.keys()):
        races = by_prompt[prompt_id]
        print(f"\n{prompt_id}:")
        for race in races:
            print(f"  - {race}")

    # Save candidates
    output_file = PROJECT_ROOT / "data" / "analysis" / "preservation_candidates.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump({
            "candidates": candidates,
            "by_prompt": dict(by_prompt),
            "models_analyzed": [a["model"] for a in analyses]
        }, f, indent=2)
    print(f"\nSaved to: {output_file}")


if __name__ == "__main__":
    main()
