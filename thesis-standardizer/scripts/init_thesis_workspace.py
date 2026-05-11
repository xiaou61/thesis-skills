#!/usr/bin/env python3
"""Copy the bundled thesis-ai-standard package into a project workspace."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from init_workflow_logs import write_workflow_logs


def copytree_merge(src: Path, dst: Path, overwrite: bool) -> None:
    if not src.exists():
        raise FileNotFoundError(f"Bundled template not found: {src}")

    if dst.exists() and not overwrite:
        raise FileExistsError(
            f"Target already exists: {dst}. Re-run with --overwrite to replace files."
        )

    if dst.exists() and overwrite:
        shutil.rmtree(dst)

    shutil.copytree(src, dst)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Initialize a thesis-ai-standard workspace from the thesis-standardizer skill."
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Project directory where thesis-ai-standard should be created.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing thesis-ai-standard directory.",
    )
    parser.add_argument(
        "--no-workflow-logs",
        action="store_true",
        help="Skip creating paper-context/workflow log files.",
    )
    args = parser.parse_args()

    skill_dir = Path(__file__).resolve().parents[1]
    src = skill_dir / "assets" / "thesis-ai-standard"
    target_dir = Path(args.target).resolve()
    dst = target_dir / "thesis-ai-standard"

    target_dir.mkdir(parents=True, exist_ok=True)
    copytree_merge(src, dst, overwrite=args.overwrite)
    workflow_paths = []
    if not args.no_workflow_logs:
        workflow_paths = write_workflow_logs(target_dir, overwrite=args.overwrite)

    print(f"Initialized thesis workspace: {dst}")
    print("Next files to fill:")
    print(f"- {dst / 'templates' / 'standard-profile.yaml'}")
    print(f"- {dst / 'templates' / 'thesis-ai-spec.yaml'}")
    print(f"- {dst / 'templates' / 'figure-registry.yaml'}")
    if args.no_workflow_logs:
        print("Skipped workflow logs by request.")
    elif workflow_paths:
        print("Workflow logs initialized:")
        for path in workflow_paths:
            print(f"- {path}")
    else:
        print(f"Workflow logs already present: {target_dir / 'paper-context' / 'workflow'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
