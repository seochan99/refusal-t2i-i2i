#!/usr/bin/env python3
"""
Minimal Step1X test - No thinking/reflection/RegionE
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PIL import Image
from models.step1x_wrapper import Step1XWrapper

def test_step1x_minimal():
    print("🧪 Testing Step1X with minimal config...")

    # Load a test image
    image_path = Path("data/source_images/final/Black/Black_Female_20s.jpg")
    if not image_path.exists():
        print(f"❌ Test image not found: {image_path}")
        return

    image = Image.open(image_path)
    print(f"✅ Loaded test image: {image.size}")

    # Create Step1X with minimal config
    model = Step1XWrapper(
        enable_thinking=False,
        enable_reflection=False,
        use_region_e=False
    )

    # Load model
    try:
        model.load()
        print("✅ Model loaded with minimal config")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return

    # Test minimal edit
    test_prompt = "Add sunglasses to this person"
    print(f"🧪 Testing with minimal prompt: {test_prompt}")

    try:
        result = model.edit(image, test_prompt)
        if result.success:
            print("🎉 SUCCESS! Step1X worked!")
            print(f"   Output image size: {result.output_image.size}")
            print(f"   Latency: {result.latency_ms:.1f}ms")
            return True
        else:
            print(f"❌ Edit failed: {result.refusal_type}")
            print(f"   Error: {result.error_message}")
            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_step1x_minimal()
    if success:
        print("\n✅ Step1X minimal test PASSED!")
    else:
        print("\n❌ Step1X minimal test FAILED!")
