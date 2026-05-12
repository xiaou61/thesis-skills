# AIGC Detection Workflow

Use this module when the user asks to detect text AIGC rate, estimate AI-generated writing percentage, compare before/after reduction, or produce an AIGC detection report.

This module now follows `xiaofenggan01/aigc-reduce`: scan the text for template phrases, burstiness, passive voice, nested numbering, colon-list scaffolds, paragraph symmetry, and punctuation regularity, then convert those signals into a local heuristic AIGC-style estimate. The script is offline and heuristic. It is not an institutional detector, not a plagiarism/AIGC platform, and not proof of misconduct or clearance.

Local mirror path:

- `thesis-standardizer/vendor/aigc-reduce/scripts/aigc_scan.py`
- `thesis-standardizer/vendor/aigc-reduce/references/detection-principles.md`

## Detection Dimensions

The detector uses these scan dimensions:

1. Template phrase density: macro openings, bridge phrases, and formulaic conclusions.
2. Passive-voice markers: `被…测定 / 通过…验证 / 采用…进行` style abstractions.
3. Burstiness: sentence-length variation, with low CV treated as a stronger AI-like signal.
4. Paragraph symmetry: runs of 3+ similarly sized paragraphs.
5. Nested numbering: excessive `（1）（2）…` style numbering markers.
6. Colon-list structure: `A：…；B：…；C：…` style scaffolded prose.
7. Punctuation regularity: especially high comma density per sentence.

## Script

Run:

```powershell
python .\thesis-standardizer\scripts\detect_aigc_rate.py .\chapter-draft.md --out .\paper-context\aigc\aigc-detection-report.md --json-out .\paper-context\aigc\aigc-detection-report.json
```

The wrapper keeps thesis-standardizer report paths, but the scan data itself should come from the mirrored upstream script.

Supported input:

- `.txt`
- `.md`
- `.html`
- `.docx`
- stdin text

Output:

- estimated AIGC rate
- overall risk: low / medium / high
- 7 scan-dimension summaries
- paragraph-level triggered metrics
- examples of template phrases and rhythm risks

## Required Framing

Always explain:

```text
这个结果是本地启发式 AIGC 风格估计，不是学校或第三方平台的官方检测分数。
```

Use it to prioritize revision:

1. Run `detect_aigc_rate.py` before revision.
2. Run `analyze_aigc_style.py` for the 10 deep AI-writing patterns from `aigc-reduce`.
3. Revise high-risk paragraphs.
4. Run `detect_aigc_rate.py` again and compare estimated rate, triggered dimension count, and paragraph-risk changes.

## Report Use

Use the detection report as a triage layer:

- High template density: remove stock bridges such as `综上所述 / 值得注意的是 / 相关研究表明`.
- Low burstiness: break overly even sentence lengths and avoid paragraph rhythm symmetry.
- High passive markers: convert abstract process shells into direct method/result statements.
- Excess nested numbering or colon lists: unfold them into natural thesis prose.
- High comma density: split overloaded clauses and reduce hanging `从而 / 进而 / 由此` chains.

Do not use the report to promise a target score. Do not write "已通过检测" unless the user provides an actual external report showing that result.
