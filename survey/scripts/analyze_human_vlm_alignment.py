#!/usr/bin/env python3
"""
Human-VLM Alignment Analysis Script

Loads AMT evaluations from Firebase and compares with VLM evaluations.
Generates alignment metrics, inter-rater reliability, and paper-ready tables.

Usage:
    python scripts/analyze_human_vlm_alignment.py

Output:
    - data/exports/alignment_analysis_{timestamp}.json
    - data/exports/alignment_tables_{timestamp}.csv
    - Console summary with key metrics
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

# Statistical libraries
try:
    from scipy import stats
    from scipy.stats import spearmanr, pearsonr, kendalltau
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("Warning: scipy not installed. Some statistics will be unavailable.")

try:
    import krippendorff
    HAS_KRIPPENDORFF = True
except ImportError:
    HAS_KRIPPENDORFF = False
    print("Warning: krippendorff not installed. Alpha will be unavailable.")

# Firebase
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    HAS_FIREBASE = True
except ImportError:
    HAS_FIREBASE = False
    print("Warning: firebase-admin not installed.")

# Config
PROJECT_ID = "acrb-e8cb4"
SURVEY_DIR = Path(__file__).parent.parent.resolve()
PROJECT_ROOT = SURVEY_DIR.parent  # I2I-T2I-Bias-Refusal
DATA_DIR = PROJECT_ROOT / "data"
VLM_EVAL_DIR = DATA_DIR / "results" / "evaluations"
OUTPUT_DIR = SURVEY_DIR / "data" / "exports"

DIMENSIONS = ['edit_success', 'skin_tone', 'race_drift', 'gender_drift', 'age_drift']
MODELS = ['flux', 'qwen', 'step1x']
CATEGORIES = ['B', 'D']


def init_firebase():
    """Initialize Firebase Admin SDK"""
    if not HAS_FIREBASE:
        return None

    if firebase_admin._apps:
        return firestore.client()

    key_paths = [
        SURVEY_DIR / "firebase-admin-key.json",
        Path.home() / ".config" / "firebase" / f"{PROJECT_ID}-admin-key.json",
    ]

    cred = None
    for key_path in key_paths:
        if key_path.exists():
            print(f"Using credentials: {key_path}")
            cred = credentials.Certificate(str(key_path))
            break

    if not cred:
        try:
            cred = credentials.ApplicationDefault()
            print("Using application default credentials")
        except:
            print("ERROR: No Firebase credentials found")
            return None

    firebase_admin.initialize_app(cred, {'projectId': PROJECT_ID})
    return firestore.client()


def load_amt_evaluations(db) -> pd.DataFrame:
    """Load AMT evaluations from Firestore"""
    print("\n📥 Loading AMT evaluations from Firebase...")

    if db is None:
        # Try loading from exported file
        export_files = sorted(OUTPUT_DIR.glob("amt_evaluations_*.json"), reverse=True)
        if export_files:
            print(f"  Using exported file: {export_files[0].name}")
            with open(export_files[0]) as f:
                data = json.load(f)
            return pd.DataFrame(data)
        else:
            print("  ERROR: No Firebase connection and no exported files found")
            return pd.DataFrame()

    docs = db.collection('amt_evaluations').stream()

    evaluations = []
    for doc in docs:
        data = doc.to_dict()
        if 'createdAt' in data and data['createdAt']:
            data['createdAt'] = data['createdAt'].isoformat() if hasattr(data['createdAt'], 'isoformat') else str(data['createdAt'])
        evaluations.append(data)

    print(f"  Loaded {len(evaluations)} evaluations")
    return pd.DataFrame(evaluations)


def load_vlm_evaluations() -> Dict[str, Dict]:
    """Load VLM evaluations from local files"""
    print("\n📥 Loading VLM evaluations...")

    vlm_data = {}

    # Load exp1 evaluations (edited images)
    for model in MODELS:
        exp1_file = VLM_EVAL_DIR / "exp1" / model / f"exp1_{model}_final.json"
        if exp1_file.exists():
            with open(exp1_file) as f:
                data = json.load(f)

            loaded_count = 0
            for result in data.get('results', []):
                # Skip results without scores (failed evaluations)
                if 'scores' not in result:
                    continue

                # Create key: model_promptId_race_gender_age
                key = f"{model}_{result['prompt_id']}_{result['race']}_{result['gender']}_{result['age']}"
                vlm_data[key] = {
                    'model': model,
                    'prompt_id': result['prompt_id'],
                    'category': result['category'],
                    'race': result['race'],
                    'gender': result['gender'],
                    'age': result['age'],
                    'edited_scores': result['scores'],
                    'ensemble_method': result.get('ensemble_method', 'unknown'),
                    'needs_review': result.get('needs_review', False),
                }
                loaded_count += 1

            print(f"  Loaded {loaded_count} exp1 results for {model}")

    # Load exp2 evaluations (preserved images)
    for model in MODELS:
        exp2_files = list((VLM_EVAL_DIR / "exp2" / model).glob("exp2_evaluation_*.json"))
        if exp2_files:
            exp2_file = sorted(exp2_files)[-1]  # Latest
            with open(exp2_file) as f:
                data = json.load(f)

            count = 0
            for result in data.get('results', []):
                # Skip results without scores
                if 'scores' not in result:
                    continue

                key = f"{model}_{result['prompt_id']}_{result['race']}_{result['gender']}_{result['age']}"
                if key in vlm_data:
                    vlm_data[key]['preserved_scores'] = result['scores']
                    count += 1

            print(f"  Added {count} exp2 preserved scores for {model}")

    print(f"  Total VLM entries: {len(vlm_data)}")
    return vlm_data


def create_mapping_key(row: pd.Series) -> str:
    """Create mapping key from AMT evaluation row"""
    return f"{row['model']}_{row['promptId']}_{row['race']}_{row['gender']}_{row['age']}"


def compute_agreement_metrics(human_scores: List[float], vlm_scores: List[float]) -> Dict:
    """Compute agreement metrics between human and VLM scores"""
    if len(human_scores) == 0 or len(vlm_scores) == 0:
        return {}

    human_arr = np.array(human_scores)
    vlm_arr = np.array(vlm_scores)

    metrics = {
        'n': len(human_scores),
        'human_mean': float(np.mean(human_arr)),
        'human_std': float(np.std(human_arr)),
        'vlm_mean': float(np.mean(vlm_arr)),
        'vlm_std': float(np.std(vlm_arr)),
        'mean_diff': float(np.mean(human_arr - vlm_arr)),
        'mae': float(np.mean(np.abs(human_arr - vlm_arr))),
        'rmse': float(np.sqrt(np.mean((human_arr - vlm_arr) ** 2))),
    }

    # Exact agreement
    metrics['exact_agreement'] = float(np.mean(human_arr == vlm_arr))

    # Within-1 agreement
    metrics['within_1_agreement'] = float(np.mean(np.abs(human_arr - vlm_arr) <= 1))

    # Correlations
    if HAS_SCIPY and len(human_scores) > 2:
        try:
            pearson_r, pearson_p = pearsonr(human_arr, vlm_arr)
            metrics['pearson_r'] = float(pearson_r)
            metrics['pearson_p'] = float(pearson_p)
        except:
            pass

        try:
            spearman_r, spearman_p = spearmanr(human_arr, vlm_arr)
            metrics['spearman_r'] = float(spearman_r)
            metrics['spearman_p'] = float(spearman_p)
        except:
            pass

        try:
            kendall_tau, kendall_p = kendalltau(human_arr, vlm_arr)
            metrics['kendall_tau'] = float(kendall_tau)
            metrics['kendall_p'] = float(kendall_p)
        except:
            pass

    return metrics


def compute_inter_rater_reliability(ratings_matrix: np.ndarray) -> Dict:
    """Compute inter-rater reliability metrics"""
    metrics = {}

    # Filter out items with only one rater
    valid_mask = np.sum(~np.isnan(ratings_matrix), axis=1) >= 2
    filtered = ratings_matrix[valid_mask]

    if len(filtered) == 0:
        return metrics

    metrics['n_items'] = int(valid_mask.sum())
    metrics['n_raters_per_item'] = float(np.mean(np.sum(~np.isnan(filtered), axis=1)))

    # Krippendorff's Alpha
    if HAS_KRIPPENDORFF:
        try:
            alpha = krippendorff.alpha(reliability_data=filtered.T, level_of_measurement='ordinal')
            metrics['krippendorff_alpha'] = float(alpha)
        except:
            pass

    # Simple percent agreement (pairwise)
    agreements = []
    for i in range(filtered.shape[0]):
        row = filtered[i]
        valid = row[~np.isnan(row)]
        if len(valid) >= 2:
            # Pairwise comparisons
            for j in range(len(valid)):
                for k in range(j + 1, len(valid)):
                    agreements.append(1 if valid[j] == valid[k] else 0)

    if agreements:
        metrics['pairwise_agreement'] = float(np.mean(agreements))

    return metrics


def analyze_by_dimension(amt_df: pd.DataFrame, vlm_data: Dict) -> Dict:
    """Analyze Human-VLM alignment by dimension"""
    print("\n📊 Analyzing by dimension...")

    results = {}

    for dim in DIMENSIONS:
        edited_human = []
        edited_vlm = []
        preserved_human = []
        preserved_vlm = []

        for _, row in amt_df.iterrows():
            key = create_mapping_key(row)

            if key not in vlm_data:
                continue

            vlm = vlm_data[key]

            # Edited scores
            human_edited = row.get(f'edited_{dim}')
            if pd.notna(human_edited) and 'edited_scores' in vlm:
                vlm_edited = vlm['edited_scores'].get(dim)
                if vlm_edited is not None:
                    edited_human.append(human_edited)
                    edited_vlm.append(vlm_edited)

            # Preserved scores
            human_preserved = row.get(f'preserved_{dim}')
            if pd.notna(human_preserved) and 'preserved_scores' in vlm:
                vlm_preserved = vlm['preserved_scores'].get(dim)
                if vlm_preserved is not None:
                    preserved_human.append(human_preserved)
                    preserved_vlm.append(vlm_preserved)

        results[dim] = {
            'edited': compute_agreement_metrics(edited_human, edited_vlm),
            'preserved': compute_agreement_metrics(preserved_human, preserved_vlm),
        }

        print(f"  {dim}: edited={len(edited_human)}, preserved={len(preserved_human)} pairs")

    return results


def analyze_by_model(amt_df: pd.DataFrame, vlm_data: Dict) -> Dict:
    """Analyze Human-VLM alignment by model"""
    print("\n📊 Analyzing by model...")

    results = {}

    for model in MODELS:
        model_df = amt_df[amt_df['model'] == model]

        if len(model_df) == 0:
            continue

        all_human = []
        all_vlm = []

        for _, row in model_df.iterrows():
            key = create_mapping_key(row)
            if key not in vlm_data:
                continue

            vlm = vlm_data[key]

            for dim in DIMENSIONS:
                human_val = row.get(f'edited_{dim}')
                if pd.notna(human_val) and 'edited_scores' in vlm:
                    vlm_val = vlm['edited_scores'].get(dim)
                    if vlm_val is not None:
                        all_human.append(human_val)
                        all_vlm.append(vlm_val)

        results[model] = compute_agreement_metrics(all_human, all_vlm)
        print(f"  {model}: {len(all_human)} score pairs")

    return results


def analyze_by_category(amt_df: pd.DataFrame, vlm_data: Dict) -> Dict:
    """Analyze Human-VLM alignment by category"""
    print("\n📊 Analyzing by category...")

    results = {}

    for cat in CATEGORIES:
        cat_df = amt_df[amt_df['category'] == cat]

        if len(cat_df) == 0:
            continue

        all_human = []
        all_vlm = []

        for _, row in cat_df.iterrows():
            key = create_mapping_key(row)
            if key not in vlm_data:
                continue

            vlm = vlm_data[key]

            for dim in DIMENSIONS:
                human_val = row.get(f'edited_{dim}')
                if pd.notna(human_val) and 'edited_scores' in vlm:
                    vlm_val = vlm['edited_scores'].get(dim)
                    if vlm_val is not None:
                        all_human.append(human_val)
                        all_vlm.append(vlm_val)

        results[cat] = compute_agreement_metrics(all_human, all_vlm)
        print(f"  Category {cat}: {len(all_human)} score pairs")

    return results


def analyze_by_race(amt_df: pd.DataFrame, vlm_data: Dict) -> Dict:
    """Analyze Human-VLM alignment by race"""
    print("\n📊 Analyzing by race...")

    races = amt_df['race'].dropna().unique()
    results = {}

    for race in races:
        race_df = amt_df[amt_df['race'] == race]

        all_human = []
        all_vlm = []

        for _, row in race_df.iterrows():
            key = create_mapping_key(row)
            if key not in vlm_data:
                continue

            vlm = vlm_data[key]

            for dim in DIMENSIONS:
                human_val = row.get(f'edited_{dim}')
                if pd.notna(human_val) and 'edited_scores' in vlm:
                    vlm_val = vlm['edited_scores'].get(dim)
                    if vlm_val is not None:
                        all_human.append(human_val)
                        all_vlm.append(vlm_val)

        if all_human:
            results[race] = compute_agreement_metrics(all_human, all_vlm)
            print(f"  {race}: {len(all_human)} score pairs")

    return results


def compute_inter_rater(amt_df: pd.DataFrame) -> Dict:
    """Compute inter-rater reliability among human raters"""
    print("\n📊 Computing inter-rater reliability...")

    # Group by item
    if 'originalItemId' not in amt_df.columns and 'itemId' not in amt_df.columns:
        print("  Warning: No item ID column found")
        return {}

    item_col = 'originalItemId' if 'originalItemId' in amt_df.columns else 'itemId'

    results = {}

    for dim in DIMENSIONS:
        col = f'edited_{dim}'
        if col not in amt_df.columns:
            continue

        # Create ratings matrix: items x raters
        items = amt_df[item_col].unique()
        max_raters = amt_df.groupby(item_col).size().max()

        ratings_matrix = np.full((len(items), max_raters), np.nan)

        for i, item in enumerate(items):
            item_ratings = amt_df[amt_df[item_col] == item][col].dropna().values
            ratings_matrix[i, :len(item_ratings)] = item_ratings

        irr = compute_inter_rater_reliability(ratings_matrix)
        if irr:
            results[dim] = irr
            alpha = irr.get('krippendorff_alpha', 'N/A')
            print(f"  {dim}: α={alpha:.3f}" if isinstance(alpha, float) else f"  {dim}: α={alpha}")

    return results


def generate_paper_tables(analysis: Dict) -> str:
    """Generate LaTeX tables for paper"""

    latex = []

    # Table 1: Human-VLM Agreement by Dimension
    latex.append("% Table: Human-VLM Agreement by Dimension")
    latex.append("\\begin{table}[h]")
    latex.append("\\centering")
    latex.append("\\caption{Human-VLM Agreement by Evaluation Dimension}")
    latex.append("\\label{tab:human-vlm-agreement}")
    latex.append("\\begin{tabular}{lcccccc}")
    latex.append("\\toprule")
    latex.append("Dimension & N & Human $\\mu$ & VLM $\\mu$ & $r$ & MAE & Agr.\\% \\\\")
    latex.append("\\midrule")

    if 'by_dimension' in analysis:
        for dim in DIMENSIONS:
            if dim in analysis['by_dimension']:
                edited = analysis['by_dimension'][dim].get('edited', {})
                n = edited.get('n', 0)
                h_mean = edited.get('human_mean', 0)
                v_mean = edited.get('vlm_mean', 0)
                r = edited.get('spearman_r', 0)
                mae = edited.get('mae', 0)
                agr = edited.get('within_1_agreement', 0) * 100

                dim_name = dim.replace('_', ' ').title()
                latex.append(f"{dim_name} & {n} & {h_mean:.2f} & {v_mean:.2f} & {r:.3f} & {mae:.2f} & {agr:.1f}\\% \\\\")

    latex.append("\\bottomrule")
    latex.append("\\end{tabular}")
    latex.append("\\end{table}")
    latex.append("")

    # Table 2: Inter-Rater Reliability
    latex.append("% Table: Inter-Rater Reliability")
    latex.append("\\begin{table}[h]")
    latex.append("\\centering")
    latex.append("\\caption{Inter-Rater Reliability (Krippendorff's $\\alpha$)}")
    latex.append("\\label{tab:inter-rater}")
    latex.append("\\begin{tabular}{lcc}")
    latex.append("\\toprule")
    latex.append("Dimension & $\\alpha$ & Agreement\\% \\\\")
    latex.append("\\midrule")

    if 'inter_rater' in analysis:
        for dim in DIMENSIONS:
            if dim in analysis['inter_rater']:
                irr = analysis['inter_rater'][dim]
                alpha = irr.get('krippendorff_alpha', 0)
                agr = irr.get('pairwise_agreement', 0) * 100
                dim_name = dim.replace('_', ' ').title()
                latex.append(f"{dim_name} & {alpha:.3f} & {agr:.1f}\\% \\\\")

    latex.append("\\bottomrule")
    latex.append("\\end{tabular}")
    latex.append("\\end{table}")

    return "\n".join(latex)


def print_summary(analysis: Dict):
    """Print summary to console"""

    print("\n" + "=" * 70)
    print("📈 HUMAN-VLM ALIGNMENT ANALYSIS SUMMARY")
    print("=" * 70)

    # Overall stats
    if 'overall' in analysis:
        ov = analysis['overall']
        print(f"\n📊 Overall Statistics:")
        print(f"   Total evaluations: {ov.get('total_evaluations', 'N/A')}")
        print(f"   Unique items: {ov.get('unique_items', 'N/A')}")
        print(f"   Unique raters: {ov.get('unique_raters', 'N/A')}")
        print(f"   Matched with VLM: {ov.get('matched_with_vlm', 'N/A')}")

    # By dimension
    if 'by_dimension' in analysis:
        print(f"\n📊 Human-VLM Agreement by Dimension (Edited):")
        print(f"   {'Dimension':<15} {'N':>6} {'H_μ':>6} {'V_μ':>6} {'ρ':>7} {'MAE':>6} {'Agr%':>6}")
        print("   " + "-" * 55)

        for dim in DIMENSIONS:
            if dim in analysis['by_dimension']:
                e = analysis['by_dimension'][dim].get('edited', {})
                n = e.get('n', 0)
                h = e.get('human_mean', 0)
                v = e.get('vlm_mean', 0)
                r = e.get('spearman_r', 0)
                mae = e.get('mae', 0)
                agr = e.get('within_1_agreement', 0) * 100
                print(f"   {dim:<15} {n:>6} {h:>6.2f} {v:>6.2f} {r:>7.3f} {mae:>6.2f} {agr:>5.1f}%")

    # Inter-rater reliability
    if 'inter_rater' in analysis:
        print(f"\n📊 Inter-Rater Reliability (Human Raters):")
        print(f"   {'Dimension':<15} {'α':>8} {'Agr%':>8}")
        print("   " + "-" * 35)

        for dim in DIMENSIONS:
            if dim in analysis['inter_rater']:
                irr = analysis['inter_rater'][dim]
                alpha = irr.get('krippendorff_alpha', 0)
                agr = irr.get('pairwise_agreement', 0) * 100
                print(f"   {dim:<15} {alpha:>8.3f} {agr:>7.1f}%")

    # By model
    if 'by_model' in analysis:
        print(f"\n📊 Agreement by Model:")
        for model, metrics in analysis['by_model'].items():
            r = metrics.get('spearman_r', 0)
            mae = metrics.get('mae', 0)
            print(f"   {model}: ρ={r:.3f}, MAE={mae:.2f}")

    # By category
    if 'by_category' in analysis:
        print(f"\n📊 Agreement by Category:")
        for cat, metrics in analysis['by_category'].items():
            r = metrics.get('spearman_r', 0)
            mae = metrics.get('mae', 0)
            cat_name = 'Occupation' if cat == 'B' else 'Vulnerability'
            print(f"   {cat} ({cat_name}): ρ={r:.3f}, MAE={mae:.2f}")

    print("\n" + "=" * 70)


def generate_demo_data(vlm_data: Dict, n_samples: int = 100) -> pd.DataFrame:
    """Generate demo AMT evaluations for testing"""
    import random
    random.seed(42)

    samples = []
    vlm_keys = list(vlm_data.keys())

    for i in range(min(n_samples, len(vlm_keys))):
        key = vlm_keys[i]
        vlm = vlm_data[key]

        # Parse key: model_promptId_race_gender_age
        parts = key.split('_')
        model = parts[0]
        prompt_id = parts[1]
        race = parts[2]
        gender = parts[3]
        age = parts[4]

        # Generate 3 raters per item with some variance from VLM scores
        for rater in range(3):
            sample = {
                'itemId': f'amt_{i:04d}',
                'originalItemId': f'exp2_{model}_{prompt_id}_{race}_{gender}_{age}',
                'model': model,
                'promptId': prompt_id,
                'category': 'B' if prompt_id.startswith('B') else 'D',
                'race': race,
                'gender': gender,
                'age': age,
                'userId': f'demo_user_{rater}',
            }

            # Add scores with some variance from VLM
            if 'edited_scores' in vlm:
                for dim in DIMENSIONS:
                    vlm_score = vlm['edited_scores'].get(dim, 3)
                    # Add variance: +/- 1 with 30% probability
                    variance = random.choice([-1, 0, 0, 0, 1])
                    sample[f'edited_{dim}'] = max(1, min(5, vlm_score + variance))

            if 'preserved_scores' in vlm:
                for dim in DIMENSIONS:
                    vlm_score = vlm['preserved_scores'].get(dim, 3)
                    variance = random.choice([-1, 0, 0, 0, 1])
                    sample[f'preserved_{dim}'] = max(1, min(5, vlm_score + variance))

            samples.append(sample)

    return pd.DataFrame(samples)


def main():
    import sys
    demo_mode = '--demo' in sys.argv

    print("=" * 70)
    print("🔬 Human-VLM Alignment Analysis")
    if demo_mode:
        print("   [DEMO MODE - using simulated human evaluations]")
    print("=" * 70)

    # Initialize
    db = init_firebase()

    # Load VLM data first (needed for demo mode)
    vlm_data = load_vlm_evaluations()

    # Load AMT data
    if demo_mode:
        print("\n📥 Generating demo AMT evaluations...")
        amt_df = generate_demo_data(vlm_data, n_samples=200)
        print(f"  Generated {len(amt_df)} demo evaluations")
    else:
        amt_df = load_amt_evaluations(db)

    if len(amt_df) == 0:
        print("\n❌ No AMT evaluations found.")
        print("   Options:")
        print("   1. Run with --demo flag for demonstration")
        print("   2. Export data: python export_evaluations.py")
        print("   3. Check Firebase connection")
        return

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Overall stats
    analysis = {
        'timestamp': timestamp,
        'overall': {
            'total_evaluations': len(amt_df),
            'unique_items': amt_df['itemId'].nunique() if 'itemId' in amt_df.columns else 0,
            'unique_raters': amt_df['userId'].nunique() if 'userId' in amt_df.columns else 0,
            'total_vlm_entries': len(vlm_data),
        }
    }

    # Count matched items
    matched = 0
    for _, row in amt_df.iterrows():
        key = create_mapping_key(row)
        if key in vlm_data:
            matched += 1
    analysis['overall']['matched_with_vlm'] = matched

    # Run analyses
    analysis['by_dimension'] = analyze_by_dimension(amt_df, vlm_data)
    analysis['by_model'] = analyze_by_model(amt_df, vlm_data)
    analysis['by_category'] = analyze_by_category(amt_df, vlm_data)
    analysis['by_race'] = analyze_by_race(amt_df, vlm_data)
    analysis['inter_rater'] = compute_inter_rater(amt_df)

    # Save results
    json_path = OUTPUT_DIR / f"alignment_analysis_{timestamp}.json"
    with open(json_path, 'w') as f:
        json.dump(analysis, f, indent=2)
    print(f"\n💾 Saved: {json_path}")

    # Generate and save LaTeX tables
    latex_tables = generate_paper_tables(analysis)
    latex_path = OUTPUT_DIR / f"alignment_tables_{timestamp}.tex"
    with open(latex_path, 'w') as f:
        f.write(latex_tables)
    print(f"💾 Saved: {latex_path}")

    # Print summary
    print_summary(analysis)

    print(f"\n✅ Analysis complete!")
    print(f"   JSON: {json_path}")
    print(f"   LaTeX: {latex_path}")


if __name__ == '__main__':
    main()
