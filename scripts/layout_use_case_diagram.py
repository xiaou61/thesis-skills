#!/usr/bin/env python3
"""Add thesis-style UML use-case coordinates to a logical JSON model."""

from __future__ import annotations

import argparse
import copy
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTOR_W = 0.72
ACTOR_H = 1.25
USE_CASE_W = 1.65
USE_CASE_H = 0.48
PAD = 0.04


@dataclass
class Box:
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


def as_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def truthy(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "是"}


def normalize_item(item: Any, index: int, prefix: str) -> dict[str, Any]:
    if isinstance(item, str):
        return {"id": item, "name": item}
    if isinstance(item, dict):
        result = dict(item)
        name = as_text(result.get("name") or result.get("title"), f"{prefix}_{index + 1}")
        result.setdefault("name", name)
        result.setdefault("id", as_text(result.get("id"), name))
        return result
    return {"id": f"{prefix}_{index + 1}", "name": f"{prefix}_{index + 1}"}


def ensure_use_case(use_cases: list[dict[str, Any]], by_id: dict[str, dict[str, Any]], item: Any) -> dict[str, Any]:
    case = normalize_item(item, len(use_cases), "use_case")
    cid = as_text(case.get("id"), as_text(case.get("name")))
    if cid in by_id:
        if isinstance(item, dict):
            by_id[cid].update({key: value for key, value in case.items() if value not in (None, "")})
        return by_id[cid]
    case["id"] = cid
    by_id[cid] = case
    use_cases.append(case)
    return case


def normalize_diagram(diagram: dict[str, Any]) -> None:
    actors = [normalize_item(item, idx, "actor") for idx, item in enumerate(as_list(diagram.get("actors") or diagram.get("actor")))]
    if not actors:
        actors = [{"id": "actor", "name": "参与者"}]

    use_cases: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    for item in as_list(diagram.get("useCases") or diagram.get("usecases")):
        ensure_use_case(use_cases, by_id, item)

    associations: list[dict[str, Any]] = []
    for actor in actors:
        actor_id = as_text(actor.get("id"), as_text(actor.get("name")))
        for case_item in as_list(actor.get("useCases") or actor.get("usecases")):
            case = ensure_use_case(use_cases, by_id, case_item)
            associations.append({"actor": actor_id, "useCase": case["id"]})

    for item in as_list(diagram.get("associations") or diagram.get("relations")):
        if not isinstance(item, dict):
            continue
        actor_id = as_text(item.get("actor") or item.get("from"))
        case_ref = item.get("useCase") or item.get("usecase") or item.get("to")
        if not actor_id or case_ref is None:
            continue
        case = ensure_use_case(use_cases, by_id, case_ref)
        associations.append({"actor": actor_id, "useCase": case["id"], "label": as_text(item.get("label"))})

    if not associations and len(actors) == 1:
        actor_id = as_text(actors[0].get("id"), as_text(actors[0].get("name")))
        for case in use_cases:
            associations.append({"actor": actor_id, "useCase": case["id"]})

    dependencies: list[dict[str, Any]] = []
    for item in as_list(diagram.get("dependencies") or diagram.get("includes") or diagram.get("extends")):
        if not isinstance(item, dict):
            continue
        source = item.get("from") or item.get("source")
        target = item.get("to") or item.get("target")
        if source is None or target is None:
            continue
        source_case = ensure_use_case(use_cases, by_id, source)
        target_case = ensure_use_case(use_cases, by_id, target)
        dependencies.append(
            {
                "from": source_case["id"],
                "to": target_case["id"],
                "type": as_text(item.get("type"), "dependency"),
                "label": as_text(item.get("label")),
            }
        )

    diagram["actors"] = actors
    diagram["useCases"] = use_cases
    diagram["associations"] = associations
    diagram["dependencies"] = dependencies


def distribute(count: int, low: float, high: float) -> list[float]:
    if count <= 0:
        return []
    if count == 1:
        return [(low + high) / 2]
    return [low + (high - low) * i / (count - 1) for i in range(count)]


def split_use_cases(use_cases: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    left = [case for case in use_cases if as_text(case.get("side")).lower() == "left"]
    right = [case for case in use_cases if as_text(case.get("side")).lower() == "right"]
    free = [case for case in use_cases if case not in left and case not in right]
    for idx, case in enumerate(free):
        if idx % 2 == 0:
            left.append(case)
        else:
            right.append(case)
    return left, right


def layout_single_actor_radial(diagram: dict[str, Any]) -> None:
    actors = diagram["actors"]
    use_cases = diagram["useCases"]
    layout = diagram.setdefault("layout", {})
    left, right = split_use_cases(use_cases)
    rows = max(len(left), len(right), 1)
    page_w = float(layout.get("pageWidth") or 7.2)
    page_h = float(layout.get("pageHeight") or max(3.8, 1.0 + rows * 0.72))

    actor = actors[0]
    actor["x"] = round(page_w / 2, 3)
    actor["y"] = round(page_h / 2, 3)
    actor["width"] = ACTOR_W
    actor["height"] = ACTOR_H

    y_values = distribute(rows, page_h - 0.65, 0.65)
    for idx, case in enumerate(left):
        case["x"] = round(0.95, 3)
        case["y"] = round(y_values[idx], 3)
    for idx, case in enumerate(right):
        case["x"] = round(page_w - 0.95, 3)
        case["y"] = round(y_values[idx], 3)

    layout["pageWidth"] = page_w
    layout["pageHeight"] = page_h
    layout["mode"] = "single_actor_radial"


def layout_single_actor_left(diagram: dict[str, Any]) -> None:
    actors = diagram["actors"]
    use_cases = diagram["useCases"]
    layout = diagram.setdefault("layout", {})
    count = max(len(use_cases), 1)
    page_w = float(layout.get("pageWidth") or 5.4)
    page_h = float(layout.get("pageHeight") or max(3.4, 0.8 + count * 0.76))

    actor = actors[0]
    actor["x"] = round(0.75, 3)
    actor["y"] = round(page_h / 2, 3)
    actor["width"] = ACTOR_W
    actor["height"] = ACTOR_H

    for case, y in zip(use_cases, distribute(count, page_h - 0.65, 0.65)):
        case["x"] = round(page_w - 1.05, 3)
        case["y"] = round(y, 3)

    layout["pageWidth"] = page_w
    layout["pageHeight"] = page_h
    layout["mode"] = "single_actor_left"


def layout_boundary(diagram: dict[str, Any]) -> None:
    actors = diagram["actors"]
    use_cases = diagram["useCases"]
    deps = diagram.get("dependencies", [])
    layout = diagram.setdefault("layout", {})
    system = diagram.get("system") if isinstance(diagram.get("system"), dict) else {}
    rows = max(len(actors), max(1, math.ceil(len(use_cases) / 2)))
    page_w = float(layout.get("pageWidth") or 7.3)
    page_h = float(layout.get("pageHeight") or max(4.2, 1.0 + rows * 0.92))

    raw_system_name = system.get("name") if "name" in system else diagram.get("systemName")
    boundary_left = 1.35
    boundary_width = page_w - 1.65
    boundary = {
        "name": as_text(raw_system_name, "系统" if raw_system_name is None else ""),
        "x": boundary_left + boundary_width / 2,
        "y": page_h / 2,
        "width": boundary_width,
        "height": page_h - 0.45,
    }
    layout["boundary"] = boundary
    layout["pageWidth"] = page_w
    layout["pageHeight"] = page_h
    layout["mode"] = "boundary"
    right_case_x = boundary_left + boundary_width - USE_CASE_W / 2 - 0.22

    actor_y = distribute(len(actors), page_h - 0.85, 0.85)
    for actor, y in zip(actors, actor_y):
        actor["x"] = 0.45
        actor["y"] = round(y, 3)
        actor["width"] = ACTOR_W
        actor["height"] = ACTOR_H

    target_ids = {as_text(dep.get("to")) for dep in deps}
    source_ids = {as_text(dep.get("from")) for dep in deps}
    primary_cases = [case for case in use_cases if truthy(case.get("primary")) or as_text(case.get("id")) in source_ids]
    if primary_cases and target_ids:
        primary = primary_cases[0]
        primary["x"] = round(boundary_left + 1.55, 3)
        primary["y"] = round(boundary["y"], 3)
        right_cases = [case for case in use_cases if case is not primary and as_text(case.get("id")) in target_ids]
        other_cases = [case for case in use_cases if case is not primary and case not in right_cases]
        ordered = right_cases + other_cases
        for case, y in zip(ordered, distribute(len(ordered), page_h - 0.85, 0.85)):
            case["x"] = round(right_case_x, 3)
            case["y"] = round(y, 3)
    else:
        columns = 1 if len(use_cases) <= 5 else 2
        if columns == 1:
            xs = [boundary_left + boundary["width"] / 2]
        else:
            xs = [boundary_left + 1.45, right_case_x]
        for col in range(columns):
            column_cases = use_cases[col::columns]
            for case, y in zip(column_cases, distribute(len(column_cases), page_h - 0.85, 0.85)):
                case["x"] = round(xs[col], 3)
                case["y"] = round(y, 3)


def apply_manual_positions(diagram: dict[str, Any]) -> None:
    for node in as_list(diagram.get("actors")) + as_list(diagram.get("useCases")):
        if not isinstance(node, dict):
            continue
        if node.get("x") is not None and node.get("y") is not None:
            node["x"] = round(float(node["x"]), 3)
            node["y"] = round(float(node["y"]), 3)
        node.setdefault("width", ACTOR_W if node in diagram.get("actors", []) else USE_CASE_W)
        node.setdefault("height", ACTOR_H if node in diagram.get("actors", []) else USE_CASE_H)


def layout_use_case(diagram: dict[str, Any]) -> None:
    normalize_diagram(diagram)
    layout = diagram.setdefault("layout", {})
    mode = as_text(layout.get("mode")).lower()
    system = diagram.get("system") if isinstance(diagram.get("system"), dict) else {}
    show_boundary = truthy(system.get("showBoundary"), len(diagram["actors"]) > 1 or bool(diagram.get("dependencies")))

    if not mode:
        if show_boundary:
            mode = "boundary"
        elif len(diagram["actors"]) == 1 and len(diagram["useCases"]) <= 5:
            mode = "single_actor_left"
        else:
            mode = "single_actor_radial"

    if mode in {"boundary", "system"}:
        layout_boundary(diagram)
    elif mode in {"single_actor_left", "left"}:
        layout_single_actor_left(diagram)
    else:
        layout_single_actor_radial(diagram)

    apply_manual_positions(diagram)


def main() -> int:
    parser = argparse.ArgumentParser(description="Layout thesis-style UML use-case JSON for Visio rendering.")
    parser.add_argument("input", help="Input logical use-case JSON.")
    parser.add_argument("--out", required=True, help="Output positioned use-case JSON.")
    args = parser.parse_args()

    source = Path(args.input)
    target = Path(args.out)
    output = copy.deepcopy(json.loads(source.read_text(encoding="utf-8")))
    diagram_type = as_text(output.get("diagramType"), "use_case").lower()
    if diagram_type not in {"use_case", "usecase", "uml_use_case"}:
        raise SystemExit(f"Unsupported diagramType: {diagram_type}")
    layout_use_case(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"input": str(source), "out": str(target), "diagramType": diagram_type}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
