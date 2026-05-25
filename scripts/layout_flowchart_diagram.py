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


def layout_flowchart(diagram: dict[str, Any]) -> None:
    normalize_diagram(diagram)
    layout = diagram.setdefault("layout", {})
    direction = as_text(layout.get("direction"), "TB").upper()
    rank_gap = float(layout.get("rankGap") or 0.72)
    column_gap = float(layout.get("columnGap") or 1.95)
    nodes = diagram["nodes"]

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
        page_w = float(layout.get("pageWidth") or max(5.8, 1.2 + (max_rank + 1) * rank_gap * 1.35))
        page_h = float(layout.get("pageHeight") or max(3.4, 1.2 + (max_column - min_column + 1) * column_gap * 0.75))
        center_y = page_h / 2
        start_x = 0.65
        for idx, node in enumerate(nodes):
            if node.get("x") is not None and node.get("y") is not None:
                continue
            rank = int(float(node.get("rank", idx)))
            col = int(float(node.get("column", 0)))
            node["x"] = round(start_x + rank * rank_gap * 1.35, 3)
            node["y"] = round(center_y - col * column_gap * 0.75, 3)
    else:
        page_w = float(layout.get("pageWidth") or max(3.2, 2.0 + (max_column - min_column + 1) * column_gap))
        page_h = float(layout.get("pageHeight") or max(3.4, 0.9 + (max_rank + 1) * rank_gap))
        center_x = page_w / 2
        top_y = page_h - 0.45
        for idx, node in enumerate(nodes):
            if node.get("x") is not None and node.get("y") is not None:
                continue
            rank = int(float(node.get("rank", idx)))
            col = int(float(node.get("column", 0)))
            node["x"] = round(center_x + col * column_gap, 3)
            node["y"] = round(top_y - rank * rank_gap, 3)

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
