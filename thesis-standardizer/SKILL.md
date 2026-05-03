---
name: thesis-standardizer
description: Standardize and draft undergraduate thesis or graduation-design papers from source code, school templates, task books, drafts, screenshots, databases, APIs, experiments, PDF literature, Word comments, and test evidence. Use when the user asks to write, generate, refactor, check, modify, or package a thesis; turn a program into thesis chapters; create thesis specs, workflow progress markdown logs, figure registries, draw.io diagrams, evidence indexes, PDF reference extraction, citation cross-reference maps, AIGC style-risk reports, Word comment todo lists, academic prose revision reports, or school-rule enforcement before drafting.
---

# Thesis Standardizer

## Operating Model

Treat a thesis as an evidence-driven project. Do not start from prose. Start from standards, facts, and evidence.

Layering:

1. `SKILL.md`: routing, contracts, guardrails, and quality gates.
2. `references/`: detailed workflows loaded only when the task needs them.
3. `scripts/`: deterministic extraction, bootstrap, and validation helpers.
4. `assets/thesis-ai-standard/`: portable thesis project templates copied into the user's workspace.
5. User materials: school template, source code, PDFs, screenshots, data, tests, and drafts.

Keep this order when working: standards -> facts -> evidence -> chapter plan -> prose -> Word/PDF review.

## Module Map

Use modules independently, then combine them for end-to-end thesis work:

1. Standards module: school rules, advisor rules, national-standard fallback.
2. Evidence module: source code, tests, screenshots, data, experiments.
3. Literature module: PDF extraction, citation cross-references, reference closure.
4. AIGC style-governance module: report-first academic prose review and targeted revision.
5. Workflow-log module: markdown status, step plan, progress log, evidence gaps, chapter progress, revision log.
6. Word-comment revision module: extract DOCX comments, create comment todos, revise document, log changes.
7. Output module: final quality gates, Word/PDF handoff, residual risks.

## Decision Tree

- New thesis workspace or missing templates: run `scripts/init_thesis_workspace.py <target-dir>`; it also creates `paper-context/workflow/*.md`.
- Missing workflow logs only: run `scripts/init_workflow_logs.py <target-dir>`.
- Standards, school-template interpretation, or version conflicts: read `references/standards-and-template-resolution.md`.
- Program/source-code thesis: read `references/source-to-thesis-workflow.md`; run `scripts/build_project_evidence.py <project-dir> --out paper-context/evidence`.
- PDF literature, related work, or citations: read `references/literature-and-pdf-workflow.md`; run the PDF extraction and citation cross-reference scripts.
- AIGC, AI flavor, templated prose, academic style naturalness, or style report: read `references/aigc-style-governance.md`; run `scripts/analyze_aigc_style.py <draft-file> --out paper-context/aigc/aigc-style-report.md`.
- Word comments, DOCX comments, advisor comments in Word, or "modify the thesis according to comments": read `references/word-comment-revision-workflow.md`; run `scripts/extract_docx_comments.py <draft.docx> --out paper-context/word-comments`.
- Existing draft or Word-format-sensitive work: use this skill for standards/evidence, then use `thesis-docx`/`docx` for Word layout and PDF review.
- Finalized thesis revision, second-round editing, or any `.docx` with stable TOC/cross-references/figure anchors: prefer in-place targeted edits inside a copied original `.docx`; avoid pandoc body round-trips unless the user explicitly accepts layout rebuild risk.
- Before final delivery: read `references/quality-gates.md` and run `scripts/check_thesis_workspace.py <workspace>` when a `thesis-ai-standard/` folder exists.

## Mode Contracts

| User asks for | Load | Run | Deliver |
| --- | --- | --- | --- |
| "turn my program into a thesis" | `source-to-thesis-workflow.md` | `build_project_evidence.py` | evidence index, missing materials, chapter plan |
| "track thesis progress" | `workflow-state-management.md` | `init_workflow_logs.py` | `paper-context/workflow/*.md` status files |
| "make the standard generic" | `standards-and-template-resolution.md` | `check_thesis_workspace.py` | standards priority, template profile, unsupported assumptions |
| "handle PDF literature" | `literature-and-pdf-workflow.md` | `extract_pdf_references.py`, `build_literature_crossrefs.py` | candidate references, citation cross-reference index, verification list |
| "lower AIGC flavor" | `aigc-style-governance.md` | `analyze_aigc_style.py` | style-risk report first, then targeted revision after confirmation |
| "revise by Word comments" | `word-comment-revision-workflow.md` | `extract_docx_comments.py` | comment todo list, revision plan, revised DOCX, change log |
| "write or revise a chapter" | `rapid-thesis-workflow.md`, then the matching detailed workflow | validation scripts if files changed | chapter draft plus evidence gaps |
| "final check" | `quality-gates.md` | `check_thesis_workspace.py` and applicable format checks | critical/major/minor findings and remaining manual review |

## Required Read Order

When `thesis-ai-standard/` exists, read:

1. `thesis-ai-standard/README.md`
2. the public-standards guide in `thesis-ai-standard/`
3. `thesis-ai-standard/templates/standard-profile.yaml`
4. `thesis-ai-standard/templates/thesis-ai-spec.yaml`
5. `thesis-ai-standard/templates/figure-registry.yaml`
6. `paper-context/workflow/workflow-status.md` when it exists.
7. literature or citation templates only when the task involves references.
8. word-comment files only when the task involves DOCX comments.

If those files do not exist, bootstrap them from `assets/thesis-ai-standard/`.

## Core Workflow

1. Collect standards: school template, advisor instructions, task book, proposal.
2. Collect evidence: source code, database schema, API docs, screenshots, test reports, data, experiment logs, PDFs, existing drafts.
3. Fill `standard-profile.yaml` before interpreting formatting rules.
4. Fill `thesis-ai-spec.yaml` before drafting chapters.
5. Fill `figure-registry.yaml` before generating diagrams or screenshots.
6. Stop and list missing materials when a claim lacks evidence.
7. Draft chapter by chapter using `chapter-section-template.md`.
8. Review with `ai-review-rubric.json`, `check_thesis_workspace.py`, and the quality gates.

## Thesis Type Selection

Use the closest `type_profile`:

- `system_design`: software, app, mini program, website, management system, IoT, embedded system.
- `empirical_research`: experiment, algorithm/model evaluation, engineering test, statistical result.
- `survey_analysis`: questionnaire, interview, case study, user or industry analysis.
- `engineering_design`: engineering plan, product design, structure/process design, prototype validation.
- `literature_review`: literature matrix, topic comparison, method review, research trend.

Do not force non-software papers into the system-design chapter structure.

## Non-Negotiable Rules

- School and advisor rules override bundled defaults.
- National standards are fallback references unless the school explicitly adopts them.
- Never invent functions, fields, API paths, tests, experiment data, samples, citations, DOI values, or school requirements.
- Never expose AI workflow language in thesis body text.
- Never frame AIGC work as bypassing a detector. Frame it as academic style, evidence density, source integrity, and revision transparency.
- For Word-format-sensitive thesis revisions, do not replace the whole body through markdown/pandoc round-trip by default. Preserve the original `.docx` structure and edit the minimum necessary text in place.
- Every figure/table/equation/screenshot must have source, ID, title, first mention, and status.
- PDF reference extraction creates candidates only; verify bibliography before final writing.
- Claim completion only after running relevant script validation or clearly stating what could not be verified.

## Bundled References

- `references/standards-and-template-resolution.md`: source priority, current public standards, and school-template conflict handling.
- `references/source-to-thesis-workflow.md`: program/source-code to thesis evidence workflow.
- `references/literature-and-pdf-workflow.md`: PDF reference extraction and citation cross-reference workflow.
- `references/aigc-style-governance.md`: report-first AIGC style-risk review and academic prose revision workflow.
- `references/workflow-state-management.md`: markdown progress logs and step-state workflow.
- `references/word-comment-revision-workflow.md`: extract DOCX comments, revise safely, and log changes.
- `references/rapid-thesis-workflow.md`: short path for common thesis package tasks.
- `references/quality-gates.md`: final validation checklist.

## Bundled Scripts

- `scripts/init_thesis_workspace.py`: copy `assets/thesis-ai-standard/` into a project.
- `scripts/init_workflow_logs.py`: create `paper-context/workflow/*.md` progress files.
- `scripts/build_project_evidence.py`: create source-code evidence files for system-design papers.
- `scripts/extract_pdf_references.py`: extract candidate reference sections from PDFs.
- `scripts/build_literature_crossrefs.py`: map extracted references to thesis topics or chapter claims.
- `scripts/extract_docx_comments.py`: extract Word comments into JSON/Markdown revision todos.
- `scripts/check_thesis_workspace.py`: validate required templates, parse YAML/JSON/XML, and report missing core files.
- `scripts/analyze_aigc_style.py`: generate a style-risk report for thesis prose before targeted revision.
