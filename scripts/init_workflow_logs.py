#!/usr/bin/env python3
"""Create compact workflow logs for a program-to-thesis workspace."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path


WORKFLOW_FILES: dict[str, str] = {
    "workflow-status.md": """# Thesis Workflow Status

Generated: {today}

## Current State

- Current stage: `intake`
- Thesis draft status: `not_started | planning | drafting | revising | formatting | final_review`
- Next action: fill `standard-profile.yaml`, `thesis-ai-spec.yaml`, `figure-registry.yaml`, and project evidence.

## Stage Tracker

| Stage | Status | Output | Notes |
| --- | --- | --- | --- |
| 1. Collect materials | in_progress | material inventory | school template, source code, screenshots, tests |
| 2. Extract template rules | pending | `paper-context/template-extract/` | only if a school `.docx` template exists |
| 3. Build project evidence | pending | `paper-context/evidence/` | code, APIs, database, tests |
| 4. Fill core planning files | pending | three YAML/registry files | standards, facts, figures |
| 5. Draft chapters | pending | chapter drafts | evidence first, prose second |
| 6. Generate figures/tables | pending | `.vsdx`, `.png`, table sources | use-case, function architecture, E-R, three-line tables |
| 7. Final review | pending | review report | evidence, figures, Word format risk |
""",
    "material-inventory.md": """# Material Inventory

| Material | Path | Status | Notes |
| --- | --- | --- | --- |
| School template |  | missing | optional but preferred |
| Source code |  | missing | required |
| Database schema |  | missing | required if the system uses a database |
| API docs or route files |  | missing | required if the system has APIs |
| Screenshots |  | missing | needed for UI/implementation evidence |
| Test reports or logs |  | missing | needed for Chapter 6 |
| Reference list |  | missing | needed mainly for Chapters 1-3 |
""",
    "evidence-gaps.md": """# Evidence Gaps

| ID | Claim or section | Missing evidence | Severity | Owner | Status |
| --- | --- | --- | --- | --- | --- |
| GAP-001 |  |  | major | user/AI | open |
""",
    "chapter-progress.md": """# Chapter Progress

| Chapter | Purpose | Evidence Ready | Draft Status | Notes |
| --- | --- | --- | --- | --- |
| Chapter 1 Introduction | background, significance, research status | no | not_started | citation-heavy |
| Chapter 2 Related technologies | technologies used by the system | no | not_started | citation-heavy |
| Chapter 3 System analysis | requirements, roles, use cases | no | not_started | Visio use-case diagram |
| Chapter 4 System design | function structure, architecture, database/data objects | no | not_started | function diagram, E-R, three-line tables |
| Chapter 5 System implementation | key modules, running functions, screenshots | no | not_started | real screenshots or needs_user_screenshot |
| Chapter 6 System testing | environment, cases, results, summary | no | not_started | write only from evidence; include summary/limits/future work unless a standalone conclusion chapter is required |
| Optional Chapter 7 Conclusion | summary, limits, future work | no | not_started | create only when school template/user requires it |
""",
    "revision-log.md": """# Revision Log

Use this file for material thesis changes.

| ID | Date | Source | Location | Change | Reason | Evidence | Files | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REV-001 | {today} | initialization | workspace | Created workflow logs | initialize traceability | script output | paper-context/workflow/* | done |
""",
    "revision-trace.jsonl": """{{"id":"REV-001","date":"{today}","source":"initialization","location":"workspace","change":"Created workflow logs","reason":"initialize traceability","evidence":"script output","files":["paper-context/workflow/*"],"status":"done"}}
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
    parser = argparse.ArgumentParser(description="Initialize compact thesis workflow logs.")
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
