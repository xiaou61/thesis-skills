#!/usr/bin/env python3
"""Validate figure/table/equation asset coverage from figure-registry.yaml."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


STRICT_ASSET_STATUSES = {"checked", "inserted"}
EDITABLE_SOURCE_TYPES = {
    "architecture",
    "flowchart",
    "use_case",
    "er_diagram",
    "sequence",
    "module",
    "model",
    "data_structure",
    "research_framework",
}
SCREENSHOT_TYPES = {"ui_screenshot", "experiment_screenshot", "test_report", "software_output"}
EDITABLE_SUFFIXES = {".drawio", ".mmd", ".mermaid", ".puml", ".plantuml", ".svg", ".vsdx"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff"}


def load_yaml(path: Path) -> object:
    try:
        import yaml  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"PyYAML not installed; skipped YAML parse: {exc}") from exc
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@dataclass
class CheckResult:
    status: str
    path: str
    message: str


def add_result(results: list[CheckResult], status: str, path: Path | str, message: str) -> None:
    results.append(CheckResult(status, str(path), message))


def looks_like_placeholder(value: str) -> bool:
    text = value.strip()
    if not text:
        return True
    markers = ("填写", "TODO", "TBD", "待补", "示例", "X-1", "图X-", "表X-", "(X-")
    return any(marker in text for marker in markers)


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


def validate_source_file(
    results: list[CheckResult],
    item_label: str,
    item_type: str,
    source_kind: str,
    source_file: str,
    workspace: Path,
    strict: bool,
) -> None:
    if not should_check_local_path(source_file):
        if item_type in EDITABLE_SOURCE_TYPES and strict:
            add_result(results, "warn", item_label, "editable figure is checked/inserted but source_file still looks unfilled")
        return

    source_path = resolve_workspace_path(workspace, source_file)
    if not source_path.exists():
        add_result(results, "error" if strict else "warn", source_path, f"missing source asset for {item_label}")
        return

    add_result(results, "ok", source_path, f"source asset present for {item_label}")
    suffix = source_path.suffix.lower()

    if item_type in EDITABLE_SOURCE_TYPES and suffix not in EDITABLE_SUFFIXES:
        add_result(results, "warn", source_path, f"expected editable diagram source for {item_label}, got {suffix or 'no extension'}")

    if item_type in SCREENSHOT_TYPES and source_kind not in {"screenshot", "software_output"}:
        add_result(results, "warn", item_label, f"screenshot-like figure should usually use screenshot/software_output source_kind, got {source_kind or 'empty'}")


def validate_export_file(
    results: list[CheckResult],
    item_label: str,
    export_file: str,
    workspace: Path,
    required: bool,
) -> None:
    if not should_check_local_path(export_file):
        if required:
            add_result(results, "error", item_label, "inserted figure is missing a concrete export_file")
        return

    export_path = resolve_workspace_path(workspace, export_file)
    if not export_path.exists():
        add_result(results, "error" if required else "warn", export_path, f"missing exported figure asset for {item_label}")
        return

    add_result(results, "ok", export_path, f"exported figure asset present for {item_label}")
    if export_path.suffix.lower() not in IMAGE_SUFFIXES:
        add_result(results, "warn", export_path, f"exported asset for {item_label} does not look like an image")
    if export_path.stat().st_size <= 1024:
        add_result(results, "warn", export_path, f"exported asset for {item_label} is very small (<= 1KB)")


def validate_evidence(
    results: list[CheckResult],
    item_label: str,
    evidence: Any,
    workspace: Path,
    strict: bool,
) -> None:
    if not isinstance(evidence, list) or not any(str(entry).strip() for entry in evidence):
        if strict:
            add_result(results, "warn", item_label, "checked/inserted item has no evidence entries")
        return
    for raw in evidence:
        text = str(raw).strip()
        if not should_check_local_path(text):
            continue
        target = resolve_workspace_path(workspace, text)
        if target.exists():
            add_result(results, "ok", target, f"evidence path present for {item_label}")
        else:
            add_result(results, "warn", target, f"missing evidence path referenced by {item_label}")


def validate_figure_registry(registry_path: Path, workspace: Path) -> list[CheckResult]:
    results: list[CheckResult] = []
    if not registry_path.exists():
        add_result(results, "error", registry_path, "figure-registry.yaml is missing")
        return results

    try:
        payload = load_yaml(registry_path)
    except RuntimeError as exc:
        add_result(results, "warn", registry_path, str(exc))
        return results
    except Exception as exc:
        add_result(results, "error", registry_path, f"parse failed: {exc}")
        return results

    add_result(results, "ok", registry_path, "parsed")
    if not isinstance(payload, dict):
        add_result(results, "error", registry_path, "registry root is not a mapping")
        return results

    figures = payload.get("figures") or []
    if not isinstance(figures, list):
        add_result(results, "error", registry_path, "figures is not a list")
        return results

    for idx, item in enumerate(figures, 1):
        if not isinstance(item, dict):
            add_result(results, "warn", f"figure[{idx}]", "entry is not a mapping")
            continue
        item_id = str(item.get("id", "")).strip() or f"figure[{idx}]"
        item_label = f"figure:{item_id}"
        item_type = str(item.get("type", "")).strip()
        source_kind = str(item.get("source_kind", "")).strip()
        status = str(item.get("status", "")).strip().lower()
        strict = status in STRICT_ASSET_STATUSES

        first_mentioned = str(item.get("first_mentioned_in", "")).strip()
        if strict and looks_like_placeholder(first_mentioned):
            add_result(results, "warn", item_label, "first_mentioned_in still looks unfilled")

        validate_source_file(results, item_label, item_type, source_kind, str(item.get("source_file", "")), workspace, strict)
        validate_export_file(results, item_label, str(item.get("export_file", "")), workspace, required=status == "inserted")
        validate_evidence(results, item_label, item.get("evidence"), workspace, strict)

    for section_name in ("tables", "equations"):
        items = payload.get(section_name) or []
        if not isinstance(items, list):
            add_result(results, "warn", registry_path, f"{section_name} is not a list")
            continue
        for idx, item in enumerate(items, 1):
            if not isinstance(item, dict):
                add_result(results, "warn", f"{section_name}[{idx}]", "entry is not a mapping")
                continue
            item_id = str(item.get("id", "")).strip() or f"{section_name}[{idx}]"
            item_label = f"{section_name[:-1]}:{item_id}"
            status = str(item.get("status", "")).strip().lower()
            strict = status in STRICT_ASSET_STATUSES
            first_mentioned = str(item.get("first_mentioned_in", "")).strip()
            if strict and looks_like_placeholder(first_mentioned):
                add_result(results, "warn", item_label, "first_mentioned_in still looks unfilled")
            validate_evidence(results, item_label, item.get("evidence"), workspace, strict)
            source_field = "expression_source" if section_name == "equations" else "source_file"
            source_text = str(item.get(source_field, "")).strip()
            if should_check_local_path(source_text):
                target = resolve_workspace_path(workspace, source_text)
                if target.exists():
                    add_result(results, "ok", target, f"source asset present for {item_label}")
                else:
                    add_result(results, "warn" if strict else "ok", target, f"missing source path referenced by {item_label}")

    return results


def render(results: list[CheckResult]) -> str:
    lines = ["# Figure Asset Validation", ""]
    for item in results:
        lines.append(f"- {item.status.upper()}: `{item.path}` - {item.message}")
    errors = sum(1 for item in results if item.status == "error")
    warnings = sum(1 for item in results if item.status == "warn")
    lines.extend(["", f"Summary: {errors} error(s), {warnings} warning(s)."])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate figure/table/equation assets from figure-registry.yaml.")
    parser.add_argument("--workspace", default=".", help="Workspace root containing thesis-ai-standard.")
    parser.add_argument(
        "--registry",
        help="Optional figure-registry.yaml path. Defaults to <workspace>/thesis-ai-standard/templates/figure-registry.yaml.",
    )
    parser.add_argument("--out", help="Optional markdown report path.")
    parser.add_argument("--json-out", help="Optional JSON report path.")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    registry_path = Path(args.registry).resolve() if args.registry else workspace / "thesis-ai-standard" / "templates" / "figure-registry.yaml"
    results = validate_figure_registry(registry_path, workspace)
    report = render(results)

    if args.out:
        out_path = Path(args.out).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")
        print(f"Wrote {out_path}")
    else:
        sys.stdout.write(report)

    if args.json_out:
        json_path = Path(args.json_out).resolve()
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps([item.__dict__ for item in results], ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {json_path}")

    return 1 if any(item.status == "error" for item in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
