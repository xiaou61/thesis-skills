#!/usr/bin/env python3
"""Build Chapter 4 database-design assets from entity evidence.

The script turns a small database design model into the assets a system-design
thesis normally needs in Chapter 4:

- overview ER logical JSON
- one single-entity ER logical JSON per entity
- one three-line table OOXML snippet per entity
- a Markdown summary of database tables
- a figure/table registry fragment
- a draft Chapter 4 database-design section
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from create_three_line_table import build_caption_xml, build_table_xml


def load_model(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        try:
            import yaml  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise SystemExit(f"PyYAML is required for YAML input: {exc}") from exc
        data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise SystemExit("Database design model must be an object.")
    if isinstance(data.get("database_design"), dict):
        data = data["database_design"]
    return data


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    result = str(value).strip()
    return result if result else default


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "是", "主键"}


def slug(value: str, fallback: str) -> str:
    raw = value.strip().lower()
    raw = re.sub(r"[^0-9a-zA-Z_-]+", "-", raw).strip("-")
    return raw or fallback


def field_name(field: Any) -> str:
    if isinstance(field, str):
        return field.strip()
    if isinstance(field, dict):
        return text(field.get("name") or field.get("field") or field.get("column"))
    return ""


def normalize_field(field: Any, index: int) -> dict[str, Any]:
    if isinstance(field, str):
        return {
            "name": field,
            "type": "",
            "description": field,
            "key": index == 0,
            "nullable": "未说明",
        }
    if not isinstance(field, dict):
        return {
            "name": f"field_{index + 1}",
            "type": "",
            "description": "",
            "key": index == 0,
            "nullable": "未说明",
        }
    name = field_name(field) or f"field_{index + 1}"
    key = truthy(field.get("key")) or truthy(field.get("pk")) or truthy(field.get("primary"))
    return {
        "name": name,
        "type": text(field.get("type") or field.get("data_type")),
        "description": text(field.get("description") or field.get("comment") or field.get("purpose"), name),
        "key": key,
        "nullable": text(field.get("nullable") or field.get("null") or field.get("allow_null"), "未说明"),
        "default": text(field.get("default"), ""),
        "evidence": text(field.get("evidence"), ""),
    }


def normalize_entity(entity: Any, index: int) -> dict[str, Any]:
    if not isinstance(entity, dict):
        name = text(entity, f"实体{index + 1}")
        entity = {"name": name}
    name = text(entity.get("name") or entity.get("title"), f"实体{index + 1}")
    eid = text(entity.get("id"), slug(text(entity.get("table"), name), f"entity_{index + 1}"))
    fields = [normalize_field(item, idx) for idx, item in enumerate(as_list(entity.get("fields") or entity.get("attributes") or entity.get("columns")))]
    if fields and not any(truthy(item.get("key")) for item in fields):
        fields[0]["key"] = True
    return {
        "id": eid,
        "name": name,
        "table": text(entity.get("table"), eid),
        "purpose": text(entity.get("purpose") or entity.get("description"), f"{name}信息存储"),
        "evidence": text(entity.get("evidence"), ""),
        "fields": fields,
        "priority": entity.get("priority", index),
    }


def normalize_relationship(item: Any, index: int) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    source = text(item.get("from") or item.get("source") or item.get("left"))
    target = text(item.get("to") or item.get("target") or item.get("right"))
    if not source or not target:
        return None
    return {
        "name": text(item.get("name") or item.get("relation"), f"关系{index + 1}"),
        "from": source,
        "to": target,
        "fromCardinality": text(item.get("fromCardinality") or item.get("from_cardinality"), "1"),
        "toCardinality": text(item.get("toCardinality") or item.get("to_cardinality"), "m"),
        "priority": item.get("priority", index),
    }


def build_overview(model: dict[str, Any], entities: list[dict[str, Any]], relationships: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "diagramType": "overview",
        "title": text(model.get("overview_title"), "系统总体E-R图"),
        "limits": {
            "maxEntities": int(model.get("max_overview_entities", 8)),
            "maxAttributesPerEntity": int(model.get("max_overview_attributes", 3)),
            "maxRelationships": int(model.get("max_overview_relationships", 8)),
        },
        "entities": [
            {
                "id": item["id"],
                "name": item["name"],
                "table": item["table"],
                "priority": item.get("priority", index),
                "attributes": [
                    {
                        "name": field["description"] if field["description"] != field["name"] else field["name"],
                        "key": truthy(field.get("key")),
                        "priority": 100 if truthy(field.get("key")) else max(0, 20 - field_index),
                    }
                    for field_index, field in enumerate(item["fields"])
                ],
            }
            for index, item in enumerate(entities)
        ],
        "relationships": relationships,
    }


def build_single_entity(entity: dict[str, Any]) -> dict[str, Any]:
    return {
        "diagramType": "single_entity",
        "title": f"{entity['name']}E-R图",
        "entity": {
            "name": entity["name"],
            "attributes": [
                {
                    "name": field["description"] if field["description"] != field["name"] else field["name"],
                    "key": truthy(field.get("key")),
                    "field": field["name"],
                    "type": field["type"],
                }
                for field in entity["fields"]
            ],
        },
    }


def table_rows(entity: dict[str, Any]) -> list[list[str]]:
    rows = []
    for field in entity["fields"]:
        rows.append(
            [
                field["name"],
                field["type"] or "未说明",
                "是" if truthy(field.get("key")) else "否",
                str(field["nullable"]),
                field["description"],
            ]
        )
    return rows


def write_table_xml(path: Path, caption: str, entity: dict[str, Any]) -> None:
    headers = ["字段名", "类型", "主键", "允许空", "说明"]
    path.write_text(build_caption_xml(caption) + "\n" + build_table_xml(headers, table_rows(entity)), encoding="utf-8")


def render_tables_markdown(entities: list[dict[str, Any]], table_start: int) -> str:
    lines = ["# Chapter 4 Database Tables", ""]
    for index, entity in enumerate(entities, start=table_start):
        lines.append(f"## 表4-{index} {entity['name']}表")
        lines.append("")
        lines.append("| 字段名 | 类型 | 主键 | 允许空 | 说明 |")
        lines.append("| --- | --- | --- | --- | --- |")
        for row in table_rows(entity):
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")
    return "\n".join(lines)


def render_registry_fragment(entities: list[dict[str, Any]], table_start: int, figure_start: int, overview: bool) -> str:
    lines = ["figures:"]
    current_figure = figure_start
    if overview:
        lines.extend(
            [
                f"  - id: \"图4-{current_figure}\"",
                "    title: \"系统总体E-R图\"",
                "    chapter: \"4\"",
                "    type: \"er_diagram\"",
                "    source_kind: \"visio\"",
                "    source_file: \"paper-context/figures/figure-4-%d-er-overview.vsdx\"" % current_figure,
                "    export_file: \"paper-context/figures/figure-4-%d-er-overview.png\"" % current_figure,
                "    status: \"planned\"",
            ]
        )
        current_figure += 1
    for entity in entities:
        safe = slug(entity["id"], f"entity-{current_figure}")
        lines.extend(
            [
                f"  - id: \"图4-{current_figure}\"",
                f"    title: \"{entity['name']}E-R图\"",
                "    chapter: \"4\"",
                "    type: \"er_diagram\"",
                "    source_kind: \"visio\"",
                f"    source_file: \"paper-context/figures/figure-4-{current_figure}-{safe}.vsdx\"",
                f"    export_file: \"paper-context/figures/figure-4-{current_figure}-{safe}.png\"",
                "    status: \"planned\"",
            ]
        )
        current_figure += 1

    lines.extend(["", "tables:"])
    for offset, entity in enumerate(entities):
        table_no = table_start + offset
        safe = slug(entity["id"], f"entity-{offset + 1}")
        lines.extend(
            [
                f"  - id: \"表4-{table_no}\"",
                f"    title: \"{entity['name']}表\"",
                "    chapter: \"4\"",
                "    type: \"database_schema\"",
                f"    source_file: \"paper-context/tables/table-4-{table_no}-{safe}.xml\"",
                "    status: \"planned\"",
            ]
        )
    return "\n".join(lines) + "\n"


def render_chapter_section(entities: list[dict[str, Any]], relationships: list[dict[str, Any]], table_start: int, figure_start: int) -> str:
    lines = [
        "## 第四章数据库设计草稿片段",
        "",
        "### 数据库概念结构设计",
        "",
        "根据系统功能需求，数据库概念结构围绕核心业务对象展开。总E-R图用于展示实体之间的主要关系，单实体E-R图用于展示每个实体的完整属性，避免总图因字段过多而拥挤。",
        "",
        f"系统总体E-R图见图4-{figure_start}。",
        "",
    ]
    figure_no = figure_start + 1
    for entity in entities:
        lines.append(f"{entity['name']}实体用于{entity['purpose']}，其单实体E-R图见图4-{figure_no}。")
        figure_no += 1
    lines.extend(["", "### 数据库表设计", ""])
    for offset, entity in enumerate(entities):
        lines.append(f"{entity['name']}表用于{entity['purpose']}，字段设计见表4-{table_start + offset}。")
    if relationships:
        lines.extend(["", "实体关系说明如下："])
        for rel in relationships:
            lines.append(
                f"- {rel['name']}：{rel['from']} 与 {rel['to']} 之间为 {rel['fromCardinality']}:{rel['toCardinality']} 关系。"
            )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Chapter 4 database ER and three-line table assets.")
    parser.add_argument("model", help="Database design model JSON/YAML, or thesis-ai-spec.yaml with database_design.")
    parser.add_argument("--out", default="paper-context/database-design", help="Output directory.")
    parser.add_argument("--table-start", type=int, default=1, help="First Chapter 4 table index.")
    parser.add_argument("--figure-start", type=int, default=2, help="First Chapter 4 ER figure index after function architecture.")
    parser.add_argument("--no-overview", action="store_true", help="Do not create overview ER logical JSON.")
    args = parser.parse_args()

    model = load_model(Path(args.model))
    entities = [normalize_entity(item, index) for index, item in enumerate(as_list(model.get("entities")))]
    entities = [item for item in entities if item["fields"]]
    relationships = [
        rel
        for index, item in enumerate(as_list(model.get("relationships")))
        if (rel := normalize_relationship(item, index)) is not None
    ]

    if not entities:
        raise SystemExit(
            "No database entities with fields were found. Add database_design.entities[].fields before drafting Chapter 4."
        )

    out = Path(args.out).resolve()
    er_dir = out / "er"
    single_dir = er_dir / "single-entity"
    table_dir = out / "tables"
    er_dir.mkdir(parents=True, exist_ok=True)
    single_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)

    if not args.no_overview:
        (er_dir / "er-overview.json").write_text(
            json.dumps(build_overview(model, entities, relationships), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    for index, entity in enumerate(entities):
        safe = slug(entity["id"], f"entity-{index + 1}")
        (single_dir / f"{safe}.json").write_text(
            json.dumps(build_single_entity(entity), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        table_no = args.table_start + index
        write_table_xml(table_dir / f"table-4-{table_no}-{safe}.xml", f"表4-{table_no} {entity['name']}表", entity)

    (out / "database-tables.md").write_text(render_tables_markdown(entities, args.table_start), encoding="utf-8")
    (out / "figure-registry-fragment.yaml").write_text(
        render_registry_fragment(entities, args.table_start, args.figure_start, not args.no_overview),
        encoding="utf-8",
    )
    (out / "chapter-4-database-section.md").write_text(
        render_chapter_section(entities, relationships, args.table_start, args.figure_start),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "out": str(out),
                "entities": len(entities),
                "relationships": len(relationships),
                "overview": not args.no_overview,
                "tables": len(entities),
                "singleEntityEr": len(entities),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
