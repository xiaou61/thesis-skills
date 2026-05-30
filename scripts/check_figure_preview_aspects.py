#!/usr/bin/env python3
"""Check figure preview aspect ratios before embedding them into a thesis DOCX."""

from __future__ import annotations

import argparse
import json
import struct
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class FigureAspectFinding:
    caption: str
    preview: str
    width_px: int
    height_px: int
    aspect: float
    fitted_width_cm: float
    fitted_height_cm: float
    status: str
    message: str


def parse_cm(value: str) -> float:
    text = value.strip().lower()
    if text.endswith("cm"):
        return float(text[:-2])
    if text.endswith("in"):
        return float(text[:-2]) * 2.54
    return float(text)


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"not a PNG preview with an IHDR header: {path}")
    width, height = struct.unpack(">II", header[16:24])
    if width <= 0 or height <= 0:
        raise ValueError(f"invalid PNG dimensions for preview: {path}")
    return width, height


def fit_size(width_px: int, height_px: int, max_width_cm: float, max_height_cm: float) -> tuple[float, float]:
    aspect = width_px / height_px
    width = max_width_cm
    height = width / aspect
    if height > max_height_cm:
        height = max_height_cm
        width = height * aspect
    return width, height


def load_figure_map(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("figure map must be a JSON list")
    return [item for item in payload if isinstance(item, dict)]


def check_item(
    item: dict[str, Any],
    base_dir: Path,
    max_width_cm: float,
    max_height_cm: float,
    min_aspect: float,
    max_aspect: float,
    min_display_width_cm: float,
    min_display_height_cm: float,
) -> FigureAspectFinding:
    caption = str(item.get("caption") or item.get("title") or "未命名图")
    preview_raw = str(item.get("preview") or item.get("export_file") or "")
    if not preview_raw:
        return FigureAspectFinding(caption, "", 0, 0, 0.0, 0.0, 0.0, "error", "missing preview path")
    preview = Path(preview_raw)
    if not preview.is_absolute():
        preview = base_dir / preview
    if not preview.exists():
        return FigureAspectFinding(caption, str(preview), 0, 0, 0.0, 0.0, 0.0, "error", "preview file not found")

    width_px, height_px = png_dimensions(preview)
    aspect = width_px / height_px
    fitted_width, fitted_height = fit_size(width_px, height_px, max_width_cm, max_height_cm)

    messages: list[str] = []
    if aspect > max_aspect:
        messages.append("preview is too wide/flat")
    if aspect < min_aspect:
        messages.append("preview is too tall/narrow")
    if fitted_height < min_display_height_cm:
        messages.append("fitted display height is too small")
    if fitted_width < min_display_width_cm:
        messages.append("fitted display width is too small")

    return FigureAspectFinding(
        caption=caption,
        preview=str(preview),
        width_px=width_px,
        height_px=height_px,
        aspect=round(aspect, 3),
        fitted_width_cm=round(fitted_width, 2),
        fitted_height_cm=round(fitted_height, 2),
        status="warn" if messages else "ok",
        message="; ".join(messages) if messages else "preview aspect is thesis-display friendly",
    )


def render_markdown(figure_map: Path, findings: list[FigureAspectFinding]) -> str:
    errors = sum(1 for item in findings if item.status == "error")
    warnings = sum(1 for item in findings if item.status == "warn")
    lines = [
        "# Figure Preview Aspect Check",
        "",
        f"- Figure map: `{figure_map}`",
        f"- Figures: `{len(findings)}`",
        f"- Errors: `{errors}`",
        f"- Warnings: `{warnings}`",
        "",
        "| Caption | Status | Aspect | Fitted size | Message |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for item in findings:
        lines.append(
            f"| {item.caption} | {item.status} | {item.aspect:.3f} | "
            f"{item.fitted_width_cm:.2f}cm x {item.fitted_height_cm:.2f}cm | {item.message} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check figure preview aspect ratios for thesis DOCX embedding.")
    parser.add_argument("figure_map", help="JSON list with caption and preview/export_file paths.")
    parser.add_argument("--max-width", default="14cm", help="Maximum Word display width used for aspect fitting.")
    parser.add_argument("--max-height", default="18cm", help="Maximum Word display height used for aspect fitting.")
    parser.add_argument("--min-aspect", type=float, default=0.33, help="Warn when preview width/height is below this ratio.")
    parser.add_argument("--max-aspect", type=float, default=5.0, help="Warn when preview width/height exceeds this ratio.")
    parser.add_argument("--min-display-width", default="5cm", help="Warn when fitted display width is below this value.")
    parser.add_argument("--min-display-height", default="3cm", help="Warn when fitted display height is below this value.")
    parser.add_argument("--fail-on-warning", action="store_true", help="Exit non-zero when warnings are present.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    parser.add_argument("--out", help="Optional report output path.")
    args = parser.parse_args()

    figure_map = Path(args.figure_map).resolve()
    base_dir = figure_map.parent
    max_width_cm = parse_cm(args.max_width)
    max_height_cm = parse_cm(args.max_height)
    min_display_width_cm = parse_cm(args.min_display_width)
    min_display_height_cm = parse_cm(args.min_display_height)

    findings: list[FigureAspectFinding] = []
    for item in load_figure_map(figure_map):
        try:
            findings.append(
                check_item(
                    item,
                    base_dir,
                    max_width_cm,
                    max_height_cm,
                    args.min_aspect,
                    args.max_aspect,
                    min_display_width_cm,
                    min_display_height_cm,
                )
            )
        except Exception as exc:
            caption = str(item.get("caption") or item.get("title") or "未命名图")
            preview = str(item.get("preview") or item.get("export_file") or "")
            findings.append(FigureAspectFinding(caption, preview, 0, 0, 0.0, 0.0, 0.0, "error", str(exc)))

    errors = sum(1 for item in findings if item.status == "error")
    warnings = sum(1 for item in findings if item.status == "warn")
    if args.json:
        report = json.dumps(
            {
                "figure_map": str(figure_map),
                "figures": len(findings),
                "errors": errors,
                "warnings": warnings,
                "findings": [asdict(item) for item in findings],
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n"
    else:
        report = render_markdown(figure_map, findings)

    if args.out:
        Path(args.out).resolve().write_text(report, encoding="utf-8")
    else:
        sys.stdout.write(report)

    if errors or (warnings and args.fail_on_warning):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
