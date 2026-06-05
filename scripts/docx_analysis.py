#!/usr/bin/env python3
"""Shared OOXML analysis helpers for thesis DOCX checks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import zipfile
from xml.etree import ElementTree as ET

from docx_io import ensure_readable_docx


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
O_NS = "urn:schemas-microsoft-com:office:office"
PR_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"w": W_NS, "o": O_NS, "pr": PR_NS}
W = f"{{{W_NS}}}"


@dataclass(frozen=True)
class DocxBlock:
    index: int
    kind: str
    text: str
    style_id: str
    has_drawing: bool
    has_visio_ole: bool
    has_toc_field: bool
    element: ET.Element


def read_xml(archive: zipfile.ZipFile, name: str) -> ET.Element | None:
    try:
        return ET.fromstring(archive.read(name))
    except KeyError:
        return None


def read_document(path: Path) -> ET.Element:
    docx = ensure_readable_docx(path)
    with zipfile.ZipFile(docx) as archive:
        return ET.fromstring(archive.read("word/document.xml"))


def load_style_names(path: Path) -> dict[str, str]:
    docx = ensure_readable_docx(path)
    with zipfile.ZipFile(docx) as archive:
        root = read_xml(archive, "word/styles.xml")
    if root is None:
        return {}
    styles: dict[str, str] = {}
    for style in root.findall("w:style", NS):
        style_id = style.get(W + "styleId") or ""
        name_node = style.find("w:name", NS)
        style_name = name_node.get(W + "val") if name_node is not None else ""
        if style_id:
            styles[style_id] = style_name or style_id
    return styles


def paragraph_text(paragraph: ET.Element) -> str:
    return "".join(node.text or "" for node in paragraph.findall(".//w:t", NS)).strip()


def element_text(element: ET.Element) -> str:
    text = "".join(node.text or "" for node in element.findall(".//w:t", NS))
    return re.sub(r"\s+", " ", text).strip()


def paragraph_style_id(paragraph: ET.Element) -> str:
    node = paragraph.find("w:pPr/w:pStyle", NS)
    return node.get(W + "val", "") if node is not None else ""


def element_has_visio_ole(element: ET.Element) -> bool:
    return any(
        (ole.attrib.get("ProgID") or "").lower().startswith("visio.")
        for ole in element.findall(".//o:OLEObject", NS)
    )


def element_has_drawing(element: ET.Element) -> bool:
    return element.find(".//w:drawing", NS) is not None or element.find(".//w:pict", NS) is not None


def element_has_toc_field(element: ET.Element) -> bool:
    instr_text = "".join(node.text or "" for node in element.findall(".//w:instrText", NS))
    return "TOC" in instr_text.upper()


def iter_body_blocks(document_root: ET.Element) -> list[DocxBlock]:
    body = document_root.find("w:body", NS)
    if body is None:
        return []

    blocks: list[DocxBlock] = []
    for child in list(body):
        if child.tag == W + "p":
            text = paragraph_text(child)
            style = paragraph_style_id(child)
            kind = "paragraph"
        elif child.tag == W + "tbl":
            text = element_text(child)
            style = ""
            kind = "table"
        else:
            continue
        blocks.append(
            DocxBlock(
                index=len(blocks) + 1,
                kind=kind,
                text=text,
                style_id=style,
                has_drawing=element_has_drawing(child),
                has_visio_ole=element_has_visio_ole(child),
                has_toc_field=element_has_toc_field(child),
                element=child,
            )
        )
    return blocks


def load_blocks(path: Path) -> list[DocxBlock]:
    return iter_body_blocks(read_document(path))


def compact_text(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def is_zh_abstract_heading(text: str) -> bool:
    raw = compact_text(text)
    return raw in {"摘要", "中文摘要"} or raw.startswith("摘要：") or raw.startswith("摘要:")


def is_en_abstract_heading(text: str) -> bool:
    raw = text.strip()
    return bool(re.match(r"^(Abstract|ABSTRACT)\b", raw))


def is_toc_heading(text: str) -> bool:
    return compact_text(text) in {"目录", "目次", "Contents", "CONTENT"}


def is_references_heading(text: str) -> bool:
    raw = compact_text(text)
    return raw.startswith("参考文献") or raw.lower().startswith("references")


def is_acknowledgement_heading(text: str) -> bool:
    raw = compact_text(text)
    return raw in {"致谢", "谢辞", "致謝", "Acknowledgements", "Acknowledgments"}


def is_appendix_heading(text: str) -> bool:
    raw = compact_text(text)
    return raw.startswith("附录") or raw.lower().startswith("appendix")


def chapter_number(text: str) -> str | None:
    raw = text.strip()
    match = re.match(r"^第([一二三四五六七八九十0-9]+)章\b", raw)
    if not match:
        match = re.match(r"^([1-9])[\s\u3000]+", raw)
    if not match:
        return None
    value = match.group(1)
    mapping = {
        "一": "1",
        "二": "2",
        "三": "3",
        "四": "4",
        "五": "5",
        "六": "6",
        "七": "7",
        "八": "8",
        "九": "9",
        "十": "10",
    }
    return mapping.get(value, value)


def component_positions(blocks: list[DocxBlock]) -> dict[str, int]:
    positions: dict[str, int] = {}
    for block in blocks:
        text = block.text
        if "zh_abstract" not in positions and is_zh_abstract_heading(text):
            positions["zh_abstract"] = block.index
        if "en_abstract" not in positions and is_en_abstract_heading(text):
            positions["en_abstract"] = block.index
        if "toc" not in positions and (block.has_toc_field or is_toc_heading(text)):
            positions["toc"] = block.index
        if "references" not in positions and is_references_heading(text):
            positions["references"] = block.index
        if "acknowledgement" not in positions and is_acknowledgement_heading(text):
            positions["acknowledgement"] = block.index
        if "appendix" not in positions and is_appendix_heading(text):
            positions["appendix"] = block.index
        chapter = chapter_number(text)
        if chapter is not None:
            positions.setdefault(f"chapter_{chapter}", block.index)
    return positions


CAPTION_RE = re.compile(r"^(图|表)\s*([0-9一二三四五六七八九十]+[-.][0-9]+)")
CONTINUED_TABLE_RE = re.compile(r"^(续表|表)\s*([0-9一二三四五六七八九十]+[-.][0-9]+)")


def caption_id(text: str) -> tuple[str, str] | None:
    raw = text.strip()
    match = CAPTION_RE.match(raw)
    if match:
        return match.group(1), match.group(2).replace(".", "-")
    match = CONTINUED_TABLE_RE.match(raw)
    if match and match.group(1) == "续表":
        return "续表", match.group(2).replace(".", "-")
    return None


def caption_reference_patterns(kind: str, number: str) -> list[re.Pattern[str]]:
    escaped_dash = re.escape(number)
    dotted = re.escape(number.replace("-", "."))
    if kind == "续表":
        kind = "表"
    return [
        re.compile(rf"{kind}\s*{escaped_dash}"),
        re.compile(rf"{kind}\s*{dotted}"),
    ]


def split_before_references(blocks: list[DocxBlock]) -> tuple[list[DocxBlock], list[DocxBlock]]:
    positions = component_positions(blocks)
    ref_index = positions.get("references")
    if ref_index is None:
        return blocks, []
    before = [block for block in blocks if block.index < ref_index]
    refs = [block for block in blocks if block.index > ref_index]
    return before, refs
