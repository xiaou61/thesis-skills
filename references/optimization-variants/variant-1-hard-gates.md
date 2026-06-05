# Variant 1: Hard Gates Enhancement

## Positioning

This variant strengthens the existing final gate so the skill refuses to call a thesis complete when deterministic Word, citation, figure, or structure defects remain.

It is the safest near-term upgrade because every rule can be checked locally with low ambiguity.

## External Patterns Absorbed

- Vale and GitHub Docs content-linter style: small named rules with severity and machine-readable output.
- validocx/openxml-audit/docx-mcp style: inspect the DOCX package, styles, relationships, fields, comments, and hidden structure rather than relying on visual review.
- paper-writer-skill stage-gate style: a stage cannot pass by intention; it passes only with fresh check output.

## New Rule Groups

1. Document component completeness
   - Chinese abstract and keywords exist.
   - English abstract and keywords exist.
   - Table of contents exists and is a Word field.
   - Main chapters exist in the expected order.
   - References, acknowledgement, and appendix rules follow the school profile.

2. Citation closure
   - Every in-text numeric citation maps to a reference entry.
   - Every reference entry is cited at least once unless the school allows uncited background references.
   - Citation numbers are continuous and not duplicated incorrectly.
   - DOI, year, volume, issue, and page values are not fabricated when absent from evidence.

3. Figure/table closure
   - Every figure/table caption is referenced in body text before or near the object.
   - Body mentions such as `图4-2` and `表3-1` point to real objects.
   - Figure captions are below figures; table captions are above tables.
   - Numbering is chapter-scoped and continuous.

4. DOCX structural hygiene
   - No unresolved comments.
   - No tracked changes.
   - No hidden text in thesis body.
   - No broken relationships to media, embedded OLE, styles, numbering, or headers/footers.
   - No duplicate static preview when a Visio OLE object is already embedded.

5. Style and safety residue
   - No `Table Grid` table unless school profile explicitly allows it.
   - No AI workflow language in thesis body.
   - No placeholder screenshot text in final body; screenshot gaps must live in the registry/report.
   - No manuscript metadata that exposes assistant workflow or temporary file names.

## Proposed Files

- `scripts/check_docx_components.py`
- `scripts/check_docx_citation_closure.py`
- `scripts/check_docx_caption_closure.py`
- `scripts/check_docx_structural_hygiene.py`
- `references/hard-gate-rule-catalog.md`
- update `scripts/check_final_thesis_docx.ps1` to call these checks.

## Acceptance Criteria

A demo thesis passes only when:

- Current aggregate gate still passes.
- Component completeness check reports zero critical failures.
- Citation closure reports zero missing references and zero orphan critical entries.
- Caption closure reports zero missing object references.
- Structural hygiene reports zero comments, zero tracked changes, zero hidden body text, and zero broken package relationships.

## Strengths

- Fastest to implement.
- Low false-positive risk.
- Excellent at preventing embarrassing formatting and integrity mistakes.

## Limits

- It prevents bad output, but it does not by itself make the prose more human or the template match more exact.
- It cannot judge whether an argument is convincing beyond deterministic structural evidence.
