#!/usr/bin/env python3
"""Validate thesis-standardizer skill wiring and gate discoverability."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALID_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
PATH_PATTERN = re.compile(
    r"(?P<path>(?:scripts|references|assets)/[^\s`'\"<>]+?\.(?:py|ps1|md|yaml|yml|json|docx|png|vsdx))"
)

REQUIRED_ENTRYPOINT_TERMS = [
    "scripts/check_final_thesis_docx.ps1",
    "references/hard-gate-rule-catalog.md",
    "references/docx-production-rules.md",
    "references/variant-generation-workflow.md",
    "scripts/generate_thesis_variants.py",
    "scripts/compare_thesis_variants.py",
]

REQUIRED_GATES = [
    "check_docx_three_line_tables.py",
    "check_docx_table_continuations.ps1",
    "check_docx_reference_hyperlinks.py",
    "check_docx_visio_ole.py",
    "check_docx_duplicate_figure_previews.py",
    "check_figure_preview_aspects.py",
    "check_docx_thesis_quality.py",
    "check_docx_thesis_voice.py",
    "check_docx_components.py",
    "check_docx_citation_closure.py",
    "check_docx_caption_closure.py",
    "check_docx_structural_hygiene.py",
]

ALLOWED_UNREACHABLE_PREFIXES = (
    "assets/thesis-ai-standard/",
    "references/optimization-variants/",
)

ALLOWED_UNREACHABLE_FILES = {
    "references/quality-gates.md",
    "references/standards-and-template-resolution.md",
    "references/template-extraction-workflow.md",
    "scripts/bootstrap_thesis_project.py",
    "scripts/docx_analysis.py",
    "scripts/docx_io.py",
    "scripts/generate_template_rule_overrides.py",
    "scripts/init_workflow_logs.py",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_root", nargs="?", type=Path, default=ROOT)
    parser.add_argument("--json", action="store_true", help="Emit JSON report.")
    parser.add_argument("--max-skill-lines", type=int, default=500)
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end].strip()
    values: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values, text[end + 4 :]


def referenced_paths(root: Path, reachable_files: list[Path]) -> set[str]:
    refs: set[str] = set()
    for path in reachable_files:
        text = read_text(path)
        base = path.parent
        for match in PATH_PATTERN.finditer(text):
            raw = match.group("path").replace("\\", "/").strip()
            raw = raw.rstrip("`'\"),.;:")
            resolved = (base / raw).resolve() if not raw.startswith(("scripts/", "references/", "assets/")) else (root / raw).resolve()
            try:
                refs.add(resolved.relative_to(root).as_posix())
            except ValueError:
                refs.add(raw)
        if path.suffix.lower() in {".md", ".py", ".ps1"}:
            for name in re.findall(r"`?([A-Za-z0-9_]+(?:\.py|\.ps1))`?", text):
                script = root / "scripts" / name
                if script.exists():
                    refs.add(script.relative_to(root).as_posix())
            for name in re.findall(r"from\s+([A-Za-z0-9_]+)\s+import|import\s+([A-Za-z0-9_]+)", text):
                module = next((part for part in name if part), "")
                script = root / "scripts" / f"{module}.py"
                if script.exists():
                    refs.add(script.relative_to(root).as_posix())
        if path.name == "init_thesis_workspace.py":
            asset_root = root / "assets" / "thesis-ai-standard"
            if asset_root.exists():
                for asset in asset_root.rglob("*"):
                    if asset.is_file():
                        refs.add(asset.relative_to(root).as_posix())
    return refs


def collect_reachable(root: Path) -> tuple[set[str], set[str]]:
    reachable = {"SKILL.md"}
    missing: set[str] = set()
    queue = [root / "SKILL.md"]
    while queue:
        current = queue.pop(0)
        refs = referenced_paths(root, [current])
        for ref in refs:
            if ref in reachable:
                continue
            target = root / ref
            if not target.exists():
                missing.add(ref)
                continue
            reachable.add(ref)
            if target.suffix.lower() in {".md", ".py", ".ps1", ".yaml", ".yml", ".json"}:
                queue.append(target)
    return reachable, missing


def tracked_skill_files(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "scripts", "references", "assets"],
        cwd=str(root),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )
    if result.returncode == 0:
        return sorted(line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip())

    files: list[str] = []
    for folder in ("scripts", "references", "assets"):
        base = root / folder
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                files.append(path.relative_to(root).as_posix())
    return sorted(files)


def check(root: Path, max_skill_lines: int) -> dict[str, object]:
    root = root.resolve()
    skill = root / "SKILL.md"
    errors: list[str] = []
    warnings: list[str] = []

    if not skill.exists():
        return {"skill_root": str(root), "passed": False, "errors": ["SKILL.md is missing"], "warnings": []}

    text = read_text(skill)
    frontmatter, body = parse_frontmatter(text)
    name = frontmatter.get("name", "")
    description = frontmatter.get("description", "")
    if not name:
        errors.append("frontmatter name is missing")
    elif not VALID_NAME.match(name):
        errors.append(f"frontmatter name is invalid: {name}")
    if not description:
        errors.append("frontmatter description is missing")
    elif len(description) < 80:
        warnings.append("frontmatter description is short; trigger coverage may be weak")
    if text.count("```") % 2 != 0:
        errors.append("SKILL.md has an unclosed fenced code block")

    line_count = len(text.splitlines())
    if line_count > max_skill_lines:
        warnings.append(f"SKILL.md has {line_count} lines; consider moving detail to references/")

    for term in REQUIRED_ENTRYPOINT_TERMS:
        if term not in text:
            errors.append(f"SKILL.md does not reference required entrypoint: {term}")

    reachable, missing = collect_reachable(root)
    for path in sorted(missing):
        errors.append(f"referenced file is missing: {path}")

    all_files = tracked_skill_files(root)
    orphaned = [
        path
        for path in all_files
        if path not in reachable
        and path not in ALLOWED_UNREACHABLE_FILES
        and not any(path.startswith(prefix) for prefix in ALLOWED_UNREACHABLE_PREFIXES)
    ]
    for path in orphaned:
        warnings.append(f"file is not reachable from SKILL.md: {path}")

    aggregate = read_text(root / "scripts" / "check_final_thesis_docx.ps1") if (root / "scripts" / "check_final_thesis_docx.ps1").exists() else ""
    if not aggregate:
        errors.append("aggregate gate script is missing: scripts/check_final_thesis_docx.ps1")
    for gate in REQUIRED_GATES:
        if not (root / "scripts" / gate).exists():
            errors.append(f"required gate script is missing: scripts/{gate}")
        elif gate not in aggregate and gate != "check_docx_duplicate_figure_previews.py" and gate != "check_figure_preview_aspects.py":
            errors.append(f"required gate is not wired into aggregate script: {gate}")

    variant = root / "scripts" / "generate_thesis_variants.py"
    if variant.exists():
        variant_text = read_text(variant)
        if "DEFAULT_GENERATOR" not in variant_text:
            errors.append("variant generator does not declare DEFAULT_GENERATOR")
        if "if args.run and not args.generator.exists()" not in variant_text:
            warnings.append("variant generator should fail early when the selected generator is missing")

    return {
        "skill_root": str(root),
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "skill_lines": line_count,
        "reachable_files": sorted(reachable),
        "orphaned_files": orphaned,
    }


def main() -> int:
    args = parse_args()
    report = check(args.skill_root, args.max_skill_lines)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("# Skill Integrity")
        print(f"- Skill root: `{report['skill_root']}`")
        print(f"- Passed: `{str(report['passed']).lower()}`")
        print(f"- Errors: `{len(report['errors'])}`")
        print(f"- Warnings: `{len(report['warnings'])}`")
        print(f"- SKILL.md lines: `{report.get('skill_lines', 0)}`")
        if report["errors"]:
            print("\n## Errors")
            for item in report["errors"]:
                print(f"- {item}")
        if report["warnings"]:
            print("\n## Warnings")
            for item in report["warnings"]:
                print(f"- {item}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
