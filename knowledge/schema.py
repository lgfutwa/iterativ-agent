"""Core Knowledge II node, edge, and validation schemas."""

from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class NodeType(str, Enum):
    CLAIM = "Claim"
    CONCEPT = "Concept"
    DOMAIN = "Domain"
    SOURCE = "Source"
    SKILL = "Skill"
    USER = "User"


class EdgeType(str, Enum):
    DERIVES_FROM = "derives_from"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    SYNTHESIZES = "synthesizes"
    DOMAIN_OF = "domain_of"
    USED_IN = "used_in"
    ABOUT_USER = "about_user"
    PRODUCED_BY = "produced_by"


class ValidationStatus(str, Enum):
    UNVALIDATED = "unvalidated"
    PASS = "pass"
    WARN = "warn"
    BLOCK = "block"


class ValidationMode(str, Enum):
    SOFT = "soft"
    HARD = "hard"


_SPACE_RE = re.compile(r"\s+")


def normalize_text(value: str) -> str:
    """Normalize text for stable IDs and rough equality checks."""
    return _SPACE_RE.sub(" ", (value or "").strip()).lower()


def stable_id(*parts: Any, prefix: str = "k") -> str:
    """Return a stable content-addressed ID for graph rows."""
    joined = "\x1f".join(normalize_text(str(part)) for part in parts if part is not None)
    digest = hashlib.sha256(joined.encode("utf-8")).hexdigest()[:24]
    return f"{prefix}_{digest}"


def utc_timestamp() -> float:
    return time.time()


@dataclass(frozen=True)
class KnowledgeNode:
    id: str
    node_type: NodeType
    label: str
    content: Optional[str] = None
    domain: Optional[str] = None
    confidence: float = 0.5
    validation_status: ValidationStatus = ValidationStatus.UNVALIDATED
    created_at: float = field(default_factory=utc_timestamp)
    updated_at: float = field(default_factory=utc_timestamp)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeEdge:
    id: str
    source_id: str
    edge_type: EdgeType
    target_id: str
    confidence: float = 0.5
    created_at: float = field(default_factory=utc_timestamp)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    severity: str = "warn"
    existing_node_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
            "existing_node_id": self.existing_node_id,
        }


@dataclass(frozen=True)
class ValidationResult:
    status: ValidationStatus
    confidence: float
    issues: List[ValidationIssue] = field(default_factory=list)
    mode: ValidationMode = ValidationMode.SOFT

    @property
    def blocked(self) -> bool:
        return self.status == ValidationStatus.BLOCK

    def to_metadata(self) -> Dict[str, Any]:
        return {
            "validation_status": self.status.value,
            "validation_confidence": self.confidence,
            "validation_mode": self.mode.value,
            "validation_issues": [issue.to_dict() for issue in self.issues],
        }


@dataclass(frozen=True)
class KnowledgeContext:
    claims: List[KnowledgeNode] = field(default_factory=list)
    domains: List[str] = field(default_factory=list)
    required_claims: List[str] = field(default_factory=list)
    missing_claims: List[str] = field(default_factory=list)
    sufficiency_score: float = 0.0

    def as_prompt_block(self) -> str:
        if not self.claims:
            return ""
        lines = ["KNOWLEDGE II CONTEXT"]
        for claim in self.claims:
            domain = f" [{claim.domain}]" if claim.domain else ""
            lines.append(f"-{domain} {claim.content or claim.label}")
        if self.missing_claims:
            lines.append("Missing claims: " + "; ".join(self.missing_claims))
        return "\n".join(lines)
