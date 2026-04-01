"""Tests for dataset loader."""

import json

from promptracer.dataset import load_cases_from_csv, load_cases_from_json, load_cases


def test_load_from_csv(tmp_path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("name,lang,text,expected\nSpanish,English,Hola,Hello\nFrench,English,Bonjour,Hello\n")

    cases = load_cases_from_csv(csv_file)
    assert len(cases) == 2
    assert cases[0].name == "Spanish"
    assert cases[0].vars == {"lang": "English", "text": "Hola"}
    assert cases[0].expected == "Hello"
    assert cases[1].name == "French"


def test_load_from_json(tmp_path):
    json_file = tmp_path / "data.json"
    data = [
        {"name": "test1", "vars": {"lang": "English", "text": "Hola"}, "expected": "Hello"},
        {"name": "test2", "vars": {"x": "1"}},
    ]
    json_file.write_text(json.dumps(data))

    cases = load_cases_from_json(json_file)
    assert len(cases) == 2
    assert cases[0].name == "test1"
    assert cases[0].vars["lang"] == "English"
    assert cases[0].expected == "Hello"
    assert cases[1].expected is None


def test_load_cases_auto_detect_csv(tmp_path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("name,x\ntest,1\n")
    cases = load_cases(csv_file)
    assert len(cases) == 1


def test_load_cases_auto_detect_json(tmp_path):
    json_file = tmp_path / "data.json"
    json_file.write_text('[{"name": "t", "vars": {"x": "1"}}]')
    cases = load_cases(json_file)
    assert len(cases) == 1


def test_load_cases_unsupported(tmp_path):
    txt_file = tmp_path / "data.txt"
    txt_file.write_text("hello")
    try:
        load_cases(txt_file)
        assert False, "Should have raised"
    except ValueError as e:
        assert ".txt" in str(e)
