#!/usr/bin/env python3
"""
Finalize Exp1 outputs for a model:
- exp1_{model}_results.jsonl
- exp1_{model}_final.json
- exp1_{model}_race_disparity.png
"""

import argparse
import json
import shutil
from pathlib import Path
import importlib.util
from typing import Optional


PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_ROOT = PROJECT_ROOT / "data" / "results" / "evaluations" / "exp1"


def _latest_file(folder: Path, pattern: str) -> Optional[Path]:
    files = list(folder.glob(pattern))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def _write_jsonl(results: list, output_path: Path) -> None:
    with output_path.open("w") as f:
        for item in results:
            f.write(json.dumps(item) + "\n")


def _load_results(file_path: Path) -> list:
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


def _load_plot_module(plot_path: Path):
    spec = importlib.util.spec_from_file_location("plot_race_summary", plot_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def finalize_model(model: str, overwrite: bool, skip_plot: bool) -> None:
    output_dir = OUTPUT_ROOT / model
    output_dir.mkdir(parents=True, exist_ok=True)

    jsonl_dest = output_dir / f"exp1_{model}_results.jsonl"
    final_dest = output_dir / f"exp1_{model}_final.json"
    final_jsonl = output_dir / "final.jsonl"

    if overwrite or not jsonl_dest.exists():
        streaming_src = _latest_file(output_dir, "streaming_*.jsonl")
        if streaming_src:
            shutil.copyfile(streaming_src, jsonl_dest)
            print(f"✓ JSONL: {jsonl_dest.name} (from {streaming_src.name})")
        else:
            eval_src = _latest_file(output_dir, f"exp1_evaluation_{model}_*.json")
            if eval_src:
                results = _load_results(eval_src)
                _write_jsonl(results, jsonl_dest)
                print(f"✓ JSONL: {jsonl_dest.name} (from {eval_src.name})")
            else:
                print("✗ No streaming JSONL or evaluation JSON found for JSONL output.")

    if jsonl_dest.exists() and (overwrite or not final_jsonl.exists()):
        shutil.copyfile(jsonl_dest, final_jsonl)
        print(f"✓ JSONL: {final_jsonl.name} (from {jsonl_dest.name})")

    if overwrite or not final_dest.exists():
        eval_src = _latest_file(output_dir, f"exp1_evaluation_{model}_*.json")
        if eval_src:
            shutil.copyfile(eval_src, final_dest)
            print(f"✓ Final JSON: {final_dest.name} (from {eval_src.name})")
        else:
            print("✗ No evaluation JSON found for final output.")

    if skip_plot:
        return

    try:
        import matplotlib  # noqa: F401
        import numpy  # noqa: F401
    except Exception:
        print("✗ matplotlib/numpy not available; skipped plot.")
        return

    results_path = jsonl_dest if jsonl_dest.exists() else None
    if not results_path:
        print("✗ No JSONL results found; skipped plot.")
        return

    plot_script = Path(__file__).parent / "plot_race_summary.py"
    plot_module = _load_plot_module(plot_script)

    results = plot_module.load_results(results_path)
    stats = plot_module.compute_stats(results)

    output_path = output_dir / f"exp1_{model}_race_disparity.png"
    plot_module.create_summary_figure(
        stats,
        output_path,
        model_name=model.upper(),
        categories="Category B (Occupation) + D (Vulnerability)"
    )


def main():
    parser = argparse.ArgumentParser(description="Finalize Exp1 outputs")
    parser.add_argument("--model", type=str, required=True, choices=["flux", "step1x", "qwen"])
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing outputs")
    parser.add_argument("--skip-plot", action="store_true", help="Skip plot generation")
    args = parser.parse_args()

    finalize_model(args.model, args.overwrite, args.skip_plot)


if __name__ == "__main__":
    main()
