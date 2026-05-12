---
name: thesis-standardizer
description: Standardize and draft undergraduate thesis or graduation-design papers from source code, school templates, task books, drafts, screenshots, databases, APIs, experiments, automated scholarly literature searches, PDF literature, and test evidence. Use when the user asks to write, generate, refactor, check, or package a thesis; turn a program into thesis chapters; automatically generate literature search configs, harvest and verify real Chinese/English references, create thesis specs, figure registries, evidence indexes, PDF reference extraction, citation cross-reference maps, AIGC rate estimates, AIGC style-risk reports, academic prose revision reports, or school-rule enforcement before drafting.
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
3. Literature module: keyword literature harvest, PDF extraction, citation cross-references, reference closure.
4. AIGC detection module: local `aigc-reduce`-style scan with template-phrase, burstiness, passive-voice, numbering, and punctuation triage.
5. AIGC style-governance module: `aigc-reduce` three-round protocol, deep-pattern audit, targeted revision, and token-heavy paragraph-by-paragraph final pass.
6. Traceability module: workflow logs, revision ledger, JSONL change trace, and evidence-gap records.
7. Output module: final quality gates, Word/PDF handoff, residual risks.

## Decision Tree

- New thesis workspace or missing templates: run `scripts/init_thesis_workspace.py <target-dir>`.
- Standards, school-template interpretation, or version conflicts: read `references/standards-and-template-resolution.md`.
- Program/source-code thesis: read `references/source-to-thesis-workflow.md`; run `scripts/build_project_evidence.py <project-dir> --out paper-context/evidence`.
- Literature search, open full-text collection, or missing PDF set: read `references/literature-harvest-workflow.md`; auto-generate the search config first unless the user supplied exact requirements, then run harvest, resume, second-pass, dedup, and verified selection before PDF extraction.
- PDF literature, related work, or citations from existing PDFs: read `references/literature-and-pdf-workflow.md`; run the PDF extraction and citation cross-reference scripts.
- AIGC rate, AI percentage, detector-style report, or before/after score estimate: read `references/aigc-detection-workflow.md`; run `scripts/detect_aigc_rate.py <draft-file> --out paper-context/aigc/aigc-detection-report.md --json-out paper-context/aigc/aigc-detection-report.json`.
- AIGC, AI flavor, templated prose, academic style naturalness, paragraph-level humanizing, or style report: read `references/aigc-style-governance.md`; run `scripts/analyze_aigc_style.py <draft-file> --out paper-context/aigc/aigc-style-report.md`.
- AIGC revision planning, deterministic reduction plan, or paragraph-by-paragraph replacement plan: read `references/aigc-style-governance.md`; run `scripts/build_aigc_revision_plan.py <draft-file> --out paper-context/aigc/aigc-revision-plan.md --json-out paper-context/aigc/aigc-revision-plan.json`.
- "AIGC final reduction version", "整篇逐段降低", or similar full-paper final pass: run `scripts/analyze_aigc_style.py <draft-file> --out paper-context/aigc/aigc-style-report.md --json-out paper-context/aigc/aigc-style-report.json --final-paragraph-pass-out paper-context/aigc/aigc-final-paragraph-pass.md`; warn the user that this mode is extremely token-consuming.
- Existing draft or Word-format-sensitive work: use this skill for standards/evidence, then use `thesis-docx`/`docx` for Word layout and PDF review.
- DOCX creation, editing, template alignment, or final Word delivery: read `references/docx-production-rules.md` before changing Word-format-sensitive files.
- Finalized thesis revision, second-round editing, or any `.docx` with stable TOC/cross-references/figure anchors: prefer in-place targeted edits inside a copied original `.docx`; avoid pandoc body round-trips unless the user explicitly accepts layout rebuild risk.
- Any content, citation, figure/table, AIGC, Word-comment, or standards edit: read `references/workflow-state-management.md`; append trace entries with `scripts/append_revision_log.py` or update `paper-context/workflow/revision-log.md` and `revision-trace.jsonl` manually.
- Before final delivery: read `references/quality-gates.md` and run `scripts/check_thesis_workspace.py <workspace>` when a `thesis-ai-standard/` folder exists.

## Mode Contracts

| User asks for | Load | Run | Deliver |
| --- | --- | --- | --- |
| "turn my program into a thesis" | `source-to-thesis-workflow.md` | `build_project_evidence.py` | evidence index, missing materials, chapter plan |
| "make the standard generic" | `standards-and-template-resolution.md` | `check_thesis_workspace.py` | standards priority, template profile, unsupported assumptions |
| "find papers/references" | `literature-harvest-workflow.md` | `generate_literature_search_config.py`, `run_keyword_harvest_no_dedup.py`, `continue_download_and_dedup.py`, `verify_select_literature.py` | generated search config, candidate table, download log, deduplicated files, verified Chinese/English selection, shortage list |
| "handle PDF literature" | `literature-and-pdf-workflow.md` | `extract_pdf_references.py`, `build_literature_crossrefs.py` | candidate references, citation cross-reference index, verification list |
| "detect AIGC rate" | `aigc-detection-workflow.md` | `detect_aigc_rate.py` | estimated rate, scan-dimension summary, paragraph risk findings |
| "lower AIGC flavor" | `aigc-style-governance.md` | `analyze_aigc_style.py` | style-risk report first, then targeted revision after confirmation |
| "build AIGC revision plan" | `aigc-style-governance.md` | `build_aigc_revision_plan.py` | deterministic paragraph actions for round 1/2/3 |
| "AIGC final reduction version" / "逐段降低" | `aigc-style-governance.md` | `analyze_aigc_style.py --final-paragraph-pass-out ...` | paragraph work order, explicit token warning, paragraph-aligned rewrite plan |
| "record changes" / "追溯修改" | `workflow-state-management.md` | `append_revision_log.py` | human-readable revision log plus JSONL trace |
| "write or revise a chapter" | `rapid-thesis-workflow.md`, then the matching detailed workflow | validation scripts if files changed | chapter draft plus evidence gaps |
| "final check" | `quality-gates.md` | `check_thesis_workspace.py` and applicable format checks | critical/major/minor findings and remaining manual review |

## Required Read Order

When `thesis-ai-standard/` exists, read:

1. `thesis-ai-standard/README.md`
2. the public-standards guide in `thesis-ai-standard/`
3. `thesis-ai-standard/templates/standard-profile.yaml`
4. `thesis-ai-standard/templates/thesis-ai-spec.yaml`
5. `thesis-ai-standard/templates/figure-registry.yaml`
6. literature harvest, review, or citation templates only when the task involves references.

If those files do not exist, bootstrap them from `assets/thesis-ai-standard/`.

## Core Workflow

1. Collect standards: school template, advisor instructions, task book, proposal.
2. Collect evidence: source code, database schema, API docs, screenshots, test reports, data, experiment logs, keyword-harvest logs, PDFs, existing drafts.
3. Fill `standard-profile.yaml` before interpreting formatting rules.
4. Fill `thesis-ai-spec.yaml` before drafting chapters.
5. Fill `figure-registry.yaml` before generating diagrams or screenshots.
6. For literature, generate search terms from thesis materials by default; user-specified search requirements override defaults.
7. For literature years, default to the recent 6 years based on the user's current year; user, school, advisor, or task-book year requirements override this default.
8. Before planning body citations, ask whether literature coverage should apply to the full body or only front research/theory chapters.
9. Keep each body citation point to at most 2 references; split larger source groups across separate claims, sentences, or matrix notes instead of clustering citations.
10. Stop and list missing materials when a claim lacks evidence.
11. For every material change, record location, before/after summary, reason, evidence, touched files, and status in `paper-context/workflow/revision-log.md` and `revision-trace.jsonl`.
12. Draft chapter by chapter using `chapter-section-template.md`; do not place citations in the abstract unless school rules require it.
13. Review with `ai-review-rubric.json`, `check_thesis_workspace.py`, and the quality gates.

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
- AIGC-rate output from bundled scripts is a local heuristic estimate only; never present it as a school or third-party official detector score.
- For paragraph-by-paragraph final AIGC reduction, explicitly state: "AIGC 最终降低版会按论文文本分割后逐段处理、逐段复查、再拼接全文，极度消耗 token。"
- No substantive thesis edit is complete until `revision-log.md` or `revision-trace.jsonl` records what changed, where it changed, why it changed, and what evidence supports it.
- For Word-format-sensitive thesis revisions, do not replace the whole body through markdown/pandoc round-trip by default. Preserve the original `.docx` structure and edit the minimum necessary text in place.
- Every figure/table/equation/screenshot must have source, ID, title, first mention, and status.
- Keyword harvest and PDF reference extraction create candidates only; verify bibliography before final writing.
- Default literature selection is Chinese `12-15` and English `3-5` unless the user or school requires otherwise.
- Default literature publication years are the recent 6 years based on the user's current year, including the current year; if the current year is 2026, use `2021-2026` unless the user or school specifies another range.
- User search requirements override automatic defaults.
- Do not output references that cannot be located by DOI, database record, stable URL, downloaded file, or user-provided export.
- Reject out-of-range or missing-year literature by default; only keep missing-year records when the user accepts manual year verification.
- Do not add citations in the abstract unless the school template explicitly requires them.
- Each body citation point may cite at most 2 references; never cluster 3 or more references after one sentence or one claim.
- Claim completion only after running relevant script validation or clearly stating what could not be verified.

## Bundled References

- `references/standards-and-template-resolution.md`: source priority, current public standards, and school-template conflict handling.
- `references/source-to-thesis-workflow.md`: program/source-code to thesis evidence workflow.
- `references/literature-harvest-workflow.md`: keyword scholarly search, legal full-text collection, HTML/XML handling, second-pass PDF chase, and file deduplication.
- `references/literature-and-pdf-workflow.md`: PDF reference extraction and citation cross-reference workflow.
- `references/aigc-detection-workflow.md`: local `aigc-reduce` scan workflow and before/after comparison guidance.
- `references/aigc-style-governance.md`: `aigc-reduce` three-round style-governance workflow, targeted paragraph revision, and final paragraph pass.
- `vendor/aigc-reduce/`: mirrored upstream rules, replacement tables, and scan script from `xiaofenggan01/aigc-reduce`.
- `references/workflow-state-management.md`: persistent workflow status, progress, evidence gaps, and traceable revision logs.
- `references/rapid-thesis-workflow.md`: short path for common thesis package tasks.
- `references/quality-gates.md`: final validation checklist.
- `references/docx-production-rules.md`: DOCX-safe operating baseline, fallback Chinese academic defaults, and verification contract.

## Bundled Scripts

- `scripts/init_thesis_workspace.py`: copy `assets/thesis-ai-standard/` into a project.
- `scripts/build_project_evidence.py`: create source-code evidence files for system-design papers.
- `scripts/generate_literature_search_config.py`: infer literature search queries and target counts from thesis materials.
- `scripts/run_keyword_harvest_no_dedup.py`: search scholarly APIs, create a no-dedup candidate table, and download accessible PDFs or HTML/XML full texts.
- `scripts/continue_download_and_dedup.py`: resume downloads, run HTML-to-PDF second pass, and deduplicate downloaded files.
- `scripts/verify_select_literature.py`: select verifiable Chinese and English literature and report shortages without fabricating references.
- `scripts/extract_pdf_references.py`: extract candidate reference sections from PDFs.
- `scripts/build_literature_crossrefs.py`: map extracted references to thesis topics or chapter claims.
- `scripts/check_thesis_workspace.py`: validate required templates, parse YAML/JSON/XML, and report missing core files.
- `scripts/detect_aigc_rate.py`: estimate a text's AIGC-style risk using the `aigc-reduce` scan dimensions and paragraph findings.
- `scripts/analyze_aigc_style.py`: generate a style-risk report for thesis prose using the `aigc-reduce` deep-pattern audit; optionally emit a token-heavy final paragraph pass work order.
- `scripts/build_aigc_revision_plan.py`: build a deterministic paragraph-by-paragraph revision plan using the `aigc-reduce` three-round protocol.
- `scripts/append_revision_log.py`: append traceable change records to `paper-context/workflow/revision-log.md` and `revision-trace.jsonl`.
