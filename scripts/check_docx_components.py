#!/usr/bin/env python3
"""Check thesis DOCX component completeness and ordering."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from docx_analysis import component_positions, load_blocks


DEFAULT_REQUIRED = [
    "zh_abstract",
    "en_abstract",
    "toc",
    "chapter_1",
    "chapter_2",
    "chapter_3",
    "chapter_4",
    "chapter_5",
    "chapter_6",
    "references",
]

DEFAULT_ORDER = [
    "zh_abstract",
    "en_abstract",
    "toc",
    "chapter_1",
    "chapter_2",
    "chapter_3",
    "chapter_4",
    "chapter_5",
    "chapter_6",
    "references",
    "acknowledgement",
    "appendix",
]

LABELS = {
    "zh_abstract": "中文摘要",
    "en_abstract": "英文摘要",
    "toc": "目录",
    "references": "参考文献",
    "acknowledgement": "致谢/谢辞",
    "appendix": "附录",
    **{f"chapter_{index}": f"第{index}章" for index in range(1, 11)},
}


def parse_csv(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def check_components(path: Path, required: list[str], order: list[str]) -> dict[str, object]:
    blocks = load_blocks(path)
    positions = component_positions(blocks)
    errors: list[str] = []
    warnings: list[str] = []

    for key in required:
        if key not in positions:
            errors.append(f"missing required component: {LABELS.get(key, key)}")

    present_in_order = [(key, positions[key]) for key in order if key in positions]
    for (left_key, left_pos), (right_key, right_pos) in zip(present_in_order, present_in_order[1:]):
        if left_pos > right_pos:
            errors.append(
                f"component order is wrong: {LABELS.get(left_key, left_key)} appears after {LABELS.get(right_key, right_key)}"
            )

    if "toc" in required and "toc" in positions:
        toc_block = next((block for block in blocks if block.index == positions["toc"]), None)
        if toc_block is not None and not toc_block.has_toc_field:
            warnings.append("TOC heading/text exists but no Word TOC field was detected near the component")

    return {
        "docx": str(path),
        "positions": positions,
        "required": required,
        "order": order,
        "errors": errors,
        "warnings": warnings,
    }


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# DOCX Component Check",
        "",
        f"- File: `{report['docx']}`",
        f"- Errors: `{len(report['errors'])}`",
        f"- Warnings: `{len(report['warnings'])}`",
        "",
        "| Component | Position |",
        "| --- | ---: |",
    ]
    positions = report["positions"]
    for key in report["order"]:
        label = LABELS.get(key, key)
        position = positions.get(key, "")
        lines.append(f"| {label} | {position} |")
    if report["errors"]:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {item}" for item in report["errors"])
    if report["warnings"]:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {item}" for item in report["warnings"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check thesis DOCX component completeness and order.")
    parser.add_argument("docx", help="DOCX file.")
    parser.add_argument("--required", default=",".join(DEFAULT_REQUIRED), help="Comma-separated required component ids.")
    parser.add_argument("--order", default=",".join(DEFAULT_ORDER), help="Comma-separated component order ids.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", help="Optional report output path.")
    args = parser.parse_args()

    report = check_components(Path(args.docx).resolve(), parse_csv(args.required), parse_csv(args.order))
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n" if args.json else render_markdown(report)
    if args.out:
        Path(args.out).resolve().write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
