#!/usr/bin/env python3
"""
Multi-Model Orchestrator

Intelligent routing system that automatically selects the best model for each task
based on task type, complexity, and model capabilities. Inspired by Perplexity Computer's
multi-model orchestration.

Features:
- Task type classification (research, coding, analysis, creative, etc.)
- Model capability registry with strengths/weaknesses
- Automatic model selection with fallback chains
- Performance tracking and optimization
- Cost-aware routing
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any
from functools import lru_cache

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Classification of task types for model routing."""
    RESEARCH = "research"
    CODING = "coding"
    ANALYSIS = "analysis"
    CREATIVE = "creative"
    REASONING = "reasoning"
    SUMMARIZATION = "summarization"
    MULTIMODAL = "multimodal"
    BROWSER_AUTOMATION = "browser_automation"
    GENERAL = "general"


@dataclass
class ModelCapabilities:
    """Capabilities and metadata for a model."""
    name: str
    provider: str
    strengths: Set[TaskType]
    weaknesses: Set[TaskType]
    context_window: int = 128000
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    supports_vision: bool = False
    supports_tools: bool = True
    supports_reasoning: bool = False
    max_speed_rank: int = 5  # 1 = fastest, 10 = slowest
    quality_rank: int = 5  # 1 = lowest quality, 10 = highest quality
    fallback_models: List[str] = field(default_factory=list)


class ModelRegistry:
    """Registry of available models with their capabilities."""
    
    def __init__(self):
        self._models: Dict[str, ModelCapabilities] = {}
        self._initialize_builtin_models()
    
    def _initialize_builtin_models(self):
        """Initialize built-in model capabilities."""
        
        # Claude models (Anthropic)
        self.register(ModelCapabilities(
            name="claude-sonnet-4-20250514",
            provider="anthropic",
            strengths={
                TaskType.REASONING,
                TaskType.ANALYSIS,
                TaskType.CODING,
                TaskType.RESEARCH,
            },
            weaknesses=set(),
            context_window=200000,
            cost_per_1k_input=3.0,
            cost_per_1k_output=15.0,
            supports_vision=True,
            supports_tools=True,
            supports_reasoning=True,
            max_speed_rank=4,
            quality_rank=9,
            fallback_models=["claude-haiku-4-20250514", "gpt-4o-mini"],
        ))
        
        self.register(ModelCapabilities(
            name="claude-opus-4-20250514",
            provider="anthropic",
            strengths={
                TaskType.REASONING,
                TaskType.ANALYSIS,
                TaskType.RESEARCH,
                TaskType.CREATIVE,
            },
            weaknesses={TaskType.CODING},  # Slower for coding
            context_window=200000,
            cost_per_1k_input=15.0,
            cost_per_1k_output=75.0,
            supports_vision=True,
            supports_tools=True,
            supports_reasoning=True,
            max_speed_rank=7,
            quality_rank=10,
            fallback_models=["claude-sonnet-4-20250514", "claude-haiku-4-20250514"],
        ))
        
        self.register(ModelCapabilities(
            name="claude-haiku-4-20250514",
            provider="anthropic",
            strengths={
                TaskType.SUMMARIZATION,
                TaskType.GENERAL,
                TaskType.ANALYSIS,
            },
            weaknesses={
                TaskType.REASONING,
                TaskType.COMPLEX_CODING,
            },
            context_window=200000,
            cost_per_1k_input=0.25,
            cost_per_1k_output=1.25,
            supports_vision=True,
            supports_tools=True,
            max_speed_rank=2,
            quality_rank=6,
            fallback_models=["gpt-4o-mini"],
        ))
        
        # OpenAI models
        self.register(ModelCapabilities(
            name="gpt-4o",
            provider="openai",
            strengths={
                TaskType.CODING,
                TaskType.MULTIMODAL,
                TaskType.REASONING,
                TaskType.BROWSER_AUTOMATION,
            },
            weaknesses=set(),
            context_window=128000,
            cost_per_1k_input=5.0,
            cost_per_1k_output=15.0,
            supports_vision=True,
            supports_tools=True,
            max_speed_rank=3,
            quality_rank=8,
            fallback_models=["gpt-4o-mini", "claude-haiku-4-20250514"],
        ))
        
        self.register(ModelCapabilities(
            name="gpt-4o-mini",
            provider="openai",
            strengths={
                TaskType.CODING,
                TaskType.GENERAL,
                TaskType.SUMMARIZATION,
            },
            weaknesses={TaskType.REASONING, TaskType.COMPLEX_RESEARCH},
            context_window=128000,
            cost_per_1k_input=0.15,
            cost_per_1k_output=0.6,
            supports_vision=True,
            supports_tools=True,
            max_speed_rank=1,
            quality_rank=5,
            fallback_models=["claude-haiku-4-20250514"],
        ))
        
        self.register(ModelCapabilities(
            name="o1-preview",
            provider="openai",
            strengths={
                TaskType.REASONING,
                TaskType.ANALYSIS,
                TaskType.RESEARCH,
            },
            weaknesses={TaskType.CODING, TaskType.BROWSER_AUTOMATION},
            context_window=128000,
            cost_per_1k_input=15.0,
            cost_per_1k_output=60.0,
            supports_tools=False,
            supports_reasoning=True,
            max_speed_rank=8,
            quality_rank=10,
            fallback_models=["claude-opus-4-20250514", "claude-sonnet-4-20250514"],
        ))
        
        # Google models
        self.register(ModelCapabilities(
            name="gemini-2.5-pro",
            provider="google",
            strengths={
                TaskType.REASONING,
                TaskType.CODING,
                TaskType.MULTIMODAL,
                TaskType.RESEARCH,
            },
            weaknesses=set(),
            context_window=1000000,
            cost_per_1k_input=1.25,
            cost_per_1k_output=5.0,
            supports_vision=True,
            supports_tools=True,
            supports_reasoning=True,
            max_speed_rank=3,
            quality_rank=8,
            fallback_models=["gemini-2.5-flash", "gpt-4o-mini"],
        ))
        
        self.register(ModelCapabilities(
            name="gemini-2.5-flash",
            provider="google",
            strengths={
                TaskType.CODING,
                TaskType.GENERAL,
                TaskType.SUMMARIZATION,
                TaskType.BROWSER_AUTOMATION,
            },
            weaknesses={TaskType.COMPLEX_REASONING},
            context_window=1000000,
            cost_per_1k_input=0.075,
            cost_per_1k_output=0.3,
            supports_vision=True,
            supports_tools=True,
            max_speed_rank=1,
            quality_rank=6,
            fallback_models=["gpt-4o-mini"],
        ))
        
        # Add more models as needed...
    
    def register(self, model: ModelCapabilities):
        """Register a model with its capabilities."""
        self._models[model.name] = model
        logger.debug(f"Registered model: {model.name} ({model.provider})")
    
    def get(self, model_name: str) -> Optional[ModelCapabilities]:
        """Get model capabilities by name."""
        return self._models.get(model_name)
    
    def list_models(self) -> List[str]:
        """List all registered model names."""
        return list(self._models.keys())
    
    def get_models_by_provider(self, provider: str) -> List[ModelCapabilities]:
        """Get all models from a specific provider."""
        return [m for m in self._models.values() if m.provider == provider]
    
    def get_models_by_strength(self, task_type: TaskType) -> List[ModelCapabilities]:
        """Get models ranked by strength for a specific task type."""
        models = [m for m in self._models.values() if task_type in m.strengths]
        # Sort by quality rank (descending) then speed rank (ascending)
        models.sort(key=lambda m: (-m.quality_rank, m.max_speed_rank))
        return models


class TaskClassifier:
    """Classifies tasks into types for model routing."""
    
    # Keywords and patterns for task classification
    RESEARCH_KEYWORDS = {
        'research', 'investigate', 'find', 'search', 'look up', 'discover',
        'explore', 'analyze', 'study', 'examine', 'learn about', 'what is',
        'how does', 'why', 'compare', 'difference', 'history', 'background',
    }
    
    CODING_KEYWORDS = {
        'code', 'program', 'function', 'class', 'debug', 'fix', 'implement',
        'write', 'script', 'algorithm', 'refactor', 'optimize', 'test',
        'api', 'database', 'frontend', 'backend', 'deploy', 'build',
    }
    
    ANALYSIS_KEYWORDS = {
        'analyze', 'evaluate', 'assess', 'review', 'examine', 'break down',
        'explain', 'understand', 'interpret', 'meaning', 'implications',
        'pros and cons', 'advantages', 'disadvantages',
    }
    
    CREATIVE_KEYWORDS = {
        'create', 'generate', 'write', 'story', 'poem', 'design', 'imagine',
        'brainstorm', 'idea', 'creative', 'novel', 'original', 'innovative',
    }
    
    REASONING_KEYWORDS = {
        'reason', 'logic', 'solve', 'problem', 'puzzle', 'deduce', 'infer',
        'conclude', 'therefore', 'because', 'step by step', 'think through',
    }
    
    SUMMARIZATION_KEYWORDS = {
        'summarize', 'summary', 'brief', 'condense', 'shorten', 'overview',
        'key points', 'main idea', 'recap', 'tldr', 'abstract',
    }
    
    BROWSER_KEYWORDS = {
        'browse', 'website', 'webpage', 'click', 'scroll', 'navigate',
        'fill form', 'submit', 'download', 'screenshot', 'web automation',
    }
    
    @classmethod
    def classify(cls, task: str, context: Optional[Dict[str, Any]] = None) -> TaskType:
        """
        Classify a task into its type.
        
        Args:
            task: The task description or user message
            context: Additional context (e.g., available tools, previous turns)
        
        Returns:
            The classified TaskType
        """
        task_lower = task.lower()
        
        # Check for browser automation context
        if context and context.get('has_browser_tools'):
            if any(kw in task_lower for kw in cls.BROWSER_KEYWORDS):
                return TaskType.BROWSER_AUTOMATION
        
        # Check for multimodal content
        if context and context.get('has_images'):
            return TaskType.MULTIMODAL
        
        # Score each task type
        scores = {
            TaskType.RESEARCH: cls._score_keywords(task_lower, cls.RESEARCH_KEYWORDS),
            TaskType.CODING: cls._score_keywords(task_lower, cls.CODING_KEYWORDS),
            TaskType.ANALYSIS: cls._score_keywords(task_lower, cls.ANALYSIS_KEYWORDS),
            TaskType.CREATIVE: cls._score_keywords(task_lower, cls.CREATIVE_KEYWORDS),
            TaskType.REASONING: cls._score_keywords(task_lower, cls.REASONING_KEYWORDS),
            TaskType.SUMMARIZATION: cls._score_keywords(task_lower, cls.SUMMARIZATION_KEYWORDS),
        }
        
        # Find the highest score
        max_score = max(scores.values())
        if max_score == 0:
            return TaskType.GENERAL
        
        # Return the task type with the highest score
        for task_type, score in scores.items():
            if score == max_score:
                return task_type
        
        return TaskType.GENERAL
    
    @classmethod
    def _score_keywords(cls, text: str, keywords: Set[str]) -> int:
        """Score text based on keyword matches."""
        score = 0
        for keyword in keywords:
            if keyword in text:
                score += 1
        return score


class ModelOrchestrator:
    """
    Main orchestrator for multi-model routing.
    
    Automatically selects the best model for each task based on:
    - Task type classification
    - Model capabilities
    - Cost constraints
    - Performance history
    - Fallback chains
    """
    
    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        cost_optimization: bool = True,
        quality_priority: bool = False,
    ):
        self.registry = registry or ModelRegistry()
        self.classifier = TaskClassifier()
        self.cost_optimization = cost_optimization
        self.quality_priority = quality_priority
        
        # Performance tracking
        self._model_performance: Dict[str, Dict[str, Any]] = {}
    
    def select_model(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        available_models: Optional[List[str]] = None,
        excluded_models: Optional[Set[str]] = None,
    ) -> Tuple[str, Optional[ModelCapabilities]]:
        """
        Select the best model for a given task.
        
        Args:
            task: The task description or user message
            context: Additional context (tools, images, etc.)
            available_models: List of available model names (if None, use all)
            excluded_models: Models to exclude from selection
        
        Returns:
            Tuple of (selected_model_name, model_capabilities)
        """
        # Classify the task
        task_type = self.classifier.classify(task, context)
        logger.debug(f"Task classified as: {task_type.value}")
        
        # Get candidate models
        candidates = self._get_candidate_models(
            task_type,
            available_models,
            excluded_models,
        )
        
        if not candidates:
            logger.warning("No candidate models found, falling back to general models")
            candidates = self._get_candidate_models(
                TaskType.GENERAL,
                available_models,
                excluded_models,
            )
        
        if not candidates:
            # Last resort: return any available model
            all_models = available_models or self.registry.list_models()
            if all_models:
                model_name = all_models[0]
                return model_name, self.registry.get(model_name)
            raise ValueError("No models available for selection")
        
        # Rank and select the best model
        selected = self._rank_and_select(candidates, task_type)
        
        logger.info(f"Selected model: {selected.name} for task type: {task_type.value}")
        return selected.name, selected
    
    def _get_candidate_models(
        self,
        task_type: TaskType,
        available_models: Optional[List[str]] = None,
        excluded_models: Optional[Set[str]] = None,
    ) -> List[ModelCapabilities]:
        """Get candidate models for a task type."""
        excluded = excluded_models or set()
        
        # Get models strong in this task type
        candidates = self.registry.get_models_by_strength(task_type)
        
        # Filter by availability and exclusions
        if available_models:
            available_set = set(available_models)
            candidates = [m for m in candidates if m.name in available_set]
        
        candidates = [m for m in candidates if m.name not in excluded]
        
        # If no models strong in this task, include general models
        if not candidates:
            candidates = [m for m in self.registry.get_models_by_strength(TaskType.GENERAL)]
            if available_models:
                available_set = set(available_models)
                candidates = [m for m in candidates if m.name in available_set]
            candidates = [m for m in candidates if m.name not in excluded]
        
        return candidates
    
    def _rank_and_select(
        self,
        candidates: List[ModelCapabilities],
        task_type: TaskType,
    ) -> ModelCapabilities:
        """
        Rank candidates and select the best one.
        
        Ranking considers:
        - Quality rank (higher is better)
        - Speed rank (lower is better)
        - Cost (lower is better if cost optimization is enabled)
        - Historical performance
        """
        def score_model(model: ModelCapabilities) -> float:
            score = 0.0
            
            # Quality score (0-10, weighted heavily if quality priority)
            quality_weight = 2.0 if self.quality_priority else 1.0
            score += model.quality_rank * quality_weight
            
            # Speed score (inverted, 1-10, weighted moderately)
            speed_score = 11 - model.max_speed_rank
            score += speed_score * 0.5
            
            # Cost score (lower cost is better)
            if self.cost_optimization:
                # Normalize cost (assuming max $15/1k input)
                cost_score = 10 - (model.cost_per_1k_input / 15.0) * 10
                score += cost_score * 0.3
            
            # Performance history bonus
            perf = self._model_performance.get(model.name, {})
            success_rate = perf.get('success_rate', 0.9)
            score += success_rate * 2.0
            
            return score
        
        # Score all candidates
        scored = [(model, score_model(model)) for model in candidates]
        
        # Sort by score (descending)
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Return the highest-scoring model
        return scored[0][0]
    
    def get_fallback_chain(
        self,
        model_name: str,
        excluded_models: Optional[Set[str]] = None,
    ) -> List[str]:
        """
        Get the fallback chain for a model.
        
        Args:
            model_name: The primary model
            excluded_models: Models to exclude from fallback
        
        Returns:
            List of model names in fallback order
        """
        model = self.registry.get(model_name)
        if not model:
            return []
        
        excluded = excluded_models or set()
        fallback_chain = []
        
        for fallback_name in model.fallback_models:
            if fallback_name not in excluded and fallback_name != model_name:
                fallback_chain.append(fallback_name)
        
        # If no fallbacks configured, try models by provider
        if not fallback_chain:
            same_provider = self.registry.get_models_by_provider(model.provider)
            for m in same_provider:
                if m.name != model_name and m.name not in excluded:
                    fallback_chain.append(m.name)
        
        return fallback_chain
    
    def record_performance(
        self,
        model_name: str,
        success: bool,
        latency_ms: Optional[int] = None,
        error: Optional[str] = None,
    ):
        """Record model performance for optimization."""
        if model_name not in self._model_performance:
            self._model_performance[model_name] = {
                'total_calls': 0,
                'successes': 0,
                'failures': 0,
                'success_rate': 0.0,
                'avg_latency_ms': 0.0,
                'errors': {},
            }
        
        perf = self._model_performance[model_name]
        perf['total_calls'] += 1
        
        if success:
            perf['successes'] += 1
        else:
            perf['failures'] += 1
            if error:
                perf['errors'][error] = perf['errors'].get(error, 0) + 1
        
        perf['success_rate'] = perf['successes'] / perf['total_calls']
        
        if latency_ms is not None:
            current_avg = perf['avg_latency_ms']
            total = perf['total_calls']
            perf['avg_latency_ms'] = (current_avg * (total - 1) + latency_ms) / total
        
        logger.debug(f"Recorded performance for {model_name}: {perf}")


# Global singleton instance
_default_orchestrator: Optional[ModelOrchestrator] = None


def get_orchestrator() -> ModelOrchestrator:
    """Get the default model orchestrator instance."""
    global _default_orchestrator
    if _default_orchestrator is None:
        _default_orchestrator = ModelOrchestrator()
    return _default_orchestrator


def select_model_for_task(
    task: str,
    context: Optional[Dict[str, Any]] = None,
    available_models: Optional[List[str]] = None,
    excluded_models: Optional[Set[str]] = None,
) -> str:
    """
    Convenience function to select a model for a task.
    
    Args:
        task: The task description or user message
        context: Additional context
        available_models: List of available model names
        excluded_models: Models to exclude
    
    Returns:
        Selected model name
    """
    orchestrator = get_orchestrator()
    model_name, _ = orchestrator.select_model(task, context, available_models, excluded_models)
    return model_name
