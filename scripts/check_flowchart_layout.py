#!/usr/bin/env python3
"""Check positioned flowchart JSON for node overlaps and connector crossings."""

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


def as_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def build_boxes(diagram: dict[str, Any]) -> list[Box]:
    boxes: list[Box] = []
    for idx, node in enumerate(as_list(diagram.get("nodes"))):
        if not isinstance(node, dict):
            continue
        nid = str(node.get("id") or node.get("text") or f"node_{idx}")
        boxes.append(
            Box(
                nid,
                str(node.get("type") or "process"),
                float(node.get("x", 0.0)),
                float(node.get("y", 0.0)),
                float(node.get("width", 1.35)),
                float(node.get("height", 0.46)),
            )
        )
    return boxes


def point_in_box(point: tuple[float, float], box: Box, eps: float = 0.001) -> bool:
    x, y = point
    return box.left + eps < x < box.right - eps and box.bottom + eps < y < box.top - eps


def segment_intersects_box(
    a: tuple[float, float],
    b: tuple[float, float],
    box: Box,
    eps: float = 0.001,
) -> bool:
    ax, ay = a
    bx, by = b
    if abs(ax - bx) <= eps:
        x = ax
        if not (box.left + eps < x < box.right - eps):
            return False
        low, high = sorted((ay, by))
        return max(low, box.bottom + eps) < min(high, box.top - eps)
    if abs(ay - by) <= eps:
        y = ay
        if not (box.bottom + eps < y < box.top - eps):
            return False
        low, high = sorted((ax, bx))
        return max(low, box.left + eps) < min(high, box.right - eps)
    return False


def default_points(source: Box, target: Box) -> list[tuple[float, float]]:
    dx = target.x - source.x
    dy = target.y - source.y
    if abs(dx) >= abs(dy):
        start = (source.right if dx >= 0 else source.left, source.y)
        end = (target.left if dx >= 0 else target.right, target.y)
    else:
        start = (source.x, source.top if dy >= 0 else source.bottom)
        end = (target.x, target.bottom if dy >= 0 else target.top)
    if abs(start[0] - end[0]) <= 0.001 or abs(start[1] - end[1]) <= 0.001:
        return [start, end]
    return [start, (end[0], start[1]), end]


def edge_points(edge: dict[str, Any], boxes_by_id: dict[str, Box]) -> list[tuple[float, float]]:
    points = []
    for point in as_list(edge.get("points")):
        if isinstance(point, dict):
            try:
                points.append((float(point["x"]), float(point["y"])))
            except (KeyError, TypeError, ValueError):
                continue
        elif isinstance(point, (list, tuple)) and len(point) >= 2:
            try:
                points.append((float(point[0]), float(point[1])))
            except (TypeError, ValueError):
                continue
    if len(points) >= 2:
        return points
    source_id = as_text(edge.get("from"))
    target_id = as_text(edge.get("to"))
    if source_id in boxes_by_id and target_id in boxes_by_id:
        return default_points(boxes_by_id[source_id], boxes_by_id[target_id])
    return []


def connector_crossings(diagram: dict[str, Any], boxes: list[Box], pad: float) -> list[dict[str, Any]]:
    boxes_by_id = {box.id: box for box in boxes}
    crossings: list[dict[str, Any]] = []
    for index, raw_edge in enumerate(as_list(diagram.get("edges"))):
        if not isinstance(raw_edge, dict):
            continue
        source_id = as_text(raw_edge.get("from"))
        target_id = as_text(raw_edge.get("to"))
        points = edge_points(raw_edge, boxes_by_id)
        if len(points) < 2:
            crossings.append(
                {
                    "edge": f"{source_id}->{target_id}",
                    "segment": None,
                    "node": None,
                    "reason": "missing route points",
                }
            )
            continue
        for a, b in zip(points, points[1:]):
            if abs(a[0] - b[0]) > 0.001 and abs(a[1] - b[1]) > 0.001:
                crossings.append(
                    {
                        "edge": f"{source_id}->{target_id}",
                        "segment": [list(a), list(b)],
                        "node": None,
                        "reason": "non-orthogonal segment",
                    }
                )
                continue
            for box in boxes:
                if box.id in {source_id, target_id}:
                    continue
                inflated = box.inflated(pad)
                if point_in_box(a, inflated) or point_in_box(b, inflated) or segment_intersects_box(a, b, inflated):
                    crossings.append(
                        {
                            "edge": f"{source_id}->{target_id}",
                            "segment": [[round(a[0], 3), round(a[1], 3)], [round(b[0], 3), round(b[1], 3)]],
                            "node": box.id,
                            "reason": "segment crosses node box",
                        }
                    )
    return crossings


def main() -> int:
    parser = argparse.ArgumentParser(description="Check positioned flowchart JSON for overlaps and connector crossings.")
    parser.add_argument("input", help="Positioned flowchart JSON.")
    parser.add_argument("--pad", type=float, default=0.05, help="Padding around boxes.")
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
    crossings = connector_crossings(diagram, boxes, args.route_pad)
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
