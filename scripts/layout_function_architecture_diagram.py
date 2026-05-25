#!/usr/bin/env python3
"""Layout thesis-style system function architecture diagrams for Visio."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


ROOT_W = 2.7
ROOT_H = 0.44
GROUP_W = 1.12
GROUP_H = 0.38
LEAF_W = 0.34
LEAF_H = 1.12
LEAF_GAP = 0.16
GROUP_GAP = 0.85


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


def normalize_child(item: Any, index: int, prefix: str) -> dict[str, Any]:
    if isinstance(item, str):
        return {"id": f"{prefix}_{index + 1}", "name": item}
    if isinstance(item, dict):
        result = dict(item)
        name = as_text(result.get("name") or result.get("text") or result.get("title"), f"{prefix}_{index + 1}")
        result.setdefault("name", name)
        result.setdefault("id", as_text(result.get("id"), f"{prefix}_{index + 1}"))
        return result
    return {"id": f"{prefix}_{index + 1}", "name": f"{prefix}_{index + 1}"}


def normalize_group(item: Any, index: int, prefix: str) -> dict[str, Any]:
    if isinstance(item, str):
        return {"id": f"{prefix}_{index + 1}", "name": item, "children": []}
    if isinstance(item, dict):
        result = dict(item)
        name = as_text(result.get("name") or result.get("text") or result.get("title"), f"{prefix}_{index + 1}")
        result.setdefault("name", name)
        result.setdefault("id", as_text(result.get("id"), f"{prefix}_{index + 1}"))
        result["children"] = [
            normalize_child(child, child_index, f"{result['id']}_child")
            for child_index, child in enumerate(as_list(result.get("children") or result.get("items") or result.get("functions")))
        ]
        return result
    return {"id": f"{prefix}_{index + 1}", "name": f"{prefix}_{index + 1}", "children": []}


def group_width(group: dict[str, Any]) -> float:
    count = max(1, len(as_list(group.get("children"))))
    return max(GROUP_W, count * LEAF_W + (count - 1) * LEAF_GAP)


def vertical_text(text: str) -> str:
    if "\n" in text:
        return text
    return "\n".join(list(text))


def add_segment(segments: list[dict[str, float]], x1: float, y1: float, x2: float, y2: float) -> None:
    segments.append({"x1": round(x1, 3), "y1": round(y1, 3), "x2": round(x2, 3), "y2": round(y2, 3)})


def layout_function_architecture(diagram: dict[str, Any]) -> None:
    layout = diagram.setdefault("layout", {})
    root_obj = diagram.get("root") if isinstance(diagram.get("root"), dict) else {}
    root_name = as_text(root_obj.get("name") or root_obj.get("text") or diagram.get("systemName") or diagram.get("title"), "系统名称")
    top_groups = [normalize_group(item, idx, "top") for idx, item in enumerate(as_list(diagram.get("topGroups") or diagram.get("frontendGroups")))]
    bottom_groups = [normalize_group(item, idx, "bottom") for idx, item in enumerate(as_list(diagram.get("bottomGroups") or diagram.get("backendGroups") or diagram.get("modules")))]
    if not top_groups and not bottom_groups:
        bottom_groups = [
            normalize_group({"id": "module", "name": "功能模块", "children": ["功能一", "功能二", "功能三"]}, 0, "bottom")
        ]

    top_width = sum(group_width(group) for group in top_groups) + max(0, len(top_groups) - 1) * GROUP_GAP
    bottom_width = sum(group_width(group) for group in bottom_groups) + max(0, len(bottom_groups) - 1) * GROUP_GAP
    page_w = float(layout.get("pageWidth") or max(7.2, top_width + 1.4, bottom_width + 1.4, ROOT_W + 1.2))
    page_h = float(layout.get("pageHeight") or 5.55)
    center_x = page_w / 2

    nodes: list[dict[str, Any]] = []
    segments: list[dict[str, float]] = []

    root = {
        "id": "root",
        "name": root_name,
        "kind": "root",
        "x": round(center_x, 3),
        "y": 3.18,
        "width": ROOT_W,
        "height": ROOT_H,
    }
    nodes.append(root)

    backend_name = as_text(diagram.get("backendName"), "后台模块")
    if bottom_groups:
        backend = {
            "id": "backend",
            "name": backend_name,
            "kind": "group",
            "x": round(center_x, 3),
            "y": 2.58,
            "width": GROUP_W,
            "height": GROUP_H,
        }
        nodes.append(backend)
        add_segment(segments, center_x, root["y"] - ROOT_H / 2, center_x, backend["y"] + GROUP_H / 2)

    if top_groups:
        cursor = center_x - top_width / 2
        root_bus_y = root["y"] + ROOT_H / 2 + 0.09
        leaf_bus_y = 4.03
        top_group_y = 3.76
        group_centers = []
        for group_index, group in enumerate(top_groups):
            width = group_width(group)
            group_center = cursor + width / 2
            group_centers.append(group_center)
            children = as_list(group.get("children"))
            leaf_y = 4.78
            group_node = {
                "id": group["id"],
                "name": group["name"],
                "kind": "group",
                "x": round(group_center, 3),
                "y": top_group_y,
                "width": GROUP_W,
                "height": GROUP_H,
            }
            nodes.append(group_node)
            if children:
                leaf_start = group_center - width / 2 + LEAF_W / 2
                leaf_centers = []
                for child_index, child in enumerate(children):
                    leaf_x = leaf_start + child_index * (LEAF_W + LEAF_GAP)
                    leaf_centers.append(leaf_x)
                    nodes.append(
                        {
                            "id": child["id"],
                            "name": child["name"],
                            "displayName": vertical_text(child["name"]),
                            "kind": "leaf",
                            "x": round(leaf_x, 3),
                            "y": leaf_y,
                            "width": LEAF_W,
                            "height": LEAF_H,
                        }
                    )
                    add_segment(segments, leaf_x, leaf_y - LEAF_H / 2, leaf_x, leaf_bus_y)
                add_segment(segments, min(leaf_centers), leaf_bus_y, max(leaf_centers), leaf_bus_y)
                add_segment(segments, group_center, leaf_bus_y, group_center, top_group_y + GROUP_H / 2)
            add_segment(segments, group_center, top_group_y - GROUP_H / 2, group_center, root_bus_y)
            cursor += width + GROUP_GAP
        if group_centers:
            add_segment(segments, center_x, root["y"] + ROOT_H / 2, center_x, root_bus_y)
            add_segment(segments, min(group_centers), root_bus_y, max(group_centers), root_bus_y)

    if bottom_groups:
        bottom_width = sum(group_width(group) for group in bottom_groups) + max(0, len(bottom_groups) - 1) * GROUP_GAP
        cursor = center_x - bottom_width / 2
        group_y = 1.9
        top_bus_y = 2.18
        leaf_bus_y = 1.42
        leaf_y = 0.72
        add_segment(segments, center_x, 2.58 - GROUP_H / 2, center_x, top_bus_y)
        group_centers = []
        for group in bottom_groups:
            width = group_width(group)
            group_center = cursor + width / 2
            group_centers.append(group_center)
            group_node = {
                "id": group["id"],
                "name": group["name"],
                "kind": "group",
                "x": round(group_center, 3),
                "y": group_y,
                "width": GROUP_W,
                "height": GROUP_H,
            }
            nodes.append(group_node)
            add_segment(segments, group_center, top_bus_y, group_center, group_y + GROUP_H / 2)
            children = as_list(group.get("children"))
            if children:
                leaf_start = group_center - width / 2 + LEAF_W / 2
                leaf_centers = []
                for child_index, child in enumerate(children):
                    leaf_x = leaf_start + child_index * (LEAF_W + LEAF_GAP)
                    leaf_centers.append(leaf_x)
                    nodes.append(
                        {
                            "id": child["id"],
                            "name": child["name"],
                            "displayName": vertical_text(child["name"]),
                            "kind": "leaf",
                            "x": round(leaf_x, 3),
                            "y": leaf_y,
                            "width": LEAF_W,
                            "height": LEAF_H,
                        }
                    )
                    add_segment(segments, leaf_x, leaf_y + LEAF_H / 2, leaf_x, leaf_bus_y)
                add_segment(segments, min(leaf_centers), leaf_bus_y, max(leaf_centers), leaf_bus_y)
                add_segment(segments, group_center, group_y - GROUP_H / 2, group_center, leaf_bus_y)
            cursor += width + GROUP_GAP
        if group_centers:
            add_segment(segments, min(group_centers), top_bus_y, max(group_centers), top_bus_y)

    layout["pageWidth"] = round(page_w, 3)
    layout["pageHeight"] = round(page_h, 3)
    layout["mode"] = "function_architecture_tree"
    diagram["nodes"] = nodes
    diagram["segments"] = segments


def main() -> int:
    parser = argparse.ArgumentParser(description="Layout thesis-style function architecture JSON for Visio rendering.")
    parser.add_argument("input", help="Input logical function architecture JSON.")
    parser.add_argument("--out", required=True, help="Output positioned function architecture JSON.")
    args = parser.parse_args()

    source = Path(args.input)
    target = Path(args.out)
    output = copy.deepcopy(json.loads(source.read_text(encoding="utf-8")))
    diagram_type = as_text(output.get("diagramType"), "function_architecture").lower()
    if diagram_type not in {"function_architecture", "function_structure", "module_architecture", "architecture"}:
        raise SystemExit(f"Unsupported diagramType: {diagram_type}")
    layout_function_architecture(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"input": str(source), "out": str(target), "diagramType": diagram_type}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
