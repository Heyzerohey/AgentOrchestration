"""Regression tests for Config nested state deep-copy isolation."""

import pytest
import os
import json
from src.common.config import Config


def test_config_set_isolation():
    config = Config()
    shared_dict = {"nested": {"key": "original_value"}}

    # Set the dictionary
    config.set("app.settings", shared_dict)

    # Mutate the original dictionary externally
    shared_dict["nested"]["key"] = "mutated_value"
    shared_dict["new_key"] = "leak"

    # Internal config state must be protected (remain original_value)
    stored = config.get("app.settings")
    assert stored["nested"]["key"] == "original_value"
    assert "new_key" not in stored


def test_config_get_isolation():
    config = Config()
    config.set("app.settings", {"nested": {"key": "original_value"}})

    # Get the dictionary
    retrieved = config.get("app.settings")

    # Mutate the retrieved dictionary externally
    retrieved["nested"]["key"] = "mutated_value"

    # Internal config state must be protected (remain original_value)
    stored = config.get("app.settings")
    assert stored["nested"]["key"] == "original_value"


def test_config_to_dict_isolation():
    config = Config()
    config.set("app.settings", {"key": "original"})

    # Get the complete dict representation
    full_dict = config.to_dict()

    # Mutate the representation externally
    full_dict["app"]["settings"]["key"] = "mutated"
    full_dict["app"]["new_field"] = "leak"

    # Internals must remain untouched
    assert config.get("app.settings.key") == "original"
    assert config.get("app.new_field") is None


def test_config_load_isolation(tmp_path):
    config_file = tmp_path / "config.json"
    initial_data = {"database": {"host": "localhost", "port": 5432}}
    with open(config_file, "w") as f:
        json.dump(initial_data, f)

    config = Config(str(config_file))

    # Mutate a returned nested dict
    db_config = config.get("database")
    db_config["host"] = "mutated_host"

    # Config should still have localhost
    assert config.get("database.host") == "localhost"
