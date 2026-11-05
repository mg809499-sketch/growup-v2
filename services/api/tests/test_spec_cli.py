from __future__ import annotations

from pathlib import Path

from scripts.spec.cli import main


def test_profiles_list_does_not_require_spec_files(tmp_path: Path, capsys) -> None:
    (tmp_path / "services" / "api").mkdir(parents=True)
    (tmp_path / "docs" / "adr").mkdir(parents=True)
    (tmp_path / "docs" / "regulatory" / "profiles").mkdir(parents=True)

    exit_code = main(["--root", str(tmp_path), "profiles", "list"])

    assert exit_code == 0
    assert capsys.readouterr().err == ""
