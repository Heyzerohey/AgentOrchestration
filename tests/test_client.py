import pytest
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError
from src.sdk.client import OrchestratorClient

def test_client_get_retries():
    client = OrchestratorClient(base_url="http://test", api_key="test", retries=2)
    
    mock_error = HTTPError("http://test/api/v2/agents", 502, "Bad Gateway", {}, None)
    mock_success = MagicMock()
    mock_success.read.return_value = b'{"success": true}'
    
    # We will simulate 2 failures then 1 success
    responses = [mock_error, mock_error, mock_success]
    
    def side_effect(*args, **kwargs):
        resp = responses.pop(0)
        if isinstance(resp, Exception):
            raise resp
        # Return a context manager for urlopen
        cm = MagicMock()
        cm.__enter__.return_value = resp
        return cm

    with patch("src.sdk.client.urlopen", side_effect=side_effect):
        with patch("time.sleep") as mock_sleep:
            result = client.list_agents()
            assert result == {"success": True}
            assert mock_sleep.call_count == 2
            
def test_client_get_retries_exceeded():
    client = OrchestratorClient(base_url="http://test", api_key="test", retries=1)
    
    mock_error = HTTPError("http://test/api/v2/agents", 502, "Bad Gateway", {}, None)
    
    responses = [mock_error, mock_error]
    
    def side_effect(*args, **kwargs):
        raise responses.pop(0)

    with patch("src.sdk.client.urlopen", side_effect=side_effect):
        with patch("time.sleep") as mock_sleep:
            result = client.list_agents()
            assert result == {"error": 502, "message": "Bad Gateway"}
            assert mock_sleep.call_count == 1
