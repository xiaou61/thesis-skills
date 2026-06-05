#!/usr/bin/env python3
"""Check numeric citation closure between thesis body and references."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from docx_analysis import component_positions, load_blocks, split_before_references


CITATION_RE = re.compile(r"(?<!\d)\[([0-9,\-，、\s]+)\]")
REF_PREFIX_RE = re.compile(r"^\s*\[?([0-9]{1,3})\]?[\.、\s]")


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


def check_docx(path: Path, allow_uncited: bool) -> dict[str, object]:
    blocks = load_blocks(path)
    positions = component_positions(blocks)
    body_blocks, reference_blocks = split_before_references(blocks)
    body_text = "\n".join(block.text for block in body_blocks if block.text)
    cited_numbers = sorted(set(number for match in CITATION_RE.findall(body_text) for number in expand_citation_numbers(match)))

    reference_numbers: list[int] = []
    reference_entries: list[dict[str, object]] = []
    for block in reference_blocks:
        text = block.text.strip()
        if not text:
            continue
        match = REF_PREFIX_RE.match(text)
        if not match:
            continue
        number = int(match.group(1))
        reference_numbers.append(number)
        reference_entries.append({"number": number, "block": block.index, "text": text[:160]})

    errors: list[str] = []
    warnings: list[str] = []
    if "references" not in positions:
        errors.append("missing references section")
    if cited_numbers and not reference_numbers:
        errors.append("body has numeric citations but no numbered reference entries were detected")

    cited_set = set(cited_numbers)
    ref_set = set(reference_numbers)
    for number in sorted(cited_set - ref_set):
        errors.append(f"citation [{number}] has no matching reference entry")
    if not allow_uncited:
        for number in sorted(ref_set - cited_set):
            warnings.append(f"reference [{number}] is not cited in the body")

    if reference_numbers:
        expected = list(range(1, max(reference_numbers) + 1))
        missing = sorted(set(expected) - ref_set)
        duplicates = sorted(number for number in set(reference_numbers) if reference_numbers.count(number) > 1)
        if missing:
            errors.append(f"reference numbering is not continuous; missing {missing}")
        if duplicates:
            errors.append(f"duplicate reference numbers: {duplicates}")

    return {
        "docx": str(path),
        "citations": cited_numbers,
        "references": reference_entries,
        "errors": errors,
        "warnings": warnings,
    }


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# DOCX Citation Closure Check",
        "",
        f"- File: `{report['docx']}`",
        f"- Cited numbers: `{report['citations']}`",
        f"- Reference entries: `{len(report['references'])}`",
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
    parser = argparse.ArgumentParser(description="Check numeric citation closure in a thesis DOCX.")
    parser.add_argument("docx", help="DOCX file.")
    parser.add_argument("--allow-uncited-references", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", help="Optional report output path.")
    args = parser.parse_args()

    report = check_docx(Path(args.docx).resolve(), allow_uncited=args.allow_uncited_references)
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n" if args.json else render_markdown(report)
    if args.out:
        Path(args.out).resolve().write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
