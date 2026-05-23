"""Validate GitHub Actions workflow permissions.

Validation jobs should run read-only. Publishing jobs may request write scopes,
but they must do so explicitly at the job level.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable

import yaml


WRITE_VALUES = {"write", "write-all"}
RELEASE_JOB_MARKERS = ("publish", "release", "deploy")


def iter_workflow_files(root: Path) -> Iterable[Path]:
    workflow_dir = root / ".github" / "workflows"
    if not workflow_dir.exists():
        return []
    return sorted(
        path
        for pattern in ("*.yml", "*.yaml")
        for path in workflow_dir.glob(pattern)
    )


def load_workflow(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: workflow must be a mapping")
    return data


def has_write_scope(permissions: Any) -> bool:
    if permissions is None:
        return False
    if isinstance(permissions, str):
        return permissions in WRITE_VALUES
    if not isinstance(permissions, dict):
        permissions_type = type(permissions).__name__
        raise ValueError(
            f"permissions must be a mapping or string, got {permissions_type}"
        )
    return any(value in WRITE_VALUES for value in permissions.values())


def is_release_job(job_name: str) -> bool:
    normalized = job_name.lower()
    return any(marker in normalized for marker in RELEASE_JOB_MARKERS)


def validate_workflows(root: Path | str = ".") -> None:
    root_path = Path(root)
    errors: list[str] = []

    for workflow_file in iter_workflow_files(root_path):
        workflow = load_workflow(workflow_file)
        top_permissions = workflow.get("permissions")

        if has_write_scope(top_permissions):
            errors.append(
                f"{workflow_file}: top-level permissions must not grant "
                "write-all or write scopes"
            )

        jobs = workflow.get("jobs") or {}
        if not isinstance(jobs, dict):
            errors.append(f"{workflow_file}: jobs must be a mapping")
            continue

        for job_name, job in jobs.items():
            if not isinstance(job, dict):
                continue

            job_permissions = job.get("permissions")
            job_name_text = str(job_name)
            if has_write_scope(job_permissions) and not is_release_job(
                job_name_text
            ):
                errors.append(
                    f"{workflow_file}: job '{job_name}' requests write "
                    "permissions but is not a release job"
                )

            if (
                is_release_job(job_name_text)
                and has_write_scope(top_permissions)
            ):
                errors.append(
                    f"{workflow_file}: release job '{job_name}' must "
                    "declare write permissions at job level"
                )

    if errors:
        raise ValueError("\n".join(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root to scan.",
    )
    args = parser.parse_args()

    try:
        validate_workflows(args.root)
    except ValueError as exc:
        print(exc)
        return 1

    print("Workflow permissions policy passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
