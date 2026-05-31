#!/usr/bin/env python3
"""Check DOCX heading levels and style usage for thesis drafts."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def paragraph_text(paragraph: ET.Element) -> str:
    return "".join(node.text or "" for node in paragraph.findall(".//w:t", NS)).strip()


def style_id(paragraph: ET.Element) -> str:
    node = paragraph.find("w:pPr/w:pStyle", NS)
    return node.get(W + "val", "") if node is not None else ""


def infer_level(style: str, text: str) -> int | None:
    if style in {"2", "Heading1", "heading 1", "76"} or style.lower() == "heading1":
        return 1
    if style == "77" or re.match(r"^[0-9]+\.[0-9]+[\s\u3000]", text):
        return 2
    if style == "4" or re.match(r"^[0-9]+\.[0-9]+\.[0-9]+[\s\u3000]", text):
        return 3
    if re.match(r"^第[0-9一二三四五六七八九十]+章[\s\u3000]", text):
        return 1
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Check DOCX heading levels.")
    parser.add_argument("docx", help="DOCX file.")
    parser.add_argument("--min-level2", type=int, default=1)
    parser.add_argument("--min-level3", type=int, default=0)
    args = parser.parse_args()

    path = Path(args.docx)
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))

    headings: list[dict[str, object]] = []
    style_counts: Counter[str] = Counter()
    level_counts: Counter[int] = Counter()
    for paragraph in root.findall(".//w:p", NS):
        text = paragraph_text(paragraph)
        if not text:
            continue
        style = style_id(paragraph)
        if style:
            style_counts[style] += 1
        level = infer_level(style, text)
        if level is not None:
            level_counts[level] += 1
            headings.append({"level": level, "style": style, "text": text[:120]})

    result = {
        "docx": str(path),
        "headingCounts": {str(key): level_counts[key] for key in sorted(level_counts)},
        "styleCounts": dict(style_counts.most_common(12)),
        "sampleHeadings": headings[:40],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if level_counts[2] < args.min_level2 or level_counts[3] < args.min_level3:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
