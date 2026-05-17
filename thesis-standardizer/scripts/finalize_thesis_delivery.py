#!/usr/bin/env python3
"""Run a structured final thesis format check workflow."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from docx_io import ensure_readable_docx


def run_step(script_dir: Path, name: str, *extra: str, allowed_returncodes: set[int] | None = None) -> int:
    script_path = script_dir / name
    completed = subprocess.run([sys.executable, str(script_path), *extra], check=False)
    allowed = allowed_returncodes or {0}
    if completed.returncode not in allowed:
        raise subprocess.CalledProcessError(completed.returncode, completed.args)
    return completed.returncode


def detect_template_inputs(workspace: Path, template_profile: str | None, template_rule_overrides: str | None) -> tuple[Path, Path | None]:
    profile_path = Path(template_profile).resolve() if template_profile else workspace / "paper-context" / "template-extract" / "template-profile.json"
    override_path = Path(template_rule_overrides).resolve() if template_rule_overrides else workspace / "paper-context" / "template-extract" / "template-rule-overrides.yaml"
    return profile_path.resolve(), override_path.resolve() if override_path.exists() else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Run workspace check plus template compare/repair/re-compare in a canonical final-delivery flow.")
    parser.add_argument("thesis_docx", help="Final thesis .docx to check.")
    parser.add_argument("--workspace", default=".", help="Workspace root containing thesis-ai-standard and paper-context.")
    parser.add_argument("--template-profile", help="Optional template-profile.json path. Defaults to paper-context/template-extract/template-profile.json.")
    parser.add_argument("--template-rule-overrides", help="Optional template-rule-overrides.yaml path.")
    parser.add_argument("--skip-delivery-preflight", action="store_true", help="Skip delivery preflight checks before compare/repair.")
    parser.add_argument("--skip-workspace-check", action="store_true", help="Skip thesis-ai-standard workspace validation.")
    parser.add_argument("--out-dir", default="paper-context/template-compare", help="Relative or absolute report directory.")
    parser.add_argument("--out-docx", help="Optional repaired .docx output path.")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    script_dir = Path(__file__).resolve().parent
    thesis_docx = ensure_readable_docx(Path(args.thesis_docx), "thesis docx")
    template_profile, template_rule_overrides = detect_template_inputs(
        workspace, args.template_profile, args.template_rule_overrides
    )

    if not template_profile.exists():
        raise FileNotFoundError(
            "template profile not found. Expected extracted school template profile at "
            f"{template_profile}. Run bootstrap_thesis_project.py --template-docx first or pass --template-profile."
        )

    if not args.skip_delivery_preflight:
        run_step(
            script_dir,
            "check_delivery_preflight.py",
            str(thesis_docx),
            "--workspace",
            str(workspace),
            "--out",
            str(workspace / "paper-context" / "template-compare" / "delivery-preflight.md"),
        )

    if not args.skip_workspace_check:
        run_step(
            script_dir,
            "check_thesis_workspace.py",
            str(workspace / "thesis-ai-standard"),
            "--out",
            str(workspace / "paper-context" / "template-compare" / "workspace-check.md"),
        )

    finalize_args = [
        str(thesis_docx),
        str(template_profile),
        "--workspace",
        str(workspace),
        "--out-dir",
        args.out_dir,
    ]
    if template_rule_overrides is not None:
        finalize_args.extend(["--template-rule-overrides", str(template_rule_overrides)])
    if args.out_docx:
        finalize_args.extend(["--out-docx", str(Path(args.out_docx).resolve())])

    finalize_code = run_step(script_dir, "finalize_docx_with_template.py", *finalize_args, allowed_returncodes={0, 2})

    print("Final thesis delivery check complete.")
    print(f"Workspace: {workspace}")
    print(f"Thesis DOCX: {thesis_docx}")
    print(f"Template profile: {template_profile}")
    if template_rule_overrides is not None:
        print(f"Template overrides: {template_rule_overrides}")
    print("Reports: paper-context/template-compare/")
    if finalize_code == 2:
        print("Result: remaining major/minor template findings still require review or manual adjustment.")
    return finalize_code


if __name__ == "__main__":
    raise SystemExit(main())
