"""Epistemological validation for Knowledge II writes."""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from knowledge.schema import (
    ValidationIssue,
    ValidationMode,
    ValidationResult,
    ValidationStatus,
)


class EpistemicValidator:
    """Deterministic validation pass for incoming knowledge claims.

    The validator is deliberately conservative. It does not try to prove truth;
    it records provenance, flags weak or contradictory writes, and lets the
    configured mode decide whether warnings become blockers.
    """

    def __init__(
        self,
        *,
        mode: str | ValidationMode = ValidationMode.SOFT,
        source_credibility_threshold: float = 0.25,
        require_corroboration: bool = False,
    ) -> None:
        self.mode = mode if isinstance(mode, ValidationMode) else ValidationMode(str(mode or "soft"))
        self.source_credibility_threshold = float(source_credibility_threshold)
        self.require_corroboration = bool(require_corroboration)

    def validate_claim(
        self,
        graph: Any,
        *,
        content: str,
        domain: Optional[str] = None,
        source: Optional[Dict[str, Any] | str] = None,
        confidence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        issues: list[ValidationIssue] = []
        metadata = metadata or {}
        base_confidence = self._bounded_confidence(confidence, metadata)

        source_score = self._source_score(source, metadata)
        if source_score is not None and source_score < self.source_credibility_threshold:
            issues.append(
                ValidationIssue(
                    code="low_source_credibility",
                    message="Source credibility is below the configured threshold.",
                    severity="block" if self.mode == ValidationMode.HARD else "warn",
                )
            )
            base_confidence = min(base_confidence, source_score)

        expires_at = metadata.get("expires_at") or metadata.get("valid_until")
        if expires_at is not None:
            try:
                if float(expires_at) < time.time():
                    issues.append(
                        ValidationIssue(
                            code="expired_claim",
                            message="Claim temporal validity has already expired.",
                            severity="block",
                        )
                    )
                    base_confidence = min(base_confidence, 0.1)
            except (TypeError, ValueError):
                issues.append(
                    ValidationIssue(
                        code="invalid_temporal_metadata",
                        message="Claim has an invalid expires_at/valid_until value.",
                        severity="warn",
                    )
                )

        try:
            contradictions = graph.find_potential_contradictions(content, domain=domain)
        except Exception:
            contradictions = []
        for node in contradictions:
            issues.append(
                ValidationIssue(
                    code="potential_contradiction",
                    message="Claim appears to contradict an existing claim.",
                    severity="block" if self.mode == ValidationMode.HARD else "warn",
                    existing_node_id=getattr(node, "id", None),
                )
            )
            base_confidence = min(base_confidence, 0.4)

        if self.require_corroboration:
            try:
                support_count = graph.count_supporting_sources(content, domain=domain)
            except Exception:
                support_count = 0
            if support_count < 2:
                issues.append(
                    ValidationIssue(
                        code="insufficient_corroboration",
                        message="Fewer than two independent sources support this claim.",
                        severity="warn",
                    )
                )
                base_confidence = min(base_confidence, 0.55)

        if any(issue.severity == "block" for issue in issues) and self.mode == ValidationMode.HARD:
            status = ValidationStatus.BLOCK
        elif issues:
            status = ValidationStatus.WARN
        else:
            status = ValidationStatus.PASS

        return ValidationResult(
            status=status,
            confidence=base_confidence,
            issues=issues,
            mode=self.mode,
        )

    @staticmethod
    def _bounded_confidence(confidence: Optional[float], metadata: Dict[str, Any]) -> float:
        raw = confidence
        if raw is None:
            raw = metadata.get("confidence", 0.5)
        try:
            return max(0.0, min(1.0, float(raw)))
        except (TypeError, ValueError):
            return 0.5

    @staticmethod
    def _source_score(
        source: Optional[Dict[str, Any] | str],
        metadata: Dict[str, Any],
    ) -> Optional[float]:
        candidates = [
            metadata.get("source_credibility"),
            metadata.get("source_confidence"),
        ]
        if isinstance(source, dict):
            candidates.extend([
                source.get("credibility"),
                source.get("confidence"),
            ])
        for candidate in candidates:
            if candidate is None:
                continue
            try:
                return max(0.0, min(1.0, float(candidate)))
            except (TypeError, ValueError):
                continue
        return None
