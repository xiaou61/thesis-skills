#!/usr/bin/env python3
"""Run the full local AIGC repair loop: detect -> analyze -> plan -> re-check work order."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import analyze_aigc_style
import build_aigc_revision_plan
import detect_aigc_rate
from aigc_reduce_core import analyze_style, overall_scan, read_text


def classify_first_round(style_item: dict[str, object], scan_item: dict[str, object]) -> bool:
    style_risk = str(style_item.get("risk", "clear"))
    scan_risk = str(scan_item.get("risk", "clear"))
    trigger_count = len(scan_item.get("triggered_metrics", []))
    return style_risk == "high" or scan_risk == "high" or (style_risk == "medium" and trigger_count >= 2)


def classify_second_round(style_item: dict[str, object], scan_item: dict[str, object]) -> bool:
    style_risk = str(style_item.get("risk", "clear"))
    scan_risk = str(scan_item.get("risk", "clear"))
    trigger_count = len(scan_item.get("triggered_metrics", []))
    return style_risk in {"high", "medium"} or scan_risk in {"high", "medium"} or trigger_count >= 2


def summarize_paragraph(style_item: dict[str, object], scan_item: dict[str, object]) -> str:
    labels = style_item.get("pattern_labels", [])
    triggers = scan_item.get("triggered_metrics", [])
    pieces: list[str] = []
    if labels:
        pieces.append("深层问题: " + "、".join(str(item) for item in labels[:3]))
    if triggers:
        pieces.append("扫描命中: " + "、".join(str(item) for item in triggers[:3]))
    if not pieces:
        pieces.append("问题不重，先不动。")
    return "；".join(pieces)


def write_loop_summary(payload: dict[str, object], path: Path) -> None:
    summary = payload["summary"]
    first_round = payload["first_round_targets"]
    second_round = payload["second_round_watchlist"]
    commands = payload["commands"]

    lines = [
        "# AIGC Repair Loop",
        "",
        "这是一份本地 AIGC 修复总控结果。它先跑检测，再跑风格分析，再给出逐段修改计划，最后把复查重点列出来。",
        "",
        "默认节奏：先修一轮 -> 本地检测一次 -> 再补一轮 -> 最后再顺全文。",
        "",
        "## 总览",
        "",
        f"- 输入文件: `{summary['source']}`",
        f"- 估计 AIGC 风险: `{summary['estimated_aigc_rate']}% / {summary['overall_scan_risk']}`",
        f"- 风格总风险: `{summary['overall_style_risk']}`",
        f"- 建议先改段落数: `{len(first_round)}`",
        f"- 复查时重点盯的段落数: `{len(second_round)}`",
        "",
        "## 第一步先跑出来的文件",
        "",
        f"- 检测报告: `{summary['detection_report']}`",
        f"- 风格报告: `{summary['style_report']}`",
        f"- 改写计划: `{summary['revision_plan']}`",
        f"- 逐段工作单: `{summary['final_pass_work_order']}`",
        f"- 总控摘要: `{path}`",
        "",
        "## 第一轮先改这些段",
        "",
    ]

    if first_round:
        for item in first_round:
            lines.extend(
                [
                    f"### P{item['paragraph']:03d}",
                    f"- 当前风险: style=`{item['style_risk']}` / scan=`{item['scan_risk']}`",
                    f"- 为什么先改: {item['why_first_round']}",
                    f"- 这段像 AI 的地方: {item['plain_reason']}",
                    f"- 预览: {item['preview']}",
                    "",
                ]
            )
    else:
        lines.extend(["- 没有特别重的段落，先按风格报告人工抽查。", ""])

    lines.extend(["## 第二轮复查时重点盯这些段", ""])
    if second_round:
        for item in second_round:
            lines.extend(
                [
                    f"- `P{item['paragraph']:03d}`: {item['plain_reason']}",
                ]
            )
    else:
        lines.append("- 没有明显复查重点。")

    lines.extend(
        [
            "",
            "## 怎么用",
            "",
            "1. 先按 `aigc-revision-plan.md` 和本文件，做第一轮逐段修改。",
            "2. 第一轮改完后，再跑一次同样的命令做本地复查。",
            "3. 只盯着复查后还高风险的段落补第二轮。",
            "4. 最后再把全文顺一遍，不要每段都像分开改的。",
            "",
            "## 可直接复跑的命令",
            "",
            "```powershell",
            commands["rerun"],
            "```",
            "",
            "## 提醒",
            "",
            "- 这个流程是本地启发式检查，不是学校官方 AIGC 平台分数。",
            "- 这份脚本不会直接帮你改正文，它负责把该跑的分析、计划、工作单一次性准备好。",
            "- 真要改正文时，先按这份清单改，再复跑本脚本做第二轮判断。",
            "",
        ]
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_payload(
    input_path: Path,
    workspace: Path,
    detection_report: Path,
    detection_json: Path,
    style_report: Path,
    style_json: Path,
    revision_plan: Path,
    revision_plan_json: Path,
    final_pass_work_order: Path,
) -> dict[str, object]:
    text = read_text(input_path)
    scan_payload = overall_scan(text)
    style_payload = analyze_style(text)
    plan_payload = build_aigc_revision_plan.build_plan(text)

    scan_by_para = {item["paragraph"]: item for item in scan_payload["paragraph_findings"]}
    style_by_para = {item["paragraph"]: item for item in style_payload["findings"]}

    first_round_targets = []
    second_round_watchlist = []
    for paragraph in sorted(style_by_para):
        style_item = style_by_para[paragraph]
        scan_item = scan_by_para.get(paragraph, {"risk": "clear", "triggered_metrics": []})
        plain_reason = summarize_paragraph(style_item, scan_item)

        if classify_first_round(style_item, scan_item):
            first_round_targets.append(
                {
                    "paragraph": paragraph,
                    "style_risk": style_item["risk"],
                    "scan_risk": scan_item["risk"],
                    "why_first_round": "高风险段优先，先把最重的问题压下去。",
                    "plain_reason": plain_reason,
                    "preview": style_item["text_preview"],
                }
            )

        if classify_second_round(style_item, scan_item):
            second_round_watchlist.append(
                {
                    "paragraph": paragraph,
                    "style_risk": style_item["risk"],
                    "scan_risk": scan_item["risk"],
                    "plain_reason": plain_reason,
                }
            )

    rerun = (
        "python thesis-standardizer\\scripts\\run_aigc_repair_loop.py "
        f"\"{input_path}\" --workspace \"{workspace}\""
    )

    return {
        "summary": {
            "source": str(input_path),
            "estimated_aigc_rate": scan_payload["estimated_aigc_rate"],
            "overall_scan_risk": scan_payload["overall_risk"],
            "overall_style_risk": style_payload["summary"]["overall_risk"],
            "detection_report": str(detection_report),
            "style_report": str(style_report),
            "revision_plan": str(revision_plan),
            "final_pass_work_order": str(final_pass_work_order),
        },
        "scan_payload": scan_payload,
        "style_payload": style_payload,
        "plan_payload": plan_payload,
        "first_round_targets": first_round_targets,
        "second_round_watchlist": second_round_watchlist,
        "commands": {"rerun": rerun},
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the local AIGC repair loop and generate all report/plan/work-order files in one go."
    )
    parser.add_argument("input", help="Draft text/markdown/html/docx file.")
    parser.add_argument("--workspace", default=".", help="Workspace root for paper-context outputs.")
    parser.add_argument(
        "--out",
        default="paper-context/aigc/aigc-repair-loop.md",
        help="Markdown summary path, relative to workspace unless absolute.",
    )
    parser.add_argument(
        "--json-out",
        default="paper-context/aigc/aigc-repair-loop.json",
        help="JSON summary path, relative to workspace unless absolute.",
    )
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    input_path = Path(args.input).resolve()
    summary_path = (workspace / args.out).resolve() if not Path(args.out).is_absolute() else Path(args.out).resolve()
    json_path = (workspace / args.json_out).resolve() if not Path(args.json_out).is_absolute() else Path(args.json_out).resolve()

    detection_report = workspace / "paper-context" / "aigc" / "aigc-detection-report.md"
    detection_json = workspace / "paper-context" / "aigc" / "aigc-detection-report.json"
    style_report = workspace / "paper-context" / "aigc" / "aigc-style-report.md"
    style_json = workspace / "paper-context" / "aigc" / "aigc-style-report.json"
    revision_plan = workspace / "paper-context" / "aigc" / "aigc-revision-plan.md"
    revision_plan_json = workspace / "paper-context" / "aigc" / "aigc-revision-plan.json"
    final_pass_work_order = workspace / "paper-context" / "aigc" / "aigc-final-paragraph-pass.md"

    text = read_text(input_path)
    scan_payload = overall_scan(text)
    style_payload = analyze_style(text)
    plan_payload = build_aigc_revision_plan.build_plan(text)

    detect_aigc_rate.write_markdown(scan_payload, detection_report)
    detection_json.parent.mkdir(parents=True, exist_ok=True)
    detection_json.write_text(json.dumps(scan_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    analyze_aigc_style.write_markdown(style_payload, style_report)
    style_json.parent.mkdir(parents=True, exist_ok=True)
    style_json.write_text(json.dumps(style_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    analyze_aigc_style.write_final_paragraph_pass(style_payload, final_pass_work_order)

    build_aigc_revision_plan.write_markdown(plan_payload, revision_plan)
    revision_plan_json.parent.mkdir(parents=True, exist_ok=True)
    revision_plan_json.write_text(json.dumps(plan_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    payload = build_payload(
        input_path=input_path,
        workspace=workspace,
        detection_report=detection_report,
        detection_json=detection_json,
        style_report=style_report,
        style_json=style_json,
        revision_plan=revision_plan,
        revision_plan_json=revision_plan_json,
        final_pass_work_order=final_pass_work_order,
    )
    write_loop_summary(payload, summary_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {detection_report}")
    print(f"Wrote {detection_json}")
    print(f"Wrote {style_report}")
    print(f"Wrote {style_json}")
    print(f"Wrote {revision_plan}")
    print(f"Wrote {revision_plan_json}")
    print(f"Wrote {final_pass_work_order}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
