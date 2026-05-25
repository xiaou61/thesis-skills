# Chapter 4 Database Workflow

Use this workflow before drafting Chapter 4 for system-design theses.

## Hard Rule

Chapter 4 must not skip database design silently. Do one of these:

1. If database evidence exists, generate:
   - one overview E-R diagram
   - one single-entity E-R diagram per core entity
   - one three-line database table per entity
   - a registry entry for every figure and table
2. If database evidence is missing, stop Chapter 4 drafting and create an evidence gap asking for schema, entity classes, migrations, SQL, or screenshots. Do not replace database design with unrelated configuration tables.

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

Fields may come from entity classes, SQL, migrations, ORM models, table screenshots, or user-provided schema notes.

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

After layout, run `scripts/check_er_layout.py` on every positioned JSON. Fix layout or reduce overview limits until every check reports `overlapPairs: 0`.

## Drafting Guidance

Chapter 4 should include:

- a paragraph explaining the conceptual database design
- the overview E-R figure
- short paragraphs for each core entity
- single-entity E-R figures for important entities
- three-line tables for all database tables used in the thesis scope

Keep overview E-R sparse. The default overview limit is 8 entities, 8 relationships, and 3 representative attributes per entity. Put complete fields in single-entity E-R figures and database tables.
