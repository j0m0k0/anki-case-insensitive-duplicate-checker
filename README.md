# Case-Insensitive Duplicate Checker

Adds a live warning when the first field of a note matches another note of the same note type after ignoring capitalization. For example, `Agony`, `aGony`, and `AGONY` are flagged if `agony` already exists.

## Install and toggle

Build the `.ankiaddon` archive with `python build_addon.py`, then in Anki choose **Tools → Add-ons → Install from file**, select the generated file in `dist/`, and restart. To toggle the extra check, choose **Tools → Case-Insensitive Duplicate Checker**. Anki's own duplicate warning remains unchanged; this add-on adds a separate warning and does not block adding a note.

## Scope

Checks the first field within the same note type, strips HTML, and applies Unicode case folding and NFC normalization. The note currently being edited is excluded. Works with Anki desktop on Windows, macOS, and Linux. Anki add-ons do not run on AnkiMobile or AnkiDroid.

## Test and build

```sh
python -m unittest discover -s tests -v
python build_addon.py
```

The build writes `dist/Case-Insensitive-Duplicate-Checker.ankiaddon`. No third-party Python packages are required. The GitHub Actions workflow runs the tests and packaging check on Windows, macOS, and Linux.

## Compatibility

Targets Anki 26.09 and later, supporting both the modern and legacy desktop note editors. This add-on supplements Anki's native duplicate checker instead of replacing its internal check.
