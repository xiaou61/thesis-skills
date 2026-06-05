# Template Replication Workflow

Use this when the user provides a school Word template or asks for close reproduction of an existing thesis DOCX.

## Purpose

The goal is to generate a thesis by component and then check it against the template profile. Do not rely on visual impression alone.

## Workflow

1. Extract the school template profile:

   ```powershell
   python .\scripts\extract_docx_template_profile.py .\template.docx --out .\paper-context\template-extract
   ```

2. Build a component-oriented structure plan:

   ```powershell
   python .\scripts\build_thesis_structure_plan.py `
     --template-profile .\paper-context\template-extract\template-profile.json `
     --spec .\thesis-ai-standard\templates\thesis-ai-spec.yaml `
     --out .\paper-context\template-extract\thesis-structure-plan.yaml
   ```

3. Generate or revise the thesis by components:

   - front matter: cover, Chinese abstract, English abstract, TOC
   - main matter: Chapters 1-6 unless the template/user requires a different structure
   - back matter: references, acknowledgement, appendix

4. Apply template style and table rules to every component.

5. Run the final aggregate gate with the template profile:

   ```powershell
   .\scripts\check_final_thesis_docx.ps1 .\final.docx `
     -TemplateProfile .\paper-context\template-extract\template-profile.json `
     -FigureMap .\paper-context\visio-ole-figure-map.json `
     -ExpectedVisioOle 12 `
     -MinContentUnits 12000 `
     -MinCjkChars 10000 `
     -RequireContinuationCaption
   ```

6. Read `paper-context/template-extract/template-replication-diff.md` if generated and fix differences that are not explicitly acceptable.

## Required Template Model

The template profile should drive these decisions:

- component order
- paragraph style map
- heading levels
- page margins and section count
- header/footer and page-number model
- figure/table caption style
- three-line table and continuation-table policy
- reference and appendix placement

## Acceptance Standard

Do not claim "same as the template" unless:

- component order check passes or all differences are listed
- style profile check passes or differences are accepted
- page model check passes or differences are accepted
- caption numbering check passes
- existing aggregate DOCX gates pass

If the school template contains unusual rules, record them in `standard-profile.yaml` and template extraction outputs before generating the next draft.
