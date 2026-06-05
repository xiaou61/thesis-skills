#!/usr/bin/env python3
"""Compare DOCX section/page model with an extracted template profile."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import zipfile
from xml.etree import ElementTree as ET

from docx_io import ensure_readable_docx
from extract_docx_template_profile import extract_sections, load_relationships, read_xml


def load_profile(path: Path | None) -> dict:
    if path is None:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def current_sections(docx: Path) -> list[dict]:
    docx = ensure_readable_docx(docx)
    with zipfile.ZipFile(docx) as archive:
        document_root = read_xml(archive, "word/document.xml")
        rels = load_relationships(read_xml(archive, "word/_rels/document.xml.rels"))
        return extract_sections(document_root, rels, archive)


def approx_equal(left: object, right: object, tolerance: float) -> bool:
    if left is None or right is None:
        return True
    try:
        return abs(float(left) - float(right)) <= tolerance
    except (TypeError, ValueError):
        return left == right


def check_docx(docx: Path, profile_path: Path | None, tolerance_cm: float) -> dict[str, object]:
    profile = load_profile(profile_path)
    expected_sections = profile.get("sections", [])
    actual_sections = current_sections(docx)
    errors: list[str] = []
    warnings: list[str] = []

    if expected_sections and len(actual_sections) != len(expected_sections):
        warnings.append(f"section count differs from template: actual {len(actual_sections)}, expected {len(expected_sections)}")
    if not expected_sections:
        warnings.append("template profile has no sections; page model comparison is weak")

    comparisons: list[dict[str, object]] = []
    for index, actual in enumerate(actual_sections):
        expected = expected_sections[index] if index < len(expected_sections) else {}
        item_errors: list[str] = []
        item_warnings: list[str] = []
        expected_page = expected.get("page", {})
        actual_page = actual.get("page", {})
        if expected_page and actual_page.get("orientation") != expected_page.get("orientation"):
            item_warnings.append(
                f"orientation differs: actual {actual_page.get('orientation')}, expected {expected_page.get('orientation')}"
            )
        for edge in ("top", "bottom", "left", "right"):
            actual_margin = actual.get("margins_cm", {}).get(edge)
            expected_margin = expected.get("margins_cm", {}).get(edge)
            if not approx_equal(actual_margin, expected_margin, tolerance_cm):
                item_errors.append(f"{edge} margin differs: actual {actual_margin}, expected {expected_margin}")
        if item_errors:
            errors.extend(f"section {index + 1}: {message}" for message in item_errors)
        if item_warnings:
            warnings.extend(f"section {index + 1}: {message}" for message in item_warnings)
        comparisons.append(
            {
                "section": index + 1,
                "actual": actual,
                "expected": expected,
                "errors": item_errors,
                "warnings": item_warnings,
            }
        )

    return {
        "docx": str(docx),
        "templateProfile": str(profile_path) if profile_path else "",
        "actualSections": len(actual_sections),
        "expectedSections": len(expected_sections),
        "errors": errors,
        "warnings": warnings,
        "comparisons": comparisons,
    }


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# DOCX Page Model Check",
        "",
        f"- File: `{report['docx']}`",
        f"- Template profile: `{report['templateProfile']}`",
        f"- Sections: `{report['actualSections']}` actual / `{report['expectedSections']}` expected",
        f"- Errors: `{len(report['errors'])}`",
        f"- Warnings: `{len(report['warnings'])}`",
    ]
    if report["errors"]:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {item}" for item in report["errors"])
    if report["warnings"]:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {item}" for item in report["warnings"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check DOCX page model against extracted template profile.")
    parser.add_argument("docx")
    parser.add_argument("--template-profile")
    parser.add_argument("--tolerance-cm", type=float, default=0.05)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out")
    args = parser.parse_args()

    report = check_docx(
        Path(args.docx).resolve(),
        Path(args.template_profile).resolve() if args.template_profile else None,
        args.tolerance_cm,
    )
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n" if args.json else render_markdown(report)
    if args.out:
        Path(args.out).resolve().write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
