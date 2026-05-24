"""Load Knowledge II domain module JSON-LD files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


def domain_modules_root() -> Path:
    return Path(__file__).resolve().parent


def load_domain_module(path: Path | str) -> Dict[str, Any]:
    module_path = Path(path)
    return json.loads(module_path.read_text(encoding="utf-8"))


def iter_domain_modules(root: Path | str | None = None) -> Iterable[Dict[str, Any]]:
    base = Path(root) if root else domain_modules_root()
    for path in sorted(base.rglob("*.jsonld")):
        yield load_domain_module(path)


def get_domain_module(name: str, root: Path | str | None = None) -> Optional[Dict[str, Any]]:
    wanted = name.strip().lower()
    for module in iter_domain_modules(root):
        module_id = str(module.get("@id") or module.get("name") or "").lower()
        module_name = str(module.get("name") or "").lower()
        if wanted in {module_id, module_name}:
            return module
    return None
