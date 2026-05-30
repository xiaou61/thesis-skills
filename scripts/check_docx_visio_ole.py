#!/usr/bin/env python3
"""Check whether a DOCX contains embedded Visio OLE objects."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET


NS = {
    "o": "urn:schemas-microsoft-com:office:office",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}


def check_docx(path: Path) -> dict:
    with ZipFile(path) as archive:
        document = ET.fromstring(archive.read("word/document.xml"))
        rels_xml = ET.fromstring(archive.read("word/_rels/document.xml.rels"))
        embeddings = [name for name in archive.namelist() if name.startswith("word/embeddings/")]
        media = [name for name in archive.namelist() if name.startswith("word/media/")]

    rel_targets = {
        str(rel.attrib.get("Id", "")): str(rel.attrib.get("Target", ""))
        for rel in rels_xml
        if rel.attrib.get("Id")
    }
    objects = []
    for obj in document.findall(".//o:OLEObject", NS):
        prog_id = obj.attrib.get("ProgID", "")
        rel_id = obj.attrib.get(f"{{{NS['r']}}}id", "")
        target = rel_targets.get(rel_id, "")
        objects.append({"progId": prog_id, "relId": rel_id, "target": target})

    visio = [item for item in objects if item["progId"].lower().startswith("visio.")]
    paragraphs = document.findall(".//w:body/w:p", NS)
    ole_before_caption = 0
    caption_after_ole = []
    for index, paragraph in enumerate(paragraphs[:-1]):
        has_visio = any(
            (obj.attrib.get("ProgID", "").lower().startswith("visio."))
            for obj in paragraph.findall(".//o:OLEObject", NS)
        )
        if not has_visio:
            continue
        next_text = "".join(text.text or "" for text in paragraphs[index + 1].findall(".//w:t", NS))
        if next_text.startswith("图"):
            ole_before_caption += 1
            caption_after_ole.append(next_text)
    return {
        "docx": str(path),
        "ole_objects": len(objects),
        "visio_ole_objects": len(visio),
        "visio_ole_before_caption": ole_before_caption,
        "embeddings": len(embeddings),
        "media_files": len(media),
        "objects": objects,
        "captions_after_ole": caption_after_ole,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check DOCX Visio OLE object count.")
    parser.add_argument("docx", help="DOCX to inspect.")
    parser.add_argument("--min-visio-ole", type=int, default=1, help="Minimum required Visio OLE object count.")
    parser.add_argument("--require-before-caption", action="store_true", help="Require every Visio OLE object to be immediately followed by a figure caption paragraph.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    args = parser.parse_args()

    report = check_docx(Path(args.docx).resolve())
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("# DOCX Visio OLE Check\n")
        print(f"- File: `{report['docx']}`")
        print(f"- OLE objects: `{report['ole_objects']}`")
        print(f"- Visio OLE objects: `{report['visio_ole_objects']}`")
        print(f"- Visio OLE before captions: `{report['visio_ole_before_caption']}`")
        print(f"- Embedded payloads: `{report['embeddings']}`")
        print(f"- Media files: `{report['media_files']}`")

    if report["visio_ole_objects"] < args.min_visio_ole:
        return 1
    if args.require_before_caption and report["visio_ole_before_caption"] < report["visio_ole_objects"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
