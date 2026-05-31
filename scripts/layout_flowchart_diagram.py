#!/usr/bin/env python3
"""Add thesis-style flowchart coordinates to a logical JSON model."""

from __future__ import annotations

import argparse
import copy
import heapq
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


TYPE_SIZE = {
    "start": (0.82, 0.38),
    "end": (0.82, 0.38),
    "terminator": (0.92, 0.38),
    "process": (1.35, 0.46),
    "action": (1.35, 0.46),
    "input": (1.35, 0.46),
    "output": (1.35, 0.46),
    "decision": (1.85, 0.62),
    "database": (1.25, 0.58),
    "document": (1.35, 0.55),
}

ROUTE_CLEARANCE = 0.18
ROUTE_BEND_PENALTY = 0.16
ROUTE_PAGE_MARGIN = 0.25


@dataclass(frozen=True)
class Box:
    id: str
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
        return Box(self.id, self.x, self.y, self.w + pad * 2, self.h + pad * 2)


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def as_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def normalize_node(item: Any, index: int) -> dict[str, Any]:
    if isinstance(item, str):
        return {"id": item, "text": item, "type": "process"}
    if isinstance(item, dict):
        node = dict(item)
        text = as_text(node.get("text") or node.get("label") or node.get("name"), f"步骤{index + 1}")
        node.setdefault("text", text)
        node.setdefault("id", as_text(node.get("id"), f"node_{index + 1}"))
        node.setdefault("type", "process")
        return node
    return {"id": f"node_{index + 1}", "text": f"步骤{index + 1}", "type": "process"}


def normalize_edge(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        edge = dict(item)
        edge.setdefault("from", as_text(edge.get("source")))
        edge.setdefault("to", as_text(edge.get("target")))
        edge.setdefault("label", as_text(edge.get("text") or edge.get("name")))
        return edge
    return {}


def node_size(node: dict[str, Any]) -> tuple[float, float]:
    kind = as_text(node.get("type"), "process").lower()
    width, height = TYPE_SIZE.get(kind, TYPE_SIZE["process"])
    text = as_text(node.get("text"))
    if len(text) > 9 and kind != "decision":
        width = max(width, min(2.0, 0.9 + len(text) * 0.07))
    if node.get("width") is not None:
        width = float(node["width"])
    if node.get("height") is not None:
        height = float(node["height"])
    return width, height


def normalize_diagram(diagram: dict[str, Any]) -> None:
    nodes = [normalize_node(item, idx) for idx, item in enumerate(as_list(diagram.get("nodes")))]
    if not nodes:
        nodes = [
            {"id": "start", "type": "start", "text": "开始"},
            {"id": "process", "type": "process", "text": "处理"},
            {"id": "end", "type": "end", "text": "结束"},
        ]
    edges = [edge for edge in (normalize_edge(item) for item in as_list(diagram.get("edges"))) if edge.get("from") and edge.get("to")]
    if not edges:
        edges = [{"from": nodes[idx]["id"], "to": nodes[idx + 1]["id"], "label": ""} for idx in range(len(nodes) - 1)]
    diagram["nodes"] = nodes
    diagram["edges"] = edges


def truthy(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"0", "false", "no", "off"}:
        return False
    if text in {"1", "true", "yes", "on"}:
        return True
    return default


def group_sizes(nodes: list[dict[str, Any]], axis: str, size_key: str) -> dict[int, float]:
    result: dict[int, float] = {}
    for idx, node in enumerate(nodes):
        value = int(float(node.get(axis, idx if axis == "rank" else 0)))
        result[value] = max(result.get(value, 0.0), float(node.get(size_key, 0.0)))
    return result


def horizontal_positions(sizes: dict[int, float], gap: float, margin: float = 0.65) -> tuple[dict[int, float], float]:
    positions: dict[int, float] = {}
    cursor = margin
    for key in sorted(sizes):
        size = sizes[key]
        positions[key] = cursor + size / 2
        cursor += size + gap
    return positions, cursor + margin - gap if sizes else margin * 2


def vertical_positions(sizes: dict[int, float], gap: float, page_height: float, margin: float = 0.65) -> tuple[dict[int, float], float]:
    total = sum(sizes.values()) + max(0, len(sizes) - 1) * gap
    page_height = max(page_height, total + margin * 2)
    positions: dict[int, float] = {}
    cursor = page_height - margin
    for key in sorted(sizes):
        size = sizes[key]
        positions[key] = cursor - size / 2
        cursor -= size + gap
    return positions, page_height


def shift_positions(positions: dict[int, float], offset: float) -> dict[int, float]:
    if abs(offset) < 0.001:
        return positions
    return {key: value + offset for key, value in positions.items()}


def build_node_index(nodes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {as_text(node.get("id")): node for node in nodes if as_text(node.get("id"))}


def build_boxes(nodes: list[dict[str, Any]]) -> dict[str, Box]:
    boxes: dict[str, Box] = {}
    for node in nodes:
        nid = as_text(node.get("id"))
        if not nid:
            continue
        boxes[nid] = Box(
            nid,
            float(node.get("x", 0.0)),
            float(node.get("y", 0.0)),
            float(node.get("width", 1.35)),
            float(node.get("height", 0.46)),
        )
    return boxes


def unique_sorted(values: list[float]) -> list[float]:
    result: list[float] = []
    for value in sorted(values):
        rounded = round(value, 3)
        if not result or abs(result[-1] - rounded) > 0.025:
            result.append(rounded)
    return result


def edge_orientation(source: Box, target: Box) -> tuple[str, str]:
    dx = target.x - source.x
    dy = target.y - source.y
    if abs(dx) >= abs(dy):
        return ("right", "left") if dx >= 0 else ("left", "right")
    return ("top", "bottom") if dy >= 0 else ("bottom", "top")


def side_point(box: Box, side: str, clearance: float = 0.0) -> tuple[float, float]:
    if side == "right":
        return (box.right + clearance, box.y)
    if side == "left":
        return (box.left - clearance, box.y)
    if side == "top":
        return (box.x, box.top + clearance)
    if side == "bottom":
        return (box.x, box.bottom - clearance)
    return (box.x, box.y)


def point_key(point: tuple[float, float]) -> tuple[float, float]:
    return (round(point[0], 3), round(point[1], 3))


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


def segment_blocked(
    a: tuple[float, float],
    b: tuple[float, float],
    obstacles: list[Box],
) -> bool:
    if abs(a[0] - b[0]) > 0.001 and abs(a[1] - b[1]) > 0.001:
        return True
    for box in obstacles:
        if point_in_box(a, box) or point_in_box(b, box) or segment_intersects_box(a, b, box):
            return True
    return False


def simplify_points(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if not points:
        return []
    simplified: list[tuple[float, float]] = []
    for point in points:
        key = point_key(point)
        if not simplified or point_key(simplified[-1]) != key:
            simplified.append(key)
    changed = True
    while changed:
        changed = False
        output: list[tuple[float, float]] = []
        for point in simplified:
            output.append(point)
            while len(output) >= 3:
                a, b, c = output[-3], output[-2], output[-1]
                if (abs(a[0] - b[0]) <= 0.001 and abs(b[0] - c[0]) <= 0.001) or (
                    abs(a[1] - b[1]) <= 0.001 and abs(b[1] - c[1]) <= 0.001
                ):
                    output.pop(-2)
                    changed = True
                else:
                    break
        simplified = output
    return simplified


def route_between_boxes(
    source: Box,
    target: Box,
    all_boxes: dict[str, Box],
    layout: dict[str, Any],
    route_hint: str,
    side_hint: str,
) -> list[tuple[float, float]]:
    clearance = float(layout.get("routeClearance") or ROUTE_CLEARANCE)
    if route_hint in {"back", "loop", "return"} and side_hint in {"left", "right", "top", "bottom"}:
        start_side = side_hint
        end_side = side_hint
    else:
        start_side, end_side = edge_orientation(source, target)

    start = side_point(source, start_side, 0.0)
    end = side_point(target, end_side, 0.0)
    start_outer = side_point(source, start_side, clearance)
    end_outer = side_point(target, end_side, clearance)

    inflated = [box.inflated(clearance) for node_id, box in all_boxes.items() if node_id not in {source.id, target.id}]
    xs = [ROUTE_PAGE_MARGIN, float(layout.get("pageWidth", 0.0)) - ROUTE_PAGE_MARGIN, source.x, target.x, start[0], end[0], start_outer[0], end_outer[0]]
    ys = [ROUTE_PAGE_MARGIN, float(layout.get("pageHeight", 0.0)) - ROUTE_PAGE_MARGIN, source.y, target.y, start[1], end[1], start_outer[1], end_outer[1]]
    for box in all_boxes.values():
        xs.extend([box.left - clearance, box.left, box.x, box.right, box.right + clearance])
        ys.extend([box.bottom - clearance, box.bottom, box.y, box.top, box.top + clearance])

    if route_hint in {"back", "loop", "return"}:
        if side_hint == "left":
            xs.append(min(source.left, target.left) - clearance * 2.2)
        elif side_hint == "right":
            xs.append(max(source.right, target.right) + clearance * 2.2)
        elif side_hint == "top":
            ys.append(max(source.top, target.top) + clearance * 2.2)
        elif side_hint == "bottom":
            ys.append(min(source.bottom, target.bottom) - clearance * 2.2)

    xs = [value for value in xs if ROUTE_PAGE_MARGIN / 2 <= value <= float(layout.get("pageWidth", 0.0)) - ROUTE_PAGE_MARGIN / 2]
    ys = [value for value in ys if ROUTE_PAGE_MARGIN / 2 <= value <= float(layout.get("pageHeight", 0.0)) - ROUTE_PAGE_MARGIN / 2]
    x_values = unique_sorted(xs)
    y_values = unique_sorted(ys)

    nodes = [(x, y) for x in x_values for y in y_values]
    start_node = point_key(start_outer)
    end_node = point_key(end_outer)
    if start_node not in nodes:
        nodes.append(start_node)
    if end_node not in nodes:
        nodes.append(end_node)

    by_x: dict[float, list[float]] = {}
    by_y: dict[float, list[float]] = {}
    for x, y in nodes:
        by_x.setdefault(x, []).append(y)
        by_y.setdefault(y, []).append(x)
    for values in by_x.values():
        values.sort()
    for values in by_y.values():
        values.sort()

    best: dict[tuple[float, float, str], float] = {}
    previous: dict[tuple[float, float, str], tuple[float, float, str]] = {}
    heap: list[tuple[float, tuple[float, float, str]]] = []
    for direction in ("",):
        state = (start_node[0], start_node[1], direction)
        best[state] = 0.0
        heapq.heappush(heap, (0.0, state))

    target_state: tuple[float, float, str] | None = None
    while heap:
        cost, state = heapq.heappop(heap)
        if cost > best.get(state, math.inf) + 0.0001:
            continue
        x, y, direction = state
        if (x, y) == end_node:
            target_state = state
            break

        candidates: list[tuple[float, float, str]] = []
        y_neighbors = by_x.get(x, [])
        y_index = y_neighbors.index(y)
        if y_index > 0:
            candidates.append((x, y_neighbors[y_index - 1], "V"))
        if y_index + 1 < len(y_neighbors):
            candidates.append((x, y_neighbors[y_index + 1], "V"))
        x_neighbors = by_y.get(y, [])
        x_index = x_neighbors.index(x)
        if x_index > 0:
            candidates.append((x_neighbors[x_index - 1], y, "H"))
        if x_index + 1 < len(x_neighbors):
            candidates.append((x_neighbors[x_index + 1], y, "H"))

        for nx, ny, ndirection in candidates:
            next_point = (nx, ny)
            current_point = (x, y)
            if segment_blocked(current_point, next_point, inflated):
                continue
            step = abs(nx - x) + abs(ny - y)
            turn = ROUTE_BEND_PENALTY if direction and direction != ndirection else 0.0
            next_state = (nx, ny, ndirection)
            next_cost = cost + step + turn
            if next_cost + 0.0001 < best.get(next_state, math.inf):
                best[next_state] = next_cost
                previous[next_state] = state
                heapq.heappush(heap, (next_cost, next_state))

    if target_state is None:
        sx, sy = start_outer
        ex, ey = end_outer
        fallback = [start, start_outer, (sx, ey), end_outer, end]
        return simplify_points(fallback)

    routed: list[tuple[float, float]] = []
    cursor: tuple[float, float, str] | None = target_state
    while cursor is not None:
        routed.append((cursor[0], cursor[1]))
        cursor = previous.get(cursor)
    routed.reverse()
    return simplify_points([start, *routed, end])


def route_flowchart_edges(diagram: dict[str, Any]) -> None:
    nodes = diagram["nodes"]
    boxes = build_boxes(nodes)
    layout = diagram.setdefault("layout", {})
    for edge in diagram["edges"]:
        source_id = as_text(edge.get("from"))
        target_id = as_text(edge.get("to"))
        if source_id not in boxes or target_id not in boxes:
            continue
        if isinstance(edge.get("points"), list) and edge["points"]:
            continue
        route_hint = as_text(edge.get("route")).lower()
        side_hint = as_text(edge.get("side")).lower()
        points = route_between_boxes(boxes[source_id], boxes[target_id], boxes, layout, route_hint, side_hint)
        edge["points"] = [{"x": round(x, 3), "y": round(y, 3)} for x, y in points]


def maybe_wrap_flat_lr(nodes: list[dict[str, Any]], layout: dict[str, Any], direction: str) -> None:
    if direction not in {"LR", "RL"}:
        return
    if any(node.get("x") is not None or node.get("y") is not None for node in nodes):
        return
    if any(node.get("column") is not None for node in nodes):
        return
    wrap_after_raw = layout.get("wrapAfter") or layout.get("maxPerRow")
    wrap_after = int(float(wrap_after_raw)) if wrap_after_raw is not None else 0
    if not wrap_after and truthy(layout.get("autoWrapFlat"), True) and len(nodes) >= 4:
        wrap_after = 2 if len(nodes) == 4 else 3
    if wrap_after <= 0 or wrap_after >= len(nodes):
        return
    for idx, node in enumerate(nodes):
        row = idx // wrap_after
        offset = idx % wrap_after
        node["rank"] = offset if row % 2 == 0 else wrap_after - offset - 1
        node["column"] = row
    layout["wrapped"] = True
    layout["wrapStyle"] = "serpentine"
    layout["wrapAfter"] = wrap_after


def layout_flowchart(diagram: dict[str, Any]) -> None:
    normalize_diagram(diagram)
    layout = diagram.setdefault("layout", {})
    direction = as_text(layout.get("direction"), "TB").upper()
    rank_gap = float(layout.get("rankGap") or 0.72)
    column_gap = float(layout.get("columnGap") or 1.95)
    nodes = diagram["nodes"]

    maybe_wrap_flat_lr(nodes, layout, direction)

    for idx, node in enumerate(nodes):
        node.setdefault("rank", idx)
        node.setdefault("column", 0)
        width, height = node_size(node)
        node["width"] = round(width, 3)
        node["height"] = round(height, 3)

    max_rank = max(int(float(node.get("rank", idx))) for idx, node in enumerate(nodes))
    min_column = min(int(float(node.get("column", 0))) for node in nodes)
    max_column = max(int(float(node.get("column", 0))) for node in nodes)

    if direction in {"LR", "RL"}:
        rank_sizes = group_sizes(nodes, "rank", "width")
        column_sizes = group_sizes(nodes, "column", "height")
        x_positions, needed_w = horizontal_positions(rank_sizes, rank_gap)
        page_w = max(float(layout.get("pageWidth") or 0.0), needed_w, 5.0)
        x_positions = shift_positions(x_positions, (page_w - needed_w) / 2)
        y_positions, page_h = vertical_positions(column_sizes, column_gap, max(float(layout.get("pageHeight") or 0.0), 3.4))
        if direction == "RL":
            x_positions = {key: round(page_w - value, 3) for key, value in x_positions.items()}
        for idx, node in enumerate(nodes):
            if node.get("x") is not None and node.get("y") is not None:
                continue
            rank = int(float(node.get("rank", idx)))
            col = int(float(node.get("column", 0)))
            node["x"] = round(x_positions[rank], 3)
            node["y"] = round(y_positions[col], 3)
    else:
        column_sizes = group_sizes(nodes, "column", "width")
        rank_sizes = group_sizes(nodes, "rank", "height")
        x_positions, needed_w = horizontal_positions(column_sizes, column_gap)
        page_w = max(float(layout.get("pageWidth") or 0.0), needed_w, 3.2)
        x_positions = shift_positions(x_positions, (page_w - needed_w) / 2)
        y_positions, page_h = vertical_positions(rank_sizes, rank_gap, max(float(layout.get("pageHeight") or 0.0), 3.4))
        if direction in {"BT"}:
            y_positions = {key: round(page_h - value, 3) for key, value in y_positions.items()}
        for idx, node in enumerate(nodes):
            if node.get("x") is not None and node.get("y") is not None:
                continue
            rank = int(float(node.get("rank", idx)))
            col = int(float(node.get("column", 0)))
            node["x"] = round(x_positions[col], 3)
            node["y"] = round(y_positions[rank], 3)

    layout["pageWidth"] = round(page_w, 3)
    layout["pageHeight"] = round(page_h, 3)
    layout["direction"] = direction
    route_flowchart_edges(diagram)


def main() -> int:
    parser = argparse.ArgumentParser(description="Layout thesis-style flowchart JSON for Visio rendering.")
    parser.add_argument("input", help="Input logical flowchart JSON.")
    parser.add_argument("--out", required=True, help="Output positioned flowchart JSON.")
    args = parser.parse_args()

    source = Path(args.input)
    target = Path(args.out)
    output = copy.deepcopy(json.loads(source.read_text(encoding="utf-8")))
    diagram_type = as_text(output.get("diagramType"), "flowchart").lower()
    if diagram_type not in {"flowchart", "workflow", "business_flow", "algorithm_flow"}:
        raise SystemExit(f"Unsupported diagramType: {diagram_type}")
    layout_flowchart(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"input": str(source), "out": str(target), "diagramType": diagram_type}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
