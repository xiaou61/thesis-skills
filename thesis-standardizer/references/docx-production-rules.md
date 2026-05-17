# DOCX Production Rules

Use this reference when the task is specifically about thesis `.docx` creation, editing, template alignment, or final Word-format delivery.

## Goal

Keep Chinese academic thesis work format-safe. Preserve `thesis-standardizer` as the workflow owner, and use the bundled `vendor/docx-editor-cn` layer for actual Word-content generation and low-level `.docx` operations.

## Working Baseline

1. School template first.
2. OOXML facts before manual judgment.
3. `thesis-standardizer` owns template extraction, comparison, repair, and delivery checks.
4. `vendor/docx-editor-cn` owns new Word content generation, three-line tables, formulas, captions, and OOXML unpack/edit/pack workflows.
5. Verification before declaring completion.

If the school or advisor gives explicit Word rules, those override every fallback in this file.

## Recommended Tool Strategy

Use a hybrid workflow instead of a single converter:

1. `thesis-standardizer/scripts/extract_docx_template_profile.py` and `generate_template_rule_overrides.py` for school-template facts.
2. `thesis-standardizer/scripts/finalize_thesis_delivery.py` for compare -> repair -> re-compare on stable thesis drafts.
3. `thesis-standardizer/scripts/extract_docx_comments.py` for Word comment intake.
4. `vendor/docx-editor-cn/scripts/new_doc.js` or `convert_paper.js` when a thesis section or appendix needs to be generated with Chinese academic layout rules.
5. `vendor/docx-editor-cn/scripts/table.py` and `formula.py` when inserting standard three-line tables or numbered formulas into unpacked OOXML.
6. `vendor/docx-editor-cn/scripts/office/unpack.py`, `pack.py`, and `validate.py` for low-level OOXML editing and structure checks.
7. Manual Word/PDF review for fields, pagination, cross-references, anchors, and any layout-sensitive result.

## Bundled docx-editor-cn Entry Points

The bundled resource lives at:

- `thesis-standardizer/vendor/docx-editor-cn/SKILL.md`

Use these commands from the repo root when the task needs the bundled DOCX layer:

```powershell
cd .\thesis-standardizer\vendor\docx-editor-cn
npm install
node .\scripts\new_doc.js
python -X utf8 .\scripts\office\validate.py .\output.docx
```

For XML-based edits:

```powershell
python .\thesis-standardizer\vendor\docx-editor-cn\scripts\office\unpack.py .\draft.docx .\paper-context\docx-unpacked
python .\thesis-standardizer\vendor\docx-editor-cn\scripts\table.py .\paper-context\docx-unpacked "1-1" "符号说明" --headers "符号,说明" --rows "[[\"S\",\"状态空间\"],[\"A\",\"动作空间\"]]"
python .\thesis-standardizer\vendor\docx-editor-cn\scripts\formula.py .\paper-context\docx-unpacked "E=mc^2" 1 --anchor "由此可得"
python .\thesis-standardizer\vendor\docx-editor-cn\scripts\office\pack.py .\paper-context\docx-unpacked .\draft_repacked.docx --original .\draft.docx
python -X utf8 .\thesis-standardizer\vendor\docx-editor-cn\scripts\office\validate.py .\draft_repacked.docx
```

## Chinese Academic Fallbacks

Use these only when the school template or advisor rules do not provide stronger constraints:

- Paper size: `A4`
- Margins: `2.5cm` on top, bottom, left, and right
- Body Chinese font: `宋体`
- Body size: `小四 / 12pt`
- Common heading fallback: `黑体`
- Figure/table caption fallback: `五号 / 10.5pt` or the school's explicit style
- Three-line table fallback: top and bottom border `1.5pt`, header-bottom border `0.75pt`, no other borders
- Block formula fallback: centered formula with right-aligned number using a borderless 3-column table layout

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

### 3. New DOCX Content or Markdown Conversion

Use the bundled `docx-editor-cn` layer when the task is creating new thesis content with Chinese academic formatting rules:

```powershell
cd .\thesis-standardizer\vendor\docx-editor-cn
npm install
node .\scripts\new_doc.js
```

Prefer `convert_paper.js` when the source is markdown and the result must keep three-line tables, captions, formulas, and Chinese heading styles together.

### 4. Word Comment Revision Intake

Use:

```powershell
python .\thesis-standardizer\scripts\extract_docx_comments.py .\draft.docx --out .\paper-context\word-comments
```

Then revise only the justified targets. For layout-sensitive or OOXML-level comment resolutions, use the bundled `vendor/docx-editor-cn` scripts instead of generic round-trip conversion.

## Editing Guardrails

- Do not treat a file as valid just because it ends with `.docx`; it must be a readable OOXML ZIP package with `word/document.xml`.
- Do not rewrite a finalized thesis through markdown/pandoc round-trip unless the user accepts layout rebuild risk.
- Do not change pagination, TOC, caption anchors, or cross-reference-heavy regions without a follow-up manual Word/PDF check.
- Do not invent school formatting rules that the template does not actually express.
- Do not silently overwrite style or section structure across the whole document when only a local fix is needed.
- Do not bypass the bundled `vendor/docx-editor-cn` scripts when the task specifically needs three-line tables, formula numbering, Word-native equations, or chapter-aware captions.

## Verification Contract

Before calling a `.docx` task done, verify:

1. input `.docx` is structurally readable
2. template extraction or template profile path is valid when template-based checks are claimed
3. compare / repair / re-compare outputs were produced when thesis-template alignment is claimed
4. bundled `vendor/docx-editor-cn` outputs were packed and validated when XML-level edits were performed
5. remaining `major` findings are either fixed or explicitly reported
6. manual review is still called out for Word fields, TOC, page numbers, and cross-references

## Stop Conditions

Do not claim success when:

- the input file is not a valid `.docx` package
- the template profile is missing but the task claims template alignment
- only markdown/text was reviewed while layout-sensitive `.docx` conclusions are being made
- a repaired or repacked document was written but not re-compared or re-validated
- remaining `major` findings still exist and were not surfaced
