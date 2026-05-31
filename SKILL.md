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
5. Build the figure/screenshot plan before drafting Chapter 3-6:
   `scripts/build_figure_plan.py thesis-ai-standard/templates/thesis-ai-spec.yaml --out paper-context/figure-plan`
   Merge planned figures into `figure-registry.yaml` or keep the fragment as the drafting checklist.
6. Draft by chapter using the chapter map below.
7. For Chapter 4, build the database-design asset set before drafting database/data-object sections:
   `scripts/build_chapter4_database_assets.py <database-model.yaml> --out paper-context/database-design`
   If no business database exists but the project has real structured configuration/data artifacts
   such as YAML, JSON, JSONL, Markdown registries, logs, or generated evidence files, create a
   clearly labeled data-object model from those artifacts and generate the same overview E-R,
   single-entity E-R, and three-line table assets. Do not call it a physical business database.
8. Generate required Visio diagrams, screenshot placeholders, and three-line tables only when the chapter needs them.
   When producing the final `.docx`, embed structural `.vsdx` figures as Visio OLE objects when OfficeCLI or Word automation is available; the `.png` export is only the preview thumbnail. Check exported preview aspect ratios before embedding, and use aspect-fit OLE sizing instead of a universal fixed rectangle.
9. Run final checks:
   `scripts/check_thesis_workspace.py <workspace>`

Read `references/thesis-module-workflow.md` when planning or executing the full route.

## Chapter Map

- Chapter 1, introduction: background, significance, research status, research content, thesis structure. This is citation-heavy.
- Chapter 2, related technologies: explain each technology and how this system uses it. This is citation-heavy.
- Chapter 3, system analysis: feasibility, roles, requirements, non-functional requirements, use-case diagram, core business flowchart, requirement/function decomposition figure when evidence supports them.
- Chapter 4, system design: function architecture diagram, overall architecture diagram, technical/deployment architecture diagram when supported, E-R overview, single-entity E-R diagrams, database/data-object three-line tables, and design rationale.
- Chapter 5, system implementation: key module implementation, implementation flowcharts, real program screenshots for login/entry, homepage, and core functions; use `needs_user_screenshot` placeholders when real screenshots are missing. This chapter is not the testing chapter.
- Chapter 6, system testing: test environment, test methods, test cases, logs/reports, test result screenshots if real evidence exists, and result tables. Do not put normal program-function screenshots here. Do not create a separate Chapter 7 by default; when conclusion content is needed, place a concise completed-work, limitations, and future-work section at the end of Chapter 6. Create standalone Chapter 7 only when the school template or user explicitly requires it.

Chapters 1-3 are the main citation area. Do not force citations into implementation or test claims unless the claim genuinely needs literature support.

## Diagram And Table Routing

- Figure/screenshot plan: `references/figure-and-screenshot-plan.md`
  Run `build_figure_plan.py` before drafting Chapter 3-6. A normal system thesis should plan many evidence-backed figures, not only one use-case diagram and one function diagram.
- Word delivery with editable Visio: read `references/docx-production-rules.md`
  For generated structural `.vsdx` figures, run `scripts/check_figure_preview_aspects.py`, then prefer `scripts/embed_visio_ole_with_officecli.py --fit-preview-aspect --max-width 14cm --max-height 18cm` and verify the final `.docx` with `scripts/check_docx_visio_ole.py`. A PNG preview in Word is not an editable Visio diagram.
- Use-case diagram: `references/visio-use-case-workflow.md`
  Run `layout_use_case_diagram.py`, `check_use_case_layout.py`, `generate_visio_use_case_diagram.ps1`.
- Function architecture diagram: `references/visio-function-architecture-workflow.md`
  Run `layout_function_architecture_diagram.py`, `check_function_architecture_layout.py`, `generate_visio_function_architecture_diagram.ps1`.
- E-R diagram: `references/visio-diagram-workflow.md`
  Run `layout_er_diagram.py`, `check_er_layout.py`, `generate_visio_er_diagram.ps1`.
- Chapter 4 database assets: `references/chapter-4-database-workflow.md`
  Run `build_chapter4_database_assets.py`, then render the overview and single-entity E-R JSON with the ER Visio route.
- Flowchart: `references/visio-flowchart-workflow.md`
  Run `layout_flowchart_diagram.py`, `check_flowchart_layout.py`, `generate_visio_flowchart_diagram.ps1`.
- Three-line tables: read `references/docx-production-rules.md`, then use `scripts/create_three_line_table.py`.
  A Word `Table Grid` table is not a three-line table.

Keep editable sources: `.vsdx` for Visio figures and script/Word source for final tables.
For Word delivery, a PNG inserted into the body is only a preview image. A figure should not be called "Word-editable Visio" unless the `.docx` contains a Visio OLE object, verified with `scripts/check_docx_visio_ole.py`.

## Hard Rules

- School and advisor rules override defaults.
- Never invent project functions, APIs, database fields, tests, screenshots, experiments, citations, DOI values, or school rules.
- If evidence is missing, list missing materials instead of pretending.
- Do not silently skip Chapter 4 database/data-object design. If schema/entity/migration/SQL evidence exists, generate overview E-R, single-entity E-R diagrams, and database three-line tables. If no business database evidence exists but the project has real structured configuration or evidence artifacts, generate a clearly labeled data-object E-R model and three-line tables from those artifacts. If neither exists, create an evidence gap before drafting Chapter 4.
- Do not merge implementation into Chapter 4 by default. For a normal system thesis, Chapter 4 is design, Chapter 5 is implementation, and Chapter 6 is testing. Do not create Chapter 7 unless the school template or user explicitly requires a standalone conclusion chapter.
- Do not under-plan figures for a normal system thesis. If fewer than 8 figures are planned across Chapters 3-6, explain the small scope or missing evidence.
- Never fabricate Chapter 5 program screenshots. Chapter 5 is the implementation chapter and should contain real running-program screenshots for implemented functions. If the app cannot be run or screenshots are not provided, create `needs_user_screenshot` entries in `figure-registry.yaml` and list them as evidence gaps.
- A three-line table means only top border, header-bottom border, and bottom border. No vertical borders, no internal grid lines, and no Word `Table Grid` styling. Verify final DOCX tables with `scripts/check_docx_three_line_tables.py` when a `.docx` is produced.
- For final `.docx` delivery, do not represent structural Visio diagrams only as static PNGs unless OLE embedding is impossible and explicitly reported. Prefer `scripts/embed_visio_ole_with_officecli.py --fit-preview-aspect`, then verify with `scripts/check_docx_visio_ole.py`.
- Do not force every Visio OLE object into one fixed display size such as `14cm x 8cm`. Preserve the preview aspect ratio. If `scripts/check_figure_preview_aspects.py` reports an extreme flat/tall figure, re-layout or split the source diagram before final delivery.
- For generated flowchart `.vsdx` figures, do not rely on Visio automatic routing alone. Run `layout_flowchart_diagram.py` so each edge receives orthogonal route points, then run `check_flowchart_layout.py` and require `connectorCrossings: 0` before rendering or embedding the figure.
- For generated E-R `.vsdx` figures, run `check_er_layout.py` after `layout_er_diagram.py` and require both `overlapPairs: 0` and `connectorCrossings: 0`. If the overview E-R is crowded, put only entities and relationships in the overview and move attributes to single-entity E-R diagrams and three-line tables.
- Single-entity E-R diagrams should use dispersed boundary glue points rather than one common center point. Prefer short Chinese field labels from schema comments, stripping parenthetical implementation notes such as enum values or encryption details.
- Every figure/table/equation/screenshot must have a source file, export file when applicable, first mention, and status in `figure-registry.yaml`.
- Do not expose AI workflow language in thesis prose.
- For stable final `.docx` files, avoid whole-document markdown round trips unless the user accepts layout risk. Markdown-to-Word/Pandoc output must still pass `check_docx_three_line_tables.py`, `check_docx_visio_ole.py`, Office/OpenXML validation, and figure aspect checks before it can be treated as deliverable.

## Minimal Reads

When `thesis-ai-standard/` exists, read these first and stop unless more detail is needed:

1. `thesis-ai-standard/templates/standard-profile.yaml`
2. `thesis-ai-standard/templates/thesis-ai-spec.yaml`
3. `thesis-ai-standard/templates/figure-registry.yaml`
4. `paper-context/evidence/`, if present
5. `paper-context/template-extract/template-rule-overrides.yaml`, if present
6. `paper-context/database-design/`, if present
7. `paper-context/figure-plan/`, if present

Use deeper reference files only for the active task.
