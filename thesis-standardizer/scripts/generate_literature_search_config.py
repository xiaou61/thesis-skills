#!/usr/bin/env python3
"""Generate a first-pass literature search configuration."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path


STOPWORDS = {
    "的",
    "与",
    "和",
    "及",
    "研究",
    "设计",
    "实现",
    "系统",
    "analysis",
    "design",
    "implementation",
    "system",
    "based",
}


def load_yaml_if_available(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        import yaml  # type: ignore
    except Exception:
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def tokenize_keywords(text: str) -> list[str]:
    items = re.findall(r"[A-Za-z][A-Za-z0-9+\-]{2,}|[\u4e00-\u9fff]{2,}", text)
    results: list[str] = []
    for item in items:
        token = item.strip()
        if not token or token.lower() in STOPWORDS or token in STOPWORDS:
            continue
        if token not in results:
            results.append(token)
    return results[:12]


def guess_queries(title: str, abstract: str, keywords: list[str]) -> dict[str, list[str]]:
    zh_terms = [item for item in keywords if re.search(r"[\u4e00-\u9fff]", item)]
    en_terms = [item for item in keywords if re.search(r"[A-Za-z]", item)]
    seed = " ".join(part for part in [title, abstract] if part)
    inferred = tokenize_keywords(seed)

    for token in inferred:
        if re.search(r"[\u4e00-\u9fff]", token) and token not in zh_terms:
            zh_terms.append(token)
        if re.search(r"[A-Za-z]", token) and token not in en_terms:
            en_terms.append(token)

    zh_queries = []
    if title:
        zh_queries.append(title)
    if len(zh_terms) >= 2:
        zh_queries.append(" ".join(zh_terms[:4]))
    zh_queries.extend(term for term in zh_terms[:6] if term not in zh_queries)

    en_queries = []
    if en_terms:
        en_queries.append(" ".join(en_terms[:4]))
        en_queries.extend(term for term in en_terms[:6] if term not in en_queries)

    return {
        "zh": zh_queries[:6],
        "en": en_queries[:6],
    }


def extract_from_spec(spec_path: Path) -> tuple[str, str, list[str]]:
    payload = load_yaml_if_available(spec_path)
    paper = payload.get("paper") if isinstance(payload, dict) else {}
    abstract = payload.get("abstract") if isinstance(payload, dict) else {}
    title = ""
    if isinstance(paper, dict):
        title = str(paper.get("title", "")).strip()
    abstract_text = ""
    if isinstance(abstract, dict):
        abstract_text = str(abstract.get("draft", "")).strip()
    keywords = payload.get("keywords") if isinstance(payload, dict) else []
    if not isinstance(keywords, list):
        keywords = []
    clean_keywords = [str(item).strip() for item in keywords if str(item).strip()]
    return title, abstract_text, clean_keywords


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a literature search config from thesis materials.")
    parser.add_argument("workspace", nargs="?", default=".", help="Project workspace root.")
    parser.add_argument("--spec", help="Optional thesis-ai-spec.yaml path.")
    parser.add_argument("--title", help="Override thesis title.")
    parser.add_argument("--abstract", help="Override abstract text.")
    parser.add_argument("--keywords", help="Comma-separated keyword override.")
    parser.add_argument("--year-start", type=int, help="Override start year.")
    parser.add_argument("--year-end", type=int, help="Override end year.")
    parser.add_argument("--cn-count", default="12-15", help="Target Chinese literature count.")
    parser.add_argument("--en-count", default="3-5", help="Target English literature count.")
    parser.add_argument(
        "--out",
        default="paper-context/literature/literature-harvest-config.json",
        help="Output JSON path.",
    )
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    spec_path = Path(args.spec).resolve() if args.spec else workspace / "thesis-ai-standard" / "templates" / "thesis-ai-spec.yaml"
    spec_title, spec_abstract, spec_keywords = extract_from_spec(spec_path)

    title = (args.title or spec_title or workspace.name).strip()
    abstract = (args.abstract or spec_abstract).strip()
    override_keywords = []
    if args.keywords:
        override_keywords = [item.strip() for item in re.split(r"[,;，；]", args.keywords) if item.strip()]
    keywords = override_keywords or spec_keywords or tokenize_keywords(f"{title} {abstract}")

    current_year = date.today().year
    year_start = args.year_start or (current_year - 5)
    year_end = args.year_end or current_year
    queries = guess_queries(title, abstract, keywords)

    payload = {
        "schema_version": "1.0",
        "generated_at": date.today().isoformat(),
        "workspace": str(workspace),
        "thesis": {
            "title": title,
            "abstract": abstract,
            "keywords": keywords,
        },
        "policy": {
            "default_recent_year_rule": "recent_6_years_including_current_year",
            "year_start": year_start,
            "year_end": year_end,
            "target_counts": {
                "zh": args.cn_count,
                "en": args.en_count,
            },
            "user_requirements_override_defaults": True,
        },
        "queries": queries,
        "sources": {
            "spec_path": str(spec_path),
        },
    }

    out_path = Path(args.out).resolve() if Path(args.out).is_absolute() else workspace / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"Title: {title}")
    print(f"Keywords: {', '.join(keywords[:8]) if keywords else 'none'}")
    print(f"Year range: {year_start}-{year_end}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
