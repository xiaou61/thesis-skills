#!/usr/bin/env python3
"""Append a traceable thesis revision record."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path


HEADER = """# Revision Log

Use this file for all thesis changes, including Word comments, AIGC detection/style edits, figure/table changes, standards fixes, and final-review edits.

Every material text change must be traceable:

1. where it changed
2. what changed
3. why it changed
4. what evidence or report justified it
5. which files were touched
6. whether any source/evidence gap remains

| ID | Date | Source | Location | Before | After | Change | Reason | Evidence | Files | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
"""


@dataclass
class RevisionRecord:
    id: str
    date: str
    timestamp: str
    source: str
    location: str
    before: str
    after: str
    change: str
    reason: str
    evidence: str
    files: list[str]
    status: str
    needs_source: str
    needs_evidence: str


def escape_cell(value: str) -> str:
    value = re.sub(r"\s+", " ", value.strip())
    value = value.replace("|", "\\|")
    return value or "-"


def next_revision_id(path: Path) -> str:
    if not path.exists():
        return "REV-001"
    text = path.read_text(encoding="utf-8", errors="ignore")
    numbers = [int(match) for match in re.findall(r"\bREV-(\d{3,})\b", text)]
    if not numbers:
        return "REV-001"
    return f"REV-{max(numbers) + 1:03d}"


def ensure_revision_log(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.stat().st_size == 0:
        path.write_text(HEADER, encoding="utf-8")


def append_markdown(path: Path, record: RevisionRecord) -> None:
    ensure_revision_log(path)
    row = [
        record.id,
        record.date,
        record.source,
        record.location,
        record.before,
        record.after,
        record.change,
        record.reason,
        record.evidence,
        ", ".join(record.files) if record.files else "-",
        record.status,
    ]
    with path.open("a", encoding="utf-8") as handle:
        handle.write("| " + " | ".join(escape_cell(item) for item in row) + " |\n")


def append_jsonl(path: Path, record: RevisionRecord) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")


def parse_files(raw: str) -> list[str]:
    return [item.strip() for item in re.split(r"[,;]", raw) if item.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Append a thesis revision trace record.")
    parser.add_argument("--workspace", default=".", help="Project workspace root.")
    parser.add_argument("--source", default="manual", help="Change source, e.g. AIGC style pass, Word comment, final review.")
    parser.add_argument("--location", required=True, help="Chapter, paragraph, section, file, figure, table, or comment ID.")
    parser.add_argument("--change", required=True, help="Short summary of the change.")
    parser.add_argument("--reason", required=True, help="Why the change was made.")
    parser.add_argument("--evidence", default="not specified", help="Evidence/report/citation/comment supporting the change.")
    parser.add_argument("--before", default="", help="Before summary or excerpt.")
    parser.add_argument("--after", default="", help="After summary or excerpt.")
    parser.add_argument("--files", default="", help="Comma-separated touched output files.")
    parser.add_argument("--status", default="done", help="done | needs_review | blocked | reverted")
    parser.add_argument("--needs-source", default="none", help="Remaining source gap.")
    parser.add_argument("--needs-evidence", default="none", help="Remaining evidence gap.")
    parser.add_argument("--log", help="Override markdown log path.")
    parser.add_argument("--jsonl", help="Override JSONL trace path.")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    log_path = Path(args.log).resolve() if args.log else workspace / "paper-context" / "workflow" / "revision-log.md"
    jsonl_path = Path(args.jsonl).resolve() if args.jsonl else workspace / "paper-context" / "workflow" / "revision-trace.jsonl"

    ensure_revision_log(log_path)
    record = RevisionRecord(
        id=next_revision_id(log_path),
        date=date.today().isoformat(),
        timestamp=datetime.now().isoformat(timespec="seconds"),
        source=args.source,
        location=args.location,
        before=args.before,
        after=args.after,
        change=args.change,
        reason=args.reason,
        evidence=args.evidence,
        files=parse_files(args.files),
        status=args.status,
        needs_source=args.needs_source,
        needs_evidence=args.needs_evidence,
    )

    append_markdown(log_path, record)
    append_jsonl(jsonl_path, record)
    print(f"Appended {record.id}")
    print(f"Wrote {log_path}")
    print(f"Wrote {jsonl_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
