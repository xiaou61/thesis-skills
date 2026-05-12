# Quality Gates

Use this before saying the thesis work is complete.

## Gate 1: Standards

Check:

- `standard-profile.yaml` exists
- school/advisor rules are explicit
- reference style version is explicit
- Word/PDF layout-sensitive items were actually checked

## Gate 2: Evidence

Check:

- `thesis-ai-spec.yaml` has real facts
- `figure-registry.yaml` lists figures/tables/equations/screenshots
- claimed functions map to code, screenshots, tests, or user materials
- claimed tests/experiments map to reports, logs, tables, or screenshots
- literature claims map to verified references
- each body citation point uses at most 2 references

## Gate 3: Integrity

Check:

- no fabricated references, DOI, data, APIs, fields, metrics, or screenshots
- no AI workflow leakage in thesis body text
- no private data exposed
- AIGC work is framed as writing-quality revision, not detector evasion

## Gate 4: Structure

Check:

- chapter structure matches thesis type
- titles and numbering are continuous
- introduction does not promise missing work
- conclusion summarizes completed work only

## Gate 5: AIGC

When AIGC work was requested, check:

- `aigc-detection-report.md` exists if detection was requested
- `aigc-style-report.md` exists if style reduction was requested
- high-risk paragraphs were revised or explicitly left unchanged with reasons
- vague attribution was removed, verified, or marked `needs_source`
- no unsupported facts or citations were added
- if final pass was used, `aigc-final-paragraph-pass.md` exists

## Gate 6: Traceability

Check:

- `revision-log.md` exists for revision tasks
- `revision-trace.jsonl` exists when helper script is available
- each material edit has location, before/after, change, reason, evidence, files, status

## Gate 7: Figures / Tables / Equations

Check:

- captions are in the right place unless school rules differ
- every figure/table/equation is mentioned in text
- structural diagrams have editable source
- formula variables and units are explained

## Gate 8: Script Validation

Run applicable checks:

```powershell
Get-ChildItem .\thesis-standardizer\scripts\*.py | ForEach-Object { python -m py_compile $_.FullName }
python .\thesis-standardizer\scripts\check_thesis_workspace.py .\thesis-standardizer\assets\thesis-ai-standard
python .\thesis-standardizer\scripts\run_aigc_repair_loop.py .\sample-draft.md --workspace .
```

## Completion Report

Always report:

1. what was generated or changed
2. what was verified
3. what still needs human/template review
4. what evidence is still missing
