# Literature Harvest Workflow

Use this reference when the user needs the skill to plan literature search terms, harvest real candidate papers, resume downloads, deduplicate files, and select verifiable Chinese/English references before PDF extraction or citation planning.

## Goal

Build a traceable literature intake pipeline before writing literature review paragraphs or placing citations.

## Inputs

Preferred inputs:

- thesis title, abstract, keywords, or `thesis-ai-spec.yaml`
- school/advisor requirements for databases, language mix, and year range
- existing manual reference list, if any
- optional exported search requirements from CNKI / WanFang / VIP / Google Scholar / library systems

## Step 1: Generate Search Config

Run:

```powershell
python .\scripts\generate_literature_search_config.py . --out .\paper-context\literature\literature-harvest-config.json
```

Outputs:

```text
paper-context/literature/
  literature-harvest-config.json
```

The config captures:

- thesis title, abstract, keywords
- inferred Chinese and English queries
- default recent-6-year range based on the current year
- target Chinese/English counts
- user overrides when explicitly provided

## Step 2: Harvest Candidate Metadata And Open Files

Run:

```powershell
python .\scripts\run_keyword_harvest_no_dedup.py .\paper-context\literature\literature-harvest-config.json --out .\paper-context\literature\harvest-runs
```

Outputs:

```text
paper-context/literature/harvest-runs/thesis_literature_YYYYMMDD_HHMMSS/
  literature-harvest-log.json
  keyword_research_candidate_table.csv
  harvest-summary.md
  downloaded_raw/
```

Rules:

- This stage creates a no-dedup candidate table on purpose.
- Keep source, query, DOI, URL, year, language, and local file path when available.
- Downloaded PDF / HTML / XML files are candidate evidence only.

## Step 3: Resume Downloads And Deduplicate Files

Run:

```powershell
python .\scripts\continue_download_and_dedup.py .\paper-context\literature\harvest-runs\thesis_literature_YYYYMMDD_HHMMSS
```

Outputs:

```text
paper-context/literature/harvest-runs/thesis_literature_YYYYMMDD_HHMMSS/
  keyword_research_candidate_table.csv
  download-resume-report.md
  downloaded_raw/
  downloaded_pdfs_deduplicated/
```

Rules:

- Retry only rows that still have a usable PDF or landing URL.
- Deduplicate by content hash, not just filename.
- Keep the no-dedup candidate CSV for auditability even after deduplicated files are produced.

## Step 4: Verify And Select Literature

Run:

```powershell
python .\scripts\verify_select_literature.py .\paper-context\literature\harvest-runs\thesis_literature_YYYYMMDD_HHMMSS\keyword_research_candidate_table.csv --config .\paper-context\literature\literature-harvest-config.json --out .\paper-context\literature\verified-selection
```

Outputs:

```text
paper-context/literature/verified-selection/
  verified-literature-selected.csv
  verified-literature-selection.md
```

Selection rules:

- Prefer recent and directly relevant literature.
- Keep only locatable items with DOI, stable URL, downloadable file, or user-provided export evidence.
- Reject missing-year or out-of-range items by default unless the user accepts manual verification.
- Default targets are Chinese `12-15` and English `3-5`.

## Step 5: Move Into PDF Extraction And Citation Closure

After verified selection is ready:

1. download or copy the final PDF set if needed
2. run `extract_pdf_references.py`
3. run `build_literature_crossrefs.py`
4. update `literature-review-matrix.yaml` and `citation-crossref-register.yaml`

## Stop Conditions

Do not claim the literature phase is complete when:

- no year range is confirmed
- no locatable references were found
- only keyword-level weak matches exist
- Chinese/English balance is far below requirement and the shortage is not recorded
- extracted PDF references were not verified before final citation placement

Return a shortage list instead.
