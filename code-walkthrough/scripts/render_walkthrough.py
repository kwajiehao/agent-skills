#!/usr/bin/env python3
"""Render structured code walkthrough data into a single local HTML file."""

from __future__ import annotations

import argparse
import html
import importlib.util
import json
from pathlib import Path


DATA_TOKEN = "__WALKTHROUGH_DATA__"
TITLE_TOKEN = "__WALKTHROUGH_TITLE__"
KIND = "code"

# Load the bundled helper without depending on another installed skill.
_spec = importlib.util.spec_from_file_location(
    "code_walkthrough_library", Path(__file__).with_name("walkthrough_library.py")
)
assert _spec and _spec.loader
library = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(library)


def render(
    data_path: Path,
    output_path: Path | None,
    template_path: Path,
    library_path: Path | None = None,
) -> Path:
    data = json.loads(data_path.expanduser().read_text(encoding="utf-8"))
    root = library.library_root(library_path)
    output_path = (output_path.expanduser() if output_path is not None
                   else library.default_output(data, KIND, root))
    if output_path.resolve().parent == root:
        raise ValueError("The library root is reserved for the gallery; use an artifact folder")
    template = template_path.read_text(encoding="utf-8")

    if DATA_TOKEN not in template or TITLE_TOKEN not in template:
        raise ValueError("template is missing a required replacement token")

    title = str(data.get("meta", {}).get("title", "Code walkthrough"))
    encoded = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    encoded = encoded.replace("</", "<\\/")
    rendered = template.replace(TITLE_TOKEN, html.escape(title)).replace(DATA_TOKEN, encoded)

    library.atomic_write(output_path, rendered)
    library.register(data, output_path, KIND, root)
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True, help="walkthrough JSON")
    parser.add_argument("--output", type=Path, help="output HTML; default: an artifact folder in ~/.agents/walkthroughs")
    parser.add_argument("--library-root", type=Path, help="override the shared walkthrough library root")
    parser.add_argument(
        "--template",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "assets" / "walkthrough-template.html",
        help="HTML template override",
    )
    args = parser.parse_args()

    output = render(args.data, args.output, args.template, args.library_root)
    print(f"Rendered walkthrough: {output.resolve()}")
    root = library.library_root(args.library_root)
    if output.resolve().is_relative_to(root):
        print(f"Walkthrough gallery: {root / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
