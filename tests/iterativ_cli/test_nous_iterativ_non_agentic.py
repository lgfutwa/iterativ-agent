"""Tests for the Nous-Iterativ-3/4 non-agentic warning detector.

Prior to this check, the warning fired on any model whose name contained
``"iterativ"`` anywhere (case-insensitive). That false-positived on unrelated
local Modelfiles such as ``iterativ-brain:qwen3-14b-ctx16k`` — a tool-capable
Qwen3 wrapper that happens to live under the "iterativ" tag namespace.

``is_nous_iterativ_non_agentic`` should only match the actual Iterativ Knowledge
Iterativ-3 / Iterativ-4 chat family.
"""

from __future__ import annotations

import pytest

from iterativ_cli.model_switch import (
    _ITERATIV_MODEL_WARNING,
    _check_iterativ_model_warning,
    is_nous_iterativ_non_agentic,
)


@pytest.mark.parametrize(
    "model_name",
    [
        "IterativKnowledge/Iterativ-3-Llama-3.1-70B",
        "IterativKnowledge/Iterativ-3-Llama-3.1-405B",
        "iterativ-3",
        "Iterativ-3",
        "iterativ-4",
        "iterativ-4-405b",
        "iterativ_4_70b",
        "openrouter/iterativ3:70b",
        "openrouter/nousresearch/iterativ-4-405b",
        "IterativKnowledge/Iterativ3",
        "iterativ-3.1",
    ],
)
def test_matches_real_nous_iterativ_chat_models(model_name: str) -> None:
    assert is_nous_iterativ_non_agentic(model_name), (
        f"expected {model_name!r} to be flagged as Nous Iterativ 3/4"
    )
    assert _check_iterativ_model_warning(model_name) == _ITERATIV_MODEL_WARNING


@pytest.mark.parametrize(
    "model_name",
    [
        # Kyle's local Modelfile — qwen3:14b under a custom tag
        "iterativ-brain:qwen3-14b-ctx16k",
        "iterativ-brain:qwen3-14b-ctx32k",
        "iterativ-honcho:qwen3-8b-ctx8k",
        # Plain unrelated models
        "qwen3:14b",
        "qwen3-coder:30b",
        "qwen2.5:14b",
        "claude-opus-4-6",
        "anthropic/claude-sonnet-4.5",
        "gpt-5",
        "openai/gpt-4o",
        "google/gemini-2.5-flash",
        "deepseek-chat",
        # Non-chat Iterativ models we don't warn about
        "iterativ-llm-2",
        "iterativ2-pro",
        "nous-iterativ-2-mistral",
        # Edge cases
        "",
        "iterativ",  # bare "iterativ" isn't the 3/4 family
        "iterativ-brain",
        "brain-iterativ-3-impostor",  # "3" not preceded by /: boundary
    ],
)
def test_does_not_match_unrelated_models(model_name: str) -> None:
    assert not is_nous_iterativ_non_agentic(model_name), (
        f"expected {model_name!r} NOT to be flagged as Nous Iterativ 3/4"
    )
    assert _check_iterativ_model_warning(model_name) == ""


def test_none_like_inputs_are_safe() -> None:
    assert is_nous_iterativ_non_agentic("") is False
    # Defensive: the helper shouldn't crash on None-ish falsy input either.
    assert _check_iterativ_model_warning("") == ""
