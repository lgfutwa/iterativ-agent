"""SQLite-backed Knowledge II graph store."""

from __future__ import annotations

import json
import logging
import re
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from iterativ_constants import get_iterativ_home
from knowledge.schema import (
    EdgeType,
    KnowledgeContext,
    KnowledgeEdge,
    KnowledgeNode,
    NodeType,
    ValidationMode,
    ValidationStatus,
    normalize_text,
    stable_id,
)
from knowledge.validator import EpistemicValidator

logger = logging.getLogger(__name__)

GRAPH_SCHEMA_VERSION = 1

GRAPH_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS knowledge_schema_version (
    version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS knowledge_nodes (
    id TEXT PRIMARY KEY,
    node_type TEXT NOT NULL,
    label TEXT NOT NULL,
    content TEXT,
    domain TEXT,
    confidence REAL NOT NULL DEFAULT 0.5,
    validation_status TEXT NOT NULL DEFAULT 'unvalidated',
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    metadata TEXT
);

CREATE TABLE IF NOT EXISTS knowledge_edges (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    edge_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 0.5,
    created_at REAL NOT NULL,
    metadata TEXT,
    UNIQUE(source_id, edge_type, target_id),
    FOREIGN KEY(source_id) REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
    FOREIGN KEY(target_id) REFERENCES knowledge_nodes(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_type ON knowledge_nodes(node_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_domain ON knowledge_nodes(domain);
CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_validation ON knowledge_nodes(validation_status);
CREATE INDEX IF NOT EXISTS idx_knowledge_edges_source ON knowledge_edges(source_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_edges_target ON knowledge_edges(target_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_edges_type ON knowledge_edges(edge_type);
"""

_NEGATION_REPLACEMENTS = (
    (" is not ", " is "),
    (" are not ", " are "),
    (" was not ", " was "),
    (" were not ", " were "),
    (" does not ", " does "),
    (" do not ", " do "),
    (" did not ", " did "),
    (" cannot ", " can "),
    (" can't ", " can "),
    (" no ", " "),
    (" not ", " "),
)


def get_default_knowledge_db_path() -> Path:
    return get_iterativ_home() / "knowledge" / "graph.db"


class SQLiteKnowledgeGraph:
    """Small graph abstraction over SQLite tables.

    It uses generic node/edge tables so the first production slice can run
    locally with no new infrastructure while leaving room for ArangoDB/Neo4j
    adapters behind the same conceptual API later.
    """

    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = Path(db_path) if db_path else get_default_knowledge_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,
            timeout=1.0,
            isolation_level=None,
        )
        self._conn.row_factory = sqlite3.Row
        self._configure_connection()
        self._init_schema()

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                try:
                    self._conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
                except Exception:
                    pass
                self._conn.close()
                self._conn = None

    def _configure_connection(self) -> None:
        try:
            self._conn.execute("PRAGMA journal_mode=WAL")
        except sqlite3.OperationalError:
            self._conn.execute("PRAGMA journal_mode=DELETE")
        self._conn.execute("PRAGMA foreign_keys=ON")

    def _init_schema(self) -> None:
        with self._lock:
            self._conn.executescript(GRAPH_SCHEMA_SQL)
            row = self._conn.execute(
                "SELECT version FROM knowledge_schema_version LIMIT 1"
            ).fetchone()
            if row is None:
                self._conn.execute(
                    "INSERT INTO knowledge_schema_version (version) VALUES (?)",
                    (GRAPH_SCHEMA_VERSION,),
                )
            elif int(row["version"]) < GRAPH_SCHEMA_VERSION:
                self._conn.execute(
                    "UPDATE knowledge_schema_version SET version = ?",
                    (GRAPH_SCHEMA_VERSION,),
                )

    def _execute_write(self, fn):
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                result = fn(self._conn)
                self._conn.commit()
                return result
            except BaseException:
                try:
                    self._conn.rollback()
                except Exception:
                    pass
                raise

    def upsert_node(
        self,
        *,
        node_type: NodeType | str,
        label: str,
        content: Optional[str] = None,
        domain: Optional[str] = None,
        confidence: float = 0.5,
        validation_status: ValidationStatus | str = ValidationStatus.UNVALIDATED,
        metadata: Optional[Dict[str, Any]] = None,
        node_id: Optional[str] = None,
    ) -> KnowledgeNode:
        node_type = node_type if isinstance(node_type, NodeType) else NodeType(str(node_type))
        validation_status = (
            validation_status
            if isinstance(validation_status, ValidationStatus)
            else ValidationStatus(str(validation_status))
        )
        if node_id is None:
            id_basis = content if node_type == NodeType.CLAIM and content else label
            node_id = stable_id(node_type.value, domain or "", id_basis, prefix="kn")
        now = time.time()
        metadata_json = json.dumps(metadata or {}, sort_keys=True)

        def _do(conn):
            existing = conn.execute(
                "SELECT created_at FROM knowledge_nodes WHERE id = ?",
                (node_id,),
            ).fetchone()
            created_at = float(existing["created_at"]) if existing else now
            conn.execute(
                """
                INSERT INTO knowledge_nodes (
                    id, node_type, label, content, domain, confidence,
                    validation_status, created_at, updated_at, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    label = excluded.label,
                    content = excluded.content,
                    domain = excluded.domain,
                    confidence = excluded.confidence,
                    validation_status = excluded.validation_status,
                    updated_at = excluded.updated_at,
                    metadata = excluded.metadata
                """,
                (
                    node_id,
                    node_type.value,
                    label,
                    content,
                    domain,
                    float(confidence),
                    validation_status.value,
                    created_at,
                    now,
                    metadata_json,
                ),
            )
            return self._row_to_node(
                conn.execute("SELECT * FROM knowledge_nodes WHERE id = ?", (node_id,)).fetchone()
            )

        return self._execute_write(_do)

    def add_edge(
        self,
        *,
        source_id: str,
        edge_type: EdgeType | str,
        target_id: str,
        confidence: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> KnowledgeEdge:
        edge_type = edge_type if isinstance(edge_type, EdgeType) else EdgeType(str(edge_type))
        edge_id = stable_id(source_id, edge_type.value, target_id, prefix="ke")
        now = time.time()
        metadata_json = json.dumps(metadata or {}, sort_keys=True)

        def _do(conn):
            conn.execute(
                """
                INSERT INTO knowledge_edges (
                    id, source_id, edge_type, target_id, confidence, created_at, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_id, edge_type, target_id) DO UPDATE SET
                    confidence = excluded.confidence,
                    metadata = excluded.metadata
                """,
                (
                    edge_id,
                    source_id,
                    edge_type.value,
                    target_id,
                    float(confidence),
                    now,
                    metadata_json,
                ),
            )
            return self._row_to_edge(
                conn.execute("SELECT * FROM knowledge_edges WHERE id = ?", (edge_id,)).fetchone()
            )

        return self._execute_write(_do)

    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        row = self._conn.execute(
            "SELECT * FROM knowledge_nodes WHERE id = ?",
            (node_id,),
        ).fetchone()
        return self._row_to_node(row) if row else None

    def integrate_claim(
        self,
        content: str,
        *,
        domain: Optional[str] = None,
        source: Optional[str | Dict[str, Any]] = None,
        confidence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        produced_by: Optional[str] = None,
        validator: Optional[EpistemicValidator] = None,
        mode: str | ValidationMode = ValidationMode.SOFT,
    ) -> Dict[str, Any]:
        content = (content or "").strip()
        if not content:
            return {"success": False, "error": "Claim content cannot be empty."}

        validator = validator or EpistemicValidator(mode=mode)
        validation = validator.validate_claim(
            self,
            content=content,
            domain=domain,
            source=source,
            confidence=confidence,
            metadata=metadata,
        )
        if validation.blocked:
            return {
                "success": False,
                "blocked": True,
                "validation": validation.to_metadata(),
            }

        node_metadata = dict(metadata or {})
        node_metadata.update(validation.to_metadata())
        claim = self.upsert_node(
            node_type=NodeType.CLAIM,
            label=self._claim_label(content),
            content=content,
            domain=domain,
            confidence=validation.confidence,
            validation_status=validation.status,
            metadata=node_metadata,
        )

        if domain:
            domain_node = self.upsert_node(
                node_type=NodeType.DOMAIN,
                label=domain,
                content=f"Knowledge domain: {domain}",
                domain=domain,
                confidence=1.0,
                validation_status=ValidationStatus.PASS,
                metadata={"system": True},
            )
            self.add_edge(
                source_id=claim.id,
                edge_type=EdgeType.DOMAIN_OF,
                target_id=domain_node.id,
                confidence=1.0,
            )

        source_node = self._upsert_source_node(source)
        if source_node:
            self.add_edge(
                source_id=claim.id,
                edge_type=EdgeType.DERIVES_FROM,
                target_id=source_node.id,
                confidence=validation.confidence,
            )

        if produced_by:
            skill = self.upsert_node(
                node_type=NodeType.SKILL,
                label=str(produced_by),
                content=f"Knowledge producer: {produced_by}",
                confidence=1.0,
                validation_status=ValidationStatus.PASS,
                metadata={"system": True},
            )
            self.add_edge(
                source_id=claim.id,
                edge_type=EdgeType.PRODUCED_BY,
                target_id=skill.id,
                confidence=1.0,
            )

        for issue in validation.issues:
            if issue.code == "potential_contradiction" and issue.existing_node_id:
                self.add_edge(
                    source_id=claim.id,
                    edge_type=EdgeType.CONTRADICTS,
                    target_id=issue.existing_node_id,
                    confidence=validation.confidence,
                    metadata=issue.to_dict(),
                )

        return {
            "success": True,
            "claim_id": claim.id,
            "validation": validation.to_metadata(),
        }

    def record_memory_entry(
        self,
        *,
        target: str,
        content: str,
        action: str = "add",
        session_id: Optional[str] = None,
        tool_call_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        domain = "user.profile" if target == "user" else "agent.memory"
        event_metadata = {
            "memory_target": target,
            "memory_action": action,
            "session_id": session_id,
            "tool_call_id": tool_call_id,
        }
        event_metadata.update(metadata or {})
        return self.integrate_claim(
            content,
            domain=domain,
            source={"label": f"MEMORY.md:{target}", "credibility": 0.8},
            confidence=0.7,
            metadata=event_metadata,
            produced_by="memory",
        )

    def import_domain_module(self, module: Dict[str, Any]) -> Dict[str, Any]:
        """Import a JSON-LD domain module into graph nodes and edges."""
        module_id = str(module.get("@id") or module.get("name") or "").strip()
        if not module_id:
            return {"success": False, "error": "Domain module is missing @id/name."}

        domain_node = self.upsert_node(
            node_type=NodeType.DOMAIN,
            label=module_id,
            content=str(module.get("description") or f"Knowledge domain: {module_id}"),
            domain=module_id,
            confidence=1.0,
            validation_status=ValidationStatus.PASS,
            metadata={"module": True, "name": module.get("name")},
        )

        concept_count = 0
        concept_ids: dict[str, str] = {}
        for concept in module.get("concepts") or []:
            if not isinstance(concept, dict):
                continue
            concept_id = str(concept.get("@id") or concept.get("id") or concept.get("name") or "").strip()
            if not concept_id:
                continue
            concept_node = self.upsert_node(
                node_type=NodeType.CONCEPT,
                label=str(concept.get("name") or concept_id),
                content=str(concept.get("definition") or concept.get("description") or concept_id),
                domain=module_id,
                confidence=1.0,
                validation_status=ValidationStatus.PASS,
                metadata={"module_id": module_id, "source_id": concept_id},
            )
            concept_ids[concept_id] = concept_node.id
            self.add_edge(
                source_id=concept_node.id,
                edge_type=EdgeType.DOMAIN_OF,
                target_id=domain_node.id,
                confidence=1.0,
            )
            concept_count += 1

        relationship_count = 0
        for rel in module.get("relationships") or []:
            if not isinstance(rel, dict):
                continue
            source_ref = str(rel.get("source") or "").strip()
            target_ref = str(rel.get("target") or "").strip()
            predicate = str(rel.get("predicate") or "").strip()
            source_id = concept_ids.get(source_ref)
            target_id = concept_ids.get(target_ref)
            if not (source_id and target_id and predicate):
                continue
            try:
                edge_type = EdgeType(predicate)
            except ValueError:
                edge_type = EdgeType.SUPPORTS
            self.add_edge(
                source_id=source_id,
                edge_type=edge_type,
                target_id=target_id,
                confidence=1.0,
                metadata={"module_id": module_id, "predicate": predicate},
            )
            relationship_count += 1

        return {
            "success": True,
            "domain_id": domain_node.id,
            "module_id": module_id,
            "concepts_imported": concept_count,
            "relationships_imported": relationship_count,
        }

    def record_tool_result(
        self,
        *,
        tool_name: str,
        args: Optional[Dict[str, Any]] = None,
        result: str = "",
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        tool_call_id: Optional[str] = None,
        duration_ms: Optional[int] = None,
    ) -> Dict[str, Any]:
        claims = self.extract_structured_claims(result)
        if not claims:
            return {"success": True, "claims_recorded": 0}

        recorded = 0
        source = {
            "label": f"tool:{tool_name}",
            "content": self._preview(result, 1000),
            "credibility": 0.6,
        }
        base_metadata = {
            "tool_name": tool_name,
            "tool_args": args or {},
            "session_id": session_id,
            "task_id": task_id,
            "tool_call_id": tool_call_id,
            "duration_ms": duration_ms,
        }
        for claim in claims:
            if isinstance(claim, str):
                content = claim
                domain = None
                confidence = 0.55
                metadata = {}
            elif isinstance(claim, dict):
                content = str(claim.get("content") or claim.get("claim") or "").strip()
                domain = claim.get("domain")
                confidence = claim.get("confidence", 0.55)
                metadata = dict(claim.get("metadata") or {})
            else:
                continue
            if not content:
                continue
            metadata.update(base_metadata)
            result_obj = self.integrate_claim(
                content,
                domain=domain,
                source=source,
                confidence=confidence,
                metadata=metadata,
                produced_by=tool_name,
            )
            if result_obj.get("success"):
                recorded += 1
        return {"success": True, "claims_recorded": recorded}

    @staticmethod
    def extract_structured_claims(result: str) -> List[Any]:
        """Extract claims only from explicit structured result fields."""
        if not result:
            return []
        try:
            data = json.loads(result)
        except (TypeError, ValueError):
            return []
        if not isinstance(data, dict):
            return []
        claims = data.get("knowledge_claims")
        if isinstance(claims, list):
            return claims
        claim = data.get("knowledge_claim")
        if claim:
            return [claim]
        return []

    def search_claims(
        self,
        query: str,
        *,
        domains: Optional[Iterable[str]] = None,
        limit: int = 10,
    ) -> List[KnowledgeNode]:
        query = (query or "").strip()
        domains_list = [d for d in (domains or []) if d]
        clauses = ["node_type = ?"]
        params: list[Any] = [NodeType.CLAIM.value]
        if query:
            terms = [term for term in re.split(r"\s+", query) if len(term) > 2][:6]
            if terms:
                term_clauses = []
                for term in terms:
                    term_clauses.append("(LOWER(content) LIKE ? OR LOWER(label) LIKE ?)")
                    like = f"%{term.lower()}%"
                    params.extend([like, like])
                clauses.append("(" + " OR ".join(term_clauses) + ")")
        if domains_list:
            placeholders = ",".join("?" for _ in domains_list)
            clauses.append(f"domain IN ({placeholders})")
            params.extend(domains_list)
        params.append(max(1, int(limit)))
        rows = self._conn.execute(
            f"""
            SELECT * FROM knowledge_nodes
            WHERE {' AND '.join(clauses)}
            ORDER BY confidence DESC, updated_at DESC
            LIMIT ?
            """,
            tuple(params),
        ).fetchall()
        return [self._row_to_node(row) for row in rows]

    def get_relevant_knowledge(
        self,
        task: str,
        *,
        domains: Optional[Iterable[str]] = None,
        required_claims: Optional[Iterable[str]] = None,
        limit: int = 8,
    ) -> KnowledgeContext:
        required = [claim for claim in (required_claims or []) if claim]
        claims = self.search_claims(task, domains=domains, limit=limit)
        missing: list[str] = []
        for required_claim in required:
            matches = self.search_claims(required_claim, domains=domains, limit=1)
            if matches:
                claims.extend(matches)
            else:
                missing.append(required_claim)

        deduped: dict[str, KnowledgeNode] = {}
        for claim in claims:
            deduped[claim.id] = claim
        denom = max(1, len(required) or 1)
        sufficiency = 1.0 if not required else max(0.0, (len(required) - len(missing)) / denom)
        return KnowledgeContext(
            claims=list(deduped.values())[:limit],
            domains=list(domains or []),
            required_claims=required,
            missing_claims=missing,
            sufficiency_score=sufficiency,
        )

    def find_potential_contradictions(
        self,
        content: str,
        *,
        domain: Optional[str] = None,
        limit: int = 5,
    ) -> List[KnowledgeNode]:
        key, polarity = self._polarity_key(content)
        if not key:
            return []
        clauses = ["node_type = ?"]
        params: list[Any] = [NodeType.CLAIM.value]
        if domain:
            clauses.append("domain = ?")
            params.append(domain)
        rows = self._conn.execute(
            f"SELECT * FROM knowledge_nodes WHERE {' AND '.join(clauses)} LIMIT 200",
            tuple(params),
        ).fetchall()
        contradictions = []
        for row in rows:
            node = self._row_to_node(row)
            existing_key, existing_polarity = self._polarity_key(node.content or node.label)
            if existing_key == key and existing_polarity != polarity:
                contradictions.append(node)
                if len(contradictions) >= limit:
                    break
        return contradictions

    def count_supporting_sources(self, content: str, *, domain: Optional[str] = None) -> int:
        key, polarity = self._polarity_key(content)
        matches = self.search_claims(content, domains=[domain] if domain else None, limit=20)
        claim_ids = [
            node.id for node in matches
            if self._polarity_key(node.content or node.label) == (key, polarity)
        ]
        if not claim_ids:
            return 0
        placeholders = ",".join("?" for _ in claim_ids)
        row = self._conn.execute(
            f"""
            SELECT COUNT(DISTINCT target_id) AS count
            FROM knowledge_edges
            WHERE source_id IN ({placeholders})
              AND edge_type = ?
            """,
            (*claim_ids, EdgeType.DERIVES_FROM.value),
        ).fetchone()
        return int(row["count"] or 0)

    def graph_health(self) -> Dict[str, Any]:
        node_rows = self._conn.execute(
            "SELECT node_type, COUNT(*) AS count FROM knowledge_nodes GROUP BY node_type"
        ).fetchall()
        edge_rows = self._conn.execute(
            "SELECT edge_type, COUNT(*) AS count FROM knowledge_edges GROUP BY edge_type"
        ).fetchall()
        status_rows = self._conn.execute(
            "SELECT validation_status, COUNT(*) AS count FROM knowledge_nodes GROUP BY validation_status"
        ).fetchall()
        return {
            "nodes": {row["node_type"]: int(row["count"]) for row in node_rows},
            "edges": {row["edge_type"]: int(row["count"]) for row in edge_rows},
            "validation": {row["validation_status"]: int(row["count"]) for row in status_rows},
        }

    def iter_nodes(self, node_type: NodeType | str | None = None, limit: int = 100) -> List[KnowledgeNode]:
        if node_type:
            node_type = node_type if isinstance(node_type, NodeType) else NodeType(str(node_type))
            rows = self._conn.execute(
                "SELECT * FROM knowledge_nodes WHERE node_type = ? ORDER BY updated_at DESC LIMIT ?",
                (node_type.value, max(1, int(limit))),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM knowledge_nodes ORDER BY updated_at DESC LIMIT ?",
                (max(1, int(limit)),),
            ).fetchall()
        return [self._row_to_node(row) for row in rows]

    def _upsert_source_node(self, source: Optional[str | Dict[str, Any]]) -> Optional[KnowledgeNode]:
        if not source:
            return None
        if isinstance(source, dict):
            label = str(source.get("label") or source.get("name") or source.get("url") or "unknown-source")
            content = source.get("content") or source.get("url") or label
            confidence = source.get("credibility", source.get("confidence", 0.5))
            metadata = dict(source)
        else:
            label = str(source)
            content = label
            confidence = 0.5
            metadata = {}
        return self.upsert_node(
            node_type=NodeType.SOURCE,
            label=label,
            content=str(content),
            confidence=float(confidence),
            validation_status=ValidationStatus.PASS,
            metadata=metadata,
        )

    @staticmethod
    def _claim_label(content: str) -> str:
        content = " ".join(content.split())
        return content[:80] + ("..." if len(content) > 80 else "")

    @staticmethod
    def _preview(value: str, limit: int) -> str:
        value = value or ""
        return value[:limit] + ("..." if len(value) > limit else "")

    @staticmethod
    def _metadata_from_json(value: Optional[str]) -> Dict[str, Any]:
        if not value:
            return {}
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError):
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def _row_to_node(self, row: sqlite3.Row) -> KnowledgeNode:
        return KnowledgeNode(
            id=row["id"],
            node_type=NodeType(row["node_type"]),
            label=row["label"],
            content=row["content"],
            domain=row["domain"],
            confidence=float(row["confidence"]),
            validation_status=ValidationStatus(row["validation_status"]),
            created_at=float(row["created_at"]),
            updated_at=float(row["updated_at"]),
            metadata=self._metadata_from_json(row["metadata"]),
        )

    def _row_to_edge(self, row: sqlite3.Row) -> KnowledgeEdge:
        return KnowledgeEdge(
            id=row["id"],
            source_id=row["source_id"],
            edge_type=EdgeType(row["edge_type"]),
            target_id=row["target_id"],
            confidence=float(row["confidence"]),
            created_at=float(row["created_at"]),
            metadata=self._metadata_from_json(row["metadata"]),
        )

    @staticmethod
    def _polarity_key(content: str) -> tuple[str, bool]:
        norm = f" {normalize_text(content)} "
        polarity = True
        stripped = norm
        for negative, positive in _NEGATION_REPLACEMENTS:
            if negative in stripped:
                stripped = stripped.replace(negative, positive)
                polarity = not polarity
        stripped = normalize_text(stripped)
        return stripped, polarity
