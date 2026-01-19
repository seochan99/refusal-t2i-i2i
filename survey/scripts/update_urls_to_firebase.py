#!/usr/bin/env python3
"""
Update amt_items.json URLs to use Firebase Storage
Run this AFTER upload_to_firebase.sh completes
"""

import json
from pathlib import Path
import urllib.parse

# Config
BUCKET = "acrb-e8cb4.firebasestorage.app"
STORAGE_PREFIX = "i2i-survey"

def update_json_urls():
    """Update JSON files with Firebase Storage URLs"""

    json_files = [
        Path(__file__).parent.parent / 'public/data/amt_items.json',
        Path(__file__).parent.parent / 'public/data/exp1_amt_sampled.json'
    ]

    base_url = f"https://firebasestorage.googleapis.com/v0/b/{BUCKET}/o"

    for json_path in json_files:
        if not json_path.exists():
            print(f"Skipping {json_path.name} - file not found")
            continue

        print(f"\nUpdating {json_path.name}...")

        with open(json_path) as f:
            data = json.load(f)

        updated_count = 0

        # Handle different JSON structures
        if 'items' in data:
            items = data['items']
        elif 'tasks' in data:
            items = []
            for task in data['tasks']:
                if 'items' in task:
                    items.extend(task['items'])
        else:
            print(f"Unknown structure in {json_path.name}")
            continue

        for item in items:
            for key in ['sourceImageUrl', 'outputImageUrl']:
                if key not in item:
                    continue

                old_url = item[key]

                # Skip if already a Firebase URL
                if 'firebasestorage.googleapis.com' in old_url:
                    continue

                # /images/source/... -> i2i-survey/source/...
                storage_path = old_url.replace('/images/', f'{STORAGE_PREFIX}/')

                # URL encode the path (but keep / as is first, then encode)
                encoded_path = urllib.parse.quote(storage_path, safe='')

                item[key] = f"{base_url}/{encoded_path}?alt=media"
                updated_count += 1

        # Save updated JSON
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"Updated {updated_count} URLs in {json_path.name}")

        # Show sample
        if items:
            sample_key = 'sourceImageUrl' if 'sourceImageUrl' in items[0] else 'outputImageUrl'
            if sample_key in items[0]:
                print(f"Sample {sample_key}:")
                print(items[0][sample_key][:100] + "...")

if __name__ == '__main__':
    update_json_urls()
