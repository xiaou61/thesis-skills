#!/usr/bin/env python3
"""Compare generated thesis variants from variant-manifest.json files."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_ROOT = ROOT / "paper-context" / "thesis-variants"
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out_root", nargs="?", type=Path, default=DEFAULT_OUT_ROOT)
    parser.add_argument("--out", type=Path, help="Markdown comparison report path.")
    parser.add_argument("--json-out", type=Path, help="JSON comparison report path.")
    return parser.parse_args()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def text_from_element(element: ET.Element) -> str:
    return "".join(node.text or "" for node in element.findall(".//w:t", NS))


def paragraph_style_id(paragraph: ET.Element) -> str:
    style = paragraph.find("./w:pPr/w:pStyle", NS)
    return style.attrib.get(f"{{{NS['w']}}}val", "") if style is not None else ""


def analyze_docx(path: Path | None) -> dict:
    if not path or not path.exists():
        return {
            "exists": False,
            "paragraphs": 0,
            "cjk_chars": 0,
            "content_units": 0,
            "tables": 0,
            "images": 0,
            "headings": {},
        }
    with zipfile.ZipFile(path) as archive:
        document_xml = archive.read("word/document.xml")
        rel_names = archive.namelist()
    root = ET.fromstring(document_xml)
    paragraphs = root.findall(".//w:p", NS)
    texts = [text_from_element(paragraph) for paragraph in paragraphs]
    full_text = "\n".join(texts)
    headings: dict[str, int] = {}
    for paragraph in paragraphs:
        style = paragraph_style_id(paragraph)
        if style.lower().startswith("heading") or style.startswith("标题"):
            headings[style] = headings.get(style, 0) + 1
    return {
        "exists": True,
        "path": str(path),
        "paragraphs": len([text for text in texts if text.strip()]),
        "cjk_chars": len(re.findall(r"[\u4e00-\u9fff]", full_text)),
        "content_units": len(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]", full_text)),
        "tables": len(root.findall(".//w:tbl", NS)),
        "images": len([name for name in rel_names if name.startswith("word/media/")]),
        "headings": headings,
    }


def parse_gate(manifest: dict) -> dict:
    gate = manifest.get("commands", {}).get("gate") or {}
    report = Path(gate.get("report", "")) if gate.get("report") else None
    failed = []
    if report and report.exists():
        text = report.read_text(encoding="utf-8", errors="replace")
        match = re.search(r"Failed:\s+``([^`]+)``", text)
        if match:
            failed = [item.strip() for item in match.group(1).split(",") if item.strip()]
    return {
        "returncode": gate.get("returncode"),
        "report": str(report) if report else "",
        "failed": failed,
    }


def collect_variant(manifest_path: Path) -> dict:
    manifest = read_json(manifest_path)
    outputs = manifest.get("outputs", {})
    docx = Path(outputs["docx"]) if outputs.get("docx") else None
    workspace = Path(manifest["workspace"])
    figure_map = Path(outputs["figure_map"]) if outputs.get("figure_map") else workspace / "visio-ole-figure-map.json"
    figures = workspace / "figures"
    return {
        "id": manifest["variant"]["id"],
        "name": manifest["variant"]["name"],
        "focus": manifest["variant"]["focus"],
        "status": manifest.get("status", "unknown"),
        "workspace": str(workspace),
        "docx": analyze_docx(docx),
        "pdf_exists": Path(outputs.get("pdf", "")).exists() if outputs.get("pdf") else False,
        "figure_map_exists": figure_map.exists(),
        "png_count": len(list(figures.glob("*.png"))) if figures.exists() else 0,
        "vsdx_count": len(list(figures.glob("*.vsdx"))) if figures.exists() else 0,
        "gate": parse_gate(manifest),
    }


def markdown_report(items: list[dict]) -> str:
    lines = [
        "# Thesis Variant Comparison",
        "",
        "| Variant | Status | DOCX | PDF | CJK chars | Units | Tables | Images | PNG/VSDX | Gate |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for item in items:
        docx = item["docx"]
        gate = item["gate"]
        gate_text = "not run" if gate["returncode"] is None else ("pass" if gate["returncode"] == 0 else "fail")
        if gate["failed"]:
            gate_text += ": " + ", ".join(gate["failed"])
        lines.append(
            "| {name} | {status} | {docx_exists} | {pdf_exists} | {cjk} | {units} | {tables} | {images} | {png}/{vsdx} | {gate} |".format(
                name=item["name"],
                status=item["status"],
                docx_exists="yes" if docx["exists"] else "no",
                pdf_exists="yes" if item["pdf_exists"] else "no",
                cjk=docx["cjk_chars"],
                units=docx["content_units"],
                tables=docx["tables"],
                images=docx["images"],
                png=item["png_count"],
                vsdx=item["vsdx_count"],
                gate=gate_text,
            )
        )
    lines.extend(["", "## Variant Notes", ""])
    for item in items:
        lines.extend([
            f"### {item['name']}",
            "",
            f"- Focus: {item['focus']}",
            f"- Workspace: `{item['workspace']}`",
            f"- Figure map: {'present' if item['figure_map_exists'] else 'missing'}",
            "",
        ])
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    out_root = args.out_root.resolve()
    manifest_paths = sorted(out_root.glob("*/variant-manifest.json"))
    if not manifest_paths:
        raise SystemExit(f"No variant manifests found under {out_root}")
    items = [collect_variant(path) for path in manifest_paths]
    json_out = (args.json_out or out_root / "variant-comparison.json").resolve()
    md_out = (args.out or out_root / "variant-comparison.md").resolve()
    json_out.write_text(json.dumps({"variants": items}, ensure_ascii=False, indent=2), encoding="utf-8")
    md_out.write_text(markdown_report(items), encoding="utf-8")
    print(json.dumps({"markdown": str(md_out), "json": str(json_out), "variants": len(items)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
