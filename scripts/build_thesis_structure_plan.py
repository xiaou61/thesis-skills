#!/usr/bin/env python3
"""Build a component-oriented thesis structure plan from profile and evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any


DEFAULT_COMPONENTS = [
    {"id": "cover", "required": False, "source": "template"},
    {"id": "zh_abstract", "required": True, "source": "generated"},
    {"id": "en_abstract", "required": True, "source": "generated"},
    {"id": "toc", "required": True, "source": "word-field"},
    {"id": "chapter_1", "required": True, "title": "绪论"},
    {"id": "chapter_2", "required": True, "title": "相关技术"},
    {"id": "chapter_3", "required": True, "title": "系统分析"},
    {"id": "chapter_4", "required": True, "title": "系统设计"},
    {"id": "chapter_5", "required": True, "title": "系统实现"},
    {"id": "chapter_6", "required": True, "title": "系统测试"},
    {"id": "references", "required": True, "source": "generated"},
    {"id": "acknowledgement", "required": False, "source": "template-or-generated"},
    {"id": "appendix", "required": False, "source": "evidence-dependent"},
]


def load_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml_like(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    try:
        import yaml  # type: ignore

        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def detect_template_components(profile: dict[str, Any]) -> list[str]:
    paragraph_usage = profile.get("paragraph_usage", {})
    sample_groups = [
        paragraph_usage.get("ordered_paragraph_samples", []),
        paragraph_usage.get("heading_candidates", []),
        paragraph_usage.get("style_format_samples", []),
    ]
    sample_texts: list[str] = []
    for samples in sample_groups:
        for item in samples:
            if isinstance(item, dict):
                sample_texts.append(str(item.get("text", "")))
    text = "\n".join(sample_texts)
    compact = re.sub(r"\s+", "", text)
    components: list[str] = []
    patterns = [
        ("cover", r"毕业论文|毕业设计|题\s*目|学生姓名|指导教师"),
        ("zh_abstract", r"摘要|中文摘要"),
        ("en_abstract", r"(^|\n)\s*(Abstract|ABSTRACT)\b"),
        ("toc", r"目录|目次"),
        ("references", r"参考文献|References"),
        ("acknowledgement", r"致谢|谢辞"),
        ("appendix", r"附录|Appendix"),
    ]
    for key, pattern in patterns:
        target = compact if key in {"zh_abstract", "toc", "references", "acknowledgement", "appendix"} else text
        if re.search(pattern, target, re.IGNORECASE):
            components.append(key)
    for index in range(1, 7):
        if f"第{index}章" in compact or "第" + "一二三四五六"[index - 1] + "章" in compact:
            components.append(f"chapter_{index}")
    return components


def build_plan(profile: dict[str, Any], spec: dict[str, Any], min_figures: int) -> dict[str, Any]:
    template_components = set(detect_template_components(profile))
    components = []
    for item in DEFAULT_COMPONENTS:
        component = dict(item)
        if component["id"] in template_components:
            component["template_detected"] = True
            component["required"] = True if component["id"] in {"zh_abstract", "en_abstract", "toc", "references"} else component["required"]
        else:
            component["template_detected"] = False
        components.append(component)

    figure_policy = {
        "minimum_total_figures": min_figures,
        "chapter_3": ["use_case", "business_flow", "requirement_decomposition"],
        "chapter_4": ["function_architecture", "system_architecture", "technical_architecture", "er_overview", "single_entity_er"],
        "chapter_5": ["implementation_flowcharts", "real_program_screenshots_or_needs_user_screenshot"],
        "chapter_6": ["test_tables", "real_test_reports_or_logs"],
    }

    return {
        "schema_version": "1.0",
        "source_profile": profile.get("source_docx"),
        "project_name": spec.get("project", {}).get("name") or spec.get("title") or "",
        "component_order": components,
        "chapter_policy": {
            "default_main_body": ["chapter_1", "chapter_2", "chapter_3", "chapter_4", "chapter_5", "chapter_6"],
            "standalone_chapter_7": "only_when_school_template_or_user_requires",
            "chapter_5": "implementation_with_real_program_screenshots_or_registered_gaps",
            "chapter_6": "testing_with_concise_summary_when_no_standalone_conclusion",
        },
        "figure_policy": figure_policy,
        "template_replication_required_checks": [
            "check_docx_component_order.py",
            "check_docx_style_profile.py",
            "check_docx_page_model.py",
            "check_docx_caption_numbering.py",
            "report_template_replication_diff.py",
        ],
    }


def dump_yaml(payload: dict[str, Any]) -> str:
    try:
        import yaml  # type: ignore

        return yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
    except Exception:
        return json.dumps(payload, ensure_ascii=False, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build thesis structure plan from template profile and spec.")
    parser.add_argument("--template-profile", help="template-profile.json from extract_docx_template_profile.py")
    parser.add_argument("--spec", help="thesis-ai-spec.yaml or JSON")
    parser.add_argument("--out", default="paper-context/template-extract/thesis-structure-plan.yaml")
    parser.add_argument("--min-figures", type=int, default=12)
    args = parser.parse_args()

    profile = load_json(Path(args.template_profile).resolve()) if args.template_profile else {}
    spec_path = Path(args.spec).resolve() if args.spec else None
    spec = load_yaml_like(spec_path)
    plan = build_plan(profile, spec, args.min_figures)
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(dump_yaml(plan), encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
