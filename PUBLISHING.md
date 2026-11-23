# AnkiWeb publishing notes

## Upload details

- **Title:** Case-Insensitive Duplicate Checker
- **Target version:** Anki 26.09.4; list it as supported after the final in-app check
- **Description:** Already have `apple` in your deck? If you add `Apple` or `APPLE`, Anki flags it as a duplicate. This add-on makes Anki's duplicate check ignore capitalization in the first field of notes of the same note type. It uses Anki's normal duplicate highlight and **Show Duplicates** control without adding extra editor UI. Toggle it from **Tools → Case-Insensitive Duplicate Checker**. Anki Desktop only.
- **Support Page:** https://github.com/j0m0k0/anki-case-insensitive-duplicate-checker/issues
- **Source code:** https://github.com/j0m0k0/anki-case-insensitive-duplicate-checker
- **Install file:** `dist/Case-Insensitive-Duplicate-Checker.ankiaddon`

## Upload steps

1. Build with `python build_addon.py`.
2. Sign in to AnkiWeb and open [Shared Add-ons](https://ankiweb.net/shared/addons).
3. Choose **Upload**, select the `.ankiaddon` file, and submit the title and description above.
4. Install the uploaded add-on through AnkiWeb on a clean Anki profile and verify the duplicate field highlight before announcing compatibility.

The builder packages only the four required root files, so local `__pycache__`, tests, and the repository folder are excluded from the upload archive as required by AnkiWeb.

## Publish the source on GitHub

The source is licensed under AGPL-3.0-or-later and includes the full license text. To make it public:

1. The public repository is `https://github.com/j0m0k0/anki-case-insensitive-duplicate-checker`.
2. In this project folder, connect it as `origin` and push the existing `main` branch:

   ```sh
   git remote add origin https://github.com/j0m0k0/anki-case-insensitive-duplicate-checker.git
   git push -u origin main
   ```

3. Add the GitHub URL to the AnkiWeb listing so users can review the source, report issues, and contribute.

## Release checklist

- Confirm the native duplicate highlight in Anki 26.09.4 on a clean profile.
- Check both the modern and legacy Add windows if available.
- Confirm **Tools → Case-Insensitive Duplicate Checker** disables and re-enables the behavior.
- Rebuild the archive after any source changes.
- Update the AnkiWeb listing's supported-version text when another Anki version has been checked.
