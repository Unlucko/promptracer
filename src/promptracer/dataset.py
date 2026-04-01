"""Load test inputs from CSV/JSON files for batch evaluation."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from promptracer.batch import Case


def load_cases_from_csv(path: str | Path, name_col: str = "name") -> list[Case]:
    """Load test cases from a CSV file.

    Each row becomes a Case. Column headers become variable names.
    One column can be designated as the case name (default: "name").

    Example CSV:
        name,lang,text,expected
        Spanish,English,Hola mundo,Hello world
        French,English,Bonjour,Hello
    """
    path = Path(path)
    cases = []
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            case_name = row.pop(name_col, None) or f"case-{i + 1}"
            expected = row.pop("expected", None)
            criteria = row.pop("criteria", None)
            cases.append(
                Case(
                    name=case_name,
                    vars={k: v for k, v in row.items() if v is not None},
                    expected=expected,
                    criteria=criteria,
                )
            )
    return cases


def load_cases_from_json(path: str | Path) -> list[Case]:
    """Load test cases from a JSON file.

    Expected format:
        [
            {"name": "test1", "vars": {"lang": "English", "text": "Hola"}, "expected": "Hello"},
            {"name": "test2", "vars": {"lang": "Spanish", "text": "Hello"}}
        ]
    """
    path = Path(path)
    data = json.loads(path.read_text())

    cases = []
    for i, item in enumerate(data):
        if isinstance(item, dict):
            cases.append(
                Case(
                    name=item.get("name", f"case-{i + 1}"),
                    vars=item.get("vars", {}),
                    expected=item.get("expected"),
                    criteria=item.get("criteria"),
                )
            )
    return cases


def load_cases(path: str | Path) -> list[Case]:
    """Auto-detect format and load cases from CSV or JSON."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return load_cases_from_csv(path)
    elif suffix in (".json", ".jsonl"):
        return load_cases_from_json(path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}. Use .csv or .json")
