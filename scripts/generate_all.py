#!/usr/bin/env python3
"""
ACRB Image Generation Script - December 2025

Generates images using 6 representative models with DISTINCT SAFETY ALIGNMENT
policies for measuring Attribute-Conditioned Refusal Bias (ACRB).

Model Selection Rationale:
  - Goal: Compare refusal patterns across different safety philosophies
  - Excluded: Turbo/Flash variants (speed-optimized, same safety policy)
  - Included: Models with meaningfully different content moderation approaches

6 Representative Models:
  API (Closed Source):
    1. GPT-Image-1.5 (OpenAI) - Most conservative, aggressive filtering
    2. Imagen 3 / Nano Banana Pro (Google) - Moderate-conservative

  Local (Open Source):
    3. FLUX.2 [dev] (BFL) - Permissive, minimal restrictions
    4. Qwen-Image-Edit-2511 (Alibaba) - Chinese regulatory alignment
    5. SD 3.5 Large (Stability AI) - Community-governed
    6. Step1X-Edit (StepFun) - I2I specialist, Chinese ecosystem

Usage:
    # Open source only (free, requires GPU)
    python scripts/generate_all.py --models flux2 qwen-edit sd35 step1x --samples 100

    # With API models (paid)
    python scripts/generate_all.py --models gpt-image imagen3 --samples 100

    # Full pipeline (all 6 models)
    python scripts/generate_all.py --models gpt-image imagen3 flux2 qwen-edit sd35 step1x
"""

import argparse
import sys
import json
import torch
import gc
import os
import time
import requests
import base64
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from tqdm import tqdm
from io import BytesIO
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from PIL import Image
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ============================================================================
# ACRB Model Configurations - 6 Representative Models with Distinct Safety Policies
#
# Selection Criteria: Models chosen for DIVERSE SAFETY ALIGNMENT approaches,
# not speed variants (Turbo/Flash excluded). Goal: Compare refusal bias across
# different organizational safety philosophies.
# ============================================================================

MODEL_CONFIGS = {
    # === API-BASED (Closed Source) ===

    # OpenAI: Most conservative safety policy, aggressive content filtering
    "gpt-image": {
        "name": "GPT-Image-1.5",
        "api_endpoint": "https://api.openai.com/v1/images/generations",
        "type": "t2i",
        "elo": 1256,
        "provider": "OpenAI",
        "policy": "conservative",  # Strictest content policy
        "local": False,
        "cost_per_image": 0.04,
    },

    # Google: Moderate-conservative, Imagen 3 with Google's Responsible AI
    "imagen3": {
        "name": "Imagen 3 (Nano Banana Pro)",
        "api_endpoint": "https://generativelanguage.googleapis.com/v1beta",
        "type": "t2i",
        "elo": 1221,
        "provider": "Google",
        "policy": "moderate-conservative",
        "local": False,
        "cost_per_image": 0.04,
    },

    # === OPEN SOURCE (Local GPU) ===

    # BFL: Permissive policy, minimal content restrictions
    "flux2": {
        "name": "FLUX.2 [dev]",
        "hf_model": "black-forest-labs/FLUX.2-dev",
        "type": "t2i",
        "dtype": "bfloat16",
        "vram": "24GB",
        "elo": 1131,
        "provider": "Black Forest Labs",
        "policy": "permissive",  # Most open policy
        "local": True,
    },

    # Alibaba/Qwen: Chinese regulatory compliance, different cultural norms
    "qwen-edit": {
        "name": "Qwen-Image-Edit-2511",
        "hf_model": "Qwen/Qwen-Image-Edit-2511",
        "type": "t2i+i2i",
        "dtype": "bfloat16",
        "vram": "24GB",
        "elo": 1133,
        "provider": "Alibaba",
        "policy": "china-aligned",  # Chinese regulatory standards
        "local": True,
    },

    # Stability AI: Community-driven, open-weights philosophy
    "sd35": {
        "name": "SD 3.5 Large",
        "hf_model": "stabilityai/stable-diffusion-3.5-large",
        "type": "t2i",
        "dtype": "bfloat16",
        "vram": "16GB",
        "elo": 1050,
        "provider": "Stability AI",
        "policy": "community",  # Community-governed
        "local": True,
    },

    # StepFun: I2I specialist, Chinese tech ecosystem
    "step1x": {
        "name": "Step1X-Edit",
        "hf_model": "StepFun/Step1X-Edit-v1p2",
        "type": "i2i",
        "dtype": "float16",
        "vram": "16GB",
        "elo": 1081,
        "provider": "StepFun",
        "policy": "china-aligned",
        "local": True,
    },
}


@dataclass
class GenerationResult:
    """Result of a single generation."""
    prompt_id: str
    prompt_text: str
    model_name: str
    output_path: Optional[str]
    success: bool
    refused: bool = False
    refusal_message: Optional[str] = None
    error: Optional[str] = None
    generation_time: float = 0.0
    seed: int = 42
    attribute_type: Optional[str] = None
    attribute_value: Optional[str] = None
    domain: Optional[str] = None


class ModelLoader:
    """Manages model loading/unloading for GPU memory efficiency."""

    def __init__(self, device: str = "cuda"):
        self.device = device if torch.cuda.is_available() else "cpu"
        self.current_model_name = None
        self.pipeline = None

        if torch.cuda.is_available():
            props = torch.cuda.get_device_properties(0)
            self.vram_gb = props.total_memory / 1e9
            logger.info(f"GPU: {torch.cuda.get_device_name(0)} ({self.vram_gb:.1f}GB VRAM)")
        else:
            self.vram_gb = 0
            logger.warning("No GPU available, using CPU (very slow)")

    def clear_memory(self):
        """Release GPU memory."""
        if self.pipeline is not None:
            del self.pipeline
            self.pipeline = None
        self.current_model_name = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        logger.info("GPU memory cleared")

    def load_model(self, model_key: str):
        """Load a model, unloading previous if necessary."""
        if self.current_model_name == model_key:
            return self.pipeline

        config = MODEL_CONFIGS.get(model_key)
        if not config:
            raise ValueError(f"Unknown model: {model_key}")

        if not config.get("local", True):
            logger.info(f"Model {model_key} is API-based, no local loading needed")
            return None

        # Clear previous model
        self.clear_memory()

        logger.info(f"Loading {config['name']}...")

        dtype = torch.bfloat16 if config["dtype"] == "bfloat16" else torch.float16

        try:
            if model_key == "flux2":
                from diffusers import FluxPipeline
                self.pipeline = FluxPipeline.from_pretrained(
                    config["hf_model"],
                    torch_dtype=dtype,
                )
            elif model_key == "qwen-edit":
                from diffusers import AutoPipelineForText2Image
                self.pipeline = AutoPipelineForText2Image.from_pretrained(
                    config["hf_model"],
                    torch_dtype=dtype,
                    trust_remote_code=True,
                )
            elif model_key == "step1x":
                from diffusers import StableDiffusionXLPipeline
                self.pipeline = StableDiffusionXLPipeline.from_pretrained(
                    config["hf_model"],
                    torch_dtype=dtype,
                    trust_remote_code=True,
                )
            elif model_key == "sd35":
                from diffusers import StableDiffusion3Pipeline
                self.pipeline = StableDiffusion3Pipeline.from_pretrained(
                    config["hf_model"],
                    torch_dtype=dtype,
                )
            elif model_key == "cosxl-edit":
                from diffusers import StableDiffusionXLInstructPix2PixPipeline
                self.pipeline = StableDiffusionXLInstructPix2PixPipeline.from_pretrained(
                    config["hf_model"],
                    torch_dtype=dtype,
                )
            else:
                from diffusers import AutoPipelineForText2Image
                self.pipeline = AutoPipelineForText2Image.from_pretrained(
                    config["hf_model"],
                    torch_dtype=dtype,
                )

            self.pipeline = self.pipeline.to(self.device)
            self.current_model_name = model_key
            logger.info(f"Model {config['name']} loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load {model_key}: {e}")
            raise

        return self.pipeline


class ImageGenerator:
    """Generates images using local or API models."""

    def __init__(self, output_dir: Path, checkpoint_dir: Path = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.checkpoint_dir = checkpoint_dir or (self.output_dir / "checkpoints")
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self.loader = ModelLoader()
        self.api_keys = {
            "openai": os.getenv("OPENAI_API_KEY"),
            "google": os.getenv("GOOGLE_API_KEY"),
            "bfl": os.getenv("BFL_API_KEY"),
        }

    def generate_t2i_local(
        self,
        model_key: str,
        prompt: str,
        seed: int = 42,
        num_steps: int = 28,
        guidance_scale: float = 3.5,
    ) -> Tuple[Optional[Image.Image], bool, Optional[str]]:
        """Generate image using local model."""
        pipeline = self.loader.load_model(model_key)

        generator = torch.Generator(self.loader.device).manual_seed(seed)

        try:
            if model_key == "flux2":
                result = pipeline(
                    prompt=prompt,
                    num_inference_steps=num_steps,
                    guidance_scale=guidance_scale,
                    generator=generator,
                )
            elif model_key in ["qwen-edit", "step1x"]:
                result = pipeline(
                    prompt=prompt,
                    num_inference_steps=num_steps,
                    guidance_scale=7.5,
                    generator=generator,
                )
            elif model_key == "sd35":
                result = pipeline(
                    prompt=prompt,
                    num_inference_steps=num_steps,
                    guidance_scale=4.5,
                    generator=generator,
                )
            else:
                result = pipeline(
                    prompt=prompt,
                    num_inference_steps=num_steps,
                    generator=generator,
                )

            image = result.images[0]

            # Check for NSFW/refusal
            if hasattr(result, 'nsfw_content_detected') and result.nsfw_content_detected:
                return None, True, "NSFW content detected"

            return image, False, None

        except Exception as e:
            error_msg = str(e).lower()
            if any(kw in error_msg for kw in ['safety', 'policy', 'blocked', 'nsfw']):
                return None, True, str(e)
            raise

    def generate_t2i_api(
        self,
        model_key: str,
        prompt: str,
    ) -> Tuple[Optional[Image.Image], bool, Optional[str]]:
        """Generate image using API."""
        config = MODEL_CONFIGS[model_key]

        if model_key == "gpt-image":
            return self._generate_openai(prompt)
        elif model_key == "imagen3":
            return self._generate_google(prompt)
        else:
            raise ValueError(f"Unknown API model: {model_key}")

    def _generate_openai(self, prompt: str) -> Tuple[Optional[Image.Image], bool, Optional[str]]:
        """Generate using OpenAI API."""
        if not self.api_keys["openai"]:
            raise ValueError("OPENAI_API_KEY not set")

        headers = {
            "Authorization": f"Bearer {self.api_keys['openai']}",
            "Content-Type": "application/json",
        }

        data = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024",
            "response_format": "b64_json",
        }

        try:
            response = requests.post(
                "https://api.openai.com/v1/images/generations",
                headers=headers,
                json=data,
                timeout=60,
            )

            if response.status_code == 400:
                error_data = response.json()
                if "content_policy" in str(error_data).lower():
                    return None, True, error_data.get("error", {}).get("message", "Content policy violation")

            response.raise_for_status()
            result = response.json()

            img_data = base64.b64decode(result["data"][0]["b64_json"])
            image = Image.open(BytesIO(img_data))
            return image, False, None

        except requests.exceptions.RequestException as e:
            if "content_policy" in str(e).lower():
                return None, True, str(e)
            raise

    def _generate_google(self, prompt: str) -> Tuple[Optional[Image.Image], bool, Optional[str]]:
        """Generate using Google Imagen API."""
        if not self.api_keys["google"]:
            raise ValueError("GOOGLE_API_KEY not set")

        # Google Generative AI API for Imagen
        url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:generateImages?key={self.api_keys['google']}"

        data = {
            "prompt": prompt,
            "number_of_images": 1,
            "aspect_ratio": "1:1",
        }

        try:
            response = requests.post(url, json=data, timeout=60)

            if response.status_code == 400:
                return None, True, "Content policy violation"

            response.raise_for_status()
            result = response.json()

            img_data = base64.b64decode(result["images"][0]["image"])
            image = Image.open(BytesIO(img_data))
            return image, False, None

        except Exception as e:
            if "blocked" in str(e).lower() or "policy" in str(e).lower():
                return None, True, str(e)
            raise

    def _generate_bfl(self, prompt: str) -> Tuple[Optional[Image.Image], bool, Optional[str]]:
        """Generate using BFL FLUX API."""
        if not self.api_keys["bfl"]:
            raise ValueError("BFL_API_KEY not set")

        headers = {
            "Authorization": f"Bearer {self.api_keys['bfl']}",
            "Content-Type": "application/json",
        }

        data = {
            "prompt": prompt,
            "width": 1024,
            "height": 1024,
        }

        try:
            response = requests.post(
                "https://api.bfl.ml/v1/flux-pro-1.1",
                headers=headers,
                json=data,
                timeout=60,
            )
            response.raise_for_status()
            result = response.json()

            img_url = result["sample"]
            img_response = requests.get(img_url)
            image = Image.open(BytesIO(img_response.content))
            return image, False, None

        except Exception as e:
            if "policy" in str(e).lower():
                return None, True, str(e)
            raise

    def generate_i2i(
        self,
        model_key: str,
        source_image: Image.Image,
        instruction: str,
        seed: int = 42,
    ) -> Tuple[Optional[Image.Image], bool, Optional[str]]:
        """Generate I2I edit."""
        pipeline = self.loader.load_model(model_key)
        generator = torch.Generator(self.loader.device).manual_seed(seed)

        try:
            result = pipeline(
                prompt=instruction,
                image=source_image,
                num_inference_steps=20,
                image_guidance_scale=1.5,
                guidance_scale=7.5,
                generator=generator,
            )
            return result.images[0], False, None
        except Exception as e:
            if "safety" in str(e).lower() or "policy" in str(e).lower():
                return None, True, str(e)
            raise

    def generate_batch(
        self,
        model_key: str,
        prompts: List[Dict],
        mode: str = "t2i",
        source_images_dir: Optional[Path] = None,
        resume_from: int = 0,
    ) -> List[GenerationResult]:
        """Generate images for a batch of prompts."""
        config = MODEL_CONFIGS[model_key]
        model_output_dir = self.output_dir / model_key
        model_output_dir.mkdir(parents=True, exist_ok=True)

        results = []
        checkpoint_file = self.checkpoint_dir / f"{model_key}_checkpoint.json"

        # Load existing results if resuming
        if resume_from > 0 and checkpoint_file.exists():
            with open(checkpoint_file) as f:
                results = json.load(f)
            logger.info(f"Resuming from checkpoint: {len(results)} results loaded")

        start_idx = len(results)
        prompts_to_process = prompts[start_idx:]

        logger.info(f"Generating {len(prompts_to_process)} images with {config['name']}")

        for i, prompt_data in enumerate(tqdm(prompts_to_process, desc=f"Generating ({model_key})")):
            idx = start_idx + i
            start_time = time.time()

            try:
                if config.get("local", True):
                    image, refused, refusal_msg = self.generate_t2i_local(
                        model_key,
                        prompt_data["expanded_text"],
                        seed=42 + idx,
                    )
                else:
                    image, refused, refusal_msg = self.generate_t2i_api(
                        model_key,
                        prompt_data["expanded_text"],
                    )

                if image and not refused:
                    output_path = model_output_dir / f"{prompt_data['prompt_id']}.png"
                    image.save(output_path)
                    output_path_str = str(output_path)
                else:
                    output_path_str = None

                result = GenerationResult(
                    prompt_id=prompt_data["prompt_id"],
                    prompt_text=prompt_data["expanded_text"],
                    model_name=config["name"],
                    output_path=output_path_str,
                    success=not refused and image is not None,
                    refused=refused,
                    refusal_message=refusal_msg,
                    generation_time=time.time() - start_time,
                    seed=42 + idx,
                    attribute_type=prompt_data.get("attribute_type"),
                    attribute_value=prompt_data.get("attribute_value"),
                    domain=prompt_data.get("domain"),
                )

            except Exception as e:
                logger.error(f"Error generating {prompt_data['prompt_id']}: {e}")
                result = GenerationResult(
                    prompt_id=prompt_data["prompt_id"],
                    prompt_text=prompt_data["expanded_text"],
                    model_name=config["name"],
                    output_path=None,
                    success=False,
                    error=str(e),
                    generation_time=time.time() - start_time,
                    seed=42 + idx,
                    attribute_type=prompt_data.get("attribute_type"),
                    attribute_value=prompt_data.get("attribute_value"),
                    domain=prompt_data.get("domain"),
                )

            results.append(asdict(result))

            # Checkpoint every 50 images
            if (idx + 1) % 50 == 0:
                with open(checkpoint_file, "w") as f:
                    json.dump(results, f, indent=2)
                logger.info(f"Checkpoint saved: {len(results)} results")

        # Save final results
        output_file = self.output_dir / f"{model_key}_results.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        # Clear memory after batch
        self.loader.clear_memory()

        return results


def load_prompts(prompts_file: Path, max_samples: int = None) -> List[Dict]:
    """Load prompts from JSON file."""
    with open(prompts_file) as f:
        prompts = json.load(f)

    if max_samples:
        prompts = prompts[:max_samples]

    logger.info(f"Loaded {len(prompts)} prompts from {prompts_file}")
    return prompts


def main():
    parser = argparse.ArgumentParser(description="ACRB Image Generation (Dec 2025 Models)")
    parser.add_argument("--models", nargs="+", default=["flux2"],
                       choices=list(MODEL_CONFIGS.keys()),
                       help="Models to use for generation")
    parser.add_argument("--samples", type=int, default=100,
                       help="Number of prompts to process")
    parser.add_argument("--prompts", type=str, default="data/prompts/expanded_prompts.json",
                       help="Path to prompts JSON file")
    parser.add_argument("--output", type=str, default="experiments/images",
                       help="Output directory")
    parser.add_argument("--mode", type=str, choices=["t2i", "i2i"], default="t2i",
                       help="Generation mode")
    parser.add_argument("--resume", action="store_true",
                       help="Resume from last checkpoint")

    args = parser.parse_args()

    # Print configuration
    print("\n" + "="*60)
    print("  ACRB Image Generation - December 2025 Models")
    print("="*60)
    print(f"\nModels: {', '.join(args.models)}")
    print(f"Samples: {args.samples}")
    print(f"Mode: {args.mode}")
    print(f"Output: {args.output}")

    for model in args.models:
        config = MODEL_CONFIGS[model]
        print(f"\n  {model}:")
        print(f"    Name: {config['name']}")
        print(f"    Provider: {config['provider']}")
        print(f"    ELO: {config['elo']}")
        print(f"    Local: {config.get('local', True)}")

    print("\n" + "-"*60 + "\n")

    # Load prompts
    prompts_path = Path(args.prompts)
    if not prompts_path.exists():
        logger.error(f"Prompts file not found: {prompts_path}")
        logger.info("Run prompt generation first: python scripts/generate_prompts.py")
        sys.exit(1)

    prompts = load_prompts(prompts_path, args.samples)

    # Generate
    generator = ImageGenerator(
        output_dir=Path(args.output),
        checkpoint_dir=Path(args.output) / "checkpoints",
    )

    all_results = {}

    for model_key in args.models:
        logger.info(f"\n{'='*40}")
        logger.info(f"Starting generation with {MODEL_CONFIGS[model_key]['name']}")
        logger.info(f"{'='*40}\n")

        results = generator.generate_batch(
            model_key=model_key,
            prompts=prompts,
            mode=args.mode,
            resume_from=0 if not args.resume else -1,
        )

        all_results[model_key] = results

        # Print summary
        success = sum(1 for r in results if r["success"])
        refused = sum(1 for r in results if r["refused"])
        failed = len(results) - success - refused

        print(f"\n{MODEL_CONFIGS[model_key]['name']} Summary:")
        print(f"  Success: {success}/{len(results)} ({100*success/len(results):.1f}%)")
        print(f"  Refused: {refused}/{len(results)} ({100*refused/len(results):.1f}%)")
        print(f"  Failed:  {failed}/{len(results)} ({100*failed/len(results):.1f}%)")

    # Save combined results
    combined_file = Path(args.output) / "all_results.json"
    with open(combined_file, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\n{'='*60}")
    print(f"All results saved to: {combined_file}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
