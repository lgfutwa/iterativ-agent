"""Knowledge II synthesis jobs and health reports."""

from __future__ import annotations

from typing import Any, Dict, List

from knowledge.schema import EdgeType, NodeType, ValidationStatus


class KnowledgeSynthesisEngine:
    """Runs lightweight synthesis jobs over a Knowledge II graph."""

    def __init__(self, graph) -> None:
        self.graph = graph

    def graph_health(self) -> Dict[str, Any]:
        return self.graph.graph_health()

    def contradiction_scan(self, limit: int = 50) -> Dict[str, Any]:
        claims = self.graph.iter_nodes(NodeType.CLAIM, limit=1000)
        seen: set[tuple[str, str]] = set()
        contradictions: list[dict[str, Any]] = []
        for claim in claims:
            for other in self.graph.find_potential_contradictions(
                claim.content or claim.label,
                domain=claim.domain,
                limit=10,
            ):
                pair = tuple(sorted((claim.id, other.id)))
                if pair in seen:
                    continue
                seen.add(pair)
                contradictions.append(
                    {
                        "claim_id": claim.id,
                        "claim": claim.content or claim.label,
                        "contradicts_id": other.id,
                        "contradicts": other.content or other.label,
                        "domain": claim.domain,
                    }
                )
                if len(contradictions) >= limit:
                    return {"contradictions": contradictions}
        return {"contradictions": contradictions}

    def skill_impact_audit(self, limit: int = 50) -> Dict[str, Any]:
        health = self.graph.graph_health()
        skill_count = health.get("nodes", {}).get(NodeType.SKILL.value, 0)
        produced_edges = health.get("edges", {}).get(EdgeType.PRODUCED_BY.value, 0)
        warned = health.get("validation", {}).get(ValidationStatus.WARN.value, 0)
        blocked = health.get("validation", {}).get(ValidationStatus.BLOCK.value, 0)
        return {
            "skill_nodes": skill_count,
            "produced_claim_edges": produced_edges,
            "warned_claims": warned,
            "blocked_claims": blocked,
            "limit": limit,
        }

    def weekly_report(self) -> Dict[str, Any]:
        return {
            "graph_health": self.graph_health(),
            "contradictions": self.contradiction_scan(),
            "skill_impact": self.skill_impact_audit(),
        }
