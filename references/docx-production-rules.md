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
- remaining major findings were hidden
