# Template Extraction Workflow

Use this reference when the user provides a school `.docx` thesis template and wants the system to extract reusable formatting constraints before drafting or final polishing.

## Goal

Turn a Word thesis template into a machine-readable template profile instead of relying on manual memory.

## Recommended Strategy

Use a hybrid pipeline rather than a single library:

1. OOXML structural extraction for sections, margins, page size, header/footer references, and style definitions.
2. `python-docx` for convenient inspection or controlled edits after extraction.
3. `pandoc --reference-doc` only for output reuse, not for lossless extraction.
4. Optional HTML/text converters like Mammoth for quick semantic inspection, not for page-layout fidelity.

## Why Hybrid

- `.docx` is an OOXML package, so sections, headers, footers, numbering, and style inheritance live in separate XML parts.
- Convenience libraries can hide inheritance rules and make section-linked headers look flattened.
- Converters that target HTML or markdown are usually semantic first and formatting second.

## Step 1: Extract Template Profile

Run:

```powershell
python .\scripts\extract_docx_template_profile.py .\school-template.docx --out .\paper-context\template-extract
```

Outputs:

```text
paper-context/template-extract/
  template-profile.json
  template-profile.md
  template-rule-overrides.yaml
```

Captured fields include:

- section count
- page size and orientation per section
- top/bottom/left/right/header/footer margins
- effective header/footer text after inheritance resolution
- available style definitions
- paragraph style usage counts
- heading-style samples
- TOC field detection
- normalized rule overrides for downstream drafting/review

## Step 2: Normalize Into Thesis Rules

Map the extracted profile into:

- `thesis-ai-standard/templates/standard-profile.yaml`
- `paper-context/template-extract/template-rule-overrides.yaml`

Use extracted facts for:

- page margins
- body font defaults
- heading style names and likely chapter levels
- whether the template uses distinct first-page headers/footers
- whether the template already contains TOC fields
- likely role of each section, such as cover/front matter/body
- likely heading style level mapping

Do not auto-claim school rules that are not explicit in the template. Mark uncertain items as manual-review.

## Step 3: Reuse The Template Safely

If the thesis will be generated from markdown or intermediate text:

- use the school template as a `pandoc --reference-doc`
- keep final formatting-sensitive work in `.docx`
- avoid markdown round-trips after the document has stable TOC/cross-references/figure anchors

## Stop Conditions

Do not claim extraction is complete when:

- the template is `.dotx` and was not converted or inspected as OOXML
- section inheritance was not resolved
- style names were extracted but not mapped to chapter/body roles
- margins or page size are missing from the report
- the template contains heavy manual formatting with weak style usage and no manual-review note was added
