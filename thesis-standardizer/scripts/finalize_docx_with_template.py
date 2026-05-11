#!/usr/bin/env python3
"""Run compare -> repair -> re-compare for a thesis .docx against a template."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

from append_revision_log import RevisionRecord, append_jsonl, append_markdown, ensure_revision_log, next_revision_id
from compare_docx_to_template import (
    compare_back_matter_page_number_policy,
    compare_caption_positions,
    compare_front_matter_page_number_rules,
    compare_heading_styles,
    compare_page_number_event_continuity,
    compare_page_number_format_zones,
    compare_section_roles_and_page_number_start,
    compare_sections,
    compare_style_formats,
    compare_toc_boundary_policy,
    compare_unexpected_page_number_restarts,
    render_markdown as render_compare_markdown,
)
from extract_docx_template_profile import build_profile
from repair_docx_from_template import RepairAction, render_markdown as render_repair_markdown, repair_docx


def load_overrides(path: str | None) -> dict[str, Any] | None:
    if not path:
        return None
    override_path = Path(path).resolve()
    if not override_path.exists():
        return None
    payload = yaml.safe_load(override_path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def collect_findings(thesis_docx: Path, template_profile: dict[str, Any], overrides: dict[str, Any] | None) -> list[Any]:
    thesis_profile = build_profile(thesis_docx)
    findings = []
    findings.extend(compare_sections(template_profile, thesis_profile))
    findings.extend(compare_heading_styles(template_profile, thesis_profile, overrides))
    findings.extend(compare_style_formats(template_profile, thesis_profile, overrides))
    findings.extend(compare_caption_positions(thesis_profile, overrides))
    findings.extend(compare_section_roles_and_page_number_start(thesis_profile, overrides))
    findings.extend(compare_front_matter_page_number_rules(thesis_profile, overrides))
    findings.extend(compare_page_number_format_zones(template_profile, thesis_profile, overrides))
    findings.extend(compare_unexpected_page_number_restarts(template_profile, thesis_profile, overrides))
    findings.extend(compare_page_number_event_continuity(template_profile, thesis_profile, overrides))
    findings.extend(compare_back_matter_page_number_policy(template_profile, thesis_profile, overrides))
    findings.extend(compare_toc_boundary_policy(thesis_profile, overrides))
    return findings


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def resolve_output_dir(raw: str, workspace: Path) -> Path:
    candidate = Path(raw)
    if candidate.is_absolute():
        return candidate.resolve()
    direct = (Path.cwd() / candidate).resolve()
    workspace_text = str(workspace).lower()
    direct_text = str(direct).lower()
    if direct == workspace or direct_text.startswith(workspace_text + "\\"):
        return direct
    normalized = str(candidate).replace("/", "\\").lower()
    workspace_name = workspace.name.lower()
    if normalized == workspace_name or normalized.startswith(workspace_name + "\\"):
        return (workspace.parent / candidate).resolve()
    return (workspace / candidate).resolve()


def append_repair_actions_to_revision_log(workspace: Path, repaired_docx: Path, report_path: Path, actions: list[RepairAction]) -> None:
    if not actions:
        return
    log_path = workspace / "paper-context" / "workflow" / "revision-log.md"
    jsonl_path = workspace / "paper-context" / "workflow" / "revision-trace.jsonl"
    ensure_revision_log(log_path)
    for action in actions:
        record = RevisionRecord(
            id=next_revision_id(log_path),
            date=date.today().isoformat(),
            timestamp=datetime.now().isoformat(timespec="seconds"),
            source="template auto repair",
            location=action.location,
            before=action.before,
            after=action.after,
            change=action.change,
            reason="synchronize thesis docx with confirmed school template profile",
            evidence=str(report_path),
            files=[str(repaired_docx), str(report_path)],
            status="done" if action.status == "done" else "needs_review",
            needs_source="none",
            needs_evidence="manual Word/PDF review still required for fields and pagination",
        )
        append_markdown(log_path, record)
        append_jsonl(jsonl_path, record)


def render_summary(
    thesis_docx: Path,
    repaired_docx: Path,
    before_findings: list[Any],
    after_findings: list[Any],
    actions: list[RepairAction],
) -> str:
    lines = [
        "# Template Finalization Summary",
        "",
        f"- Source thesis: `{thesis_docx}`",
        f"- Repaired thesis: `{repaired_docx}`",
        f"- Findings before repair: `{len(before_findings)}`",
        f"- Repair actions: `{len(actions)}`",
        f"- Findings after repair: `{len(after_findings)}`",
        "",
    ]
    if before_findings:
        lines.append("## Outcome")
        lines.append("")
        lines.append(f"- Before repair, the document had `{len(before_findings)}` detected template deviations.")
        lines.append(f"- After repair, the document has `{len(after_findings)}` remaining deviations within the current comparison scope.")
        lines.append("")
    lines.append("Manual review still remains required for TOC fields, page-number fields, cross-references, and complex pagination.")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Finalize a thesis docx with template compare/repair/re-compare.")
    parser.add_argument("thesis_docx", help="Thesis .docx file to process.")
    parser.add_argument("template_profile_json", help="template-profile.json path extracted from school template.")
    parser.add_argument("--template-rule-overrides", help="Optional template-rule-overrides.yaml path.")
    parser.add_argument("--workspace", default=".", help="Workspace root for workflow logging.")
    parser.add_argument("--out-dir", default="paper-context/template-compare", help="Directory for compare/repair reports.")
    parser.add_argument("--out-docx", help="Path for repaired .docx. Defaults to <name>_repaired.docx next to source.")
    args = parser.parse_args()

    thesis_docx = Path(args.thesis_docx).resolve()
    template_json = Path(args.template_profile_json).resolve()
    workspace = Path(args.workspace).resolve()
    out_dir = resolve_output_dir(args.out_dir, workspace)
    out_dir.mkdir(parents=True, exist_ok=True)

    template_profile = json.loads(template_json.read_text(encoding="utf-8"))
    overrides = load_overrides(args.template_rule_overrides)
    repaired_docx = Path(args.out_docx).resolve() if args.out_docx else thesis_docx.with_name(f"{thesis_docx.stem}_repaired{thesis_docx.suffix}")

    before_findings = collect_findings(thesis_docx, template_profile, overrides)
    before_md = out_dir / "template-compare-before.md"
    before_json = out_dir / "template-compare-before.json"
    write_text(before_md, render_compare_markdown(thesis_docx, template_json, before_findings))
    write_json(
        before_json,
        {
            "thesis_docx": str(thesis_docx),
            "template_profile_json": str(template_json),
            "finding_count": len(before_findings),
            "findings": [finding.__dict__ for finding in before_findings],
        },
    )

    actions = repair_docx(thesis_docx, template_profile, repaired_docx, overrides)
    repair_md = out_dir / "template-repair-report.md"
    repair_json = out_dir / "template-repair-report.json"
    write_text(repair_md, render_repair_markdown(thesis_docx, repaired_docx, actions))
    write_json(
        repair_json,
        {
            "source_docx": str(thesis_docx),
            "repaired_docx": str(repaired_docx),
            "actions": [action.__dict__ for action in actions],
        },
    )

    after_findings = collect_findings(repaired_docx, template_profile, overrides)
    after_md = out_dir / "template-compare-after.md"
    after_json = out_dir / "template-compare-after.json"
    write_text(after_md, render_compare_markdown(repaired_docx, template_json, after_findings))
    write_json(
        after_json,
        {
            "thesis_docx": str(repaired_docx),
            "template_profile_json": str(template_json),
            "finding_count": len(after_findings),
            "findings": [finding.__dict__ for finding in after_findings],
        },
    )

    append_repair_actions_to_revision_log(workspace, repaired_docx, repair_md, actions)

    summary_md = out_dir / "template-finalization-summary.md"
    write_text(summary_md, render_summary(thesis_docx, repaired_docx, before_findings, after_findings, actions))

    print(f"Wrote {before_md}")
    print(f"Wrote {before_json}")
    print(f"Wrote {repair_md}")
    print(f"Wrote {repair_json}")
    print(f"Wrote {after_md}")
    print(f"Wrote {after_json}")
    print(f"Wrote {summary_md}")
    print(f"Wrote {repaired_docx}")

    return 0 if not any(item.severity in {"critical", "major"} for item in after_findings) else 2


if __name__ == "__main__":
    raise SystemExit(main())
