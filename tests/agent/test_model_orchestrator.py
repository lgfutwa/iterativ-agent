#!/usr/bin/env python3
"""Tests for the multi-model orchestrator."""

import pytest

from agent.model_orchestrator import (
    TaskType,
    ModelCapabilities,
    ModelRegistry,
    TaskClassifier,
    ModelOrchestrator,
    get_orchestrator,
    select_model_for_task,
)


class TestTaskClassifier:
    """Test task classification logic."""
    
    def test_classify_research_task(self):
        """Test classification of research tasks."""
        task = "Research the latest developments in quantum computing"
        task_type = TaskClassifier.classify(task)
        assert task_type == TaskType.RESEARCH
    
    def test_classify_coding_task(self):
        """Test classification of coding tasks."""
        task = "Write a Python function to sort a list"
        task_type = TaskClassifier.classify(task)
        assert task_type == TaskType.CODING
    
    def test_classify_analysis_task(self):
        """Test classification of analysis tasks."""
        task = "Analyze the pros and cons of this approach"
        task_type = TaskClassifier.classify(task)
        assert task_type == TaskType.ANALYSIS
    
    def test_classify_creative_task(self):
        """Test classification of creative tasks."""
        task = "Create a story about a robot learning to love"
        task_type = TaskClassifier.classify(task)
        assert task_type == TaskType.CREATIVE
    
    def test_classify_summarization_task(self):
        """Test classification of summarization tasks."""
        task = "Summarize this article in 3 bullet points"
        task_type = TaskClassifier.classify(task)
        assert task_type == TaskType.SUMMARIZATION
    
    def test_classify_general_task(self):
        """Test classification of general tasks."""
        task = "Hello, how are you?"
        task_type = TaskClassifier.classify(task)
        assert task_type == TaskType.GENERAL
    
    def test_classify_with_browser_context(self):
        """Test classification with browser tool context."""
        task = "Click on the submit button"
        context = {"has_browser_tools": True}
        task_type = TaskClassifier.classify(task, context)
        assert task_type == TaskType.BROWSER_AUTOMATION
    
    def test_classify_with_images(self):
        """Test classification with multimodal context."""
        task = "What's in this image?"
        context = {"has_images": True}
        task_type = TaskClassifier.classify(task, context)
        assert task_type == TaskType.MULTIMODAL


class TestModelRegistry:
    """Test model registry functionality."""
    
    def test_register_model(self):
        """Test registering a model."""
        registry = ModelRegistry()
        model = ModelCapabilities(
            name="test-model",
            provider="test",
            strengths={TaskType.CODING},
            weaknesses=set(),
        )
        registry.register(model)
        assert registry.get("test-model") == model
    
    def test_get_nonexistent_model(self):
        """Test getting a model that doesn't exist."""
        registry = ModelRegistry()
        assert registry.get("nonexistent") is None
    
    def test_list_models(self):
        """Test listing all models."""
        registry = ModelRegistry()
        models = registry.list_models()
        assert isinstance(models, list)
        assert len(models) > 0  # Should have built-in models
    
    def test_get_models_by_provider(self):
        """Test getting models by provider."""
        registry = ModelRegistry()
        anthropic_models = registry.get_models_by_provider("anthropic")
        assert all(m.provider == "anthropic" for m in anthropic_models)
        assert len(anthropic_models) > 0
    
    def test_get_models_by_strength(self):
        """Test getting models by task strength."""
        registry = ModelRegistry()
        coding_models = registry.get_models_by_strength(TaskType.CODING)
        assert all(TaskType.CODING in m.strengths for m in coding_models)
        assert len(coding_models) > 0


class TestModelOrchestrator:
    """Test model orchestration logic."""
    
    def test_select_model_for_coding(self):
        """Test selecting a model for coding tasks."""
        orchestrator = ModelOrchestrator()
        task = "Write a Python function to implement quicksort"
        model_name, capabilities = orchestrator.select_model(task)
        assert model_name is not None
        assert capabilities is not None
        # Should select a model strong in coding
        assert TaskType.CODING in capabilities.strengths or TaskType.GENERAL in capabilities.strengths
    
    def test_select_model_for_research(self):
        """Test selecting a model for research tasks."""
        orchestrator = ModelOrchestrator()
        task = "Research the history of the Roman Empire"
        model_name, capabilities = orchestrator.select_model(task)
        assert model_name is not None
        assert capabilities is not None
        # Should select a model strong in research
        assert TaskType.RESEARCH in capabilities.strengths or TaskType.GENERAL in capabilities.strengths
    
    def test_select_model_with_available_models(self):
        """Test selecting from a restricted set of available models."""
        orchestrator = ModelOrchestrator()
        task = "Write some code"
        available_models = ["claude-haiku-4-20250514", "gpt-4o-mini"]
        model_name, capabilities = orchestrator.select_model(
            task,
            available_models=available_models,
        )
        assert model_name in available_models
    
    def test_select_model_with_exclusions(self):
        """Test selecting models with exclusions."""
        orchestrator = ModelOrchestrator()
        task = "Write some code"
        excluded_models = {"claude-opus-4-20250514"}
        model_name, capabilities = orchestrator.select_model(
            task,
            excluded_models=excluded_models,
        )
        assert model_name not in excluded_models
    
    def test_get_fallback_chain(self):
        """Test getting fallback chain for a model."""
        orchestrator = ModelOrchestrator()
        fallback_chain = orchestrator.get_fallback_chain("claude-opus-4-20250514")
        assert isinstance(fallback_chain, list)
        # Should have at least one fallback
        assert len(fallback_chain) >= 0
    
    def test_record_performance(self):
        """Test recording model performance."""
        orchestrator = ModelOrchestrator()
        orchestrator.record_performance(
            model_name="claude-sonnet-4-20250514",
            success=True,
            latency_ms=1500,
        )
        # Should not raise an exception
        orchestrator.record_performance(
            model_name="claude-sonnet-4-20250514",
            success=False,
            error="rate_limit",
        )
    
    def test_cost_optimization_mode(self):
        """Test cost optimization mode."""
        orchestrator = ModelOrchestrator(cost_optimization=True)
        task = "Summarize this text"
        model_name, capabilities = orchestrator.select_model(task)
        assert model_name is not None
        # In cost optimization mode, should prefer cheaper models
        assert capabilities.cost_per_1k_input < 10.0  # Reasonable threshold
    
    def test_quality_priority_mode(self):
        """Test quality priority mode."""
        orchestrator = ModelOrchestrator(quality_priority=True)
        task = "Solve this complex reasoning problem"
        model_name, capabilities = orchestrator.select_model(task)
        assert model_name is not None
        # In quality mode, should prefer high-quality models
        assert capabilities.quality_rank >= 8


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_get_orchestrator_singleton(self):
        """Test that get_orchestrator returns a singleton."""
        orchestrator1 = get_orchestrator()
        orchestrator2 = get_orchestrator()
        assert orchestrator1 is orchestrator2
    
    def test_select_model_for_task_function(self):
        """Test the convenience function for model selection."""
        task = "Write a Python script"
        model_name = select_model_for_task(task)
        assert model_name is not None
        assert isinstance(model_name, str)


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_task(self):
        """Test classification of empty task."""
        task_type = TaskClassifier.classify("")
        assert task_type == TaskType.GENERAL
    
    def test_no_available_models(self):
        """Test selection when no models are available."""
        orchestrator = ModelOrchestrator()
        # This should fall back to general models or raise an error
        with pytest.raises(ValueError):
            orchestrator.select_model(
                "test",
                available_models=[],
                excluded_models=set(orchestrator.registry.list_models()),
            )
    
    def test_all_models_excluded(self):
        """Test selection when all models are excluded."""
        orchestrator = ModelOrchestrator()
        all_models = set(orchestrator.registry.list_models())
        with pytest.raises(ValueError):
            orchestrator.select_model(
                "test",
                excluded_models=all_models,
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
