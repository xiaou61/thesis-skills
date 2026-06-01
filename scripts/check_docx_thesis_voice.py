#!/usr/bin/env python3
"""Check whether thesis DOCX prose leaks workflow/meta wording."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


FORBIDDEN_PATTERNS: list[tuple[str, str]] = [
    (r"根据.*(源码|代码|README|PRD|现有工程|已有工程|当前材料|当前项目|用户提供)", "source-process narration"),
    (r"(通过|经过)分析.*(源码|代码|项目|工程|材料)", "analysis-process narration"),
    (r"当前材料|当前可读|当前只提供|可读取项目|用户提供", "draft-material boundary leaked into thesis"),
    (r"证据|源码静态|代码证据|证据状态|待补证据", "evidence/audit wording leaked into thesis"),
    (r"不编造|避免过度承诺|不能直接证明", "assistant integrity disclaimer leaked into thesis"),
    (r"(?<![A-Za-z])AI(?![A-Za-z])|人工智能生成|生成图片替代", "AI workflow wording leaked into thesis"),
    (r"待补|占位|pending_user_screenshot|needs_user_screenshot", "placeholder wording leaked into thesis"),
    (r"README|PRD|init\.sql|pom\.xml|application\.yml", "source-file name leaked into thesis prose"),
    (r"D:\\|C:\\|/Users/|/home/", "local filesystem path leaked into thesis prose"),
]


def paragraph_text(paragraph: ET.Element) -> str:
    return "".join(node.text or "" for node in paragraph.findall(".//w:t", NS)).strip()


def load_paragraphs(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        document = ET.fromstring(archive.read("word/document.xml"))
    return [
        text
        for paragraph in document.findall(".//w:p", NS)
        if (text := paragraph_text(paragraph))
    ]


def check_docx(path: Path) -> dict[str, object]:
    paragraphs = load_paragraphs(path)
    issues: list[dict[str, object]] = []
    for index, text in enumerate(paragraphs, start=1):
        for pattern, reason in FORBIDDEN_PATTERNS:
            if re.search(pattern, text, flags=re.IGNORECASE):
                issues.append({
                    "paragraph": index,
                    "pattern": pattern,
                    "reason": reason,
                    "text": text[:220],
                })
                break
    return {
        "docx": str(path),
        "paragraphs": len(paragraphs),
        "issues": issues,
    }


def render_markdown(report: dict[str, object]) -> str:
    issues = report["issues"]
    lines = [
        "# DOCX Thesis Voice Check",
        "",
        f"- File: `{report['docx']}`",
        f"- Paragraphs: `{report['paragraphs']}`",
        f"- Issues: `{len(issues)}`",
    ]
    if issues:
        lines.extend([
            "",
            "| Paragraph | Reason | Text |",
            "| ---: | --- | --- |",
        ])
        for issue in issues:
            text = str(issue["text"]).replace("|", "\\|")
            lines.append(f"| {issue['paragraph']} | {issue['reason']} | {text} |")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check thesis prose for workflow/meta wording.")
    parser.add_argument("docx", help="DOCX file.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = check_docx(Path(args.docx).resolve())
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(report))
    return 1 if report["issues"] else 0


if __name__ == "__main__":
    sys.exit(main())
