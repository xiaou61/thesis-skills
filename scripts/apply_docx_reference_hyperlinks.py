#!/usr/bin/env python3
"""Add internal Word hyperlinks from numeric citations to reference entries.

This script edits only `word/document.xml` and preserves the original namespace
map. That matters for Word documents containing OLE objects: generic XML
serializers can drop compatibility namespace declarations and make Word report
that the file is damaged.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import shutil
import tempfile
import zipfile

from lxml import etree

from docx_io import ensure_readable_docx


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NS = {"w": W_NS}
W = f"{{{W_NS}}}"
XML_SPACE = f"{{{XML_NS}}}space"

REF_PREFIX_RE = re.compile(r"^\s*\[?([0-9]{1,3})\]?[\.、\s]")
SINGLE_CITATION_RE = re.compile(r"(?<!\d)\[([0-9]{1,3})\]")


def w_tag(name: str) -> str:
    return f"{{{W_NS}}}{name}"


def parse_document(blob: bytes) -> etree._Element:
    parser = etree.XMLParser(remove_blank_text=False, recover=False, huge_tree=True)
    return etree.fromstring(blob, parser)


def paragraph_text(paragraph: etree._Element) -> str:
    return "".join(paragraph.xpath(".//w:t/text()", namespaces=NS)).strip()


def is_references_heading(text: str) -> bool:
    compact = re.sub(r"\s+", "", text or "")
    return compact.startswith("参考文献") or compact.lower().startswith("references")


def body(root: etree._Element) -> etree._Element | None:
    result = root.xpath("./w:body", namespaces=NS)
    return result[0] if result else None


def iter_body_paragraphs(root: etree._Element) -> list[etree._Element]:
    body_node = body(root)
    if body_node is None:
        return []
    return [child for child in body_node if child.tag == W + "p"]


def find_references_paragraph_index(paragraphs: list[etree._Element]) -> int | None:
    for index, paragraph in enumerate(paragraphs):
        if is_references_heading(paragraph_text(paragraph)):
            return index
    return None


def reference_number(paragraph: etree._Element) -> int | None:
    match = REF_PREFIX_RE.match(paragraph_text(paragraph))
    return int(match.group(1)) if match else None


def next_bookmark_id(root: etree._Element) -> int:
    values: list[int] = []
    for node in root.xpath(".//w:bookmarkStart", namespaces=NS):
        raw = node.get(W + "id")
        if raw and raw.isdigit():
            values.append(int(raw))
    return (max(values) + 1) if values else 1


def remove_existing_reference_bookmarks(root: etree._Element) -> int:
    ids: set[str] = set()
    removed = 0
    for start in list(root.xpath(".//w:bookmarkStart", namespaces=NS)):
        name = start.get(W + "name") or ""
        if not re.fullmatch(r"ref_[0-9]{1,3}", name):
            continue
        bookmark_id = start.get(W + "id")
        if bookmark_id:
            ids.add(bookmark_id)
        parent = start.getparent()
        if parent is not None:
            parent.remove(start)
            removed += 1

    for end in list(root.xpath(".//w:bookmarkEnd", namespaces=NS)):
        if (end.get(W + "id") or "") not in ids:
            continue
        parent = end.getparent()
        if parent is not None:
            parent.remove(end)
            removed += 1
    return removed


def add_reference_bookmarks(root: etree._Element, reference_paragraphs: list[etree._Element]) -> dict[int, str]:
    bookmark_id = next_bookmark_id(root)
    anchors: dict[int, str] = {}
    for paragraph in reference_paragraphs:
        number = reference_number(paragraph)
        if number is None:
            continue
        anchor = f"ref_{number}"
        start = etree.Element(w_tag("bookmarkStart"), nsmap=paragraph.nsmap)
        start.set(W + "id", str(bookmark_id))
        start.set(W + "name", anchor)
        end = etree.Element(w_tag("bookmarkEnd"), nsmap=paragraph.nsmap)
        end.set(W + "id", str(bookmark_id))

        insert_at = 1 if len(paragraph) and paragraph[0].tag == W + "pPr" else 0
        paragraph.insert(insert_at, start)
        paragraph.append(end)
        anchors[number] = anchor
        bookmark_id += 1
    return anchors


def clear_run_text(run: etree._Element) -> etree._Element:
    clone = etree.Element(w_tag("r"), nsmap=run.nsmap)
    rpr = run.find("w:rPr", namespaces=NS)
    if rpr is not None:
        clone.append(etree.fromstring(etree.tostring(rpr)))
    return clone


def append_text(run: etree._Element, text: str) -> None:
    node = etree.SubElement(run, w_tag("t"))
    if text[:1].isspace() or text[-1:].isspace():
        node.set(XML_SPACE, "preserve")
    node.text = text


def make_text_run(text: str, source_run: etree._Element) -> etree._Element:
    run = clear_run_text(source_run)
    append_text(run, text)
    return run


def make_citation_hyperlink(number: int, nsmap: dict | None) -> etree._Element:
    hyperlink = etree.Element(w_tag("hyperlink"), nsmap=nsmap)
    hyperlink.set(W + "anchor", f"ref_{number}")
    hyperlink.set(W + "history", "1")

    run = etree.SubElement(hyperlink, w_tag("r"))
    rpr = etree.SubElement(run, w_tag("rPr"))
    style = etree.SubElement(rpr, w_tag("rStyle"))
    style.set(W + "val", "Hyperlink")
    append_text(run, f"[{number}]")
    return hyperlink


def replace_child(parent: etree._Element, child: etree._Element, replacements: list[etree._Element]) -> None:
    index = parent.index(child)
    parent.remove(child)
    for replacement in reversed(replacements):
        parent.insert(index, replacement)


def unwrap_reference_hyperlinks(paragraph: etree._Element) -> int:
    changed = 0
    for child in list(paragraph):
        if child.tag != W + "hyperlink":
            continue
        anchor = child.get(W + "anchor") or ""
        if not re.fullmatch(r"ref_[0-9]{1,3}", anchor):
            continue
        replace_child(paragraph, child, list(child))
        changed += 1
    return changed


def run_is_simple_text(run: etree._Element) -> bool:
    allowed = {W + "rPr", W + "t"}
    return all(child.tag in allowed for child in list(run)) and len(run.xpath("./w:t", namespaces=NS)) == 1


def link_citations_in_paragraph(paragraph: etree._Element) -> int:
    changed = unwrap_reference_hyperlinks(paragraph)
    for child in list(paragraph):
        if child.tag != W + "r" or not run_is_simple_text(child):
            continue
        text_nodes = child.xpath("./w:t", namespaces=NS)
        if not text_nodes or not text_nodes[0].text:
            continue
        text = text_nodes[0].text
        matches = list(SINGLE_CITATION_RE.finditer(text))
        if not matches:
            continue
        replacements: list[etree._Element] = []
        cursor = 0
        for match in matches:
            if match.start() > cursor:
                replacements.append(make_text_run(text[cursor:match.start()], child))
            replacements.append(make_citation_hyperlink(int(match.group(1)), paragraph.nsmap))
            cursor = match.end()
        if cursor < len(text):
            replacements.append(make_text_run(text[cursor:], child))
        replace_child(paragraph, child, replacements)
        changed += len(matches)
    return changed


def patch_document_xml(document_xml: bytes) -> tuple[bytes, dict[str, object]]:
    root = parse_document(document_xml)
    paragraphs = iter_body_paragraphs(root)
    ref_index = find_references_paragraph_index(paragraphs)
    if ref_index is None:
        raise ValueError("missing references heading; cannot create citation hyperlinks")

    body_paragraphs = paragraphs[:ref_index]
    reference_paragraphs = paragraphs[ref_index + 1 :]
    removed_bookmarks = remove_existing_reference_bookmarks(root)
    anchors = add_reference_bookmarks(root, reference_paragraphs)

    linked = 0
    for paragraph in body_paragraphs:
        linked += link_citations_in_paragraph(paragraph)

    xml = etree.tostring(root, encoding="UTF-8", xml_declaration=True, standalone=True)
    return xml, {
        "referenceBookmarks": len(anchors),
        "removedOldBookmarkNodes": removed_bookmarks,
        "linkedCitationRuns": linked,
        "anchors": anchors,
    }


def apply_docx_reference_hyperlinks(docx: Path, out: Path | None = None) -> dict[str, object]:
    source = ensure_readable_docx(docx)
    target = out.resolve() if out is not None else source
    if out is not None:
        target.parent.mkdir(parents=True, exist_ok=True)

    temp_path: Path | None = None
    with zipfile.ZipFile(source, "r") as archive:
        names = archive.namelist()
        document_xml = archive.read("word/document.xml")
        patched_xml, report = patch_document_xml(document_xml)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as handle:
            temp_path = Path(handle.name)

        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as output:
            for name in names:
                data = patched_xml if name == "word/document.xml" else archive.read(name)
                output.writestr(name, data)

    try:
        shutil.move(str(temp_path), str(target))
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()

    return {"docx": str(target), **report}


def main() -> int:
    parser = argparse.ArgumentParser(description="Add Word internal hyperlinks from numeric citations to reference entries.")
    parser.add_argument("docx", help="Input DOCX file.")
    parser.add_argument("--out", help="Optional output DOCX path. Defaults to modifying the input file in place.")
    args = parser.parse_args()

    import json

    report = apply_docx_reference_hyperlinks(Path(args.docx), Path(args.out) if args.out else None)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
