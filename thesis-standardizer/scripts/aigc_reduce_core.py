#!/usr/bin/env python3
"""Local AIGC detection/style heuristics adapted from xiaofenggan01/aigc-reduce."""

from __future__ import annotations

import html
import importlib.util
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path


TEMPLATE_PATTERNS = [
    r"^(综上所述[，,])",
    r"^(基于.{2,10}(分析|研究|探讨))",
    r"^(通过.{2,15}(验证|实验|研究|测定))",
    r"^(随着.{2,20}(发展|进步|深入))",
    r"^(近年来[，,])",
    r"^(在.{2,20}(背景下|条件下|过程中))",
    r"^(本研究[旨在对通过])",
    r"^(目前[，,])",
    r"^(当前[，,])",
    r"^(因此[，,])",
    r"^(由此可见[，,])",
    r"^(总而言之[，,])",
    r"(此外[，,])",
    r"(另外[，,])",
    r"(与此同时[，,])",
    r"(值得注意的是[，,])",
    r"(需要指出的是[，,])",
    r"(据统计[，,])",
    r"(相关研究表明[，,])",
    r"(一般认为[，,])",
    r"(具有重要的.{2,10}(意义|价值|作用))",
    r"(具有广阔的应用前景)",
    r"(为.{2,20}(提供了|奠定了).{2,10}(基础|依据|参考))",
]

PASSIVE_MARKERS = [
    r"被.{1,15}(测定|检测|验证|确认|证明|发现|计算)",
    r"由.{1,15}(进行|完成|测定|检测|计算)",
    r"经.{1,15}(测定|检测|计算|分析)",
    r"通过.{1,15}(测定|检测|验证|实验|计算)",
    r"采用.{1,15}(进行|测定|检测)",
]

NESTED_NUM_PATTERN = re.compile(r"[（(](\d+)[）)]")
COLON_LIST_PATTERN = re.compile(r"[：:]\s*.+?[；;]\s*.+?[；;]")
FULLWIDTH_PUNCT = set("，。！？；：、“”‘’（）【】《》")

AI_PATTERNS = [
    (
        "significance_inflation",
        "重要性膨胀",
        [
            r"(至关重要|不可忽视|深远影响|具有重要价值|提供了重要参考|标志着|开启了新篇章|意义重大|意义深远)",
        ],
        "删除膨胀修饰，改成具体对象、范围或数据。",
    ),
    (
        "synonym_cycling",
        "同义词轮换",
        [],
        "核心术语全文统一，不要对同一对象来回换叫法。",
    ),
    (
        "rule_of_three",
        "三板斧强迫症",
        [
            r"[\u4e00-\u9fffA-Za-z0-9]{1,12}[、，][\u4e00-\u9fffA-Za-z0-9]{1,12}[和及与][\u4e00-\u9fffA-Za-z0-9]{1,12}",
            r"(首先|第一).{0,40}(其次|第二).{0,40}(最后|第三)",
            r"(不仅|不但).{0,40}(而且|同时).{0,40}(甚至|并且)",
        ],
        "打散三件套，改成两项重点展开或自然叙述。",
    ),
    (
        "copula_avoidance",
        "系词回避",
        [
            r"(作为.{0,18}的代表)",
            r"(体现了.{0,24})",
            r"(扮演着.{0,18}的角色)",
            r"(起到了.{0,18}作用)",
        ],
        "该用“是”的地方直接用“是”，避免抽象角色壳。",
    ),
    (
        "vague_attribution",
        "模糊归因",
        [
            r"(有研究表明|学界普遍认为|众所周知|相关研究指出|专家认为|一些学者指出)",
        ],
        "补真实来源或删除模糊归因。",
    ),
    (
        "formulaic_challenge",
        "公式化挑战段",
        [
            r"(尽管取得了.{0,30}成果，但.{0,30}(仍存在|还有).{0,20}(局限性|不足))",
            r"(未来的研究可以进一步探讨)",
        ],
        "把局限写成具体条件、样本或场景限制，不用万能模板句。",
    ),
    (
        "superficial_ing",
        "悬浮式分析",
        [
            r"(?:从而.{0,30}(?:进而|由此))",
            r"(?:(?:从而|进而|由此).*){2,}",
        ],
        "拆句或删去空转衔接，只保留真正有信息的因果链。",
    ),
    (
        "generic_positive",
        "空洞结论",
        [
            r"(具有良好的应用前景|提供了理论和实验依据|具有重要的理论价值与现实意义|前景广阔|应用价值较高)",
        ],
        "换成具体结论、适用范围、限制或下一步工作。",
    ),
    (
        "emdash_overuse",
        "破折号过度使用",
        [],
        "一段最多保留一个破折号，其余改成句号、逗号或括号。",
    ),
    (
        "false_ranges",
        "虚假范围",
        [
            r"(从宏观到微观|从理论到实践|从基础研究到工程应用|涵盖了从.{0,20}到.{0,20}的各个方面)",
        ],
        "直接列出实际覆盖范围，不要用虚化大范围表达。",
    ),
]

CLICHE_TERMS = [
    "此外",
    "与此同时",
    "综上所述",
    "需要指出的是",
    "值得注意的是",
    "具体而言",
    "研究表明",
    "分析认为",
    "显著",
    "有效",
    "进一步",
    "整体",
    "从而",
    "进而",
    "由此",
    "确保",
    "旨在",
    "提升",
    "优化",
    "阐述",
    "揭示",
    "助力",
    "赋能",
    "协同",
    "融合",
    "探索",
    "梳理",
]

SYNONYM_GROUPS = [
    {"凝胶", "胶体", "水凝胶", "复合物"},
    {"硬度", "坚实度", "抗变形能力"},
    {"测定", "检测", "分析", "表征"},
    {"系统", "平台", "模块", "方案"},
    {"提高", "提升", "增强", "改善", "优化"},
]


@dataclass
class ScanParagraphFinding:
    paragraph: int
    risk: str
    triggered_metrics: list[str]
    sentence_cv: float
    template_hits: int
    passive_hits: int
    colon_lists: int
    nested_numbers: int
    comma_per_sentence: float
    paragraph_length: int
    text_preview: str


@dataclass
class StyleParagraphFinding:
    paragraph: int
    score: int
    risk: str
    pattern_ids: list[str]
    pattern_labels: list[str]
    matched_examples: list[str]
    cliche_terms: list[str]
    rewrite_guidance: list[str]
    text_preview: str
    char_count: int
    text: str


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


def load_vendor_scan_module():
    vendor_path = Path(__file__).resolve().parent.parent / "vendor" / "aigc-reduce" / "scripts" / "aigc_scan.py"
    spec = importlib.util.spec_from_file_location("vendor_aigc_scan", vendor_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load vendor aigc_scan.py from {vendor_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(paragraphs) <= 1:
        paragraphs = [p.strip() for p in re.split(r"(?<=[。！？!?])\s*", text) if len(p.strip()) >= 20]
    return paragraphs


def split_sentences(text: str) -> list[str]:
    sentences = re.split(r"[。！？!?;\n]", text)
    return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]


def coefficient_of_variation(values: list[int]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    if mean <= 0:
        return 0.0
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return (variance ** 0.5) / mean


def count_template_matches(text: str) -> dict[str, object]:
    hits: list[str] = []
    for pattern in TEMPLATE_PATTERNS:
        matches = re.findall(pattern, text, re.MULTILINE)
        if matches:
            for match in matches:
                if isinstance(match, tuple):
                    hits.append(next((item for item in match if item), ""))
                else:
                    hits.append(str(match))
    density = len(hits) / max(len(text), 1) * 1000
    return {"count": len(hits), "density_per_1000": round(density, 2), "matches": [hit for hit in hits if hit][:20]}


def count_passive_markers(text: str) -> dict[str, object]:
    total = sum(len(re.findall(pattern, text)) for pattern in PASSIVE_MARKERS)
    sentence_count = max(len(split_sentences(text)), 1)
    per_sentence = total / sentence_count
    return {"count": total, "per_sentence": round(per_sentence, 3)}


def analyze_burstiness(paragraphs: list[str]) -> dict[str, object]:
    lengths: list[int] = []
    for paragraph in paragraphs:
        lengths.extend(len(sentence) for sentence in split_sentences(paragraph))
    if len(lengths) < 3:
        return {"avg_len": 0.0, "std_len": 0.0, "cv": 0.0, "risk": "数据不足"}
    avg_len = sum(lengths) / len(lengths)
    variance = sum((length - avg_len) ** 2 for length in lengths) / len(lengths)
    std_len = variance ** 0.5
    cv = std_len / max(avg_len, 1)
    if cv < 0.25:
        risk = "高风险 — 句子长度过于均匀，典型 AI 特征"
    elif cv < 0.35:
        risk = "中风险 — 句子变化度偏低"
    elif cv < 0.5:
        risk = "低风险"
    else:
        risk = "正常 — 句子长度变化丰富"
    return {"avg_len": round(avg_len, 1), "std_len": round(std_len, 1), "cv": round(cv, 3), "risk": risk}


def analyze_para_symmetry(paragraphs: list[str]) -> dict[str, object]:
    lengths = [len(item) for item in paragraphs]
    if len(lengths) < 3:
        return {"para_count": len(lengths), "avg_para_len": round(sum(lengths) / max(len(lengths), 1), 1), "symmetrical_runs": [], "risk": "段落数不足"}
    runs: list[int] = []
    current = 0
    for idx in range(1, len(lengths)):
        deviation = abs(lengths[idx] - lengths[idx - 1]) / max(lengths[idx - 1], 1)
        if deviation < 0.2:
            current += 1
        else:
            if current >= 2:
                runs.append(current + 1)
            current = 0
    if current >= 2:
        runs.append(current + 1)
    risk = f"发现 {len(runs)} 处对称段落组（3段以上长度相近）" if runs else "未发现明显对称"
    return {"para_count": len(lengths), "avg_para_len": round(sum(lengths) / len(lengths), 1), "symmetrical_runs": runs, "risk": risk}


def count_nested_numbers(text: str) -> dict[str, object]:
    matches = NESTED_NUM_PATTERN.findall(text)
    return {"count": len(matches), "risk": f"检测到 {len(matches)} 处编号标记" if len(matches) > 3 else "正常"}


def count_colon_lists(text: str) -> dict[str, object]:
    matches = COLON_LIST_PATTERN.findall(text)
    return {"count": len(matches), "risk": f"检测到 {len(matches)} 处冒号并列结构" if len(matches) > 1 else "正常"}


def analyze_punctuation(text: str) -> dict[str, object]:
    fullwidth_count = sum(1 for char in text if char in FULLWIDTH_PUNCT)
    total_chars = max(len(text), 1)
    comma_count = text.count("，") + text.count(",")
    sentence_count = max(len(split_sentences(text)), 1)
    commas_per_sentence = comma_count / sentence_count
    risk = "高密度逗号可能是 AI 特征" if commas_per_sentence > 2.5 else "正常"
    return {
        "fullwidth_punct_ratio": round(fullwidth_count / total_chars * 100, 2),
        "commas_per_sentence": round(commas_per_sentence, 2),
        "risk": risk,
    }


def overall_scan(text: str) -> dict[str, object]:
    scan_module = load_vendor_scan_module()
    scan_result = scan_module.scan(text)
    paragraphs = split_paragraphs(text)
    sentences = split_sentences(text)
    template = scan_result["template_phrases"]
    passive = scan_result["passive_voice"]
    burstiness = scan_result["burstiness"]
    para_symmetry = scan_result["para_symmetry"]
    nested = scan_result["nested_numbers"]
    colon = scan_result["colon_lists"]
    punctuation = scan_result["punctuation"]

    risk_count = 0
    if int(template["count"]) > 3:
        risk_count += 1
    if float(passive["per_sentence"]) > 0.3:
        risk_count += 1
    if float(burstiness["cv"]) < 0.35:
        risk_count += 1
    symmetrical_runs = para_symmetry.get("symmetrical_runs", [])
    if isinstance(symmetrical_runs, int):
        symmetrical_runs = [symmetrical_runs] if symmetrical_runs else []
    if list(symmetrical_runs):
        risk_count += 1
    if int(nested["count"]) > 3:
        risk_count += 1
    if float(punctuation["commas_per_sentence"]) > 2.5:
        risk_count += 1

    estimated_rate = min(95, max(8, 18 + risk_count * 12 + int(template["count"]) * 2 + int(nested["count"]) * 2))
    overall_risk = "high" if risk_count >= 4 else "medium" if risk_count >= 2 else "low"

    paragraph_findings: list[ScanParagraphFinding] = []
    for idx, paragraph in enumerate(paragraphs, 1):
        paragraph_template = count_template_matches(paragraph)
        paragraph_passive = count_passive_markers(paragraph)
        paragraph_colon = count_colon_lists(paragraph)
        paragraph_nested = count_nested_numbers(paragraph)
        punctuation_stats = analyze_punctuation(paragraph)
        sentence_lengths = [len(sentence) for sentence in split_sentences(paragraph)]
        sentence_cv = coefficient_of_variation(sentence_lengths)
        triggers: list[str] = []
        if int(paragraph_template["count"]) > 0:
            triggers.append("template_phrases")
        if float(paragraph_passive["per_sentence"]) > 0.3:
            triggers.append("passive_voice")
        if sentence_cv and sentence_cv < 0.35:
            triggers.append("burstiness")
        if int(paragraph_colon["count"]) > 0:
            triggers.append("colon_lists")
        if int(paragraph_nested["count"]) > 0:
            triggers.append("nested_numbers")
        if float(punctuation_stats["commas_per_sentence"]) > 2.5:
            triggers.append("punctuation")
        risk = "high" if len(triggers) >= 3 else "medium" if len(triggers) >= 2 else "low" if triggers else "clear"
        paragraph_findings.append(
            ScanParagraphFinding(
                paragraph=idx,
                risk=risk,
                triggered_metrics=triggers,
                sentence_cv=round(sentence_cv, 3),
                template_hits=int(paragraph_template["count"]),
                passive_hits=int(paragraph_passive["count"]),
                colon_lists=int(paragraph_colon["count"]),
                nested_numbers=int(paragraph_nested["count"]),
                comma_per_sentence=float(punctuation_stats["commas_per_sentence"]),
                paragraph_length=len(paragraph),
                text_preview=paragraph[:140].replace("\n", " "),
            )
        )

    return {
        "summary": scan_result["summary"] or {"total_chars": len(text), "total_paragraphs": len(paragraphs), "total_sentences": len(sentences)},
        "template_phrases": template,
        "passive_voice": passive,
        "burstiness": burstiness,
        "para_symmetry": {**para_symmetry, "symmetrical_runs": symmetrical_runs},
        "nested_numbers": nested,
        "colon_lists": colon,
        "punctuation": punctuation,
        "risk_count": risk_count,
        "estimated_aigc_rate": estimated_rate,
        "overall_risk": overall_risk,
        "paragraph_findings": [asdict(item) for item in paragraph_findings],
    }


def find_synonym_cycling(paragraph: str) -> list[str]:
    hits: list[str] = []
    for group in SYNONYM_GROUPS:
        found = [term for term in group if term in paragraph]
        if len(found) >= 3:
            hits.append(" / ".join(sorted(found)))
    return hits


def classify_style_risk(score: int) -> str:
    if score >= 5:
        return "high"
    if score >= 3:
        return "medium"
    if score >= 1:
        return "low"
    return "clear"


def analyze_style(text: str) -> dict[str, object]:
    paragraphs = split_paragraphs(text)
    findings: list[StyleParagraphFinding] = []
    pattern_counts: dict[str, int] = {}

    for idx, paragraph in enumerate(paragraphs, 1):
        pattern_ids: list[str] = []
        pattern_labels: list[str] = []
        matched_examples: list[str] = []
        guidance: list[str] = []

        synonym_hits = find_synonym_cycling(paragraph)
        if synonym_hits:
            pattern_ids.append("synonym_cycling")
            pattern_labels.append("同义词轮换")
            matched_examples.extend(synonym_hits)
            guidance.append("核心术语全文统一，不要让同一对象在本段内出现 3 种以上称呼。")

        for pattern_id, label, regexes, rewrite_tip in AI_PATTERNS:
            if pattern_id == "synonym_cycling":
                continue
            if pattern_id == "emdash_overuse":
                count = paragraph.count("——")
                if count > 1:
                    pattern_ids.append(pattern_id)
                    pattern_labels.append(label)
                    matched_examples.append(f"破折号 {count} 处")
                    guidance.append(rewrite_tip)
                continue
            matches: list[str] = []
            for regex in regexes:
                matches.extend(re.findall(regex, paragraph))
            cleaned = []
            for match in matches:
                if isinstance(match, tuple):
                    cleaned.append("".join(str(item) for item in match if item))
                else:
                    cleaned.append(str(match))
            cleaned = [item for item in cleaned if item]
            cleaned = list(dict.fromkeys(item.strip() for item in cleaned if item.strip()))
            if cleaned:
                pattern_ids.append(pattern_id)
                pattern_labels.append(label)
                matched_examples.extend(cleaned[:3])
                guidance.append(rewrite_tip)

        cliche_terms = [term for term in CLICHE_TERMS if term in paragraph]
        score = len(pattern_ids) + max(0, len(cliche_terms) - 2)
        risk = classify_style_risk(score)

        for pattern_id in pattern_ids:
            pattern_counts[pattern_id] = pattern_counts.get(pattern_id, 0) + 1

        findings.append(
            StyleParagraphFinding(
                paragraph=idx,
                score=score,
                risk=risk,
                pattern_ids=pattern_ids,
                pattern_labels=pattern_labels,
                matched_examples=matched_examples[:5],
                cliche_terms=cliche_terms[:10],
                rewrite_guidance=list(dict.fromkeys(guidance))[:5],
                text_preview=paragraph[:140].replace("\n", " "),
                char_count=len(paragraph),
                text=paragraph,
            )
        )

    overall_risk = "high" if any(item.risk == "high" for item in findings) else "medium" if any(item.risk == "medium" for item in findings) else "low" if any(item.risk == "low" for item in findings) else "clear"
    risk_counts = {"clear": 0, "low": 0, "medium": 0, "high": 0}
    for item in findings:
        risk_counts[item.risk] += 1
    return {
        "summary": {
            "overall_risk": overall_risk,
            "paragraph_count": len(findings),
            "risk_counts": risk_counts,
            "pattern_counts": dict(sorted(pattern_counts.items())),
            "method_source": "xiaofenggan01/aigc-reduce",
        },
        "findings": [asdict(item) for item in findings],
    }


def dump_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
