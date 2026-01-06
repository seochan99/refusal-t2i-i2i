"""
Prompt validation utilities for boundary cases and minimal-pair constraints.
"""

from __future__ import annotations

import os
import re
import difflib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .base_prompts import SAFETY_DOMAINS, BasePrompt


STOPWORDS = {
    "a", "an", "the", "in", "on", "at", "to", "of", "and", "or", "with", "for",
    "from", "by", "as", "is", "are", "was", "were", "be", "being", "been", "this",
    "that", "these", "those", "person", "people", "someone", "someone's"
}


@dataclass
class ValidationConfig:
    semantic_similarity_threshold: float = 0.85
    max_token_difference: int = 3
    require_domain_trigger: bool = True
    allow_cross_domain_triggers: bool = False
    require_attribute_marker: bool = True
    allow_fallback_similarity: bool = True
    benign_validation: bool = False
    benign_threshold: float = 0.5
    require_benign_checker: bool = False
    sentence_model_path: Optional[str] = None


@dataclass
class ValidationResult:
    ok: bool
    reasons: List[str] = field(default_factory=list)
    scores: Dict[str, float] = field(default_factory=dict)
    meta: Dict[str, str] = field(default_factory=dict)


class PromptValidator:
    """Validate boundary prompts and minimal-pair constraints."""

    def __init__(
        self,
        config: Optional[ValidationConfig] = None,
        benign_checker: Optional[object] = None
    ):
        self.config = config or ValidationConfig()
        self._embedder = self._init_embedder()
        self.benign_checker = benign_checker

    def _init_embedder(self):
        model_path = self.config.sentence_model_path or os.getenv("ACRB_SENTENCE_MODEL")
        if not model_path:
            return None
        if not Path(model_path).exists():
            return None
        try:
            from sentence_transformers import SentenceTransformer
        except Exception:
            return None
        try:
            return SentenceTransformer(model_path)
        except Exception:
            return None

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^a-z0-9\\s]", " ", text)
        text = re.sub(r"\\s+", " ", text).strip()
        return text

    @classmethod
    def _tokenize(cls, text: str) -> List[str]:
        return cls._normalize(text).split()

    @staticmethod
    def _clean_attr_value(value: str) -> str:
        return value.replace("_", " ").replace("-", " ").strip()

    @classmethod
    def _strip_markers(cls, text: str, markers: List[str]) -> str:
        stripped = text
        for marker in markers:
            pattern = re.compile(re.escape(marker), re.IGNORECASE)
            stripped = pattern.sub("", stripped)
        stripped = re.sub(r"\\s+", " ", stripped).strip()
        return stripped

    @staticmethod
    def _contains_phrase(text: str, phrase: str) -> bool:
        text_norm = PromptValidator._normalize(text)
        phrase_norm = PromptValidator._normalize(phrase)
        if not phrase_norm:
            return False
        if " " in phrase_norm:
            return phrase_norm in text_norm
        return bool(re.search(rf"\\b{re.escape(phrase_norm)}\\b", text_norm))

    def _semantic_similarity(self, text_a: str, text_b: str) -> float:
        if self._embedder:
            try:
                embeddings = self._embedder.encode([text_a, text_b], normalize_embeddings=True)
                return float((embeddings[0] * embeddings[1]).sum())
            except Exception:
                if not self.config.allow_fallback_similarity:
                    return 0.0
        tokens_a = self._tokenize(text_a)
        tokens_b = self._tokenize(text_b)
        set_a, set_b = set(tokens_a), set(tokens_b)
        if not set_a or not set_b:
            return 0.0
        jaccard = len(set_a & set_b) / len(set_a | set_b)
        seq = difflib.SequenceMatcher(None, self._normalize(text_a), self._normalize(text_b)).ratio()
        return 0.5 * (jaccard + seq)

    def _attribute_present(self, text: str, attr_value: str, markers: List[str]) -> bool:
        text_tokens = set(self._tokenize(text))
        candidates = [attr_value, self._clean_attr_value(attr_value)] + markers
        for candidate in candidates:
            if self._contains_phrase(text, candidate):
                return True
        marker_tokens = []
        for marker in candidates:
            marker_tokens.extend(
                t for t in self._tokenize(marker) if t and t not in STOPWORDS
            )
        return any(token in text_tokens for token in marker_tokens)

    def _domain_triggers(self, domain: str) -> List[str]:
        return SAFETY_DOMAINS.get(domain, {}).get("trigger_words", [])

    def _cross_domain_triggers(self, domain: str) -> List[str]:
        triggers = []
        for other_domain, info in SAFETY_DOMAINS.items():
            if other_domain == domain:
                continue
            triggers.extend(info.get("trigger_words", []))
        return triggers

    def validate_boundary(
        self,
        text: str,
        domain: str,
        base_triggers: Optional[List[str]] = None
    ) -> ValidationResult:
        reasons = []
        scores: Dict[str, float] = {}
        triggers = list(base_triggers or []) + self._domain_triggers(domain)
        triggers = [t for t in triggers if t]

        if self.config.require_domain_trigger and triggers:
            has_trigger = any(self._contains_phrase(text, trig) for trig in triggers)
            scores["domain_trigger_hit"] = 1.0 if has_trigger else 0.0
            if not has_trigger:
                reasons.append("missing_domain_trigger")

        if not self.config.allow_cross_domain_triggers:
            cross_triggers = self._cross_domain_triggers(domain)
            cross_hit = any(self._contains_phrase(text, trig) for trig in cross_triggers)
            scores["cross_domain_hit"] = 1.0 if cross_hit else 0.0
            if cross_hit:
                reasons.append("cross_domain_trigger")

        return ValidationResult(ok=not reasons, reasons=reasons, scores=scores)

    def validate_expansion(
        self,
        base_prompt: BasePrompt,
        expanded_text: str,
        attribute_type: str,
        attribute_value: str,
        attribute_markers: Optional[List[str]] = None
    ) -> ValidationResult:
        reasons = []
        scores: Dict[str, float] = {}
        meta: Dict[str, str] = {}
        markers = attribute_markers or []

        if attribute_type != "neutral" and self.config.require_attribute_marker:
            if not self._attribute_present(expanded_text, attribute_value, markers):
                reasons.append("missing_attribute_marker")

        boundary_result = self.validate_boundary(
            expanded_text,
            domain=base_prompt.domain,
            base_triggers=base_prompt.trigger_words,
        )
        if not boundary_result.ok:
            reasons.extend([f"boundary:{r}" for r in boundary_result.reasons])
        scores.update({f"boundary_{k}": v for k, v in boundary_result.scores.items()})

        base_clean = self._strip_markers(base_prompt.text, markers)
        expanded_clean = self._strip_markers(expanded_text, markers)
        similarity = self._semantic_similarity(base_clean, expanded_clean)
        scores["semantic_similarity"] = similarity
        if similarity < self.config.semantic_similarity_threshold:
            reasons.append("semantic_drift")

        token_diff = abs(len(self._tokenize(base_clean)) - len(self._tokenize(expanded_clean)))
        scores["token_diff"] = float(token_diff)
        if token_diff > self.config.max_token_difference:
            reasons.append("structure_drift")

        if self.config.benign_validation:
            if not self.benign_checker:
                if self.config.require_benign_checker:
                    reasons.append("benign_checker_unavailable")
            else:
                result = self.benign_checker.check(expanded_text)
                scores["benign_score"] = result.score
                meta["benign_label"] = result.label
                if not result.is_benign or result.score < self.config.benign_threshold:
                    reasons.append("non_benign")

        return ValidationResult(ok=not reasons, reasons=reasons, scores=scores, meta=meta)
