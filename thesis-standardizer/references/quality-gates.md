# Quality Gates

Use before saying a thesis package, chapter draft, or review is complete.

## Gate 1: Standards

- `standard-profile.yaml` exists and identifies school/advisor rules.
- `template-rule-overrides.yaml` exists when a school `.docx` template was supplied.
- A template comparison report exists when final `.docx` delivery is checked against a supplied school template.
- If automatic repair was used, a repair report exists and the repaired `.docx` was re-compared against the template.
- Body-start section inferred from the template is reviewed, especially when cover, abstract, TOC, and正文 are split across multiple sections.
- Explicit Arabic page numbering starts in the same section as the inferred body-start section, unless the school template clearly uses another rule.
- Front-matter sections before the inferred body-start section do not introduce explicit Arabic page-number settings unless the school template explicitly does so.
- Later body sections do not introduce unexpected page-number restarts unless the school template explicitly resets numbering there.
- If the template uses Roman numerals in front matter and Arabic numerals in the body, that format switch is preserved at the same section boundary.
- Explicit page-number restart events after body start follow the same section sequence and restart values as the template.
- Back-matter sections such as `参考文献` / `附录` follow the same restart-or-continue page-number policy as the template.
- If the template uses dedicated TOC sections, the TOC-to-body section boundary is preserved in the thesis document.
- Reference style version is explicit.
- Bundled defaults are marked as fallback, not school requirements.
- Standard conflicts are resolved using `standards-and-template-resolution.md`.
- Word/PDF layout-sensitive items are not claimed verified unless they were checked.

## Gate 2: Evidence

- `thesis-ai-spec.yaml` contains the thesis type and real facts.
- `figure-registry.yaml` lists each figure, table, equation, screenshot, and source.
- Claimed functions map to code, screenshots, tests, or user-provided materials.
- Claimed tests or experiments map to reports, logs, tables, or screenshots.
- Literature claims map to verified references or explicit `needs_check` candidates.
- Each body citation point uses at most 2 references; no sentence or claim has 3 or more clustered citations.

## Gate 3: Academic Integrity

- No fabricated references, DOI values, years, journals, APIs, fields, test results, samples, or metrics.
- No clustered citations used to inflate reference density.
- No AI workflow leakage in body text.
- PDF reference extraction is treated as candidate evidence until verified.
- Private data, tokens, account names, phone numbers, and keys are not exposed in screenshots or prose.
- AIGC style work is framed as academic writing quality review, not detector evasion.

## Gate 4: Structure

- Chapter structure matches `type_profile`.
- Chapter titles and numbering are continuous.
- Introduction does not promise work absent from later chapters.
- Conclusion summarizes completed work only.

## Gate 4.5: AIGC Style Governance

- `aigc-detection-report.md` exists when the user requested AIGC-rate detection.
- AIGC-rate estimates are framed as local heuristic estimates, not official detector scores.
- `aigc-style-report.md` exists when the user requested AIGC/style reduction.
- High-risk paragraphs were revised or explicitly left unchanged with reasons.
- Vague attribution was removed, verified, or marked `needs_source`.
- Generic positive conclusions were replaced with concrete claims, limits, or future work.
- Revisions did not add unsupported facts or citations.
- If final paragraph pass was used, `aigc-final-paragraph-pass.md` exists, the token-cost warning was shown, paragraph IDs stayed aligned, and the final text was checked for cross-paragraph cohesion.

## Gate 4.6: Revision Traceability

- `paper-context/workflow/revision-log.md` exists for any revision task.
- `paper-context/workflow/revision-trace.jsonl` exists for machine-readable traceability when the helper script is available.
- Each material edit records location, before/after summary, change, reason, evidence, touched files, and status.
- Each high/medium-risk AIGC paragraph rewrite maps to a paragraph ID in the style report or final paragraph pass work order.
- Unresolved source or evidence gaps are recorded in `evidence-gaps.md` or marked in the revision record.

## Gate 5: Figures, Tables, Equations

- Figure captions are below figures unless school rules differ.
- Table captions are above tables unless school rules differ.
- Every figure/table/equation is mentioned in text before or near placement.
- Structural diagrams have editable sources.
- Formula variables and units are explained.

## Gate 6: Script Validation

Run applicable checks:

```powershell
Get-ChildItem .\thesis-standardizer\scripts\*.py | ForEach-Object { python -m py_compile $_.FullName }
python .\thesis-standardizer\scripts\check_thesis_workspace.py .\thesis-standardizer\assets\thesis-ai-standard
python .\thesis-standardizer\scripts\analyze_aigc_style.py .\sample-draft.md --out .\paper-context\aigc\aigc-style-report.md
python .\thesis-standardizer\scripts\compare_docx_to_template.py .\draft.docx .\paper-context\template-extract\template-profile.json --template-rule-overrides .\paper-context\template-extract\template-rule-overrides.yaml --out .\paper-context\template-compare\template-compare-report.md
python .\thesis-standardizer\scripts\repair_docx_from_template.py .\draft.docx .\paper-context\template-extract\template-profile.json --out-docx .\draft_repaired.docx --out-report .\paper-context\template-compare\template-repair-report.md
python .\thesis-standardizer\scripts\finalize_docx_with_template.py .\draft.docx .\paper-context\template-extract\template-profile.json --template-rule-overrides .\paper-context\template-extract\template-rule-overrides.yaml --workspace . --out-dir .\paper-context\template-compare
python .\thesis-standardizer\scripts\finalize_thesis_delivery.py .\draft.docx --workspace .
```

For generated thesis workspaces:

```powershell
python - <<'PY'
import json, yaml
from pathlib import Path
base = Path('thesis-ai-standard/templates')
for name in ['standard-profile.yaml', 'thesis-ai-spec.yaml', 'figure-registry.yaml']:
    yaml.safe_load((base / name).read_text(encoding='utf-8'))
json.loads((base / 'ai-review-rubric.json').read_text(encoding='utf-8'))
print('OK')
PY
```

On Windows PowerShell, use a here-string piped into Python if shell heredoc is unavailable.

## Completion Language

Report:

- what was generated or changed
- what was verified
- what still needs human/school-template review
- which evidence is missing, if any
