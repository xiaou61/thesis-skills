#!/usr/bin/env python3
"""Check whether a DOCX contains embedded Visio OLE objects."""

from __future__ import annotations

import argparse
import json
import posixpath
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

from docx_io import ensure_readable_docx


NS = {
    "o": "urn:schemas-microsoft-com:office:office",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}

PR_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def resolve_word_target(target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join("word", target))


def check_docx(path: Path) -> dict:
    docx = ensure_readable_docx(path)
    errors: list[str] = []
    with ZipFile(docx) as archive:
        names = set(archive.namelist())
        document = ET.fromstring(archive.read("word/document.xml"))
        rels_xml = ET.fromstring(archive.read("word/_rels/document.xml.rels"))
        embeddings = [name for name in archive.namelist() if name.startswith("word/embeddings/")]
        media = [name for name in archive.namelist() if name.startswith("word/media/")]

    rel_targets = {
        str(rel.attrib.get("Id", "")): str(rel.attrib.get("Target", ""))
        for rel in rels_xml.findall(f"{{{PR_NS}}}Relationship")
        if rel.attrib.get("Id")
    }
    rel_modes = {
        str(rel.attrib.get("Id", "")): str(rel.attrib.get("TargetMode", ""))
        for rel in rels_xml.findall(f"{{{PR_NS}}}Relationship")
        if rel.attrib.get("Id")
    }
    objects = []
    for obj in document.findall(".//o:OLEObject", NS):
        prog_id = obj.attrib.get("ProgID", "")
        rel_id = obj.attrib.get(f"{{{NS['r']}}}id", "")
        target = rel_targets.get(rel_id, "")
        resolved_target = resolve_word_target(target) if target else ""
        is_visio = prog_id.lower().startswith("visio.")
        if is_visio:
            if not rel_id:
                errors.append("Visio OLE object is missing r:id")
            elif rel_id not in rel_targets:
                errors.append(f"Visio OLE relationship {rel_id} is missing from document.xml.rels")
            elif rel_modes.get(rel_id, "").lower() == "external":
                errors.append(f"Visio OLE relationship {rel_id} points to an external target")
            elif resolved_target not in names:
                errors.append(f"Visio OLE relationship {rel_id} points to missing payload {resolved_target}")
            elif not resolved_target.startswith("word/embeddings/"):
                errors.append(f"Visio OLE relationship {rel_id} points outside word/embeddings: {resolved_target}")
        objects.append({"progId": prog_id, "relId": rel_id, "target": target, "resolvedTarget": resolved_target})

    visio = [item for item in objects if item["progId"].lower().startswith("visio.")]
    paragraphs = document.findall(".//w:body/w:p", NS)
    ole_before_caption = 0
    caption_after_ole = []
    missing_caption_after_ole = 0
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
        else:
            missing_caption_after_ole += 1
    return {
        "docx": str(docx),
        "ole_objects": len(objects),
        "visio_ole_objects": len(visio),
        "visio_ole_before_caption": ole_before_caption,
        "visio_ole_missing_caption_after": missing_caption_after_ole,
        "embeddings": len(embeddings),
        "media_files": len(media),
        "objects": objects,
        "captions_after_ole": caption_after_ole,
        "errors": errors,
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
        print(f"- Visio OLE missing following captions: `{report['visio_ole_missing_caption_after']}`")
        print(f"- Embedded payloads: `{report['embeddings']}`")
        print(f"- Media files: `{report['media_files']}`")
        if report["errors"]:
            print("\n## Errors\n")
            for item in report["errors"]:
                print(f"- {item}")

    if report["visio_ole_objects"] < args.min_visio_ole:
        return 1
    if args.require_before_caption and report["visio_ole_before_caption"] < report["visio_ole_objects"]:
        return 1
    if report["errors"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
