# Literature Harvest

Use this when the user needs real literature before writing citations or literature review text.

## Goal

Build a traceable literature pipeline before writing.

## Default Flow

1. Generate config:

```powershell
python .\scripts\generate_literature_search_config.py . --out .\paper-context\literature\literature-harvest-config.json
```

2. Harvest candidates:

```powershell
python .\scripts\run_keyword_harvest_no_dedup.py .\paper-context\literature\literature-harvest-config.json --out .\paper-context\literature\harvest-runs
```

3. Resume downloads and dedup:

```powershell
python .\scripts\continue_download_and_dedup.py .\paper-context\literature\harvest-runs\thesis_literature_YYYYMMDD_HHMMSS
```

4. Verify and select:

```powershell
python .\scripts\verify_select_literature.py .\paper-context\literature\harvest-runs\thesis_literature_YYYYMMDD_HHMMSS\keyword_research_candidate_table.csv --config .\paper-context\literature\literature-harvest-config.json --out .\paper-context\literature\verified-selection
```

5. Then move to:

- `extract_pdf_references.py`
- `build_literature_crossrefs.py`

## Keep / Reject Rules

Keep:

- recent and relevant papers
- locatable papers with DOI, stable URL, downloadable file, or user-provided export

Reject by default:

- missing-year items
- out-of-range items
- weak keyword matches
- papers that cannot be located again

## Default Targets

- Chinese: `12-15`
- English: `3-5`
- Year range: recent 6 years unless school/user rules override

## Stop Conditions

Do not say literature is ready if:

- year range is not confirmed
- no locatable references were found
- Chinese/English balance is far below requirement
- verified selection is missing

Return a shortage list instead.
