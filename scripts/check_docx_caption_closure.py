#!/usr/bin/env python3
"""Check figure/table caption numbering, placement, and body references."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import sys

from docx_analysis import DocxBlock, caption_id, caption_reference_patterns, load_blocks, split_before_references


def is_caption_block(block: DocxBlock) -> bool:
    return caption_id(block.text) is not None


def body_blocks_only(blocks: list[DocxBlock]) -> list[DocxBlock]:
    return [block for block in blocks if block.kind == "paragraph" and block.text and not is_caption_block(block)]


def body_text_before(blocks: list[DocxBlock], caption_index: int) -> str:
    return "\n".join(block.text for block in body_blocks_only(blocks) if block.index < caption_index)


def object_near_before(blocks: list[DocxBlock], caption: DocxBlock, max_scan: int = 4) -> bool:
    scanned = 0
    for block in reversed([item for item in blocks if item.index < caption.index]):
        if scanned >= max_scan:
            break
        scanned += 1
        if block.kind == "table" or block.has_drawing or block.has_visio_ole:
            return True
        if block.text.strip() and caption.text.startswith("图"):
            break
    return False


def table_near_after(blocks: list[DocxBlock], caption: DocxBlock, max_scan: int = 4) -> bool:
    scanned = 0
    for block in [item for item in blocks if item.index > caption.index]:
        if scanned >= max_scan:
            break
        scanned += 1
        if block.kind == "table":
            return True
        if block.text.strip() and not block.text.startswith("续表"):
            break
    return False


def check_number_sequence(captions: list[tuple[str, str, int, str]]) -> list[str]:
    errors: list[str] = []
    by_kind_chapter: dict[tuple[str, str], list[tuple[int, int, str]]] = defaultdict(list)
    for kind, number, index, text in captions:
        if kind == "续表":
            continue
        match = re.match(r"^([0-9一二三四五六七八九十]+)-([0-9]+)$", number)
        if not match:
            errors.append(f"caption number has unsupported format at block {index}: {text}")
            continue
        chapter, seq = match.groups()
        by_kind_chapter[(kind, chapter)].append((int(seq), index, text))

    for (kind, chapter), items in sorted(by_kind_chapter.items()):
        seen: set[int] = set()
        expected = 1
        for seq, index, text in sorted(items):
            if seq in seen:
                errors.append(f"duplicate {kind}{chapter}-{seq} at block {index}: {text}")
            seen.add(seq)
            if seq != expected:
                errors.append(f"{kind}{chapter}-{seq} is not continuous; expected {kind}{chapter}-{expected}")
                expected = seq
            expected += 1
    return errors


def check_docx(path: Path, require_references: bool, max_scan: int) -> dict[str, object]:
    blocks = load_blocks(path)
    body_blocks, _ = split_before_references(blocks)
    all_text = "\n".join(block.text for block in body_blocks_only(body_blocks))
    findings: list[dict[str, object]] = []
    caption_tuples: list[tuple[str, str, int, str]] = []
    errors: list[str] = []
    warnings: list[str] = []

    for block in body_blocks:
        parsed = caption_id(block.text)
        if parsed is None:
            continue
        kind, number = parsed
        caption_tuples.append((kind, number, block.index, block.text))

        if kind == "图":
            if not object_near_before(body_blocks, block, max_scan=max_scan):
                errors.append(f"figure caption has no nearby object before it at block {block.index}: {block.text}")
        elif kind == "表":
            if not table_near_after(body_blocks, block, max_scan=max_scan):
                errors.append(f"table caption has no nearby table after it at block {block.index}: {block.text}")

        reference_found = False
        if require_references:
            preceding = body_text_before(body_blocks, block.index)
            reference_found = any(pattern.search(preceding) for pattern in caption_reference_patterns(kind, number))
            if not reference_found and kind != "续表":
                errors.append(f"caption is not referenced before object: {kind}{number} at block {block.index}")

        findings.append(
            {
                "block": block.index,
                "kind": kind,
                "number": number,
                "text": block.text,
                "referencedBefore": reference_found,
            }
        )

    errors.extend(check_number_sequence(caption_tuples))

    body_mentions = sorted(set(re.findall(r"([图表]\s*[0-9一二三四五六七八九十]+[-.][0-9]+)", all_text)))
    caption_numbers = {
        f"{kind}{number}".replace("-", "")
        for kind, number, _, _ in caption_tuples
        if kind in {"图", "表"}
    }
    for mention in body_mentions:
        normalized = re.sub(r"\s+", "", mention).replace(".", "-")
        key = normalized.replace("-", "")
        if key not in caption_numbers:
            warnings.append(f"body mentions {mention}, but no matching caption was found")

    return {
        "docx": str(path),
        "captions": len(findings),
        "errors": errors,
        "warnings": warnings,
        "findings": findings,
    }


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# DOCX Caption Closure Check",
        "",
        f"- File: `{report['docx']}`",
        f"- Captions: `{report['captions']}`",
        f"- Errors: `{len(report['errors'])}`",
        f"- Warnings: `{len(report['warnings'])}`",
        "",
        "| Block | Kind | Number | Referenced before | Caption |",
        "| ---: | --- | --- | --- | --- |",
    ]
    for item in report["findings"]:
        lines.append(
            f"| {item['block']} | {item['kind']} | {item['number']} | {item['referencedBefore']} | {item['text'][:80]} |"
        )
    if report["errors"]:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {item}" for item in report["errors"])
    if report["warnings"]:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {item}" for item in report["warnings"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check thesis DOCX figure/table caption closure.")
    parser.add_argument("docx", help="DOCX file.")
    parser.add_argument("--no-require-body-reference", action="store_true")
    parser.add_argument("--max-scan", type=int, default=4)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", help="Optional report output path.")
    args = parser.parse_args()

    report = check_docx(
        Path(args.docx).resolve(),
        require_references=not args.no_require_body_reference,
        max_scan=args.max_scan,
    )
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n" if args.json else render_markdown(report)
    if args.out:
        Path(args.out).resolve().write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
