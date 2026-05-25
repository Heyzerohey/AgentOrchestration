import pytest
import tempfile
import os
import shutil
from pathlib import Path
from src.agent.sandbox import AgentSandbox

def test_sandbox_get_path_verification():
    sandbox = AgentSandbox()
    path = sandbox.create("agent-test")
    
    # Should work normally
    assert sandbox.get_path("agent-test") == path
    
    # Should fail if deleted
    shutil.rmtree(path)
    assert sandbox.get_path("agent-test") is None
    
    # Recreate and simulate escaping sandbox
    path = sandbox.create("agent-test-2")
    
    # Symlink to outside
    bad_link = path / "bad"
    os.symlink("/tmp", bad_link)
    
    # Update the tracking dict to point to the bad link
    sandbox._sandboxes["agent-test-2"] = bad_link
    
    # Should fail relative_to check
    assert sandbox.get_path("agent-test-2") is None
    
    sandbox.cleanup_all()
