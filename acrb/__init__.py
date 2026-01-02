"""
ACRB: Attribute-Conditioned Refusal Bias Framework

A comprehensive toolkit for auditing fairness in T2I and I2I generative models
by measuring attribute-conditioned refusal bias across demographic and cultural attributes.

Key Components:
- pipeline: Main ACRB pipeline (Algorithm 1 implementation)
- prompt_generation: Dynamic prompt synthesis with LLM red-teaming
- models: T2I/I2I model wrappers
- metrics: Hard refusal detection + soft refusal (cue erasure) scoring
- evaluation: Legacy pipeline (deprecated, use pipeline.py)

Quick Start:
    from acrb.pipeline import ACRBPipeline, ACRBConfig

    config = ACRBConfig(
        model_name="flux-2-dev",
        mode="t2i",
        max_base_prompts=10,
        llm_model="gemini-3-flash-preview"
    )

    pipeline = ACRBPipeline(config)
    result = pipeline.run()

    print(f"Δ_refusal: {result.delta_refusal:.4f}")
    print(f"Δ_erasure: {result.delta_erasure:.4f}")
"""

__version__ = "0.2.0"
__author__ = "ACRB Research Team"

# Main pipeline (Algorithm 1)
from .pipeline import ACRBPipeline, ACRBConfig, ACRBResult

# Prompt generation
from .prompt_generation import (
    BasePromptGenerator,
    AttributeExpander,
    LLMBackend,
    BasePrompt,
    ExpandedPrompt,
    ATTRIBUTE_CATEGORIES,
    SAFETY_DOMAINS
)

# Model wrappers
from .models import T2IModelWrapper, I2IModelWrapper

# Metrics
from .metrics import (
    RefusalDetector,
    CueRetentionScorer,
    DisparityMetric,
    RefusalResult,
    CueRetentionResult,
    DisparityResult
)

__all__ = [
    # Pipeline
    "ACRBPipeline",
    "ACRBConfig",
    "ACRBResult",

    # Prompt generation
    "BasePromptGenerator",
    "AttributeExpander",
    "LLMBackend",
    "BasePrompt",
    "ExpandedPrompt",
    "ATTRIBUTE_CATEGORIES",
    "SAFETY_DOMAINS",

    # Models
    "T2IModelWrapper",
    "I2IModelWrapper",

    # Metrics
    "RefusalDetector",
    "CueRetentionScorer",
    "DisparityMetric",
    "RefusalResult",
    "CueRetentionResult",
    "DisparityResult",
]
