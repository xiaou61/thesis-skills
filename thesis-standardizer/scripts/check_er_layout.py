#!/usr/bin/env python3
"""Check positioned ER JSON for shape bounding-box overlaps."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ENTITY_W = 1.15
ENTITY_H = 0.55
ATTR_W = 1.18
ATTR_H = 0.46
REL_W = 0.95
REL_H = 0.58
LABEL_W = 0.28
LABEL_H = 0.18


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


def cardinality_label_position(
    entity_x: float,
    entity_y: float,
    relation_x: float,
    relation_y: float,
    side: float,
) -> tuple[float, float]:
    dx = relation_x - entity_x
    dy = relation_y - entity_y
    length = (dx * dx + dy * dy) ** 0.5
    if length < 0.001:
        return entity_x, entity_y
    ux = dx / length
    uy = dy / length
    px = -uy
    py = ux
    distance = min(max(length * 0.50, 0.72), max(0.10, length - 0.52))
    return entity_x + ux * distance + px * 0.18 * side, entity_y + uy * distance + py * 0.18 * side


def build_boxes(diagram: dict[str, Any]) -> list[Box]:
    boxes: list[Box] = []
    diagram_type = str(diagram.get("diagramType", "overview")).lower()
    if diagram_type in {"single", "single_entity", "entity"}:
        entity = diagram.get("entity") if isinstance(diagram.get("entity"), dict) else {}
        layout = diagram.get("layout") if isinstance(diagram.get("layout"), dict) else {}
        ex = float(layout.get("entityX", 3.0))
        ey = float(layout.get("entityY", 2.8))
        entity_id = str(entity.get("name", "entity"))
        boxes.append(Box(entity_id, "entity", ex, ey, 1.35, 0.48))
        for attr in as_list(entity.get("attributes")):
            if not isinstance(attr, dict):
                continue
            name = str(attr.get("name", "attribute"))
            dx = float(attr.get("dx", 0.0))
            dy = float(attr.get("dy", 0.0))
            boxes.append(Box(f"{entity_id}.{name}", "attribute", ex + dx, ey + dy, ATTR_W, ATTR_H))
        return boxes

    entity_positions: dict[str, tuple[float, float]] = {}
    for idx, entity in enumerate(as_list(diagram.get("entities"))):
        if not isinstance(entity, dict):
            continue
        eid = str(entity.get("id") or entity.get("name") or f"entity_{idx}")
        ex = float(entity.get("x", 0.0))
        ey = float(entity.get("y", 0.0))
        entity_positions[eid] = (ex, ey)
        boxes.append(Box(eid, "entity", ex, ey, ENTITY_W, ENTITY_H))
        for attr in as_list(entity.get("attributes")):
            if not isinstance(attr, dict):
                continue
            name = str(attr.get("name", "attribute"))
            dx = float(attr.get("dx", 0.0))
            dy = float(attr.get("dy", 0.0))
            boxes.append(Box(f"{eid}.{name}", "attribute", ex + dx, ey + dy, ATTR_W, ATTR_H))

    for idx, rel in enumerate(as_list(diagram.get("relationships"))):
        if not isinstance(rel, dict):
            continue
        name = str(rel.get("name") or f"relationship_{idx}")
        rx = float(rel.get("x", 0.0))
        ry = float(rel.get("y", 0.0))
        boxes.append(Box(f"rel:{name}:{idx}", "relationship", rx, ry, REL_W, REL_H))
        src = str(rel.get("from", ""))
        dst = str(rel.get("to", ""))
        if src in entity_positions and rel.get("fromCardinality"):
            sx, sy = entity_positions[src]
            if rel.get("fromLabelX") is not None and rel.get("fromLabelY") is not None:
                lx, ly = float(rel["fromLabelX"]), float(rel["fromLabelY"])
            else:
                lx, ly = cardinality_label_position(sx, sy, rx, ry, 1.0)
            boxes.append(Box(f"label:{name}:{idx}:from", "label", lx, ly, LABEL_W, LABEL_H))
        if dst in entity_positions and rel.get("toCardinality"):
            tx, ty = entity_positions[dst]
            if rel.get("toLabelX") is not None and rel.get("toLabelY") is not None:
                lx, ly = float(rel["toLabelX"]), float(rel["toLabelY"])
            else:
                lx, ly = cardinality_label_position(tx, ty, rx, ry, -1.0)
            boxes.append(Box(f"label:{name}:{idx}:to", "label", lx, ly, LABEL_W, LABEL_H))
    return boxes


def main() -> int:
    parser = argparse.ArgumentParser(description="Check positioned ER JSON for overlaps.")
    parser.add_argument("input", help="Positioned ER JSON.")
    parser.add_argument("--pad", type=float, default=0.02, help="Padding around boxes.")
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
