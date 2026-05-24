"""Domain module loading for Knowledge II JSON-LD ontologies."""

from knowledge.domain_modules.loader import (
    get_domain_module,
    iter_domain_modules,
    load_domain_module,
)

__all__ = ["get_domain_module", "iter_domain_modules", "load_domain_module"]
