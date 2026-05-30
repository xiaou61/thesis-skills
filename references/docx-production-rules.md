# DOCX Production Rules

Use this reference for the slim skill's Word-sensitive operations.

## Baseline

1. School template first.
2. Extract OOXML facts before judging format.
3. Avoid whole-document markdown round trips for stable `.docx` files.
4. Use local scripts only for narrow, evidence-backed operations.

## Supported Operations

### Template Extraction

```powershell
python .\scripts\extract_docx_template_profile.py .\school-template.docx --out .\paper-context\template-extract
python .\scripts\generate_template_rule_overrides.py .\paper-context\template-extract\template-profile.json --out .\paper-context\template-extract\template-rule-overrides.yaml
```

### Three-Line Table XML Snippet

Use for database design tables and test case tables:

```powershell
python .\scripts\create_three_line_table.py --caption "表 4-1 用户表" --headers "字段,类型,说明" --rows "[[\"id\",\"bigint\",\"主键\"],[\"username\",\"varchar\",\"用户名\"]]"
```

If inserting into an unpacked `word/document.xml`, pass the unpacked directory and anchor arguments shown by `--help`.

For Chapter 4 database tables, prefer the batch generator:

```powershell
python .\scripts\build_chapter4_database_assets.py .\paper-context\evidence\database-design-model.yaml --out .\paper-context\database-design
```

It creates one three-line OOXML snippet per entity under `paper-context/database-design/tables/`.

### What Counts As A Three-Line Table

A thesis three-line table has exactly these visible rules by default:

- table top border: single line, normally `1.5pt`
- header-bottom border: single line, normally `0.75pt`
- table bottom border: single line, normally `1.5pt`

It must not have visible vertical borders, inside horizontal grid lines, or Word `Table Grid` styling. A table created with `doc.add_table(...); table.style = "Table Grid"` is a grid table, not a three-line table.

When generating `.docx` with `python-docx`, explicitly remove table-level borders and set cell-level OOXML borders for only the top, header-bottom, and bottom lines. After generation, run:

```powershell
python .\scripts\check_docx_three_line_tables.py .\paper.docx
```

### Editable Visio Figures In Word

For structural thesis figures generated as `.vsdx`, the final `.docx` should contain a Visio OLE object, not only a static PNG. The PNG export is a preview thumbnail for the OLE object and may also be used in PDF export, but it is not the editable source.

Use OfficeCLI when available:

```powershell
python .\scripts\embed_visio_ole_with_officecli.py .\paper.docx --figure-map .\paper-context\visio-ole-figure-map.json
python .\scripts\check_docx_visio_ole.py .\paper.docx --min-visio-ole 8
```

The figure map is a JSON list:

```json
[
  {
    "caption": "图4-1 系统功能结构图",
    "vsdx": "F:/paper-context/figures/figure-4-1-function-architecture.vsdx",
    "preview": "F:/paper-context/figures/figure-4-1-function-architecture.png",
    "width": "14cm",
    "height": "8cm"
  }
]
```

Default layout is: Visio OLE paragraph, then figure caption paragraph. Do not insert the OLE object into the caption paragraph unless the user explicitly accepts that rough layout.

## Fallbacks

Use only when the school template does not provide stronger rules:

- Paper size: `A4`
- Margins: do not auto-change unless extracted from the school template
- Body Chinese font: usually `宋体`
- Body size: usually `小四 / 12pt`
- Three-line table: top/bottom border `1.5pt`, header-bottom border `0.75pt`, no other borders

These are operational defaults, not claims about a specific school.

## Stop Conditions

Do not claim a `.docx` task is done when:

- the input is not a readable OOXML `.docx`
- template alignment was claimed but no template profile exists
- tables were called three-line tables but still use `Table Grid`, vertical borders, or internal grid lines
- generated Visio figures are only static PNGs in the final `.docx` and the lack of OLE embedding was not explicitly reported
- remaining major findings were hidden
