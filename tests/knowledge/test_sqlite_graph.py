import json

from knowledge.domain_modules import get_domain_module
from knowledge.graph.sqlite import SQLiteKnowledgeGraph
from knowledge.schema import NodeType, ValidationStatus
from tools.memory_tool import MemoryStore
from tools.knowledge_tool import knowledge_graph_tool


def test_integrate_claim_records_provenance_and_domain(tmp_path):
    graph = SQLiteKnowledgeGraph(tmp_path / "knowledge.db")
    try:
        result = graph.integrate_claim(
            "Iterativ Agent uses a Knowledge II graph substrate.",
            domain="iterativ.iks",
            source={"label": "proposal", "credibility": 0.9},
            confidence=0.8,
            produced_by="unit-test",
        )

        assert result["success"] is True
        claims = graph.search_claims("Knowledge II graph", domains=["iterativ.iks"])
        assert len(claims) == 1
        assert claims[0].validation_status == ValidationStatus.PASS

        health = graph.graph_health()
        assert health["nodes"][NodeType.CLAIM.value] == 1
        assert health["nodes"][NodeType.DOMAIN.value] == 1
        assert health["nodes"][NodeType.SOURCE.value] == 1
        assert health["nodes"][NodeType.SKILL.value] == 1
        assert health["edges"]["derives_from"] == 1
        assert health["edges"]["domain_of"] == 1
        assert health["edges"]["produced_by"] == 1
    finally:
        graph.close()


def test_soft_validation_warns_on_contradiction(tmp_path):
    graph = SQLiteKnowledgeGraph(tmp_path / "knowledge.db")
    try:
        first = graph.integrate_claim("The feature is enabled.", domain="test")
        second = graph.integrate_claim("The feature is not enabled.", domain="test")

        assert first["success"] is True
        assert second["success"] is True
        assert second["validation"]["validation_status"] == "warn"
        assert second["validation"]["validation_issues"][0]["code"] == "potential_contradiction"
        assert graph.graph_health()["edges"]["contradicts"] == 1
    finally:
        graph.close()


def test_memory_store_dual_writes_to_knowledge_graph(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.memory_tool.get_memory_dir", lambda: tmp_path / "memories")
    graph = SQLiteKnowledgeGraph(tmp_path / "knowledge.db")
    try:
        store = MemoryStore(memory_char_limit=500, user_char_limit=300, knowledge_graph=graph)
        store.load_from_disk()

        result = store.add("memory", "Project convention: prefer scoped Knowledge II changes.")

        assert result["success"] is True
        claims = graph.search_claims("Knowledge II changes", domains=["agent.memory"])
        assert len(claims) == 1
        assert claims[0].metadata["memory_action"] == "add"
    finally:
        graph.close()


def test_knowledge_graph_tool_uses_supplied_graph(tmp_path):
    graph = SQLiteKnowledgeGraph(tmp_path / "knowledge.db")
    try:
        add_result = json.loads(
            knowledge_graph_tool(
                action="add_claim",
                content="Domain modules are JSON-LD files.",
                domain="iterativ.iks",
                graph=graph,
            )
        )
        search_result = json.loads(
            knowledge_graph_tool(
                action="search",
                query="JSON-LD",
                domains=["iterativ.iks"],
                graph=graph,
            )
        )

        assert add_result["success"] is True
        assert search_result["success"] is True
        assert search_result["claims"][0]["content"] == "Domain modules are JSON-LD files."
    finally:
        graph.close()


def test_builtin_domain_module_loader_finds_iks_module():
    module = get_domain_module("iterativ.iks")

    assert module is not None
    assert module["@id"] == "iterativ.iks"
    assert any(c["name"] == "Knowledge Genealogy" for c in module["concepts"])
