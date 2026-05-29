# Thesis Module Workflow

Use this when the task is the normal case: build a thesis from a real software project.

## Inputs

Prefer these materials, in this order:

1. school `.docx` template or formatting guide
2. source code or project repository
3. database schema, migrations, entities, or SQL
4. API docs, route files, controllers, or service files
5. screenshots, run logs, test reports
6. reference list or literature requirements
7. existing thesis draft, if any

If an important material is missing, name it directly and continue with the parts that can be evidenced.

## Main Workflow

1. Template extraction
   - If a school template exists, run `extract_docx_template_profile.py`.
   - Use the result for fonts, sizes, headings, captions, margins, page setup, and table constraints.
2. Project evidence
   - Run `build_project_evidence.py`.
   - Read `project-evidence.json`, `tech-stack.md`, `api-list.md`, `database-schema.md`, and `test-results.md`.
   - Verify important claims against source files when risk is high.
3. Standard files
   - Fill `standard-profile.yaml`, `thesis-ai-spec.yaml`, and `figure-registry.yaml`.
   - Treat these as the planning contract before writing.
4. Chapter drafting
   - Draft from evidence, not generic thesis prose.
   - Mark unsupported claims as missing evidence.
5. Figures and tables
   - Read `references/figure-and-screenshot-plan.md`.
   - Run `build_figure_plan.py` before drafting Chapter 3-5.
   - Generate only evidence-backed figures/tables needed by the current chapter, but do not under-plan a normal system thesis.
   - Keep editable sources and exported images registered.
   - For Chapter 4 database or structured data-object design, read `references/chapter-4-database-workflow.md` and generate the full E-R/table asset set before drafting.
6. Delivery checks
   - Run `check_thesis_workspace.py`.
   - For final `.docx`, use the extracted template profile as the review baseline and list any remaining manual Word checks.

## Chapter Defaults

### Chapter 1: Introduction

Write:

- research/design background
- purpose and significance
- domestic/foreign research status or related work
- main work of the thesis
- thesis organization

Use citations here. Avoid implementation details.

### Chapter 2: Related Technologies

For each technology:

1. what it is
2. why it is suitable
3. where the system uses it
4. limitation or boundary, if relevant

Use citations here. Do not include technologies not present in the project.

### Chapter 3: System Analysis

Write:

- feasibility analysis
- user/role analysis
- functional requirements
- non-functional requirements
- use-case analysis

Expected figure:

- Visio use-case diagram via `visio-use-case-workflow.md`.
- Visio core business flowchart when the workflow is known.
- Visio requirement/function decomposition figure when module evidence exists.

Use-case names must match the requirement text.

### Chapter 4: Design And Implementation

Write:

- system function structure
- database conceptual design
- database table design
- key module design and implementation
- selected process or screenshot evidence if needed

Expected assets:

- Visio function architecture diagram via `visio-function-architecture-workflow.md`
- Visio overall architecture diagram
- Visio technical/deployment architecture diagram when stack or deployment evidence exists
- database asset set via `chapter-4-database-workflow.md`
- Visio E-R overview via `visio-diagram-workflow.md`
- single-entity E-R diagrams for core entities
- key module flowcharts for 2-4 important modules when code or workflow evidence exists
- database design three-line tables via `build_chapter4_database_assets.py` and `docx-production-rules.md`

Keep E-R overview diagrams limited to core entities and relationships.
If business database evidence is absent but the project itself is a local tool, generator, CLI, skill, library, or documentation pipeline with real YAML/JSON/JSONL/Markdown data artifacts, model those artifacts as "data objects" and explicitly state that they are not physical business database tables. Then still generate the overview E-R diagram, single-entity E-R diagrams, and three-line tables for those data objects. If neither business schema nor structured project data exists, record the missing schema/entity/migration/SQL evidence and stop that subsection.

### Chapter 5: Testing

Write only from evidence:

- test environment
- test cases
- screenshots, logs, or reports
- test result tables

Expected assets:

- test environment table
- test case three-line table
- real program screenshots, run logs, or report screenshots
- screenshot placeholders with `status: needs_user_screenshot` when the user has not provided real screenshots

Never fabricate program screenshots. If the app cannot be run locally or the user has not provided screenshots, keep figure entries with `source_file: pending_user_screenshot`, leave visible placeholders in the draft, and list them in evidence gaps.

### Chapter 6: Conclusion

Write:

- completed work
- limitations
- future work

Do not introduce new features or evidence here.
