#!/usr/bin/env python3
"""Build a paragraph-by-paragraph aigc-reduce revision plan without free rewriting."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aigc_reduce_core import (
    analyze_style,
    coefficient_of_variation,
    overall_scan,
    read_text,
    split_paragraphs,
    split_sentences,
)


REPLACEMENT_SUGGESTIONS = {
    "此外": ["另一方面", "从另一角度看", "删除"],
    "与此同时": ["同时", "另一方面", "结合前文来看"],
    "综上所述": ["删除", "把以上结论放在一起看", "改为具体判断"],
    "需要指出的是": ["值得说明的是", "删除"],
    "值得注意的是": ["有意思的是", "特别之处在于", "删除"],
    "研究表明": ["实验表明", "从结果来看", "测试结果显示"],
    "相关研究表明": ["给出具体来源", "从结果来看", "删除模糊归因"],
    "分析认为": ["推测", "据此推断", "可能的原因是"],
    "具体而言": ["从数据来看", "拆开来看"],
    "具体来说": ["从细节来看", "细看各组数据"],
    "显著": ["明显", "大幅", "可观地"],
    "进一步": ["更深入地", "删除"],
    "整体": ["全局来看", "汇总来看"],
    "从而": ["拆句", "改成直接因果", "删除空转衔接"],
    "进而": ["拆句", "因此", "删除空转衔接"],
    "由此": ["因此", "所以", "拆句"],
    "确保": ["保证", "使"],
    "旨在": ["为了", "目的是"],
    "提升": ["提高", "增强", "改善"],
    "优化": ["改进", "调整"],
    "阐述": ["说明", "解释"],
    "揭示": ["显示", "指向"],
    "助力": ["帮助", "有利于"],
    "赋能": ["支持", "帮助"],
    "协同": ["配合", "共同"],
    "融合": ["结合", "混合"],
    "探索": ["尝试", "研究", "考察"],
    "梳理": ["整理", "回顾"],
    "具有良好的应用前景": ["改成具体应用判断", "改成适用范围", "改成限制条件"],
    "具有重要的理论价值与现实意义": ["改成具体结论", "改成可验证贡献"],
    "有研究表明": ["补真实来源", "删除模糊归因"],
    "学界普遍认为": ["补真实来源", "删除模糊归因"],
    "相关研究指出": ["补真实来源", "删除模糊归因"],
}

PATTERN_CHECKLIST = {
    "significance_inflation": "删掉“重要/关键/深远”等词后，句子是否仍成立？",
    "synonym_cycling": "同一对象是否在本段被叫成三种以上名称？",
    "rule_of_three": "是否能把机械三件套拆成两项重点展开或自然叙述？",
    "copula_avoidance": "能否把“体现/扮演角色/起作用”改成直接谓语或“是”？",
    "vague_attribution": "是否已经补上具体来源编号或删除模糊归因？",
    "formulaic_challenge": "局限和展望是否已改成具体条件、样本或场景限制？",
    "superficial_ing": "是否还存在“从而/进而/由此”连挂的空转分析？",
    "generic_positive": "结论是否已改成具体判断、边界或后续任务？",
    "emdash_overuse": "本段破折号是否压到 1 个以内？",
    "false_ranges": "是否已删去“从宏观到微观”这类虚假范围？",
}


def build_round1_actions(paragraph: str, cliche_terms: list[str]) -> list[str]:
    actions: list[str] = []
    seen: set[str] = set()
    for term in cliche_terms:
        if term in REPLACEMENT_SUGGESTIONS and term not in seen:
            suggestions = " / ".join(REPLACEMENT_SUGGESTIONS[term][:3])
            actions.append(f"替换 `{term}` -> {suggestions}")
            seen.add(term)
    if "首先" in paragraph and "其次" in paragraph:
        actions.append("拆掉 `首先/其次/最后` 序列，改成自然叙述或两项重点展开。")
    if "（1）" in paragraph or "(1)" in paragraph:
        actions.append("把编号式列举改成自然句群，不保留机械编号。")
    if "：" in paragraph and "；" in paragraph:
        actions.append("把 `A：…；B：…` 的冒号并列结构拆成独立句。")
    return actions


def build_round2_actions(paragraph: str) -> list[str]:
    sentences = split_sentences(paragraph)
    lengths = [len(sentence) for sentence in sentences]
    cv = coefficient_of_variation(lengths)
    actions: list[str] = []
    if cv < 0.4 and len(sentences) >= 2:
        actions.append("句长过于均匀：拆一条 50 字以上长句，插入一条 10 字以内短句，提升突发性。")
    if any(length >= 50 for length in lengths):
        actions.append("长句优先断开成 15-25 字短句，避免整段节奏过平。")
    if not any(marker in paragraph for marker in ["推测", "猜测", "不过", "但这还需要", "我们倾向于认为"]):
        actions.append("如证据允许，可补 1 句受控的人类判断或限制说明。")
    if any(keyword in paragraph for keyword in ["实验", "测试", "数据"]) and not any(keyword in paragraph for keyword in ["浮动", "偏高", "观察到", "过程中发现"]):
        actions.append("如原材料允许，可补 1 句操作观察 / 参数波动 / 异常值说明。")
    return actions


def build_round3_checks(pattern_ids: list[str]) -> list[str]:
    checks = [PATTERN_CHECKLIST[item] for item in pattern_ids if item in PATTERN_CHECKLIST]
    if not checks:
        checks.append("复查是否仍有模板连接词、空泛总结或节奏过平的问题。")
    return checks


def build_plan(text: str) -> dict[str, object]:
    style_payload = analyze_style(text)
    scan_payload = overall_scan(text)
    paragraphs = split_paragraphs(text)
    style_findings = {item["paragraph"]: item for item in style_payload["findings"]}
    scan_findings = {item["paragraph"]: item for item in scan_payload["paragraph_findings"]}

    paragraph_plans = []
    for idx, paragraph in enumerate(paragraphs, 1):
        style_item = style_findings[idx]
        scan_item = scan_findings[idx]
        round1 = build_round1_actions(paragraph, style_item.get("cliche_terms", []))
        round2 = build_round2_actions(paragraph)
        round3 = build_round3_checks(style_item.get("pattern_ids", []))
        modification_pressure = "high" if style_item["risk"] == "high" else "medium" if style_item["risk"] == "medium" else "low"
        paragraph_plans.append(
            {
                "paragraph": idx,
                "risk": style_item["risk"],
                "modification_pressure": modification_pressure,
                "pattern_labels": style_item.get("pattern_labels", []),
                "triggered_metrics": scan_item.get("triggered_metrics", []),
                "round1_remove_ai_traces": round1,
                "round2_add_human_features": round2,
                "round3_anti_ai_audit": round3,
                "text_preview": style_item["text_preview"],
                "text": paragraph,
            }
        )

    return {
        "schema_version": "1.0",
        "method_source": "xiaofenggan01/aigc-reduce",
        "summary": {
            "overall_style_risk": style_payload["summary"]["overall_risk"],
            "estimated_aigc_rate": scan_payload["estimated_aigc_rate"],
            "paragraph_count": len(paragraph_plans),
        },
        "paragraph_plans": paragraph_plans,
    }


def write_markdown(payload: dict[str, object], path: Path) -> None:
    lines = [
        "# AIGC Revision Plan",
        "",
        "This plan follows the `xiaofenggan01/aigc-reduce` three-round protocol.",
        "It is a deterministic revision plan, not a free rewrite.",
        "",
        f"- Overall style risk: `{payload['summary']['overall_style_risk']}`",
        f"- Estimated AIGC rate: `{payload['summary']['estimated_aigc_rate']}%`",
        f"- Paragraphs: `{payload['summary']['paragraph_count']}`",
        "",
        "## Plan Table",
        "",
        "| Paragraph | Risk | Pressure | Deep patterns | Triggered metrics |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in payload["paragraph_plans"]:
        lines.append(
            f"| P{item['paragraph']:03d} | {item['risk']} | {item['modification_pressure']} | "
            f"{'<br>'.join(item['pattern_labels']) if item['pattern_labels'] else 'none'} | "
            f"{'<br>'.join(item['triggered_metrics']) if item['triggered_metrics'] else 'none'} |"
        )

    lines.extend(["", "## Paragraph Actions", ""])
    for item in payload["paragraph_plans"]:
        lines.append(f"### P{item['paragraph']:03d} - {item['risk']}")
        lines.append("")
        lines.append(f"- Preview: {item['text_preview']}")
        lines.append("- Round 1 - Remove AI traces:")
        for action in item["round1_remove_ai_traces"] or ["无明显词级/句级替换动作，保留原术语。"]:
            lines.append(f"  - {action}")
        lines.append("- Round 2 - Add human features:")
        for action in item["round2_add_human_features"] or ["无需额外注入人类特征，避免过写。"]:
            lines.append(f"  - {action}")
        lines.append("- Round 3 - Anti-AI audit:")
        for action in item["round3_anti_ai_audit"]:
            lines.append(f"  - {action}")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an aigc-reduce-style deterministic revision plan.")
    parser.add_argument("input", nargs="?", help="Draft text/markdown/html/docx file. Reads stdin when omitted.")
    parser.add_argument("--out", default="paper-context/aigc/aigc-revision-plan.md", help="Markdown plan path.")
    parser.add_argument("--json-out", default="paper-context/aigc/aigc-revision-plan.json", help="JSON plan path.")
    args = parser.parse_args()

    input_path = Path(args.input).resolve() if args.input else None
    text = read_text(input_path)
    payload = build_plan(text)
    payload["source"] = str(input_path) if input_path else "stdin"

    out_path = Path(args.out).resolve()
    json_path = Path(args.json_out).resolve()
    write_markdown(payload, out_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"Wrote {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
