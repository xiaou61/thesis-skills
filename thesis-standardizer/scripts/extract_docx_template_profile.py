#!/usr/bin/env python3
"""Extract a thesis template profile from a Word .docx file.

This script is intentionally read-only. It inspects OOXML parts directly so
section inheritance, header/footer references, and style definitions can be
captured without mutating the source document.
"""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PR_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"w": W_NS, "r": R_NS, "pr": PR_NS}


def w_tag(name: str) -> str:
    return f"{{{W_NS}}}{name}"


def r_tag(name: str) -> str:
    return f"{{{R_NS}}}{name}"


def parse_xml(blob: bytes) -> ET.Element:
    return ET.fromstring(blob)


def read_xml(archive: zipfile.ZipFile, name: str) -> ET.Element | None:
    try:
        return parse_xml(archive.read(name))
    except KeyError:
        return None


def twips_to_cm(raw: str | None) -> float | None:
    if not raw or not raw.isdigit():
        return None
    return round(int(raw) / 567.0, 2)


def half_points_to_pt(raw: str | None) -> float | None:
    if not raw or not raw.isdigit():
        return None
    return round(int(raw) / 2.0, 1)


def sanitize_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text


def iter_text(root: ET.Element) -> list[str]:
    texts: list[str] = []
    for node in root.iter():
        if node.tag == w_tag("t") and node.text:
            texts.append(node.text)
    return texts


@dataclass
class StyleSummary:
    style_id: str
    name: str
    style_type: str
    based_on: str | None
    font_ascii: str | None
    font_east_asia: str | None
    font_size_pt: float | None
    bold: bool
    italic: bool
    alignment: str | None
    spacing_before_pt: float | None
    spacing_after_pt: float | None
    line_spacing_pt: float | None
    line_spacing_rule: str | None
    left_indent_cm: float | None
    right_indent_cm: float | None
    first_line_indent_cm: float | None
    hanging_indent_cm: float | None


def extract_styles(styles_root: ET.Element | None) -> dict[str, Any]:
    if styles_root is None:
        return {"styles": [], "defaults": {}}

    styles: list[StyleSummary] = []
    for style in styles_root.findall("w:style", NS):
        style_id = style.get(w_tag("styleId")) or ""
        style_type = style.get(w_tag("type")) or ""
        name_node = style.find("w:name", NS)
        based_on_node = style.find("w:basedOn", NS)
        rpr = style.find("w:rPr", NS)
        fonts = rpr.find("w:rFonts", NS) if rpr is not None else None
        size = rpr.find("w:sz", NS) if rpr is not None else None
        styles.append(
            StyleSummary(
                style_id=style_id,
                name=(name_node.get(w_tag("val")) if name_node is not None else style_id),
                style_type=style_type,
                based_on=(based_on_node.get(w_tag("val")) if based_on_node is not None else None),
                font_ascii=(fonts.get(w_tag("ascii")) if fonts is not None else None),
                font_east_asia=(fonts.get(w_tag("eastAsia")) if fonts is not None else None),
                font_size_pt=half_points_to_pt(size.get(w_tag("val")) if size is not None else None),
                bold=bool_property(rpr.find("w:b", NS) if rpr is not None else None),
                italic=bool_property(rpr.find("w:i", NS) if rpr is not None else None),
                alignment=extract_alignment(style.find("w:pPr", NS)),
                spacing_before_pt=extract_spacing(style.find("w:pPr", NS)).get("before_pt"),
                spacing_after_pt=extract_spacing(style.find("w:pPr", NS)).get("after_pt"),
                line_spacing_pt=extract_spacing(style.find("w:pPr", NS)).get("line_pt"),
                line_spacing_rule=extract_spacing(style.find("w:pPr", NS)).get("line_rule"),
                left_indent_cm=extract_indent(style.find("w:pPr", NS)).get("left_cm"),
                right_indent_cm=extract_indent(style.find("w:pPr", NS)).get("right_cm"),
                first_line_indent_cm=extract_indent(style.find("w:pPr", NS)).get("first_line_cm"),
                hanging_indent_cm=extract_indent(style.find("w:pPr", NS)).get("hanging_cm"),
            )
        )

    doc_defaults = styles_root.find("w:docDefaults", NS)
    defaults: dict[str, Any] = {}
    if doc_defaults is not None:
        rpr_default = doc_defaults.find("w:rPrDefault/w:rPr", NS)
        if rpr_default is not None:
            fonts = rpr_default.find("w:rFonts", NS)
            size = rpr_default.find("w:sz", NS)
            defaults = {
                "font_ascii": fonts.get(w_tag("ascii")) if fonts is not None else None,
                "font_east_asia": fonts.get(w_tag("eastAsia")) if fonts is not None else None,
                "font_size_pt": half_points_to_pt(size.get(w_tag("val")) if size is not None else None),
            }

    return {
        "styles": [asdict(item) for item in styles],
        "defaults": defaults,
    }


def twips_to_pt(raw: str | None) -> float | None:
    if not raw:
        return None
    try:
        return round(int(raw) / 20.0, 1)
    except ValueError:
        return None


def extract_alignment(ppr: ET.Element | None) -> str | None:
    if ppr is None:
        return None
    node = ppr.find("w:jc", NS)
    return node.get(w_tag("val")) if node is not None else None


def extract_spacing(ppr: ET.Element | None) -> dict[str, Any]:
    if ppr is None:
        return {}
    spacing = ppr.find("w:spacing", NS)
    if spacing is None:
        return {}
    return {
        "before_pt": twips_to_pt(spacing.get(w_tag("before"))),
        "after_pt": twips_to_pt(spacing.get(w_tag("after"))),
        "line_pt": twips_to_pt(spacing.get(w_tag("line"))),
        "line_rule": spacing.get(w_tag("lineRule")),
    }


def extract_indent(ppr: ET.Element | None) -> dict[str, Any]:
    if ppr is None:
        return {}
    indent = ppr.find("w:ind", NS)
    if indent is None:
        return {}
    return {
        "left_cm": twips_to_cm(indent.get(w_tag("left"))),
        "right_cm": twips_to_cm(indent.get(w_tag("right"))),
        "first_line_cm": twips_to_cm(indent.get(w_tag("firstLine"))),
        "hanging_cm": twips_to_cm(indent.get(w_tag("hanging"))),
    }


def extract_run_style(rpr: ET.Element | None) -> dict[str, Any]:
    if rpr is None:
        return {}
    fonts = rpr.find("w:rFonts", NS)
    size = rpr.find("w:sz", NS)
    return {
        "font_ascii": fonts.get(w_tag("ascii")) if fonts is not None else None,
        "font_east_asia": fonts.get(w_tag("eastAsia")) if fonts is not None else None,
        "font_size_pt": half_points_to_pt(size.get(w_tag("val")) if size is not None else None),
        "bold": bool_property(rpr.find("w:b", NS)),
        "italic": bool_property(rpr.find("w:i", NS)),
    }


def extract_paragraph_properties(ppr: ET.Element | None) -> dict[str, Any]:
    spacing = extract_spacing(ppr)
    indent = extract_indent(ppr)
    return {
        "alignment": extract_alignment(ppr),
        "spacing_before_pt": spacing.get("before_pt"),
        "spacing_after_pt": spacing.get("after_pt"),
        "line_spacing_pt": spacing.get("line_pt"),
        "line_spacing_rule": spacing.get("line_rule"),
        "left_indent_cm": indent.get("left_cm"),
        "right_indent_cm": indent.get("right_cm"),
        "first_line_indent_cm": indent.get("first_line_cm"),
        "hanging_indent_cm": indent.get("hanging_cm"),
    }


def bool_property(node: ET.Element | None) -> bool:
    if node is None:
        return False
    raw = node.get(w_tag("val"))
    if raw is None:
        return True
    return raw.lower() not in {"0", "false", "off"}


def extract_sample_run_properties(paragraph: ET.Element) -> dict[str, Any]:
    for run in paragraph.findall("w:r", NS):
        texts = [node.text for node in run.findall("w:t", NS) if node.text]
        if not sanitize_text(" ".join(texts)):
            continue
        return extract_run_style(run.find("w:rPr", NS))
    return {}


def load_relationships(root: ET.Element | None) -> dict[str, str]:
    if root is None:
        return {}
    rels: dict[str, str] = {}
    for rel in root.findall(f"{{{PR_NS}}}Relationship"):
        rel_id = rel.get("Id")
        target = rel.get("Target")
        if rel_id and target:
            rels[rel_id] = target
    return rels


def extract_sections(document_root: ET.Element | None, rels: dict[str, str], archive: zipfile.ZipFile) -> list[dict[str, Any]]:
    if document_root is None:
        return []

    sections: list[dict[str, Any]] = []
    previous_header_refs: list[dict[str, str]] = []
    previous_footer_refs: list[dict[str, str]] = []

    for idx, sect_pr in enumerate(document_root.findall(".//w:sectPr", NS), 1):
        pg_sz = sect_pr.find("w:pgSz", NS)
        pg_mar = sect_pr.find("w:pgMar", NS)
        pg_num = sect_pr.find("w:pgNumType", NS)
        title_pg = sect_pr.find("w:titlePg", NS) is not None

        header_refs = []
        for ref in sect_pr.findall("w:headerReference", NS):
            rel_id = ref.get(r_tag("id"))
            if rel_id:
                header_refs.append(
                    {
                        "type": ref.get(w_tag("type")) or "default",
                        "target": rels.get(rel_id, ""),
                    }
                )
        footer_refs = []
        for ref in sect_pr.findall("w:footerReference", NS):
            rel_id = ref.get(r_tag("id"))
            if rel_id:
                footer_refs.append(
                    {
                        "type": ref.get(w_tag("type")) or "default",
                        "target": rels.get(rel_id, ""),
                    }
                )

        effective_headers = header_refs or previous_header_refs
        effective_footers = footer_refs or previous_footer_refs
        previous_header_refs = effective_headers
        previous_footer_refs = effective_footers

        headers = []
        for item in effective_headers:
            target = item["target"]
            if not target:
                continue
            part = read_xml(archive, f"word/{target}")
            texts = [sanitize_text(t) for t in iter_text(part)] if part is not None else []
            headers.append({"type": item["type"], "target": target, "text": [t for t in texts if t]})

        footers = []
        for item in effective_footers:
            target = item["target"]
            if not target:
                continue
            part = read_xml(archive, f"word/{target}")
            texts = [sanitize_text(t) for t in iter_text(part)] if part is not None else []
            footers.append({"type": item["type"], "target": target, "text": [t for t in texts if t]})

        sections.append(
            {
                "index": idx,
                "page": {
                    "width_cm": twips_to_cm(pg_sz.get(w_tag("w")) if pg_sz is not None else None),
                    "height_cm": twips_to_cm(pg_sz.get(w_tag("h")) if pg_sz is not None else None),
                    "orientation": (pg_sz.get(w_tag("orient")) if pg_sz is not None else None) or "portrait",
                },
                "margins_cm": {
                    "top": twips_to_cm(pg_mar.get(w_tag("top")) if pg_mar is not None else None),
                    "bottom": twips_to_cm(pg_mar.get(w_tag("bottom")) if pg_mar is not None else None),
                    "left": twips_to_cm(pg_mar.get(w_tag("left")) if pg_mar is not None else None),
                    "right": twips_to_cm(pg_mar.get(w_tag("right")) if pg_mar is not None else None),
                    "header": twips_to_cm(pg_mar.get(w_tag("header")) if pg_mar is not None else None),
                    "footer": twips_to_cm(pg_mar.get(w_tag("footer")) if pg_mar is not None else None),
                    "gutter": twips_to_cm(pg_mar.get(w_tag("gutter")) if pg_mar is not None else None),
                },
                "different_first_page": title_pg,
                "page_number": {
                    "start": int(pg_num.get(w_tag("start"))) if pg_num is not None and pg_num.get(w_tag("start"), "").isdigit() else None,
                    "format": pg_num.get(w_tag("fmt")) if pg_num is not None else None,
                    "chapter_style": pg_num.get(w_tag("chapStyle")) if pg_num is not None else None,
                    "chapter_separator": pg_num.get(w_tag("chapSep")) if pg_num is not None else None,
                },
                "headers": headers,
                "footers": footers,
            }
        )
    return sections


def extract_paragraph_usage(document_root: ET.Element | None, styles_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if document_root is None:
        return {
            "style_counts": [],
            "heading_candidates": [],
            "toc_detected": False,
            "style_format_samples": [],
            "ordered_paragraph_samples": [],
        }

    style_counter: Counter[str] = Counter()
    heading_samples: list[dict[str, str]] = []
    toc_detected = False
    style_samples: dict[str, dict[str, Any]] = {}
    ordered_samples: list[dict[str, Any]] = []

    body = document_root.find("w:body", NS)
    if body is None:
        return {
            "style_counts": [],
            "heading_candidates": [],
            "toc_detected": False,
            "style_format_samples": [],
            "ordered_paragraph_samples": [],
        }

    current_section_index = 1
    for child in list(body):
        paragraphs: list[ET.Element] = []
        if child.tag == w_tag("p"):
            paragraphs = [child]
        elif child.tag == w_tag("tbl"):
            paragraphs = child.findall(".//w:p", NS)
        else:
            continue

        for paragraph in paragraphs:
            style_id = ""
            ppr = paragraph.find("w:pPr", NS)
            p_style = paragraph.find("w:pPr/w:pStyle", NS)
            if p_style is not None:
                style_id = p_style.get(w_tag("val")) or ""

            texts = [sanitize_text(t) for t in iter_text(paragraph)]
            joined = sanitize_text(" ".join(texts))
            if not joined:
                continue
            if not style_id and "Normal" in styles_by_id:
                style_id = "Normal"
            if style_id:
                style_counter[style_id] += 1

            instr_text = "".join(node.text or "" for node in paragraph.findall(".//w:instrText", NS))
            if "TOC" in instr_text.upper():
                toc_detected = True

            style_name = styles_by_id.get(style_id, {}).get("name", style_id)
            ordered_samples.append(
                {
                    "section_index": current_section_index,
                    "style_id": style_id,
                    "style_name": style_name,
                    "text": joined[:120],
                }
            )
            if style_id and style_id not in style_samples:
                style_samples[style_id] = {
                    "style_id": style_id,
                    "style_name": style_name,
                    "text": joined[:120],
                    "paragraph_properties": extract_paragraph_properties(ppr),
                    "run_properties": extract_sample_run_properties(paragraph),
                }
            if style_name.lower().startswith("heading") or "标题" in style_name:
                heading_samples.append({"style_id": style_id, "style_name": style_name, "text": joined[:120]})

        if child.find("w:pPr/w:sectPr", NS) is not None:
            current_section_index += 1

    return {
        "style_counts": [
            {
                "style_id": style_id,
                "style_name": styles_by_id.get(style_id, {}).get("name", style_id),
                "count": count,
            }
            for style_id, count in style_counter.most_common()
        ],
        "heading_candidates": heading_samples[:30],
        "toc_detected": toc_detected,
        "style_format_samples": list(style_samples.values())[:50],
        "ordered_paragraph_samples": ordered_samples[:400],
    }


def build_profile(docx_path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(docx_path) as archive:
        document_root = read_xml(archive, "word/document.xml")
        styles_root = read_xml(archive, "word/styles.xml")
        rels_root = read_xml(archive, "word/_rels/document.xml.rels")

        style_payload = extract_styles(styles_root)
        styles_by_id = {
            item["style_id"]: item
            for item in style_payload["styles"]
            if item.get("style_id")
        }
        rels = load_relationships(rels_root)
        sections = extract_sections(document_root, rels, archive)
        paragraph_usage = extract_paragraph_usage(document_root, styles_by_id)

        return {
            "source_docx": str(docx_path),
            "sections": sections,
            "styles": style_payload["styles"],
            "style_defaults": style_payload["defaults"],
            "paragraph_usage": paragraph_usage,
        }


def render_markdown(profile: dict[str, Any]) -> str:
    lines = [
        "# DOCX Template Extraction Report",
        "",
        f"- Source: `{profile['source_docx']}`",
        f"- Section count: `{len(profile['sections'])}`",
        f"- Style count: `{len(profile['styles'])}`",
        f"- TOC detected: `{profile['paragraph_usage']['toc_detected']}`",
        "",
        "## Sections",
        "",
    ]

    for section in profile["sections"]:
        page = section["page"]
        lines.append(
            f"- Section {section['index']}: `{page['orientation']}` {page['width_cm']} x {page['height_cm']} cm, "
            f"margins(top/bottom/left/right)=`{section['margins_cm']['top']}`/`{section['margins_cm']['bottom']}`/"
            f"`{section['margins_cm']['left']}`/`{section['margins_cm']['right']}` cm"
        )
        if section["headers"]:
            header_preview = " | ".join(
                sanitize_text(" ".join(item["text"])) for item in section["headers"] if item["text"]
            )
            lines.append(f"  header: `{header_preview or '(empty)'}`")
        if section["footers"]:
            footer_preview = " | ".join(
                sanitize_text(' '.join(item['text'])) for item in section["footers"] if item["text"]
            )
            lines.append(f"  footer: `{footer_preview or '(empty)'}`")

    lines.extend(["", "## Paragraph Styles Used", ""])
    for item in profile["paragraph_usage"]["style_counts"][:20]:
        lines.append(f"- `{item['style_name']}` ({item['style_id']}): {item['count']}")

    lines.extend(["", "## Heading Samples", ""])
    for item in profile["paragraph_usage"]["heading_candidates"][:20]:
        lines.append(f"- `{item['style_name']}`: {item['text']}")

    lines.extend(["", "## Style Format Samples", ""])
    for item in profile["paragraph_usage"].get("style_format_samples", [])[:20]:
        p = item.get("paragraph_properties", {})
        r = item.get("run_properties", {})
        lines.append(
            f"- `{item['style_name']}`: align=`{p.get('alignment')}`, "
            f"before=`{p.get('spacing_before_pt')}`pt, after=`{p.get('spacing_after_pt')}`pt, "
            f"line=`{p.get('line_spacing_pt')}`pt/{p.get('line_spacing_rule')}, "
            f"firstLine=`{p.get('first_line_indent_cm')}`cm, "
            f"font=`{r.get('font_east_asia') or r.get('font_ascii')}`, size=`{r.get('font_size_pt')}`pt, "
            f"bold=`{r.get('bold')}`; sample=`{item.get('text')}`"
        )

    lines.extend(["", "## Style Defaults", ""])
    defaults = profile["style_defaults"]
    if defaults:
        lines.append(
            f"- ascii font: `{defaults.get('font_ascii')}`; eastAsia font: `{defaults.get('font_east_asia')}`; "
            f"size: `{defaults.get('font_size_pt')}` pt"
        )
    else:
        lines.append("- No document defaults found.")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract a structural profile from a Word thesis template.")
    parser.add_argument("docx", help="Path to the school thesis .docx template.")
    parser.add_argument("--out", default="paper-context/template-extract", help="Output directory.")
    args = parser.parse_args()

    docx_path = Path(args.docx).resolve()
    if docx_path.suffix.lower() != ".docx":
        raise ValueError("Input must be a .docx file.")
    if not docx_path.exists():
        raise FileNotFoundError(docx_path)

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    profile = build_profile(docx_path)
    json_path = out_dir / "template-profile.json"
    md_path = out_dir / "template-profile.md"
    json_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(profile), encoding="utf-8")

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
