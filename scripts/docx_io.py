#!/usr/bin/env python3
"""Shared DOCX input validation helpers for thesis-standardizer scripts."""

from __future__ import annotations

from pathlib import Path
import zipfile


def ensure_readable_docx(path: Path, label: str = "DOCX file") -> Path:
    resolved = path.resolve()
    if resolved.suffix.lower() != ".docx":
        raise ValueError(f"{label} must be a .docx file: {resolved}")
    if not resolved.exists():
        raise FileNotFoundError(f"{label} not found: {resolved}")
    if not zipfile.is_zipfile(resolved):
        raise ValueError(f"{label} is not a valid OOXML/ZIP package: {resolved}")

    try:
        with zipfile.ZipFile(resolved) as archive:
            names = set(archive.namelist())
    except zipfile.BadZipFile as exc:
        raise ValueError(f"{label} cannot be opened as a valid .docx package: {resolved}") from exc

    if "word/document.xml" not in names:
        raise ValueError(
            f"{label} is missing word/document.xml and does not look like a readable Word document: {resolved}"
        )
    return resolved
