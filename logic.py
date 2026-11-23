"""Pure helper functions used by the add-on and its tests."""
from __future__ import annotations

import unicodedata
from collections.abc import Callable
from html.parser import HTMLParser
from threading import RLock
from typing import Any


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "img":
            source = next((value for name, value in attrs if name.lower() == "src"), None)
            if source:
                self.parts.append(source)
        elif tag == "br":
            self.parts.append("\n")


def visible_text(value: str) -> str:
    """Return text comparable to Anki's HTML-stripped first-field check."""
    parser = _TextExtractor()
    try:
        parser.feed(value)
        parser.close()
        return "".join(parser.parts)
    except Exception:
        # Malformed pasted HTML should not make the add-on fail.
        return value


def make_note_key(value: str) -> str:
    """Normalize a first field for case-insensitive matching.

    Unicode NFC normalization makes canonically equivalent text compare
    consistently; casefold handles Unicode case mappings more fully than lower.
    Whitespace remains significant, matching Anki's native duplicate rule.
    """
    return unicodedata.normalize("NFC", visible_text(value)).casefold()


def split_note_fields(stored_fields: str) -> list[str]:
    """Split Anki's unit-separator-delimited database field string."""
    return stored_fields.split("\x1f")


def get_note_fields(note_info: Any) -> list[str]:
    """Read field values from the modern editor's NoteInfo object or dict."""
    fields = (
        note_info.get("fields", [])
        if isinstance(note_info, dict)
        else getattr(note_info, "fields", [])
    )
    return list(fields or [])


def case_variant_matches(
    entries: dict[str, list[tuple[int, str, str]]],
    key: str,
    candidate: str,
    current_note_id: int | None = None,
) -> list[str]:
    """Return capitalization variants, excluding the current or exact note."""
    candidate_text = visible_text(candidate)
    return [
        text
        for note_id, _normalized, text in entries.get(key, [])
        if note_id != current_note_id and visible_text(text) != candidate_text
    ]


def case_variant_note_ids(
    entries: dict[str, list[tuple[int, str, str]]],
    key: str,
    candidate: str,
    current_note_id: int | None = None,
) -> list[int]:
    """Return IDs for capitalization variants, excluding the current/exact note."""
    candidate_text = visible_text(candidate)
    return [
        note_id
        for note_id, _normalized, text in entries.get(key, [])
        if note_id != current_note_id and visible_text(text) != candidate_text
    ]


class DuplicateIndex:
    """Lazy per-note-type cache of normalized first-field values."""

    def __init__(self) -> None:
        self._entries: dict[int, dict[str, list[tuple[int, str, str]]]] = {}
        self._lock = RLock()

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def for_notetype(
        self,
        notetype_id: int,
        loader: Callable[[], dict[str, list[tuple[int, str, str]]]],
    ) -> dict[str, list[tuple[int, str, str]]]:
        with self._lock:
            if notetype_id not in self._entries:
                self._entries[notetype_id] = loader()
            return self._entries[notetype_id]
