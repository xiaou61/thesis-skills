# Variant 3: Agentic Scorer And Review Pipeline

## Positioning

This variant turns thesis generation into a multi-agent production and review pipeline. It is designed for quality ceiling rather than first-pass stability.

It should be optional at first, because it is heavier and may require external search, LLM judging, or manual confirmation for some evidence claims.

## External Patterns Absorbed

- SNL-UCSB paper-writing-skill: persistent project context, section architecture, section drafting, integration, and compression.
- academic-paper-skills: strategist/composer separation and quality standards.
- paper-writer-skill: stage gates, retry limits, and escalation when a stage cannot be fixed.
- Material Passport style research suites: every important claim maps to evidence, source material, or a declared gap.
- ResearchRubrics/AutoChecklist/LLM-Rubric style: structured scoring by dimension rather than a single vague review.

## Agent Roles

1. Evidence Miner
   - Reads code, database, API, screenshots, tests, logs, and templates.
   - Produces a material passport with source paths and confidence.

2. Thesis Architect
   - Produces chapter map, section map, figure/table plan, and citation plan.
   - Rejects over-small figure plans for normal system theses.

3. Diagram Planner
   - Produces use-case, architecture, flowchart, E-R, and screenshot registry entries.
   - Flags missing real screenshots instead of fabricating them.

4. Chapter Writer
   - Writes chapter sections from approved evidence and section moves.
   - Keeps evidence language out of the thesis body.

5. Format Auditor
   - Runs DOCX, table, Visio OLE, heading, template, and page checks.
   - Returns machine-readable issues.

6. Thesis Reviewer
   - Scores the result by rubric dimensions.
   - Produces prioritized fixes and separates hard failures from quality suggestions.

## Material Passport

Each claim-worthy thesis item should record:

- claim_id
- chapter and section
- body summary
- source type: code, database, API, screenshot, test, template, literature, user input
- source path or citation
- confidence: high, medium, low, missing
- whether the claim may appear in final prose
- whether the wording must avoid evidence/audit language

## Scoring Dimensions

- Template compliance
- Chapter structure completeness
- Project evidence grounding
- Figure/table density and usefulness
- Visio editability and layout quality
- Database/design completeness
- Implementation screenshot readiness
- Test credibility
- Reference/citation closure
- Thesis voice and naturalness
- Revision traceability

## Proposed Files

- `references/agentic-thesis-pipeline.md`
- `references/material-passport-schema.md`
- `scripts/build_material_passport.py`
- `scripts/check_material_passport.py`
- `scripts/score_thesis_rubric.py`
- `scripts/export_thesis_issue_list.py`
- extend `thesis-ai-standard/templates/ai-review-rubric.json`

## Acceptance Criteria

A demo thesis run should produce:

- a material passport
- a figure/table/screenshot issue list
- a rubric score report with dimension scores
- a retry/fix log for failed gates
- a final DOCX that still passes deterministic aggregate checks

Suggested threshold:

- hard gates: zero critical failures
- rubric total score: at least 85 before normal delivery
- template compliance score: at least 90 when a real template is supplied
- evidence grounding score: at least 85 unless the user explicitly accepts missing materials

## Strengths

- Highest long-term quality ceiling.
- Makes failures visible and fixable instead of hidden in prose.
- Very suitable for repeated demo generation and A/B comparison.

## Limits

- Heavier workflow.
- Requires careful orchestration so agents do not invent missing screenshots, references, or database fields.
- Some intelligent citation verification should remain optional because web/API availability and false positives can vary.
