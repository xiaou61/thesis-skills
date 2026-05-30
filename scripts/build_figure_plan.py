#!/usr/bin/env python3
"""Build a thesis figure plan with screenshot placeholders.

This script does not draw diagrams. It creates the planning contract that a
system-design thesis should satisfy before chapter drafting and figure export:

- structural Visio figures to generate
- ER overview and single-entity figures to generate
- Chapter 5 implementation screenshots that must be filled by real screenshots
- Chapter 6 test evidence screenshots only when real logs/reports exist
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        raise SystemExit(f"PyYAML is required: {exc}") from exc
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def dump_yaml(data: Any) -> str:
    import yaml  # type: ignore

    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)


def text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    result = str(value).strip()
    return result if result else default


def is_placeholder(value: Any) -> bool:
    raw = text(value).lower()
    if not raw:
        return True
    placeholder_values = {
        "not_applicable",
        "none",
        "null",
        "missing",
        "模块名称",
        "角色名称",
        "实体名称",
        "表名",
        "填写截图目录或 not_applicable",
        "填写测试材料路径或 not_applicable",
        "填写数据库结构材料路径或 not_applicable",
        "填写系统或项目名称",
        "填写论文题目",
    }
    return raw in placeholder_values or "填写" in raw


def slug(value: str, fallback: str) -> str:
    raw = re.sub(r"[^0-9a-zA-Z_-]+", "-", value.strip().lower()).strip("-")
    return raw or fallback


def as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def module_names(spec: dict[str, Any], limit: int) -> list[str]:
    modules = spec.get("functional_modules") or []
    result: list[str] = []
    for item in as_list(modules):
        if isinstance(item, dict):
            name = text(item.get("name"))
        else:
            name = text(item)
        if name and not is_placeholder(name):
            result.append(name)
        if len(result) >= limit:
            break
    return result


def database_entities(spec: dict[str, Any]) -> list[dict[str, Any]]:
    design = spec.get("database_design") or {}
    if not isinstance(design, dict):
        return []
    entities = design.get("entities") or []
    result: list[dict[str, Any]] = []
    for item in as_list(entities):
        if not isinstance(item, dict):
            continue
        name = text(item.get("name") or item.get("table"))
        fields = item.get("fields")
        if name and not is_placeholder(name) and isinstance(fields, list) and fields:
            result.append(item)
    return result


def figure(
    figure_id: str,
    title: str,
    chapter: int,
    figure_type: str,
    source_kind: str,
    source_file: str,
    export_file: str,
    status: str,
    evidence: list[str],
    purpose: str,
    risk_notes: str = "",
) -> dict[str, Any]:
    return {
        "id": figure_id,
        "title": title,
        "chapter": str(chapter),
        "type": figure_type,
        "purpose": purpose,
        "source_kind": source_kind,
        "source_file": source_file,
        "export_file": export_file,
        "evidence": evidence,
        "first_mentioned_in": f"第{chapter}章",
        "status": status,
        "risk_notes": risk_notes,
    }


def build_plan(spec: dict[str, Any], max_module_flows: int, max_screenshots: int) -> dict[str, Any]:
    impl = spec.get("implementation_sources") or {}
    if not isinstance(impl, dict):
        impl = {}

    screenshots_source = text(impl.get("screenshots"))
    screenshot_status = "planned" if screenshots_source and not is_placeholder(screenshots_source) else "needs_user_screenshot"
    screenshot_evidence = [screenshots_source] if screenshot_status == "planned" else ["pending_user_screenshot"]

    modules = module_names(spec, max(max_module_flows, max_screenshots))
    entities = database_entities(spec)
    project_name = text((spec.get("project") or {}).get("name") if isinstance(spec.get("project"), dict) else "", "系统")
    if is_placeholder(project_name):
        project_name = "系统"

    figures: list[dict[str, Any]] = []

    figures.append(
        figure(
            "图3-1",
            f"{project_name}用例图",
            3,
            "use_case",
            "visio",
            "paper-context/figures/figure-3-1-use-case.vsdx",
            "paper-context/figures/figure-3-1-use-case.png",
            "planned",
            ["functional_modules", "roles"],
            "说明系统角色与功能边界",
        )
    )
    figures.append(
        figure(
            "图3-2",
            f"{project_name}核心业务流程图",
            3,
            "flowchart",
            "visio",
            "paper-context/figures/figure-3-2-business-flow.vsdx",
            "paper-context/figures/figure-3-2-business-flow.png",
            "planned" if modules else "needs_evidence",
            ["functional_modules"],
            "说明核心业务处理顺序和分支",
            "" if modules else "缺少可抽取的功能模块或业务流程材料",
        )
    )
    figures.append(
        figure(
            "图3-3",
            f"{project_name}功能需求结构图",
            3,
            "function_architecture",
            "visio",
            "paper-context/figures/figure-3-3-requirement-structure.vsdx",
            "paper-context/figures/figure-3-3-requirement-structure.png",
            "planned" if modules else "needs_evidence",
            ["functional_modules"],
            "把需求分析中的功能分解可视化",
            "" if modules else "缺少功能模块清单",
        )
    )

    figures.append(
        figure(
            "图4-1",
            f"{project_name}功能结构图",
            4,
            "function_architecture",
            "visio",
            "paper-context/figures/figure-4-1-function-architecture.vsdx",
            "paper-context/figures/figure-4-1-function-architecture.png",
            "planned",
            ["functional_modules"],
            "说明系统模块和功能层级",
        )
    )
    figures.append(
        figure(
            "图4-2",
            f"{project_name}总体架构图",
            4,
            "architecture",
            "visio",
            "paper-context/figures/figure-4-2-system-architecture.vsdx",
            "paper-context/figures/figure-4-2-system-architecture.png",
            "planned",
            ["technology_stack", "implementation_sources"],
            "说明前端、后端、数据层和外部依赖关系",
        )
    )
    figures.append(
        figure(
            "图4-3",
            f"{project_name}技术部署结构图",
            4,
            "architecture",
            "visio",
            "paper-context/figures/figure-4-3-deployment-architecture.vsdx",
            "paper-context/figures/figure-4-3-deployment-architecture.png",
            "planned",
            ["technology_stack"],
            "说明运行环境、服务组件和部署边界",
        )
    )
    figures.append(
        figure(
            "图4-4",
            f"{project_name}总体E-R图",
            4,
            "er_diagram",
            "visio",
            "paper-context/figures/figure-4-4-er-overview.vsdx",
            "paper-context/figures/figure-4-4-er-overview.png",
            "planned" if entities else "needs_evidence",
            ["database_design.entities"],
            "说明核心实体或数据对象之间的关系",
            "" if entities else "缺少数据库实体或数据对象字段材料",
        )
    )

    next_ch4 = 5
    for entity in entities:
        name = text(entity.get("name") or entity.get("table"), f"实体{next_ch4}")
        stem = slug(name, f"entity-{next_ch4}")
        figures.append(
            figure(
                f"图4-{next_ch4}",
                f"{name}实体E-R图",
                4,
                "er_diagram",
                "visio",
                f"paper-context/figures/figure-4-{next_ch4}-{stem}.vsdx",
                f"paper-context/figures/figure-4-{next_ch4}-{stem}.png",
                "planned",
                [text(entity.get("evidence"), "database_design.entities")],
                "展示单个核心实体或数据对象的完整字段",
            )
        )
        next_ch4 += 1

    next_ch5 = 1
    for index, name in enumerate(modules[:max_module_flows], start=1):
        stem = slug(name, f"module-{index}")
        figures.append(
            figure(
                f"图5-{next_ch5}",
                f"{name}模块处理流程图",
                5,
                "flowchart",
                "visio",
                f"paper-context/figures/figure-5-{next_ch5}-{stem}-flow.vsdx",
                f"paper-context/figures/figure-5-{next_ch5}-{stem}-flow.png",
                "planned",
                [f"functional_modules[{index - 1}]"],
                "说明关键模块的处理步骤、判断分支和异常路径",
            )
        )
        next_ch5 += 1

    screenshot_titles = ["登录或入口界面实现截图", "系统首页实现截图"]
    screenshot_titles.extend(f"{name}功能实现截图" for name in modules[:max_screenshots])

    for index, title in enumerate(screenshot_titles, start=next_ch5):
        stem = slug(title, f"screenshot-{index}")
        figures.append(
            figure(
                f"图5-{index}",
                title,
                5,
                "ui_screenshot",
                "screenshot",
                screenshot_evidence[0],
                f"paper-context/screenshots/figure-5-{index}-{stem}.png",
                screenshot_status,
                screenshot_evidence,
                "支撑第五章系统实现和功能运行效果描述",
                "AI 不得伪造程序截图；无真实截图时保留占位并列入证据缺口" if screenshot_status == "needs_user_screenshot" else "",
            )
        )

    test_report_source = text(impl.get("test_reports"))
    if test_report_source and not is_placeholder(test_report_source):
        figures.append(
            figure(
                "图6-1",
                "测试结果或运行日志截图",
                6,
                "test_report",
                "screenshot",
                test_report_source,
                "paper-context/screenshots/figure-6-1-test-result-or-log.png",
                "planned",
                [test_report_source],
                "支撑第六章测试结果描述",
            )
        )

    return {
        "schema_version": "1.0",
        "policy": {
            "structural_diagrams_require_vsdx": True,
            "screenshots_must_be_real": True,
            "placeholder_status": "needs_user_screenshot",
        },
        "figures": figures,
    }


def build_markdown(plan: dict[str, Any]) -> str:
    lines = ["# Thesis Figure And Screenshot Plan", ""]
    lines.append("| ID | Title | Type | Source | Status |")
    lines.append("| --- | --- | --- | --- | --- |")
    for item in plan.get("figures", []):
        lines.append(
            f"| {item['id']} | {item['title']} | {item['type']} | {item['source_kind']} | {item['status']} |"
        )
    lines.extend(
        [
            "",
            "## Screenshot Rule",
            "",
            "Chapter 5 screenshots must come from a real running program, user-provided images, or browser automation. Chapter 6 may include real test logs/reports/screenshots only when such evidence exists. If no real evidence exists, keep screenshot items as `needs_user_screenshot` and do not generate synthetic UI screenshots.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a thesis figure and screenshot plan.")
    parser.add_argument(
        "spec",
        nargs="?",
        default="thesis-ai-standard/templates/thesis-ai-spec.yaml",
        help="Path to thesis-ai-spec.yaml.",
    )
    parser.add_argument("--out", default="paper-context/figure-plan", help="Output directory.")
    parser.add_argument("--max-module-flows", type=int, default=4, help="Maximum Chapter 4 module flowcharts.")
    parser.add_argument("--max-screenshots", type=int, default=4, help="Maximum module screenshots in Chapter 5.")
    args = parser.parse_args()

    spec_path = Path(args.spec).resolve()
    spec = load_yaml(spec_path)
    plan = build_plan(spec, max_module_flows=args.max_module_flows, max_screenshots=args.max_screenshots)

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "figure-plan.yaml").write_text(dump_yaml(plan), encoding="utf-8")
    (out_dir / "figure-registry-fragment.yaml").write_text(dump_yaml({"figures": plan["figures"]}), encoding="utf-8")
    (out_dir / "figure-plan.md").write_text(build_markdown(plan), encoding="utf-8")

    print(f"Wrote {out_dir / 'figure-plan.yaml'}")
    print(f"Wrote {out_dir / 'figure-registry-fragment.yaml'}")
    print(f"Wrote {out_dir / 'figure-plan.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
