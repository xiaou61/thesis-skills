# Workflow State Management

Use this reference when a thesis project needs persistent progress tracking, step-by-step execution records, or a clear "where are we now" state.

## Goal

Create a thesis workbench under `paper-context/workflow/` so the agent can resume work without guessing.

## Bootstrap

Run:

```powershell
python C:\Users\Lenovo\.codex\skills\thesis-standardizer\scripts\init_workflow_logs.py .
```

`init_thesis_workspace.py` runs this automatically unless `--no-workflow-logs` is used.

## Generated Files

| File | Purpose |
| --- | --- |
| `workflow-status.md` | Current stage, next action, overall status |
| `step-plan.md` | Step-by-step task board with dependencies |
| `progress-log.md` | Chronological work-session log |
| `material-inventory.md` | School, project, evidence, and literature inventory |
| `evidence-gaps.md` | Unsupported claims and missing materials |
| `chapter-progress.md` | Chapter-level drafting/review status |
| `revision-log.md` | Human-readable table of all changes from comments, AIGC pass, standards, figures, and final review |
| `revision-trace.jsonl` | Machine-readable append-only trace of the same changes |

## Update Rules

At the start of a thesis task:

1. Read `workflow-status.md`.
2. Read `step-plan.md`.
3. Read the module-specific files for the user's request.
4. Update current stage and next action before doing substantial work.

At the end of a thesis task:

1. Append an entry to `progress-log.md`.
2. Update `step-plan.md` statuses.
3. Update `chapter-progress.md` if chapter work changed.
4. Add unresolved materials to `evidence-gaps.md`.
5. Add actual edits to `revision-log.md` and `revision-trace.jsonl`.

Use the helper when possible:

```powershell
python C:\Users\Lenovo\.codex\skills\thesis-standardizer\scripts\append_revision_log.py --workspace . --source "AIGC style pass" --location "第3章 P012" --change "删去套句并补充证据边界" --reason "aigc-style-report.md 标记为 high risk" --evidence "paper-context/aigc/aigc-style-report.md P012" --before "综上所述..." --after "本节测试结果显示..." --files "draft.docx,paper-context/aigc/aigc-style-report.md" --status needs_review
```

## Revision Trace Requirements

For every material change, record:

- location: chapter, section, paragraph ID, figure/table ID, Word comment ID, or file path
- before: short excerpt or summary of the original state
- after: short excerpt or summary of the revised state
- change: concrete action, not just "polished"
- reason: user request, advisor comment, AIGC report, evidence gap, school standard, or final review
- evidence: source file, citation, screenshot, test report, detector report, style report, or `needs_evidence`
- files: touched files
- status: `done`, `needs_review`, `blocked`, or `reverted`

For AIGC work, every rewritten high/medium-risk paragraph must have a trace entry. For final paragraph pass, paragraph IDs in `aigc-final-paragraph-pass.md` must match the revision log locations.

## Status Vocabulary

Use these values consistently:

- `pending`: not started
- `in_progress`: currently being worked on
- `blocked`: cannot proceed without material or decision
- `needs_review`: generated but needs human/school/template review
- `done`: verified enough for the current stage
- `deprecated`: no longer used

## Non-Negotiable Rule

Do not silently skip log updates after changing thesis content or workflow state. The workbench is the memory of the thesis project. A revision without a trace entry is not considered complete.
