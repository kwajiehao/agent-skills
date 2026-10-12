"""Read-only behavior probe; run with -B to avoid bytecode output."""
import json
import subprocess
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
old_source = subprocess.check_output(["git", "show", "3646c5a141d310d990ebbb9cf062c67156968290:greeting.py"], cwd=repo, text=True)
new_source = (repo / "greeting.py").read_text()
old_scope, new_scope = {}, {}
exec(compile(old_source, "base:greeting.py", "exec"), old_scope)
exec(compile(new_source, "working:greeting.py", "exec"), new_scope)
cases = [
    ("plain", "Ada", "Hello, Ada!"),
    ("padded", "  Ada  ", "Hello, Ada!"),
    ("tabs/newlines", "\tAda\n", "Hello, Ada!"),
    ("empty", "", "Hello, !"),
    ("blank", " \t\n", "Hello, !"),
    ("interior", "Ada  Lovelace", "Hello, Ada  Lovelace!"),
    ("case", "aDa", "Hello, aDa!"),
    ("unicode", "\u2003Ada\u00a0", "Hello, Ada!"),
]
results = []
for label, value, expected in cases:
    before, after = old_scope["greet"](value), new_scope["greet"](value)
    assert after == expected, (label, after, expected)
    results.append({"case": label, "input": value, "before": before, "after": after, "passed": True})
for value in (None, 42):
    before = old_scope["greet"](value)
    try:
        new_scope["greet"](value)
    except AttributeError as error:
        results.append({"input": value, "before": before, "after_exception": type(error).__name__, "passed": True})
    else:
        raise AssertionError("Expected AttributeError for non-string fixture input")
print(json.dumps({"status": "passed", "string_cases": 8, "boundary_cases": 2, "results": results}, indent=2))
