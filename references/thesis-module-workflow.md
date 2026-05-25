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
   - Generate only the figures/tables needed by the current chapter.
   - Keep editable sources and exported images registered.
   - For Chapter 4 database design, read `references/chapter-4-database-workflow.md` and generate the full database asset set before drafting.
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
- database asset set via `chapter-4-database-workflow.md`
- Visio E-R overview via `visio-diagram-workflow.md`
- single-entity E-R diagrams for core entities
- database design three-line tables via `build_chapter4_database_assets.py` and `docx-production-rules.md`

Keep E-R overview diagrams limited to core entities and relationships.
Do not replace database table design with unrelated configuration tables. If database evidence is absent, record the missing schema/entity/migration/SQL evidence and stop that subsection.

### Chapter 5: Testing

Write only from evidence:

- test environment
- test cases
- screenshots, logs, or reports
- test result tables

No special diagram is required by default.

### Chapter 6: Conclusion

Write:

- completed work
- limitations
- future work

Do not introduce new features or evidence here.
