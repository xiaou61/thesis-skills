---
name: thesis-standardizer
description: Generate and standardize an undergraduate system-design thesis from a real program/project. Use when the user provides source code, a repo, database/API evidence, screenshots, a school template, or asks for thesis drafting, chapter generation, Visio thesis diagrams, three-line tables, or thesis workspace checks.
---

# Thesis Standardizer

## Purpose

Default to one main job: turn a real program into a defensible undergraduate thesis.

Always work from evidence:

1. template rules
2. project facts
3. code/database/API/test evidence
4. chapter plan
5. prose
6. figures/tables
7. Word/PDF checks

Do not start from free prose unless the user explicitly asks for a rough draft and accepts missing evidence risk.

## Mainline: Program To Thesis

For a project/repo/system source, run this route:

1. If a school `.docx` template exists, extract it:
   `scripts/extract_docx_template_profile.py <template.docx> --out paper-context/template-extract`
2. Initialize/check the thesis workspace:
   `scripts/init_thesis_workspace.py <target-dir>`
3. Build project evidence:
   `scripts/build_project_evidence.py <project-dir> --out paper-context/evidence`
4. Fill or update:
   `thesis-ai-standard/templates/standard-profile.yaml`
   `thesis-ai-standard/templates/thesis-ai-spec.yaml`
   `thesis-ai-standard/templates/figure-registry.yaml`
5. Draft by chapter using the chapter map below.
6. Generate required Visio diagrams and three-line tables only when the chapter needs them.
7. Run final checks:
   `scripts/check_thesis_workspace.py <workspace>`

Read `references/thesis-module-workflow.md` when planning or executing the full route.

## Chapter Map

- Chapter 1, introduction: background, significance, research status, research content, thesis structure. This is citation-heavy.
- Chapter 2, related technologies: explain each technology and how this system uses it. This is citation-heavy.
- Chapter 3, system analysis: feasibility, roles, requirements, non-functional requirements, use-case diagram.
- Chapter 4, design and implementation: function architecture diagram, E-R overview, single-entity E-R diagrams, database three-line tables, key module implementation.
- Chapter 5, testing: test environment, cases, screenshots/logs, result tables. No special diagram by default.
- Chapter 6, conclusion: completed work, limitations, future work. No special diagram by default.

Chapters 1-3 are the main citation area. Do not force citations into implementation or test claims unless the claim genuinely needs literature support.

## Diagram And Table Routing

- Use-case diagram: `references/visio-use-case-workflow.md`
  Run `layout_use_case_diagram.py`, `check_use_case_layout.py`, `generate_visio_use_case_diagram.ps1`.
- Function architecture diagram: `references/visio-function-architecture-workflow.md`
  Run `layout_function_architecture_diagram.py`, `check_function_architecture_layout.py`, `generate_visio_function_architecture_diagram.ps1`.
- E-R diagram: `references/visio-diagram-workflow.md`
  Run `layout_er_diagram.py`, `check_er_layout.py`, `generate_visio_er_diagram.ps1`.
- Flowchart: `references/visio-flowchart-workflow.md`
  Run `layout_flowchart_diagram.py`, `check_flowchart_layout.py`, `generate_visio_flowchart_diagram.ps1`.
- Three-line tables: read `references/docx-production-rules.md`, then use `scripts/create_three_line_table.py`.

Keep editable sources: `.vsdx` for Visio figures and script/Word source for final tables.

## Hard Rules

- School and advisor rules override defaults.
- Never invent project functions, APIs, database fields, tests, screenshots, experiments, citations, DOI values, or school rules.
- If evidence is missing, list missing materials instead of pretending.
- Every figure/table/equation/screenshot must have a source file, export file when applicable, first mention, and status in `figure-registry.yaml`.
- Do not expose AI workflow language in thesis prose.
- For stable `.docx` files, avoid whole-document markdown round trips unless the user accepts layout risk.

## Minimal Reads

When `thesis-ai-standard/` exists, read these first and stop unless more detail is needed:

1. `thesis-ai-standard/templates/standard-profile.yaml`
2. `thesis-ai-standard/templates/thesis-ai-spec.yaml`
3. `thesis-ai-standard/templates/figure-registry.yaml`
4. `paper-context/evidence/`, if present
5. `paper-context/template-extract/template-rule-overrides.yaml`, if present

Use deeper reference files only for the active task.
