from __future__ import annotations

import json
from pathlib import Path

from app.main import app


def main() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    output = repo_root / "packages" / "contracts" / "openapi.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"OpenAPI escrito en {output}")


if __name__ == "__main__":
    main()
