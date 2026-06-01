#!/usr/bin/env python3
"""Check thesis DOCX content quality gates such as length and structure."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def paragraph_text(paragraph: ET.Element) -> str:
    return "".join(node.text or "" for node in paragraph.findall(".//w:t", NS)).strip()


def paragraph_style_id(paragraph: ET.Element) -> str:
    node = paragraph.find("w:pPr/w:pStyle", NS)
    return node.get(W + "val", "") if node is not None else ""


def infer_heading_level(style: str, text: str) -> int | None:
    lowered = style.lower()
    if style in {"2", "76", "Heading1"} or lowered == "heading1":
        return 1
    if style in {"77", "Heading2"} or lowered == "heading2" or re.match(r"^[0-9]+\.[0-9]+[\s\u3000]", text):
        return 2
    if style in {"4", "Heading3"} or lowered == "heading3" or re.match(r"^[0-9]+\.[0-9]+\.[0-9]+[\s\u3000]", text):
        return 3
    if re.match(r"^第[0-9一二三四五六七八九十]+章[\s\u3000]", text):
        return 1
    return None


def content_units(text: str) -> dict[str, int]:
    cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
    latin_number_tokens = len(re.findall(r"[A-Za-z0-9]+", text))
    return {
        "cjk_chars": cjk,
        "latin_number_tokens": latin_number_tokens,
        "content_units": cjk + latin_number_tokens,
    }


def chapter_key(text: str) -> str | None:
    match = re.match(r"^第([1-6一二三四五六])章", text)
    if not match:
        return None
    raw = match.group(1)
    mapping = {"一": "1", "二": "2", "三": "3", "四": "4", "五": "5", "六": "6"}
    return mapping.get(raw, raw)


def check_docx(path: Path) -> dict[str, object]:
    with zipfile.ZipFile(path) as archive:
        document = ET.fromstring(archive.read("word/document.xml"))

    paragraphs: list[dict[str, object]] = []
    headings: list[dict[str, object]] = []
    current_chapter: str | None = None
    chapter_text: dict[str, list[str]] = {str(index): [] for index in range(1, 7)}

    for paragraph in document.findall(".//w:p", NS):
        text = paragraph_text(paragraph)
        if not text:
            continue
        style = paragraph_style_id(paragraph)
        level = infer_heading_level(style, text)
        if level is not None:
            headings.append({"level": level, "style": style, "text": text[:120]})
            if level == 1:
                key = chapter_key(text)
                if key is not None:
                    current_chapter = key
        else:
            if current_chapter is not None:
                chapter_text[current_chapter].append(text)
        paragraphs.append({"text": text, "style": style, "level": level})

    all_text = "\n".join(item["text"] for item in paragraphs)
    heading_counts = Counter(item["level"] for item in headings)
    chapter_units = {
        key: content_units("\n".join(values)) for key, values in chapter_text.items()
    }

    tables = len(document.findall(".//w:tbl", NS))
    figures = len([item for item in paragraphs if str(item["text"]).startswith("图")])
    table_captions = len([item for item in paragraphs if str(item["text"]).startswith("表") or str(item["text"]).startswith("续表")])
    screenshot_placeholders = len([item for item in paragraphs if "待补真实程序截图" in str(item["text"])])

    return {
        "docx": str(path),
        "paragraphs": len(paragraphs),
        "headings": {str(key): heading_counts[key] for key in sorted(key for key in heading_counts if key is not None)},
        "totals": content_units(all_text),
        "chapterUnits": chapter_units,
        "tables": tables,
        "tableCaptions": table_captions,
        "figureCaptions": figures,
        "screenshotPlaceholders": screenshot_placeholders,
        "sampleHeadings": headings[:40],
    }


def render_markdown(report: dict[str, object], errors: list[str], warnings: list[str]) -> str:
    totals = report["totals"]
    lines = [
        "# DOCX Thesis Quality Check",
        "",
        f"- File: `{report['docx']}`",
        f"- Content units: `{totals['content_units']}`",
        f"- CJK chars: `{totals['cjk_chars']}`",
        f"- Latin/number tokens: `{totals['latin_number_tokens']}`",
        f"- Tables: `{report['tables']}`",
        f"- Table captions: `{report['tableCaptions']}`",
        f"- Figure captions: `{report['figureCaptions']}`",
        f"- Screenshot placeholders: `{report['screenshotPlaceholders']}`",
        f"- Errors: `{len(errors)}`",
        f"- Warnings: `{len(warnings)}`",
        "",
        "| Chapter | Content units | CJK chars | Latin/number tokens |",
        "| --- | ---: | ---: | ---: |",
    ]
    for chapter, units in report["chapterUnits"].items():
        lines.append(f"| 第{chapter}章 | {units['content_units']} | {units['cjk_chars']} | {units['latin_number_tokens']} |")
    if errors:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in errors)
    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in warnings)
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check thesis DOCX content quality.")
    parser.add_argument("docx", help="DOCX file.")
    parser.add_argument("--min-content-units", type=int, default=12000)
    parser.add_argument("--min-cjk-chars", type=int, default=10000)
    parser.add_argument("--min-figures", type=int, default=8)
    parser.add_argument("--min-tables", type=int, default=6)
    parser.add_argument("--min-chapter-units", type=int, default=800)
    parser.add_argument("--require-chapters", default="1,2,3,4,5,6")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = check_docx(Path(args.docx).resolve())
    totals = report["totals"]
    errors: list[str] = []
    warnings: list[str] = []

    if totals["content_units"] < args.min_content_units:
        errors.append(f"content units {totals['content_units']} below minimum {args.min_content_units}")
    if totals["cjk_chars"] < args.min_cjk_chars:
        errors.append(f"CJK chars {totals['cjk_chars']} below minimum {args.min_cjk_chars}")
    if int(report["figureCaptions"]) < args.min_figures:
        errors.append(f"figure captions {report['figureCaptions']} below minimum {args.min_figures}")
    if int(report["tables"]) < args.min_tables:
        errors.append(f"tables {report['tables']} below minimum {args.min_tables}")

    required_chapters = [item.strip() for item in args.require_chapters.split(",") if item.strip()]
    for chapter in required_chapters:
        units = report["chapterUnits"].get(chapter)
        if not units:
            errors.append(f"missing chapter {chapter}")
            continue
        if units["content_units"] < args.min_chapter_units:
            warnings.append(f"chapter {chapter} content units {units['content_units']} below suggested minimum {args.min_chapter_units}")

    if args.json:
        payload = {**report, "errors": errors, "warnings": warnings}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(report, errors, warnings))

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
