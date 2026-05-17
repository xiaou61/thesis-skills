#!/usr/bin/env python3
"""Generate a local AIGC scan report using the aigc-reduce detection approach."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from aigc_reduce_core import overall_scan, read_text


def write_markdown(payload: dict[str, object], path: Path) -> None:
    summary = payload["summary"]
    template = payload["template_phrases"]
    passive = payload["passive_voice"]
    burstiness = payload["burstiness"]
    para_symmetry = payload["para_symmetry"]
    nested = payload["nested_numbers"]
    colon = payload["colon_lists"]
    punctuation = payload["punctuation"]
    findings = payload["paragraph_findings"]

    lines = [
        "# AIGC Detection Report",
        "",
        "This is a local heuristic estimate based on the `xiaofenggan01/aigc-reduce` scanning approach.",
        "It is not a school or third-party official detector score.",
        "",
        f"- Generated at: `{date.today().isoformat()}`",
        f"- Estimated AIGC rate: `{payload['estimated_aigc_rate']}%`",
        f"- Overall risk: `{payload['overall_risk']}`",
        f"- Triggered dimensions: `{payload['risk_count']}/7`",
        f"- Characters: `{summary['total_chars']}`",
        f"- Paragraphs: `{summary['total_paragraphs']}`",
        f"- Sentences: `{summary['total_sentences']}`",
        "",
        "## Scan Dimensions",
        "",
        f"- 模板句式密度: `{template['count']}` 次，`{template['density_per_1000']}` / 千字",
        f"- 被动语态: `{passive['count']}` 次，`{passive['per_sentence']}` / 句",
        f"- 句长突发性 CV: `{burstiness['cv']}`",
        f"- 段落对称组: `{len(para_symmetry['symmetrical_runs'])}`",
        f"- 嵌套编号: `{nested['count']}` 处",
        f"- 冒号并列: `{colon['count']}` 处",
        f"- 每句逗号数: `{punctuation['commas_per_sentence']}`",
        "",
        "## Dimension Notes",
        "",
        f"- 模板句式: {template['matches'][:5] if template['matches'] else '未命中明显模板句式'}",
        f"- 句长突发性: {burstiness['risk']}",
        f"- 段落对称性: {para_symmetry['risk']}",
        f"- 嵌套编号: {nested['risk']}",
        f"- 冒号并列: {colon['risk']}",
        f"- 标点规律: {punctuation['risk']}",
        "",
        "## Paragraph Findings",
        "",
    ]

    for item in findings:
        lines.append(f"### Paragraph {item['paragraph']} - {item['risk']} risk")
        lines.append(f"- Triggered metrics: {', '.join(item['triggered_metrics']) if item['triggered_metrics'] else 'none'}")
        lines.append(f"- Sentence CV: `{item['sentence_cv']}`")
        lines.append(f"- Template hits: `{item['template_hits']}`")
        lines.append(f"- Passive hits: `{item['passive_hits']}`")
        lines.append(f"- Colon lists: `{item['colon_lists']}`")
        lines.append(f"- Nested numbers: `{item['nested_numbers']}`")
        lines.append(f"- Commas per sentence: `{item['comma_per_sentence']}`")
        lines.append(f"- Preview: {item['text_preview']}")
        lines.append("")

    lines.extend(
        [
            "## Use Notes",
            "",
            "- Treat this as a local scan signal for revision priority.",
            "- For exact prose problems, read `aigc-style-report.md` next.",
            "- Do not present this estimate as an official AIGC result from CNKI, 万方, PaperPass, PaperPure, or any school platform.",
            "",
        ]
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Estimate AIGC-style risk with the aigc-reduce scan dimensions.")
    parser.add_argument("input", nargs="?", help="Text/markdown/html/docx file. Reads stdin when omitted.")
    parser.add_argument("--out", default="paper-context/aigc/aigc-detection-report.md", help="Markdown report path.")
    parser.add_argument("--json-out", default="paper-context/aigc/aigc-detection-report.json", help="JSON report path.")
    parser.add_argument("--discipline", default="general", help="Reserved compatibility option.")
    args = parser.parse_args()

    input_path = Path(args.input).resolve() if args.input else None
    text = read_text(input_path)
    payload = overall_scan(text)
    payload["source"] = str(input_path) if input_path else "stdin"
    payload["discipline"] = args.discipline
    payload["policy_note"] = "This is a local heuristic estimate based on aigc-reduce, not an official detector result."

    out_path = Path(args.out).resolve()
    json_path = Path(args.json_out).resolve()
    write_markdown(payload, out_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {out_path}")
    print(f"Wrote {json_path}")
    print(f"Estimated AIGC rate: {payload['estimated_aigc_rate']}% ({payload['overall_risk']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
