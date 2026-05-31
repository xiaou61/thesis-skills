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

    def inflated(self, pad: float) -> "Box":
        return Box(self.id, self.kind, self.x, self.y, self.w + pad * 2, self.h + pad * 2)


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


def boundary_point(source: Box, target: Box) -> tuple[float, float]:
    dx = target.x - source.x
    dy = target.y - source.y
    if abs(dx) < 0.001 and abs(dy) < 0.001:
        return source.x, source.y
    scale_x = (source.w / 2) / abs(dx) if abs(dx) > 0.001 else float("inf")
    scale_y = (source.h / 2) / abs(dy) if abs(dy) > 0.001 else float("inf")
    scale = min(scale_x, scale_y)
    return source.x + dx * scale, source.y + dy * scale


def point_in_box(point: tuple[float, float], box: Box, eps: float = 0.001) -> bool:
    x, y = point
    return box.left + eps < x < box.right - eps and box.bottom + eps < y < box.top - eps


def orientation(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def on_segment(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float], eps: float = 0.001) -> bool:
    return (
        min(a[0], c[0]) - eps <= b[0] <= max(a[0], c[0]) + eps
        and min(a[1], c[1]) - eps <= b[1] <= max(a[1], c[1]) + eps
        and abs(orientation(a, b, c)) <= eps
    )


def segments_intersect(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
    d: tuple[float, float],
    eps: float = 0.001,
) -> bool:
    o1 = orientation(a, b, c)
    o2 = orientation(a, b, d)
    o3 = orientation(c, d, a)
    o4 = orientation(c, d, b)
    if o1 * o2 < -eps and o3 * o4 < -eps:
        return True
    return (
        on_segment(a, c, b, eps)
        or on_segment(a, d, b, eps)
        or on_segment(c, a, d, eps)
        or on_segment(c, b, d, eps)
    )


def segment_intersects_box(a: tuple[float, float], b: tuple[float, float], box: Box) -> bool:
    if point_in_box(a, box) or point_in_box(b, box):
        return True
    corners = [
        (box.left, box.bottom),
        (box.right, box.bottom),
        (box.right, box.top),
        (box.left, box.top),
    ]
    sides = list(zip(corners, corners[1:] + corners[:1]))
    return any(segments_intersect(a, b, c, d) for c, d in sides)


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


def build_segments(diagram: dict[str, Any], boxes: list[Box]) -> list[dict[str, Any]]:
    boxes_by_id = {box.id: box for box in boxes}
    segments: list[dict[str, Any]] = []
    diagram_type = str(diagram.get("diagramType", "overview")).lower()
    if diagram_type in {"single", "single_entity", "entity"}:
        entity = diagram.get("entity") if isinstance(diagram.get("entity"), dict) else {}
        entity_id = str(entity.get("name", "entity"))
        entity_box = boxes_by_id.get(entity_id)
        if entity_box is None:
            return segments
        for attr in as_list(entity.get("attributes")):
            if not isinstance(attr, dict):
                continue
            attr_id = f"{entity_id}.{attr.get('name', 'attribute')}"
            attr_box = boxes_by_id.get(attr_id)
            if attr_box is None:
                continue
            start = boundary_point(entity_box, attr_box)
            end = boundary_point(attr_box, entity_box)
            segments.append({"id": f"{entity_id}->{attr_id}", "source": entity_id, "target": attr_id, "points": [start, end]})
        return segments

    for idx, entity in enumerate(as_list(diagram.get("entities"))):
        if not isinstance(entity, dict):
            continue
        eid = str(entity.get("id") or entity.get("name") or f"entity_{idx}")
        entity_box = boxes_by_id.get(eid)
        if entity_box is None:
            continue
        for attr in as_list(entity.get("attributes")):
            if not isinstance(attr, dict):
                continue
            attr_id = f"{eid}.{attr.get('name', 'attribute')}"
            attr_box = boxes_by_id.get(attr_id)
            if attr_box is None:
                continue
            segments.append(
                {
                    "id": f"{eid}->{attr_id}",
                    "source": eid,
                    "target": attr_id,
                    "points": [boundary_point(entity_box, attr_box), boundary_point(attr_box, entity_box)],
                }
            )

    for idx, rel in enumerate(as_list(diagram.get("relationships"))):
        if not isinstance(rel, dict):
            continue
        name = str(rel.get("name") or f"relationship_{idx}")
        rel_id = f"rel:{name}:{idx}"
        rel_box = boxes_by_id.get(rel_id)
        if rel_box is None:
            continue
        src = str(rel.get("from", ""))
        dst = str(rel.get("to", ""))
        for entity_id in (src, dst):
            entity_box = boxes_by_id.get(entity_id)
            if entity_box is None:
                continue
            segments.append(
                {
                    "id": f"{entity_id}->{rel_id}",
                    "source": entity_id,
                    "target": rel_id,
                    "points": [boundary_point(entity_box, rel_box), boundary_point(rel_box, entity_box)],
                }
            )
    return segments


def connector_crossings(boxes: list[Box], segments: list[dict[str, Any]], pad: float) -> list[dict[str, Any]]:
    crossings: list[dict[str, Any]] = []
    for segment in segments:
        points = segment.get("points") or []
        if len(points) != 2:
            continue
        a, b = points
        source = str(segment.get("source", ""))
        target = str(segment.get("target", ""))
        for box in boxes:
            if box.id in {source, target}:
                continue
            if box.kind == "label":
                continue
            inflated = box.inflated(pad)
            if segment_intersects_box(a, b, inflated):
                crossings.append(
                    {
                        "edge": segment.get("id", ""),
                        "segment": [[round(a[0], 3), round(a[1], 3)], [round(b[0], 3), round(b[1], 3)]],
                        "shape": box.id,
                        "shape_kind": box.kind,
                        "reason": "segment crosses shape box",
                    }
                )
    return crossings


def main() -> int:
    parser = argparse.ArgumentParser(description="Check positioned ER JSON for overlaps.")
    parser.add_argument("input", help="Positioned ER JSON.")
    parser.add_argument("--pad", type=float, default=0.02, help="Padding around boxes.")
    parser.add_argument("--route-pad", type=float, default=0.02, help="Padding around boxes when checking connector crossings.")
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
    crossings = connector_crossings(boxes, build_segments(diagram, boxes), args.route_pad)
    print(
        json.dumps(
            {
                "boxes": len(boxes),
                "overlapPairs": len(overlaps),
                "largestOverlap": overlaps[0]["area"] if overlaps else 0,
                "connectorCrossings": len(crossings),
                "overlaps": overlaps[:20],
                "crossings": crossings[:30],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if overlaps or crossings else 0


if __name__ == "__main__":
    raise SystemExit(main())
