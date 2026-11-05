from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from .analyze import AnalysisResult, analyze, format_issues, format_issues_json
from .clarify import (
    collect_questions,
    format_questions_json,
    format_questions_markdown,
    format_questions_text,
)
from .converge import (
    ConvergenceResult,
    converge,
    format_convergence_json,
    format_convergence_markdown,
    format_convergence_text,
)
from .paths import SpecPaths
from .profiles import (
    ProfileError,
    check_profile,
    format_profile_json,
    format_profile_markdown,
    format_profile_text,
    format_profiles,
    load_profile,
    load_profiles,
)

DEFAULT_CONVERGENCE_REPORT = "docs/spec/convergence-report.md"
EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="spec",
        description="Checks de especificación de Growup (clarify, analyze, converge, perfiles).",
    )
    parser.add_argument("--root", type=Path, default=None, help="Raíz del repo")
    subparsers = parser.add_subparsers(dest="command", required=True)

    clarify = subparsers.add_parser("clarify", help="Preguntas abiertas antes de implementar")
    clarify.add_argument("--limit", type=int, default=0, help="Máximo de preguntas (0 = todas)")
    clarify.add_argument("--format", choices=("text", "markdown", "json"), default="text")
    clarify.add_argument("--write", type=Path, default=None, help="Escribe la salida en un archivo")

    analyze_parser = subparsers.add_parser(
        "analyze", help="Consistencia spec <-> diseño <-> tareas"
    )
    analyze_parser.add_argument("--fail-on", choices=("error", "warning", "none"), default="error")
    analyze_parser.add_argument("--format", choices=("text", "json"), default="text")
    analyze_parser.add_argument("--write", type=Path, default=None)

    converge_parser = subparsers.add_parser(
        "converge", help="Verifica que lo implementado cumple la spec"
    )
    converge_parser.add_argument("--fail-on", choices=("error", "warning", "none"), default="error")
    converge_parser.add_argument("--format", choices=("text", "markdown", "json"), default="text")
    converge_parser.add_argument(
        "--write",
        nargs="?",
        const=Path(DEFAULT_CONVERGENCE_REPORT),
        default=None,
        type=Path,
        help=f"Escribe el reporte (por defecto {DEFAULT_CONVERGENCE_REPORT})",
    )

    profiles = subparsers.add_parser("profiles", help="Perfiles regulatorios (SOC 2, PCI)")
    profile_subparsers = profiles.add_subparsers(dest="profiles_command", required=True)
    profile_subparsers.add_parser("list", help="Lista los perfiles instalados")
    check = profile_subparsers.add_parser("check", help="Evalúa un perfil")
    check.add_argument("profile")
    check.add_argument("--format", choices=("text", "markdown", "json"), default="text")
    check.add_argument("--fail-on", choices=("fail", "none"), default="fail")
    check.add_argument("--write", type=Path, default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        paths = SpecPaths.discover(
            args.root,
            require_spec=(
                args.command != "profiles" or args.profiles_command != "list"
            ),
        )
    except FileNotFoundError as error:
        print(f"error: {error}", file=sys.stderr)
        return EXIT_ERROR

    if args.command == "clarify":
        return _run_clarify(args, paths)
    if args.command == "analyze":
        return _run_analyze(args, paths)
    if args.command == "converge":
        return _run_converge(args, paths)
    if args.command == "profiles":
        return _run_profiles(args, paths)
    parser.error(f"comando desconocido: {args.command}")
    return EXIT_ERROR


def _run_clarify(args: argparse.Namespace, paths: SpecPaths) -> int:
    questions = collect_questions(paths, limit=args.limit)
    if args.format == "json":
        output = format_questions_json(questions, paths)
    elif args.format == "markdown":
        output = format_questions_markdown(questions, paths)
    else:
        output = format_questions_text(questions, paths)
    _emit(args.write, output, paths)
    return EXIT_OK


def _run_analyze(args: argparse.Namespace, paths: SpecPaths) -> int:
    result = analyze(paths)
    output = (
        format_issues_json(result, paths) if args.format == "json" else format_issues(result, paths)
    )
    _emit(args.write, output, paths)
    return _analyze_exit_code(result, args.fail_on)


def _analyze_exit_code(result: AnalysisResult, fail_on: str) -> int:
    if fail_on == "none":
        return EXIT_OK
    if fail_on == "warning":
        return EXIT_FINDINGS if result.issues else EXIT_OK
    return EXIT_FINDINGS if result.count("error") else EXIT_OK


def _run_converge(args: argparse.Namespace, paths: SpecPaths) -> int:
    result = converge(paths)
    if args.format == "json":
        output = format_convergence_json(result)
    elif args.format == "markdown":
        output = format_convergence_markdown(result, date.today().isoformat())
    else:
        output = format_convergence_text(result)
    _emit(args.write, output, paths)
    return _converge_exit_code(result, args.fail_on)


def _converge_exit_code(result: ConvergenceResult, fail_on: str) -> int:
    if fail_on == "none":
        return EXIT_OK
    if fail_on == "warning":
        return EXIT_FINDINGS if result.errors or result.warnings else EXIT_OK
    return EXIT_FINDINGS if result.errors else EXIT_OK


def _run_profiles(args: argparse.Namespace, paths: SpecPaths) -> int:
    if args.profiles_command == "list":
        print(format_profiles(load_profiles(paths.profiles_dir)))
        return EXIT_OK
    try:
        profile = load_profile(paths.profiles_dir, args.profile)
    except ProfileError as error:
        print(f"error: {error}", file=sys.stderr)
        return EXIT_ERROR
    report = check_profile(profile, paths)
    if args.format == "json":
        output = format_profile_json(report)
    elif args.format == "markdown":
        output = format_profile_markdown(report)
    else:
        output = format_profile_text(report)
    _emit(args.write, output, paths)
    if args.fail_on == "fail" and report.failed:
        return EXIT_FINDINGS
    return EXIT_OK


def _emit(target: Path | None, output: str, paths: SpecPaths) -> None:
    if target is None:
        print(output)
        return
    destination = target if target.is_absolute() else paths.root / target
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(output.rstrip() + "\n", encoding="utf-8")
    print(f"Escrito en {paths.relative(destination)}")


if __name__ == "__main__":
    raise SystemExit(main())
