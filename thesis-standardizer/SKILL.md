---
name: thesis-standardizer
description: Standardize and draft undergraduate thesis or graduation-design papers from source code, school templates, task books, drafts, screenshots, databases, APIs, experiments, literature, PDFs, and test evidence. Use for thesis writing, checking, packaging, literature workflows, citation closure, AIGC style reduction, and school-rule enforcement.
---

# Thesis Standardizer

## Core Rule

Treat the thesis as an evidence project.

Work in this order:

1. standards
2. facts
3. evidence
4. chapter plan
5. prose
6. Word/PDF review

Do not start from free prose.

## AIGC Fast Path

Use this first for requests like:

- `降 AIGC`
- `降低 AI 味`
- `大白话一点`
- `一段一段修`
- `修完先测`

Steps:

1. Make a local draft file.
2. Run `scripts/run_aigc_repair_loop.py <draft-file> --workspace <workspace>`.
3. Round 1: revise only high-risk paragraphs.
4. Run the same loop again.
5. Round 2: revise only remaining high/medium-risk paragraphs.
6. If needed, use `paper-context/aigc/aigc-final-paragraph-pass.md`.

Rules:

- No direct free rewriting before the script loop.
- Explain problems in plain Chinese.
- If the text was pasted in chat, save it to a local file first.

## Fast Routing

- Missing thesis workspace or templates:
  run `scripts/init_thesis_workspace.py <target-dir>`
- Program/source-code thesis:
  read `references/source-to-thesis-workflow.md`
  then run `scripts/build_project_evidence.py <project-dir> --out paper-context/evidence`
- Literature search / full-text collection:
  read `references/literature-harvest-workflow.md`
- PDF literature / citation extraction:
  read `references/literature-and-pdf-workflow.md`
- AIGC rate / detector-style report:
  read `references/aigc-detection-workflow.md`
  then run `scripts/detect_aigc_rate.py`
- AIGC reduction:
  use `AIGC Fast Path`
- AIGC plan only:
  run `scripts/build_aigc_revision_plan.py`
- Final AIGC paragraph-by-paragraph pass:
  run `scripts/run_aigc_repair_loop.py` first
- DOCX-sensitive revision:
  read `references/docx-production-rules.md`
  use bundled `vendor/docx-editor-cn/` for Word creation/editing, three-line tables, formulas, captions, and OOXML unpack/pack/validate
- Visio ER diagram generation:
  read `references/visio-diagram-workflow.md`
  then run `scripts/layout_er_diagram.py`, `scripts/generate_visio_er_diagram.ps1`, and `scripts/check_er_layout.py`
- Final delivery:
  read `references/quality-gates.md`
  then run `scripts/check_thesis_workspace.py <workspace>`

## Minimal Contracts

| Request | Read | Run | Deliver |
| --- | --- | --- | --- |
| program -> thesis | `source-to-thesis-workflow.md` | `build_project_evidence.py` | evidence index, missing materials, chapter plan |
| find papers | `literature-harvest-workflow.md` | harvest scripts | candidate table, downloaded files, verified selection |
| handle PDF literature | `literature-and-pdf-workflow.md` | `extract_pdf_references.py`, `build_literature_crossrefs.py` | candidate references, cross-reference index |
| detect AIGC | `aigc-detection-workflow.md` | `detect_aigc_rate.py` | local estimate, paragraph risk findings |
| lower AIGC | `aigc-style-governance.md` | `run_aigc_repair_loop.py` | `先跑脚本 -> 改高风险段 -> 本地复查 -> 再补一轮` |
| build AIGC plan | `aigc-style-governance.md` | `build_aigc_revision_plan.py` | paragraph actions |
| final AIGC pass | `aigc-style-governance.md` | `run_aigc_repair_loop.py` | final paragraph work order |
| final check | `quality-gates.md` | `check_thesis_workspace.py` | critical / major / minor findings |

## Required Reads

When `thesis-ai-standard/` exists, read only these first:

1. `thesis-ai-standard/README.md`
2. `thesis-ai-standard/templates/standard-profile.yaml`
3. `thesis-ai-standard/templates/thesis-ai-spec.yaml`
4. `thesis-ai-standard/templates/figure-registry.yaml`

Read other templates only when the task needs them.

## Hard Rules

- School and advisor rules override bundled defaults.
- Never invent facts, code behavior, APIs, tables, screenshots, experiments, citations, DOI values, or school requirements.
- Never expose AI workflow language in thesis body text.
- Never frame AIGC work as detector bypass.
- AIGC-rate output is a local heuristic estimate, not an official school or third-party score.
- For AIGC reduction, run `run_aigc_repair_loop.py` before rewriting.
- For final paragraph-by-paragraph AIGC pass, explicitly warn that it is token-heavy.
- For plainer writing, use everyday Chinese.
- For pasted text, save to a local draft file before running the AIGC loop.
- Every material change must be written to `revision-log.md` or `revision-trace.jsonl`.
- For Word-sensitive files, do not rebuild the whole `.docx` unless the user accepts layout risk.
- For thesis DOCX content creation or low-level Word editing, prefer bundled `vendor/docx-editor-cn` resources over ad hoc markdown/pandoc round-trips.
- Every figure/table/equation/screenshot must have source, ID, title, first mention, and status.
- Do not add citations in the abstract unless the school requires it.
- Each body citation point may cite at most 2 references.

## Default Thesis Rules

- Default literature selection: Chinese `12-15`, English `3-5`, unless school/user rules override.
- Default literature year range: recent 6 years based on the user's current year, unless school/user rules override.
- Stop and mark missing evidence when a claim is unsupported.
- Draft chapter by chapter, not full freeform thesis dumping.

## Must-Use References

- `references/standards-and-template-resolution.md`
- `references/source-to-thesis-workflow.md`
- `references/literature-harvest-workflow.md`
- `references/literature-and-pdf-workflow.md`
- `references/aigc-detection-workflow.md`
- `references/aigc-style-governance.md`
- `references/workflow-state-management.md`
- `references/quality-gates.md`
- `references/docx-production-rules.md`
- `references/visio-diagram-workflow.md`

## Bundled DOCX Layer

When a thesis task reaches actual Word content generation or XML-level editing, switch from the thesis workflow scripts to the bundled `vendor/docx-editor-cn` layer:

- `vendor/docx-editor-cn/SKILL.md`
- `vendor/docx-editor-cn/scripts/new_doc.js`
- `vendor/docx-editor-cn/scripts/convert_paper.js`
- `vendor/docx-editor-cn/scripts/table.py`
- `vendor/docx-editor-cn/scripts/formula.py`
- `vendor/docx-editor-cn/scripts/office/unpack.py`
- `vendor/docx-editor-cn/scripts/office/pack.py`
- `vendor/docx-editor-cn/scripts/office/validate.py`

## Main Scripts

- `scripts/init_thesis_workspace.py`
- `scripts/build_project_evidence.py`
- `scripts/generate_literature_search_config.py`
- `scripts/run_keyword_harvest_no_dedup.py`
- `scripts/continue_download_and_dedup.py`
- `scripts/verify_select_literature.py`
- `scripts/extract_pdf_references.py`
- `scripts/build_literature_crossrefs.py`
- `scripts/check_thesis_workspace.py`
- `scripts/layout_er_diagram.py`
- `scripts/check_er_layout.py`
- `scripts/generate_visio_er_diagram.ps1`
- `scripts/detect_aigc_rate.py`
- `scripts/analyze_aigc_style.py`
- `scripts/build_aigc_revision_plan.py`
- `scripts/run_aigc_repair_loop.py`
- `scripts/append_revision_log.py`
