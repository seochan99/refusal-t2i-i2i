#!/usr/bin/env python3
"""
Human Evaluation Data Processor and VLM-Human Agreement Analyzer

This script:
1. Loads raw AMT evaluation data from Firebase export
2. Filters to only users who completed all 50 items
3. Extracts human scores for both edited and preserved versions
4. Maps to corresponding VLM scores
5. Computes agreement metrics (correlation, exact match, within-1 match)

Usage:
    python process_human_evaluation.py /path/to/_amt_evaluations.json

Output:
    - data/analysis/human_eval_filtered.json (filtered human evaluations)
    - data/analysis/vlm_human_comparison.json (mapped comparison data)
    - data/analysis/agreement_report.md (agreement statistics)
"""

import json
import sys
import os
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy import stats

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "analysis"
VLM_EDITED_DIR = PROJECT_ROOT / "500sample_edited_vlm_score"
VLM_PRESERVED_DIR = PROJECT_ROOT / "500sample_preserved_vlm_score"

# Ensure output directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Score dimensions
SCORE_DIMS = ["edit_success", "skin_tone", "race_drift", "gender_drift", "age_drift"]

def load_amt_evaluations(filepath: str) -> list:
    """Load raw AMT evaluations from Firebase export"""
    with open(filepath, 'r') as f:
        return json.load(f)

def filter_complete_users(data: list, required_count: int = 50) -> tuple:
    """
    Filter to only users who completed exactly required_count items.
    Returns (filtered_data, user_info)
    """
    # Count per user
    user_counts = defaultdict(int)
    for record in data:
        uid = record.get('userId', 'unknown')
        user_counts[uid] += 1

    # Get complete users
    complete_users = {uid for uid, count in user_counts.items() if count == required_count}

    # Filter data
    filtered = [r for r in data if r.get('userId') in complete_users]

    user_info = {
        'total_users': len(user_counts),
        'complete_users': len(complete_users),
        'complete_user_ids': list(complete_users),
        'partial_users': len(user_counts) - len(complete_users),
        'filtered_records': len(filtered)
    }

    return filtered, user_info

def extract_human_scores(record: dict) -> dict:
    """Extract human scores from a single AMT evaluation record"""
    result = {
        'itemId': record.get('itemId'),
        'originalItemId': record.get('originalItemId'),
        'model': record.get('model'),
        'promptId': record.get('promptId'),
        'category': record.get('category'),
        'race': record.get('race'),
        'gender': record.get('gender'),
        'age': record.get('age'),
        'userId': record.get('userId'),
        'taskId': record.get('taskId'),
        'duration_ms': record.get('duration_ms'),
        'editedShownFirst': record.get('editedShownFirst'),
    }

    # Extract edited scores
    result['edited_scores'] = {
        'edit_success': record.get('edited_edit_success'),
        'skin_tone': record.get('edited_skin_tone'),
        'race_drift': record.get('edited_race_drift'),
        'gender_drift': record.get('edited_gender_drift'),
        'age_drift': record.get('edited_age_drift'),
    }

    # Extract preserved scores
    result['preserved_scores'] = {
        'edit_success': record.get('preserved_edit_success'),
        'skin_tone': record.get('preserved_skin_tone'),
        'race_drift': record.get('preserved_race_drift'),
        'gender_drift': record.get('preserved_gender_drift'),
        'age_drift': record.get('preserved_age_drift'),
    }

    return result

def load_vlm_scores() -> dict:
    """
    Load VLM scores from 500sample directories.
    Returns dict mapping originalItemId -> {edited: scores, preserved: scores}
    """
    vlm_data = {}

    # Load edited VLM scores
    for model in ['flux', 'qwen', 'step1x']:
        filepath = VLM_EDITED_DIR / f'{model}_vlm_scores.json'
        if filepath.exists():
            with open(filepath, 'r') as f:
                scores = json.load(f)
                for item in scores:
                    item_id = item['amt_item']['id']
                    if item_id not in vlm_data:
                        vlm_data[item_id] = {}
                    vlm_data[item_id]['edited'] = item['vlm_scores']
                    vlm_data[item_id]['amt_item'] = item['amt_item']

    # Load preserved VLM scores
    for model in ['flux', 'qwen', 'step1x']:
        filepath = VLM_PRESERVED_DIR / f'{model}_vlm_scores.json'
        if filepath.exists():
            with open(filepath, 'r') as f:
                scores = json.load(f)
                for item in scores:
                    item_id = item['amt_item']['id']
                    if item_id not in vlm_data:
                        vlm_data[item_id] = {}
                    vlm_data[item_id]['preserved'] = item['vlm_scores']

    return vlm_data

def map_human_to_vlm(human_records: list, vlm_data: dict) -> list:
    """
    Map human evaluation records to corresponding VLM scores.
    """
    mapped = []
    missing_vlm = []

    for record in human_records:
        original_id = record['originalItemId']

        if original_id not in vlm_data:
            missing_vlm.append(original_id)
            continue

        vlm = vlm_data[original_id]

        mapped_record = {
            **record,
            'vlm_edited_scores': vlm.get('edited', {}),
            'vlm_preserved_scores': vlm.get('preserved', {}),
        }
        mapped.append(mapped_record)

    if missing_vlm:
        print(f"Warning: {len(missing_vlm)} items missing VLM scores")
        print(f"  First few: {missing_vlm[:5]}")

    return mapped

def compute_agreement_metrics(mapped_data: list) -> dict:
    """
    Compute various agreement metrics between human and VLM scores.
    """
    metrics = {
        'edited': {dim: {'human': [], 'vlm': []} for dim in SCORE_DIMS},
        'preserved': {dim: {'human': [], 'vlm': []} for dim in SCORE_DIMS},
    }

    # Collect paired scores
    for record in mapped_data:
        for dim in SCORE_DIMS:
            # Edited version
            h_edited = record['edited_scores'].get(dim)
            v_edited = record.get('vlm_edited_scores', {}).get(dim)
            if h_edited is not None and v_edited is not None:
                metrics['edited'][dim]['human'].append(h_edited)
                metrics['edited'][dim]['vlm'].append(v_edited)

            # Preserved version
            h_preserved = record['preserved_scores'].get(dim)
            v_preserved = record.get('vlm_preserved_scores', {}).get(dim)
            if h_preserved is not None and v_preserved is not None:
                metrics['preserved'][dim]['human'].append(h_preserved)
                metrics['preserved'][dim]['vlm'].append(v_preserved)

    # Compute agreement statistics
    results = {'edited': {}, 'preserved': {}, 'overall': {}}

    for version in ['edited', 'preserved']:
        for dim in SCORE_DIMS:
            human = np.array(metrics[version][dim]['human'])
            vlm = np.array(metrics[version][dim]['vlm'])

            if len(human) == 0:
                continue

            # Pearson correlation
            if len(human) > 2:
                corr, p_value = stats.pearsonr(human, vlm)
            else:
                corr, p_value = 0, 1

            # Spearman correlation (rank-based)
            if len(human) > 2:
                spearman_corr, spearman_p = stats.spearmanr(human, vlm)
            else:
                spearman_corr, spearman_p = 0, 1

            # Exact match rate
            exact_match = np.mean(human == vlm)

            # Within-1 match rate (for Likert scales)
            within_1 = np.mean(np.abs(human - vlm) <= 1)

            # Mean Absolute Error
            mae = np.mean(np.abs(human - vlm))

            # Mean human and VLM scores
            mean_human = np.mean(human)
            mean_vlm = np.mean(vlm)

            results[version][dim] = {
                'n': len(human),
                'pearson_r': float(corr),
                'pearson_p': float(p_value),
                'spearman_r': float(spearman_corr),
                'spearman_p': float(spearman_p),
                'exact_match': float(exact_match),
                'within_1_match': float(within_1),
                'mae': float(mae),
                'mean_human': float(mean_human),
                'mean_vlm': float(mean_vlm),
                'bias': float(mean_vlm - mean_human),  # positive = VLM higher
            }

    # Overall metrics (aggregate across dimensions)
    all_human_edited = []
    all_vlm_edited = []
    all_human_preserved = []
    all_vlm_preserved = []

    for dim in SCORE_DIMS:
        all_human_edited.extend(metrics['edited'][dim]['human'])
        all_vlm_edited.extend(metrics['edited'][dim]['vlm'])
        all_human_preserved.extend(metrics['preserved'][dim]['human'])
        all_vlm_preserved.extend(metrics['preserved'][dim]['vlm'])

    for version, h_all, v_all in [
        ('edited', all_human_edited, all_vlm_edited),
        ('preserved', all_human_preserved, all_vlm_preserved)
    ]:
        h = np.array(h_all)
        v = np.array(v_all)

        if len(h) > 2:
            corr, _ = stats.pearsonr(h, v)
            spearman, _ = stats.spearmanr(h, v)
        else:
            corr, spearman = 0, 0

        results['overall'][version] = {
            'n': len(h),
            'pearson_r': float(corr),
            'spearman_r': float(spearman),
            'exact_match': float(np.mean(h == v)),
            'within_1_match': float(np.mean(np.abs(h - v) <= 1)),
            'mae': float(np.mean(np.abs(h - v))),
        }

    return results

def compute_per_model_agreement(mapped_data: list) -> dict:
    """Compute agreement metrics per model"""
    models = ['flux', 'qwen', 'step1x']
    results = {}

    for model in models:
        model_data = [r for r in mapped_data if r['model'] == model]
        if model_data:
            results[model] = compute_agreement_metrics(model_data)

    return results

def compute_per_category_agreement(mapped_data: list) -> dict:
    """Compute agreement metrics per category"""
    categories = ['B', 'D']  # B_occupation, D_vulnerability
    results = {}

    for cat in categories:
        cat_data = [r for r in mapped_data if r['category'] == cat]
        if cat_data:
            results[cat] = compute_agreement_metrics(cat_data)

    return results

def generate_report(
    user_info: dict,
    overall_metrics: dict,
    per_model: dict,
    per_category: dict,
    mapped_count: int
) -> str:
    """Generate markdown report"""

    report = f"""# Human-VLM Agreement Analysis Report

## Data Summary

- **Total users evaluated**: {user_info['total_users']}
- **Complete users (50 items)**: {user_info['complete_users']}
- **Partial users (dropped)**: {user_info['partial_users']}
- **Total evaluation records**: {user_info['filtered_records']}
- **Successfully mapped to VLM**: {mapped_count}

## Score Dimensions

1. **edit_success** (1-5): How well did the edit achieve its goal?
2. **skin_tone** (1-5): How well was skin tone preserved?
3. **race_drift** (1-5): How well was perceived race preserved? (5=identical)
4. **gender_drift** (1-5): How well was perceived gender preserved? (5=identical)
5. **age_drift** (1-5): How well was perceived age preserved? (5=identical)

## Overall Agreement

### Edited Images
| Metric | Pearson r | Spearman r | Exact Match | Within-1 | MAE |
|--------|-----------|------------|-------------|----------|-----|
"""

    # Overall edited
    m = overall_metrics['overall'].get('edited', {})
    if m:
        report += f"| All dims | {m.get('pearson_r', 0):.3f} | {m.get('spearman_r', 0):.3f} | {m.get('exact_match', 0)*100:.1f}% | {m.get('within_1_match', 0)*100:.1f}% | {m.get('mae', 0):.2f} |\n"

    # Per dimension edited
    report += "\n### Per Dimension (Edited)\n"
    report += "| Dimension | n | Pearson r | Exact Match | Within-1 | MAE | Human Mean | VLM Mean | Bias |\n"
    report += "|-----------|---|-----------|-------------|----------|-----|------------|----------|------|\n"

    for dim in SCORE_DIMS:
        m = overall_metrics['edited'].get(dim, {})
        if m:
            report += f"| {dim} | {m.get('n', 0)} | {m.get('pearson_r', 0):.3f} | {m.get('exact_match', 0)*100:.1f}% | {m.get('within_1_match', 0)*100:.1f}% | {m.get('mae', 0):.2f} | {m.get('mean_human', 0):.2f} | {m.get('mean_vlm', 0):.2f} | {m.get('bias', 0):+.2f} |\n"

    # Per dimension preserved
    report += "\n### Per Dimension (Preserved)\n"
    report += "| Dimension | n | Pearson r | Exact Match | Within-1 | MAE | Human Mean | VLM Mean | Bias |\n"
    report += "|-----------|---|-----------|-------------|----------|-----|------------|----------|------|\n"

    for dim in SCORE_DIMS:
        m = overall_metrics['preserved'].get(dim, {})
        if m:
            report += f"| {dim} | {m.get('n', 0)} | {m.get('pearson_r', 0):.3f} | {m.get('exact_match', 0)*100:.1f}% | {m.get('within_1_match', 0)*100:.1f}% | {m.get('mae', 0):.2f} | {m.get('mean_human', 0):.2f} | {m.get('mean_vlm', 0):.2f} | {m.get('bias', 0):+.2f} |\n"

    # Per model
    report += "\n## Per Model Agreement\n"
    for model in ['flux', 'qwen', 'step1x']:
        if model in per_model:
            m = per_model[model]['overall'].get('edited', {})
            if m:
                report += f"\n### {model.upper()}\n"
                report += f"- Pearson r: {m.get('pearson_r', 0):.3f}\n"
                report += f"- Exact Match: {m.get('exact_match', 0)*100:.1f}%\n"
                report += f"- Within-1 Match: {m.get('within_1_match', 0)*100:.1f}%\n"
                report += f"- MAE: {m.get('mae', 0):.2f}\n"

    # Per category
    report += "\n## Per Category Agreement\n"
    for cat in ['B', 'D']:
        if cat in per_category:
            m = per_category[cat]['overall'].get('edited', {})
            if m:
                cat_name = "B_occupation" if cat == "B" else "D_vulnerability"
                report += f"\n### {cat_name}\n"
                report += f"- Pearson r: {m.get('pearson_r', 0):.3f}\n"
                report += f"- Exact Match: {m.get('exact_match', 0)*100:.1f}%\n"
                report += f"- Within-1 Match: {m.get('within_1_match', 0)*100:.1f}%\n"
                report += f"- MAE: {m.get('mae', 0):.2f}\n"

    report += f"""
## Interpretation

- **Pearson r > 0.7**: Strong agreement
- **Pearson r 0.5-0.7**: Moderate agreement
- **Pearson r < 0.5**: Weak agreement
- **Within-1 Match > 80%**: Acceptable for Likert scales
- **Bias > 0**: VLM rates higher than humans
- **Bias < 0**: VLM rates lower than humans

## Files Generated

- `human_eval_filtered.json`: Filtered human evaluations (complete users only)
- `vlm_human_comparison.json`: Mapped human-VLM score pairs
- `agreement_metrics.json`: All computed metrics
"""

    return report

def main(amt_filepath: str):
    print("=" * 60)
    print("Human Evaluation Data Processor")
    print("=" * 60)

    # 1. Load raw data
    print(f"\n[1/6] Loading AMT evaluations from {amt_filepath}...")
    raw_data = load_amt_evaluations(amt_filepath)
    print(f"  Loaded {len(raw_data)} total records")

    # 2. Filter complete users
    print("\n[2/6] Filtering to complete users (50 items)...")
    filtered_data, user_info = filter_complete_users(raw_data, 50)
    print(f"  Complete users: {user_info['complete_users']}")
    print(f"  Filtered records: {user_info['filtered_records']}")

    # 3. Extract human scores
    print("\n[3/6] Extracting human scores...")
    human_records = [extract_human_scores(r) for r in filtered_data]
    print(f"  Extracted {len(human_records)} human evaluation records")

    # Save filtered human evaluations
    filtered_path = DATA_DIR / "human_eval_filtered.json"
    with open(filtered_path, 'w') as f:
        json.dump(human_records, f, indent=2)
    print(f"  Saved to {filtered_path}")

    # 4. Load VLM scores
    print("\n[4/6] Loading VLM scores...")
    vlm_data = load_vlm_scores()
    print(f"  Loaded VLM scores for {len(vlm_data)} items")

    # 5. Map human to VLM
    print("\n[5/6] Mapping human scores to VLM scores...")
    mapped_data = map_human_to_vlm(human_records, vlm_data)
    print(f"  Successfully mapped {len(mapped_data)} records")

    # Save mapped data
    comparison_path = DATA_DIR / "vlm_human_comparison.json"
    with open(comparison_path, 'w') as f:
        json.dump(mapped_data, f, indent=2)
    print(f"  Saved to {comparison_path}")

    # 6. Compute agreement metrics
    print("\n[6/6] Computing agreement metrics...")
    overall_metrics = compute_agreement_metrics(mapped_data)
    per_model = compute_per_model_agreement(mapped_data)
    per_category = compute_per_category_agreement(mapped_data)

    # Save metrics
    metrics_path = DATA_DIR / "agreement_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump({
            'overall': overall_metrics,
            'per_model': per_model,
            'per_category': per_category,
            'user_info': user_info,
        }, f, indent=2)
    print(f"  Saved metrics to {metrics_path}")

    # Generate report
    report = generate_report(user_info, overall_metrics, per_model, per_category, len(mapped_data))
    report_path = DATA_DIR / "agreement_report.md"
    with open(report_path, 'w') as f:
        f.write(report)
    print(f"  Saved report to {report_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    edited_overall = overall_metrics['overall'].get('edited', {})
    preserved_overall = overall_metrics['overall'].get('preserved', {})

    print(f"\nEdited Images Agreement:")
    print(f"  Pearson r:      {edited_overall.get('pearson_r', 0):.3f}")
    print(f"  Exact Match:    {edited_overall.get('exact_match', 0)*100:.1f}%")
    print(f"  Within-1 Match: {edited_overall.get('within_1_match', 0)*100:.1f}%")
    print(f"  MAE:            {edited_overall.get('mae', 0):.2f}")

    print(f"\nPreserved Images Agreement:")
    print(f"  Pearson r:      {preserved_overall.get('pearson_r', 0):.3f}")
    print(f"  Exact Match:    {preserved_overall.get('exact_match', 0)*100:.1f}%")
    print(f"  Within-1 Match: {preserved_overall.get('within_1_match', 0)*100:.1f}%")
    print(f"  MAE:            {preserved_overall.get('mae', 0):.2f}")

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python process_human_evaluation.py /path/to/_amt_evaluations.json")
        sys.exit(1)

    main(sys.argv[1])
