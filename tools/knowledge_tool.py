#!/usr/bin/env python3
"""Knowledge II graph tool."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from knowledge.graph.sqlite import SQLiteKnowledgeGraph
from knowledge.synthesis import KnowledgeSynthesisEngine
from tools.registry import registry, tool_error


def _default_graph() -> Optional[SQLiteKnowledgeGraph]:
    try:
        from knowledge.hooks import get_knowledge_graph_from_config

        return get_knowledge_graph_from_config()
    except Exception:
        return None


def _node_to_dict(node) -> Dict[str, Any]:
    return {
        "id": node.id,
        "type": node.node_type.value,
        "label": node.label,
        "content": node.content,
        "domain": node.domain,
        "confidence": node.confidence,
        "validation_status": node.validation_status.value,
        "metadata": node.metadata,
    }


def knowledge_graph_tool(
    *,
    action: str,
    query: str = "",
    content: str = "",
    domain: str = "",
    domains: Optional[list[str]] = None,
    required_claims: Optional[list[str]] = None,
    source_label: str = "",
    confidence: Optional[float] = None,
    limit: int = 10,
    module: str = "",
    include_user: bool = True,
    graph: Optional[SQLiteKnowledgeGraph] = None,
) -> str:
    graph = graph or _default_graph()
    if graph is None:
        return tool_error("Knowledge graph is not available or is disabled.", success=False)

    action = (action or "").strip()
    if action == "health":
        return json.dumps({"success": True, "health": graph.graph_health()}, ensure_ascii=False)

    if action == "search":
        claims = graph.search_claims(query, domains=domains, limit=limit)
        return json.dumps(
            {"success": True, "claims": [_node_to_dict(node) for node in claims]},
            ensure_ascii=False,
        )

    if action == "context":
        context = graph.get_relevant_knowledge(
            query,
            domains=domains,
            required_claims=required_claims,
            limit=limit,
        )
        return json.dumps(
            {
                "success": True,
                "sufficiency_score": context.sufficiency_score,
                "missing_claims": context.missing_claims,
                "claims": [_node_to_dict(node) for node in context.claims],
            },
            ensure_ascii=False,
        )

    if action == "add_claim":
        if not content:
            return tool_error("content is required for add_claim.", success=False)
        result = graph.integrate_claim(
            content,
            domain=domain or None,
            source={"label": source_label or "knowledge_graph_tool", "credibility": 0.6},
            confidence=confidence,
            produced_by="knowledge_graph_tool",
        )
        return json.dumps({"success": bool(result.get("success")), **result}, ensure_ascii=False)

    if action == "contradictions":
        engine = KnowledgeSynthesisEngine(graph)
        return json.dumps(
            {"success": True, **engine.contradiction_scan(limit=limit)},
            ensure_ascii=False,
        )

    if action == "list_domain_modules":
        from knowledge.domain_modules import iter_domain_modules

        modules = [
            {
                "id": item.get("@id"),
                "name": item.get("name"),
                "description": item.get("description"),
                "concept_count": len(item.get("concepts") or []),
            }
            for item in iter_domain_modules()
        ]
        return json.dumps({"success": True, "modules": modules}, ensure_ascii=False)

    if action == "import_domain_module":
        from knowledge.domain_modules import get_domain_module

        if not module:
            return tool_error("module is required for import_domain_module.", success=False)
        domain_module = get_domain_module(module)
        if domain_module is None:
            return tool_error(f"Domain module '{module}' not found.", success=False)
        result = graph.import_domain_module(domain_module)
        return json.dumps(result, ensure_ascii=False)

    if action == "import_memory":
        from tools.memory_tool import ENTRY_DELIMITER, get_memory_dir

        mem_dir = get_memory_dir()
        imported = 0
        targets = ["memory", "user"] if include_user else ["memory"]
        for target in targets:
            path = mem_dir / ("USER.md" if target == "user" else "MEMORY.md")
            if not path.exists():
                continue
            raw = path.read_text(encoding="utf-8")
            entries = [entry.strip() for entry in raw.split(ENTRY_DELIMITER) if entry.strip()]
            for entry in entries:
                result = graph.record_memory_entry(
                    target=target,
                    content=entry,
                    action="import",
                    metadata={"source_path": str(path)},
                )
                if result.get("success"):
                    imported += 1
        return json.dumps({"success": True, "claims_imported": imported}, ensure_ascii=False)

    return tool_error(
        "Unknown action "
        f"'{action}'. Use: health, search, context, add_claim, contradictions, "
        "list_domain_modules, import_domain_module, import_memory.",
        success=False,
    )


def check_knowledge_requirements() -> bool:
    try:
        from iterativ_cli.config import load_config

        cfg = load_config()
        return bool((cfg.get("knowledge", {}) or {}).get("enabled", True))
    except Exception:
        return True


KNOWLEDGE_GRAPH_SCHEMA = {
    "name": "knowledge_graph",
    "description": (
        "Query and write the Knowledge II graph. Use it for provenance-aware "
        "claims, graph health, contradiction checks, and domain-scoped context."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "health",
                    "search",
                    "context",
                    "add_claim",
                    "contradictions",
                    "list_domain_modules",
                    "import_domain_module",
                    "import_memory",
                ],
                "description": "Graph operation to perform.",
            },
            "query": {
                "type": "string",
                "description": "Search/context query or task description.",
            },
            "content": {
                "type": "string",
                "description": "Claim content for add_claim.",
            },
            "domain": {
                "type": "string",
                "description": "Domain for add_claim, e.g. iterativ.iks.",
            },
            "domains": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Domain filters for search/context.",
            },
            "required_claims": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Claims that must be present for context sufficiency.",
            },
            "source_label": {
                "type": "string",
                "description": "Human-readable provenance label for add_claim.",
            },
            "confidence": {
                "type": "number",
                "description": "Optional confidence score from 0 to 1 for add_claim.",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum rows to return.",
            },
            "module": {
                "type": "string",
                "description": "Domain module id/name for import_domain_module, e.g. iterativ.iks.",
            },
            "include_user": {
                "type": "boolean",
                "description": "For import_memory, include USER.md as user.profile claims.",
            },
        },
        "required": ["action"],
    },
}


registry.register(
    name="knowledge_graph",
    toolset="knowledge",
    schema=KNOWLEDGE_GRAPH_SCHEMA,
    handler=lambda args, **kw: knowledge_graph_tool(
        action=args.get("action", ""),
        query=args.get("query", ""),
        content=args.get("content", ""),
        domain=args.get("domain", ""),
        domains=args.get("domains"),
        required_claims=args.get("required_claims"),
        source_label=args.get("source_label", ""),
        confidence=args.get("confidence"),
        limit=args.get("limit", 10),
        module=args.get("module", ""),
        include_user=args.get("include_user", True),
        graph=kw.get("graph"),
    ),
    check_fn=check_knowledge_requirements,
)
