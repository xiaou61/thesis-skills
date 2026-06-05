#!/usr/bin/env python3
"""Compare DOCX paragraph style usage against an extracted template profile."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

from docx_analysis import load_blocks, load_style_names


def load_profile(path: Path | None) -> dict:
    if path is None:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def template_style_counts(profile: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in profile.get("paragraph_usage", {}).get("style_counts", []):
        style_id = str(item.get("style_id", ""))
        if style_id:
            counts[style_id] = int(item.get("count", 0))
    return counts


def template_style_name_counts(profile: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in profile.get("paragraph_usage", {}).get("style_counts", []):
        name = str(item.get("style_name", "")).strip()
        if name:
            counts[name] = int(item.get("count", 0))
    return counts


def check_docx(docx: Path, profile_path: Path | None, min_known_style_ratio: float) -> dict[str, object]:
    profile = load_profile(profile_path)
    known_styles = set(template_style_counts(profile))
    known_style_names = set(template_style_name_counts(profile))
    blocks = load_blocks(docx)
    style_names = load_style_names(docx)
    style_counter = Counter(block.style_id for block in blocks if block.kind == "paragraph" and block.style_id)
    style_name_counter = Counter(style_names.get(block.style_id, block.style_id) for block in blocks if block.kind == "paragraph" and block.style_id)
    styled_count = sum(style_counter.values())
    known_count = sum(count for style, count in style_counter.items() if style in known_styles) if known_styles else 0
    known_name_count = (
        sum(count for name, count in style_name_counter.items() if name in known_style_names)
        if known_style_names
        else 0
    )
    known_ratio = (known_count / styled_count) if styled_count else 1.0
    known_name_ratio = (known_name_count / styled_count) if styled_count else 1.0

    errors: list[str] = []
    warnings: list[str] = []
    best_ratio = max(known_ratio, known_name_ratio)
    if known_styles and best_ratio < min_known_style_ratio:
        errors.append(
            f"known template style ratio {best_ratio:.2%} below minimum {min_known_style_ratio:.2%} "
            f"(styleId={known_ratio:.2%}, styleName={known_name_ratio:.2%})"
        )
    if not known_styles:
        warnings.append("template profile has no style_counts; style comparison is weak")

    unknown_styles = [
        {"style_id": style, "count": count}
        for style, count in style_counter.most_common()
        if style not in known_styles
    ]
    unknown_style_names = [
        {"style_name": name, "count": count}
        for name, count in style_name_counter.most_common()
        if name not in known_style_names
    ]

    return {
        "docx": str(docx),
        "templateProfile": str(profile_path) if profile_path else "",
        "styledParagraphs": styled_count,
        "knownTemplateStyleRatio": known_ratio,
        "knownTemplateStyleNameRatio": known_name_ratio,
        "topStyles": [
            {"style_id": style, "style_name": style_names.get(style, style), "count": count}
            for style, count in style_counter.most_common(20)
        ],
        "topStyleNames": [{"style_name": name, "count": count} for name, count in style_name_counter.most_common(20)],
        "unknownStyles": unknown_styles[:20],
        "unknownStyleNames": unknown_style_names[:20],
        "errors": errors,
        "warnings": warnings,
    }


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# DOCX Style Profile Check",
        "",
        f"- File: `{report['docx']}`",
        f"- Template profile: `{report['templateProfile']}`",
        f"- Styled paragraphs: `{report['styledParagraphs']}`",
        f"- Known template styleId ratio: `{report['knownTemplateStyleRatio']:.2%}`",
        f"- Known template styleName ratio: `{report['knownTemplateStyleNameRatio']:.2%}`",
        f"- Errors: `{len(report['errors'])}`",
        f"- Warnings: `{len(report['warnings'])}`",
        "",
        "| Style ID | Style name | Count |",
        "| --- | --- | ---: |",
    ]
    for item in report["topStyles"]:
        lines.append(f"| {item['style_id']} | {item['style_name']} | {item['count']} |")
    if report["unknownStyles"]:
        lines.extend(["", "## Unknown Style IDs", ""])
        for item in report["unknownStyles"]:
            lines.append(f"- `{item['style_id']}`: {item['count']}")
    if report["unknownStyleNames"]:
        lines.extend(["", "## Unknown Style Names", ""])
        for item in report["unknownStyleNames"]:
            lines.append(f"- `{item['style_name']}`: {item['count']}")
    if report["errors"]:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {item}" for item in report["errors"])
    if report["warnings"]:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {item}" for item in report["warnings"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check DOCX styles against an extracted template profile.")
    parser.add_argument("docx")
    parser.add_argument("--template-profile")
    parser.add_argument("--min-known-style-ratio", type=float, default=0.70)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out")
    args = parser.parse_args()

    report = check_docx(
        Path(args.docx).resolve(),
        Path(args.template_profile).resolve() if args.template_profile else None,
        args.min_known_style_ratio,
    )
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n" if args.json else render_markdown(report)
    if args.out:
        Path(args.out).resolve().write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
