"""DDD boundary enforcement tests.

Verifies that domain layer files do not import across bounded context boundaries.
Uses AST parsing to statically check imports without executing any code.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# All bounded contexts (domain directories)
BOUNDED_CONTEXTS = [
    "backtest",
    "data_ingest",
    "execution",
    "portfolio",
    "regime",
    "scoring",
    "signals",
    "valuation",
]


def _get_import_modules(filepath: Path) -> list[str]:
    """Parse a Python file and return all imported module strings."""
    source = filepath.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(filepath))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


class TestExecutionDomainBoundary:
    """execution/domain/ must not import from portfolio/domain/ directly."""

    def test_no_portfolio_import_in_execution_domain_services(self) -> None:
        filepath = PROJECT_ROOT / "src" / "execution" / "domain" / "services.py"
        assert filepath.exists(), f"File not found: {filepath}"
        modules = _get_import_modules(filepath)
        portfolio_imports = [m for m in modules if "src.portfolio" in m]
        assert portfolio_imports == [], (
            f"execution/domain/services.py must not import from portfolio: {portfolio_imports}"
        )


class TestCrossContextDomainImports:
    """No domain/ file should import from another context's domain/ directly.

    Allowed: imports from src.shared.domain (shared kernel)
    Allowed: imports within same context (e.g., scoring.domain.services -> scoring.domain.value_objects)
    Forbidden: imports across contexts (e.g., execution.domain -> portfolio.domain)
    """

    @pytest.mark.parametrize("context", BOUNDED_CONTEXTS)
    def test_no_cross_context_domain_imports(self, context: str) -> None:
        domain_dir = PROJECT_ROOT / "src" / context / "domain"
        if not domain_dir.exists():
            pytest.skip(f"No domain dir for {context}")

        violations: list[str] = []
        for py_file in domain_dir.glob("*.py"):
            if py_file.name == "__pycache__":
                continue
            modules = _get_import_modules(py_file)
            for mod in modules:
                # Check if this imports from another bounded context's domain
                for other_ctx in BOUNDED_CONTEXTS:
                    if other_ctx == context:
                        continue
                    if f"src.{other_ctx}" in mod:
                        violations.append(
                            f"{py_file.name}: imports '{mod}' (cross-context)"
                        )
        assert violations == [], (
            f"Cross-context domain imports in {context}/domain/:\n"
            + "\n".join(f"  - {v}" for v in violations)
        )
