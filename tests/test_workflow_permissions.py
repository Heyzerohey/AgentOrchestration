import textwrap
from pathlib import Path

import pytest

from scripts.validate_workflow_permissions import (
    validate_workflows,
)


def write_workflow(root: Path, name: str, contents: str) -> None:
    workflow_dir = root / ".github" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    workflow = workflow_dir / name
    workflow.write_text(textwrap.dedent(contents), encoding="utf-8")


def test_pull_request_validation_jobs_are_read_only(tmp_path):
    write_workflow(
        tmp_path,
        "ci.yml",
        """
        name: CI
        on: [pull_request]
        permissions:
          contents: read
        jobs:
          test:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v4
        """,
    )

    validate_workflows(tmp_path)


def test_broad_top_level_write_permission_is_rejected(tmp_path):
    write_workflow(
        tmp_path,
        "ci.yml",
        """
        name: CI
        on: [pull_request]
        permissions: write-all
        jobs:
          test:
            runs-on: ubuntu-latest
            steps: []
        """,
    )

    with pytest.raises(ValueError, match="write-all"):
        validate_workflows(tmp_path)


def test_validation_job_cannot_request_write_scope(tmp_path):
    write_workflow(
        tmp_path,
        "ci.yml",
        """
        name: CI
        on: [pull_request]
        permissions:
          contents: read
        jobs:
          lint:
            permissions:
              contents: write
            runs-on: ubuntu-latest
            steps: []
        """,
    )

    with pytest.raises(ValueError, match="lint"):
        validate_workflows(tmp_path)


def test_release_job_must_declare_required_write_scope_explicitly(tmp_path):
    write_workflow(
        tmp_path,
        "release.yml",
        """
        name: Release
        on: [push]
        permissions:
          contents: read
        jobs:
          release:
            permissions:
              contents: write
            runs-on: ubuntu-latest
            steps: []
        """,
    )

    validate_workflows(tmp_path)
