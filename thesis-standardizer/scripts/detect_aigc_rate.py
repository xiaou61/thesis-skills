#!/usr/bin/env python3
"""Estimate AIGC-style risk for academic prose.

This helper follows a five-dimension academic AIGC analysis workflow inspired by
AIGC-Detector-Pro. It is not an official detector and cannot verify an
institutional AIGC percentage.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path


DIMENSION_WEIGHTS = {
    "sentence_regularity": 0.25,
    "connector_density": 0.20,
    "voice_characteristics": 0.15,
    "vocabulary_diversity": 0.15,
    "argumentation_depth": 0.25,
}

DIMENSION_LABELS_ZH = {
    "sentence_regularity": "句式规整度",
    "connector_density": "逻辑词密度",
    "voice_characteristics": "语态特征",
    "vocabulary_diversity": "词汇多样性",
    "argumentation_depth": "论证深度",
}

DIMENSION_LABELS_EN = {
    "sentence_regularity": "Sentence Regularity",
    "connector_density": "Connector Density",
    "voice_characteristics": "Voice Characteristics",
    "vocabulary_diversity": "Vocabulary Diversity",
    "argumentation_depth": "Argumentation Depth",
}

CONNECTORS_ZH = [
    "首先",
    "其次",
    "再次",
    "最后",
    "综上所述",
    "由此可见",
    "具体而言",
    "也就是说",
    "换言之",
    "值得注意的是",
    "需要指出的是",
    "总体而言",
    "一方面",
    "另一方面",
    "与此同时",
]

CONNECTORS_EN = [
    "firstly",
    "secondly",
    "finally",
    "in conclusion",
    "therefore",
    "it is worth noting",
    "it should be emphasized",
    "to some extent",
    "arguably",
    "building on previous work",
]

TEMPLATE_PATTERNS = [
    r"首先.{0,80}其次.{0,80}(再次|最后)",
    r"一是.{0,80}二是.{0,80}三是",
    r"(随着|近年来|当前|现阶段).{0,40}(发展|推进|普及|深化)",
    r"(基于|依据|根据).{0,24}(理论|框架|原则|模型)",
    r"(综上所述|由此可见|可以看出)",
    r"(firstly|secondly|in conclusion|it is important to note that)",
]

PASSIVE_PATTERNS = [
    r"被[\u4e00-\u9fff]{1,8}(分析|发现|证明|认为|应用|用于)",
    r"(得到|受到|进行|实现了|完成了).{0,8}(分析|验证|优化|提升|处理)",
    r"(该设计|该方法|该系统|这一做法).{0,18}(体现|反映|表明|说明)",
    r"(was|were|is|are|has been|have been)\s+\w+ed\b",
    r"it\s+(was|is)\s+(found|shown|demonstrated|suggested)\s+that",
]

GENERIC_TERMS = [
    "显著",
    "有效",
    "重要",
    "促进",
    "提升",
    "优化",
    "具有重要意义",
    "提供参考",
    "应用价值",
    "前景广阔",
    "significantly",
    "effectively",
    "important",
    "facilitate",
    "comprehensive",
    "leverage",
    "utilize",
]

EVIDENCE_PATTERNS = [
    r"\[[0-9,\-\s]+\]",
    r"（[^）]{1,20}(19|20)\d{2}[^）]{0,20}）",
    r"\b(19|20)\d{2}\b",
    r"\d+(\.\d+)?\s?(%|％|ms|s|秒|人|次|条|组|个|GB|MB)",
    r"(表|图)\s?\d+",
    r"(实验|测试|样本|访谈|问卷|数据|日志|截图|接口|数据库|代码|对比|指标|误差|限制|不足|案例)",
    r"(experiment|sample|dataset|table|figure|result|baseline|metric|limitation|case study|method)",
]

LIMITATION_TERMS = [
    "限制",
    "不足",
    "误差",
    "边界",
    "局限",
    "未能",
    "仅",
    "limitation",
    "caveat",
    "however",
    "although",
]


@dataclass
class ParagraphRateFinding:
    paragraph: int
    score: int
    risk: str
    dimension_scores: dict[str, int]
    issues: list[str]
    rationale: str
    text_preview: str
    char_count: int


def clamp(value: float, low: float = 0, high: float = 100) -> int:
    return int(round(max(low, min(high, value))))


def read_bytes_text(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def read_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        document = zf.read("word/document.xml")
    root = ET.fromstring(document)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: list[str] = []
    for para in root.findall(".//w:p", ns):
        texts = [node.text or "" for node in para.findall(".//w:t", ns)]
        text = "".join(texts).strip()
        if text:
            paragraphs.append(text)
    return "\n\n".join(paragraphs)


def read_text(path: Path | None) -> str:
    if path is None:
        return read_bytes_text(sys.stdin.buffer.read())
    if path.suffix.lower() == ".docx":
        return read_docx(path)
    return read_bytes_text(path.read_bytes())


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
        blocks = [block.strip() for block in re.split(r"(?<=[。！？!?；;])\s*", text) if len(block.strip()) >= 20]
    return blocks


def split_sentences(text: str) -> list[str]:
    return [item.strip() for item in re.split(r"(?<=[。！？!?；;.!?])\s*", text) if item.strip()]


def sentence_start(text: str) -> str:
    clean = re.sub(r"^[\s#>*\-0-9.、（）()]+", "", text.strip())
    match = re.match(r"[\u4e00-\u9fffA-Za-z]{1,8}", clean)
    return match.group(0) if match else ""


def tokenize(text: str) -> list[str]:
    english = re.findall(r"[A-Za-z][A-Za-z\-']+", text.lower())
    chinese_chars = re.findall(r"[\u4e00-\u9fff]", text)
    chinese_bigrams = ["".join(chinese_chars[i : i + 2]) for i in range(max(0, len(chinese_chars) - 1))]
    numbers = re.findall(r"\d+(?:\.\d+)?", text)
    return english + chinese_bigrams + numbers


def count_regex(patterns: list[str], text: str, flags: int = re.I) -> int:
    return sum(len(re.findall(pattern, text, flags)) for pattern in patterns)


def count_terms(terms: list[str], text: str) -> int:
    lower = text.lower()
    return sum(lower.count(term.lower()) for term in terms)


def coefficient_of_variation(values: list[int]) -> float:
    if len(values) < 2:
        return 1.0
    mean = sum(values) / len(values)
    if mean <= 0:
        return 1.0
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return math.sqrt(variance) / mean


def risk_label(score: int) -> str:
    if score >= 75:
        return "high"
    if score >= 55:
        return "medium"
    if score >= 35:
        return "low"
    return "clear"


def estimate_confidence(char_count: int, paragraph_count: int) -> str:
    if char_count >= 3000 and paragraph_count >= 8:
        return "medium-high"
    if char_count >= 1200 and paragraph_count >= 4:
        return "medium"
    if char_count >= 300:
        return "low-medium"
    return "low"


def score_text(text: str, paragraph_index: int = 0) -> tuple[dict[str, int], list[str], str]:
    paragraphs = split_paragraphs(text)
    sentences = split_sentences(text)
    sentence_lengths = [len(sentence) for sentence in sentences if len(sentence) >= 2]
    tokens = tokenize(text)
    char_count = len(re.sub(r"\s+", "", text))

    template_hits = count_regex(TEMPLATE_PATTERNS, text)
    connector_hits = count_terms(CONNECTORS_ZH + CONNECTORS_EN, text)
    passive_hits = count_regex(PASSIVE_PATTERNS, text)
    generic_hits = count_terms(GENERIC_TERMS, text)
    evidence_hits = count_regex(EVIDENCE_PATTERNS, text)
    limitation_hits = count_terms(LIMITATION_TERMS, text)

    starts = [sentence_start(paragraph) for paragraph in paragraphs]
    repeated_starts = sum(
        1
        for idx in range(2, len(starts))
        if starts[idx] and starts[idx] == starts[idx - 1] == starts[idx - 2]
    )

    sent_cv = coefficient_of_variation(sentence_lengths)
    avg_sent = sum(sentence_lengths) / max(1, len(sentence_lengths))
    very_uniform = 1 if 0.12 <= sent_cv <= 0.38 and len(sentences) >= 4 else 0
    sentence_regularity = clamp(
        22
        + very_uniform * 25
        + template_hits * 9
        + repeated_starts * 8
        + (12 if 32 <= avg_sent <= 68 and len(sentences) >= 4 else 0)
        - (18 if sent_cv > 0.85 else 0)
    )

    connector_per_sentence = connector_hits / max(1, len(sentences))
    connector_density = clamp(15 + connector_per_sentence * 42 + max(0, connector_hits - 4) * 4)

    passive_per_sentence = passive_hits / max(1, len(sentences))
    voice_characteristics = clamp(18 + passive_per_sentence * 35 + template_hits * 4 + generic_hits * 2)

    unique_ratio = len(set(tokens)) / max(1, len(tokens))
    if len(tokens) < 20:
        vocabulary_diversity = 45
    else:
        vocabulary_diversity = clamp(70 - unique_ratio * 55 + generic_hits * 4 + max(0, len(tokens) - len(set(tokens)) - 12) * 0.8)

    evidence_density = evidence_hits / max(1, len(paragraphs))
    generic_pressure = generic_hits / max(1, len(sentences))
    argumentation_depth = clamp(
        68
        - evidence_density * 15
        - limitation_hits * 6
        + generic_pressure * 35
        + (18 if evidence_hits == 0 and char_count >= 240 else 0)
        + (10 if paragraph_index and char_count < 80 else 0)
    )

    scores = {
        "sentence_regularity": sentence_regularity,
        "connector_density": connector_density,
        "voice_characteristics": voice_characteristics,
        "vocabulary_diversity": vocabulary_diversity,
        "argumentation_depth": argumentation_depth,
    }

    issues: list[str] = []
    if template_hits:
        issues.append(f"模板化句式命中 {template_hits} 次")
    if connector_hits >= 3:
        issues.append(f"逻辑连接词偏密集：{connector_hits} 次")
    if passive_hits:
        issues.append(f"被动/抽象语态命中 {passive_hits} 次")
    if generic_hits:
        issues.append(f"泛化评价词命中 {generic_hits} 次")
    if evidence_hits == 0 and char_count >= 180:
        issues.append("未检测到明显数据、引用、图表、实验或案例证据")
    if repeated_starts:
        issues.append(f"连续段落句首重复 {repeated_starts} 次")
    if not issues:
        issues.append("未发现明显 AIGC 风格高频特征")

    rationale = (
        f"句子数 {len(sentences)}，平均句长 {avg_sent:.1f}，句长变异系数 {sent_cv:.2f}；"
        f"连接词 {connector_hits} 次，证据线索 {evidence_hits} 次，泛化词 {generic_hits} 次。"
    )
    return scores, issues, rationale


def weighted_rate(scores: dict[str, int]) -> int:
    total = 0.0
    for name, weight in DIMENSION_WEIGHTS.items():
        total += scores[name] * weight
    return clamp(total)


def analyze(text: str, source: str, discipline: str) -> dict[str, object]:
    paragraphs = split_paragraphs(text)
    full_scores, full_issues, full_rationale = score_text(text)
    rate = weighted_rate(full_scores)

    findings: list[ParagraphRateFinding] = []
    for idx, paragraph in enumerate(paragraphs, 1):
        scores, issues, rationale = score_text(paragraph, idx)
        paragraph_score = weighted_rate(scores)
        findings.append(
            ParagraphRateFinding(
                paragraph=idx,
                score=paragraph_score,
                risk=risk_label(paragraph_score),
                dimension_scores=scores,
                issues=issues,
                rationale=rationale,
                text_preview=paragraph[:140].replace("\n", " "),
                char_count=len(re.sub(r"\s+", "", paragraph)),
            )
        )

    risk_counts = {"clear": 0, "low": 0, "medium": 0, "high": 0}
    for finding in findings:
        risk_counts[finding.risk] += 1

    char_count = len(re.sub(r"\s+", "", strip_markup(text)))
    payload = {
        "schema_version": "1.0",
        "source": source,
        "discipline": discipline,
        "generated_at": date.today().isoformat(),
        "policy_note": "This is a local heuristic AIGC-style estimate, not an official detector result.",
        "estimated_aigc_rate": rate,
        "overall_risk": risk_label(rate),
        "confidence": estimate_confidence(char_count, len(paragraphs)),
        "char_count": char_count,
        "paragraph_count": len(paragraphs),
        "dimension_weights": DIMENSION_WEIGHTS,
        "dimension_scores": full_scores,
        "overall_issues": full_issues,
        "overall_rationale": full_rationale,
        "risk_counts": risk_counts,
        "paragraph_findings": [asdict(item) for item in findings],
    }
    return payload


def write_markdown(payload: dict[str, object], path: Path) -> None:
    scores = payload["dimension_scores"]
    assert isinstance(scores, dict)
    findings = payload["paragraph_findings"]
    assert isinstance(findings, list)

    lines = [
        "# AIGC Rate Detection Report",
        "",
        "This is a local heuristic estimate, not an official detector score.",
        "",
        f"- Estimated AIGC rate: `{payload['estimated_aigc_rate']}%`",
        f"- Overall risk: `{payload['overall_risk']}`",
        f"- Confidence: `{payload['confidence']}`",
        f"- Discipline: `{payload['discipline']}`",
        f"- Characters: `{payload['char_count']}`",
        f"- Paragraphs: `{payload['paragraph_count']}`",
        f"- Risk counts: `{payload['risk_counts']}`",
        "",
        "## Five-Dimension Scores",
        "",
    ]
    for name, score in scores.items():
        label = DIMENSION_LABELS_ZH.get(name, name)
        weight = DIMENSION_WEIGHTS[name]
        lines.append(f"- {label} / {DIMENSION_LABELS_EN[name]}: `{score}` (weight `{weight:.0%}`)")

    lines.extend(["", "## Overall Rationale", "", str(payload["overall_rationale"]), "", "## Overall Issues", ""])
    for issue in payload["overall_issues"]:
        lines.append(f"- {issue}")

    lines.extend(["", "## Paragraph Findings", ""])
    for item in findings:
        lines.append(f"### Paragraph {item['paragraph']} - {item['risk']} risk")
        lines.append(f"- Estimated rate: `{item['score']}%`")
        lines.append(f"- Characters: `{item['char_count']}`")
        dim = item["dimension_scores"]
        for name, score in dim.items():
            lines.append(f"- {DIMENSION_LABELS_ZH.get(name, name)}: `{score}`")
        lines.append(f"- Rationale: {item['rationale']}")
        lines.append(f"- Issues: {'；'.join(item['issues'])}")
        lines.append(f"- Preview: {item['text_preview']}")
        lines.append("")

    lines.extend(
        [
            "## Use Notes",
            "",
            "- Treat this as a triage signal for revision priority.",
            "- Do not cite this number as an institutional AIGC result.",
            "- For final writing, combine this report with `aigc-style-report.md` and evidence review.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Estimate text AIGC-style rate with a five-dimension heuristic.")
    parser.add_argument("input", nargs="?", help="Text/markdown/html/docx file. Reads stdin when omitted.")
    parser.add_argument("--out", default="paper-context/aigc/aigc-detection-report.md", help="Markdown report path.")
    parser.add_argument("--json-out", default="paper-context/aigc/aigc-detection-report.json", help="JSON report path.")
    parser.add_argument("--discipline", default="general", help="Optional discipline label for the report.")
    args = parser.parse_args()

    input_path = Path(args.input).resolve() if args.input else None
    text = read_text(input_path)
    payload = analyze(text, str(input_path) if input_path else "stdin", args.discipline)

    out = Path(args.out).resolve()
    json_out = Path(args.json_out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    write_markdown(payload, out)
    json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {out}")
    print(f"Wrote {json_out}")
    print(f"Estimated AIGC rate: {payload['estimated_aigc_rate']}% ({payload['overall_risk']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

