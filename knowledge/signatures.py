"""Knowledge signatures for skills and scheduled skill runs."""

from __future__ import annotations

from typing import Any, Dict, Optional


def normalize_knowledge_signature(raw: Any) -> Optional[Dict[str, Any]]:
    """Normalize a skill ``knowledge_signature`` frontmatter block.

    Supported fields mirror the proposal:
      - requires_domains
      - requires_claims
      - produces_claims
      - sufficiency_threshold
    """
    if not isinstance(raw, dict):
        return None

    requires_domains = _string_list(raw.get("requires_domains"))
    requires_claims = _string_list(raw.get("requires_claims"))
    produces_claims = _string_list(raw.get("produces_claims"))
    if not (requires_domains or requires_claims or produces_claims):
        return None

    threshold = raw.get("sufficiency_threshold", raw.get("threshold", 0.75))
    try:
        threshold_value = max(0.0, min(1.0, float(threshold)))
    except (TypeError, ValueError):
        threshold_value = 0.75

    return {
        "requires_domains": requires_domains,
        "requires_claims": requires_claims,
        "produces_claims": produces_claims,
        "sufficiency_threshold": threshold_value,
    }


def build_skill_knowledge_context(
    signature: Optional[Dict[str, Any]],
    *,
    task: str = "",
    graph=None,
    limit: int = 8,
) -> Optional[Dict[str, Any]]:
    if not signature or graph is None:
        return None
    try:
        context = graph.get_relevant_knowledge(
            task or " ".join(signature.get("requires_claims") or []),
            domains=signature.get("requires_domains") or None,
            required_claims=signature.get("requires_claims") or None,
            limit=limit,
        )
    except Exception:
        return None

    return {
        "sufficiency_score": context.sufficiency_score,
        "sufficient": context.sufficiency_score >= signature.get("sufficiency_threshold", 0.75),
        "missing_claims": context.missing_claims,
        "claims": [
            {
                "id": claim.id,
                "content": claim.content or claim.label,
                "domain": claim.domain,
                "confidence": claim.confidence,
                "validation_status": claim.validation_status.value,
            }
            for claim in context.claims
        ],
    }


def format_knowledge_context_block(
    signature: Optional[Dict[str, Any]],
    context: Optional[Dict[str, Any]],
) -> str:
    if not signature:
        return ""

    lines = ["[Knowledge II signature for this skill]"]
    if signature.get("requires_domains"):
        lines.append("Requires domains: " + ", ".join(signature["requires_domains"]))
    if signature.get("requires_claims"):
        lines.append("Requires claims: " + "; ".join(signature["requires_claims"]))
    if signature.get("produces_claims"):
        lines.append("Produces claims: " + "; ".join(signature["produces_claims"]))

    if context:
        lines.append(f"Sufficiency score: {context.get('sufficiency_score', 0):.2f}")
        missing = context.get("missing_claims") or []
        if missing:
            lines.append("Missing claims: " + "; ".join(missing))
        claims = context.get("claims") or []
        if claims:
            lines.append("Relevant graph claims:")
            for claim in claims[:8]:
                domain = f" [{claim.get('domain')}]" if claim.get("domain") else ""
                lines.append(f"-{domain} {claim.get('content')}")
    else:
        lines.append("No graph context was available for this signature.")

    return "\n".join(lines)


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text and text not in result:
            result.append(text)
    return result
