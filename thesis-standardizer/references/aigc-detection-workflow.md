# AIGC Detection Workflow

Use this module when the user asks to detect text AIGC rate, estimate AI-generated writing percentage, compare before/after reduction, or produce an AIGC detection report.

This module is inspired by `free-revalution/AIGC-Detector-Pro`: score text across five dimensions and combine them into an estimated AIGC-style rate. The local script is heuristic and offline. It is not an institutional detector, not a plagiarism/AIGC platform, and not proof of misconduct or clearance.

## Five Dimensions

The detector uses these dimensions:

1. Sentence regularity, weight 25%: sentence length uniformity, template openings, repeated starts.
2. Connector density, weight 20%: overuse of "首先/其次/综上所述/值得注意的是" or similar English connectors.
3. Voice characteristics, weight 15%: passive shells, abstract "该设计体现/该方法说明" patterns, impersonal phrasing.
4. Vocabulary diversity, weight 15%: low lexical variety, repeated generic academic terms.
5. Argumentation depth, weight 25%: weak evidence, few data/citation/table/experiment/case signals, generic value claims.

## Script

Run:

```powershell
python .\thesis-standardizer\scripts\detect_aigc_rate.py .\chapter-draft.md --out .\paper-context\aigc\aigc-detection-report.md --json-out .\paper-context\aigc\aigc-detection-report.json
```

Supported input:

- `.txt`
- `.md`
- `.html`
- `.docx`
- stdin text

Output:

- estimated AIGC rate
- overall risk: clear / low / medium / high
- confidence level
- five-dimension scores
- paragraph-level estimated rates
- issues and rationale

## Required Framing

Always explain:

```text
这个结果是本地启发式 AIGC 风格估计，不是学校或第三方平台的官方检测分数。
```

Use it to prioritize revision:

1. Run `detect_aigc_rate.py` before revision.
2. Run `analyze_aigc_style.py` for exact formulaic patterns.
3. Revise high-risk paragraphs.
4. Run `detect_aigc_rate.py` again and compare estimated rate, dimension scores, and high-risk paragraph counts.

## Report Use

Use the detection report as a triage layer:

- High sentence regularity: vary paragraph rhythm and remove template scaffolds.
- High connector density: remove mechanical transitions and use evidence-driven transitions.
- High voice-characteristics risk: replace passive shells with concrete method or evidence claims.
- High vocabulary-diversity risk: reduce repeated generic academic terms.
- High argumentation-depth risk: add verified data, citation, table, experiment, limitation, or mark `needs_evidence`.

Do not use the report to promise a target score. Do not write "已通过检测" unless the user provides an actual external report showing that result.
