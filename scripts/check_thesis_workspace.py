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
from collections import Counter
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


def is_placeholder(value: object) -> bool:
    text = str(value or "").strip().lower()
    if not text:
        return True
    placeholder_values = {
        "not_applicable",
        "none",
        "null",
        "missing",
        "字段名",
        "字段类型",
        "字段说明",
        "实体名称",
        "表名",
        "schema/entity/migration 路径",
        "schema/entity/migration/sql/table screenshot path",
    }
    return text in placeholder_values or "填写" in text


def database_entities_with_fields(spec: object) -> list[dict]:
    if not isinstance(spec, dict):
        return []
    design = spec.get("database_design")
    if not isinstance(design, dict):
        return []
    entities = design.get("entities") or []
    if not isinstance(entities, list):
        return []
    real_entities: list[dict] = []
    for item in entities:
        if not isinstance(item, dict) or not isinstance(item.get("fields"), list):
            continue
        if is_placeholder(item.get("name")) and is_placeholder(item.get("table")):
            continue
        real_fields = []
        for field in item.get("fields") or []:
            if isinstance(field, dict):
                if not is_placeholder(field.get("name")):
                    real_fields.append(field)
            elif not is_placeholder(field):
                real_fields.append(field)
        if real_fields:
            real_entities.append(item)
    return real_entities


def database_design_expected(spec: object) -> tuple[bool, str]:
    if not isinstance(spec, dict):
        return False, "spec unavailable"
    design = spec.get("database_design")
    if not isinstance(design, dict):
        return False, "database_design missing"
    status = str(design.get("evidence_status", "")).strip().lower()
    entities = database_entities_with_fields(spec)
    source_files = design.get("source_files") or []
    if not isinstance(source_files, list):
        source_files = [source_files]
    concrete_sources = [item for item in source_files if not is_placeholder(item)]
    if status in {"confirmed", "partial"}:
        return True, f"evidence_status is {status}"
    if entities:
        return True, "database entities with fields are present"
    if concrete_sources:
        return True, "database source files are present"
    return False, "database evidence is missing"


def inspect_chapter4_database_assets(base: Path) -> list[CheckResult]:
    checks: list[CheckResult] = []
    spec_path = base / "templates" / "thesis-ai-spec.yaml"
    workspace_root = detect_workspace_root(base)
    out_dir = workspace_root / "paper-context" / "database-design"
    figures_dir = workspace_root / "paper-context" / "figures"
    registry_path = base / "templates" / "figure-registry.yaml"

    try:
        spec = load_yaml(spec_path)
    except Exception as exc:
        return [CheckResult("warn", spec_path.name, f"chapter-4 database inspection skipped: {exc}")]

    expected, reason = database_design_expected(spec)
    if not expected:
        return checks

    entity_count = len(database_entities_with_fields(spec))
    if entity_count == 0:
        checks.append(
            CheckResult(
                "error",
                str(spec_path),
                f"Chapter 4 database design is expected because {reason}, but database_design.entities[].fields is empty",
            )
        )
        return checks

    required_files = [
        out_dir / "er" / "er-overview.json",
        out_dir / "database-tables.md",
        out_dir / "figure-registry-fragment.yaml",
        out_dir / "chapter-4-database-section.md",
    ]
    for path in required_files:
        if not path.exists():
            checks.append(CheckResult("error", str(path), "Chapter 4 database asset is missing"))
        elif path.stat().st_size == 0:
            checks.append(CheckResult("error", str(path), "Chapter 4 database asset is empty"))
        else:
            checks.append(CheckResult("ok", str(path), "present"))

    single_dir = out_dir / "er" / "single-entity"
    single_files = list(single_dir.glob("*.json")) if single_dir.exists() else []
    single_sources = [path for path in single_files if not path.name.endswith(".positioned.json")]
    if len(single_sources) < entity_count:
        checks.append(
            CheckResult(
                "error",
                str(single_dir),
                f"expected at least {entity_count} single-entity ER JSON files, found {len(single_sources)}",
            )
        )
    else:
        checks.append(CheckResult("ok", str(single_dir), f"{len(single_sources)} single-entity ER JSON file(s) present"))

    table_dir = out_dir / "tables"
    table_files = list(table_dir.glob("table-4-*.xml")) if table_dir.exists() else []
    if len(table_files) < entity_count:
        checks.append(
            CheckResult(
                "error",
                str(table_dir),
                f"expected at least {entity_count} database three-line table XML files, found {len(table_files)}",
            )
        )
    else:
        checks.append(CheckResult("ok", str(table_dir), f"{len(table_files)} database table XML file(s) present"))

    png_files = list(figures_dir.glob("figure-4-*-*.png")) if figures_dir.exists() else []
    vsdx_files = list(figures_dir.glob("figure-4-*-*.vsdx")) if figures_dir.exists() else []
    if png_files or vsdx_files:
        checks.append(CheckResult("ok", str(figures_dir), f"{len(vsdx_files)} Visio source file(s), {len(png_files)} PNG export(s) present"))
    else:
        checks.append(CheckResult("warn", str(figures_dir), "database ER JSON exists but Visio .vsdx/.png exports are not present yet"))

    try:
        registry_text = registry_path.read_text(encoding="utf-8") if registry_path.exists() else ""
        fragment_path = out_dir / "figure-registry-fragment.yaml"
        fragment_text = fragment_path.read_text(encoding="utf-8") if fragment_path.exists() else ""
        combined = registry_text + "\n" + fragment_text
        if "er_diagram" not in combined or "database_schema" not in combined:
            checks.append(
                CheckResult(
                    "warn",
                    str(registry_path),
                    "figure/table registry does not mention both er_diagram and database_schema entries",
                )
            )
    except Exception as exc:
        checks.append(CheckResult("warn", str(registry_path), f"registry inspection skipped: {exc}"))

    return checks


def inspect_figure_plan(base: Path) -> list[CheckResult]:
    checks: list[CheckResult] = []
    workspace_root = detect_workspace_root(base)
    plan_dir = workspace_root / "paper-context" / "figure-plan"
    if not plan_dir.exists():
        return checks

    required_files = [
        plan_dir / "figure-plan.yaml",
        plan_dir / "figure-registry-fragment.yaml",
        plan_dir / "figure-plan.md",
    ]
    for path in required_files:
        if not path.exists():
            checks.append(CheckResult("error", str(path), "figure plan output is missing"))
        elif path.stat().st_size == 0:
            checks.append(CheckResult("error", str(path), "figure plan output is empty"))
        else:
            checks.append(CheckResult("ok", str(path), "present"))

    plan_path = plan_dir / "figure-plan.yaml"
    if not plan_path.exists():
        return checks

    try:
        plan = load_yaml(plan_path)
    except Exception as exc:
        checks.append(CheckResult("error", str(plan_path), f"parse failed: {exc}"))
        return checks

    figures = plan.get("figures") if isinstance(plan, dict) else None
    if not isinstance(figures, list):
        checks.append(CheckResult("error", str(plan_path), "figures must be a list"))
        return checks

    if len(figures) < 8:
        checks.append(CheckResult("warn", str(plan_path), f"only {len(figures)} figure(s) planned; normal system theses usually need more or a missing-evidence explanation"))
    else:
        checks.append(CheckResult("ok", str(plan_path), f"{len(figures)} figure(s) planned"))

    for item in figures:
        if not isinstance(item, dict):
            checks.append(CheckResult("error", str(plan_path), "figure item must be an object"))
            continue
        figure_id = str(item.get("id", "unknown"))
        source_kind = str(item.get("source_kind", "")).strip().lower()
        source_file = str(item.get("source_file", "")).strip()
        status = str(item.get("status", "")).strip().lower()
        if source_kind == "visio" and not source_file.lower().endswith(".vsdx"):
            checks.append(CheckResult("error", figure_id, "Visio figure source_file must be a .vsdx path"))
        if source_kind == "screenshot":
            if source_file == "pending_user_screenshot" and status != "needs_user_screenshot":
                checks.append(CheckResult("error", figure_id, "pending screenshots must use status needs_user_screenshot"))
            if source_file != "pending_user_screenshot" and status == "needs_user_screenshot":
                checks.append(CheckResult("warn", figure_id, "screenshot has a source file but is still marked needs_user_screenshot"))

    return checks


def inspect_figure_registry(base: Path) -> list[CheckResult]:
    checks: list[CheckResult] = []
    registry_path = base / "templates" / "figure-registry.yaml"
    if not registry_path.exists():
        return checks

    try:
        registry = load_yaml(registry_path)
    except Exception as exc:
        checks.append(CheckResult("error", str(registry_path), f"parse failed: {exc}"))
        return checks

    if not isinstance(registry, dict):
        checks.append(CheckResult("error", str(registry_path), "figure registry must be a mapping"))
        return checks

    for key, label in (("figures", "figure"), ("tables", "table")):
        items = registry.get(key) or []
        if not isinstance(items, list):
            checks.append(CheckResult("error", str(registry_path), f"{key} must be a list"))
            continue
        ids = [
            str(item.get("id", "")).strip()
            for item in items
            if isinstance(item, dict) and str(item.get("id", "")).strip()
        ]
        duplicates = sorted(identifier for identifier, count in Counter(ids).items() if count > 1)
        if duplicates:
            checks.append(CheckResult("error", str(registry_path), f"duplicate {label} id(s): {', '.join(duplicates)}"))
        elif ids:
            checks.append(CheckResult("ok", str(registry_path), f"{len(ids)} {label} id(s) unique"))

    return checks


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
        results.extend(inspect_figure_registry(base))
        results.extend(inspect_chapter4_database_assets(base))
        results.extend(inspect_figure_plan(base))
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
