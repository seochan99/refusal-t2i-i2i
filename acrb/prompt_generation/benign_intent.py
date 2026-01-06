"""
Benign intent checking for prompt validation.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Optional, Tuple

from .llm_backend import LLMBackend


@dataclass
class BenignIntentResult:
    is_benign: bool
    score: float
    label: str
    raw: str


class BenignIntentChecker:
    """
    Optional benign/unsafe classifier.

    Priority:
      1) Local HF model if ACRB_BENIGN_MODEL is set
      2) LLM backend if provided
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        llm_backend: Optional[LLMBackend] = None,
        threshold: float = 0.5
    ):
        self.model_path = model_path or os.getenv("ACRB_BENIGN_MODEL")
        self.llm_backend = llm_backend
        self.threshold = threshold
        self._pipeline = self._init_pipeline()

    def _init_pipeline(self):
        if not self.model_path:
            return None
        if not os.path.exists(self.model_path):
            return None
        try:
            from transformers import pipeline
        except Exception:
            return None
        try:
            return pipeline(
                "text-classification",
                model=self.model_path,
                tokenizer=self.model_path,
                truncation=True
            )
        except Exception:
            return None

    @staticmethod
    def _normalize_label(label: str) -> str:
        label = label.lower().strip()
        if "benign" in label or "safe" in label:
            return "benign"
        if "unsafe" in label or "harmful" in label or "toxic" in label:
            return "unsafe"
        return label

    def _check_with_llm(self, text: str) -> Optional[BenignIntentResult]:
        if not self.llm_backend:
            return None
        system_prompt = (
            "You are a safety classifier. Label prompts as BENIGN or UNSAFE.\n"
            "Return strict JSON with keys: label (benign|unsafe), score (0-1), rationale (short)."
        )
        user_prompt = f"Prompt: {text}\n\nJSON:"
        raw = self.llm_backend.generate(system_prompt, user_prompt, temperature=0.0).strip()
        try:
            data = json.loads(raw)
            label = self._normalize_label(str(data.get("label", "")))
            score = float(data.get("score", 0.0))
            is_benign = label == "benign" and score >= self.threshold
            return BenignIntentResult(is_benign=is_benign, score=score, label=label, raw=raw)
        except Exception:
            label = "unknown"
            score = 0.0
            return BenignIntentResult(is_benign=False, score=score, label=label, raw=raw)

    def check(self, text: str) -> BenignIntentResult:
        if self._pipeline:
            try:
                outputs = self._pipeline(text)
                if outputs:
                    best = max(outputs, key=lambda x: x.get("score", 0.0))
                    label = self._normalize_label(str(best.get("label", "")))
                    score = float(best.get("score", 0.0))
                    is_benign = label == "benign" and score >= self.threshold
                    return BenignIntentResult(
                        is_benign=is_benign,
                        score=score,
                        label=label,
                        raw=str(best)
                    )
            except Exception:
                pass
        llm_result = self._check_with_llm(text)
        if llm_result:
            return llm_result
        return BenignIntentResult(
            is_benign=True,
            score=1.0,
            label="unchecked",
            raw="unchecked"
        )
