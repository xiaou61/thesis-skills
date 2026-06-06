#!/usr/bin/env python3
"""Check Word internal hyperlinks from numeric citations to reference entries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

from docx_analysis import component_positions, load_blocks, split_before_references
from docx_io import ensure_readable_docx


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
W = f"{{{W_NS}}}"

CITATION_RE = re.compile(r"(?<!\d)\[([0-9,\-，、\s]+)\]")
SINGLE_CITATION_RE = re.compile(r"^\[([0-9]{1,3})\]$")
REF_PREFIX_RE = re.compile(r"^\s*\[?([0-9]{1,3})\]?[\.、\s]")
PUNCTUATION_BEFORE_CITATION_RE = re.compile(r"([。！？；，、,.!?;:：])\s*(\[[0-9]{1,3}\])")


def expand_citation_numbers(raw: str) -> list[int]:
    numbers: list[int] = []
    for part in re.split(r"[,，、\s]+", raw):
        if not part:
            continue
        if "-" in part:
            left, right = part.split("-", 1)
            if left.isdigit() and right.isdigit():
                start, end = int(left), int(right)
                if start <= end and end - start <= 50:
                    numbers.extend(range(start, end + 1))
                continue
        if part.isdigit():
            numbers.append(int(part))
    return numbers


def element_text(element: ET.Element) -> str:
    return "".join(node.text or "" for node in element.findall(".//w:t", NS))


def load_document_root(path: Path) -> ET.Element:
    docx = ensure_readable_docx(path)
    with zipfile.ZipFile(docx) as archive:
        return ET.fromstring(archive.read("word/document.xml"))


def body_children(root: ET.Element) -> list[ET.Element]:
    body = root.find("w:body", NS)
    if body is None:
        return []
    return list(body)


def block_index_by_element(root: ET.Element) -> dict[int, int]:
    mapping: dict[int, int] = {}
    index = 0
    for child in body_children(root):
        if child.tag not in {W + "p", W + "tbl"}:
            continue
        index += 1
        mapping[id(child)] = index
    return mapping


def reference_entries(reference_blocks: list) -> dict[int, int]:
    entries: dict[int, int] = {}
    for block in reference_blocks:
        match = REF_PREFIX_RE.match(block.text.strip())
        if match:
            entries[int(match.group(1))] = block.index
    return entries


def collect_reference_bookmarks(root: ET.Element) -> dict[int, dict[str, object]]:
    bookmarks: dict[int, dict[str, object]] = {}
    block_map = block_index_by_element(root)
    parents = {child: parent for parent in root.iter() for child in list(parent)}
    for node in root.findall(".//w:bookmarkStart", NS):
        name = node.get(W + "name") or ""
        match = re.fullmatch(r"ref_([0-9]{1,3})", name)
        if not match:
            continue
        parent = parents.get(node)
        while parent is not None and parent.tag not in {W + "p", W + "tbl"}:
            parent = parents.get(parent)
        bookmarks[int(match.group(1))] = {
            "anchor": name,
            "block": block_map.get(id(parent), None) if parent is not None else None,
        }
    return bookmarks


def collect_hyperlinked_citations(root: ET.Element, body_block_count: int) -> list[dict[str, object]]:
    citations: list[dict[str, object]] = []
    block_index = 0
    for child in body_children(root):
        if child.tag not in {W + "p", W + "tbl"}:
            continue
        block_index += 1
        if block_index > body_block_count:
            break
        for hyperlink in child.findall(".//w:hyperlink", NS):
            text = element_text(hyperlink).strip()
            match = SINGLE_CITATION_RE.match(text)
            if not match:
                continue
            is_superscript = False
            for run in hyperlink.findall(".//w:r", NS):
                if not element_text(run).strip():
                    continue
                vert = run.find("w:rPr/w:vertAlign", NS)
                if vert is not None and (vert.get(W + "val") or "") == "superscript":
                    is_superscript = True
                    break
            citations.append(
                {
                    "number": int(match.group(1)),
                    "anchor": hyperlink.get(W + "anchor") or "",
                    "block": block_index,
                    "text": text,
                    "superscript": is_superscript,
                }
            )
    return citations


def collect_unlinked_single_citations(root: ET.Element, body_block_count: int) -> list[dict[str, object]]:
    citations: list[dict[str, object]] = []
    parents = {child_node: parent_node for parent_node in root.iter() for child_node in list(parent_node)}
    block_index = 0
    for child in body_children(root):
        if child.tag not in {W + "p", W + "tbl"}:
            continue
        block_index += 1
        if block_index > body_block_count:
            break
        pieces: list[str] = []
        for node in child.iter(W + "t"):
            parent = parents.get(node)
            inside_hyperlink = False
            while parent is not None and parent is not child:
                if parent.tag == W + "hyperlink":
                    inside_hyperlink = True
                    break
                parent = parents.get(parent)
            if not inside_hyperlink:
                pieces.append(node.text or "")
        text = "".join(pieces)
        for match in re.finditer(r"(?<!\d)\[([0-9]{1,3})\]", text):
            citations.append({"number": int(match.group(1)), "block": block_index, "text": match.group(0)})
    return citations


def check_docx(path: Path) -> dict[str, object]:
    blocks = load_blocks(path)
    positions = component_positions(blocks)
    body_blocks, reference_blocks = split_before_references(blocks)
    body_text = "\n".join(block.text for block in body_blocks if block.text)
    cited_numbers = sorted(set(number for match in CITATION_RE.findall(body_text) for number in expand_citation_numbers(match)))

    root = load_document_root(path)
    refs = reference_entries(reference_blocks)
    bookmarks = collect_reference_bookmarks(root)
    links = collect_hyperlinked_citations(root, len(body_blocks))
    unlinked = collect_unlinked_single_citations(root, len(body_blocks))

    linked_by_number: dict[int, list[dict[str, object]]] = {}
    for link in links:
        linked_by_number.setdefault(int(link["number"]), []).append(link)

    errors: list[str] = []
    warnings: list[str] = []
    if "references" not in positions:
        errors.append("missing references section")
    for block in body_blocks:
        for match in PUNCTUATION_BEFORE_CITATION_RE.finditer(block.text):
            errors.append(
                f"body citation {match.group(2)} at block {block.index} appears after punctuation `{match.group(1)}`; place it before the punctuation"
            )
    for number in cited_numbers:
        if number not in refs:
            errors.append(f"citation [{number}] has no matching reference entry")
            continue
        bookmark = bookmarks.get(number)
        if not bookmark:
            errors.append(f"reference [{number}] is missing target bookmark ref_{number}")
        elif bookmark.get("block") != refs[number]:
            errors.append(f"bookmark ref_{number} is not placed on reference [{number}]")

        expected_anchor = f"ref_{number}"
        matching_links = [link for link in linked_by_number.get(number, []) if link.get("anchor") == expected_anchor]
        if not matching_links:
            errors.append(f"body citation [{number}] is not an internal hyperlink to ref_{number}")

    for citation in unlinked:
        errors.append(f"body citation [{citation['number']}] at block {citation['block']} is plain text, not an internal hyperlink")

    for link in links:
        number = int(link["number"])
        expected_anchor = f"ref_{number}"
        if link.get("anchor") != expected_anchor:
            errors.append(f"body citation [{number}] links to {link.get('anchor') or '(empty)'} instead of {expected_anchor}")
        if not link.get("superscript"):
            errors.append(f"body citation [{number}] at block {link['block']} is linked but not formatted as superscript")

    for number in sorted(set(refs) - set(cited_numbers)):
        warnings.append(f"reference [{number}] has no body citation")

    return {
        "docx": str(path),
        "citations": cited_numbers,
        "referenceEntries": refs,
        "referenceBookmarks": bookmarks,
        "hyperlinkedCitations": links,
        "unlinkedCitations": unlinked,
        "errors": errors,
        "warnings": warnings,
    }


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# DOCX Reference Hyperlink Check",
        "",
        f"- File: `{report['docx']}`",
        f"- Cited numbers: `{report['citations']}`",
        f"- Reference bookmarks: `{len(report['referenceBookmarks'])}`",
        f"- Hyperlinked citation runs: `{len(report['hyperlinkedCitations'])}`",
        f"- Plain-text citation runs: `{len(report['unlinkedCitations'])}`",
        f"- Superscript citation runs: `{sum(1 for item in report['hyperlinkedCitations'] if item.get('superscript'))}`",
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
    parser = argparse.ArgumentParser(description="Check whether DOCX numeric citations hyperlink to reference entries.")
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
