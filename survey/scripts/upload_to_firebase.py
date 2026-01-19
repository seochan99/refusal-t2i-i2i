#!/usr/bin/env python3
"""
Upload survey images to Firebase Storage
Only uploads images referenced in amt_items.json
"""

import json
import os
import subprocess
from pathlib import Path

# Config
PROJECT_ID = "acrb-e8cb4"
BUCKET = f"{PROJECT_ID}.firebasestorage.app"
STORAGE_PREFIX = "i2i-survey"

def get_required_images():
    """Extract all image paths from amt_items.json"""
    with open('public/data/amt_items.json') as f:
        data = json.load(f)

    images = set()
    for item in data['items']:
        images.add(item['sourceImageUrl'])
        images.add(item['editedImageUrl'])
        images.add(item['preservedImageUrl'])

    return sorted(images)

def upload_images():
    """Upload images to Firebase Storage using gsutil"""
    images = get_required_images()
    print(f"Found {len(images)} unique images to upload")

    # Check if gsutil is available
    try:
        subprocess.run(['gsutil', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: gsutil not found. Install Google Cloud SDK:")
        print("  brew install google-cloud-sdk")
        print("  gcloud auth login")
        return False

    uploaded = 0
    failed = []

    for i, img_url in enumerate(images):
        local_path = f"public{img_url}"

        if not os.path.exists(local_path):
            print(f"  SKIP (not found): {local_path}")
            failed.append(local_path)
            continue

        # Storage path: remove leading /images/ and add prefix
        storage_path = img_url.replace('/images/', f'{STORAGE_PREFIX}/')
        gs_url = f"gs://{BUCKET}/{storage_path}"

        try:
            result = subprocess.run(
                ['gsutil', '-q', 'cp', local_path, gs_url],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                uploaded += 1
                if uploaded % 50 == 0:
                    print(f"  Uploaded {uploaded}/{len(images)}...")
            else:
                print(f"  FAIL: {local_path} -> {result.stderr}")
                failed.append(local_path)
        except Exception as e:
            print(f"  ERROR: {local_path} -> {e}")
            failed.append(local_path)

    print(f"\nDone! Uploaded {uploaded}/{len(images)} images")
    if failed:
        print(f"Failed: {len(failed)} files")

    return len(failed) == 0

def update_json_urls():
    """Update amt_items.json with Firebase Storage URLs"""
    base_url = f"https://firebasestorage.googleapis.com/v0/b/{BUCKET}/o"

    with open('public/data/amt_items.json') as f:
        data = json.load(f)

    for item in data['items']:
        for key in ['sourceImageUrl', 'editedImageUrl', 'preservedImageUrl']:
            old_url = item[key]
            # /images/source/... -> i2i-survey/source/...
            storage_path = old_url.replace('/images/', f'{STORAGE_PREFIX}/')
            # URL encode the path
            encoded_path = storage_path.replace('/', '%2F')
            item[key] = f"{base_url}/{encoded_path}?alt=media"

    # Save updated JSON
    with open('public/data/amt_items.json', 'w') as f:
        json.dump(data, f, indent=2)

    print("Updated amt_items.json with Firebase Storage URLs")

def main():
    os.chdir(Path(__file__).parent.parent)

    print("=" * 50)
    print("Firebase Storage Image Uploader")
    print("=" * 50)
    print(f"Bucket: {BUCKET}")
    print(f"Prefix: {STORAGE_PREFIX}")
    print()

    # Step 1: Upload
    print("Step 1: Uploading images...")
    if not upload_images():
        print("Some uploads failed. Fix and retry.")
        return

    # Step 2: Update JSON
    print("\nStep 2: Updating JSON URLs...")
    update_json_urls()

    print("\nAll done!")

if __name__ == '__main__':
    main()
