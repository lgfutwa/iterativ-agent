import json

from knowledge.graph.sqlite import SQLiteKnowledgeGraph


def test_skill_view_surfaces_knowledge_signature_and_context(tmp_path, monkeypatch):
    skills_dir = tmp_path / "skills"
    skill_dir = skills_dir / "software" / "architecture-review"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        """---
name: architecture-review
description: Review architecture.
knowledge_signature:
  requires_domains: [iterativ.iks]
  requires_claims:
    - Knowledge II uses provenance tracking
  produces_claims:
    - Architecture health assessment
---
# Architecture Review
Use the graph.
""",
        encoding="utf-8",
    )

    graph = SQLiteKnowledgeGraph(tmp_path / "knowledge.db")
    try:
        graph.integrate_claim(
            "Knowledge II uses provenance tracking",
            domain="iterativ.iks",
            source={"label": "test", "credibility": 1.0},
            confidence=0.9,
        )

        monkeypatch.setattr("tools.skills_tool.SKILLS_DIR", skills_dir)
        monkeypatch.setattr("knowledge.hooks.get_knowledge_graph_from_config", lambda config=None: graph)

        from tools.skills_tool import skill_view

        result = json.loads(skill_view("architecture-review", preprocess=False))

        assert result["success"] is True
        assert result["knowledge_signature"]["requires_domains"] == ["iterativ.iks"]
        assert result["knowledge_signature"]["produces_claims"] == ["Architecture health assessment"]
        assert result["knowledge_context"]["sufficient"] is True
        assert result["knowledge_context"]["missing_claims"] == []
        assert result["knowledge_context"]["claims"][0]["content"] == "Knowledge II uses provenance tracking"
    finally:
        graph.close()


def test_cron_skill_prompt_includes_knowledge_context(tmp_path, monkeypatch):
    skills_dir = tmp_path / "skills"
    skill_dir = skills_dir / "review"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        """---
name: review
description: Review with knowledge.
knowledge_signature:
  requires_domains: [iterativ.iks]
  requires_claims: [IKS tracks knowledge genealogy]
---
# Review
Follow the signature.
""",
        encoding="utf-8",
    )

    graph = SQLiteKnowledgeGraph(tmp_path / "knowledge.db")
    try:
        graph.integrate_claim(
            "IKS tracks knowledge genealogy",
            domain="iterativ.iks",
            source={"label": "test", "credibility": 1.0},
            confidence=0.95,
        )

        monkeypatch.setattr("tools.skills_tool.SKILLS_DIR", skills_dir)
        monkeypatch.setattr("knowledge.hooks.get_knowledge_graph_from_config", lambda config=None: graph)

        from cron.scheduler import _build_job_prompt

        prompt = _build_job_prompt(
            {
                "id": "job1",
                "name": "Knowledge Review",
                "prompt": "Run the review.",
                "skills": ["review"],
            }
        )

        assert "[Knowledge II signature for this skill]" in prompt
        assert "Requires domains: iterativ.iks" in prompt
        assert "IKS tracks knowledge genealogy" in prompt
    finally:
        graph.close()
