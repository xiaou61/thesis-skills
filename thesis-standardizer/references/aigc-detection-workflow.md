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
3. Revise high-risk paragraphs one by one, not the whole chapter in one shot.
4. Run `detect_aigc_rate.py` again after that first repair round.
5. Compare estimated rate, triggered dimension count, and paragraph-risk changes.
6. Do one more focused repair round on the paragraphs that are still obviously high risk.

In plain words, the default rhythm is:

1. 先看哪里问题大。
2. 一段一段改。
3. 改完先本地测一次。
4. 看测出来还像不像 AI。
5. 再补一轮，不要一次性全重写。

## Report Use

Use the detection report as a triage layer:

- High template density: remove stock bridges such as `综上所述 / 值得注意的是 / 相关研究表明`.
- Low burstiness: break overly even sentence lengths and avoid paragraph rhythm symmetry.
- High passive markers: convert abstract process shells into direct method/result statements.
- Excess nested numbering or colon lists: unfold them into natural thesis prose.
- High comma density: split overloaded clauses and reduce hanging `从而 / 进而 / 由此` chains.

If the user asks for "大白话", explain the findings in ordinary Chinese first, for example:

- 不说 "burstiness too low", 直接说 "这几句长得太整齐了，看着像一批量产出来的"。
- 不说 "template phrase density is elevated", 直接说 "这一段套话有点多，像在凑标准论文腔"。
- 不说 "colon-list scaffold", 直接说 "这句像在列配置单，不像人在顺着讲"。

Do not use the report to promise a target score. Do not write "已通过检测" unless the user provides an actual external report showing that result.
