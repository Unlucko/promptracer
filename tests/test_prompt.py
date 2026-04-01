"""Tests for the core Prompt class."""

import tempfile
from pathlib import Path

from promptracer.prompt import Prompt


def test_create_prompt():
    p = Prompt("Hello {{name}}")
    assert p.template == "Hello {{name}}"
    assert p.version == 1


def test_variables_extraction():
    p = Prompt("Translate {{text}} to {{lang}}")
    assert sorted(p.variables) == ["lang", "text"]


def test_set_vars_and_render():
    p = Prompt("Hello {{name}}, you are {{age}} years old")
    p.set_vars(name="Cesar", age="25")
    assert p.render() == "Hello Cesar, you are 25 years old"


def test_render_missing_vars():
    p = Prompt("Hello {{name}}")
    try:
        p.render()
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "name" in str(e)


def test_chaining():
    p = Prompt("{{a}} {{b}}").set_vars(a="x", b="y")
    assert p.render() == "x y"


def test_versioning():
    p = Prompt("version 1")
    assert p.version == 1
    p.update("version 2")
    assert p.version == 2
    assert p.template == "version 2"
    assert len(p.history()) == 2


def test_diff():
    p = Prompt("v1")
    p.update("v2")
    p.update("v3")
    old, new = p.diff()
    assert old == "v2"
    assert new == "v3"
    old, new = p.diff(1, 3)
    assert old == "v1"
    assert new == "v3"


def test_save_and_load():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test.yaml"
        p = Prompt("Hello {{name}}", name="greeting", system="Be friendly")
        p.set_vars(name="World")
        p.save(path)

        loaded = Prompt.load(path)
        assert loaded.template == "Hello {{name}}"
        assert loaded.name == "greeting"
        assert loaded.system == "Be friendly"
        assert loaded.render() == "Hello World"


def test_save_load_with_history():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "versioned.yaml"
        p = Prompt("v1")
        p.update("v2")
        p.save(path)

        loaded = Prompt.load(path)
        assert loaded.version == 2
        assert loaded.template == "v2"


def test_repr():
    p = Prompt("short")
    assert "short" in repr(p)
    assert "v1" in repr(p)

    long_template = "x" * 100
    p2 = Prompt(long_template)
    assert "..." in repr(p2)


def test_metadata():
    p = Prompt("test", metadata={"tags": ["a", "b"]})
    assert p.metadata["tags"] == ["a", "b"]


def test_no_variables():
    p = Prompt("No variables here")
    assert p.variables == []
    assert p.render() == "No variables here"
