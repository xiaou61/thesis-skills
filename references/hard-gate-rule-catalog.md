# Hard Gate Rule Catalog

Use these checks for final thesis DOCX delivery. They are deterministic stop conditions, not writing suggestions.

## Component Gate

Script: `scripts/check_docx_components.py`

Checks:

- Chinese abstract, English abstract, table of contents, Chapters 1-6, and references exist by default.
- Components appear in thesis order.
- A detected table of contents should be a Word field, not only hand-typed text.

Use options when a school template explicitly changes the component set:

```powershell
python .\scripts\check_docx_components.py .\final.docx --required zh_abstract,en_abstract,toc,chapter_1,chapter_2,references
```

## Citation Closure Gate

Script: `scripts/check_docx_citation_closure.py`

Checks:

- Body numeric citations such as `[1]` map to numbered reference entries.
- Reference numbering is continuous and not duplicated.
- Uncited references are warnings by default unless the school allows background references.

This script does not prove citation truth. It only proves the Word document has a closed numeric citation structure.

## Caption Closure Gate

Script: `scripts/check_docx_caption_closure.py`

Checks:

- Figure captions have a nearby figure object before the caption.
- Table captions have a nearby Word table after the caption.
- Figure/table numbering is chapter-scoped and continuous.
- Body mentions such as `图4-2` and `表3-1` point to real captions.
- Captions should be referenced before the object unless the school template says otherwise.

## Structural Hygiene Gate

Script: `scripts/check_docx_structural_hygiene.py`

Checks:

- No unresolved comments.
- No tracked changes.
- No hidden text in the thesis body.
- No broken OOXML relationships to styles, media, headers/footers, or embedded objects.

## Aggregate Gate Integration

`scripts/check_final_thesis_docx.ps1` runs these gates by default. Use `-SkipHardGateChecks` only for a rough internal draft, never for a delivery claim.

For a final undergraduate system-design thesis, combine them with existing gates:

```powershell
.\scripts\check_final_thesis_docx.ps1 .\final.docx `
  -FigureMap .\visio-ole-figure-map.json `
  -ExpectedVisioOle 12 `
  -MinLevel2 20 `
  -MinLevel3 4 `
  -MinContentUnits 12000 `
  -MinCjkChars 10000 `
  -RequireContinuationCaption
```
