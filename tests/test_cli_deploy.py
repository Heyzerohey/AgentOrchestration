"""Regression tests for CLI exit codes and deploy argument validation."""

import os
import json
import pytest
from unittest.mock import patch, MagicMock

from src.cli.main import cli


def test_cli_init_success():
    # Calling init should return 0
    code = cli(["init", "my-project"])
    assert code == 0


def test_cli_deploy_missing_manifest(tmp_path, capsys):
    manifest_path = tmp_path / "missing.json"
    code = cli(["deploy", str(manifest_path)])

    assert code == 1
    captured = capsys.readouterr()
    assert "Error: Manifest file not found" in captured.err


def test_cli_deploy_malformed_json(tmp_path, capsys):
    manifest_path = tmp_path / "malformed.json"
    with open(manifest_path, "w") as f:
        f.write("{invalid-json}")

    code = cli(["deploy", str(manifest_path)])

    assert code == 1
    captured = capsys.readouterr()
    assert "Error: Failed to parse manifest JSON" in captured.err


def test_cli_deploy_missing_keys(tmp_path, capsys):
    manifest_path = tmp_path / "invalid_manifest.json"
    # missing 'type' key
    with open(manifest_path, "w") as f:
        json.dump({"name": "my-agent"}, f)

    code = cli(["deploy", str(manifest_path)])

    assert code == 1
    captured = capsys.readouterr()
    assert "Error: Manifest must contain 'name' and 'type' keys" in captured.err


@patch("src.cli.main.OrchestratorClient.register_agent")
def test_cli_deploy_api_error(mock_register, tmp_path, capsys):
    manifest_path = tmp_path / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump({"name": "my-agent", "type": "python"}, f)

    # Mock client error response
    mock_register.return_value = {"error": 400, "message": "Invalid agent type"}

    code = cli(["deploy", str(manifest_path)])

    assert code == 1
    captured = capsys.readouterr()
    assert "Error: Deployment failed: Invalid agent type" in captured.err


@patch("src.cli.main.OrchestratorClient.register_agent")
def test_cli_deploy_connection_refused(mock_register, tmp_path, capsys):
    manifest_path = tmp_path / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump({"name": "my-agent", "type": "python"}, f)

    # Mock connection exception
    mock_register.side_effect = Exception("Connection refused")

    code = cli(["deploy", str(manifest_path)])

    assert code == 1
    captured = capsys.readouterr()
    assert "Error: Failed to contact the orchestrator: Connection refused" in captured.err


@patch("src.cli.main.OrchestratorClient.register_agent")
def test_cli_deploy_success(mock_register, tmp_path, capsys):
    manifest_path = tmp_path / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump({"name": "my-agent", "type": "python", "config": {"memory": 512}}, f)

    # Mock successful response
    mock_register.return_value = {"agent_id": "agent-12345"}

    code = cli(["deploy", str(manifest_path)])

    assert code == 0
    captured = capsys.readouterr()
    assert "Agent deployed successfully: agent-12345" in captured.out
