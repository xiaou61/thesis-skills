# Visio Diagram Workflow

Use this workflow when a thesis needs editable `.vsdx` ER diagrams instead of only `.drawio` templates.

The ER style follows common thesis examples:

- single entity ER: one rectangle entity with oval attributes
- overview ER: multiple rectangle entities, oval attributes, diamond relationships, and `1/m/n` cardinality labels

## Single Entity ER Input

```json
{
  "diagramType": "single_entity",
  "title": "农户信息E-R图",
  "entity": {
    "name": "农户信息",
    "attributes": [
      {"name": "农户账号", "key": true},
      "农户姓名",
      "性别",
      "农户电话",
      "头像"
    ]
  }
}
```

Optional attribute objects may include `dx` and `dy` to control their positions relative to the entity rectangle.
`title` is metadata by default because Word usually carries the figure caption outside the image. Set `layout.showTitle` to `true` only when the title should be drawn inside the Visio page.

## Overview ER Input

```json
{
  "diagramType": "overview",
  "title": "系统总体E-R图",
  "limits": {
    "maxEntities": 8,
    "maxAttributesPerEntity": 4,
    "maxRelationships": 8
  },
  "layout": {
    "pageWidth": 10.5,
    "pageHeight": 6
  },
  "entities": [
    {
      "id": "user",
      "name": "用户",
      "x": 5.2,
      "y": 3.3,
      "attributes": [
        {"name": "用户账号", "key": true, "dx": -1.2, "dy": 0.85},
        {"name": "用户姓名", "dx": -0.3, "dy": 1.05},
        {"name": "用户电话", "dx": 0.6, "dy": 1.05}
      ]
    }
  ],
  "relationships": [
    {
      "name": "管理",
      "from": "admin",
      "to": "user",
      "fromCardinality": "1",
      "toCardinality": "m",
      "x": 3.8,
      "y": 3.3
    }
  ]
}
```

Entity `x/y` and relationship `x/y` are Visio page coordinates in inches. Use them for thesis figures where the layout needs to be visually controlled.

For overview diagrams, keep the picture intentionally sparse:

- `maxEntities`: keep only the most central entities in the overview
- `maxAttributesPerEntity`: show primary keys and several representative attributes
- `maxRelationships`: keep the main relationship lines

The layout script records omitted entities, relationships, and attributes in `layoutNotes`. Use single entity ER diagrams and database table design sections for the omitted detail.
For crowded thesis overview ER diagrams, use `maxAttributesPerEntity: 3` and create separate single-entity ER diagrams for the full fields.
The layout command also accepts `--max-entities`, `--max-attributes-per-entity`, and `--max-relationships` for temporary preview variants without editing the source JSON.

## Generate Editable Visio Output

Run from the repository root:

```powershell
python .\thesis-standardizer\scripts\layout_er_diagram.py `
  .\paper-context\evidence\er-model.json `
  --out .\paper-context\evidence\er-model.positioned.json `
  --max-attributes-per-entity 4

powershell -ExecutionPolicy Bypass -File .\thesis-standardizer\scripts\generate_visio_er_diagram.ps1 `
  -InputJson .\paper-context\evidence\er-model.positioned.json `
  -OutputVsdx .\thesis-ai-standard\visio\er-diagram.vsdx `
  -OutputPng .\thesis-ai-standard\exports\er-diagram.png
```

The script:

- opens Microsoft Visio through COM automation
- uses Visio basic masters for rectangles, ellipses, and diamonds when available
- falls back to primitive Visio drawing calls if a master is missing
- respects precomputed entity, attribute, relationship, and cardinality-label positions
- writes an editable `.vsdx`
- exports a `.png` preview for Word insertion
- prints a JSON summary with entity, attribute, and relationship counts

Use `-Visible -KeepOpen` when you want to watch Visio draw and keep the file open for manual editing.

## Figure Registry

For generated Visio diagrams, register the figure with:

```yaml
type: "er_diagram"
source_kind: "visio"
source_file: "thesis-ai-standard/visio/er-diagram.vsdx"
export_file: "thesis-ai-standard/exports/er-diagram.png"
```

The source `.vsdx` is the editable artifact. The exported `.png` is the figure image used in Word.
