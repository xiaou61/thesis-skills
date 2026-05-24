#!/usr/bin/env python3
"""Check positioned use-case JSON for shape bounding-box overlaps."""

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
    for idx, actor in enumerate(as_list(diagram.get("actors"))):
        if not isinstance(actor, dict):
            continue
        aid = str(actor.get("id") or actor.get("name") or f"actor_{idx}")
        boxes.append(
            Box(
                aid,
                "actor",
                float(actor.get("x", 0.0)),
                float(actor.get("y", 0.0)),
                float(actor.get("width", 0.72)),
                float(actor.get("height", 1.25)),
            )
        )
    for idx, case in enumerate(as_list(diagram.get("useCases"))):
        if not isinstance(case, dict):
            continue
        cid = str(case.get("id") or case.get("name") or f"use_case_{idx}")
        boxes.append(
            Box(
                cid,
                "use_case",
                float(case.get("x", 0.0)),
                float(case.get("y", 0.0)),
                float(case.get("width", 1.65)),
                float(case.get("height", 0.48)),
            )
        )
    return boxes


def main() -> int:
    parser = argparse.ArgumentParser(description="Check positioned use-case JSON for overlaps.")
    parser.add_argument("input", help="Positioned use-case JSON.")
    parser.add_argument("--pad", type=float, default=0.03, help="Padding around boxes.")
    args = parser.parse_args()

    diagram = json.loads(Path(args.input).read_text(encoding="utf-8"))
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
    print(json.dumps({"boxes": len(boxes), "overlapPairs": len(overlaps), "largestOverlap": overlaps[0]["area"] if overlaps else 0, "overlaps": overlaps[:20]}, ensure_ascii=False, indent=2))
    return 1 if overlaps else 0


if __name__ == "__main__":
    raise SystemExit(main())
