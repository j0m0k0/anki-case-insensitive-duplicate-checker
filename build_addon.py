"""Build an installable Anki .ankiaddon archive using only the standard library."""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "dist" / "Case-Insensitive-Duplicate-Checker.ankiaddon"
ADDON_FILES = ("__init__.py", "logic.py", "config.json", "manifest.json")


def build() -> Path:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(OUTPUT, "w", ZIP_DEFLATED) as archive:
        for filename in ADDON_FILES:
            source = ROOT / filename
            if not source.is_file():
                raise FileNotFoundError(source)
            archive.write(source, filename)
    return OUTPUT


if __name__ == "__main__":
    print(build())
