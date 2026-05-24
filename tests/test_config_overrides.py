import os
from unittest import mock
import pytest
from src.common.config import Config


def test_env_numeric_coercion():
    env_mock = {
        "AO_APP_PORT": "8080",
        "AO_APP_PORTNEG": "-8080",
        "AO_APP_PORTZERO": "0",
        "AO_DB_TIMEOUT": "5.5",
        "AO_DB_TIMEOUTNEG": "-5.5",
        "AO_DB_TIMEOUTSCI": "1e3",
        "AO_APP_VERSION": "1.0.0",
        "AO_DB_HOST": "127.0.0.1",
        "AO_DB_ENABLED": "true",
        "AO_DB_NAME": "nan",
        "AO_DB_INF": "inf",
        "AO_DB_INFVAL": "infinity",
        "AO_DB_INFNEG": "-inf",
        "AO_DB_INFNEGVAL": "-infinity",
    }
    with mock.patch.dict(os.environ, env_mock):
        config = Config()
        assert config.get("app.port") == 8080
        assert config.get("app.portneg") == -8080
        assert config.get("app.portzero") == 0
        assert config.get("db.timeout") == 5.5
        assert config.get("db.timeoutneg") == -5.5
        assert config.get("db.timeoutsci") == 1000.0
        assert config.get("app.version") == "1.0.0"
        assert config.get("db.host") == "127.0.0.1"
        assert config.get("db.enabled") == "true"
        assert config.get("db.name") == "nan"
        assert config.get("db.inf") == "inf"
        assert config.get("db.infval") == "infinity"
        assert config.get("db.infneg") == "-inf"
        assert config.get("db.infnegval") == "-infinity"
