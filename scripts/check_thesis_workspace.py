#!/usr/bin/env python3
"""Validate a thesis-ai-standard workspace.

The check is intentionally lightweight: it verifies required files, parses
machine-readable templates when dependencies are available, and reports missing
core evidence paths without pretending to validate thesis quality.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path


REQUIRED_FILES = [
    "README.md",
    "templates/standard-profile.yaml",
    "templates/thesis-ai-spec.yaml",
    "templates/figure-registry.yaml",
    "templates/chapter-section-template.md",
    "templates/ai-review-rubric.json",
]

@dataclass
class CheckResult:
    status: str
    path: str
    message: str


def load_yaml(path: Path) -> object:
    try:
        import yaml  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(f"PyYAML not installed; skipped YAML parse: {exc}") from exc
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def check_required(base: Path, rel_path: str) -> CheckResult:
    path = base / rel_path
    if not path.exists():
        return CheckResult("error", rel_path, "missing required file")
    if path.is_file() and path.stat().st_size == 0:
        return CheckResult("error", rel_path, "file is empty")
    return CheckResult("ok", rel_path, "present")


def check_parse(base: Path, rel_path: str) -> CheckResult:
    path = base / rel_path
    try:
        if rel_path.endswith(".json"):
            json.loads(path.read_text(encoding="utf-8"))
        elif rel_path.endswith((".yaml", ".yml")):
            load_yaml(path)
        else:
            return CheckResult("ok", rel_path, "no parser required")
    except RuntimeError as exc:
        return CheckResult("warn", rel_path, str(exc))
    except Exception as exc:
        return CheckResult("error", rel_path, f"parse failed: {exc}")
    return CheckResult("ok", rel_path, "parsed")


def inspect_core_fields(base: Path) -> list[CheckResult]:
    checks: list[CheckResult] = []
    spec_path = base / "templates" / "thesis-ai-spec.yaml"
    profile_path = base / "templates" / "standard-profile.yaml"

    try:
        spec = load_yaml(spec_path)
        if isinstance(spec, dict):
            paper = spec.get("paper") or {}
            if isinstance(paper, dict):
                title = str(paper.get("title", "")).strip()
                type_profile = str(paper.get("type_profile", "")).strip()
                if not title or title == "填写论文题目":
                    checks.append(CheckResult("warn", spec_path.name, "paper.title still looks unfilled"))
                if "|" in type_profile or type_profile in {"", "other"}:
                    checks.append(CheckResult("warn", spec_path.name, "paper.type_profile needs a concrete value"))
    except Exception as exc:
        checks.append(CheckResult("warn", spec_path.name, f"core-field inspection skipped: {exc}"))

    try:
        profile = load_yaml(profile_path)
        if isinstance(profile, dict):
            versions = profile.get("standard_versions") or {}
            refs = versions.get("references") if isinstance(versions, dict) else None
            if isinstance(refs, dict):
                version = str(refs.get("version", "")).strip()
                if "填写" in version or not version:
                    checks.append(CheckResult("warn", profile_path.name, "reference standard version is not confirmed"))
    except Exception as exc:
        checks.append(CheckResult("warn", profile_path.name, f"core-field inspection skipped: {exc}"))

    return checks


def detect_workspace_root(base: Path) -> Path:
    return base.parent if base.name == "thesis-ai-standard" else base


def inspect_template_extract(base: Path) -> list[CheckResult]:
    checks: list[CheckResult] = []
    workspace_root = detect_workspace_root(base)
    template_dir = workspace_root / "paper-context" / "template-extract"
    profile_path = base / "templates" / "standard-profile.yaml"

    template_expected = False
    try:
        profile = load_yaml(profile_path)
        if isinstance(profile, dict):
            sources = profile.get("source_priority") or []
            if isinstance(sources, list) and sources:
                first = sources[0]
                if isinstance(first, dict):
                    source_path = str(first.get("file_or_url", "")).strip().lower()
                    status = str(first.get("confirmation_status", "")).strip().lower()
                    template_expected = source_path.endswith(".docx") and status == "confirmed"
    except Exception as exc:
        checks.append(CheckResult("warn", profile_path.name, f"template-extract inspection skipped: {exc}"))
        return checks

    if template_expected and not template_dir.exists():
        checks.append(
            CheckResult(
                "warn",
                str(template_dir),
                "school .docx template is confirmed in standard-profile.yaml but template-extract outputs are missing",
            )
        )
        return checks

    if not template_dir.exists():
        return checks

    for rel_name in ("template-profile.json", "template-profile.md", "template-rule-overrides.yaml"):
        path = template_dir / rel_name
        if not path.exists():
            checks.append(CheckResult("warn", str(path), "template extract directory exists but file is missing"))
            continue
        if path.stat().st_size == 0:
            checks.append(CheckResult("error", str(path), "file is empty"))
            continue
        checks.append(CheckResult("ok", str(path), "present"))
        try:
            if rel_name.endswith(".json"):
                json.loads(path.read_text(encoding="utf-8"))
            elif rel_name.endswith(".yaml"):
                load_yaml(path)
        except Exception as exc:
            checks.append(CheckResult("error", str(path), f"parse failed: {exc}"))
        else:
            if rel_name.endswith((".json", ".yaml")):
                checks.append(CheckResult("ok", str(path), "parsed"))

    return checks


def render(results: list[CheckResult]) -> str:
    lines = ["# Thesis Workspace Check", ""]
    for result in results:
        lines.append(f"- {result.status.upper()}: `{result.path}` - {result.message}")
    errors = sum(1 for item in results if item.status == "error")
    warnings = sum(1 for item in results if item.status == "warn")
    lines.extend(["", f"Summary: {errors} error(s), {warnings} warning(s)."])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a thesis-ai-standard workspace.")
    parser.add_argument("workspace", nargs="?", default="thesis-ai-standard", help="Path to thesis-ai-standard.")
    parser.add_argument("--out", help="Optional markdown report path.")
    args = parser.parse_args()

    base = Path(args.workspace).resolve()
    results: list[CheckResult] = []
    if not base.exists():
        results.append(CheckResult("error", str(base), "workspace does not exist"))
    else:
        for rel_path in REQUIRED_FILES:
            result = check_required(base, rel_path)
            results.append(result)
            if result.status == "ok" and rel_path.endswith((".json", ".yaml", ".yml")):
                results.append(check_parse(base, rel_path))
        results.extend(inspect_core_fields(base))
        results.extend(inspect_template_extract(base))

    report = render(results)
    if args.out:
        Path(args.out).resolve().write_text(report, encoding="utf-8")
        print(f"Wrote {Path(args.out).resolve()}")
    else:
        sys.stdout.write(report)

    return 1 if any(item.status == "error" for item in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
