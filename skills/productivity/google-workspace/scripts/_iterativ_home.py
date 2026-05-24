"""Resolve ITERATIV_HOME for standalone skill scripts.

Skill scripts may run outside the Iterativ process (e.g. system Python,
nix env, CI) where ``iterativ_constants`` is not importable.  This module
provides the same ``get_iterativ_home()`` and ``display_iterativ_home()``
contracts as ``iterativ_constants`` without requiring it on ``sys.path``.

When ``iterativ_constants`` IS available it is used directly so that any
future enhancements (profile resolution, Docker detection, etc.) are
picked up automatically.  The fallback path replicates the core logic
from ``iterativ_constants.py`` using only the stdlib.

All scripts under ``google-workspace/scripts/`` should import from here
instead of duplicating the ``ITERATIV_HOME = Path(os.getenv(...))`` pattern.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from iterativ_constants import display_iterativ_home as display_iterativ_home
    from iterativ_constants import get_iterativ_home as get_iterativ_home
except (ModuleNotFoundError, ImportError):

    def get_iterativ_home() -> Path:
        """Return the Iterativ home directory (default: ~/.iterativ).

        Mirrors ``iterativ_constants.get_iterativ_home()``."""
        val = os.environ.get("ITERATIV_HOME", "").strip()
        return Path(val) if val else Path.home() / ".iterativ"

    def display_iterativ_home() -> str:
        """Return a user-friendly ``~/``-shortened display string.

        Mirrors ``iterativ_constants.display_iterativ_home()``."""
        home = get_iterativ_home()
        try:
            return "~/" + str(home.relative_to(Path.home()))
        except ValueError:
            return str(home)
