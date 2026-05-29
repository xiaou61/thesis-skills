# Quality Gates

Use this before saying program-to-thesis work is complete.

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
- Chapter 4 function architecture, overall architecture, technical/deployment architecture, flowchart, and E-R diagrams have editable `.vsdx` sources when generated.
- database/data-object tables use a real three-line table format or a school-provided table style.
- final `.docx` tables are not Word `Table Grid` tables unless the school template explicitly requires it.
- Chapter 5 program screenshots are real screenshots/logs/reports, or are explicitly registered as `needs_user_screenshot`; synthetic screenshots are not allowed.
- every figure/table is mentioned in the text.

## Gate 4: Chapter Structure

- Chapter 1 introduces background, significance, research status, content, and structure.
- Chapter 2 explains only technologies actually used by the system.
- Chapter 3 covers analysis and requirements.
- Chapter 4 covers design and implementation.
- Chapter 5 uses real testing evidence.
- Chapter 6 summarizes completed work and does not introduce new claims.

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
```

## Completion Report

Always report:

1. what was generated or changed
2. what was verified
3. what still needs human/template review
4. what evidence is still missing
