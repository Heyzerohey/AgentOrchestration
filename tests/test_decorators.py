import pytest
from src.sdk.decorators import agent

def test_agent_decorator_version_validation():
    # Should work
    @agent(name="test", version="1.0.0")
    class ValidAgent:
        pass
        
    assert ValidAgent.__agent_config__["version"] == "1.0.0"
    
    # Should fail
    with pytest.raises(ValueError, match="version must be in semantic version format"):
        @agent(name="test", version="v1.0.0")
        class InvalidAgent1:
            pass
            
    with pytest.raises(ValueError, match="version must be in semantic version format"):
        @agent(name="test", version="1.0")
        class InvalidAgent2:
            pass
