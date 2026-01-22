#!/usr/bin/env python3
"""Generate Appendix K: Massive image mosaic of representative examples."""

import os
import random
from pathlib import Path
from PIL import Image
import math

# Correct image path
DATA_DIR = Path("/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/survey/public/images")
OUTPUT_DIR = Path("/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/paper/IJCAI_ECAI_26_I2I_Bias___Appendix/assets")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def collect_images():
    """Collect all edited images from exp1_sampling_b_d."""
    images = {'flux': [], 'step1x': [], 'qwen': []}

    exp1_dir = DATA_DIR / "exp1_sampling_b_d"

    for model in ['flux', 'step1x', 'qwen']:
        model_dir = exp1_dir / model
        if model_dir.exists():
            for img_path in model_dir.rglob("*.png"):
                # Verify file exists and is readable
                if img_path.exists() and img_path.stat().st_size > 0:
                    images[model].append(img_path)

    return images

def create_mosaic(image_paths, output_path, cols=20, thumb_size=80, max_images=400):
    """Create a dense mosaic grid with no gaps."""
    # Filter to valid images only
    valid_images = []
    for img_path in image_paths:
        try:
            if img_path.exists() and img_path.stat().st_size > 1000:  # At least 1KB
                valid_images.append(img_path)
        except:
            continue

    if len(valid_images) > max_images:
        valid_images = random.sample(valid_images, max_images)

    rows = math.ceil(len(valid_images) / cols)

    # Create canvas
    canvas_width = cols * thumb_size
    canvas_height = rows * thumb_size
    canvas = Image.new('RGB', (canvas_width, canvas_height), (255, 255, 255))

    successful = 0
    for idx, img_path in enumerate(valid_images):
        try:
            img = Image.open(img_path)
            img = img.convert('RGB')
            img = img.resize((thumb_size, thumb_size), Image.Resampling.LANCZOS)

            row = idx // cols
            col = idx % cols
            x = col * thumb_size
            y = row * thumb_size

            canvas.paste(img, (x, y))
            successful += 1
        except Exception as e:
            continue

    canvas.save(output_path, quality=95, dpi=(300, 300))
    print(f"Saved: {output_path} ({successful} images, {cols}x{rows} grid)")
    return canvas

def create_single_column_mosaic(image_paths, output_path, target_width=1600, thumb_size=40, max_images=600):
    """Create a dense mosaic sized for single column (textwidth)."""
    # Filter valid images
    valid_images = []
    for img_path in image_paths:
        try:
            if img_path.exists() and img_path.stat().st_size > 1000:
                valid_images.append(img_path)
        except:
            continue

    if len(valid_images) > max_images:
        valid_images = random.sample(valid_images, max_images)

    cols = target_width // thumb_size
    rows = math.ceil(len(valid_images) / cols)

    canvas_width = cols * thumb_size
    canvas_height = rows * thumb_size
    canvas = Image.new('RGB', (canvas_width, canvas_height), (255, 255, 255))

    successful = 0
    for idx, img_path in enumerate(valid_images):
        try:
            img = Image.open(img_path)
            img = img.convert('RGB')
            img = img.resize((thumb_size, thumb_size), Image.Resampling.LANCZOS)

            row = idx // cols
            col = idx % cols
            x = col * thumb_size
            y = row * thumb_size

            canvas.paste(img, (x, y))
            successful += 1
        except:
            continue

    canvas.save(output_path, quality=95, dpi=(300, 300))
    print(f"Saved: {output_path} ({successful} images, {cols}x{rows} grid, width={canvas_width}px)")
    return canvas

def main():
    print("Collecting images from survey/public/images...")
    images_by_model = collect_images()

    for model, imgs in images_by_model.items():
        print(f"  {model}: {len(imgs)} images")

    random.seed(42)

    # Combine all images
    all_images = []
    for model_imgs in images_by_model.values():
        all_images.extend(model_imgs)
    print(f"  Total: {len(all_images)} images")

    # 1. Dense mosaic - single column width (600 images, 40x15 grid)
    print("\n1. Creating dense mosaic for single column...")
    create_single_column_mosaic(
        all_images,
        OUTPUT_DIR / "appendix_k_dense_mosaic.png",
        target_width=1600,
        thumb_size=40,
        max_images=600
    )

    # 2. Giant mosaic (500 images, larger thumbnails)
    print("\n2. Creating giant mosaic...")
    create_single_column_mosaic(
        all_images,
        OUTPUT_DIR / "appendix_k_giant_mosaic.png",
        target_width=1600,
        thumb_size=50,
        max_images=480
    )

    # 3. Super dense (800 images, tiny thumbnails)
    print("\n3. Creating super dense mosaic (800 images)...")
    create_single_column_mosaic(
        all_images,
        OUTPUT_DIR / "appendix_k_super_dense.png",
        target_width=1600,
        thumb_size=32,
        max_images=800
    )

    print("\nDone! Generated mosaics in:", OUTPUT_DIR)

if __name__ == "__main__":
    main()
