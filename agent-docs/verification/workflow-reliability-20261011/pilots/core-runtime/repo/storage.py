import json
from os import PathLike
from pathlib import Path
from typing import TypeAlias, cast


JSONValue: TypeAlias = (
    str | int | float | bool | None | list["JSONValue"] | dict[str, "JSONValue"]
)


def save_value(path: str | PathLike[str], value: JSONValue) -> None:
    Path(path).write_text(json.dumps(value), encoding="utf-8")


def load_value(path: str | PathLike[str]) -> JSONValue:
    try:
        content = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    return cast(JSONValue, json.loads(content))
