# DOCX Production Rules

Use this reference when the task is specifically about thesis `.docx` creation, editing, template alignment, or final Word-format delivery.

## Goal

Keep Chinese academic thesis work format-safe. Prefer template-driven, minimal-risk `.docx` operations over content round-trips that rebuild layout.

## Working Baseline

1. School template first.
2. OOXML facts before manual judgment.
3. Minimal in-place edits before body rebuild.
4. Verification before declaring completion.

If the school or advisor gives explicit Word rules, those override every fallback in this file.

## Recommended Tool Strategy

Use a hybrid workflow instead of a single converter:

1. OOXML inspection for sections, page size, margins, headers, footers, numbering, TOC fields, and style definitions.
2. `python-docx` for conservative edits such as section properties, style defaults, and header/footer text.
3. Markdown or pandoc only for early drafting or template reuse, not for stable final `.docx` round-trips.
4. Manual Word/PDF review for fields, pagination, cross-references, anchors, and any layout-sensitive result.

## Chinese Academic Fallbacks

Use these only when the school template or advisor rules do not provide stronger constraints:

- Paper size: `A4`
- Margins: `2.5cm` on top, bottom, left, and right
- Body Chinese font: `宋体`
- Body size: `小四 / 12pt`
- Common heading fallback: `黑体`
- Figure/table caption fallback: `五号 / 10.5pt` or the school's explicit style

These are operational defaults, not claims about a specific school rule.

## Safe Workflows

### 1. School Template Extraction

Use:

```powershell
python .\thesis-standardizer\scripts\extract_docx_template_profile.py .\school-template.docx --out .\paper-context\template-extract
python .\thesis-standardizer\scripts\generate_template_rule_overrides.py .\paper-context\template-extract\template-profile.json --out .\paper-context\template-extract\template-rule-overrides.yaml
```

Expect:

- `template-profile.json`
- `template-profile.md`
- `template-rule-overrides.yaml`

### 2. Existing Draft Finalization

Use:

```powershell
python .\thesis-standardizer\scripts\finalize_thesis_delivery.py .\draft.docx --workspace .
```

This runs:

1. workspace check
2. template comparison
3. conservative auto repair
4. post-repair re-compare
5. repair log write-back

### 3. Word Comment Revision Intake

Use:

```powershell
python .\thesis-standardizer\scripts\extract_docx_comments.py .\draft.docx --out .\paper-context\word-comments
```

Then revise only the justified targets and log each decision.

## Editing Guardrails

- Do not treat a file as valid just because it ends with `.docx`; it must be a readable OOXML ZIP package with `word/document.xml`.
- Do not rewrite a finalized thesis through markdown/pandoc round-trip unless the user accepts layout rebuild risk.
- Do not change pagination, TOC, caption anchors, or cross-reference-heavy regions without a follow-up manual Word/PDF check.
- Do not invent school formatting rules that the template does not actually express.
- Do not silently overwrite style or section structure across the whole document when only a local fix is needed.

## Verification Contract

Before calling a `.docx` task done, verify:

1. input `.docx` is structurally readable
2. template extraction or template profile path is valid when template-based checks are claimed
3. compare / repair / re-compare outputs were produced
4. remaining `major` findings are either fixed or explicitly reported
5. manual review is still called out for Word fields, TOC, page numbers, and cross-references

## Stop Conditions

Do not claim success when:

- the input file is not a valid `.docx` package
- the template profile is missing but the task claims template alignment
- only markdown/text was reviewed while layout-sensitive `.docx` conclusions are being made
- a repaired document was written but not re-compared
- remaining `major` findings still exist and were not surfaced
