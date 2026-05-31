#!/usr/bin/env python3
"""Embed Visio .vsdx figures into a DOCX as editable OLE objects using OfficeCLI.

The default layout is thesis-friendly:

1. find the figure caption paragraph from OOXML paragraph order
2. reuse an existing Visio OLE paragraph before the caption when present
3. otherwise insert a centered Visio OLE object paragraph before the caption
4. remove stale static PNG preview paragraphs and duplicate OLE paragraphs
   from the same figure block

This keeps the Word body as: editable Visio object, then figure caption.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import struct
from dataclasses import dataclass
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
class EmbedResult:
    caption: str
    width: str
    height: str
    inserted: bool
    reused: bool
    removed_preview_paragraphs: int


def run(args: list[str]) -> str:
    completed = subprocess.run(args, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return completed.stdout.strip()


def run_json(args: list[str]) -> dict:
    output = run(args)
    payload = json.loads(output)
    if not isinstance(payload, dict):
        raise RuntimeError(f"expected JSON object from command: {' '.join(args)}")
    return payload


def query_results(officecli: Path, docx: Path, selector: str) -> list[dict]:
    output = run([str(officecli), "query", str(docx), selector, "--json"])
    payload = json.loads(output)
    data = payload.get("data") if isinstance(payload, dict) else {}
    results = data.get("results") if isinstance(data, dict) else []
    return [item for item in results if isinstance(item, dict) and item.get("path")]


def query_paths(officecli: Path, docx: Path, selector: str) -> list[str]:
    return [str(item["path"]) for item in query_results(officecli, docx, selector)]


def paragraph_path_from_ooxml(index: int, paragraph: ET.Element) -> str:
    para_id = paragraph.attrib.get(f"{{{NS['w14']}}}paraId")
    if para_id:
        return f"/body/p[@paraId={para_id}]"
    return f"/body/p[{index}]"


def document_paragraphs(docx: Path) -> list[ParagraphInfo]:
    with ZipFile(docx) as archive:
        document = ET.fromstring(archive.read("word/document.xml"))
    body = document.find("w:body", NS)
    if body is None:
        return []

    paragraphs: list[ParagraphInfo] = []
    for index, paragraph in enumerate(body.findall("w:p", NS), 1):
        text = "".join(t.text or "" for t in paragraph.findall(".//w:t", NS))
        has_visio_ole = any(
            (ole.attrib.get("ProgID", "").lower().startswith("visio."))
            for ole in paragraph.findall(".//o:OLEObject", NS)
        )
        has_picture = (
            (paragraph.find(".//w:drawing", NS) is not None or paragraph.find(".//w:pict", NS) is not None)
            and not has_visio_ole
        )
        paragraphs.append(
            ParagraphInfo(
                index=index,
                path=paragraph_path_from_ooxml(index, paragraph),
                text=text,
                has_picture=has_picture,
                has_visio_ole=has_visio_ole,
            )
        )
    return paragraphs


def find_caption_paragraph(docx: Path, caption: str) -> ParagraphInfo | None:
    for paragraph in document_paragraphs(docx):
        if caption in paragraph.text:
            return paragraph
    return None


def nearby_figure_block_before_caption(docx: Path, caption: str, max_scan: int = 4) -> tuple[ParagraphInfo, list[ParagraphInfo]]:
    paragraphs = document_paragraphs(docx)
    caption_para = next((paragraph for paragraph in paragraphs if caption in paragraph.text), None)
    if caption_para is None:
        raise RuntimeError(f"caption paragraph not found in DOCX: {caption}")

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


def cleanup_duplicate_previews_before_caption(officecli: Path, docx: Path, caption: str) -> int:
    """Keep one Visio OLE paragraph before a figure caption and remove static leftovers."""
    _caption_para, candidates = nearby_figure_block_before_caption(docx, caption)
    if not candidates:
        return 0

    keep_ole_path: str | None = None
    for paragraph in reversed(candidates):
        if paragraph.has_visio_ole:
            keep_ole_path = paragraph.path
            break

    removals = [
        paragraph.path
        for paragraph in candidates
        if paragraph.has_picture or (paragraph.has_visio_ole and paragraph.path != keep_ole_path)
    ]
    for path in reversed(removals):
        run([str(officecli), "remove", str(docx), path])
    return len(removals)


def existing_ole_before_caption(docx: Path, caption: str) -> ParagraphInfo | None:
    _caption_para, candidates = nearby_figure_block_before_caption(docx, caption)
    for paragraph in reversed(candidates):
        if paragraph.has_visio_ole:
            return paragraph
    return None


def resolve_officecli(explicit: str | None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    candidates.extend([
        Path.cwd() / ".tools" / "officecli" / "officecli.exe",
        Path.cwd() / ".tools" / "officecli" / "officecli",
    ])
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return Path("officecli")


def parent_paragraph_from_child(path: str) -> str | None:
    match = re.search(r"(/body/p(?:\[[^\]]+\]|\[@paraId=[^\]]+\]))(?:/|$)", path)
    return match.group(1) if match else None


def parse_cm(value: str) -> float:
    text = value.strip().lower()
    if text.endswith("cm"):
        return float(text[:-2])
    if text.endswith("in"):
        return float(text[:-2]) * 2.54
    return float(text)


def format_cm(value: float) -> str:
    return f"{value:.2f}cm"


def png_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        with path.open("rb") as handle:
            header = handle.read(24)
    except OSError:
        return None
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        return None
    width, height = struct.unpack(">II", header[16:24])
    if width <= 0 or height <= 0:
        return None
    return width, height


def fit_size_from_preview(preview: Path, max_width: str, max_height: str) -> tuple[str, str]:
    dimensions = png_dimensions(preview)
    if not dimensions:
        return max_width, max_height
    width_px, height_px = dimensions
    max_w = parse_cm(max_width)
    max_h = parse_cm(max_height)
    ratio = width_px / height_px
    width = max_w
    height = width / ratio
    if height > max_h:
        height = max_h
        width = height * ratio
    return format_cm(width), format_cm(height)


def add_ole_before_caption(
    officecli: Path,
    docx: Path,
    caption_path: str,
    vsdx: Path,
    preview: Path,
    width: str,
    height: str,
    prog_id: str,
) -> str:
    output = run([
        str(officecli),
        "add",
        str(docx),
        "/body",
        "--type",
        "ole",
        "--before",
        caption_path,
        "--prop",
        f"src={vsdx}",
        "--prop",
        f"preview={preview}",
        "--prop",
        f"progId={prog_id}",
        "--prop",
        f"width={width}",
        "--prop",
        f"height={height}",
    ])
    paragraph = parent_paragraph_from_child(output)
    if not paragraph:
        matches = query_paths(officecli, docx, "ole")
        if not matches:
            raise RuntimeError("OfficeCLI reported success but no OLE object was found")
        paragraph = parent_paragraph_from_child(matches[-1])
    if not paragraph:
        raise RuntimeError(f"could not identify inserted OLE paragraph from OfficeCLI output: {output}")
    run([str(officecli), "set", str(docx), paragraph, "--prop", "align=center"])
    return paragraph


def embed_one(
    officecli: Path,
    docx: Path,
    caption: str,
    vsdx: Path,
    preview: Path,
    width: str,
    height: str,
    prog_id: str,
    remove_preview: bool,
) -> EmbedResult:
    caption_para = find_caption_paragraph(docx, caption)
    if caption_para is None:
        raise RuntimeError(f"caption paragraph not found in DOCX: {caption}")
    caption_path = caption_para.path

    existing_ole = existing_ole_before_caption(docx, caption)
    if existing_ole is not None:
        removed = 0
        if remove_preview:
            removed = cleanup_duplicate_previews_before_caption(officecli, docx, caption)
        existing_ole = existing_ole_before_caption(docx, caption)
        if existing_ole is not None:
            run([str(officecli), "set", str(docx), existing_ole.path, "--prop", "align=center"])
        return EmbedResult(caption, width, height, inserted=False, reused=True, removed_preview_paragraphs=removed)

    add_ole_before_caption(officecli, docx, caption_path, vsdx, preview, width, height, prog_id)

    removed = 0
    if remove_preview:
        removed = cleanup_duplicate_previews_before_caption(officecli, docx, caption)
        if removed == 0:
            print(json.dumps({
                "warning": "no static preview paragraph was removed near caption",
                "caption": caption,
            }, ensure_ascii=False))
    return EmbedResult(caption, width, height, inserted=True, reused=False, removed_preview_paragraphs=removed)


def main() -> int:
    parser = argparse.ArgumentParser(description="Embed Visio .vsdx figures into DOCX caption paragraphs as OLE objects.")
    parser.add_argument("docx", help="DOCX file to modify.")
    parser.add_argument("--figure-map", required=True, help="JSON list with caption, vsdx, preview, width, and height.")
    parser.add_argument("--officecli", help="Path to officecli executable. Defaults to PATH or .tools/officecli.")
    parser.add_argument("--prog-id", default="Visio.Drawing.15", help="Visio OLE ProgID.")
    parser.add_argument("--keep-static-previews", action="store_true", help="Keep existing PNG preview paragraphs in the DOCX.")
    parser.add_argument("--fit-preview-aspect", action="store_true", help="Compute OLE display width/height from preview PNG aspect ratio.")
    parser.add_argument("--max-width", default="14cm", help="Maximum fitted OLE width when --fit-preview-aspect is used.")
    parser.add_argument("--max-height", default="18cm", help="Maximum fitted OLE height when --fit-preview-aspect is used.")
    args = parser.parse_args()

    docx = Path(args.docx).resolve()
    officecli = resolve_officecli(args.officecli)
    mappings = json.loads(Path(args.figure_map).read_text(encoding="utf-8"))
    if not isinstance(mappings, list):
        raise ValueError("figure map must be a JSON list")

    results: list[EmbedResult] = []
    for item in mappings:
        if not isinstance(item, dict):
            raise ValueError("figure map items must be objects")
        caption = str(item["caption"])
        vsdx = Path(item["vsdx"]).resolve()
        preview = Path(item["preview"]).resolve()
        width = str(item.get("width", "14cm"))
        height = str(item.get("height", "8cm"))
        if not vsdx.exists():
            raise FileNotFoundError(vsdx)
        if not preview.exists():
            raise FileNotFoundError(preview)
        if args.fit_preview_aspect:
            width, height = fit_size_from_preview(preview, args.max_width, args.max_height)
        result = embed_one(officecli, docx, caption, vsdx, preview, width, height, args.prog_id, not args.keep_static_previews)
        results.append(result)

    # OfficeCLI may leave a resident document process alive for speed. Flush and
    # close it so independent ZIP/OpenXML validators read the updated DOCX from disk.
    subprocess.run([str(officecli), "save", str(docx)], check=False, capture_output=True, text=True, encoding="utf-8", errors="replace")
    subprocess.run([str(officecli), "close", str(docx)], check=False, capture_output=True, text=True, encoding="utf-8", errors="replace")

    inserted = sum(1 for item in results if item.inserted)
    reused = sum(1 for item in results if item.reused)
    removed = sum(item.removed_preview_paragraphs for item in results)
    print(json.dumps({
        "docx": str(docx),
        "processed_figures": len(results),
        "inserted_visio_ole": inserted,
        "reused_visio_ole": reused,
        "removed_static_preview_paragraphs": removed,
        "embedded_visio_ole": len(results),
        "items": [result.__dict__ for result in results],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
