#!/usr/bin/env python3
"""Add thesis-style flowchart coordinates to a logical JSON model."""

from __future__ import annotations

import argparse
import copy
import json
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
