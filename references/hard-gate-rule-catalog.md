# Hard Gate Rule Catalog

Use these checks for final thesis DOCX delivery. They are deterministic stop conditions, not writing suggestions.

For the rule model and scoring boundary, read `references/skill-rule-structure-research.md`. In this catalog every listed delivery rule is a `must_gate`: if it applies and fails, repair it and rerun the aggregate gate, or report the thesis as blocked/non-final.

## Rule Metadata Contract

Each hard gate should be reported with:

- `id`: stable rule id.
- `trigger`: when the rule applies.
- `command`: checker or aggregate command.
- `pass condition`: observable pass state.
- `failure action`: expected repair/block path.
- `handoff evidence`: command, exit code, and the important counts/errors.

Use `-SkipHardGateChecks` only for rough internal drafts. A skipped hard gate must appear in the handoff evidence and the artifact must not be described as final delivery.

## Component Gate

Rule id: `docx.components.required_order`

Script: `scripts/check_docx_components.py`

Trigger: every final thesis `.docx`.

Checks:

- Chinese abstract, English abstract, table of contents, Chapters 1-6, and references exist by default.
- Components appear in thesis order.
- A detected table of contents should be a Word field, not only hand-typed text.

Pass condition: zero errors. TOC field warnings should be repaired for normal final delivery unless a school template explicitly uses a typed table of contents.

Failure action: add or reorder missing components from the template/profile, regenerate TOC as a Word field when required, then rerun `scripts/check_final_thesis_docx.ps1`.

Use options when a school template explicitly changes the component set:

```powershell
python .\scripts\check_docx_components.py .\final.docx --required zh_abstract,en_abstract,toc,chapter_1,chapter_2,references
```

## Citation Closure Gate

Rule id: `docx.citation.closure`

Script: `scripts/check_docx_citation_closure.py`

Trigger: every final thesis `.docx` with a references section or numeric body citations.

Checks:

- Body numeric citations such as `[1]` map to numbered reference entries.
- Reference numbering is continuous and not duplicated.
- Uncited references are warnings by default unless the school allows background references.

This script does not prove citation truth. It only proves the Word document has a closed numeric citation structure.

Pass condition: zero errors. Warnings for uncited references must be either fixed or recorded as school/user-accepted background references.

Failure action: repair citation numbers/reference entries from real literature evidence. Do not invent DOI, year, volume, issue, page, or title values.

## Reference Hyperlink Gate

Rule id: `docx.citation.hyperlinks`

Script: `scripts/check_docx_reference_hyperlinks.py`

Trigger: final thesis `.docx` contains numeric body citations.

Checks:

- Body reference markers such as `[1]` are Word internal hyperlinks.
- Hyperlinks target matching reference bookmarks such as `ref_1`.
- Citation markers use expected superscript formatting.
- Citation punctuation order follows thesis style expectations.

Pass condition: zero errors.

Failure action: run `scripts/apply_docx_reference_hyperlinks.py <paper.docx>` when appropriate, manually repair unresolved bookmarks or citation ranges, then rerun the aggregate gate.

## Caption Closure Gate

Rule id: `docx.caption.closure`

Script: `scripts/check_docx_caption_closure.py`

Trigger: every final thesis `.docx` containing figures, tables, screenshots, equations, or body mentions such as `图4-2` / `表3-1`.

Checks:

- Figure captions have a nearby figure object before the caption.
- Table captions have a nearby Word table after the caption.
- Figure/table numbering is chapter-scoped and continuous.
- Body mentions such as `图4-2` and `表3-1` point to real captions.
- Captions should be referenced before the object unless the school template says otherwise.

Pass condition: zero errors. Warnings for body mentions without matching captions should be treated as repair items for normal delivery.

Failure action: add/remove body mentions, move captions next to real objects, repair numbering, and update `figure-registry.yaml` or figure map when the source registry is stale.

## Structural Hygiene Gate

Rule id: `docx.package.hygiene`

Script: `scripts/check_docx_structural_hygiene.py`

Trigger: every final thesis `.docx`.

Checks:

- No unresolved comments.
- No tracked changes.
- No hidden text in the thesis body.
- No broken OOXML relationships to styles, media, headers/footers, or embedded objects.

Pass condition: zero errors.

Failure action: accept/reject tracked changes, remove comments and hidden body text, repair or regenerate broken OOXML package relationships, then rerun the aggregate gate.

## Table Format Gate

Rule id: `docx.tables.three_line`

Script: `scripts/check_docx_three_line_tables.py`

Trigger: final thesis `.docx` contains Word tables that should follow thesis three-line table rules.

Checks:

- Tables use top border, header-bottom border, and bottom border only.
- No vertical borders or internal grid lines remain.
- Tables are not left in Word `Table Grid` style unless a school template explicitly requires it.

Pass condition: zero errors.

Failure action: rebuild tables with `scripts/create_three_line_table.py` or repair Word table borders, then rerun the aggregate gate.

## Continuation Table Gate

Rule id: `docx.tables.continuation`

Script: `scripts/check_docx_table_continuations.ps1`

Trigger: final thesis `.docx` has cross-page tables, or final gate runs with `-RequireContinuationCaption`.

Checks:

- Header row repeats across pages.
- Row splitting is disabled where required.
- Visible continuation captions exist when required by template/user.

Pass condition: zero errors.

Failure action: run `scripts/apply_table_continuations.ps1` or repair table properties/captions in Word automation, then rerun the aggregate gate.

## Heading And Length Gate

Rule ids: `docx.heading.levels`, `docx.length.content_units`

Scripts:

- `scripts/check_docx_heading_levels.py`
- `scripts/check_docx_thesis_quality.py`

Trigger: every normal final undergraduate system-design thesis unless the school gives a different requirement.

Checks:

- Required level-2 and level-3 heading density exists.
- Content units and CJK character counts meet configured thresholds.

Pass condition: zero errors against the selected thresholds.

Failure action: expand real chapter content from evidence; do not pad with repeated prose or workflow notes.

## Thesis Voice Gate

Rule id: `docx.prose.thesis_voice`

Script: `scripts/check_docx_thesis_voice.py`

Trigger: every final thesis `.docx`.

Checks:

- Body prose avoids source-audit/workflow wording.
- Missing materials are not hidden inside final thesis body as placeholders.
- Assistant/process language does not leak into the document.

Pass condition: zero errors.

Failure action: move evidence/status wording to reports or registries, rewrite body prose in student thesis voice, then rerun the aggregate gate.

## Visio And Figure Package Gates

Rule ids: `figure.visio.ole`, `figure.preview.duplicate`, `figure.preview.aspect`

Scripts:

- `scripts/check_docx_visio_ole.py`
- `scripts/check_docx_duplicate_figure_previews.py`
- `scripts/check_figure_preview_aspects.py`

Trigger:

- `figure.visio.ole`: expected Visio OLE count is greater than zero.
- `figure.preview.duplicate`: figure map is supplied.
- `figure.preview.aspect`: figure map is supplied and aspect check is not explicitly skipped for a non-final draft.

Checks:

- Generated structural Visio figures are embedded as editable OLE objects.
- Static PNG previews are not duplicated beside OLE objects.
- Preview aspect ratios are not extreme, distorted, or stale relative to the source map.

Pass condition: zero errors; for aspect checks, warnings fail when called with `--fail-on-warning`.

Failure action: re-layout crowded diagrams, re-export previews, embed with aspect-fit sizing, remove stale static previews, then rerun the aggregate gate.

## Template Replication Gates

Rule ids: `template.style_profile`, `template.page_model`, `template.replication_diff`

Scripts:

- `scripts/check_docx_style_profile.py`
- `scripts/check_docx_page_model.py`
- `scripts/report_template_replication_diff.py`

Trigger: a template profile exists and `-TemplateProfile` is supplied.

Checks:

- Paragraph style usage is close to the extracted school template/profile.
- Page margins, section model, and orientation match expected profile data.
- Replication differences are written to a report for review.

Pass condition: style/page checkers return zero errors and replication diff is generated.

Failure action: apply template profile, repair section/page/style mismatches, regenerate the diff report, then rerun the aggregate gate.

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

## Final Handoff Evidence

Paste a compact evidence block after a final pass:

```markdown
## Final Thesis Gate Evidence

- Final DOCX:
- Figure map:
- Template profile:
- Expected Visio OLE:
- Min level-2 / level-3 headings:
- Min content units / CJK chars:
- Continuation caption required:
- Aggregate command:
- Aggregate exit code:
- Failed gates:
- Repaired issues:
- Skipped gates and reason:
- Remaining evidence gaps:
```

If `Failed gates` is anything other than `none`, the artifact is blocked or non-final.
