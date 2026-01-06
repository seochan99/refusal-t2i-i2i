#!/usr/bin/env python3
"""
Validate boundary/minimal-pair constraints on expanded prompts.

Usage:
  python scripts/validate_prompt_constraints.py
  python scripts/validate_prompt_constraints.py --expanded data/prompts/expanded_prompts.json
  python scripts/validate_prompt_constraints.py --write-clean data/prompts/expanded_prompts.clean.json
"""

import argparse
import json
import random
import hashlib
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional

from acrb.prompt_generation import PromptValidator, ValidationConfig, BenignIntentChecker, LLMBackend
from acrb.prompt_generation.base_prompts import BasePrompt


def load_json(path: Path):
    with path.open() as f:
        return json.load(f)


def resolve_base_path(expanded_path: Path, base_path: Optional[Path]) -> Path:
    if base_path and base_path.exists():
        return base_path
    candidate = expanded_path.parent / "base_prompts.json"
    if candidate.exists():
        return candidate
    fallback = Path(__file__).parent.parent / "data" / "raw" / "base_prompts.json"
    return fallback


def build_base_lookup(base_prompts):
    lookup = {}
    for bp in base_prompts:
        lookup[bp["prompt_id"]] = BasePrompt(
            prompt_id=bp["prompt_id"],
            text=bp["text"],
            domain=bp["domain"],
            intent=bp.get("intent", "neutral"),
            is_benign=bp.get("is_benign", True),
            trigger_words=bp.get("trigger_words", []),
        )
    return lookup


def _tokenize(text: str):
    cleaned = "".join(ch.lower() if ch.isalnum() or ch.isspace() else " " for ch in text)
    return [t for t in cleaned.split() if t]


def simhash(text: str, bits: int = 64) -> int:
    tokens = _tokenize(text)
    if not tokens:
        return 0
    vector = [0] * bits
    for token in tokens:
        h = hashlib.md5(token.encode("utf-8")).digest()
        value = int.from_bytes(h[:8], "big")
        for i in range(bits):
            bit = 1 if (value >> i) & 1 else -1
            vector[i] += bit
    fingerprint = 0
    for i in range(bits):
        if vector[i] > 0:
            fingerprint |= 1 << i
    return fingerprint


def hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def dedup_base_prompts(base_lookup, base_ids, threshold: int = 3):
    kept = []
    hashes = []
    for base_id in base_ids:
        base_prompt = base_lookup[base_id]
        fingerprint = simhash(base_prompt.text)
        duplicate = False
        for existing in hashes:
            if hamming(fingerprint, existing) <= threshold:
                duplicate = True
                break
        if not duplicate:
            kept.append(base_id)
            hashes.append(fingerprint)
    return kept


def sample_base_prompts(base_lookup, base_ids, max_base: int, seed: int = 42):
    random.seed(seed)
    by_domain = defaultdict(list)
    for base_id in base_ids:
        by_domain[base_lookup[base_id].domain].append(base_id)

    domains = sorted(by_domain.keys())
    if not domains:
        return []

    target_per_domain = max_base // len(domains)
    remainder = max_base % len(domains)

    sampled = []
    for idx, domain in enumerate(domains):
        pool = by_domain[domain]
        count = target_per_domain + (1 if idx < remainder else 0)
        if count >= len(pool):
            sampled.extend(pool)
        else:
            sampled.extend(random.sample(pool, count))
    return sampled


def parse_args():
    parser = argparse.ArgumentParser(description="Validate prompt constraints")
    parser.add_argument(
        "--expanded",
        type=str,
        default="data/prompts/expanded_prompts.json",
        help="Expanded prompts JSON file"
    )
    parser.add_argument(
        "--base",
        type=str,
        default=None,
        help="Base prompts JSON file (default: inferred)"
    )
    parser.add_argument(
        "--report",
        type=str,
        default="data/prompts/validation_report.json",
        help="Write validation report JSON to this path"
    )
    parser.add_argument(
        "--details",
        type=str,
        default=None,
        help="Write per-prompt validation details JSON to this path"
    )
    parser.add_argument(
        "--write-clean",
        type=str,
        default=None,
        help="Write passing prompts JSON to this path"
    )
    parser.add_argument(
        "--drop-incomplete",
        action="store_true",
        help="Drop base prompts with any failed expansions"
    )
    parser.add_argument(
        "--dedup",
        action="store_true",
        help="Deduplicate at base-prompt level using simhash"
    )
    parser.add_argument(
        "--simhash-threshold",
        type=int,
        default=3,
        help="Max simhash Hamming distance for dedup (default: 3)"
    )
    parser.add_argument(
        "--max-base-prompts",
        type=int,
        default=None,
        help="Sample this many base prompts (keeps all expansions)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for sampling (default: 42)"
    )
    parser.add_argument(
        "--benign-validation",
        action="store_true",
        help="Enable benign-intent validation (requires model or LLM)"
    )
    parser.add_argument(
        "--benign-model",
        type=str,
        default=None,
        help="Local benign classifier model path (overrides ACRB_BENIGN_MODEL)"
    )
    parser.add_argument(
        "--benign-llm",
        type=str,
        default=None,
        help="LLM model for benign classification (OpenAI-compatible)"
    )
    parser.add_argument(
        "--benign-api-base",
        type=str,
        default="https://generativelanguage.googleapis.com/v1beta/openai",
        help="LLM API base URL for benign classification"
    )
    parser.add_argument(
        "--benign-api-key",
        type=str,
        default=None,
        help="LLM API key for benign classification (defaults to ACRB_LLM_API_KEY)"
    )
    parser.add_argument(
        "--benign-threshold",
        type=float,
        default=0.5,
        help="Benign score threshold (default: 0.5)"
    )
    parser.add_argument(
        "--require-benign-checker",
        action="store_true",
        help="Fail validation if benign checker is unavailable"
    )
    parser.add_argument(
        "--sentence-model",
        type=str,
        default=None,
        help="Local sentence-transformer model path for similarity checks"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    expanded_path = Path(args.expanded)
    if not expanded_path.exists():
        raise FileNotFoundError(f"Expanded prompts not found: {expanded_path}")

    base_path = resolve_base_path(expanded_path, Path(args.base) if args.base else None)
    if not base_path.exists():
        raise FileNotFoundError(f"Base prompts not found: {base_path}")

    expanded = load_json(expanded_path)
    base_prompts = load_json(base_path)
    base_lookup = build_base_lookup(base_prompts)

    llm_backend = None
    if args.benign_llm:
        llm_backend = LLMBackend(
            model_name=args.benign_llm,
            api_base=args.benign_api_base,
            api_key=args.benign_api_key or os.getenv("ACRB_LLM_API_KEY")
        )
    benign_checker = None
    if args.benign_validation:
        benign_checker = BenignIntentChecker(
            model_path=args.benign_model,
            llm_backend=llm_backend,
            threshold=args.benign_threshold
        )
    validator = PromptValidator(
        ValidationConfig(
            benign_validation=args.benign_validation,
            benign_threshold=args.benign_threshold,
            require_benign_checker=args.require_benign_checker,
            sentence_model_path=args.sentence_model,
        ),
        benign_checker=benign_checker
    )

    failures = []
    failure_reasons = Counter()
    domain_failures = Counter()
    attribute_failures = Counter()
    base_to_fail = defaultdict(list)

    passing = []
    details = []

    for prompt in expanded:
        base_id = prompt["base_prompt_id"]
        base_prompt = base_lookup.get(base_id)
        if not base_prompt:
            failure_reasons["missing_base_prompt"] += 1
            failures.append(prompt)
            continue

        markers = []
        marker = prompt.get("attribute_marker")
        if marker:
            markers.append(marker)

        result = validator.validate_expansion(
            base_prompt=base_prompt,
            expanded_text=prompt["expanded_text"],
            attribute_type=prompt["attribute_type"],
            attribute_value=prompt["attribute_value"],
            attribute_markers=markers
        )
        details.append({
            "expanded_id": prompt["expanded_id"],
            "base_prompt_id": prompt["base_prompt_id"],
            "domain": prompt["domain"],
            "attribute_type": prompt["attribute_type"],
            "attribute_value": prompt["attribute_value"],
            "ok": result.ok,
            "reasons": result.reasons,
            "scores": result.scores,
            "meta": result.meta,
        })

        if result.ok:
            passing.append(prompt)
        else:
            failures.append(prompt)
            base_to_fail[base_id].append(prompt["expanded_id"])
            for reason in result.reasons:
                failure_reasons[reason] += 1
            domain_failures[prompt["domain"]] += 1
            attribute_failures[prompt["attribute_type"]] += 1

    total = len(expanded)
    passed = len(passing)
    failed = len(failures)

    print("=" * 70)
    print("PROMPT CONSTRAINT VALIDATION")
    print("=" * 70)
    print(f"Expanded prompts: {total}")
    print(f"Passed:           {passed} ({passed / total:.1%})")
    print(f"Failed:           {failed} ({failed / total:.1%})")

    if failure_reasons:
        print("\nTop failure reasons:")
        for reason, count in failure_reasons.most_common(10):
            print(f"  {reason:25s} {count:5d}")

    if domain_failures:
        print("\nFailures by domain:")
        for domain, count in domain_failures.most_common():
            print(f"  {domain:25s} {count:5d}")

    if attribute_failures:
        print("\nFailures by attribute type:")
        for attr, count in attribute_failures.most_common():
            print(f"  {attr:15s} {count:5d}")

    curated = passing
    if args.drop_incomplete:
        failing_bases = set(base_to_fail.keys())
        curated = [p for p in curated if p["base_prompt_id"] not in failing_bases]

    base_ids = sorted({p["base_prompt_id"] for p in curated})
    base_after_validation = len(base_ids)

    if args.dedup:
        base_ids = dedup_base_prompts(
            base_lookup,
            base_ids,
            threshold=args.simhash_threshold
        )

    if args.max_base_prompts is not None:
        base_ids = sample_base_prompts(
            base_lookup,
            base_ids,
            max_base=args.max_base_prompts,
            seed=args.seed
        )

    base_id_set = set(base_ids)
    curated = [p for p in curated if p["base_prompt_id"] in base_id_set]

    if args.dedup or args.max_base_prompts is not None or args.drop_incomplete:
        print("\nCuration summary:")
        print(f"  Base prompts after validation: {base_after_validation}")
        print(f"  Base prompts after dedup/sampling: {len(base_id_set)}")
        print(f"  Curated prompts: {len(curated)}")

    def _stats(values):
        if not values:
            return {"min": None, "max": None, "avg": None}
        return {
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
        }

    semantic_scores = [d["scores"].get("semantic_similarity") for d in details if "semantic_similarity" in d["scores"]]
    token_diffs = [d["scores"].get("token_diff") for d in details if "token_diff" in d["scores"]]
    benign_scores = [d["scores"].get("benign_score") for d in details if "benign_score" in d["scores"]]

    report = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "failure_reasons": dict(failure_reasons),
        "domain_failures": dict(domain_failures),
        "attribute_failures": dict(attribute_failures),
        "base_with_failures": {k: v for k, v in base_to_fail.items()},
        "expanded_path": str(expanded_path),
        "base_path": str(base_path),
        "post_validation_base_prompts": base_after_validation,
        "post_dedup_base_prompts": len(base_id_set),
        "curated_prompts": len(curated),
        "score_stats": {
            "semantic_similarity": _stats(semantic_scores),
            "token_diff": _stats(token_diffs),
            "benign_score": _stats(benign_scores),
        },
    }

    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("w") as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved to: {report_path}")

    if args.details:
        details_path = Path(args.details)
        details_path.parent.mkdir(parents=True, exist_ok=True)
        with details_path.open("w") as f:
            json.dump(details, f, indent=2)
        print(f"Validation details saved to: {details_path}")

    if args.write_clean:
        clean_path = Path(args.write_clean)
        clean_path.parent.mkdir(parents=True, exist_ok=True)
        with clean_path.open("w") as f:
            json.dump(curated, f, indent=2, ensure_ascii=False)
        print(f"Clean prompts saved to: {clean_path}")


if __name__ == "__main__":
    main()
