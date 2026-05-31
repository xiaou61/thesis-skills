# Chapter 4 Database Workflow

Use this workflow before drafting Chapter 4 for system-design theses.

## Hard Rule

Chapter 4 must not skip database/data-object design silently. Do one of these:

1. If database evidence exists, generate:
   - one overview E-R diagram
   - one single-entity E-R diagram per core entity
   - one three-line database table per entity
   - a registry entry for every figure and table
2. If business database evidence is missing but the project has real structured artifacts such as YAML configuration, JSON evidence, JSONL revision traces, Markdown registries, generated model files, or logs, create a clearly labeled data-object model from those artifacts and generate the same overview E-R, single-entity E-R, and three-line table assets. In the prose, state that this is a configuration/data-object model, not a physical business database.
3. If neither business database evidence nor structured project data exists, stop Chapter 4 drafting and create an evidence gap asking for schema, entity classes, migrations, SQL, screenshots, or a confirmed data-object list.

## Input Model

Create or fill `paper-context/evidence/database-design-model.yaml`:

```yaml
entities:
  - id: user
    name: 用户
    table: user
    purpose: 存储系统用户账号、联系方式和状态
    evidence: src/main/java/.../User.java
    fields:
      - {name: id, type: bigint, key: true, nullable: false, description: 用户编号}
      - {name: username, type: varchar(50), nullable: false, description: 用户账号}
      - {name: phone, type: varchar(20), nullable: true, description: 联系电话}
relationships:
  - {name: 下单, from: user, to: order, fromCardinality: "1", toCardinality: "m"}
```

Fields may come from entity classes, SQL, migrations, ORM models, table screenshots, user-provided schema notes, or clearly identified structured project artifacts. Do not import demo tables from `tmp/` unless the user explicitly says the demo is the target system.

## Generate Assets

```powershell
python .\scripts\build_chapter4_database_assets.py `
  .\paper-context\evidence\database-design-model.yaml `
  --out .\paper-context\database-design `
  --table-start 1 `
  --figure-start 2
```

This creates:

- `paper-context/database-design/er/er-overview.json`
- `paper-context/database-design/er/single-entity/*.json`
- `paper-context/database-design/tables/table-4-*.xml`
- `paper-context/database-design/database-tables.md`
- `paper-context/database-design/figure-registry-fragment.yaml`
- `paper-context/database-design/chapter-4-database-section.md`

## Render Visio ER Diagrams

For the overview:

```powershell
python .\scripts\layout_er_diagram.py `
  .\paper-context\database-design\er\er-overview.json `
  --out .\paper-context\database-design\er\er-overview.positioned.json

powershell -ExecutionPolicy Bypass -File .\scripts\generate_visio_er_diagram.ps1 `
  -InputJson .\paper-context\database-design\er\er-overview.positioned.json `
  -OutputVsdx .\paper-context\figures\figure-4-2-er-overview.vsdx `
  -OutputPng .\paper-context\figures\figure-4-2-er-overview.png
```

For each single entity JSON, run the same layout and Visio commands and number figures after the overview.

After layout, run `scripts/check_er_layout.py` on every positioned JSON. Fix layout or reduce overview limits until every check reports `overlapPairs: 0` and `connectorCrossings: 0`. If a high-degree entity creates many lines from one area, use the hub-spoke overview layout, set overview attributes to `0`, and rely on single-entity E-R diagrams for fields.

## Drafting Guidance

Chapter 4 should include:

- a paragraph explaining whether the design is a business database model or a structured data-object model
- the overview E-R figure
- short paragraphs for each core entity
- single-entity E-R figures for important entities
- three-line tables for all database/data-object tables used in the thesis scope

Keep overview E-R sparse. The default overview limit is 8 entities, 8 relationships, and 0 attributes per entity for normal system theses. Put fields in single-entity E-R figures and database tables. Single-entity figures should keep only core fields in the oval layout and leave full field lists to the three-line tables.
