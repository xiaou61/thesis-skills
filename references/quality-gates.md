# Quality Gates

Use this before saying program-to-thesis work is complete.

## Gate Function

For final Word delivery, do not rely on a mental checklist. Use an executable gate:

1. Identify the current `.docx`, the figure map, expected Visio OLE count, and heading thresholds.
2. Run `scripts/check_final_thesis_docx.ps1` against the current `.docx`.
3. Read the exit code and output.
4. If it fails, fix the failed gate and run it again.
5. Only a fresh pass can support a completion claim.

## Gate 1: Standards

- `standard-profile.yaml` exists.
- school/advisor rules are explicit or marked missing.
- template extraction outputs exist if a school `.docx` template was used.

## Gate 2: Project Evidence

- `thesis-ai-spec.yaml` contains real project facts.
- claimed functions map to code, screenshots, tests, or user materials.
- claimed database fields map to schema/entity/migration evidence.
- claimed APIs map to route/controller/service evidence.
- claimed tests map to reports, logs, screenshots, or test files.

## Gate 3: Figures And Tables

- `figure-registry.yaml` lists required figures/tables.
- `paper-context/figure-plan/figure-plan.yaml` exists for full program-to-thesis work or the report explains why figure planning was skipped.
- Chapter 3 use-case diagram has editable `.vsdx` source when generated.
- Chapter 3 business-flow / requirement-structure diagrams have editable `.vsdx` sources when generated.
- Chapter 4 function architecture, overall architecture, technical/deployment architecture, and E-R diagrams have editable `.vsdx` sources when generated.
- Chapter 5 implementation flowcharts have editable `.vsdx` sources when generated.
- final `.docx` embeds generated structural `.vsdx` figures as Visio OLE objects when OfficeCLI or Word automation is available; verify with `scripts/check_docx_visio_ole.py`.
- database/data-object tables use a real three-line table format or a school-provided table style.
- final `.docx` tables are not Word `Table Grid` tables unless the school template explicitly requires it.
- final `.docx` cross-page tables repeat header rows, prevent row splitting across pages, and include visible continuation captions when required; verify with `scripts/check_docx_table_continuations.ps1`.
- Chapter 5 program screenshots are real implementation screenshots, or are explicitly registered as `needs_user_screenshot`; synthetic screenshots are not allowed.
- Chapter 6 test screenshots/logs/reports are used only when real test evidence exists.
- every figure/table is mentioned in the text.

## Gate 4: Chapter Structure

- Chapter 1 introduces background, significance, research status, content, and structure.
- Chapter 2 explains only technologies actually used by the system.
- Chapter 3 covers analysis and requirements.
- Chapter 4 covers system design.
- Chapter 5 covers system implementation and program screenshots.
- Chapter 6 covers testing from real testing evidence and, unless a standalone conclusion chapter is required, includes concise completed-work, limitation, and future-work summary sections.
- Chapter 7 appears only when the school template or user explicitly requires a standalone conclusion chapter; if present, it does not introduce new claims.

## Gate 5: Integrity

- no fabricated functions, APIs, fields, tests, screenshots, references, DOI values, or school rules.
- no AI workflow language appears in thesis body text.
- missing evidence is reported instead of hidden.

## Gate 6: Script Validation

Run applicable checks:

```powershell
python .\scripts\check_thesis_workspace.py .\thesis-ai-standard
python .\scripts\build_figure_plan.py .\thesis-ai-standard\templates\thesis-ai-spec.yaml --out .\paper-context\figure-plan
python -m py_compile .\scripts\build_project_evidence.py
python .\scripts\check_docx_three_line_tables.py .\path\to\final-paper.docx
.\scripts\check_docx_table_continuations.ps1 .\path\to\final-paper.docx -RequireContinuationCaption
python .\scripts\check_docx_visio_ole.py .\path\to\final-paper.docx --min-visio-ole <expected-count>
.\scripts\check_final_thesis_docx.ps1 .\path\to\final-paper.docx -FigureMap .\path\to\visio-ole-figure-map.json -ExpectedVisioOle <expected-count> -RequireContinuationCaption
```

## Red Flags

Stop and run the aggregate gate when any of these thoughts appear:

- "It passed earlier."
- "Only a formatting/table/figure change was made."
- "The table is short enough."
- "Word will handle the page break."
- "The screenshot or OLE check is unrelated."
- "The generated document looks fine visually."

## Completion Report

Always report:

1. what was generated or changed
2. what was verified
3. what still needs human/template review
4. what evidence is still missing
