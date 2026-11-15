from __future__ import annotations

import ast
from pathlib import Path

# Regla de fronteras modulares (WP-13):
# Ningún dominio en `app/domains/<domain>` puede importar directamente el
# módulo privado `.repository` de otro dominio hermano (excepto a través de
# inyección de dependencias en `app/api/deps.py` o `app/main.py`).
# Solo `identity` (`models`, `permissions`) y `tenants` (`models`, `zones`) son
# contratos transversales compartidos entre dominios.


def find_forbidden_cross_domain_repository_imports(domains_root: Path) -> list[str]:
    violations: list[str] = []
    for py_file in sorted(domains_root.rglob("*.py")):
        rel = py_file.relative_to(domains_root)
        if len(rel.parts) < 2:
            continue
        current_domain = rel.parts[0]
        source = py_file.read_text(encoding="utf-8")
        violations.extend(
            check_source_for_cross_domain_repository_imports(
                source,
                current_domain=current_domain,
                file_label=str(rel),
            )
        )
    return violations


def check_source_for_cross_domain_repository_imports(
    source: str,
    *,
    current_domain: str,
    file_label: str = "<memory>",
) -> list[str]:
    tree = ast.parse(source, filename=file_label)
    violations: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            parts = node.module.split(".")
            if (
                len(parts) >= 4
                and parts[0] == "app"
                and parts[1] == "domains"
                and parts[2] != current_domain
                and parts[3] == "repository"
            ):
                violations.append(
                    f"{file_label}:{node.lineno}: dominio '{current_domain}' importa "
                    f"repositorio privado '{node.module}'"
                )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                if (
                    len(parts) >= 4
                    and parts[0] == "app"
                    and parts[1] == "domains"
                    and parts[2] != current_domain
                    and parts[3] == "repository"
                ):
                    violations.append(
                        f"{file_label}:{node.lineno}: dominio '{current_domain}' importa "
                        f"repositorio privado '{alias.name}'"
                    )
    return violations


def test_no_domain_imports_sibling_private_repository() -> None:
    domains_root = Path(__file__).resolve().parents[1] / "app" / "domains"
    violations = find_forbidden_cross_domain_repository_imports(domains_root)
    assert violations == []


def test_boundary_checker_catches_forbidden_repository_import() -> None:
    bad_code = (
        "from app.domains.commerce.repository import CommerceRepository\n"
        "import app.domains.inventory.repository as inv_repo\n"
    )
    violations = check_source_for_cross_domain_repository_imports(
        bad_code,
        current_domain="catalog",
        file_label="catalog/service.py",
    )
    assert len(violations) == 2
    assert "app.domains.commerce.repository" in violations[0]
    assert "app.domains.inventory.repository" in violations[1]
