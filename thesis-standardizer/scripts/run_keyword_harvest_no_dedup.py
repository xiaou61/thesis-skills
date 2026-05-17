#!/usr/bin/env python3
"""Harvest literature candidates from public scholarly APIs without deduplication."""

from __future__ import annotations

import argparse
import csv
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path


USER_AGENT = "thesis-standardizer/1.0 (+https://example.local)"


def http_get_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8", errors="ignore"))


def slugify(text: str) -> str:
    text = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff]+", "_", text.strip())
    text = text.strip("_")
    return text[:80] or "literature"


def safe_filename(text: str, ext: str) -> str:
    return f"{slugify(text)[:80]}.{ext}"


def detect_extension(content_type: str, url: str) -> str:
    lower_type = content_type.lower()
    lower_url = url.lower()
    if "pdf" in lower_type or lower_url.endswith(".pdf"):
        return "pdf"
    if "xml" in lower_type or lower_url.endswith(".xml"):
        return "xml"
    if "html" in lower_type or lower_url.endswith(".html") or lower_url.endswith(".htm"):
        return "html"
    return "bin"


def maybe_download(url: str, title: str, out_dir: Path) -> tuple[str, str]:
    if not url:
        return "not_attempted", ""
    try:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=45) as response:
            content = response.read()
            content_type = response.headers.get("Content-Type", "")
        ext = detect_extension(content_type, url)
        out_dir.mkdir(parents=True, exist_ok=True)
        file_path = out_dir / safe_filename(title or "download", ext)
        file_path.write_bytes(content)
        return "downloaded", str(file_path)
    except Exception:
        return "failed", ""


def query_openalex(query: str, year_start: int, year_end: int, per_page: int) -> list[dict[str, str]]:
    params = {
        "search": query,
        "per-page": str(per_page),
        "filter": f"from_publication_date:{year_start}-01-01,to_publication_date:{year_end}-12-31",
    }
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    payload = http_get_json(url)
    rows = []
    for item in payload.get("results", []):
        title = str(item.get("display_name") or "").strip()
        if not title:
            continue
        authors = ", ".join(
            author.get("author", {}).get("display_name", "")
            for author in item.get("authorships", [])[:6]
            if author.get("author", {}).get("display_name")
        )
        location = item.get("primary_location") or {}
        pdf_url = ""
        landing = str(location.get("landing_page_url") or "")
        source_name = ""
        if isinstance(location.get("source"), dict):
            source_name = str(location["source"].get("display_name") or "")
        open_access = item.get("open_access") or {}
        if isinstance(open_access, dict):
            pdf_url = str(open_access.get("oa_url") or "")
        rows.append(
            {
                "source": "openalex",
                "title": title,
                "authors": authors,
                "year": str(item.get("publication_year") or ""),
                "language": "en",
                "venue": source_name,
                "doi": str(item.get("doi") or ""),
                "landing_page": landing,
                "pdf_url": pdf_url,
            }
        )
    return rows


def query_crossref(query: str, year_start: int, year_end: int, rows_limit: int) -> list[dict[str, str]]:
    params = {
        "query.bibliographic": query,
        "rows": str(rows_limit),
        "filter": f"from-pub-date:{year_start},until-pub-date:{year_end}",
    }
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
    payload = http_get_json(url)
    rows = []
    for item in payload.get("message", {}).get("items", []):
        titles = item.get("title") or []
        title = str(titles[0] if titles else "").strip()
        if not title:
            continue
        authors = []
        for person in item.get("author", [])[:6]:
            family = str(person.get("family") or "").strip()
            given = str(person.get("given") or "").strip()
            full = " ".join(part for part in [given, family] if part)
            if full:
                authors.append(full)
        year = ""
        for key in ("published-print", "published-online", "issued"):
            parts = item.get(key, {}).get("date-parts", [])
            if parts and parts[0]:
                year = str(parts[0][0])
                break
        rows.append(
            {
                "source": "crossref",
                "title": title,
                "authors": ", ".join(authors),
                "year": year,
                "language": "en",
                "venue": str((item.get("container-title") or [""])[0]),
                "doi": str(item.get("DOI") or ""),
                "landing_page": str((item.get("link") or [{}])[0].get("URL") or item.get("URL") or ""),
                "pdf_url": "",
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "query",
        "source",
        "title",
        "authors",
        "year",
        "language",
        "venue",
        "doi",
        "landing_page",
        "pdf_url",
        "download_status",
        "local_file",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(path: Path, rows: list[dict[str, str]], errors: list[str]) -> None:
    lines = ["# Literature Harvest Summary", ""]
    lines.append(f"- Candidate rows: `{len(rows)}`")
    lines.append(f"- Error count: `{len(errors)}`")
    lines.append("")
    by_source: dict[str, int] = {}
    for row in rows:
        by_source[row["source"]] = by_source.get(row["source"], 0) + 1
    for source, count in sorted(by_source.items()):
        lines.append(f"- {source}: `{count}`")
    if errors:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {item}" for item in errors)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Harvest literature metadata without deduplication.")
    parser.add_argument("config", help="literature-harvest-config.json path.")
    parser.add_argument("--out", default="paper-context/literature/harvest-runs", help="Harvest runs directory.")
    parser.add_argument("--per-query", type=int, default=10, help="Rows per API query.")
    parser.add_argument("--skip-download", action="store_true", help="Skip downloading open URLs.")
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    thesis_title = str(config.get("thesis", {}).get("title") or "thesis_literature")
    policy = config.get("policy", {})
    year_start = int(policy.get("year_start", datetime.now().year - 5))
    year_end = int(policy.get("year_end", datetime.now().year))

    run_name = f"{slugify(thesis_title)[:24]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    out_root = Path(args.out).resolve()
    run_dir = out_root / run_name
    raw_dir = run_dir / "downloaded_raw"
    run_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    errors: list[str] = []
    queries = config.get("queries", {})
    for language, query_list in queries.items():
        if not isinstance(query_list, list):
            continue
        for query in query_list:
            clean_query = str(query).strip()
            if not clean_query:
                continue
            try:
                openalex_rows = query_openalex(clean_query, year_start, year_end, args.per_query)
                crossref_rows = query_crossref(clean_query, year_start, year_end, args.per_query)
            except urllib.error.URLError as exc:
                errors.append(f"{language}:{clean_query}: {exc}")
                continue
            for candidate in openalex_rows + crossref_rows:
                if language == "zh" and not re.search(r"[\u4e00-\u9fff]", candidate["title"]):
                    candidate["language"] = candidate.get("language") or "en"
                elif language == "zh":
                    candidate["language"] = "zh"
                else:
                    candidate["language"] = candidate.get("language") or "en"
                download_status = "not_attempted"
                local_file = ""
                if not args.skip_download:
                    download_url = candidate.get("pdf_url") or candidate.get("landing_page") or ""
                    download_status, local_file = maybe_download(download_url, candidate["title"], raw_dir)
                rows.append(
                    {
                        "query": clean_query,
                        "source": candidate["source"],
                        "title": candidate["title"],
                        "authors": candidate["authors"],
                        "year": candidate["year"],
                        "language": candidate["language"],
                        "venue": candidate["venue"],
                        "doi": candidate["doi"],
                        "landing_page": candidate["landing_page"],
                        "pdf_url": candidate["pdf_url"],
                        "download_status": download_status,
                        "local_file": local_file,
                    }
                )

    csv_path = run_dir / "keyword_research_candidate_table.csv"
    log_path = run_dir / "literature-harvest-log.json"
    md_path = run_dir / "harvest-summary.md"
    write_csv(csv_path, rows)
    write_summary(md_path, rows, errors)
    log_payload = {
        "schema_version": "1.0",
        "config": str(config_path),
        "run_dir": str(run_dir),
        "candidate_count": len(rows),
        "errors": errors,
    }
    log_path.write_text(json.dumps(log_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")
    print(f"Wrote {log_path}")
    return 0 if rows else 2


if __name__ == "__main__":
    raise SystemExit(main())
