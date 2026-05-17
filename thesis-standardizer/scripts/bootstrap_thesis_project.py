#!/usr/bin/env python3
"""Run the common thesis bootstrap flow in one command."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from docx_io import ensure_readable_docx


def run_step(script_dir: Path, name: str, *extra: str) -> None:
    script_path = script_dir / name
    subprocess.run([sys.executable, str(script_path), *extra], check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap a thesis workspace and optional evidence in one command.")
    parser.add_argument("workspace", nargs="?", default=".", help="Project workspace root.")
    parser.add_argument("--project-dir", help="Optional source project directory for evidence scanning.")
    parser.add_argument("--template-docx", help="Optional school thesis .docx template to extract and apply.")
    parser.add_argument("--skip-evidence", action="store_true", help="Skip build_project_evidence.py.")
    parser.add_argument("--skip-check", action="store_true", help="Skip check_thesis_workspace.py.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite thesis-ai-standard if it already exists.")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    script_dir = Path(__file__).resolve().parent

    init_args = [str(workspace)]
    if args.overwrite:
        init_args.append("--overwrite")
    run_step(script_dir, "init_thesis_workspace.py", *init_args)

    if args.template_docx:
        template_docx = ensure_readable_docx(Path(args.template_docx), "school template docx")
        template_extract_dir = workspace / "paper-context" / "template-extract"
        template_profile_json = template_extract_dir / "template-profile.json"
        run_step(
            script_dir,
            "extract_docx_template_profile.py",
            str(template_docx),
            "--out",
            str(template_extract_dir),
        )
        run_step(
            script_dir,
            "generate_template_rule_overrides.py",
            str(template_profile_json),
            "--out",
            str(template_extract_dir / "template-rule-overrides.yaml"),
        )
        run_step(
            script_dir,
            "apply_docx_template_profile.py",
            str(template_profile_json),
            "--standard-profile",
            str(workspace / "thesis-ai-standard" / "templates" / "standard-profile.yaml"),
            "--template-docx",
            str(template_docx),
        )

    if not args.skip_evidence:
        project_dir = Path(args.project_dir).resolve() if args.project_dir else workspace
        evidence_out = workspace / "paper-context" / "evidence"
        run_step(script_dir, "build_project_evidence.py", str(project_dir), "--out", str(evidence_out))

    if not args.skip_check:
        run_step(script_dir, "check_thesis_workspace.py", str(workspace / "thesis-ai-standard"))

    print("Bootstrap complete.")
    print(f"Workspace: {workspace}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
