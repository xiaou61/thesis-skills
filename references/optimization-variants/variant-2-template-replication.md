# Variant 2: Template Replication

## Positioning

This variant makes the skill template-first. The goal is not only to produce a valid thesis, but to reproduce the supplied school/template document as closely as Word automation allows.

This is the recommended main line because the user has repeatedly found that visual and structural fidelity matters as much as content generation.

## External Patterns Absorbed

- thuthesis, ustcthesis, BIThesis, BUAAThesis, fduthesis, and similar Chinese thesis templates: front matter, main matter, and back matter are treated as formal thesis components.
- Word template repositories such as SCU and FZU templates: Word styles, heading levels, captions, page numbers, table styles, and template-specific quirks must be extracted and checked.
- skill-creator progressive disclosure: keep `SKILL.md` lean and move detailed replication rules into references and scripts.

## Template Profile Model

The template extractor should produce a profile with these sections:

1. component_order
   - cover
   - statement or authorization pages when present
   - zh_abstract
   - en_abstract
   - toc
   - list_of_figures when present
   - list_of_tables when present
   - chapters
   - references
   - acknowledgement
   - appendix

2. style_map
   - title styles for levels 1-4
   - abstract title and keyword styles
   - body paragraph style
   - figure caption style
   - table caption style
   - reference entry style
   - appendix and acknowledgement styles

3. page_model
   - section breaks
   - margins
   - header/footer rules
   - page-number format and restart rules
   - portrait/landscape sections

4. numbering_model
   - chapter numbering
   - figure/table/equation numbering
   - appendix numbering
   - reference numbering

5. table_model
   - three-line table borders
   - continuation caption format
   - repeated header row
   - row split rules
   - allowed school-specific table exceptions

## Workflow Changes

1. Extract template profile before writing.
2. Produce a `thesis-structure-plan.yaml` from the profile and project evidence.
3. Generate thesis parts by component, not by free-form document flow.
4. Apply template profile to every generated component.
5. Render DOCX and PDF.
6. Run page/style comparison and final aggregate gate.
7. Produce a template replication report listing differences that still require manual Word review.

## Proposed Files

- `scripts/build_thesis_structure_plan.py`
- `scripts/check_docx_component_order.py`
- `scripts/check_docx_style_profile.py`
- `scripts/check_docx_page_model.py`
- `scripts/check_docx_caption_numbering.py`
- `scripts/report_template_replication_diff.py`
- `references/template-replication-workflow.md`
- extend `references/template-extraction-workflow.md`
- extend `thesis-ai-standard/templates/standard-profile.yaml`

## Acceptance Criteria

A demo thesis is acceptable only when:

- It includes the same required thesis components as the source template or an explicit difference report.
- Heading levels include level 2 and level 3 sections where the chapter content requires them.
- Main body follows the six-chapter undergraduate system thesis structure unless the template requires otherwise.
- Captions, tables, continuation captions, and page sections match the profile or are listed as unresolved differences.
- The final DOCX passes the aggregate gate and also produces a replication diff report.

## Strengths

- Best fit for strict school-template reproduction.
- Directly addresses visual fidelity, heading hierarchy, table continuation, and Word-specific problems.
- Provides a reviewable difference report instead of vague claims like "looks similar".

## Limits

- More implementation work than Variant 1.
- Some page-level differences may still require Word desktop/PDF rendering checks.
- Requires real templates for best results.
