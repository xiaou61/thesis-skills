#!/usr/bin/env python3
"""Embed Visio .vsdx figures into a DOCX as editable OLE objects using OfficeCLI.

The default layout is thesis-friendly:

1. find the figure caption paragraph
2. insert a centered Visio OLE object paragraph before the caption
3. remove the static PNG preview paragraph immediately before the OLE object,
   only when that paragraph actually contains a picture

This keeps the Word body as: editable Visio object, then figure caption.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


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


def get_result(officecli: Path, docx: Path, path: str) -> dict | None:
    payload = run_json([str(officecli), "get", str(docx), path, "--json"])
    data = payload.get("data") if isinstance(payload, dict) else {}
    results = data.get("results") if isinstance(data, dict) else []
    if isinstance(results, list) and results and isinstance(results[0], dict):
        return results[0]
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


def numeric_body_paragraph_index(path: str) -> int | None:
    match = re.fullmatch(r"/body/p\[(\d+)\]", path)
    return int(match.group(1)) if match else None


def parent_paragraph_from_child(path: str) -> str | None:
    match = re.search(r"(/body/p\[[^\]]+\])(?:/|$)", path)
    return match.group(1) if match else None


def has_picture_child(result: dict | None) -> bool:
    if not isinstance(result, dict):
        return False
    children = result.get("children") or []
    return any(isinstance(child, dict) and child.get("type") == "picture" for child in children)


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
) -> None:
    matches = query_paths(officecli, docx, f'paragraph:contains("{caption}")')
    if not matches:
        raise RuntimeError(f"caption paragraph not found in DOCX: {caption}")
    caption_path = matches[0]

    for ole_path in reversed(query_paths(officecli, docx, "ole")):
        parent = parent_paragraph_from_child(ole_path)
        if parent == caption_path:
            run([str(officecli), "remove", str(docx), ole_path])

    caption_index = numeric_body_paragraph_index(caption_path)
    preview_path = f"/body/p[{caption_index - 1}]" if caption_index and caption_index > 1 else None
    ole_paragraph = add_ole_before_caption(officecli, docx, caption_path, vsdx, preview, width, height, prog_id)

    if remove_preview and preview_path:
        previous = get_result(officecli, docx, preview_path)
        if has_picture_child(previous):
            run([str(officecli), "remove", str(docx), preview_path])
        else:
            print(json.dumps({
                "warning": "preview paragraph not removed because it does not contain a picture",
                "caption": caption,
                "expected_preview_path": preview_path,
                "inserted_ole_paragraph": ole_paragraph,
            }, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser(description="Embed Visio .vsdx figures into DOCX caption paragraphs as OLE objects.")
    parser.add_argument("docx", help="DOCX file to modify.")
    parser.add_argument("--figure-map", required=True, help="JSON list with caption, vsdx, preview, width, and height.")
    parser.add_argument("--officecli", help="Path to officecli executable. Defaults to PATH or .tools/officecli.")
    parser.add_argument("--prog-id", default="Visio.Drawing.15", help="Visio OLE ProgID.")
    parser.add_argument("--keep-static-previews", action="store_true", help="Keep existing PNG preview paragraphs in the DOCX.")
    args = parser.parse_args()

    docx = Path(args.docx).resolve()
    officecli = resolve_officecli(args.officecli)
    mappings = json.loads(Path(args.figure_map).read_text(encoding="utf-8"))
    if not isinstance(mappings, list):
        raise ValueError("figure map must be a JSON list")

    embedded = 0
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
        embed_one(officecli, docx, caption, vsdx, preview, width, height, args.prog_id, not args.keep_static_previews)
        embedded += 1

    # OfficeCLI may leave a resident document process alive for speed. Flush and
    # close it so independent ZIP/OpenXML validators read the updated DOCX from disk.
    subprocess.run([str(officecli), "save", str(docx)], check=False, capture_output=True, text=True, encoding="utf-8", errors="replace")
    subprocess.run([str(officecli), "close", str(docx)], check=False, capture_output=True, text=True, encoding="utf-8", errors="replace")

    print(json.dumps({"docx": str(docx), "embedded_visio_ole": embedded}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
