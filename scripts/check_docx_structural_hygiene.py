#!/usr/bin/env python3
"""Check DOCX package hygiene: comments, revisions, hidden text, and broken relationships."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import posixpath
import sys
import zipfile
from xml.etree import ElementTree as ET

from docx_io import ensure_readable_docx


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
PR_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"w": W_NS, "pr": PR_NS}
W = f"{{{W_NS}}}"

REVISION_TAGS = {"ins", "del", "moveFrom", "moveTo", "rPrChange", "pPrChange", "tblPrChange", "tcPrChange", "trPrChange"}


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def part_dir(part_name: str) -> str:
    directory = posixpath.dirname(part_name)
    return directory if directory else "."


def relationship_part_for(part_name: str) -> str:
    directory = posixpath.dirname(part_name)
    base = posixpath.basename(part_name)
    if directory:
        return f"{directory}/_rels/{base}.rels"
    return f"_rels/{base}.rels"


def resolve_target(source_part: str, target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join(part_dir(source_part), target))


def check_relationships(archive: zipfile.ZipFile, names: set[str]) -> list[str]:
    errors: list[str] = []
    rel_parts = [name for name in names if name.endswith(".rels")]
    for rel_part in rel_parts:
        try:
            root = ET.fromstring(archive.read(rel_part))
        except ET.ParseError as exc:
            errors.append(f"relationship part is not valid XML: {rel_part}: {exc}")
            continue
        if rel_part == "_rels/.rels":
            source_part = ""
        else:
            parent_dir = posixpath.dirname(posixpath.dirname(rel_part))
            source_base = posixpath.basename(rel_part).replace(".rels", "")
            source_part = posixpath.normpath(posixpath.join(parent_dir, source_base))
        for rel in root.findall(f"{{{PR_NS}}}Relationship"):
            target = rel.get("Target") or ""
            mode = rel.get("TargetMode") or ""
            rel_id = rel.get("Id") or ""
            if not target or mode.lower() == "external":
                continue
            resolved = resolve_target(source_part, target)
            if resolved not in names:
                errors.append(f"broken relationship {rel_id} in {rel_part}: missing {resolved}")
    return errors


def count_nodes(root: ET.Element, names: set[str]) -> int:
    return sum(1 for node in root.iter() if local_name(node.tag) in names)


def check_docx(path: Path) -> dict[str, object]:
    docx = ensure_readable_docx(path)
    errors: list[str] = []
    warnings: list[str] = []
    with zipfile.ZipFile(docx) as archive:
        names = set(archive.namelist())
        document = ET.fromstring(archive.read("word/document.xml"))

        comments = len([name for name in names if name.startswith("word/comments") and name.endswith(".xml")])
        revisions = count_nodes(document, REVISION_TAGS)
        hidden = len(document.findall(".//w:vanish", NS))
        comment_refs = len(document.findall(".//w:commentRangeStart", NS)) + len(document.findall(".//w:commentReference", NS))

        if comments or comment_refs:
            errors.append(f"unresolved Word comments detected: commentParts={comments}, commentRefs={comment_refs}")
        if revisions:
            errors.append(f"tracked changes/revision markup detected: {revisions}")
        if hidden:
            errors.append(f"hidden text property detected in body: {hidden}")

        errors.extend(check_relationships(archive, names))

        core_props = "docProps/core.xml" in names
        app_props = "docProps/app.xml" in names
        if not core_props or not app_props:
            warnings.append("standard docProps core/app metadata parts are missing")

    return {
        "docx": str(docx),
        "comments": comments,
        "commentReferences": comment_refs,
        "revisions": revisions,
        "hiddenTextProperties": hidden,
        "errors": errors,
        "warnings": warnings,
    }


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# DOCX Structural Hygiene Check",
        "",
        f"- File: `{report['docx']}`",
        f"- Comments: `{report['comments']}`",
        f"- Comment references: `{report['commentReferences']}`",
        f"- Revisions: `{report['revisions']}`",
        f"- Hidden text properties: `{report['hiddenTextProperties']}`",
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
    parser = argparse.ArgumentParser(description="Check DOCX comments, revisions, hidden text, and relationships.")
    parser.add_argument("docx", help="DOCX file.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", help="Optional report output path.")
    args = parser.parse_args()

    report = check_docx(Path(args.docx).resolve())
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n" if args.json else render_markdown(report)
    if args.out:
        Path(args.out).resolve().write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
