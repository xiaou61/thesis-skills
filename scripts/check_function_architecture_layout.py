#!/usr/bin/env python3
"""Check positioned function architecture JSON for box overlaps and page bounds."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Box:
    id: str
    kind: str
    x: float
    y: float
    w: float
    h: float

    @property
    def left(self) -> float:
        return self.x - self.w / 2

    @property
    def right(self) -> float:
        return self.x + self.w / 2

    @property
    def bottom(self) -> float:
        return self.y - self.h / 2

    @property
    def top(self) -> float:
        return self.y + self.h / 2


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def overlap(a: Box, b: Box, pad: float) -> float:
    dx = min(a.right + pad, b.right + pad) - max(a.left - pad, b.left - pad)
    dy = min(a.top + pad, b.top + pad) - max(a.bottom - pad, b.bottom - pad)
    if dx <= 0 or dy <= 0:
        return 0.0
    return dx * dy


def build_boxes(diagram: dict[str, Any]) -> list[Box]:
    boxes: list[Box] = []
    for idx, node in enumerate(as_list(diagram.get("nodes"))):
        if not isinstance(node, dict):
            continue
        nid = str(node.get("id") or node.get("name") or f"node_{idx}")
        boxes.append(
            Box(
                id=nid,
                kind=str(node.get("kind") or "node"),
                x=float(node.get("x", 0.0)),
                y=float(node.get("y", 0.0)),
                w=float(node.get("width", 0.0)),
                h=float(node.get("height", 0.0)),
            )
        )
    return boxes


def out_of_bounds(box: Box, page_w: float, page_h: float, margin: float) -> bool:
    return box.left < margin or box.right > page_w - margin or box.bottom < margin or box.top > page_h - margin


def main() -> int:
    parser = argparse.ArgumentParser(description="Check positioned function architecture JSON.")
    parser.add_argument("input", help="Positioned function architecture JSON.")
    parser.add_argument("--pad", type=float, default=0.04, help="Padding around boxes for overlap checks.")
    parser.add_argument("--margin", type=float, default=0.04, help="Minimum page margin in inches.")
    args = parser.parse_args()

    diagram = json.loads(Path(args.input).read_text(encoding="utf-8"))
    layout = diagram.get("layout") if isinstance(diagram.get("layout"), dict) else {}
    page_w = float(layout.get("pageWidth", 0.0))
    page_h = float(layout.get("pageHeight", 0.0))
    boxes = build_boxes(diagram)

    overlaps = []
    for i, first in enumerate(boxes):
        for second in boxes[i + 1 :]:
            area = overlap(first, second, args.pad)
            if area > 0.001:
                overlaps.append(
                    {
                        "a": first.id,
                        "a_kind": first.kind,
                        "b": second.id,
                        "b_kind": second.kind,
                        "area": round(area, 4),
                    }
                )
    overlaps.sort(key=lambda item: item["area"], reverse=True)

    bounds = [
        {"id": box.id, "kind": box.kind, "left": round(box.left, 3), "right": round(box.right, 3), "bottom": round(box.bottom, 3), "top": round(box.top, 3)}
        for box in boxes
        if out_of_bounds(box, page_w, page_h, args.margin)
    ]

    result = {
        "boxes": len(boxes),
        "segments": len(as_list(diagram.get("segments"))),
        "overlapPairs": len(overlaps),
        "largestOverlap": overlaps[0]["area"] if overlaps else 0,
        "outOfBounds": len(bounds),
        "overlaps": overlaps[:20],
        "bounds": bounds[:20],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if overlaps or bounds else 0


if __name__ == "__main__":
    raise SystemExit(main())
