#!/usr/bin/env python3
"""Run final-delivery preflight checks for a thesis workspace."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from check_figure_assets import validate_figure_registry
from docx_io import ensure_readable_docx


def load_yaml(path: Path) -> object:
    try:
        import yaml  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(f"PyYAML not installed; skipped YAML parse: {exc}") from exc
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@dataclass
class CheckResult:
    status: str
    path: str
    message: str


def add_result(results: list[CheckResult], status: str, path: Path | str, message: str) -> None:
    results.append(CheckResult(status, str(path), message))


def parse_file(path: Path) -> object:
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    if path.suffix.lower() in {".yaml", ".yml"}:
        return load_yaml(path)
    return path.read_text(encoding="utf-8")


def check_required_file(results: list[CheckResult], path: Path) -> object | None:
    if not path.exists():
        add_result(results, "error", path, "required file is missing")
        return None
    if path.is_file() and path.stat().st_size == 0:
        add_result(results, "error", path, "file is empty")
        return None
    add_result(results, "ok", path, "present")
    try:
        payload = parse_file(path)
    except RuntimeError as exc:
        add_result(results, "warn", path, str(exc))
        return None
    except Exception as exc:
        add_result(results, "error", path, f"parse failed: {exc}")
        return None
    add_result(results, "ok", path, "parsed")
    return payload


def looks_like_placeholder(value: str) -> bool:
    text = value.strip()
    if not text:
        return True
    markers = ("填写", "TODO", "TBD", "待补", "示例", "X-1", "图X-", "表X-", "(X-")
    upper = text.upper()
    return any(marker in text for marker in markers) or upper in {"PENDING", "PLANNED"}


def should_check_local_path(value: str) -> bool:
    text = value.strip()
    if not text or looks_like_placeholder(text):
        return False
    if text.startswith(("http://", "https://")):
        return False
    return True


def resolve_workspace_path(workspace: Path, raw: str) -> Path:
    candidate = Path(raw)
    if candidate.is_absolute():
        return candidate
    return (workspace / candidate).resolve()


def inspect_registry_items(
    results: list[CheckResult],
    workspace: Path,
    section_name: str,
    items: list[dict[str, Any]],
) -> None:
    strict_statuses = {"checked", "inserted"}
    for idx, item in enumerate(items, 1):
        item_id = str(item.get("id", "")).strip() or f"{section_name}[{idx}]"
        status = str(item.get("status", "")).strip().lower()
        path_label = f"figure-registry:{section_name}:{item_id}"

        if status in strict_statuses:
            first_mentioned = str(item.get("first_mentioned_in", "")).strip()
            if looks_like_placeholder(first_mentioned):
                add_result(results, "warn", path_label, "first_mentioned_in still looks unfilled")

            evidence = item.get("evidence") or []
            if not isinstance(evidence, list) or not any(str(entry).strip() for entry in evidence):
                add_result(results, "warn", path_label, "evidence list is empty for a checked/inserted item")

        for key in ("source_file", "export_file", "expression_source"):
            raw = str(item.get(key, "")).strip()
            if not should_check_local_path(raw):
                continue
            target = resolve_workspace_path(workspace, raw)
            if target.exists():
                add_result(results, "ok", target, f"resolved from {path_label}:{key}")
            else:
                severity = "error" if status == "inserted" and key == "export_file" else "warn"
                add_result(results, severity, target, f"missing path referenced by {path_label}:{key}")


def inspect_figure_registry(results: list[CheckResult], workspace: Path, registry_path: Path) -> None:
    payload = check_required_file(results, registry_path)
    if not isinstance(payload, dict):
        return
    for item in validate_figure_registry(registry_path, workspace):
        if item.message == "parsed":
            continue
        results.append(item)


def render(results: list[CheckResult]) -> str:
    lines = ["# Thesis Delivery Preflight", ""]
    for item in results:
        lines.append(f"- {item.status.upper()}: `{item.path}` - {item.message}")
    errors = sum(1 for item in results if item.status == "error")
    warnings = sum(1 for item in results if item.status == "warn")
    lines.extend(["", f"Summary: {errors} error(s), {warnings} warning(s)."])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run thesis final-delivery preflight checks.")
    parser.add_argument("thesis_docx", help="Final thesis .docx to inspect.")
    parser.add_argument("--workspace", default=".", help="Workspace root containing thesis-ai-standard and paper-context.")
    parser.add_argument("--out", help="Optional markdown report output path.")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    results: list[CheckResult] = []

    try:
        thesis_docx = ensure_readable_docx(Path(args.thesis_docx), "thesis docx")
    except Exception as exc:
        add_result(results, "error", args.thesis_docx, str(exc))
        thesis_docx = None
    else:
        add_result(results, "ok", thesis_docx, "readable docx package")

    thesis_standard = workspace / "thesis-ai-standard"
    if not thesis_standard.exists():
        add_result(results, "error", thesis_standard, "thesis-ai-standard directory is missing")
    else:
        add_result(results, "ok", thesis_standard, "present")
        templates_dir = thesis_standard / "templates"
        check_required_file(results, templates_dir / "standard-profile.yaml")
        check_required_file(results, templates_dir / "thesis-ai-spec.yaml")
        inspect_figure_registry(results, workspace, templates_dir / "figure-registry.yaml")

    template_extract = workspace / "paper-context" / "template-extract"
    if template_extract.exists():
        add_result(results, "ok", template_extract, "present")
        check_required_file(results, template_extract / "template-profile.json")
        check_required_file(results, template_extract / "template-profile.md")
        overrides_path = template_extract / "template-rule-overrides.yaml"
        if overrides_path.exists():
            check_required_file(results, overrides_path)
        else:
            add_result(results, "warn", overrides_path, "template extract exists but template-rule-overrides.yaml is missing")
    else:
        add_result(results, "warn", template_extract, "template-extract directory is missing")

    workflow_dir = workspace / "paper-context" / "workflow"
    revision_log = workflow_dir / "revision-log.md"
    revision_trace = workflow_dir / "revision-trace.jsonl"
    if revision_log.exists():
        add_result(results, "ok", revision_log, "present")
    else:
        add_result(results, "warn", revision_log, "revision log is missing; final delivery changes may be hard to trace")
    if revision_trace.exists():
        add_result(results, "ok", revision_trace, "present")
    else:
        add_result(results, "warn", revision_trace, "machine-readable revision trace is missing")

    if thesis_docx is not None and thesis_docx.parent != workspace:
        add_result(results, "warn", thesis_docx, "docx is outside the declared workspace root")

    report = render(results)
    if args.out:
        out_path = Path(args.out).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")
        print(f"Wrote {out_path}")
    else:
        sys.stdout.write(report)

    return 1 if any(item.status == "error" for item in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
