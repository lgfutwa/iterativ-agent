"""Runtime hooks that connect tools and memory to Knowledge II."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from knowledge.graph.sqlite import SQLiteKnowledgeGraph
from knowledge.validator import EpistemicValidator

logger = logging.getLogger(__name__)

_HOOKS_SINGLETON = None


def _knowledge_config() -> Dict[str, Any]:
    try:
        from iterativ_cli.config import load_config

        cfg = load_config()
        return dict((cfg or {}).get("knowledge", {}) or {})
    except Exception:
        return {}


def get_knowledge_graph_from_config(config: Optional[Dict[str, Any]] = None) -> Optional[SQLiteKnowledgeGraph]:
    config = config or _knowledge_config()
    if not config.get("enabled", True):
        return None
    db_path = str(config.get("db_path") or "").strip()
    try:
        return SQLiteKnowledgeGraph(Path(db_path).expanduser() if db_path else None)
    except Exception as exc:
        logger.debug("Knowledge graph unavailable: %s", exc, exc_info=True)
        return None


class KnowledgeHooks:
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or _knowledge_config()
        self.enabled = bool(self.config.get("enabled", True))
        self.capture_tool_results = bool(self.config.get("capture_tool_results", True))
        self.graph = get_knowledge_graph_from_config(self.config) if self.enabled else None
        self.validator = EpistemicValidator(
            mode=self.config.get("validation_mode", "soft"),
            source_credibility_threshold=float(
                self.config.get("source_credibility_threshold", 0.25)
            ),
            require_corroboration=bool(self.config.get("require_corroboration", False)),
        )

    def before_tool_execution(
        self,
        *,
        tool_name: str,
        args: Dict[str, Any],
        session_id: str = "",
        task_id: str = "",
    ):
        if not (self.enabled and self.graph):
            return None
        domains = args.get("domains") if isinstance(args, dict) else None
        required_claims = args.get("requires_claims") if isinstance(args, dict) else None
        if not domains and not required_claims:
            return None
        try:
            return self.graph.get_relevant_knowledge(
                tool_name,
                domains=domains if isinstance(domains, list) else None,
                required_claims=required_claims if isinstance(required_claims, list) else None,
            )
        except Exception as exc:
            logger.debug("Knowledge pre-tool hook failed: %s", exc, exc_info=True)
            return None

    def after_tool_execution(
        self,
        *,
        tool_name: str,
        args: Dict[str, Any],
        result: str,
        session_id: str = "",
        task_id: str = "",
        tool_call_id: str = "",
        duration_ms: Optional[int] = None,
    ) -> None:
        if not (self.enabled and self.capture_tool_results and self.graph):
            return
        try:
            self.graph.record_tool_result(
                tool_name=tool_name,
                args=args,
                result=result,
                session_id=session_id,
                task_id=task_id,
                tool_call_id=tool_call_id,
                duration_ms=duration_ms,
            )
        except Exception as exc:
            logger.debug("Knowledge post-tool hook failed: %s", exc, exc_info=True)


def get_knowledge_hooks() -> KnowledgeHooks:
    global _HOOKS_SINGLETON
    if _HOOKS_SINGLETON is None:
        _HOOKS_SINGLETON = KnowledgeHooks()
    return _HOOKS_SINGLETON
