# Skill Rule Structure Research

This note defines a rule structure for `thesis-standardizer` that makes thesis quality gates easier to execute, score, repair, and report. It is intentionally local: no external research, no generation-script rewrites.

## Design Goal

The skill should separate thesis rules into three layers:

1. `must_gate`: deterministic delivery blockers. A failed rule stops any final `.docx` completion claim.
2. `should_score`: quality or completeness rules that produce a score and prioritized fix list.
3. `evidence_note`: contextual facts, accepted exceptions, and human/template review items.

This keeps hard rules from becoming prose reminders while still preserving softer reviewer judgment.

## Rule Record

Every reusable rule should be expressible as a small record:

| Field | Required | Purpose |
| --- | --- | --- |
| `id` | yes | Stable id such as `docx.citation.hyperlinks` or `figure.visio.ole`. |
| `level` | yes | `must_gate`, `should_score`, or `evidence_note`. |
| `stage` | yes | `intake`, `planning`, `draft`, `asset`, `final_docx`, or `handoff`. |
| `owner` | yes | The workflow role responsible for fixing it, e.g. `format_auditor`, `chapter_writer`, `diagram_planner`. |
| `trigger` | yes | When the rule applies. |
| `check` | yes for gates | Script, file inspection, or explicit manual evidence. |
| `pass_condition` | yes | Observable condition required to pass. |
| `failure_action` | yes | Repair, rerun, block, or report missing evidence. |
| `evidence` | yes | Exact command/output/report fields to include in final handoff. |
| `exception_policy` | yes | Who/what can override it and how the override is recorded. |

Example:

```yaml
id: docx.citation.hyperlinks
level: must_gate
stage: final_docx
owner: format_auditor
trigger: final DOCX contains numeric body citations
check: python scripts/check_docx_reference_hyperlinks.py <docx>
pass_condition: zero errors
failure_action: run apply_docx_reference_hyperlinks.py, then rerun aggregate gate
evidence: command, exit code, error count, citation count
exception_policy: no delivery override; rough drafts must label this as skipped
```

## Gate Levels

### `must_gate`

Use for rules that can make a delivered thesis objectively wrong or misleading:

- final `.docx` gate freshness
- template/profile compliance when a template exists
- component completeness and order
- citation closure and reference hyperlinks
- caption/object/body-reference closure
- three-line and continuation table rules
- thesis length and heading density thresholds
- thesis voice residue checks
- Visio OLE presence and duplicate-preview prevention
- DOCX structural hygiene
- no invented functions, APIs, fields, screenshots, tests, citations, DOI values, or school rules

Handling: fix and rerun; if not fixable, block and report the failed rule id plus missing evidence. Do not downgrade to a warning during final delivery.

### `should_score`

Use for rules that improve thesis quality but need judgment or may depend on scope:

- figure/table usefulness and chapter distribution
- chapter argument strength
- database/data-object design clarity
- screenshot coverage beyond the minimum
- test-case diversity
- template visual similarity beyond deterministic style/page checks
- prose naturalness after deterministic voice checks pass

Handling: score 0-5, record rationale, and fix the lowest high-impact scores first. A low score can block delivery only when the user/school threshold says so.

### `evidence_note`

Use for facts that guide the workflow but are not pass/fail:

- school/advisor exceptions
- unavailable Office/Visio automation
- user-provided acceptance of rough draft scope
- missing screenshots to collect later
- template differences intentionally preserved

Handling: include in handoff evidence so later workers do not re-litigate the same context.

## Failure Handling Contract

When a gate fails, the worker must produce one of four outcomes:

| Outcome | Use When | Required Evidence |
| --- | --- | --- |
| `repaired` | The issue was fixed locally. | Failed command, edit summary, rerun command, passing output. |
| `blocked_missing_evidence` | A true source artifact is missing. | Missing artifact list, affected thesis claim/section, safe placeholder location. |
| `blocked_tooling` | Required local tooling is unavailable. | Tool attempted, error, fallback attempted, delivery limitation. |
| `rough_draft_exception` | User explicitly requested a non-final draft. | User/school scope, skipped gate ids, statement that it is not final delivery. |

Never use "visual inspection", "looks fine", or "previously passed" as a gate result.

## Scoring Model

After all `must_gate` rules pass or are explicitly marked non-final, calculate a lightweight reviewer score:

| Dimension | Weight | Scoring Anchor |
| --- | ---: | --- |
| Evidence grounding | 20 | Claims map to code/database/API/screenshot/test/template/literature evidence. |
| Chapter completeness | 15 | Chapters 1-6 serve distinct roles and required sections exist. |
| Figure/table plan | 15 | Figures/tables are sufficient, referenced, useful, and backed by editable sources. |
| Template/format fidelity | 15 | Template checks pass and manual differences are explained. |
| Citation/reference quality | 10 | Deterministic citation gates pass and references suit the topic. |
| Thesis voice | 10 | Body reads like student thesis prose, not workflow notes. |
| Test/design credibility | 10 | Chapter 4 design and Chapter 6 tests are evidence-backed. |
| Handoff traceability | 5 | Final report includes commands, outputs, missing evidence, and exceptions. |

Suggested default threshold for normal final delivery: `85/100`, with every `must_gate` passing. Rough drafts may report a score without meeting the threshold, but must not be called final.

## Executable Checklist

Use this checklist before final handoff:

1. Record final artifact paths: `.docx`, figure map, template profile, generated reports.
2. Record delivery assumptions: expected Visio OLE count, heading thresholds, content-unit thresholds, continuation-caption requirement.
3. Run workspace checks when a thesis workspace exists.
4. Run the aggregate gate on the current `.docx`.
5. If any gate fails, apply the failure handling contract and rerun from the aggregate gate after edits.
6. Score `should_score` dimensions only after hard gates are resolved.
7. Produce a final evidence block using the template below.

## Final Evidence Template

```markdown
## Final Thesis Gate Evidence

- Final DOCX:
- Figure map:
- Template profile:
- Expected Visio OLE:
- Length thresholds:
- Continuation caption required:
- Aggregate command:
- Aggregate exit code:
- Failed gate ids:
- Repaired issues:
- Skipped gates and reason:
- Remaining evidence gaps:
- Should-score total:
- Human/template review notes:
```

## Integration Recommendation

Keep `scripts/check_final_thesis_docx.ps1` as the single final gate runner. Add new small checkers only when a rule has a deterministic signal and can return a non-zero exit code. Keep scorer/report helpers separate from generation scripts so quality controls can evolve without destabilizing demo generation.
