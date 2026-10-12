# Durable JSON values

`save_value(path, value)` saves a JSON-compatible value at a caller-selected file.
`load_value(path)` returns that value, or `None` when the path is missing.
Data must remain readable after the saving process exits.

Tests: `python3 -m unittest discover -s tests -v`.
