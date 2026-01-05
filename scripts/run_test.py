#!/usr/bin/env python3
"""
ACRB Quick Test Script

Tests 1 closed-source model and 1 open-source model with minimal samples
to verify the server setup is working correctly.

Paper: IJCAI-ECAI 2026

Usage:
    # Quick test (default: 5 samples each)
    python scripts/run_test.py

    # Test with specific models
    python scripts/run_test.py --closed-model gpt_image_1_5 --open-model flux_2_dev

    # Test only T2I
    python scripts/run_test.py --t2i-only

    # Test only I2I
    python scripts/run_test.py --i2i-only --dataset data/ffhq

    # Verbose output
    python scripts/run_test.py --verbose
"""

import argparse
import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import subprocess

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def parse_args():
    parser = argparse.ArgumentParser(
        description="Quick test to verify ACRB pipeline on server"
    )
    parser.add_argument(
        "--samples", type=int, default=5,
        help="Number of test samples (default: 5)"
    )
    parser.add_argument(
        "--closed-model", type=str, default="gpt_image_1_5",
        help="Closed source model to test (default: gpt_image_1_5)"
    )
    parser.add_argument(
        "--open-model", type=str, default="flux_2_dev",
        help="Open source model to test (default: flux_2_dev)"
    )
    parser.add_argument(
        "--t2i-only", action="store_true",
        help="Test only T2I mode"
    )
    parser.add_argument(
        "--i2i-only", action="store_true",
        help="Test only I2I mode"
    )
    parser.add_argument(
        "--dataset", type=str, default=None,
        help="Dataset path for I2I testing"
    )
    parser.add_argument(
        "--skip-closed", action="store_true",
        help="Skip closed source model test (if no API key)"
    )
    parser.add_argument(
        "--skip-open", action="store_true",
        help="Skip open source model test"
    )
    parser.add_argument(
        "--output", type=str, default="experiments/test",
        help="Output directory for test results"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--timeout", type=int, default=600,
        help="Timeout per test in seconds (default: 600)"
    )
    return parser.parse_args()


def check_environment() -> Dict:
    """Check environment setup and dependencies."""
    checks = {
        "python_version": sys.version.split()[0],
        "project_root": str(Path(__file__).parent.parent),
        "api_keys": {},
        "dependencies": {},
        "gpu_available": False
    }

    # Check API keys
    checks["api_keys"] = {
        "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
        "GOOGLE_API_KEY": bool(os.getenv("GOOGLE_API_KEY")),
        "BYTEPLUS_API_KEY": bool(os.getenv("BYTEPLUS_API_KEY")),
        "ACRB_LLM_API_KEY": bool(os.getenv("ACRB_LLM_API_KEY") or os.getenv("GOOGLE_API_KEY")),
    }

    # Check key dependencies
    try:
        import torch
        checks["dependencies"]["torch"] = torch.__version__
        checks["gpu_available"] = torch.cuda.is_available()
        if checks["gpu_available"]:
            checks["gpu_name"] = torch.cuda.get_device_name(0)
            checks["gpu_memory"] = f"{torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB"
    except ImportError:
        checks["dependencies"]["torch"] = "NOT INSTALLED"

    try:
        import transformers
        checks["dependencies"]["transformers"] = transformers.__version__
    except ImportError:
        checks["dependencies"]["transformers"] = "NOT INSTALLED"

    try:
        import diffusers
        checks["dependencies"]["diffusers"] = diffusers.__version__
    except ImportError:
        checks["dependencies"]["diffusers"] = "NOT INSTALLED"

    try:
        import mediapipe
        checks["dependencies"]["mediapipe"] = mediapipe.__version__
    except ImportError:
        checks["dependencies"]["mediapipe"] = "NOT INSTALLED"

    try:
        from acrb import config
        checks["dependencies"]["acrb"] = "OK"
        checks["acrb_models"] = len(config.MODELS['t2i'])
    except ImportError as e:
        checks["dependencies"]["acrb"] = f"ERROR: {e}"

    return checks


def run_test(
    model: str,
    mode: str,
    samples: int,
    output_dir: str,
    dataset: Optional[str] = None,
    verbose: bool = False,
    timeout: int = 600
) -> Dict:
    """Run a single test."""

    cmd = [
        "python", "scripts/run_audit.py",
        "--model", model.replace('_', '-'),
        "--mode", mode,
        "--samples", str(samples),
        "--attributes", "culture", "gender",  # Minimal attributes for quick test
        "--output", output_dir,
        "--seed", "42",
    ]

    if mode == "i2i" and dataset:
        cmd.extend(["--dataset", dataset])

    if verbose:
        cmd.append("--verbose")

    test_name = f"{model}_{mode}"
    print(f"\n{'='*50}")
    print(f"TEST: {test_name}")
    print(f"{'='*50}")
    print(f"Command: {' '.join(cmd)}")

    start_time = time.time()

    try:
        if verbose:
            # Stream output in verbose mode
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            output_lines = []
            for line in iter(process.stdout.readline, ''):
                print(f"  {line.rstrip()}")
                output_lines.append(line)

            process.wait(timeout=timeout)
            returncode = process.returncode
            stdout = ''.join(output_lines)
            stderr = ""
        else:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            returncode = result.returncode
            stdout = result.stdout
            stderr = result.stderr

        elapsed = time.time() - start_time

        if returncode == 0:
            status = "PASSED"
            print(f"\n  Status: {status} ({elapsed:.1f}s)")
        else:
            status = "FAILED"
            print(f"\n  Status: {status} ({elapsed:.1f}s)")
            if stderr:
                print(f"  Error: {stderr[-300:]}")

        return {
            "test": test_name,
            "model": model,
            "mode": mode,
            "status": status,
            "elapsed_seconds": round(elapsed, 1),
            "returncode": returncode,
            "error": stderr[-500:] if stderr and returncode != 0 else None
        }

    except subprocess.TimeoutExpired:
        print(f"\n  Status: TIMEOUT (>{timeout}s)")
        return {
            "test": test_name,
            "model": model,
            "mode": mode,
            "status": "TIMEOUT",
            "timeout": timeout
        }
    except Exception as e:
        print(f"\n  Status: ERROR - {e}")
        return {
            "test": test_name,
            "model": model,
            "mode": mode,
            "status": "ERROR",
            "error": str(e)
        }


def main():
    args = parse_args()

    print("\n" + "="*70)
    print("   ACRB Quick Test Suite")
    print("   Server Verification")
    print("="*70)

    # Check environment
    print("\n1. ENVIRONMENT CHECK")
    print("-" * 40)
    env_check = check_environment()

    print(f"  Python: {env_check['python_version']}")
    print(f"  Project Root: {env_check['project_root']}")
    print(f"  GPU Available: {env_check['gpu_available']}")
    if env_check['gpu_available']:
        print(f"    - {env_check.get('gpu_name', 'Unknown')}")
        print(f"    - Memory: {env_check.get('gpu_memory', 'Unknown')}")

    print("\n  API Keys:")
    for key, available in env_check['api_keys'].items():
        status = "OK" if available else "MISSING"
        print(f"    - {key}: {status}")

    print("\n  Dependencies:")
    for dep, version in env_check['dependencies'].items():
        print(f"    - {dep}: {version}")

    # Determine what to test
    tests_to_run = []

    if not args.i2i_only:
        # T2I tests
        if not args.skip_closed:
            tests_to_run.append({
                "model": args.closed_model,
                "mode": "t2i",
                "type": "closed"
            })
        if not args.skip_open:
            tests_to_run.append({
                "model": args.open_model,
                "mode": "t2i",
                "type": "open"
            })

    if not args.t2i_only and args.dataset:
        # I2I tests
        if not args.skip_closed:
            tests_to_run.append({
                "model": args.closed_model,
                "mode": "i2i",
                "type": "closed"
            })
        if not args.skip_open:
            tests_to_run.append({
                "model": args.open_model,
                "mode": "i2i",
                "type": "open"
            })

    if not tests_to_run:
        print("\nNo tests to run. Check arguments.")
        sys.exit(1)

    print(f"\n2. TESTS TO RUN ({len(tests_to_run)})")
    print("-" * 40)
    for t in tests_to_run:
        print(f"  - {t['model']} ({t['mode']}, {t['type']})")

    # Check API key availability for closed models
    for test in tests_to_run:
        if test['type'] == 'closed':
            if test['model'] == 'gpt_image_1_5' and not env_check['api_keys']['OPENAI_API_KEY']:
                print(f"\nWARNING: Skipping {test['model']} - OPENAI_API_KEY not set")
                test['skip'] = True
            elif test['model'] == 'imagen_3' and not env_check['api_keys']['GOOGLE_API_KEY']:
                print(f"\nWARNING: Skipping {test['model']} - GOOGLE_API_KEY not set")
                test['skip'] = True

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run tests
    print(f"\n3. RUNNING TESTS")
    print("-" * 40)

    results = []
    for test in tests_to_run:
        if test.get('skip'):
            results.append({
                "test": f"{test['model']}_{test['mode']}",
                "status": "SKIPPED",
                "reason": "missing_api_key"
            })
            continue

        result = run_test(
            model=test['model'],
            mode=test['mode'],
            samples=args.samples,
            output_dir=str(output_dir),
            dataset=args.dataset,
            verbose=args.verbose,
            timeout=args.timeout
        )
        results.append(result)

    # Summary
    print("\n" + "="*70)
    print("   TEST RESULTS SUMMARY")
    print("="*70)

    passed = sum(1 for r in results if r['status'] == 'PASSED')
    failed = sum(1 for r in results if r['status'] == 'FAILED')
    skipped = sum(1 for r in results if r['status'] == 'SKIPPED')
    timeout = sum(1 for r in results if r['status'] == 'TIMEOUT')
    errors = sum(1 for r in results if r['status'] == 'ERROR')

    for r in results:
        status_icon = {
            'PASSED': '[OK]',
            'FAILED': '[FAIL]',
            'SKIPPED': '[SKIP]',
            'TIMEOUT': '[TIME]',
            'ERROR': '[ERR]'
        }.get(r['status'], '[?]')

        elapsed = r.get('elapsed_seconds', '-')
        print(f"  {status_icon} {r['test']}: {r['status']} ({elapsed}s)")

    print(f"\n  Total: {len(results)} tests")
    print(f"    Passed:  {passed}")
    print(f"    Failed:  {failed}")
    print(f"    Skipped: {skipped}")
    print(f"    Timeout: {timeout}")
    print(f"    Errors:  {errors}")

    # Save results
    test_report = {
        "timestamp": datetime.now().isoformat(),
        "environment": env_check,
        "tests_run": len(results),
        "passed": passed,
        "failed": failed,
        "results": results
    }

    report_path = output_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w') as f:
        json.dump(test_report, f, indent=2)

    print(f"\n  Report saved to: {report_path}")

    # Exit code
    if failed > 0 or errors > 0:
        print("\n  RESULT: Some tests failed!")
        sys.exit(1)
    else:
        print("\n  RESULT: All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
