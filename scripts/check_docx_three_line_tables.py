#!/usr/bin/env python3
"""Check DOCX tables for thesis-style three-line table borders."""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from dataclasses import dataclass, asdict
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


@dataclass
class TableFinding:
    table: int
    status: str
    message: str


def attr(element: ET.Element | None, name: str, default: str = "") -> str:
    if element is None:
        return default
    return element.attrib.get(W + name, default)


def border_val(parent: ET.Element | None, edge: str) -> str:
    if parent is None:
        return ""
    edge_element = parent.find(f"w:{edge}", NS)
    return attr(edge_element, "val")


def is_visible_border(parent: ET.Element | None, edge: str) -> bool:
    value = border_val(parent, edge)
    return value not in {"", "none", "nil"}


def cell_borders(cell: ET.Element) -> ET.Element | None:
    tc_pr = cell.find("w:tcPr", NS)
    return None if tc_pr is None else tc_pr.find("w:tcBorders", NS)


def table_borders(table: ET.Element) -> ET.Element | None:
    tbl_pr = table.find("w:tblPr", NS)
    return None if tbl_pr is None else tbl_pr.find("w:tblBorders", NS)


def table_has_grid_style(table: ET.Element) -> bool:
    tbl_pr = table.find("w:tblPr", NS)
    if tbl_pr is None:
        return False
    style = tbl_pr.find("w:tblStyle", NS)
    return attr(style, "val").lower() == "tablegrid"


def row_cells(row: ET.Element) -> list[ET.Element]:
    return row.findall("w:tc", NS)


def check_table(table: ET.Element, index: int) -> list[TableFinding]:
    findings: list[TableFinding] = []
    rows = table.findall("w:tr", NS)
    if not rows:
        return [TableFinding(index, "warn", "table has no rows")]

    if table_has_grid_style(table):
        findings.append(TableFinding(index, "error", "uses Word TableGrid style"))

    tbl_borders = table_borders(table)
    for edge in ("left", "right", "insideH", "insideV"):
        if is_visible_border(tbl_borders, edge):
            findings.append(TableFinding(index, "error", f"table-level {edge} border is visible"))

    header_cells = row_cells(rows[0])
    if not header_cells:
        findings.append(TableFinding(index, "error", "header row has no cells"))
    for cell_index, cell in enumerate(header_cells, start=1):
        borders = cell_borders(cell)
        if not is_visible_border(borders, "top"):
            findings.append(TableFinding(index, "error", f"header cell {cell_index} is missing top border"))
        if not is_visible_border(borders, "bottom"):
            findings.append(TableFinding(index, "error", f"header cell {cell_index} is missing header-bottom border"))
        for edge in ("left", "right"):
            if is_visible_border(borders, edge):
                findings.append(TableFinding(index, "error", f"header cell {cell_index} has visible {edge} border"))

    last_cells = row_cells(rows[-1])
    for cell_index, cell in enumerate(last_cells, start=1):
        borders = cell_borders(cell)
        if not is_visible_border(borders, "bottom"):
            findings.append(TableFinding(index, "error", f"last-row cell {cell_index} is missing bottom border"))
        for edge in ("left", "right"):
            if is_visible_border(borders, edge):
                findings.append(TableFinding(index, "error", f"last-row cell {cell_index} has visible {edge} border"))

    for row_index, row in enumerate(rows[1:-1], start=2):
        for cell_index, cell in enumerate(row_cells(row), start=1):
            borders = cell_borders(cell)
            for edge in ("top", "bottom", "left", "right"):
                if is_visible_border(borders, edge):
                    findings.append(TableFinding(index, "error", f"body cell r{row_index}c{cell_index} has visible {edge} border"))

    if not findings:
        findings.append(TableFinding(index, "ok", "three-line table borders detected"))
    return findings


def check_docx(path: Path) -> tuple[list[TableFinding], int]:
    if path.suffix.lower() != ".docx":
        raise ValueError(f"input must be a .docx file: {path}")
    if not path.exists():
        raise FileNotFoundError(path)
    if not zipfile.is_zipfile(path):
        raise ValueError(f"not a readable OOXML/ZIP package: {path}")

    with zipfile.ZipFile(path) as archive:
        document_xml = archive.read("word/document.xml")
    root = ET.fromstring(document_xml)
    tables = root.findall(".//w:tbl", NS)
    findings: list[TableFinding] = []
    for index, table in enumerate(tables, start=1):
        findings.extend(check_table(table, index))
    return findings, len(tables)


def render_markdown(path: Path, findings: list[TableFinding], table_count: int) -> str:
    errors = sum(1 for item in findings if item.status == "error")
    warnings = sum(1 for item in findings if item.status == "warn")
    lines = [
        "# DOCX Three-Line Table Check",
        "",
        f"- File: `{path}`",
        f"- Tables: `{table_count}`",
        f"- Errors: `{errors}`",
        f"- Warnings: `{warnings}`",
        "",
        "| Table | Status | Message |",
        "| --- | --- | --- |",
    ]
    for item in findings:
        lines.append(f"| {item.table} | {item.status} | {item.message} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check DOCX tables for true three-line borders.")
    parser.add_argument("docx", help="DOCX file to inspect.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    parser.add_argument("--out", help="Optional report output path.")
    args = parser.parse_args()

    path = Path(args.docx).resolve()
    findings, table_count = check_docx(path)
    errors = sum(1 for item in findings if item.status == "error")
    warnings = sum(1 for item in findings if item.status == "warn")

    if args.json:
        report = json.dumps(
            {
                "file": str(path),
                "tables": table_count,
                "errors": errors,
                "warnings": warnings,
                "findings": [asdict(item) for item in findings],
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n"
    else:
        report = render_markdown(path, findings, table_count)

    if args.out:
        Path(args.out).resolve().write_text(report, encoding="utf-8")
    else:
        sys.stdout.write(report)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
