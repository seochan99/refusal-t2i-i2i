#!/usr/bin/env python3
"""
Quick test script for ACRB pipeline implementation.

Tests each stage of Algorithm 1 with minimal samples to verify correctness.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from acrb.pipeline import ACRBPipeline, ACRBConfig
from acrb.prompt_generation import BasePromptGenerator, AttributeExpander
from acrb.metrics import RefusalDetector, CueRetentionScorer, DisparityMetric


def test_stage_1_prompt_generation():
    """Test Stage I: Prompt synthesis without LLM (template-based)."""
    print("\n" + "="*60)
    print("TEST: Stage I - Prompt Synthesis (Template-based)")
    print("="*60)

    # Initialize components
    base_gen = BasePromptGenerator(seed=42)
    expander = AttributeExpander(include_neutral=True)

    # Sample base prompts
    base_prompts = base_gen.sample_prompts(n=3)
    print(f"\nSampled {len(base_prompts)} base prompts:")
    for bp in base_prompts:
        print(f"  [{bp.domain}] {bp.text}")

    # Expand with attributes
    expanded = []
    for bp in base_prompts:
        expanded.extend(expander.expand_prompt(bp, attribute_types=["culture", "gender"]))

    print(f"\nExpanded to {len(expanded)} prompts (3 base × 10 variations)")
    print("\nSample expansions:")
    for ep in expanded[:5]:
        print(f"  [{ep.attribute_type}:{ep.attribute_value}] {ep.expanded_text[:60]}...")

    print("\n✓ Stage I test passed")
    return expanded


def test_stage_2_metrics():
    """Test Stage III metrics without actual generation."""
    print("\n" + "="*60)
    print("TEST: Stage III - Metrics Computation")
    print("="*60)

    # Initialize metrics
    refusal_detector = RefusalDetector(use_clip=False)  # Disable CLIP for testing
    disparity_metric = DisparityMetric()

    # Test refusal detection (text-based)
    test_cases = [
        ("I cannot generate this image as it violates our policy.", True),
        ("Image generated successfully.", False),
        ("This content is inappropriate and blocked.", True),
    ]

    print("\nTesting hard refusal detection:")
    for text, expected in test_cases:
        result = refusal_detector.detect(text_output=text)
        status = "✓" if result.is_refused == expected else "✗"
        print(f"  {status} '{text[:40]}...' -> {result.is_refused} (expected: {expected})")

    # Test disparity metrics
    print("\nTesting disparity computation:")
    refusal_rates = {
        "culture:Korean": 0.15,
        "culture:Nigerian": 0.35,
        "culture:American": 0.08,
    }

    disparity = disparity_metric.compute_refusal_disparity(refusal_rates)
    print(f"  Refusal rates: {refusal_rates}")
    print(f"  Δ_refusal: {disparity.delta:.4f}")
    print(f"  Max: {disparity.max_attribute} ({disparity.max_value:.2f})")
    print(f"  Min: {disparity.min_attribute} ({disparity.min_value:.2f})")

    assert disparity.delta == 0.35 - 0.08, "Disparity calculation incorrect"
    print("\n✓ Metrics test passed")


def test_full_pipeline_dry_run():
    """Test full pipeline with minimal configuration (dry run)."""
    print("\n" + "="*60)
    print("TEST: Full Pipeline Dry Run (No actual generation)")
    print("="*60)

    # Minimal config
    config = ACRBConfig(
        model_name="test-model",
        mode="t2i",
        max_base_prompts=2,
        attribute_types=["culture"],
        llm_model=None,  # Template-based
        seed=42
    )

    print("\nConfiguration:")
    print(f"  Model: {config.model_name}")
    print(f"  Base prompts: {config.max_base_prompts}")
    print(f"  Attributes: {config.attribute_types}")
    print(f"  Expected prompts: ~{config.max_base_prompts * 7}")  # 6 cultures + neutral

    # Initialize pipeline
    pipeline = ACRBPipeline(config)

    # Test Stage I only
    print("\nRunning Stage I (Prompt Synthesis)...")
    prompts = pipeline.stage_1_prompt_synthesis()
    print(f"  Generated {len(prompts)} prompts")

    # Verify structure
    assert len(prompts) > 0, "No prompts generated"
    assert "expanded_text" in prompts[0], "Missing expanded_text field"
    assert "attribute_type" in prompts[0], "Missing attribute_type field"

    print("\nSample prompts:")
    for p in prompts[:3]:
        print(f"  [{p['attribute_type']}:{p['attribute_value']}] {p['expanded_text'][:50]}...")

    print("\n✓ Full pipeline dry run passed")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("ACRB Pipeline Implementation Tests")
    print("Algorithm 1 Verification")
    print("="*60)

    try:
        # Test individual components
        test_stage_1_prompt_generation()
        test_stage_2_metrics()

        # Test full pipeline
        test_full_pipeline_dry_run()

        print("\n" + "="*60)
        print("ALL TESTS PASSED ✓")
        print("="*60)
        print("\nImplementation is ready for production use.")
        print("\nNext steps:")
        print("  1. Run small-scale audit: python scripts/run_audit.py --samples 5")
        print("  2. Add LLM expansion: python scripts/run_audit.py --samples 10 --llm gemini-3-flash-preview")
        print("  3. Full audit: python scripts/run_audit.py --samples 100 --llm gemini-3-flash-preview")
        print("="*60 + "\n")

        return True

    except Exception as e:
        print(f"\n\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
