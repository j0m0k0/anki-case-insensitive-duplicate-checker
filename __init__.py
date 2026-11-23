"""Case-Insensitive Duplicate Checker for Anki."""
from __future__ import annotations

import logging

from anki.notes import Note, NoteFieldsCheckResult
from aqt import gui_hooks, mw
from aqt.qt import QAction
from aqt.utils import tooltip

from .logic import DuplicateIndex, case_variant_note_ids, make_note_key, split_note_fields

ADDON_NAME = __name__
log = logging.getLogger(__name__)

_DEFAULT_CONFIG = {"enabled": True}


def _config() -> dict:
    config = mw.addonManager.getConfig(ADDON_NAME) or {}
    return {**_DEFAULT_CONFIG, **config}


class DuplicateChecker:
    """Promotes case-only matches to Anki's native duplicate state."""

    def __init__(self) -> None:
        self._index = DuplicateIndex()
        self._action: QAction | None = None

        action = QAction("Case-Insensitive Duplicate Checker", mw)
        action.setCheckable(True)
        action.setChecked(bool(_config()["enabled"]))
        action.toggled.connect(self.set_enabled)
        mw.form.menuTools.addAction(action)
        self._action = action

        gui_hooks.operation_did_execute.append(self._on_operation)
        self._patch_note_check()
        self._patch_modern_editor_check()

    def set_enabled(self, enabled: bool) -> None:
        config = _config()
        config["enabled"] = bool(enabled)
        mw.addonManager.writeConfig(ADDON_NAME, config)
        if self._action and self._action.isChecked() != bool(enabled):
            self._action.setChecked(bool(enabled))
        tooltip("Case-insensitive duplicate checking " + ("on" if enabled else "off"))

    def _on_operation(self, changes: object, _handler: object) -> None:
        if getattr(changes, "note", False):
            self._index.clear()

    def _patch_note_check(self) -> None:
        """Use Anki's normal NoteFieldsCheck result in the legacy editor."""
        original = Note.fields_check
        if getattr(original, "_case_insensitive_duplicate_checker", False):
            return

        def fields_check(note: Note):
            result = original(note)
            if result != NoteFieldsCheckResult.NORMAL or not _config()["enabled"]:
                return result
            if self.has_case_variant(note.mid, note.fields[0], note.id):
                return NoteFieldsCheckResult.DUPLICATE
            return result

        fields_check._case_insensitive_duplicate_checker = True  # type: ignore[attr-defined]
        Note.fields_check = fields_check

    def _patch_modern_editor_check(self) -> None:
        """Promote the modern editor's backend response before Anki renders it."""
        try:
            from anki import notes_pb2
            from flask import Response, request
            from aqt import mediasrv

            original = mediasrv.post_handlers.get("noteFieldsCheck")
            if original is None or getattr(
                original, "_case_insensitive_duplicate_checker", False
            ):
                return
        except Exception:
            log.debug("Modern editor duplicate endpoint is unavailable", exc_info=True)
            return

        def note_fields_check():
            request_bytes = request.get_data()
            response = original()
            if not _config()["enabled"] or mw.col is None:
                return response
            try:
                note = notes_pb2.Note()
                note.ParseFromString(request_bytes)
                result = notes_pb2.NoteFieldsCheckResponse()
                result.ParseFromString(response.get_data())
                if result.state != NoteFieldsCheckResult.NORMAL:
                    return response
                if not note.fields or not self.has_case_variant(
                    note.notetype_id, note.fields[0], note.id
                ):
                    return response
                result.state = NoteFieldsCheckResult.DUPLICATE
                response.set_data(result.SerializeToString())
            except Exception:
                log.debug("Could not augment Anki's duplicate check", exc_info=True)
            return response

        note_fields_check._case_insensitive_duplicate_checker = True  # type: ignore[attr-defined]
        mediasrv.post_handlers["noteFieldsCheck"] = note_fields_check

    def has_case_variant(
        self, notetype_id: int, candidate: str, current_note_id: int | None
    ) -> bool:
        if not _config()["enabled"] or mw.col is None:
            return False
        key = make_note_key(candidate)
        if not key.strip():
            return False
        entries = self._index.for_notetype(
            int(notetype_id), lambda: self._load_notetype(int(notetype_id))
        )
        return bool(
            case_variant_note_ids(entries, key, candidate, current_note_id)
        )

    @staticmethod
    def _load_notetype(mid: int) -> dict[str, list[tuple[int, str, str]]]:
        entries: dict[str, list[tuple[int, str, str]]] = {}
        for nid, stored_fields in mw.col.db.all(
            "select id, flds from notes where mid = ?", mid
        ):
            fields = split_note_fields(stored_fields)
            if not fields:
                continue
            original = fields[0]
            key = make_note_key(original)
            if key:
                entries.setdefault(key, []).append((int(nid), key, original))
        return entries


checker = DuplicateChecker()
