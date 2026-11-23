# AnkiWeb publishing notes

## Upload details

- **Title:** Case-Insensitive Duplicate Checker
- **Target version:** Anki 26.09.4; list it as supported after the final in-app check
- **Description:** Makes Anki's duplicate check case-insensitive for the first field of a note. For example, `agony`, `Agony`, `aGony`, and `AGONY` are treated as duplicates. Uses Anki's existing duplicate highlight and **Show Duplicates** control, with no extra editor UI. Toggle it from **Tools → Case-Insensitive Duplicate Checker**. Checks notes of the same note type. Desktop Anki only.
- **Source code:** Optional. No GitHub remote is configured for this local repository.
- **Install file:** `dist/Case-Insensitive-Duplicate-Checker.ankiaddon`

## Upload steps

1. Build with `python build_addon.py`.
2. Sign in to AnkiWeb and open [Shared Add-ons](https://ankiweb.net/shared/addons).
3. Choose **Upload**, select the `.ankiaddon` file, and submit the title and description above.
4. Install the uploaded add-on through AnkiWeb on a clean Anki profile and verify the duplicate field highlight before announcing compatibility.

The builder packages only the four required root files, so local `__pycache__`, tests, and the repository folder are excluded from the upload archive as required by AnkiWeb.

## Release checklist

- Confirm the native duplicate highlight in Anki 26.09.4 on a clean profile.
- Check both the modern and legacy Add windows if available.
- Confirm **Tools → Case-Insensitive Duplicate Checker** disables and re-enables the behavior.
- Rebuild the archive after any source changes.
- Update the AnkiWeb listing's supported-version text when another Anki version has been checked.
