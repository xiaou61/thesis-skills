#!/usr/bin/env python3
"""Generate a thesis prose style-risk report.

This helper flags formulaic academic prose patterns. It is not an AI detector
and does not predict institutional AIGC scores.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


PATTERNS = [
    ("macro_opening", r"^(随着|近年来|当前|现阶段|在.{0,18}背景下).{0,30}(发展|推进|普及|深化|转型)"),
    ("theory_start", r"^(依据|基于|根据|按照|遵循).{0,20}(理论|框架|原则|观点|模型)"),
    ("summary_tail", r"(由此可见|综上所述|不难发现|可以看出|因此可以得出结论|这提示我们)"),
    ("case_tail", r"(此案例|该案例|这一案例|上述案例).{0,12}(印证|揭示|表明|体现|挑战)"),
    ("rigid_sequence", r"(首先|其次|再次|最后|第一|第二|第三|一方面|另一方面)"),
    ("passive_shell", r"(该处理|该设计|该方法|该决策|这一做法|上述选择|该机制).{0,18}(体现|基于|反映|展现|印证|凸显)"),
    ("core_problem_shell", r"(核心问题是|核心问题在于|核心挑战在于|主要矛盾体现在|关键问题是如何)"),
    ("vague_attribution", r"(专家认为|研究表明|业内普遍认为|有观点认为|一些学者指出|相关研究指出)"),
    ("filler_phrase", r"(值得注意的是|不难发现|需要指出的是|总体而言|从某种程度上|换言之|与此同时)"),
    ("generic_positive", r"(具有重要意义|意义深远|意义重大|前景广阔|提供了新思路|开辟了新方向|不可或缺|具有较高应用价值)"),
    ("copula_avoidance", r"(作为.{0,12}重要载体|扮演着.{0,12}角色|充当着.{0,12}功能|起到了.{0,12}作用)"),
    ("value_claim_without_boundary", r"(提升|优化|改善|增强|促进|推动).{0,20}(效率|质量|体验|能力|水平|发展)"),
    ("method_shell", r"(通过|利用|采用).{0,18}(方式|方法|手段|路径|策略).{0,18}(实现|完成|提升|优化|解决)"),
    ("parallel_triad", r"([\u4e00-\u9fffA-Za-z]{2,8}[性化度][、，；]){2,}[\u4e00-\u9fffA-Za-z]{2,8}[性化度]"),
    ("double_clause_balance", r"(不仅|不但).{0,80}(而且|同时|还|也)"),
    ("absolute_claim", r"(必然|显著提升|有效提高|极大促进|全面提升|根本解决|完全满足)"),
]

PATTERN_LABELS = {
    "macro_opening": "宏大背景起笔",
    "theory_start": "理论/框架前置起笔",
    "summary_tail": "套句式段末总结",
    "case_tail": "案例套句收束",
    "rigid_sequence": "过整齐枚举",
    "passive_shell": "被动分析壳",
    "core_problem_shell": "核心问题套壳",
    "vague_attribution": "模糊归因",
    "filler_phrase": "空引导/填充词",
    "generic_positive": "空泛价值判断",
    "copula_avoidance": "抽象角色壳",
    "value_claim_without_boundary": "无边界效果声明",
    "method_shell": "方法套壳",
    "parallel_triad": "并列三元结构",
    "double_clause_balance": "不仅而且式均衡句",
    "absolute_claim": "绝对化效果判断",
    "excessive_bold": "正文过度加粗",
    "repeated_start": "连续段落句首重复",
    "long_paragraph": "段落过长",
}

CLICHE_TERMS = [
    "随着社会的发展",
    "信息化时代",
    "数字化转型",
    "深刻揭示",
    "深入探讨",
    "系统梳理",
    "综合运用",
    "理论支撑",
    "有效解决",
    "充分说明",
    "进一步",
    "不可或缺",
    "重要意义",
    "现实意义",
    "应用价值",
    "优化路径",
    "实践价值",
]

HARD_FAILURE_PATTERNS = {
    "vague_attribution": "vague attribution needs a verified source or removal",
    "generic_positive": "generic positive conclusion needs concrete academic claim",
    "absolute_claim": "absolute effect claim needs evidence, condition, or softer wording",
    "value_claim_without_boundary": "effect claim needs a concrete object, metric, sample, or limitation",
}

REVISION_GUIDANCE = {
    "macro_opening": "删除宏观背景，把本段直接落到研究对象、材料或章节任务。",
    "theory_start": "不要用理论名开头；把理论放到解释链条中真正需要的位置。",
    "summary_tail": "删掉套句式总结，改为具体推论、限制条件或承接下一段的问题。",
    "case_tail": "把“案例表明”改成案例中的具体变量、步骤、冲突或结果。",
    "rigid_sequence": "打散等长枚举，让最重要的理由多占篇幅，次要内容合并。",
    "passive_shell": "把“体现/反映”改成具体设计原因、实验原因或文本证据。",
    "core_problem_shell": "明确问题对象、发生条件和影响范围。",
    "vague_attribution": "补真实来源，或删除“研究表明/专家认为”等无主语归因。",
    "filler_phrase": "删除不增加信息的引导词。",
    "generic_positive": "把价值判断换成具体结论、适用范围、局限或后续工作。",
    "copula_avoidance": "用直接谓语替代“扮演角色/起到作用”。",
    "value_claim_without_boundary": "补充指标、对象、场景、样本或证据边界。",
    "method_shell": "写清采用该方法的原因、输入、处理过程和输出。",
    "parallel_triad": "拆开并列词串，保留有证据支撑的核心维度。",
    "double_clause_balance": "避免机械对称，按因果或递进关系重排句子。",
    "absolute_claim": "删除绝对化词语，加入条件、数据或保守表达。",
    "long_paragraph": "按论点或证据边界拆段。",
    "repeated_start": "调整段首句功能，避免连续段落同一节奏。",
}


@dataclass
class ParagraphFinding:
    paragraph: int
    score: int
    risk: str
    patterns: list[str]
    pattern_labels: list[str]
    cliche_terms: list[str]
    hard_failures: list[str]
    rewrite_guidance: list[str]
    repeated_start: bool
    char_count: int
    text_preview: str
    text: str


def read_text(path: Path | None) -> str:
    if path is None:
        raw = sys.stdin.buffer.read()
    else:
        raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def strip_markup(text: str) -> str:
    text = re.sub(r"(?is)<script.*?</script>", " ", text)
    text = re.sub(r"(?is)<style.*?</style>", " ", text)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p\s*>", "\n\n", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_paragraphs(text: str) -> list[str]:
    text = strip_markup(text)
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    if len(blocks) <= 1:
        blocks = [block.strip() for block in re.split(r"(?<=[。！？!?])\s*", text) if len(block.strip()) >= 30]
    return blocks


def sentence_start(text: str) -> str:
    clean = re.sub(r"^[\s#>*\-0-9.、（）()]+", "", text.strip())
    match = re.match(r"[\u4e00-\u9fffA-Za-z]{1,6}", clean)
    return match.group(0) if match else ""


def classify(score: int) -> str:
    if score >= 5:
        return "high"
    if score >= 3:
        return "medium"
    if score >= 1:
        return "low"
    return "clear"


def analyze_paragraphs(paragraphs: list[str]) -> list[ParagraphFinding]:
    starts = [sentence_start(paragraph) for paragraph in paragraphs]
    findings: list[ParagraphFinding] = []

    for idx, paragraph in enumerate(paragraphs, 1):
        hits: list[str] = []
        for name, pattern in PATTERNS:
            if re.search(pattern, paragraph):
                hits.append(name)

        cliches = [term for term in CLICHE_TERMS if term in paragraph]
        score = len(hits) + max(0, len(cliches) - 1)
        hard_failures = [name for name in hits if name in HARD_FAILURE_PATTERNS]

        repeated_start = False
        if idx >= 3 and starts[idx - 1] and starts[idx - 1] == starts[idx - 2] == starts[idx - 3]:
            repeated_start = True
            hits.append("repeated_start")
            score += 1

        bold_count = paragraph.count("**") // 2 + len(re.findall(r"<b>|<strong>", paragraph, re.I))
        if bold_count > 2:
            hits.append("excessive_bold")
            score += 1

        if len(paragraph) >= 520:
            hits.append("long_paragraph")
            score += 1

        guidance = []
        for pattern_name in hits:
            instruction = REVISION_GUIDANCE.get(pattern_name)
            if instruction and instruction not in guidance:
                guidance.append(instruction)

        findings.append(
            ParagraphFinding(
                paragraph=idx,
                score=score,
                risk=classify(score),
                patterns=hits,
                pattern_labels=[PATTERN_LABELS.get(name, name) for name in hits],
                cliche_terms=cliches,
                hard_failures=hard_failures,
                rewrite_guidance=guidance[:5],
                repeated_start=repeated_start,
                char_count=len(paragraph),
                text_preview=paragraph[:120].replace("\n", " "),
                text=paragraph,
            )
        )
    return findings


def summarize(findings: list[ParagraphFinding]) -> dict[str, object]:
    counts = {"clear": 0, "low": 0, "medium": 0, "high": 0}
    pattern_counts: dict[str, int] = {}
    hard_failures: list[dict[str, object]] = []
    for finding in findings:
        counts[finding.risk] += 1
        for pattern in finding.patterns:
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
            if pattern in HARD_FAILURE_PATTERNS:
                hard_failures.append(
                    {
                        "paragraph": finding.paragraph,
                        "pattern": pattern,
                        "message": HARD_FAILURE_PATTERNS[pattern],
                    }
                )

    if counts["high"]:
        overall = "high"
    elif counts["medium"]:
        overall = "medium"
    elif counts["low"]:
        overall = "low"
    else:
        overall = "clear"

    return {
        "overall_risk": overall,
        "paragraph_count": len(findings),
        "risk_counts": counts,
        "pattern_counts": dict(sorted(pattern_counts.items())),
        "hard_failures": hard_failures,
    }


def write_markdown(payload: dict[str, object], path: Path) -> None:
    summary = payload["summary"]
    findings = payload["findings"]
    assert isinstance(summary, dict)
    assert isinstance(findings, list)

    lines = [
        "# AIGC Style Governance Report",
        "",
        "This is a style-risk report, not an AI-detector score.",
        "The goal is academic naturalness, evidence density, and source integrity.",
        "",
        f"- Overall risk: `{summary['overall_risk']}`",
        f"- Paragraphs: `{summary['paragraph_count']}`",
        f"- Risk counts: `{summary['risk_counts']}`",
        "",
        "## Pattern Counts",
        "",
    ]
    pattern_counts = summary.get("pattern_counts", {})
    if pattern_counts:
        for name, count in pattern_counts.items():
            lines.append(f"- `{name}`: {count}")
    else:
        lines.append("- No major formulaic patterns detected.")

    hard_failures = summary.get("hard_failures", [])
    lines.extend(["", "## Hard Failures", ""])
    if hard_failures:
        for item in hard_failures:
            lines.append(f"- Paragraph {item['paragraph']}: `{item['pattern']}` - {item['message']}")
    else:
        lines.append("- None.")

    lines.extend(["", "## Paragraph Findings", ""])
    for item in findings:
        if item["risk"] == "clear":
            continue
        lines.append(f"### Paragraph {item['paragraph']} - {item['risk']} risk")
        lines.append(f"- Score: `{item['score']}`")
        labels = item.get("pattern_labels") or item["patterns"]
        lines.append(f"- Patterns: {', '.join(labels) if labels else 'none'}")
        lines.append(f"- Cliche terms: {', '.join(item['cliche_terms']) if item['cliche_terms'] else 'none'}")
        if item.get("hard_failures"):
            lines.append(f"- Hard constraints: {', '.join(item['hard_failures'])}")
        if item.get("rewrite_guidance"):
            lines.append(f"- Rewrite moves: {'；'.join(item['rewrite_guidance'])}")
        lines.append(f"- Characters: `{item.get('char_count', 0)}`")
        lines.append(f"- Preview: {item['text_preview']}")
        lines.append("")

    lines.extend(
        [
            "## Suggested Revision Order",
            "",
            "1. Fix vague attribution with verified sources or remove it.",
            "2. Replace generic conclusions with concrete claims, limits, or next-step questions.",
            "3. Break rigid enumeration and repeated paragraph rhythm.",
            "4. Remove filler phrases and excessive academic cliches.",
            "5. Preserve facts and mark unsupported claims as `needs_source`.",
            "6. For a final full-paper pass, use paragraph-by-paragraph rewriting only when the token budget is acceptable.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_final_paragraph_pass(payload: dict[str, object], path: Path) -> None:
    findings = payload["findings"]
    assert isinstance(findings, list)

    lines = [
        "# AIGC 最终降低版分段工作单",
        "",
        "本文件用于把论文按段落逐段处理：逐段诊断、逐段改写、逐段复查，最后再拼接全文。",
        "",
        "> 注意：该模式会把每个段落都作为独立任务处理，并要求保留事实、引用、数据边界和修改记录，极度消耗 token。只建议用于终稿、外部报告集中命中，或用户明确要求“最终降低版”时。",
        "",
        "## 全局规则",
        "",
        "1. 不承诺绕过检测器，只做中文学术表达质量治理。",
        "2. 不新增未核验事实、实验、数据、参考文献、DOI 或作者信息。",
        "3. 每段先保留原意和证据边界，再调整句群结构、连接方式和论证密度。",
        "4. 模糊归因统一改为真实来源或标注 `needs_source`。",
        "5. 证据不足的位置标注 `needs_evidence`，不要用套话补空。",
        "6. 最终拼接后再检查段间衔接，避免每段都像孤立改写。",
        "",
        "## 逐段任务",
        "",
    ]

    for item in findings:
        paragraph_id = item["paragraph"]
        risk = item["risk"]
        labels = item.get("pattern_labels") or item.get("patterns", [])
        guidance = item.get("rewrite_guidance") or ["保持事实，减少模板化表达，增强具体论证。"]
        lines.extend(
            [
                f"### P{paragraph_id:03d} - {risk}",
                "",
                f"- 命中模式：{', '.join(labels) if labels else '无明显模式'}",
                f"- 字数：`{item.get('char_count', 0)}`",
                f"- 改写动作：{'；'.join(guidance)}",
                "",
                "原段落：",
                "",
                "```text",
                item.get("text", ""),
                "```",
                "",
                "输出要求：",
                "",
                "1. `revised_paragraph`：只输出本段改写结果。",
                "2. `changes`：列出删套话、调结构、补边界等关键动作。",
                "3. `preserved_facts`：列出保留的事实、数据、引用或术语。",
                "4. `needs_source` / `needs_evidence`：没有则写 `none`。",
                "",
            ]
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze thesis prose for formulaic AIGC-style risks.")
    parser.add_argument("input", nargs="?", help="Draft text/markdown/html file. Reads stdin when omitted.")
    parser.add_argument("--out", default="paper-context/aigc/aigc-style-report.md", help="Markdown report path.")
    parser.add_argument("--json-out", default="paper-context/aigc/aigc-style-report.json", help="JSON report path.")
    parser.add_argument(
        "--final-paragraph-pass-out",
        help="Optional Markdown work order for the token-heavy paragraph-by-paragraph final pass.",
    )
    args = parser.parse_args()

    input_path = Path(args.input).resolve() if args.input else None
    text = read_text(input_path)
    paragraphs = split_paragraphs(text)
    findings = analyze_paragraphs(paragraphs)
    payload = {
        "schema_version": "1.0",
        "source": str(input_path) if input_path else "stdin",
        "summary": summarize(findings),
        "findings": [asdict(item) for item in findings],
    }

    out = Path(args.out).resolve()
    json_out = Path(args.json_out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    write_markdown(payload, out)
    json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {out}")
    print(f"Wrote {json_out}")
    if args.final_paragraph_pass_out:
        final_pass_out = Path(args.final_paragraph_pass_out).resolve()
        write_final_paragraph_pass(payload, final_pass_out)
        print(f"Wrote {final_pass_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
