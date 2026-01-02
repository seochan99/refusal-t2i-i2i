#!/usr/bin/env python3
"""
Test script to verify installation and setup.

Usage:
    python scripts/test_setup.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """Test all required imports."""
    print("Testing imports...")

    tests = {
        "PyTorch": lambda: __import__("torch"),
        "Transformers": lambda: __import__("transformers"),
        "Diffusers": lambda: __import__("diffusers"),
        "CLIP": lambda: __import__("clip"),
        "OpenAI": lambda: __import__("openai"),
        "Pillow": lambda: __import__("PIL"),
        "NumPy": lambda: __import__("numpy"),
        "Pandas": lambda: __import__("pandas"),
        "tqdm": lambda: __import__("tqdm"),
    }

    passed = 0
    failed = 0

    for name, import_func in tests.items():
        try:
            import_func()
            print(f"  ✓ {name}")
            passed += 1
        except ImportError as e:
            print(f"  ✗ {name}: {e}")
            failed += 1

    print(f"\nImport tests: {passed} passed, {failed} failed")
    return failed == 0


def test_gpu():
    """Test GPU availability."""
    print("\nTesting GPU...")

    try:
        import torch

        if torch.cuda.is_available():
            print(f"  ✓ CUDA available")
            print(f"  ✓ GPU: {torch.cuda.get_device_name(0)}")
            print(f"  ✓ CUDA version: {torch.version.cuda}")
            memory = torch.cuda.get_device_properties(0).total_memory / 1e9
            print(f"  ✓ GPU memory: {memory:.1f} GB")
            return True
        else:
            print("  ✗ CUDA not available (CPU mode)")
            return False
    except Exception as e:
        print(f"  ✗ GPU test failed: {e}")
        return False


def test_project_structure():
    """Test project structure."""
    print("\nTesting project structure...")

    required_dirs = [
        "acrb",
        "scripts",
        "data",
        "experiments",
    ]

    required_files = [
        "requirements.txt",
        "scripts/generate_all.py",
        "scripts/evaluate_all.py",
        "scripts/compute_results.py",
    ]

    project_root = Path(__file__).parent.parent

    passed = 0
    failed = 0

    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists() and dir_path.is_dir():
            print(f"  ✓ {dir_name}/")
            passed += 1
        else:
            print(f"  ✗ {dir_name}/ not found")
            failed += 1

    for file_name in required_files:
        file_path = project_root / file_name
        if file_path.exists() and file_path.is_file():
            print(f"  ✓ {file_name}")
            passed += 1
        else:
            print(f"  ✗ {file_name} not found")
            failed += 1

    print(f"\nStructure tests: {passed} passed, {failed} failed")
    return failed == 0


def test_acrb_imports():
    """Test ACRB package imports."""
    print("\nTesting ACRB package...")

    tests = {
        "base_prompts": lambda: __import__("acrb.prompt_generation.base_prompts", fromlist=["BasePromptGenerator"]),
        "models": lambda: __import__("acrb.models", fromlist=["T2IModelWrapper", "I2IModelWrapper"]),
        "metrics": lambda: __import__("acrb.metrics", fromlist=["RefusalDetector"]),
    }

    passed = 0
    failed = 0

    for name, import_func in tests.items():
        try:
            import_func()
            print(f"  ✓ acrb.{name}")
            passed += 1
        except ImportError as e:
            print(f"  ✗ acrb.{name}: {e}")
            failed += 1

    print(f"\nACRB tests: {passed} passed, {failed} failed")
    return failed == 0


def test_prompt_generation():
    """Test prompt generation."""
    print("\nTesting prompt generation...")

    try:
        from acrb.prompt_generation.base_prompts import BasePromptGenerator

        generator = BasePromptGenerator(seed=42)
        prompts = generator.sample_prompts(5)

        print(f"  ✓ Generated {len(prompts)} prompts")
        print(f"  ✓ Sample: {prompts[0].text[:60]}...")
        return True

    except Exception as e:
        print(f"  ✗ Prompt generation failed: {e}")
        return False


def main():
    """Run all tests."""
    print("="*70)
    print("   ACRB Setup Test")
    print("="*70)

    results = {
        "Imports": test_imports(),
        "GPU": test_gpu(),
        "Project Structure": test_project_structure(),
        "ACRB Package": test_acrb_imports(),
        "Prompt Generation": test_prompt_generation(),
    }

    print("\n" + "="*70)
    print("   Test Summary")
    print("="*70)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status:8s} {test_name}")

    all_passed = all(results.values())

    print("\n" + "="*70)
    if all_passed:
        print("   All tests passed! Ready to run experiments.")
    else:
        print("   Some tests failed. Please check the errors above.")
    print("="*70)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
