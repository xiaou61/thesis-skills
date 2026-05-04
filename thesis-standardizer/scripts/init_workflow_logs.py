#!/usr/bin/env python3
"""Create markdown workflow logs for a thesis workspace."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path


WORKFLOW_FILES: dict[str, str] = {
    "workflow-status.md": """# Thesis Workflow Status

Generated: {today}

## Current State

- Current stage: `intake`
- Current owner: `AI + user`
- Thesis draft status: `not_started | planning | drafting | revising | formatting | final_review`
- Word document status: `not_uploaded | comments_extracted | revision_planned | revised | pdf_checked`
- Next action: Fill `standard-profile.yaml`, `thesis-ai-spec.yaml`, and evidence inputs.

## Stage Tracker

| Stage | Status | Output | Notes |
| --- | --- | --- | --- |
| 1. Intake materials | in_progress | material inventory | Upload school template, task book, draft, code, PDFs, screenshots |
| 2. Resolve standards | pending | `standard-profile.yaml` | School/advisor rules first |
| 3. Build evidence | pending | `paper-context/evidence/` | Source code, tests, screenshots, data |
| 4. Build literature map | pending | `paper-context/literature/` | PDF extraction and citation closure |
| 5. Plan figures/tables | pending | `figure-registry.yaml` | Every item needs source and first mention |
| 6. Draft chapters | pending | chapter drafts | Evidence first, prose second |
| 7. Word comment revision | pending | `paper-context/word-comments/` | Extract comments, revise, log changes |
| 8. AIGC detection/style pass | pending | `paper-context/aigc/` | Optional rate estimate, style report, targeted revision, final paragraph pass with token warning |
| 9. Final review | pending | review report | Quality gates, Word/PDF visual review |

## Latest Decision

- None yet.
""",
    "step-plan.md": """# Thesis Step Plan

## How To Use

Keep this file as the task board for the thesis. Move each item through:
`pending -> in_progress -> blocked -> done`.

## Steps

| ID | Step | Status | Depends On | Deliverable |
| --- | --- | --- | --- | --- |
| S1 | Collect school template, task book, advisor notes | pending | none | material inventory |
| S2 | Fill standards profile | pending | S1 | `standard-profile.yaml` |
| S3 | Scan program/source evidence | pending | source project | `paper-context/evidence/` |
| S4 | Extract PDF references | pending | PDF folder | `paper-context/literature/reference-extraction.md` |
| S5 | Build citation cross-references | pending | S4 + topic outline | `citation-crossrefs.md` |
| S6 | Fill thesis facts | pending | S2-S5 | `thesis-ai-spec.yaml` |
| S7 | Plan figures/tables/equations | pending | S6 | `figure-registry.yaml` |
| S8 | Draft chapters | pending | S6-S7 | chapter drafts |
| S9 | Extract Word comments | pending | `.docx` draft | `word-comment-todos.md` |
| S10 | Revise by comments | pending | S9 | revised `.docx` + `docx-revision-log.md` |
| S11 | Run AIGC detection/style reports / optional final paragraph pass | pending | chapter drafts | `aigc-detection-report.md`, `aigc-style-report.md`, optional `aigc-final-paragraph-pass.md` |
| S12 | Update revision trace logs | pending | S8-S11 | `revision-log.md` + `revision-trace.jsonl` |
| S13 | Final quality gate | pending | S8-S12 | final review report |
""",
    "progress-log.md": """# Thesis Progress Log

Use one entry per work session.

## Entries

### {today}

- Action: Initialized thesis workflow logs.
- Inputs used: none
- Outputs created: workflow markdown files
- Decisions: none
- Blockers: fill real project and school materials
- Next action: complete material inventory and standards profile
""",
    "material-inventory.md": """# Material Inventory

## School And Advisor Materials

| Material | Path | Status | Notes |
| --- | --- | --- | --- |
| School template |  | missing |  |
| Task book |  | missing |  |
| Proposal/opening report |  | missing |  |
| Advisor comments |  | missing |  |

## Project / Research Evidence

| Material | Path | Status | Notes |
| --- | --- | --- | --- |
| Source code |  | missing |  |
| Database schema |  | missing |  |
| API docs |  | missing |  |
| Screenshots |  | missing |  |
| Test reports |  | missing |  |
| Experiment/data files |  | missing |  |

## Literature

| Material | Path | Status | Notes |
| --- | --- | --- | --- |
| PDF papers | `papers/` | missing |  |
| Existing reference list |  | missing |  |
""",
    "evidence-gaps.md": """# Evidence Gaps

Record every claim that cannot yet be supported.

| ID | Claim or section | Missing evidence | Severity | Owner | Status |
| --- | --- | --- | --- | --- | --- |
| GAP-001 |  |  | major | user/AI | open |
""",
    "chapter-progress.md": """# Chapter Progress

| Chapter | Purpose | Evidence Ready | Draft Status | Review Status | Notes |
| --- | --- | --- | --- | --- | --- |
| Chapter 1 Introduction | background, value, scope | no | not_started | not_started | write after core facts are known |
| Chapter 2 Theory/Technology | method and stack | no | not_started | not_started |  |
| Chapter 3 Requirements/Design | requirements or research design | no | not_started | not_started |  |
| Chapter 4 Overall Design/Process | architecture, process, data | no | not_started | not_started |  |
| Chapter 5 Implementation/Results | implementation or analysis | no | not_started | not_started |  |
| Chapter 6 Testing/Discussion | tests, validation, discussion | no | not_started | not_started |  |
| Conclusion | summary and limits | no | not_started | not_started | write last |
""",
    "revision-log.md": """# Revision Log

Use this file for all thesis changes, including Word comments, AIGC style edits, figure/table changes, and standard fixes.

Every material text change must be traceable:

1. where it changed
2. what changed
3. why it changed
4. what evidence or report justified it
5. which files were touched
6. whether any source/evidence gap remains

| ID | Date | Source | Location | Before | After | Change | Reason | Evidence | Files | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REV-001 | {today} | initialization | workspace | - | workflow absent | Created workflow logs | initialize traceability workbench | script output | paper-context/workflow/* | done |
""",
    "revision-trace.jsonl": """{{"id":"REV-001","date":"{today}","source":"initialization","location":"workspace","before":"-","after":"workflow logs created","change":"Created workflow logs","reason":"initialize traceability workbench","evidence":"script output","files":["paper-context/workflow/*"],"status":"done","needs_source":"none","needs_evidence":"none"}}
""",
}


def write_workflow_logs(target: Path, overwrite: bool = False) -> list[Path]:
    workflow_dir = target / "paper-context" / "workflow"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    written: list[Path] = []
    for name, template in WORKFLOW_FILES.items():
        path = workflow_dir / name
        if path.exists() and not overwrite:
            continue
        path.write_text(template.format(today=today), encoding="utf-8")
        written.append(path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize thesis workflow markdown logs.")
    parser.add_argument("target", nargs="?", default=".", help="Project directory.")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing workflow files.")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    target.mkdir(parents=True, exist_ok=True)
    written = write_workflow_logs(target, overwrite=args.overwrite)
    print(f"Workflow directory: {target / 'paper-context' / 'workflow'}")
    if written:
        for path in written:
            print(f"- wrote {path}")
    else:
        print("No files written; existing files were preserved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
