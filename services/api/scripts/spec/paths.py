from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SPEC_DIR = Path(".kiro") / "specs" / "storefront-platform-v2"


def find_repo_root(start: Path | None = None) -> Path:
    """Sube desde *start* hasta encontrar la raíz del monorepo."""
    current = (start or Path(__file__)).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        is_monorepo = (candidate / "services" / "api").is_dir() and (
            candidate / "docs" / "adr"
        ).is_dir()
        if is_monorepo:
            return candidate
    raise FileNotFoundError(f"No se encontró la raíz del repo desde {current}")


@dataclass(frozen=True, slots=True)
class SpecPaths:
    """Rutas de los artefactos que consumen los comandos de spec."""

    root: Path
    requirements: Path
    design: Path
    tasks: Path
    decisions: tuple[Path, ...]
    steering: tuple[Path, ...]
    adr_dir: Path
    traceability: Path
    profiles_dir: Path

    @classmethod
    def discover(
        cls, root: Path | None = None, *, require_spec: bool = True
    ) -> SpecPaths:
        base = find_repo_root(root)
        spec = base / SPEC_DIR
        if require_spec:
            required = (
                spec / "requirements.md",
                spec / "design.md",
                spec / "tasks.md",
            )
            missing = [path for path in required if not path.is_file()]
            if missing:
                paths = ", ".join(path.relative_to(base).as_posix() for path in missing)
                raise FileNotFoundError(
                    f"Faltan archivos de especificación: {paths}. "
                    "No se puede ejecutar el análisis hasta restaurar la spec."
                )
        docs = base / "docs"
        return cls(
            root=base,
            requirements=spec / "requirements.md",
            design=spec / "design.md",
            tasks=spec / "tasks.md",
            decisions=tuple(sorted(docs.glob("decisiones-pendientes*.md"))),
            steering=tuple(sorted((base / ".kiro" / "steering").glob("*.md"))),
            adr_dir=docs / "adr",
            traceability=docs / "spec" / "traceability.json",
            profiles_dir=docs / "regulatory" / "profiles",
        )

    def relative(self, path: Path) -> str:
        """Devuelve *path* relativo a la raíz, con separadores POSIX."""
        try:
            return path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return path.as_posix()
