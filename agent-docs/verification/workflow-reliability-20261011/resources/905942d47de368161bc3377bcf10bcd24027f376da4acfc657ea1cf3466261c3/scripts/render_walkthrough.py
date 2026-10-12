#!/usr/bin/env python3
"""Render structured PR walkthrough data into a single local HTML file."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


DATA_TOKEN = "__WALKTHROUGH_DATA__"
TITLE_TOKEN = "__WALKTHROUGH_TITLE__"


def render(data_path: Path, output_path: Path, template_path: Path) -> None:
    data = json.loads(data_path.read_text(encoding="utf-8"))
    template = template_path.read_text(encoding="utf-8")

    if DATA_TOKEN not in template or TITLE_TOKEN not in template:
        raise ValueError("template is missing a required replacement token")

    title = str(data.get("meta", {}).get("title", "PR walkthrough"))
    encoded = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    encoded = encoded.replace("</", "<\\/")
    rendered = template.replace(TITLE_TOKEN, html.escape(title)).replace(DATA_TOKEN, encoded)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True, help="walkthrough JSON")
    parser.add_argument("--output", type=Path, required=True, help="output HTML")
    parser.add_argument(
        "--template",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "assets" / "walkthrough-template.html",
        help="HTML template override",
    )
    args = parser.parse_args()

    render(args.data, args.output, args.template)
    print(f"Rendered walkthrough: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
