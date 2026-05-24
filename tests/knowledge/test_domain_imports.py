import json

from knowledge.domain_modules import get_domain_module
from knowledge.graph.sqlite import SQLiteKnowledgeGraph
from tools.knowledge_tool import knowledge_graph_tool


def test_import_domain_module_creates_concepts_and_edges(tmp_path):
    graph = SQLiteKnowledgeGraph(tmp_path / "knowledge.db")
    try:
        module = get_domain_module("iterativ.iks")
        result = graph.import_domain_module(module)

        assert result["success"] is True
        assert result["module_id"] == "iterativ.iks"
        assert result["concepts_imported"] >= 3
        assert result["relationships_imported"] >= 2

        health = graph.graph_health()
        assert health["nodes"]["Domain"] == 1
        assert health["nodes"]["Concept"] >= 3
        assert health["edges"]["domain_of"] >= 3
    finally:
        graph.close()


def test_knowledge_tool_import_domain_module_action(tmp_path):
    graph = SQLiteKnowledgeGraph(tmp_path / "knowledge.db")
    try:
        result = json.loads(
            knowledge_graph_tool(
                action="import_domain_module",
                module="iterativ.iks",
                graph=graph,
            )
        )

        assert result["success"] is True
        assert result["module_id"] == "iterativ.iks"
    finally:
        graph.close()
