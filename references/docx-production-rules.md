# DOCX Production Rules

Use this reference for the slim skill's Word-sensitive operations.

## Baseline

1. School template first.
2. Extract OOXML facts before judging format.
3. Avoid whole-document markdown round trips for stable final `.docx` files. Markdown can be a drafting format, but the final thesis Word file must still pass the DOCX, table, and OLE checks below.
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

Figure captions and the OLE figure map must use the same display text as the school template. If the template uses `图 4.1` and `表4.1`, do not embed with stale map captions such as `图4-1`; OfficeCLI will not find the caption paragraph.

Use OfficeCLI when available:

```powershell
python .\scripts\check_figure_preview_aspects.py .\paper-context\visio-ole-figure-map.json
python .\scripts\embed_visio_ole_with_officecli.py .\paper.docx --figure-map .\paper-context\visio-ole-figure-map.json --fit-preview-aspect --max-width 14cm --max-height 18cm
python .\scripts\check_docx_visio_ole.py .\paper.docx --min-visio-ole 8
```

Do not embed every OLE object with the same universal `14cm x 8cm` display size. That distorts tall flowcharts and flat architecture diagrams. Fit the OLE display size from the PNG preview aspect ratio, then inspect warnings from `check_figure_preview_aspects.py`. Extreme warnings mean the source diagram layout should be split or redesigned instead of stretched inside Word.

The figure map is a JSON list:

```json
[
  {
    "caption": "图 4.1 系统功能结构图",
    "vsdx": "F:/paper-context/figures/figure-4-1-function-architecture.vsdx",
    "preview": "F:/paper-context/figures/figure-4-1-function-architecture.png",
    "width": "14cm",
    "height": "8cm"
  }
]
```

Default layout is: Visio OLE paragraph, then figure caption paragraph. Do not insert the OLE object into the caption paragraph unless the user explicitly accepts that rough layout.

### Markdown Drafts And Pandoc

Pandoc can produce a quick `.docx` from Markdown, but that raw output is not a thesis-final Word pipeline by default. Before treating any Markdown-derived DOCX as deliverable, verify:

```powershell
python .\scripts\check_docx_three_line_tables.py .\paper.docx
python .\scripts\check_docx_visio_ole.py .\paper.docx --min-visio-ole 8 --require-before-caption
python .\scripts\check_figure_preview_aspects.py .\paper-context\visio-ole-figure-map.json
```

If the Markdown-derived DOCX only contains static images, re-embed Visio OLE objects with OfficeCLI and re-run the checks. If tables fail the three-line check or the document fails OpenXML validation, use the controlled Word-generation path instead of shipping the Markdown conversion.

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
- OLE figures were embedded with a fixed size that visibly stretches the preview instead of preserving the source aspect ratio
- `check_figure_preview_aspects.py` reports extreme flat/tall figure warnings and no split/re-layout decision is documented
- remaining major findings were hidden
