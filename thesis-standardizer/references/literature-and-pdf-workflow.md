# Literature And PDF Workflow

Use this reference when a thesis needs literature review, related work, citation cleanup, citation placement, or reference extraction from PDF papers.

If the user does not already have a PDF folder and needs scholarly search or open full-text collection first, read `literature-harvest-workflow.md` before this file. Use `generate_literature_search_config.py` to infer search terms from thesis materials, then use `verify_select_literature.py` to keep only real, locatable Chinese and English references before final citation planning.

## Inputs

Preferred inputs:

- PDF papers in one folder
- deduplicated harvest output from `literature-harvest-workflow.md`, when available
- thesis title, abstract, keywords, chapter outline, or `thesis-ai-spec.yaml`
- school reference style requirement
- existing reference list, if any
- `verified-literature-selected.csv` from `verify_select_literature.py`, when the literature was harvested

## PDF Reference Extraction

Run:

```powershell
python .\scripts\extract_pdf_references.py .\papers --out .\paper-context\literature
```

For harvested literature, use the deduplicated download folder:

```powershell
python .\scripts\extract_pdf_references.py .\paper-context\literature\harvest-runs\thesis_literature_YYYYMMDD\downloaded_pdfs_deduplicated --out .\paper-context\literature
```

Outputs:

```text
paper-context/literature/
  reference-extraction.json
  reference-extraction.md
```

The script extracts candidate reference sections. Treat output as raw evidence. Verify bibliographic fields manually or with trusted sources before final formatting.

## Citation Cross-References

If a topic outline exists, create a citation cross-reference index:

```powershell
python .\scripts\build_literature_crossrefs.py .\paper-context\literature\reference-extraction.json --topics .\paper-context\topics.md --out .\paper-context\literature\citation-crossrefs.md --json-out .\paper-context\literature\citation-crossrefs.json
```

Cross-reference rules:

- Match references to claims by overlap with topic terms, methods, domain words, and known acronyms.
- Prefer recent and directly relevant papers for research status sections; default recency is the recent 6-year window based on the user's current year, unless the user or school specifies another range.
- Prefer method papers for method/theory sections.
- Prefer system/application papers for design comparison sections.
- Do not cite a paper merely because a keyword appears once.
- Keep each body citation point to at most 2 references; do not place 3 or more sources after one sentence or one claim.
- Mark weak matches as `needs_check`.

After generating cross-references, update `thesis-ai-standard/templates/citation-crossref-register.yaml` or a project copy of it. The register is the closure layer:

- body claim -> citation candidate
- citation candidate -> verified reference-list entry
- reference-list entry -> body citation location
- unresolved candidate -> `needs_check`, `rejected`, or `missing_source`

## Writing Literature Review

Structure by theme, not by one-paper-per-paragraph:

1. Define the research or engineering problem.
2. Group literature into 2-4 themes.
3. Compare methods, data, systems, or conclusions.
4. Identify the gap that the thesis addresses.
5. Connect the gap to the thesis work.

Avoid:

- fabricated author/year/venue
- fabricated or unlocatable references
- references not cited in body text
- body citations missing from final reference list
- DOI or URL hallucination
- citations in the abstract, unless the school template explicitly requires them
- clustered citations with 3 or more references attached to one sentence or one claim
- "AI found" or "the uploaded paper says" wording

## Citation Placement Scope

Before planning citations across the body text, ask whether the user wants:

- full-text citation coverage, or
- only the front chapters such as introduction, research status, literature review, theory foundation, and related technology.

Do not assume every chapter needs newly searched literature. For system-design theses, implementation and testing chapters usually cite project evidence, screenshots, code, tests, and data first; literature is used only where it supports methods, standards, comparison, or theory.

## Final Checks

- Every cited source appears in the reference list.
- Every reference-list item is cited, unless school rules allow uncited background references.
- `citation-crossref-register.yaml` or equivalent notes record the body/reference closure.
- Reference format follows `standard-profile.yaml`.
- Extraction uncertainty is resolved before final submission.
- Default selected literature counts are Chinese `12-15` and English `3-5`, unless the user or school requires otherwise.
- Default selected literature year range is recent 6 years based on the user's current year; out-of-range or missing-year records stay out of the final list unless the user explicitly accepts manual verification or a different year range.
- Each body citation point cites no more than 2 references; larger source groups are split into separate claims, sentences, or literature-matrix comparisons.
