#!/usr/bin/env python3
"""
Export all AMT evaluations from Firestore to CSV/JSON for analysis.

Usage:
    python scripts/export_evaluations.py

Requires:
    pip install firebase-admin pandas

Setup:
    1. Download service account key from Firebase Console
    2. Set environment variable: export GOOGLE_APPLICATION_CREDENTIALS="path/to/key.json"
    Or place the key at: survey/firebase-admin-key.json
"""

import os
import json
import pandas as pd
from datetime import datetime
from pathlib import Path

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:
    print("ERROR: firebase-admin not installed")
    print("Run: pip install firebase-admin pandas")
    exit(1)

# Config
PROJECT_ID = "acrb-e8cb4"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "exports"

def init_firebase():
    """Initialize Firebase Admin SDK"""
    if firebase_admin._apps:
        return firestore.client()

    # Try different credential sources
    key_paths = [
        Path(__file__).parent.parent / "firebase-admin-key.json",
        Path.home() / ".config" / "firebase" / f"{PROJECT_ID}-admin-key.json",
    ]

    cred = None
    for key_path in key_paths:
        if key_path.exists():
            print(f"Using credentials from: {key_path}")
            cred = credentials.Certificate(str(key_path))
            break

    if not cred:
        # Try default credentials (gcloud auth)
        try:
            cred = credentials.ApplicationDefault()
            print("Using application default credentials")
        except:
            print("ERROR: No credentials found")
            print("Options:")
            print("  1. Download service account key from Firebase Console")
            print("     Place at: survey/firebase-admin-key.json")
            print("  2. Or run: gcloud auth application-default login")
            exit(1)

    firebase_admin.initialize_app(cred, {'projectId': PROJECT_ID})
    return firestore.client()

def export_amt_evaluations(db):
    """Export amt_evaluations collection"""
    print("\n=== Exporting AMT Evaluations ===")

    docs = db.collection('amt_evaluations').stream()

    evaluations = []
    for doc in docs:
        data = doc.to_dict()
        # Convert timestamp to string
        if 'createdAt' in data and data['createdAt']:
            data['createdAt'] = data['createdAt'].isoformat()
        evaluations.append(data)

    print(f"Found {len(evaluations)} evaluations")

    if not evaluations:
        print("No evaluations to export")
        return None

    # Convert to DataFrame
    df = pd.DataFrame(evaluations)

    # Reorder columns for readability
    priority_cols = [
        'evalId', 'itemId', 'originalItemId', 'taskId',
        'userId', 'userEmail',
        'model', 'promptId', 'category', 'categoryName',
        'race', 'gender', 'age',
        'edited_edit_success', 'edited_skin_tone', 'edited_race_drift', 'edited_gender_drift', 'edited_age_drift',
        'preserved_edit_success', 'preserved_skin_tone', 'preserved_race_drift', 'preserved_gender_drift', 'preserved_age_drift',
        'editedShownFirst', 'duration_ms', 'createdAt'
    ]
    existing_cols = [c for c in priority_cols if c in df.columns]
    other_cols = [c for c in df.columns if c not in priority_cols]
    df = df[existing_cols + other_cols]

    return df

def export_task_completions(db):
    """Export amt_task_completions collection"""
    print("\n=== Exporting Task Completions ===")

    docs = db.collection('amt_task_completions').stream()

    completions = []
    for doc in docs:
        data = doc.to_dict()
        if 'completedAt' in data and data['completedAt']:
            data['completedAt'] = data['completedAt'].isoformat()
        completions.append(data)

    print(f"Found {len(completions)} task completions")

    if not completions:
        return None

    return pd.DataFrame(completions)

def generate_summary(df):
    """Generate summary statistics"""
    print("\n=== Summary Statistics ===")

    print(f"\nTotal evaluations: {len(df)}")
    print(f"Unique users: {df['userId'].nunique()}")
    print(f"Unique items evaluated: {df['itemId'].nunique()}")

    if 'model' in df.columns:
        print(f"\nBy Model:")
        print(df['model'].value_counts().to_string())

    if 'category' in df.columns:
        print(f"\nBy Category:")
        print(df['category'].value_counts().to_string())

    if 'race' in df.columns:
        print(f"\nBy Race:")
        print(df['race'].value_counts().to_string())

    # Average scores
    score_cols = [c for c in df.columns if 'edit_success' in c or 'skin_tone' in c or 'drift' in c]
    if score_cols:
        print(f"\nAverage Scores:")
        for col in score_cols:
            print(f"  {col}: {df[col].mean():.2f}")

def main():
    print("=" * 60)
    print("AMT Evaluation Data Export")
    print("=" * 60)

    # Initialize Firebase
    db = init_firebase()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Export evaluations
    eval_df = export_amt_evaluations(db)
    if eval_df is not None:
        # Save as CSV
        csv_path = OUTPUT_DIR / f"amt_evaluations_{timestamp}.csv"
        eval_df.to_csv(csv_path, index=False)
        print(f"Saved: {csv_path}")

        # Save as JSON
        json_path = OUTPUT_DIR / f"amt_evaluations_{timestamp}.json"
        eval_df.to_json(json_path, orient='records', indent=2)
        print(f"Saved: {json_path}")

        # Generate summary
        generate_summary(eval_df)

    # Export task completions
    comp_df = export_task_completions(db)
    if comp_df is not None:
        csv_path = OUTPUT_DIR / f"task_completions_{timestamp}.csv"
        comp_df.to_csv(csv_path, index=False)
        print(f"Saved: {csv_path}")

    print("\n" + "=" * 60)
    print("Export complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()
