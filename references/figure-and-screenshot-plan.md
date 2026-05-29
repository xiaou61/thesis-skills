# Figure And Screenshot Plan

Use this before drafting Chapter 3, Chapter 4, or Chapter 5.

## Hard Rule

A complete system-design thesis should have a figure plan, not just a few ad hoc diagrams. Do not pad the thesis with decorative figures, but do plan enough evidence-backed visuals to explain analysis, design, implementation, and testing.

Default target for a normal undergraduate system thesis:

- Chapter 3: 2-3 figures
- Chapter 4: 6-15 figures, depending on the number of entities and core modules
- Chapter 5: 3-8 real program screenshots or screenshot placeholders

## Build The Plan

Run:

```powershell
python .\scripts\build_figure_plan.py .\thesis-ai-standard\templates\thesis-ai-spec.yaml --out .\paper-context\figure-plan
```

This creates:

- `paper-context/figure-plan/figure-plan.yaml`
- `paper-context/figure-plan/figure-registry-fragment.yaml`
- `paper-context/figure-plan/figure-plan.md`

Merge the fragment into `thesis-ai-standard/templates/figure-registry.yaml` or use it as the chapter drafting checklist.

## Default Figure Matrix

Chapter 3 usually needs:

- system use-case diagram, Visio `.vsdx`
- core business flowchart, Visio `.vsdx`, if workflow evidence exists
- requirement/function decomposition figure, Visio `.vsdx`, if module evidence exists

Chapter 4 usually needs:

- system function structure diagram, Visio `.vsdx`
- overall architecture diagram, Visio `.vsdx`
- technical/deployment architecture diagram, Visio `.vsdx`, if stack/deployment evidence exists
- overview E-R diagram, Visio `.vsdx`
- one single-entity E-R diagram per core entity/data object, Visio `.vsdx`
- 2-4 key module flowcharts, Visio `.vsdx`, selected from real modules

Chapter 5 usually needs:

- login or entry-page test screenshot
- main page screenshot
- screenshots for 2-4 core functions
- test result, run log, or report screenshot

## Screenshot Policy

Never fabricate program screenshots.

If the app is runnable locally and browser automation can capture real screens, capture them and register the image files as evidence. If the app cannot be run, requires credentials, depends on missing services, or needs the user's environment, leave screenshot entries in `figure-registry.yaml` with:

```yaml
source_kind: screenshot
source_file: pending_user_screenshot
export_file: paper-context/screenshots/figure-5-X-name.png
status: needs_user_screenshot
risk_notes: "AI 不得伪造程序截图；等待用户补真实截图"
```

Do not write final test-result claims that depend on missing screenshots. Use wording such as "待补充运行截图后确认" in drafts and list the screenshot gap in the delivery report.

## Density Guardrails

- If fewer than 8 figures are planned for a normal system thesis, explain why the project scope is small or evidence is missing.
- If more than 20 figures are planned, split low-value screenshots into appendix candidates.
- Every structural figure must keep an editable `.vsdx` source.
- Every screenshot must be a real capture or a clearly marked placeholder.
- Every figure must have first mention, title, evidence, source path, export path, and status.
