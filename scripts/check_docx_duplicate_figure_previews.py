#!/usr/bin/env python3
"""Check for stale static PNG previews left next to Visio OLE figures in DOCX."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET


NS = {
    "o": "urn:schemas-microsoft-com:office:office",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
}


@dataclass(frozen=True)
class ParagraphInfo:
    index: int
    path: str
    text: str
    has_picture: bool
    has_visio_ole: bool


@dataclass(frozen=True)
class FigurePreviewFinding:
    caption: str
    status: str
    message: str
    caption_path: str
    picture_paragraphs: list[str]
    ole_paragraphs: list[str]


def paragraph_path(index: int, paragraph: ET.Element) -> str:
    para_id = paragraph.attrib.get(f"{{{NS['w14']}}}paraId")
    if para_id:
        return f"/body/p[@paraId={para_id}]"
    return f"/body/p[{index}]"


def paragraph_text(paragraph: ET.Element) -> str:
    return "".join(text.text or "" for text in paragraph.findall(".//w:t", NS))


def read_paragraphs(docx: Path) -> list[ParagraphInfo]:
    with ZipFile(docx) as archive:
        document = ET.fromstring(archive.read("word/document.xml"))
    body = document.find("w:body", NS)
    if body is None:
        return []

    paragraphs: list[ParagraphInfo] = []
    for index, paragraph in enumerate(body.findall("w:p", NS), 1):
        has_visio_ole = any(
            ole.attrib.get("ProgID", "").lower().startswith("visio.")
            for ole in paragraph.findall(".//o:OLEObject", NS)
        )
        has_picture = (
            (paragraph.find(".//w:drawing", NS) is not None or paragraph.find(".//w:pict", NS) is not None)
            and not has_visio_ole
        )
        paragraphs.append(
            ParagraphInfo(
                index=index,
                path=paragraph_path(index, paragraph),
                text=paragraph_text(paragraph),
                has_picture=has_picture,
                has_visio_ole=has_visio_ole,
            )
        )
    return paragraphs


def load_captions(figure_map: Path | None) -> list[str] | None:
    if figure_map is None:
        return None
    payload = json.loads(figure_map.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("figure map must be a JSON list")
    captions: list[str] = []
    for item in payload:
        if not isinstance(item, dict) or not item.get("caption"):
            raise ValueError("figure map items must contain caption")
        captions.append(str(item["caption"]))
    return captions


def caption_candidates(paragraphs: list[ParagraphInfo], captions: list[str] | None) -> list[str]:
    if captions is not None:
        return captions
    return [paragraph.text for paragraph in paragraphs if paragraph.text.startswith("图 ")]


def figure_block_before_caption(
    paragraphs: list[ParagraphInfo],
    caption: str,
    max_scan: int,
) -> tuple[ParagraphInfo | None, list[ParagraphInfo]]:
    caption_para = next((paragraph for paragraph in paragraphs if caption in paragraph.text), None)
    if caption_para is None:
        return None, []

    candidates: list[ParagraphInfo] = []
    cursor = caption_para.index - 2
    scanned = 0
    while cursor >= 0 and scanned < max_scan:
        paragraph = paragraphs[cursor]
        if paragraph.text.strip():
            break
        if paragraph.has_picture or paragraph.has_visio_ole:
            candidates.append(paragraph)
            cursor -= 1
            scanned += 1
            continue
        if candidates:
            break
        cursor -= 1
        scanned += 1
    candidates.reverse()
    return caption_para, candidates


def check_docx(docx: Path, captions: list[str] | None, max_scan: int) -> dict:
    paragraphs = read_paragraphs(docx)
    findings: list[FigurePreviewFinding] = []

    for caption in caption_candidates(paragraphs, captions):
        caption_para, block = figure_block_before_caption(paragraphs, caption, max_scan)
        if caption_para is None:
            findings.append(FigurePreviewFinding(caption, "error", "caption not found", "", [], []))
            continue

        picture_paths = [paragraph.path for paragraph in block if paragraph.has_picture]
        ole_paths = [paragraph.path for paragraph in block if paragraph.has_visio_ole]
        if len(ole_paths) == 0:
            findings.append(
                FigurePreviewFinding(caption, "error", "no Visio OLE paragraph before caption", caption_para.path, picture_paths, ole_paths)
            )
        elif len(ole_paths) > 1:
            findings.append(
                FigurePreviewFinding(caption, "error", "multiple Visio OLE paragraphs before caption", caption_para.path, picture_paths, ole_paths)
            )
        elif picture_paths:
            findings.append(
                FigurePreviewFinding(caption, "error", "static picture preview remains next to Visio OLE", caption_para.path, picture_paths, ole_paths)
            )
        else:
            findings.append(FigurePreviewFinding(caption, "ok", "single Visio OLE before caption", caption_para.path, [], ole_paths))

    errors = [finding for finding in findings if finding.status == "error"]
    return {
        "docx": str(docx),
        "checked_figures": len(findings),
        "errors": len(errors),
        "findings": [asdict(finding) for finding in findings],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check DOCX figure blocks for duplicate static previews around Visio OLE objects.")
    parser.add_argument("docx", help="DOCX file to inspect.")
    parser.add_argument("--figure-map", help="Optional Visio OLE figure map. When provided, only these captions are checked.")
    parser.add_argument("--max-scan", type=int, default=4, help="Maximum empty figure paragraphs to scan before each caption.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    args = parser.parse_args()

    docx = Path(args.docx).resolve()
    captions = load_captions(Path(args.figure_map).resolve() if args.figure_map else None)
    report = check_docx(docx, captions, args.max_scan)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("# DOCX Duplicate Figure Preview Check\n")
        print(f"- File: `{report['docx']}`")
        print(f"- Checked figures: `{report['checked_figures']}`")
        print(f"- Errors: `{report['errors']}`")
        for finding in report["findings"]:
            if finding["status"] == "error":
                print(f"- ERROR `{finding['caption']}`: {finding['message']}")

    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
