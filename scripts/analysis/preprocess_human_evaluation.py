#!/usr/bin/env python3
"""
Human Evaluation Data Preprocessing Script

Preprocesses AMT evaluation data from Firebase export into separate files
for preserved and edited evaluations, both raw (1,500 records each) and
averaged across 3 workers (500 records each).

Input:
    - /Users/chan/Downloads/_amt_evaluations.json (Firebase export)

Output (6 files):
    - data/analysis/human_survey_preserved_result.json (1,500)
    - data/analysis/human_survey_preserved_result.csv (1,500)
    - data/analysis/human_survey_edited_result.json (1,500)
    - data/analysis/human_survey_edited_result.csv (1,500)
    - data/analysis/human_survey_sample_avg_preserved_evaluation.jsonl (500)
    - data/analysis/human_survey_sample_avg_edited_evaluation.jsonl (500)
"""

import json
import csv
from pathlib import Path
from collections import defaultdict
from statistics import mean
from typing import Dict, List, Any, Tuple


def load_data(filepath: str) -> List[Dict[str, Any]]:
    """Load JSON data from file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def filter_complete_users(data: List[Dict[str, Any]], required_count: int = 50) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Filter to users who completed exactly required_count items.

    Returns:
        - Filtered data (only records from complete users)
        - Dictionary of {prolificPid: count}
    """
    # Count items per user
    user_counts = defaultdict(int)
    for record in data:
        pid = record.get('prolificPid')
        if pid:
            user_counts[pid] += 1

    # Find users with exactly required_count
    complete_users = {pid for pid, count in user_counts.items() if count == required_count}

    # Filter data
    filtered_data = [r for r in data if r.get('prolificPid') in complete_users]

    return filtered_data, dict(user_counts)


def validate_task_worker_mapping(data: List[Dict[str, Any]]) -> Dict[int, List[str]]:
    """
    Validate that each task has exactly 3 workers.

    Returns:
        - Dictionary of {taskId: [prolificPid1, prolificPid2, prolificPid3]}
    """
    task_workers = defaultdict(set)

    for record in data:
        task_id = record.get('taskId')
        pid = record.get('prolificPid')
        if task_id is not None and pid:
            task_workers[task_id].add(pid)

    # Convert sets to lists
    return {task_id: list(workers) for task_id, workers in sorted(task_workers.items())}


def extract_preserved_records(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract preserved evaluation fields from each record.
    """
    preserved_records = []

    for record in data:
        preserved_record = {
            # Identifiers
            'evalId': record.get('evalId'),
            'itemId': record.get('itemId'),
            'originalItemId': record.get('originalItemId'),

            # Worker info
            'prolificPid': record.get('prolificPid'),
            'taskId': record.get('taskId'),

            # Image metadata
            'race': record.get('race'),
            'gender': record.get('gender'),
            'age': record.get('age'),
            'model': record.get('model'),
            'category': record.get('category'),
            'categoryName': record.get('categoryName'),
            'promptId': record.get('promptId'),

            # Image URLs
            'sourceImageUrl': record.get('sourceImageUrl'),
            'preservedImageUrl': record.get('preservedImageUrl'),

            # Evaluation scores (preserved)
            'edit_success': record.get('preserved_edit_success'),
            'skin_tone': record.get('preserved_skin_tone'),
            'race_drift': record.get('preserved_race_drift'),
            'gender_drift': record.get('preserved_gender_drift'),
            'age_drift': record.get('preserved_age_drift'),

            # Timing
            'duration_ms': record.get('duration_ms'),
            'createdAt': record.get('createdAt'),
        }
        preserved_records.append(preserved_record)

    return preserved_records


def extract_edited_records(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract edited evaluation fields from each record.
    """
    edited_records = []

    for record in data:
        edited_record = {
            # Identifiers
            'evalId': record.get('evalId'),
            'itemId': record.get('itemId'),
            'originalItemId': record.get('originalItemId'),

            # Worker info
            'prolificPid': record.get('prolificPid'),
            'taskId': record.get('taskId'),

            # Image metadata
            'race': record.get('race'),
            'gender': record.get('gender'),
            'age': record.get('age'),
            'model': record.get('model'),
            'category': record.get('category'),
            'categoryName': record.get('categoryName'),
            'promptId': record.get('promptId'),

            # Image URLs
            'sourceImageUrl': record.get('sourceImageUrl'),
            'editedImageUrl': record.get('editedImageUrl'),

            # Evaluation scores (edited)
            'edit_success': record.get('edited_edit_success'),
            'skin_tone': record.get('edited_skin_tone'),
            'race_drift': record.get('edited_race_drift'),
            'gender_drift': record.get('edited_gender_drift'),
            'age_drift': record.get('edited_age_drift'),

            # Timing
            'duration_ms': record.get('duration_ms'),
            'createdAt': record.get('createdAt'),
        }
        edited_records.append(edited_record)

    return edited_records


def compute_averages(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Compute 3-worker averages for each unique itemId.

    Groups records by itemId and computes mean scores across workers.
    """
    # Group by itemId
    item_groups = defaultdict(list)
    for record in records:
        item_id = record.get('itemId')
        if item_id:
            item_groups[item_id].append(record)

    averaged_records = []
    score_fields = ['edit_success', 'skin_tone', 'race_drift', 'gender_drift', 'age_drift']

    for item_id in sorted(item_groups.keys()):
        group = item_groups[item_id]

        # Use first record as template for metadata
        template = group[0]

        avg_record = {
            # Identifiers
            'itemId': item_id,
            'originalItemId': template.get('originalItemId'),

            # Image metadata
            'race': template.get('race'),
            'gender': template.get('gender'),
            'age': template.get('age'),
            'model': template.get('model'),
            'category': template.get('category'),
            'categoryName': template.get('categoryName'),
            'promptId': template.get('promptId'),

            # Number of workers who evaluated this item
            'n_workers': len(group),

            # Worker IDs
            'worker_ids': [r.get('prolificPid') for r in group],
        }

        # Compute average scores
        for field in score_fields:
            scores = [r.get(field) for r in group if r.get(field) is not None]
            if scores:
                avg_record[f'{field}_avg'] = round(mean(scores), 3)
                avg_record[f'{field}_scores'] = scores
            else:
                avg_record[f'{field}_avg'] = None
                avg_record[f'{field}_scores'] = []

        averaged_records.append(avg_record)

    return averaged_records


def save_json(data: List[Dict[str, Any]], filepath: Path):
    """Save data as JSON."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Saved JSON: {filepath} ({len(data)} records)")


def save_csv(data: List[Dict[str, Any]], filepath: Path):
    """Save data as CSV."""
    if not data:
        print(f"  Warning: No data to save to {filepath}")
        return

    # Get all keys from first record
    fieldnames = list(data[0].keys())

    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    print(f"  Saved CSV: {filepath} ({len(data)} records)")


def save_jsonl(data: List[Dict[str, Any]], filepath: Path):
    """Save data as JSONL (one JSON object per line)."""
    with open(filepath, 'w') as f:
        for record in data:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    print(f"  Saved JSONL: {filepath} ({len(data)} records)")


def main():
    """Main preprocessing pipeline."""
    # Paths
    input_path = Path("/Users/chan/Downloads/_amt_evaluations.json")
    output_dir = Path("/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/data/analysis")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Human Evaluation Data Preprocessing")
    print("=" * 60)

    # Step 1: Load raw data
    print("\n[Step 1] Loading raw data...")
    raw_data = load_data(input_path)
    print(f"  Total records loaded: {len(raw_data)}")

    # Step 2: Filter complete users
    print("\n[Step 2] Filtering complete users (50 items each)...")
    filtered_data, user_counts = filter_complete_users(raw_data, required_count=50)

    complete_users = [pid for pid, count in user_counts.items() if count == 50]
    incomplete_users = [(pid, count) for pid, count in user_counts.items() if count != 50]

    print(f"  Complete users (50 items): {len(complete_users)}")
    print(f"  Incomplete users: {len(incomplete_users)}")
    if incomplete_users:
        print("  Incomplete user counts:")
        for pid, count in sorted(incomplete_users, key=lambda x: x[1], reverse=True)[:5]:
            print(f"    {pid[:12]}...: {count} items")
        if len(incomplete_users) > 5:
            print(f"    ... and {len(incomplete_users) - 5} more")

    print(f"  Filtered records: {len(filtered_data)}")

    # Validation check
    expected_records = 30 * 50  # 30 workers × 50 items each
    if len(filtered_data) != expected_records:
        print(f"  WARNING: Expected {expected_records} records, got {len(filtered_data)}")

    # Step 3: Validate task-worker mapping
    print("\n[Step 3] Validating task-worker mapping...")
    task_workers = validate_task_worker_mapping(filtered_data)

    print(f"  Tasks found: {len(task_workers)}")
    all_valid = True
    for task_id, workers in sorted(task_workers.items()):
        status = "OK" if len(workers) == 3 else "WARN"
        if len(workers) != 3:
            all_valid = False
        print(f"    Task {task_id}: {len(workers)} workers [{status}]")

    if all_valid:
        print("  All tasks have exactly 3 workers")

    # Step 4: Extract preserved records
    print("\n[Step 4] Extracting preserved evaluation records...")
    preserved_records = extract_preserved_records(filtered_data)
    print(f"  Preserved records: {len(preserved_records)}")

    # Step 5: Extract edited records
    print("\n[Step 5] Extracting edited evaluation records...")
    edited_records = extract_edited_records(filtered_data)
    print(f"  Edited records: {len(edited_records)}")

    # Step 6: Save raw results
    print("\n[Step 6] Saving raw results...")
    save_json(preserved_records, output_dir / "human_survey_preserved_result.json")
    save_csv(preserved_records, output_dir / "human_survey_preserved_result.csv")
    save_json(edited_records, output_dir / "human_survey_edited_result.json")
    save_csv(edited_records, output_dir / "human_survey_edited_result.csv")

    # Step 7: Compute averages
    print("\n[Step 7] Computing 3-worker averages...")
    preserved_avg = compute_averages(preserved_records)
    edited_avg = compute_averages(edited_records)
    print(f"  Preserved averaged records: {len(preserved_avg)}")
    print(f"  Edited averaged records: {len(edited_avg)}")

    # Validate average counts
    if len(preserved_avg) != 500:
        print(f"  WARNING: Expected 500 preserved averages, got {len(preserved_avg)}")
    if len(edited_avg) != 500:
        print(f"  WARNING: Expected 500 edited averages, got {len(edited_avg)}")

    # Check worker counts per item
    worker_count_issues = []
    for record in preserved_avg + edited_avg:
        if record['n_workers'] != 3:
            worker_count_issues.append((record['itemId'], record['n_workers']))

    if worker_count_issues:
        print(f"  WARNING: {len(worker_count_issues)} items don't have exactly 3 workers")
        for item_id, count in worker_count_issues[:5]:
            print(f"    {item_id}: {count} workers")
    else:
        print("  All items have exactly 3 worker evaluations")

    # Step 8: Save averaged results
    print("\n[Step 8] Saving averaged results...")
    save_jsonl(preserved_avg, output_dir / "human_survey_sample_avg_preserved_evaluation.jsonl")
    save_jsonl(edited_avg, output_dir / "human_survey_sample_avg_edited_evaluation.jsonl")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Input: {input_path}")
    print(f"Output directory: {output_dir}")
    print()
    print("Generated files:")
    print(f"  1. human_survey_preserved_result.json    ({len(preserved_records)} records)")
    print(f"  2. human_survey_preserved_result.csv     ({len(preserved_records)} records)")
    print(f"  3. human_survey_edited_result.json       ({len(edited_records)} records)")
    print(f"  4. human_survey_edited_result.csv        ({len(edited_records)} records)")
    print(f"  5. human_survey_sample_avg_preserved_evaluation.jsonl ({len(preserved_avg)} records)")
    print(f"  6. human_survey_sample_avg_edited_evaluation.jsonl    ({len(edited_avg)} records)")
    print()
    print("Data quality:")
    print(f"  - Complete users: {len(complete_users)}/30 expected")
    print(f"  - Tasks with 3 workers: {sum(1 for w in task_workers.values() if len(w) == 3)}/10")
    print(f"  - Items with 3 evaluations: {500 - len(worker_count_issues)}/500")


if __name__ == "__main__":
    main()
