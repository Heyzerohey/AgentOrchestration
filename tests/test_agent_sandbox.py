import pytest
import tempfile
from pathlib import Path
from src.agent.sandbox import AgentSandbox


def test_sandbox_create_valid():
    with tempfile.TemporaryDirectory() as tmpdir:
        sandbox = AgentSandbox(base_path=tmpdir)
        path = sandbox.create("valid-agent-1")
        assert path.exists()
        assert path.parent == Path(tmpdir).resolve()
        assert sandbox.get_path("valid-agent-1") == path


def test_sandbox_create_directory_traversal():
    with tempfile.TemporaryDirectory() as tmpdir:
        sandbox = AgentSandbox(base_path=tmpdir)

        with pytest.raises(ValueError, match="Unsafe agent ID"):
            sandbox.create("sub/folder")

        with pytest.raises(ValueError, match="Unsafe agent ID"):
            sandbox.create("sub\\folder")

        with pytest.raises(ValueError, match="Unsafe agent ID"):
            sandbox.create("../outside")

        with pytest.raises(ValueError, match="Unsafe agent ID"):
            sandbox.create("agent\x00id")

        with pytest.raises(ValueError, match="Unsafe agent ID"):
            sandbox.create("")
