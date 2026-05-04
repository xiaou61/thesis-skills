# Rapid Thesis Workflow

Use this reference when the user wants to quickly turn a program, experiment, or existing draft into a thesis package.

## Intake Checklist

Collect what exists before drafting:

- school template or formatting guide
- task book, proposal, advisor notes
- source code or project folder
- database schema, API docs, test reports
- screenshots or experiment outputs
- existing thesis draft, if any
- reference list or required citation style

If school rules are missing, use bundled defaults but mark them as replaceable.

## Bootstrap

Run:

```powershell
python .\scripts\init_thesis_workspace.py .
```

Then fill:

```text
thesis-ai-standard/templates/standard-profile.yaml
thesis-ai-standard/templates/thesis-ai-spec.yaml
thesis-ai-standard/templates/figure-registry.yaml
```

Validate the package before writing:

```powershell
python .\scripts\check_thesis_workspace.py .\thesis-ai-standard
```

## From Program To Thesis

For software/system projects:

1. Run `build_project_evidence.py` to create a first-pass evidence folder:
   ```powershell
   python .\scripts\build_project_evidence.py . --out .\paper-context\evidence
   ```
2. Read `project-evidence.json`, `tech-stack.md`, `api-list.md`, `database-schema.md`, and `test-results.md`.
3. Inspect the source files behind important claims; script output is an index, not proof by itself.
4. Extract real facts into `thesis-ai-spec.yaml`.
5. Create a figure plan in `figure-registry.yaml`:
   - system architecture
   - module diagram
   - business flow
   - ER diagram or data model
   - key sequence diagrams
   - screenshots and test result figures
6. Draft chapters in this order:
   - related technology
   - requirement analysis
   - overall design
   - detailed implementation
   - testing
   - introduction and conclusion last

## From Experiment Or Survey To Thesis

For research/data papers:

1. Identify research question, objects, variables, data source, method, and limitations.
2. Use `type_profile: empirical_research` or `survey_analysis`.
3. Build tables before prose:
   - variable definition table
   - sample/data source table
   - method or model table
   - result table
4. Draft results only from provided data.

## AIGC Style Pass

For existing chapter drafts or after first drafting:

1. If the user asks for AIGC rate or before/after comparison, run the local detection report:
   ```powershell
   python .\scripts\detect_aigc_rate.py .\chapter-draft.md --out .\paper-context\aigc\aigc-detection-report.md --json-out .\paper-context\aigc\aigc-detection-report.json
   ```
   State that this is a local heuristic estimate, not an official detector score.
2. Run the local style report:
   ```powershell
   python .\scripts\analyze_aigc_style.py .\chapter-draft.md --out .\paper-context\aigc\aigc-style-report.md --json-out .\paper-context\aigc\aigc-style-report.json
   ```
3. Read `references/aigc-style-governance.md`.
4. Update `thesis-ai-standard/templates/aigc-style-review.yaml` or a project copy.
5. Revise only confirmed high-risk paragraphs.
6. Mark unsupported claims as `needs_source` or `needs_evidence`.

For a full-paper final paragraph pass, warn the user first:

```text
AIGC 最终降低版会按论文文本分割后逐段处理、逐段复查、再拼接全文，极度消耗 token。建议只在终稿或外部报告集中命中时使用。
```

Then run:

```powershell
python .\scripts\analyze_aigc_style.py .\chapter-draft.md --out .\paper-context\aigc\aigc-style-report.md --json-out .\paper-context\aigc\aigc-style-report.json --final-paragraph-pass-out .\paper-context\aigc\aigc-final-paragraph-pass.md
```

Do not describe this as bypassing an AIGC detector. Describe it as academic style and evidence-quality revision.

## Stop Conditions

Do not draft final prose when these are missing:

- school template for layout-sensitive delivery
- source evidence for claimed functions or experiments
- test/experiment result records
- database/API facts for system papers
- reference list for literature review and citations

Instead output an exact missing-material list.

## Review

Before final response, run or perform:

- `check_thesis_workspace.py` for generated template packages
- YAML parse for standard/spec/registry files
- JSON parse for review rubric
- XML parse for draw.io templates if modified
- scan for project-specific leftovers when creating a generic package
- review for AI-workflow leakage in thesis prose
