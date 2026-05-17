#!/usr/bin/env python3
"""Resume literature downloads and deduplicate downloaded files."""

from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
import urllib.request
from pathlib import Path


USER_AGENT = "thesis-standardizer/1.0 (+https://example.local)"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def detect_ext(content_type: str, url: str) -> str:
    lower_type = content_type.lower()
    lower_url = url.lower()
    if "pdf" in lower_type or lower_url.endswith(".pdf"):
        return ".pdf"
    if "xml" in lower_type or lower_url.endswith(".xml"):
        return ".xml"
    if "html" in lower_type or lower_url.endswith(".html") or lower_url.endswith(".htm"):
        return ".html"
    return ".bin"


def download(url: str, title: str, raw_dir: Path) -> tuple[str, str]:
    if not url:
        return "not_attempted", ""
    try:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=45) as response:
            content = response.read()
            content_type = response.headers.get("Content-Type", "")
        ext = detect_ext(content_type, url)
        file_name = "".join(char if char.isalnum() else "_" for char in title)[:80] or "download"
        raw_dir.mkdir(parents=True, exist_ok=True)
        file_path = raw_dir / f"{file_name}{ext}"
        file_path.write_bytes(content)
        return "downloaded", str(file_path)
    except Exception:
        return "failed", ""


def deduplicate(raw_dir: Path, dedup_dir: Path) -> tuple[int, int]:
    dedup_dir.mkdir(parents=True, exist_ok=True)
    seen: dict[str, Path] = {}
    copied = 0
    skipped = 0
    for file_path in sorted(raw_dir.rglob("*")):
        if not file_path.is_file():
            continue
        digest = hashlib.sha256(file_path.read_bytes()).hexdigest()
        if digest in seen:
            skipped += 1
            continue
        seen[digest] = file_path
        shutil.copy2(file_path, dedup_dir / file_path.name)
        copied += 1
    return copied, skipped


def write_report(path: Path, rows: list[dict[str, str]], copied: int, skipped: int) -> None:
    downloaded = sum(1 for row in rows if row.get("download_status") == "downloaded")
    failed = sum(1 for row in rows if row.get("download_status") == "failed")
    lines = [
        "# Download Resume Report",
        "",
        f"- Candidate rows: `{len(rows)}`",
        f"- Downloaded rows: `{downloaded}`",
        f"- Failed rows: `{failed}`",
        f"- Deduplicated files kept: `{copied}`",
        f"- Duplicate files skipped: `{skipped}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Resume literature downloads and deduplicate files.")
    parser.add_argument("run_dir", help="Harvest run directory.")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    csv_path = run_dir / "keyword_research_candidate_table.csv"
    raw_dir = run_dir / "downloaded_raw"
    dedup_dir = run_dir / "downloaded_pdfs_deduplicated"
    report_path = run_dir / "download-resume-report.md"

    rows = read_rows(csv_path)
    for row in rows:
        if row.get("download_status") == "downloaded" and row.get("local_file"):
            continue
        url = row.get("pdf_url") or row.get("landing_page") or ""
        status, local_file = download(url, row.get("title", "download"), raw_dir)
        row["download_status"] = status
        row["local_file"] = local_file

    copied, skipped = deduplicate(raw_dir, dedup_dir)
    write_rows(csv_path, rows)
    write_report(report_path, rows, copied, skipped)
    print(f"Wrote {csv_path}")
    print(f"Wrote {report_path}")
    print(f"Deduplicated files stored in {dedup_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
