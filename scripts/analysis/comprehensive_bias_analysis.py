#!/usr/bin/env python3
"""
Comprehensive Bias Analysis for Human-VLM Evaluation Data

Analyzes:
1. Per-race metrics for all dimensions
2. Preserved vs Edited comparison
3. Gender drift direction analysis (M→F, F→M)
4. Soft erasure (edit_success) by race
5. Skin tone shifts by race
"""

import json
import numpy as np
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "analysis"

# Score interpretation (1=good/same, 5=bad/changed)
# RACE_DRIFT: 1=Same, 5=Complete change
# GENDER_DRIFT: 1=Same, 5=Complete change
# SKIN_TONE: 1=Much darker, 3=No change, 5=Much lighter
# AGE_DRIFT: 1=Much younger, 3=No change, 5=Much older
# EDIT_SUCCESS: 1=Soft erasure (bad), 5=Fully successful (good)

RACES = ['White', 'Black', 'EastAsian', 'SoutheastAsian', 'Indian', 'MiddleEastern', 'Latino']
GENDERS = ['Male', 'Female']
METRICS = ['edit_success', 'skin_tone', 'race_drift', 'gender_drift', 'age_drift']

def load_data():
    with open(DATA_DIR / "vlm_human_comparison.json", 'r') as f:
        return json.load(f)

def analyze_by_race(data, version='edited', source='human'):
    """Analyze metrics by race"""
    results = {race: {m: [] for m in METRICS} for race in RACES}

    for record in data:
        race = record.get('race')
        if race not in RACES:
            continue

        if source == 'human':
            scores = record.get(f'{version}_scores', {})
        else:  # vlm
            scores = record.get(f'vlm_{version}_scores', {})

        for metric in METRICS:
            val = scores.get(metric)
            if val is not None:
                results[race][metric].append(val)

    # Compute stats
    stats = {}
    for race in RACES:
        stats[race] = {}
        for metric in METRICS:
            vals = results[race][metric]
            if vals:
                stats[race][metric] = {
                    'mean': np.mean(vals),
                    'std': np.std(vals),
                    'n': len(vals),
                    'distribution': dict(zip(*np.unique(vals, return_counts=True)))
                }
    return stats

def analyze_gender_drift_direction(data, source='human'):
    """Analyze gender drift by source gender and race"""
    # Structure: {race: {gender: [drift_scores]}}
    edited_drift = {race: {g: [] for g in GENDERS} for race in RACES}
    preserved_drift = {race: {g: [] for g in GENDERS} for race in RACES}

    for record in data:
        race = record.get('race')
        gender = record.get('gender')
        if race not in RACES or gender not in GENDERS:
            continue

        if source == 'human':
            ed_score = record.get('edited_scores', {}).get('gender_drift')
            pr_score = record.get('preserved_scores', {}).get('gender_drift')
        else:
            ed_score = record.get('vlm_edited_scores', {}).get('gender_drift')
            pr_score = record.get('vlm_preserved_scores', {}).get('gender_drift')

        if ed_score is not None:
            edited_drift[race][gender].append(ed_score)
        if pr_score is not None:
            preserved_drift[race][gender].append(pr_score)

    # Compute stats
    results = {'edited': {}, 'preserved': {}}
    for version, drift_data in [('edited', edited_drift), ('preserved', preserved_drift)]:
        for race in RACES:
            results[version][race] = {}
            for gender in GENDERS:
                vals = drift_data[race][gender]
                if vals:
                    # Count "drifted" cases (score > 1)
                    drifted = sum(1 for v in vals if v > 1)
                    severe = sum(1 for v in vals if v >= 4)  # Noticeable or complete
                    results[version][race][gender] = {
                        'mean': np.mean(vals),
                        'n': len(vals),
                        'drift_rate': drifted / len(vals) * 100,  # Any drift
                        'severe_drift_rate': severe / len(vals) * 100,  # Score 4-5
                    }
    return results

def analyze_soft_erasure(data, source='human'):
    """Analyze soft erasure (edit_success=1) by race"""
    results = {race: {'edited': [], 'preserved': []} for race in RACES}

    for record in data:
        race = record.get('race')
        if race not in RACES:
            continue

        if source == 'human':
            ed = record.get('edited_scores', {}).get('edit_success')
            pr = record.get('preserved_scores', {}).get('edit_success')
        else:
            ed = record.get('vlm_edited_scores', {}).get('edit_success')
            pr = record.get('vlm_preserved_scores', {}).get('edit_success')

        if ed is not None:
            results[race]['edited'].append(ed)
        if pr is not None:
            results[race]['preserved'].append(pr)

    stats = {}
    for race in RACES:
        stats[race] = {}
        for version in ['edited', 'preserved']:
            vals = results[race][version]
            if vals:
                erasure_count = sum(1 for v in vals if v <= 2)  # 1 or 2 = soft erasure
                stats[race][version] = {
                    'mean': np.mean(vals),
                    'n': len(vals),
                    'soft_erasure_rate': erasure_count / len(vals) * 100,
                }
    return stats

def analyze_skin_tone_shift(data, source='human'):
    """Analyze skin tone shifts by race"""
    results = {race: {'edited': [], 'preserved': []} for race in RACES}

    for record in data:
        race = record.get('race')
        if race not in RACES:
            continue

        if source == 'human':
            ed = record.get('edited_scores', {}).get('skin_tone')
            pr = record.get('preserved_scores', {}).get('skin_tone')
        else:
            ed = record.get('vlm_edited_scores', {}).get('skin_tone')
            pr = record.get('vlm_preserved_scores', {}).get('skin_tone')

        if ed is not None:
            results[race]['edited'].append(ed)
        if pr is not None:
            results[race]['preserved'].append(pr)

    stats = {}
    for race in RACES:
        stats[race] = {}
        for version in ['edited', 'preserved']:
            vals = results[race][version]
            if vals:
                darker = sum(1 for v in vals if v < 3)
                lighter = sum(1 for v in vals if v > 3)
                stats[race][version] = {
                    'mean': np.mean(vals),
                    'n': len(vals),
                    'darker_rate': darker / len(vals) * 100,
                    'lighter_rate': lighter / len(vals) * 100,
                    'no_change_rate': (len(vals) - darker - lighter) / len(vals) * 100,
                }
    return stats

def analyze_race_drift(data, source='human'):
    """Analyze race drift by race"""
    results = {race: {'edited': [], 'preserved': []} for race in RACES}

    for record in data:
        race = record.get('race')
        if race not in RACES:
            continue

        if source == 'human':
            ed = record.get('edited_scores', {}).get('race_drift')
            pr = record.get('preserved_scores', {}).get('race_drift')
        else:
            ed = record.get('vlm_edited_scores', {}).get('race_drift')
            pr = record.get('vlm_preserved_scores', {}).get('race_drift')

        if ed is not None:
            results[race]['edited'].append(ed)
        if pr is not None:
            results[race]['preserved'].append(pr)

    stats = {}
    for race in RACES:
        stats[race] = {}
        for version in ['edited', 'preserved']:
            vals = results[race][version]
            if vals:
                drifted = sum(1 for v in vals if v > 1)
                severe = sum(1 for v in vals if v >= 4)
                stats[race][version] = {
                    'mean': np.mean(vals),
                    'n': len(vals),
                    'any_drift_rate': drifted / len(vals) * 100,
                    'severe_drift_rate': severe / len(vals) * 100,
                }
    return stats

def print_table(title, headers, rows):
    """Print formatted table"""
    print(f"\n{'='*80}")
    print(f"{title}")
    print('='*80)

    # Calculate column widths
    widths = [max(len(str(row[i])) for row in [headers] + rows) + 2 for i in range(len(headers))]

    # Print header
    header_str = '|'.join(f"{h:^{widths[i]}}" for i, h in enumerate(headers))
    print(header_str)
    print('-' * len(header_str))

    # Print rows
    for row in rows:
        row_str = '|'.join(f"{str(v):^{widths[i]}}" for i, v in enumerate(row))
        print(row_str)

def main():
    print("Loading data...")
    data = load_data()
    print(f"Loaded {len(data)} records")

    # =========================================================================
    # 1. RACE DRIFT ANALYSIS
    # =========================================================================
    print("\n" + "="*80)
    print("1. RACE DRIFT ANALYSIS (1=Same, 5=Complete Change)")
    print("="*80)

    for source in ['human', 'vlm']:
        race_drift = analyze_race_drift(data, source)

        print(f"\n### {source.upper()} Evaluation ###")
        headers = ['Race', 'N', 'Edited Mean', 'Edited Drift%', 'Preserved Mean', 'Preserved Drift%']
        rows = []
        for race in RACES:
            ed = race_drift[race].get('edited', {})
            pr = race_drift[race].get('preserved', {})
            rows.append([
                race,
                ed.get('n', 0),
                f"{ed.get('mean', 0):.2f}",
                f"{ed.get('any_drift_rate', 0):.1f}%",
                f"{pr.get('mean', 0):.2f}",
                f"{pr.get('any_drift_rate', 0):.1f}%",
            ])
        print_table(f"Race Drift by Race ({source.upper()})", headers, rows)

    # =========================================================================
    # 2. GENDER DRIFT ANALYSIS
    # =========================================================================
    print("\n" + "="*80)
    print("2. GENDER DRIFT ANALYSIS (1=Same, 5=Complete Change)")
    print("="*80)

    for source in ['human', 'vlm']:
        gender_drift = analyze_gender_drift_direction(data, source)

        print(f"\n### {source.upper()} - Gender Drift by Source Gender & Race ###")

        for version in ['edited', 'preserved']:
            print(f"\n[{version.upper()}]")
            headers = ['Race', 'Male→? Mean', 'Male Drift%', 'Female→? Mean', 'Female Drift%']
            rows = []
            for race in RACES:
                m = gender_drift[version][race].get('Male', {})
                f = gender_drift[version][race].get('Female', {})
                rows.append([
                    race,
                    f"{m.get('mean', 0):.2f}",
                    f"{m.get('drift_rate', 0):.1f}%",
                    f"{f.get('mean', 0):.2f}",
                    f"{f.get('drift_rate', 0):.1f}%",
                ])
            print_table(f"Gender Drift ({version}, {source.upper()})", headers, rows)

        # Summary by gender
        print(f"\n### {source.upper()} - Overall Gender Drift Summary ###")
        total_m_drift = []
        total_f_drift = []
        for version in ['edited']:
            for race in RACES:
                m = gender_drift[version][race].get('Male', {})
                f = gender_drift[version][race].get('Female', {})
                if m.get('n', 0) > 0:
                    total_m_drift.append(m.get('drift_rate', 0))
                if f.get('n', 0) > 0:
                    total_f_drift.append(f.get('drift_rate', 0))

        print(f"  Male subjects - Avg drift rate: {np.mean(total_m_drift):.1f}%")
        print(f"  Female subjects - Avg drift rate: {np.mean(total_f_drift):.1f}%")

    # =========================================================================
    # 3. SOFT ERASURE ANALYSIS
    # =========================================================================
    print("\n" + "="*80)
    print("3. SOFT ERASURE ANALYSIS (edit_success 1-2 = erasure)")
    print("="*80)

    for source in ['human', 'vlm']:
        erasure = analyze_soft_erasure(data, source)

        headers = ['Race', 'N', 'Edited Erasure%', 'Edited Mean', 'Preserved Erasure%', 'Preserved Mean']
        rows = []
        for race in RACES:
            ed = erasure[race].get('edited', {})
            pr = erasure[race].get('preserved', {})
            rows.append([
                race,
                ed.get('n', 0),
                f"{ed.get('soft_erasure_rate', 0):.1f}%",
                f"{ed.get('mean', 0):.2f}",
                f"{pr.get('soft_erasure_rate', 0):.1f}%",
                f"{pr.get('mean', 0):.2f}",
            ])
        print_table(f"Soft Erasure by Race ({source.upper()})", headers, rows)

    # =========================================================================
    # 4. SKIN TONE SHIFT ANALYSIS
    # =========================================================================
    print("\n" + "="*80)
    print("4. SKIN TONE SHIFT ANALYSIS (1-2=Darker, 3=Same, 4-5=Lighter)")
    print("="*80)

    for source in ['human', 'vlm']:
        skin = analyze_skin_tone_shift(data, source)

        headers = ['Race', 'N', 'Darker%', 'Same%', 'Lighter%', 'Mean']
        rows = []
        for race in RACES:
            ed = skin[race].get('edited', {})
            rows.append([
                race,
                ed.get('n', 0),
                f"{ed.get('darker_rate', 0):.1f}%",
                f"{ed.get('no_change_rate', 0):.1f}%",
                f"{ed.get('lighter_rate', 0):.1f}%",
                f"{ed.get('mean', 0):.2f}",
            ])
        print_table(f"Skin Tone Shift - Edited ({source.upper()})", headers, rows)

    # =========================================================================
    # 5. HUMAN vs VLM COMPARISON SUMMARY
    # =========================================================================
    print("\n" + "="*80)
    print("5. HUMAN vs VLM COMPARISON - KEY DISPARITIES")
    print("="*80)

    human_race = analyze_race_drift(data, 'human')
    vlm_race = analyze_race_drift(data, 'vlm')

    print("\n### Race Drift - Human vs VLM Agreement ###")
    headers = ['Race', 'Human Drift%', 'VLM Drift%', 'Difference']
    rows = []
    for race in RACES:
        h = human_race[race].get('edited', {}).get('any_drift_rate', 0)
        v = vlm_race[race].get('edited', {}).get('any_drift_rate', 0)
        rows.append([race, f"{h:.1f}%", f"{v:.1f}%", f"{v-h:+.1f}pp"])
    print_table("Race Drift Comparison (Edited)", headers, rows)

    human_erasure = analyze_soft_erasure(data, 'human')
    vlm_erasure = analyze_soft_erasure(data, 'vlm')

    print("\n### Soft Erasure - Human vs VLM Agreement ###")
    headers = ['Race', 'Human Erasure%', 'VLM Erasure%', 'Difference']
    rows = []
    for race in RACES:
        h = human_erasure[race].get('edited', {}).get('soft_erasure_rate', 0)
        v = vlm_erasure[race].get('edited', {}).get('soft_erasure_rate', 0)
        rows.append([race, f"{h:.1f}%", f"{v:.1f}%", f"{v-h:+.1f}pp"])
    print_table("Soft Erasure Comparison (Edited)", headers, rows)

    # =========================================================================
    # 6. KEY FINDINGS FOR PAPER
    # =========================================================================
    print("\n" + "="*80)
    print("6. KEY FINDINGS FOR PAPER")
    print("="*80)

    # Find max disparity races
    human_erasure_rates = {r: human_erasure[r].get('edited', {}).get('soft_erasure_rate', 0) for r in RACES}
    human_drift_rates = {r: human_race[r].get('edited', {}).get('any_drift_rate', 0) for r in RACES}

    max_erasure_race = max(human_erasure_rates, key=human_erasure_rates.get)
    min_erasure_race = min(human_erasure_rates, key=human_erasure_rates.get)

    max_drift_race = max(human_drift_rates, key=human_drift_rates.get)
    min_drift_race = min(human_drift_rates, key=human_drift_rates.get)

    print(f"""
SOFT ERASURE DISPARITY (Human Evaluation):
  Highest: {max_erasure_race} ({human_erasure_rates[max_erasure_race]:.1f}%)
  Lowest:  {min_erasure_race} ({human_erasure_rates[min_erasure_race]:.1f}%)
  Disparity: {human_erasure_rates[max_erasure_race] - human_erasure_rates[min_erasure_race]:.1f}pp

RACE DRIFT DISPARITY (Human Evaluation):
  Highest: {max_drift_race} ({human_drift_rates[max_drift_race]:.1f}%)
  Lowest:  {min_drift_race} ({human_drift_rates[min_drift_race]:.1f}%)
  Disparity: {human_drift_rates[max_drift_race] - human_drift_rates[min_drift_race]:.1f}pp
""")

    # Gender drift summary
    human_gender = analyze_gender_drift_direction(data, 'human')

    male_drifts = [human_gender['edited'][r].get('Male', {}).get('drift_rate', 0) for r in RACES if human_gender['edited'][r].get('Male')]
    female_drifts = [human_gender['edited'][r].get('Female', {}).get('drift_rate', 0) for r in RACES if human_gender['edited'][r].get('Female')]

    print(f"""
GENDER DRIFT BY SOURCE GENDER (Human Evaluation, Edited):
  Male subjects avg drift: {np.mean(male_drifts):.1f}%
  Female subjects avg drift: {np.mean(female_drifts):.1f}%
  Direction bias: {"Male→Female more common" if np.mean(male_drifts) > np.mean(female_drifts) else "Female→Male more common"}
""")

    print("\n" + "="*80)
    print("Analysis Complete!")
    print("="*80)

if __name__ == "__main__":
    main()
