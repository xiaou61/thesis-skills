#!/usr/bin/env python3
"""Create a combined template replication diff report for a final DOCX."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


def run_check(command: list[str]) -> dict[str, object]:
    result = subprocess.run(command, text=True, capture_output=True)
    return {
        "command": command,
        "exitCode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run template-replication checks and write a combined report.")
    parser.add_argument("docx")
    parser.add_argument("--template-profile")
    parser.add_argument("--out", default="paper-context/template-extract/template-replication-diff.md")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    docx = str(Path(args.docx).resolve())
    profile_args = ["--template-profile", str(Path(args.template_profile).resolve())] if args.template_profile else []
    checks = [
        ["python", str(script_dir / "check_docx_component_order.py"), docx],
        ["python", str(script_dir / "check_docx_style_profile.py"), docx, *profile_args],
        ["python", str(script_dir / "check_docx_page_model.py"), docx, *profile_args],
        ["python", str(script_dir / "check_docx_caption_numbering.py"), docx],
    ]
    results = [run_check(command) for command in checks]
    failed = [item for item in results if item["exitCode"] != 0]

    lines = [
        "# Template Replication Diff Report",
        "",
        f"- DOCX: `{docx}`",
        f"- Template profile: `{args.template_profile or ''}`",
        f"- Checks: `{len(results)}`",
        f"- Failed checks: `{len(failed)}`",
        "",
    ]
    for item in results:
        lines.append(f"## {' '.join(item['command'][:3])}")
        lines.append("")
        lines.append(f"- Exit code: `{item['exitCode']}`")
        if item["stdout"]:
            lines.extend(["", "```text", item["stdout"].strip(), "```", ""])
        if item["stderr"]:
            lines.extend(["", "```text", item["stderr"].strip(), "```", ""])

    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
