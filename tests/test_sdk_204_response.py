import json
from unittest.mock import MagicMock, patch
import pytest
from src.sdk.client import OrchestratorClient


def test_sdk_handles_204_no_content():
    client = OrchestratorClient(base_url="http://test-api", api_key="test-key")
    
    mock_resp = MagicMock()
    mock_resp.status = 204
    mock_resp.read.return_value = b""
    
    with patch("src.sdk.client.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = mock_resp
        
        res = client._request("DELETE", "/agents/agent-123")
        assert res == {"status": "success"}


def test_sdk_handles_empty_body_success():
    client = OrchestratorClient(base_url="http://test-api", api_key="test-key")
    
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = b""
    
    with patch("src.sdk.client.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = mock_resp
        
        res = client._request("POST", "/agents/agent-123/stop")
        assert res == {"status": "success"}


def test_sdk_handles_json_response():
    client = OrchestratorClient(base_url="http://test-api", api_key="test-key")
    
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = b'{"status": "running", "id": "agent-123"}'
    
    with patch("src.sdk.client.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = mock_resp
        
        res = client._request("GET", "/agents/agent-123")
        assert res == {"status": "running", "id": "agent-123"}
