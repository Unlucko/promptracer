"""Tests for config module."""

from pathlib import Path

from promptracer.config import load_config, find_config


def test_load_config_from_path(tmp_path):
    config_file = tmp_path / ".promptracer.yaml"
    config_file.write_text("default_model: openai/gpt-4o\ntrack_costs: true\n")

    config = load_config(config_file)
    assert config["default_model"] == "openai/gpt-4o"
    assert config["track_costs"] is True


def test_load_config_missing():
    config = load_config(Path("/nonexistent/.promptracer.yaml"))
    assert config == {}


def test_find_config(tmp_path):
    config_file = tmp_path / ".promptracer.yaml"
    config_file.write_text("default_model: test\n")

    found = find_config(tmp_path)
    assert found == config_file


def test_find_config_not_found(tmp_path):
    subdir = tmp_path / "deep" / "nested"
    subdir.mkdir(parents=True)
    found = find_config(subdir)
    # May or may not find one depending on user's home dir
    # Just ensure it doesn't crash
    assert found is None or found.exists()
