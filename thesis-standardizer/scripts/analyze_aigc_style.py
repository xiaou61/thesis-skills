#!/usr/bin/env python3
"""Generate an AIGC style governance report using the aigc-reduce pattern set."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aigc_reduce_core import analyze_style, read_text


def write_markdown(payload: dict[str, object], path: Path) -> None:
    summary = payload["summary"]
    findings = payload["findings"]

    lines = [
        "# AIGC Style Governance Report",
        "",
        "This report follows the `xiaofenggan01/aigc-reduce` methodology.",
        "It is a style-governance and revision-planning report, not an official detector score.",
        "",
        f"- Overall risk: `{summary['overall_risk']}`",
        f"- Paragraphs: `{summary['paragraph_count']}`",
        f"- Risk counts: `{summary['risk_counts']}`",
        f"- Method source: `{summary['method_source']}`",
        "",
        "## Pattern Counts",
        "",
    ]

    pattern_counts = summary.get("pattern_counts", {})
    if pattern_counts:
        for key, count in pattern_counts.items():
            lines.append(f"- `{key}`: {count}")
    else:
        lines.append("- No major deep AI-writing patterns detected.")

    lines.extend(["", "## Paragraph Findings", ""])
    for item in findings:
        if item["risk"] == "clear":
            continue
        lines.append(f"### Paragraph {item['paragraph']} - {item['risk']} risk")
        lines.append(f"- Score: `{item['score']}`")
        lines.append(f"- Pattern labels: {', '.join(item['pattern_labels']) if item['pattern_labels'] else 'none'}")
        lines.append(f"- Matched examples: {'；'.join(item['matched_examples']) if item['matched_examples'] else 'none'}")
        lines.append(f"- AI high-frequency terms: {', '.join(item['cliche_terms']) if item['cliche_terms'] else 'none'}")
        lines.append(f"- Rewrite guidance: {'；'.join(item['rewrite_guidance']) if item['rewrite_guidance'] else 'none'}")
        lines.append(f"- Characters: `{item['char_count']}`")
        lines.append(f"- Preview: {item['text_preview']}")
        lines.append("")

    lines.extend(
        [
            "## Revision Order",
            "",
            "1. Remove significance inflation, vague attribution, and generic positive conclusions first.",
            "2. Unify core terminology before touching sentence rhythm.",
            "3. Break rigid three-item structures and floating “从而/进而/由此” chains.",
            "4. Replace abstract role-shell expressions with direct verbs or concrete judgments.",
            "5. Re-scan with `detect_aigc_rate.py` after targeted revision and compare paragraph risk changes.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_final_paragraph_pass(payload: dict[str, object], path: Path) -> None:
    findings = payload["findings"]
    lines = [
        "# AIGC 最终降低版分段工作单",
        "",
        "本文件按 `aigc-reduce` 的三轮降重协议整理逐段任务：先去 AI 痕迹，再注入人类特征，最后做 Anti-AI 审计。",
        "",
        "> 注意：AIGC 最终降低版会按论文文本分割后逐段处理。每段先修，再本地检测，再补一轮，最后再拼接全文，极度消耗 token。建议只在终稿或外部报告集中命中时使用。",
        "",
        "## 统一规则",
        "",
        "1. 先做确定性替换和结构调整，不要整段让模型自由重写。",
        "2. 修改后仍要保留事实、数据、引用、术语边界。",
        "3. 模糊归因一律补来源或删掉，不用套话补空。",
        "4. 每段最多补 1-2 处人类观察/限制说明，避免重新模板化。",
        "5. 逐段完成后，再复查段间节奏和术语一致性。",
        "",
        "## 逐段任务",
        "",
    ]

    for item in findings:
        lines.extend(
            [
                f"### P{item['paragraph']:03d} - {item['risk']}",
                "",
                f"- 命中模式：{', '.join(item['pattern_labels']) if item['pattern_labels'] else '无'}",
                f"- 高危词：{', '.join(item['cliche_terms']) if item['cliche_terms'] else '无'}",
                f"- 改写方向：{'；'.join(item['rewrite_guidance']) if item['rewrite_guidance'] else '保持事实边界，减少模板化表达。'}",
                "",
                "原段落：",
                "",
                "```text",
                item["text"],
                "```",
                "",
                "输出要求：",
                "",
                "1. `revised_paragraph`：只输出本段改写结果。",
                "2. `deterministic_changes`：列出删套话、拆句、术语统一等动作。",
                "3. `human_features_added`：列出补入的不确定性、观察细节或限制说明。",
                "4. `preserved_facts`：列出必须保留的事实、数据、引用、术语。",
                "5. `needs_source` / `needs_evidence`：没有则写 `none`。",
                "",
            ]
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze thesis prose with the aigc-reduce deep-pattern rules.")
    parser.add_argument("input", nargs="?", help="Draft text/markdown/html/docx file. Reads stdin when omitted.")
    parser.add_argument("--out", default="paper-context/aigc/aigc-style-report.md", help="Markdown report path.")
    parser.add_argument("--json-out", default="paper-context/aigc/aigc-style-report.json", help="JSON report path.")
    parser.add_argument("--final-paragraph-pass-out", help="Optional paragraph-by-paragraph final pass work order.")
    args = parser.parse_args()

    input_path = Path(args.input).resolve() if args.input else None
    text = read_text(input_path)
    payload = analyze_style(text)
    payload["source"] = str(input_path) if input_path else "stdin"

    out_path = Path(args.out).resolve()
    json_path = Path(args.json_out).resolve()
    write_markdown(payload, out_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"Wrote {json_path}")

    if args.final_paragraph_pass_out:
        final_path = Path(args.final_paragraph_pass_out).resolve()
        write_final_paragraph_pass(payload, final_path)
        print(f"Wrote {final_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
