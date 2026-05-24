"""Regression tests for _apply_profile_override ITERATIV_HOME guard (issue #22502).

When ITERATIV_HOME is set to the iterativ root (e.g. systemd hardcodes
ITERATIV_HOME=/root/.iterativ), _apply_profile_override must still read
active_profile and update ITERATIV_HOME to the profile directory.

When ITERATIV_HOME is already a profile directory (.../profiles/<name>),
_apply_profile_override must trust it and return without re-reading
active_profile (child-process inheritance contract).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


def _run_apply_profile_override(
    tmp_path, monkeypatch, *, iterativ_home: str | None, active_profile: str | None,
    argv: list[str] | None = None,
):
    """Run _apply_profile_override in isolation.

    Returns the value of os.environ["ITERATIV_HOME"] after the call,
    or None if unset.
    """
    iterativ_root = tmp_path / ".iterativ"
    iterativ_root.mkdir(parents=True, exist_ok=True)

    if active_profile is not None:
        (iterativ_root / "active_profile").write_text(active_profile)

    if active_profile and active_profile != "default":
        (iterativ_root / "profiles" / active_profile).mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    if iterativ_home is not None:
        monkeypatch.setenv("ITERATIV_HOME", iterativ_home)
    else:
        monkeypatch.delenv("ITERATIV_HOME", raising=False)

    monkeypatch.setattr(sys, "argv", argv or ["iterativ", "gateway", "start"])

    from iterativ_cli.main import _apply_profile_override
    _apply_profile_override()

    return os.environ.get("ITERATIV_HOME")


class TestApplyProfileOverrideIterativHomeGuard:
    """Regression guard for issue #22502.

    Verifies that ITERATIV_HOME pointing to the iterativ root does NOT suppress
    the active_profile check, while ITERATIV_HOME already pointing to a
    profile directory IS trusted as-is.
    """

    def test_iterativ_home_at_root_with_active_profile_is_redirected(
        self, tmp_path, monkeypatch
    ):
        """ITERATIV_HOME=/root/.iterativ + active_profile=coder must redirect
        ITERATIV_HOME to .../profiles/coder.

        Bug scenario from #22502: systemd sets ITERATIV_HOME to the iterativ root
        and the user switches to a profile via `iterativ profile use`.
        Before the fix, the guard returned early and active_profile was ignored.
        """
        iterativ_root = tmp_path / ".iterativ"
        iterativ_root.mkdir(parents=True, exist_ok=True)

        result = _run_apply_profile_override(
            tmp_path,
            monkeypatch,
            iterativ_home=str(iterativ_root),
            active_profile="coder",
        )

        assert result is not None, "ITERATIV_HOME must be set after profile redirect"
        assert "profiles" in result, (
            f"Expected ITERATIV_HOME to point into profiles/ dir, got: {result!r}"
        )
        assert result.endswith("coder"), (
            f"Expected ITERATIV_HOME to end with 'coder', got: {result!r}"
        )

    def test_iterativ_home_already_profile_dir_is_trusted(self, tmp_path, monkeypatch):
        """ITERATIV_HOME=.../profiles/coder must not be overridden even when
        active_profile says something different.

        Preserves the child-process inheritance contract: a subprocess spawned
        with ITERATIV_HOME already set to a specific profile must stay in that
        profile.
        """
        iterativ_root = tmp_path / ".iterativ"
        profile_dir = iterativ_root / "profiles" / "coder"
        profile_dir.mkdir(parents=True, exist_ok=True)

        (iterativ_root / "active_profile").write_text("other")

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setenv("ITERATIV_HOME", str(profile_dir))
        monkeypatch.setattr(sys, "argv", ["iterativ", "gateway", "start"])

        from iterativ_cli.main import _apply_profile_override
        _apply_profile_override()

        assert os.environ.get("ITERATIV_HOME") == str(profile_dir), (
            "ITERATIV_HOME must remain unchanged when already pointing to a profile dir"
        )

    def test_iterativ_home_unset_reads_active_profile(self, tmp_path, monkeypatch):
        """Classic case: ITERATIV_HOME unset + active_profile=coder must set
        ITERATIV_HOME to the profile directory (existing behaviour must not regress).
        """
        result = _run_apply_profile_override(
            tmp_path,
            monkeypatch,
            iterativ_home=None,
            active_profile="coder",
        )

        assert result is not None
        assert "coder" in result

    def test_iterativ_home_unset_default_profile_no_redirect(self, tmp_path, monkeypatch):
        """active_profile=default must not redirect ITERATIV_HOME."""
        iterativ_root = tmp_path / ".iterativ"
        iterativ_root.mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.delenv("ITERATIV_HOME", raising=False)
        monkeypatch.setattr(sys, "argv", ["iterativ", "gateway", "start"])
        (iterativ_root / "active_profile").write_text("default")

        from iterativ_cli.main import _apply_profile_override
        _apply_profile_override()

        assert os.environ.get("ITERATIV_HOME") is None
