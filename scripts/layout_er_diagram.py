#!/usr/bin/env python3
"""Add thesis-style Chen ER diagram coordinates to a logical ER JSON file.

The output is intended for generate_visio_er_diagram.ps1.  It keeps the input
schema small while avoiding the worst overlap cases by separating the problem
into two passes:

1. place the entity/relationship skeleton
2. place attribute ovals in non-overlapping candidate slots around each entity
"""

from __future__ import annotations

import argparse
import copy
import json
import math
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
PAD = 0.08
DEFAULT_OVERVIEW_LIMITS = {
    "maxEntities": 8,
    "maxAttributesPerEntity": 0,
    "maxRelationships": 8,
}


@dataclass
class Box:
    x: float
    y: float
    w: float
    h: float
    kind: str = "shape"

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
        return Box(self.x, self.y, self.w + pad * 2, self.h + pad * 2, self.kind)


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def attr_name(attr: Any) -> str:
    if isinstance(attr, str):
        return attr.strip()
    if isinstance(attr, dict):
        return str(attr.get("name", "")).strip()
    return ""


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "是"}


def numeric(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def attr_is_key(attr: Any) -> bool:
    if not isinstance(attr, dict):
        return False
    return truthy(attr.get("key")) or truthy(attr.get("pk")) or truthy(attr.get("primary"))


def attr_priority(attr: Any) -> float:
    if not isinstance(attr, dict):
        return 0.0
    return numeric(attr.get("priority"), 0.0)


def get_overview_limits(diagram: dict[str, Any]) -> dict[str, int]:
    layout = diagram.setdefault("layout", {})
    raw_limits: dict[str, Any] = {}
    if isinstance(diagram.get("limits"), dict):
        raw_limits.update(diagram["limits"])
    if isinstance(layout.get("limits"), dict):
        raw_limits.update(layout["limits"])

    limits: dict[str, int] = {}
    for key, default in DEFAULT_OVERVIEW_LIMITS.items():
        value = raw_limits.get(key, default)
        try:
            limits[key] = int(value)
        except Exception:
            limits[key] = default
    return limits


def has_xy(item: dict[str, Any]) -> bool:
    return item.get("x") is not None and item.get("y") is not None


def bbox_overlap(a: Box, b: Box, pad: float = PAD) -> float:
    dx = min(a.right + pad, b.right + pad) - max(a.left - pad, b.left - pad)
    dy = min(a.top + pad, b.top + pad) - max(a.bottom - pad, b.bottom - pad)
    if dx <= 0 or dy <= 0:
        return 0.0
    return dx * dy


def boundary_distance(ux: float, uy: float, width: float, height: float) -> float:
    """Distance from a rectangle center to its edge in a ray direction."""

    candidates: list[float] = []
    if abs(ux) > 0.001:
        candidates.append((width / 2) / abs(ux))
    if abs(uy) > 0.001:
        candidates.append((height / 2) / abs(uy))
    return min(candidates) if candidates else 0.0


def projected_half_width(ux: float, uy: float, width: float, height: float) -> float:
    return abs(ux) * width / 2 + abs(uy) * height / 2


def page_defaults(entity_count: int, attr_count: int) -> tuple[float, float]:
    width = max(6.0, min(15.0, 3.15 * max(2, math.ceil(math.sqrt(max(1, entity_count * 2))))))
    height = max(4.0, min(10.5, 1.2 + entity_count * 0.75 + attr_count * 0.035))
    return width, height


def page_outside_penalty(x: float, y: float, w: float, h: float, page_w: float, page_h: float) -> float:
    outside = 0.0
    if x < w / 2:
        outside += w / 2 - x
    if x > page_w - w / 2:
        outside += x - (page_w - w / 2)
    if y < h / 2:
        outside += h / 2 - y
    if y > page_h - h / 2:
        outside += y - (page_h - h / 2)
    return outside


def same_box(a: Box, b: Box, eps: float = 0.001) -> bool:
    return (
        abs(a.x - b.x) <= eps
        and abs(a.y - b.y) <= eps
        and abs(a.w - b.w) <= eps
        and abs(a.h - b.h) <= eps
        and a.kind == b.kind
    )


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


def segment_crossing_count(
    a: tuple[float, float],
    b: tuple[float, float],
    obstacles: list[Box],
    exclude: tuple[Box, ...] = (),
    pad: float = 0.02,
) -> int:
    count = 0
    for obstacle in obstacles:
        if any(same_box(obstacle, item) for item in exclude):
            continue
        if segment_intersects_box(a, b, obstacle.inflated(pad)):
            count += 1
    return count


def overview_ring_angles(count: int) -> list[float]:
    """Return balanced angles with the first two hubs on opposite sides."""

    preferred = [180, 0, 60, 120, 240, 300, 90, 270]
    if count <= len(preferred):
        return [math.radians(item) for item in preferred[:count]]
    return [math.pi + (2 * math.pi * i / max(1, count)) for i in range(count)]


def build_degrees(entities: list[dict[str, Any]], relationships: list[dict[str, Any]]) -> dict[str, int]:
    ids = [entity_id(e, i) for i, e in enumerate(entities)]
    degrees = {item: 0 for item in ids}
    for rel in relationships:
        src = str(rel.get("from", "")).strip()
        dst = str(rel.get("to", "")).strip()
        if src in degrees:
            degrees[src] += 1
        if dst in degrees:
            degrees[dst] += 1
    return degrees


def entity_id(entity: dict[str, Any], index: int) -> str:
    return str(entity.get("id") or entity.get("name") or f"entity_{index}").strip()


def sort_hubs(entities: list[dict[str, Any]], relationships: list[dict[str, Any]]) -> list[str]:
    degrees = build_degrees(entities, relationships)
    name_bonus: dict[str, float] = {}
    for i, entity in enumerate(entities):
        eid = entity_id(entity, i)
        name = str(entity.get("name", ""))
        bonus = 0.0
        if "用户" in name or "user" in eid.lower():
            bonus += 0.35
        if "管理" in name or "admin" in eid.lower():
            bonus += 0.25
        name_bonus[eid] = bonus
    return sorted(degrees, key=lambda item: (degrees[item] + name_bonus.get(item, 0.0), degrees[item]), reverse=True)


def hub_spoke_angles(count: int) -> list[float]:
    preferred = [0, 55, -55, 125, -125, 180, 90, -90, 35, -35, 145, -145]
    if count <= len(preferred):
        return [math.radians(item) for item in preferred[:count]]
    return [2 * math.pi * i / max(1, count) for i in range(count)]


def apply_overview_limits(diagram: dict[str, Any]) -> None:
    """Keep overview ER diagrams readable by limiting detail density.

    The omitted detail is recorded in layoutNotes so the user can generate
    single-entity diagrams or database tables for the full field list.
    """

    limits = get_overview_limits(diagram)
    entities = [item for item in as_list(diagram.get("entities")) if isinstance(item, dict)]
    relationships = [item for item in as_list(diagram.get("relationships")) if isinstance(item, dict)]
    degrees = build_degrees(entities, relationships)
    notes: dict[str, Any] = {
        "limits": limits,
        "omittedEntities": [],
        "omittedRelationships": [],
        "omittedAttributes": {},
    }

    max_entities = limits.get("maxEntities", 0)
    if max_entities > 0 and len(entities) > max_entities:
        scored: list[tuple[float, int, dict[str, Any], str]] = []
        for idx, entity in enumerate(entities):
            eid = entity_id(entity, idx)
            score = degrees.get(eid, 0) * 10
            score += numeric(entity.get("priority"), 0.0)
            if truthy(entity.get("include")) or truthy(entity.get("core")):
                score += 10000
            name = str(entity.get("name", ""))
            if "用户" in name or "user" in eid.lower():
                score += 2
            if "管理" in name or "admin" in eid.lower():
                score += 1
            scored.append((score, -idx, entity, eid))
        scored.sort(reverse=True, key=lambda item: (item[0], item[1]))
        keep_ids = {eid for _, _, _, eid in scored[:max_entities]}
        kept_entities = [entity for _, _, entity, eid in scored if eid in keep_ids]
        omitted = [entity for _, _, entity, eid in scored if eid not in keep_ids]
        notes["omittedEntities"] = [
            {"id": entity_id(entity, idx), "name": entity.get("name", entity_id(entity, idx))}
            for idx, entity in enumerate(omitted)
        ]
        diagram["entities"] = kept_entities
        relationships = [
            rel
            for rel in relationships
            if str(rel.get("from", "")).strip() in keep_ids and str(rel.get("to", "")).strip() in keep_ids
        ]
        entities = kept_entities

    max_relationships = limits.get("maxRelationships", 0)
    if max_relationships > 0 and len(relationships) > max_relationships:
        degrees = build_degrees(entities, relationships)

        def relationship_score(item: tuple[int, dict[str, Any]]) -> tuple[float, int]:
            idx, rel = item
            src = str(rel.get("from", "")).strip()
            dst = str(rel.get("to", "")).strip()
            score = degrees.get(src, 0) + degrees.get(dst, 0)
            score += numeric(rel.get("priority"), 0.0)
            if truthy(rel.get("include")) or truthy(rel.get("core")):
                score += 10000
            return score, -idx

        indexed = list(enumerate(relationships))
        indexed.sort(key=relationship_score, reverse=True)
        keep_indexes = {idx for idx, _ in indexed[:max_relationships]}
        notes["omittedRelationships"] = [
            {
                "name": rel.get("name", "关系"),
                "from": rel.get("from", ""),
                "to": rel.get("to", ""),
            }
            for idx, rel in indexed
            if idx not in keep_indexes
        ]
        relationships = [rel for idx, rel in enumerate(relationships) if idx in keep_indexes]

    max_attrs = limits.get("maxAttributesPerEntity", 0)
    if max_attrs >= 0:
        for entity in entities:
            attrs = as_list(entity.get("attributes"))
            if len(attrs) <= max_attrs:
                continue
            keyed = [(idx, attr) for idx, attr in enumerate(attrs) if attr_is_key(attr)]
            rest = [(idx, attr) for idx, attr in enumerate(attrs) if not attr_is_key(attr)]
            rest.sort(key=lambda item: (attr_priority(item[1]), -item[0]), reverse=True)
            selected = [] if max_attrs == 0 else keyed[:max_attrs]
            remaining_slots = max_attrs - len(selected)
            if remaining_slots > 0:
                selected.extend(rest[:remaining_slots])
            selected_indexes = {idx for idx, _ in selected}
            kept = [attr for idx, attr in enumerate(attrs) if idx in selected_indexes]
            omitted = [attr_name(attr) for idx, attr in enumerate(attrs) if idx not in selected_indexes and attr_name(attr)]
            if omitted:
                eid = str(entity.get("id") or entity.get("name") or "entity")
                notes["omittedAttributes"][eid] = omitted
            entity["attributes"] = kept

    diagram["relationships"] = relationships
    if notes["omittedEntities"] or notes["omittedRelationships"] or notes["omittedAttributes"]:
        diagram["layoutNotes"] = notes


def adjacent(a: str, b: str, relationships: list[dict[str, Any]]) -> bool:
    for rel in relationships:
        src = str(rel.get("from", "")).strip()
        dst = str(rel.get("to", "")).strip()
        if {src, dst} == {a, b}:
            return True
    return False


def place_entities(diagram: dict[str, Any]) -> tuple[float, float, dict[str, tuple[float, float]]]:
    entities = as_list(diagram.get("entities"))
    relationships = as_list(diagram.get("relationships"))
    attr_count = sum(len(as_list(e.get("attributes"))) for e in entities if isinstance(e, dict))
    layout = diagram.setdefault("layout", {})
    default_w, default_h = page_defaults(len(entities), attr_count)
    page_w = float(layout.get("pageWidth") or default_w)
    page_h = float(layout.get("pageHeight") or default_h)
    layout["pageWidth"] = page_w
    layout["pageHeight"] = page_h

    positions: dict[str, tuple[float, float]] = {}
    for i, entity in enumerate(entities):
        if not isinstance(entity, dict):
            continue
        eid = entity_id(entity, i)
        if has_xy(entity):
            positions[eid] = (float(entity["x"]), float(entity["y"]))

    missing = [e for e in entities if isinstance(e, dict) and entity_id(e, entities.index(e)) not in positions]
    if not missing:
        return page_w, page_h, positions

    ids = [entity_id(e, i) for i, e in enumerate(entities) if isinstance(e, dict)]
    if len(ids) == 1:
        positions[ids[0]] = (page_w / 2, page_h - 0.8)
    elif len(ids) <= 4 or not relationships:
        cols = math.ceil(math.sqrt(len(ids)))
        rows = math.ceil(len(ids) / cols)
        x_gap = page_w / (cols + 1)
        y_gap = page_h / (rows + 1)
        for idx, eid in enumerate(ids):
            if eid in positions:
                continue
            col = idx % cols
            row = idx // cols
            positions[eid] = (x_gap * (col + 1), page_h - y_gap * (row + 1))
    else:
        ordered = [eid for eid in sort_hubs([e for e in entities if isinstance(e, dict)], relationships) if eid in ids]
        ordered.extend(eid for eid in ids if eid not in ordered)
        center_x = page_w / 2
        center_y = page_h / 2
        degrees = build_degrees([e for e in entities if isinstance(e, dict)], relationships)
        hub_id = ordered[0] if ordered else ""
        hub_degree = degrees.get(hub_id, 0)
        if hub_id and hub_degree >= max(3, math.ceil(len(relationships) * 0.45)):
            positions.setdefault(hub_id, (center_x, center_y))
            spokes = [eid for eid in ordered if eid != hub_id]
            radius_x = max(2.85, min(page_w * 0.38, page_w / 2 - 0.95))
            radius_y = max(1.75, min(page_h * 0.34, page_h / 2 - 0.62))
            for eid, angle in zip(spokes, hub_spoke_angles(len(spokes))):
                if eid in positions:
                    continue
                x = center_x + math.cos(angle) * radius_x
                y = center_y + math.sin(angle) * radius_y
                positions[eid] = (
                    min(max(x, ENTITY_W / 2 + 0.35), page_w - ENTITY_W / 2 - 0.35),
                    min(max(y, ENTITY_H / 2 + 0.35), page_h - ENTITY_H / 2 - 0.35),
                )
        else:
            radius_x = max(2.25, min(page_w * 0.34, page_w / 2 - 1.05))
            radius_y = max(1.45, min(page_h * 0.31, page_h / 2 - 0.72))
            for eid, angle in zip(ordered, overview_ring_angles(len(ordered))):
                if eid in positions:
                    continue
                x = center_x + math.cos(angle) * radius_x
                y = center_y + math.sin(angle) * radius_y
                positions[eid] = (
                    min(max(x, ENTITY_W / 2 + 0.35), page_w - ENTITY_W / 2 - 0.35),
                    min(max(y, ENTITY_H / 2 + 0.35), page_h - ENTITY_H / 2 - 0.35),
                )

    for i, entity in enumerate(entities):
        if not isinstance(entity, dict):
            continue
        eid = entity_id(entity, i)
        x, y = positions[eid]
        entity["id"] = eid
        entity["x"] = round(x, 3)
        entity["y"] = round(y, 3)
    return page_w, page_h, positions


def place_relationships(
    diagram: dict[str, Any],
    positions: dict[str, tuple[float, float]],
    occupied: list[Box],
    page_w: float,
    page_h: float,
) -> list[Box]:
    placed: list[Box] = []
    placed_segments: list[tuple[tuple[float, float], tuple[float, float]]] = []
    for idx, rel in enumerate(as_list(diagram.get("relationships"))):
        if not isinstance(rel, dict):
            continue
        src = str(rel.get("from", "")).strip()
        dst = str(rel.get("to", "")).strip()
        if src not in positions or dst not in positions:
            continue
        sx, sy = positions[src]
        tx, ty = positions[dst]
        if has_xy(rel):
            x, y = float(rel["x"]), float(rel["y"])
        else:
            dx = tx - sx
            dy = ty - sy
            length = math.hypot(dx, dy) or 1.0
            px = -dy / length
            py = dx / length
            candidates: list[tuple[float, float, float]] = []
            for t in (0.50, 0.42, 0.58, 0.34, 0.66):
                base_x = sx + dx * t
                base_y = sy + dy * t
                for offset in (0.0, 0.38, -0.38, 0.68, -0.68, 0.98, -0.98, 1.28, -1.28, 1.68, -1.68, 2.08, -2.08):
                    preference = abs(t - 0.50) * 3.0 + abs(offset) * 0.6
                    candidates.append((base_x + px * offset, base_y + py * offset, preference))
            for radius in (0.95, 1.25, 1.55, 1.9, 2.25, 2.65):
                for delta_deg in (0, -18, 18, -34, 34, -52, 52, -76, 76):
                    angle = math.atan2(dy, dx) + math.radians(delta_deg)
                    base_x = sx + math.cos(angle) * radius
                    base_y = sy + math.sin(angle) * radius
                    preference = abs(delta_deg) / 45.0 + abs(radius - min(max(length * 0.42, 1.05), 1.8)) * 0.4
                    candidates.append((base_x, base_y, preference))

            def relationship_score(candidate: tuple[float, float, float]) -> float:
                cx, cy, preference = candidate
                box = Box(cx, cy, REL_W, REL_H, "relationship")
                overlap = sum(bbox_overlap(box, other) for other in occupied + placed)
                outside = page_outside_penalty(cx, cy, REL_W, REL_H, page_w, page_h)
                crossings = 0
                src_box = Box(sx, sy, ENTITY_W, ENTITY_H, "entity")
                dst_box = Box(tx, ty, ENTITY_W, ENTITY_H, "entity")
                obstacles = occupied + placed
                crossings += segment_crossing_count(boundary_point(src_box, box), boundary_point(box, src_box), obstacles, (src_box, box))
                crossings += segment_crossing_count(boundary_point(dst_box, box), boundary_point(box, dst_box), obstacles, (dst_box, box))
                segment_hits = sum(1 for start, end in placed_segments if segment_intersects_box(start, end, box.inflated(0.03)))
                return overlap * 10000 + crossings * 7500 + segment_hits * 9000 + outside * 1000 + preference

            best = min(candidates, key=relationship_score)
            x, y, _ = best
        rel["x"] = round(x, 3)
        rel["y"] = round(y, 3)
        box = Box(x, y, REL_W, REL_H, "relationship")
        placed.append(box)
        src_box = Box(sx, sy, ENTITY_W, ENTITY_H, "entity")
        dst_box = Box(tx, ty, ENTITY_W, ENTITY_H, "entity")
        placed_segments.append((boundary_point(src_box, box), boundary_point(box, src_box)))
        placed_segments.append((boundary_point(dst_box, box), boundary_point(box, dst_box)))
    occupied.extend(placed)
    return placed


def candidate_positions(
    ex: float,
    ey: float,
    page_w: float,
    page_h: float,
    index: int,
    count: int,
) -> list[tuple[float, float, float]]:
    cx, cy = page_w / 2, page_h / 2
    out_angle = math.atan2(ey - cy, ex - cx)
    if abs(ex - cx) < page_w * 0.12 and ey >= cy:
        out_angle = math.pi / 2
    elif abs(ex - cx) < page_w * 0.12 and ey < cy:
        out_angle = -math.pi / 2

    angles: list[float] = []
    for delta_deg in (0, -25, 25, -50, 50, -75, 75, -105, 105, 140, -140, 180):
        angles.append(out_angle + math.radians(delta_deg))
    for k in range(24):
        angles.append(2 * math.pi * k / 24)

    positions: list[tuple[float, float, float]] = []
    for radius in (1.05, 1.32, 1.62, 1.95, 2.28, 2.65):
        for angle in angles:
            x = ex + math.cos(angle) * radius
            y = ey + math.sin(angle) * radius
            positions.append((x, y, angle))
    return positions


def angle_distance(a: float, b: float) -> float:
    return abs(math.atan2(math.sin(a - b), math.cos(a - b)))


def place_attributes(diagram: dict[str, Any], page_w: float, page_h: float, occupied: list[Box]) -> None:
    entities = as_list(diagram.get("entities"))
    center_x, center_y = page_w / 2, page_h / 2
    for eidx, entity in enumerate(entities):
        if not isinstance(entity, dict):
            continue
        ex = float(entity["x"])
        ey = float(entity["y"])
        attrs = as_list(entity.get("attributes"))
        out_angle = math.atan2(ey - center_y, ex - center_x)
        for aidx, attr in enumerate(attrs):
            if isinstance(attr, str):
                attr_obj: dict[str, Any] = {"name": attr}
                attrs[aidx] = attr_obj
            elif isinstance(attr, dict):
                attr_obj = attr
            else:
                continue
            if attr_obj.get("dx") is not None and attr_obj.get("dy") is not None:
                ax = ex + float(attr_obj["dx"])
                ay = ey + float(attr_obj["dy"])
                occupied.append(Box(ax, ay, ATTR_W, ATTR_H, "attribute"))
                continue

            best: tuple[float, float, float] | None = None
            best_score = float("inf")
            for x, y, angle in candidate_positions(ex, ey, page_w, page_h, aidx, len(attrs)):
                box = Box(x, y, ATTR_W, ATTR_H, "attribute")
                overlap = sum(bbox_overlap(box, other) for other in occupied)
                outside = page_outside_penalty(x, y, ATTR_W, ATTR_H, page_w, page_h) * 20
                prefer_outward = angle_distance(angle, out_angle)
                distance = math.hypot(x - ex, y - ey)
                entity_box = Box(ex, ey, ENTITY_W, ENTITY_H, "entity")
                crossings = segment_crossing_count(boundary_point(entity_box, box), boundary_point(box, entity_box), occupied, (entity_box, box))
                score = overlap * 2500 + crossings * 1800 + outside * 100 + prefer_outward * 2.0 + distance * 0.2
                if score < best_score:
                    best_score = score
                    best = (x, y, angle)
            if best is None:
                continue
            ax, ay, _ = best
            attr_obj["dx"] = round(ax - ex, 3)
            attr_obj["dy"] = round(ay - ey, 3)
            occupied.append(Box(ax, ay, ATTR_W, ATTR_H, "attribute"))
        entity["attributes"] = attrs


def label_candidates(
    entity_x: float,
    entity_y: float,
    relation_x: float,
    relation_y: float,
    side: float,
) -> list[tuple[float, float, float]]:
    dx = relation_x - entity_x
    dy = relation_y - entity_y
    length = math.hypot(dx, dy)
    if length < 0.001:
        return [(entity_x, entity_y, 0.0)]

    ux = dx / length
    uy = dy / length
    px = -uy
    py = ux
    entity_exit = boundary_distance(ux, uy, ENTITY_W, ENTITY_H)
    relation_entry = boundary_distance(-ux, -uy, REL_W, REL_H)
    label_half = projected_half_width(ux, uy, LABEL_W, LABEL_H)
    min_distance = entity_exit + label_half + 0.05
    max_distance = length - relation_entry - label_half - 0.05

    if max_distance >= min_distance:
        distances = [
            min_distance,
            (min_distance + max_distance) / 2,
            max_distance,
            min_distance + (max_distance - min_distance) * 0.32,
            min_distance + (max_distance - min_distance) * 0.68,
        ]
    else:
        distances = [
            max(0.12, length * 0.35),
            max(0.12, length * 0.50),
            max(0.12, length * 0.65),
            min(length + 0.18, entity_exit + label_half + 0.12),
        ]

    offsets = [
        0.0,
        0.20 * side,
        -0.20 * side,
        0.34 * side,
        -0.34 * side,
        0.52 * side,
        -0.52 * side,
        0.72 * side,
        -0.72 * side,
        0.92 * side,
        -0.92 * side,
    ]
    candidates: list[tuple[float, float, float]] = []
    for distance in distances:
        for offset in offsets:
            x = entity_x + ux * distance + px * offset
            y = entity_y + uy * distance + py * offset
            preference = abs(offset - (0.20 * side)) + abs(distance - max(min_distance, min(length * 0.50, max_distance if max_distance >= min_distance else length)))
            candidates.append((x, y, preference))
    return candidates


def place_cardinality_labels(
    diagram: dict[str, Any],
    positions: dict[str, tuple[float, float]],
    page_w: float,
    page_h: float,
    occupied: list[Box],
) -> None:
    labels: list[Box] = []

    def choose_label(entity_x: float, entity_y: float, relation_x: float, relation_y: float, side: float) -> tuple[float, float]:
        best: tuple[float, float] | None = None
        best_score = float("inf")
        for x, y, preference in label_candidates(entity_x, entity_y, relation_x, relation_y, side):
            box = Box(x, y, LABEL_W, LABEL_H, "label")
            overlap = sum(bbox_overlap(box, other, pad=0.025) for other in occupied + labels)
            outside = 0.0
            if x < LABEL_W / 2:
                outside += (LABEL_W / 2 - x) * 20
            if x > page_w - LABEL_W / 2:
                outside += (x - (page_w - LABEL_W / 2)) * 20
            if y < LABEL_H / 2:
                outside += (LABEL_H / 2 - y) * 20
            if y > page_h - LABEL_H / 2:
                outside += (y - (page_h - LABEL_H / 2)) * 20
            score = overlap * 10000 + outside * 100 + preference
            if score < best_score:
                best_score = score
                best = (x, y)
        return best if best is not None else (entity_x, entity_y)

    for rel in as_list(diagram.get("relationships")):
        if not isinstance(rel, dict):
            continue
        src = str(rel.get("from", "")).strip()
        dst = str(rel.get("to", "")).strip()
        rx = float(rel.get("x", 0.0))
        ry = float(rel.get("y", 0.0))
        if src in positions and rel.get("fromCardinality"):
            sx, sy = positions[src]
            lx, ly = choose_label(sx, sy, rx, ry, 1.0)
            rel["fromLabelX"] = round(lx, 3)
            rel["fromLabelY"] = round(ly, 3)
            labels.append(Box(lx, ly, LABEL_W, LABEL_H, "label"))
        if dst in positions and rel.get("toCardinality"):
            tx, ty = positions[dst]
            lx, ly = choose_label(tx, ty, rx, ry, -1.0)
            rel["toLabelX"] = round(lx, 3)
            rel["toLabelY"] = round(ly, 3)
            labels.append(Box(lx, ly, LABEL_W, LABEL_H, "label"))

    occupied.extend(labels)


def layout_overview(diagram: dict[str, Any]) -> None:
    apply_overview_limits(diagram)
    page_w, page_h, positions = place_entities(diagram)
    occupied = [Box(x, y, ENTITY_W, ENTITY_H, "entity") for x, y in positions.values()]
    place_relationships(diagram, positions, occupied, page_w, page_h)
    place_attributes(diagram, page_w, page_h, occupied)
    place_cardinality_labels(diagram, positions, page_w, page_h, occupied)


def layout_single_entity(diagram: dict[str, Any]) -> None:
    entity = diagram.get("entity")
    if not isinstance(entity, dict):
        entities = as_list(diagram.get("entities"))
        entity = entities[0] if entities and isinstance(entities[0], dict) else {}
        diagram["entity"] = entity
    attrs = as_list(entity.get("attributes"))
    layout = diagram.setdefault("layout", {})
    radius_x = max(2.15, min(3.55, 1.85 + len(attrs) * 0.16))
    radius_y = max(1.45, min(2.25, 1.15 + len(attrs) * 0.10))
    page_w = float(layout.get("pageWidth") or max(6.0, 2.2 + radius_x * 2))
    page_h = float(layout.get("pageHeight") or max(3.8, 1.85 + radius_y * 2))
    layout["pageWidth"] = page_w
    layout["pageHeight"] = page_h
    layout.setdefault("entityX", round(page_w / 2, 3))
    layout.setdefault("entityY", round(max(0.8, page_h * 0.28), 3))

    ex = float(layout["entityX"])
    ey = float(layout["entityY"])
    entity_box = Box(ex, ey, 1.35, 0.48, "entity")
    occupied = [entity_box]
    fixed_attrs: list[Any] = []
    for idx, attr in enumerate(attrs):
        if isinstance(attr, str):
            attr_obj = {"name": attr}
        elif isinstance(attr, dict):
            attr_obj = dict(attr)
        else:
            continue
        if attr_obj.get("dx") is None or attr_obj.get("dy") is None:
            if len(attrs) == 1:
                nominal_angle = math.radians(90)
            else:
                start_deg, end_deg = 172.0, 8.0
                nominal_angle = math.radians(start_deg + (end_deg - start_deg) * idx / max(1, len(attrs) - 1))
            candidates: list[tuple[float, float, float]] = []
            for radius_scale in (1.0, 1.16, 1.32):
                for delta_deg in (0, -10, 10, -20, 20, -32, 32, -46, 46):
                    angle = nominal_angle + math.radians(delta_deg)
                    x = ex + math.cos(angle) * radius_x * radius_scale
                    y = ey + math.sin(angle) * radius_y * radius_scale
                    preference = angle_distance(angle, nominal_angle) + abs(radius_scale - 1.0) * 0.9
                    candidates.append((x, y, preference))

            def attribute_score(candidate: tuple[float, float, float]) -> float:
                x, y, preference = candidate
                box = Box(x, y, ATTR_W, ATTR_H, "attribute")
                overlap = sum(bbox_overlap(box, other) for other in occupied)
                outside = page_outside_penalty(x, y, ATTR_W, ATTR_H, page_w, page_h)
                distance = math.hypot(x - ex, y - ey)
                crossings = segment_crossing_count(boundary_point(entity_box, box), boundary_point(box, entity_box), occupied, (entity_box, box))
                return overlap * 10000 + crossings * 6000 + outside * 1000 + preference * 5 + distance * 0.05

            ax, ay, _ = min(candidates, key=attribute_score)
            attr_obj["dx"] = round(ax - ex, 3)
            attr_obj["dy"] = round(ay - ey, 3)
        ax = ex + float(attr_obj["dx"])
        ay = ey + float(attr_obj["dy"])
        occupied.append(Box(ax, ay, ATTR_W, ATTR_H, "attribute"))
        fixed_attrs.append(attr_obj)
    entity["attributes"] = fixed_attrs


def apply_cli_limit_overrides(
    diagram: dict[str, Any],
    max_entities: int | None,
    max_attributes_per_entity: int | None,
    max_relationships: int | None,
) -> None:
    overrides = {
        "maxEntities": max_entities,
        "maxAttributesPerEntity": max_attributes_per_entity,
        "maxRelationships": max_relationships,
    }
    cleaned = {key: value for key, value in overrides.items() if value is not None}
    if not cleaned:
        return
    limits = diagram.setdefault("limits", {})
    if not isinstance(limits, dict):
        limits = {}
        diagram["limits"] = limits
    limits.update(cleaned)


def main() -> int:
    parser = argparse.ArgumentParser(description="Layout thesis-style Chen ER JSON for Visio rendering.")
    parser.add_argument("input", help="Input logical ER JSON.")
    parser.add_argument("--out", required=True, help="Output positioned ER JSON.")
    parser.add_argument("--max-entities", type=int, help="Override overview maxEntities.")
    parser.add_argument("--max-attributes-per-entity", type=int, help="Override overview maxAttributesPerEntity.")
    parser.add_argument("--max-relationships", type=int, help="Override overview maxRelationships.")
    args = parser.parse_args()

    source = Path(args.input)
    target = Path(args.out)
    diagram = json.loads(source.read_text(encoding="utf-8"))
    output = copy.deepcopy(diagram)
    apply_cli_limit_overrides(output, args.max_entities, args.max_attributes_per_entity, args.max_relationships)
    diagram_type = str(output.get("diagramType") or "overview").lower()
    if diagram_type in {"single", "single_entity", "entity"}:
        layout_single_entity(output)
    elif diagram_type in {"overview", "total", "general", "chen"}:
        layout_overview(output)
    else:
        raise SystemExit(f"Unsupported diagramType: {diagram_type}")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"input": str(source), "out": str(target), "diagramType": diagram_type}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
