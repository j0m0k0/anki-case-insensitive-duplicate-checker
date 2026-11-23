# Case-Insensitive Duplicate Checker

Makes Anki's existing duplicate checker case-insensitive for the first field of a note. If `agony` exists, entering `Agony`, `aGony`, or `AGONY` is reported using Anki's own duplicate field highlight and **Show Duplicates** control. The add-on adds no duplicate warning, button, or other editor element.

## Install and toggle

Build the `.ankiaddon` archive with `python build_addon.py`, then in Anki choose **Tools → Add-ons → Install from file**, select the generated file in `dist/`, and restart. Toggle the behavior with **Tools → Case-Insensitive Duplicate Checker**. When disabled, Anki's duplicate checking works normally.

## Scope

Checks the first field within the same note type, strips HTML, and applies Unicode case folding and NFC normalization. Exact spelling duplicates remain handled by Anki. The note currently being edited is excluded. Works with Anki desktop on Windows, macOS, and Linux. Anki add-ons do not run on AnkiMobile or AnkiDroid.

## Test and build

```sh
python -m unittest discover -s tests -v
python build_addon.py
```

The build writes `dist/Case-Insensitive-Duplicate-Checker.ankiaddon`. No third-party Python packages are required. The GitHub Actions workflow runs the tests and packaging check on Windows, macOS, and Linux.

## Compatibility

Targets Anki 26.09 and later, supporting both the modern and legacy desktop note editors. It reports case-only matches through Anki's native duplicate status, so Anki controls the editor appearance.

## License

Licensed under the GNU Affero General Public License v3.0 or any later version (AGPL-3.0-or-later). See [LICENSE](LICENSE).
