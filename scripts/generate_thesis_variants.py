#!/usr/bin/env python3
"""Prepare or run three thesis-generation variants with isolated workspaces."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_ROOT = ROOT / "paper-context" / "thesis-variants"
DEFAULT_GENERATOR = ROOT / "scripts" / "generate_campus_affairs_demo.py"
DEFAULT_CHECKER = ROOT / "scripts" / "check_final_thesis_docx.ps1"
DOCX_SUFFIX = "_论文草稿.docx"


@dataclass(frozen=True)
class Variant:
    id: str
    name: str
    focus: str
    workspace: str
    generation_notes: list[str]
    gate_profile: str
    expected_outputs: list[str]


VARIANTS = [
    Variant(
        id="template_first",
        name="模板优先版",
        focus="优先复现学校模板、组件顺序、标题层级、页边距、题注和三线表格式。",
        workspace="01-template-first",
        generation_notes=[
            "先提取 template-profile.json，并生成 thesis-structure-plan.yaml。",
            "正文扩写服从模板组件顺序；格式修复优先级高于新增图表。",
            "gate 必须启用 TemplateProfile 参数；读取 template-replication-diff.md 后再判断可交付性。",
        ],
        gate_profile="template",
        expected_outputs=[
            "final docx",
            "optional pdf export",
            "template-replication-diff.md",
            "gate-report.txt",
            "variant-manifest.json",
        ],
    ),
    Variant(
        id="figure_enhanced",
        name="图表增强版",
        focus="强化第3-6章图表计划、Visio 源文件、OLE 嵌入和图表闭环。",
        workspace="02-figure-enhanced",
        generation_notes=[
            "先运行 build_figure_plan.py，并把图表计划合入 figure-registry.yaml。",
            "第3章补用例图、业务流程图、需求结构图；第4章补架构图、功能图、E-R 图和三线表。",
            "gate 必须检查 FigureMap、ExpectedVisioOle、重复预览和预览宽高比。",
        ],
        gate_profile="figure",
        expected_outputs=[
            "final docx",
            "optional pdf export",
            "figures/*.vsdx",
            "figures/*.png",
            "visio-ole-figure-map.json",
            "gate-report.txt",
            "variant-manifest.json",
        ],
    ),
    Variant(
        id="narrative_enhanced",
        name="正文叙事增强版",
        focus="强化本科论文语气、章节连贯性、论证密度和证据边界表达。",
        workspace="03-narrative-enhanced",
        generation_notes=[
            "扩写前阅读 thesis-voice-and-style.md，避免把工作日志或证据审计措辞写入正文。",
            "第1-2章集中处理引用，第3-6章按系统事实展开，不编造功能、测试或截图。",
            "gate 必须启用 MinContentUnits、MinCjkChars 和 thesis voice 检查。",
        ],
        gate_profile="narrative",
        expected_outputs=[
            "final docx",
            "optional pdf export",
            "thesis draft markdown",
            "delivery-check-report.md",
            "gate-report.txt",
            "variant-manifest.json",
        ],
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT, help="Root directory for variant workspaces.")
    parser.add_argument("--generator", type=Path, default=DEFAULT_GENERATOR, help="Existing thesis generator to call.")
    parser.add_argument("--checker", type=Path, default=DEFAULT_CHECKER, help="Aggregate DOCX gate script.")
    parser.add_argument("--python", default=sys.executable, help="Python executable used to run the generator.")
    parser.add_argument("--run", action="store_true", help="Actually call the existing generator for each variant.")
    parser.add_argument("--check", action="store_true", help="Run the aggregate DOCX gate after generation when a DOCX exists.")
    parser.add_argument("--clean", action="store_true", help="Delete each variant workspace before running.")
    parser.add_argument(
        "--export-pdf-command",
        help="Optional shell command template for PDF export. Use {docx} and {pdf} placeholders.",
    )
    parser.add_argument("--min-content-units", type=int, default=12000)
    parser.add_argument("--min-cjk-chars", type=int, default=10000)
    parser.add_argument("--expected-visio-ole", type=int, default=0)
    parser.add_argument("--template-profile", type=Path, help="Template profile JSON for the template-first gate.")
    parser.add_argument("--figure-map-name", default="visio-ole-figure-map.json")
    return parser.parse_args()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def run_command(command: list[str], *, env: dict[str, str] | None = None, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=str(cwd), env=env, text=True, encoding="utf-8", errors="replace", capture_output=True)


def find_docx(workspace: Path) -> Path | None:
    preferred = sorted(workspace.glob(f"*{DOCX_SUFFIX}"))
    if preferred:
        return preferred[0]
    matches = sorted(workspace.glob("*.docx"))
    return matches[0] if matches else None


def run_generator(args: argparse.Namespace, workspace: Path) -> dict:
    env = os.environ.copy()
    env["CAMPUS_AFFAIRS_DEMO_WORKSPACE"] = str(workspace)
    result = run_command([args.python, str(args.generator)], env=env)
    log = workspace / "reports" / "generator-run.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(result.stdout + ("\n[stderr]\n" + result.stderr if result.stderr else ""), encoding="utf-8")
    return {
        "command": [args.python, str(args.generator)],
        "returncode": result.returncode,
        "log": str(log),
    }


def export_pdf(command_template: str, docx: Path, workspace: Path) -> dict:
    pdf = docx.with_suffix(".pdf")
    command = command_template.format(docx=str(docx), pdf=str(pdf))
    result = subprocess.run(command, cwd=str(ROOT), shell=True, text=True, encoding="utf-8", errors="replace", capture_output=True)
    log = workspace / "reports" / "pdf-export.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(result.stdout + ("\n[stderr]\n" + result.stderr if result.stderr else ""), encoding="utf-8")
    return {"command": command, "returncode": result.returncode, "pdf": str(pdf), "log": str(log)}


def gate_args(args: argparse.Namespace, variant: Variant, docx: Path, workspace: Path) -> list[str]:
    command = [
        "powershell",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(args.checker),
        str(docx),
        "-MinContentUnits",
        str(args.min_content_units),
        "-MinCjkChars",
        str(args.min_cjk_chars),
        "-RequireContinuationCaption",
    ]
    figure_map = workspace / args.figure_map_name
    if figure_map.exists():
        command.extend(["-FigureMap", str(figure_map)])
    if args.expected_visio_ole > 0:
        command.extend(["-ExpectedVisioOle", str(args.expected_visio_ole)])
    if variant.gate_profile == "template" and args.template_profile:
        command.extend(["-TemplateProfile", str(args.template_profile)])
    return command


def run_gate(args: argparse.Namespace, variant: Variant, workspace: Path, docx: Path) -> dict:
    command = gate_args(args, variant, docx, workspace)
    result = run_command(command)
    report = workspace / "reports" / "gate-report.txt"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(result.stdout + ("\n[stderr]\n" + result.stderr if result.stderr else ""), encoding="utf-8")
    summary = {"command": command, "returncode": result.returncode, "report": str(report)}
    write_json(workspace / "reports" / "gate-report.json", summary)
    return summary


def write_variant_brief(variant: Variant, workspace: Path) -> Path:
    brief = workspace / "variant-brief.md"
    lines = [
        f"# {variant.name}",
        "",
        f"- Variant ID: `{variant.id}`",
        f"- Focus: {variant.focus}",
        f"- Gate profile: `{variant.gate_profile}`",
        "",
        "## Generation Notes",
        "",
        *[f"- {note}" for note in variant.generation_notes],
        "",
        "## Expected Outputs",
        "",
        *[f"- {item}" for item in variant.expected_outputs],
        "",
    ]
    brief.write_text("\n".join(lines), encoding="utf-8")
    return brief


def process_variant(args: argparse.Namespace, variant: Variant) -> dict:
    workspace = (args.out_root / variant.workspace).resolve()
    if args.clean and workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True, exist_ok=True)

    brief = write_variant_brief(variant, workspace)
    manifest = {
        "variant": asdict(variant),
        "workspace": str(workspace),
        "brief": str(brief),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "run_requested": bool(args.run),
        "check_requested": bool(args.check),
        "status": "planned",
        "generator": str(args.generator),
        "checker": str(args.checker),
        "outputs": {},
        "commands": {},
    }

    if args.run:
        manifest["commands"]["generator"] = run_generator(args, workspace)
        manifest["status"] = "generated" if manifest["commands"]["generator"]["returncode"] == 0 else "generator_failed"

    docx = find_docx(workspace)
    if docx:
        manifest["outputs"]["docx"] = str(docx)
    if (workspace / args.figure_map_name).exists():
        manifest["outputs"]["figure_map"] = str(workspace / args.figure_map_name)

    if args.export_pdf_command and docx:
        manifest["commands"]["pdf_export"] = export_pdf(args.export_pdf_command, docx, workspace)
        pdf = docx.with_suffix(".pdf")
        if pdf.exists():
            manifest["outputs"]["pdf"] = str(pdf)

    if args.check and docx:
        manifest["commands"]["gate"] = run_gate(args, variant, workspace, docx)
        manifest["outputs"]["gate_report"] = manifest["commands"]["gate"]["report"]
        manifest["status"] = "gate_passed" if manifest["commands"]["gate"]["returncode"] == 0 else "gate_failed"
    elif args.check and not docx:
        manifest["status"] = "missing_docx_for_gate"

    write_json(workspace / "variant-manifest.json", manifest)
    return manifest


def write_matrix(out_root: Path) -> Path:
    matrix = {
        "variants": [asdict(variant) for variant in VARIANTS],
        "notes": [
            "This matrix separates optimization intent from generator internals.",
            "The current campus demo generator is invoked through CAMPUS_AFFAIRS_DEMO_WORKSPACE so each variant stays isolated.",
            "Use compare_thesis_variants.py after generating or checking variants.",
        ],
    }
    path = out_root / "variant-matrix.json"
    write_json(path, matrix)
    return path


def main() -> int:
    args = parse_args()
    args.out_root = args.out_root.resolve()
    args.out_root.mkdir(parents=True, exist_ok=True)
    matrix_path = write_matrix(args.out_root)
    manifests = [process_variant(args, variant) for variant in VARIANTS]
    summary = {
        "out_root": str(args.out_root),
        "matrix": str(matrix_path),
        "manifests": [str(Path(item["workspace"]) / "variant-manifest.json") for item in manifests],
        "statuses": {item["variant"]["id"]: item["status"] for item in manifests},
    }
    write_json(args.out_root / "variant-generation-summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
