"""Case-Insensitive Duplicate Checker for Anki."""
from __future__ import annotations

import json
import logging
from collections.abc import Callable

from anki import gui_hooks
from aqt import mw
from aqt.qt import QAction, QTimer
from aqt.utils import tooltip

from .logic import (
    DuplicateIndex,
    case_variant_matches,
    get_note_fields,
    make_note_key,
    split_note_fields,
)

ADDON_NAME = __name__
log = logging.getLogger(__name__)

_DEFAULT_CONFIG = {"enabled": True, "poll_interval_ms": 500}


def _config() -> dict:
    config = mw.addonManager.getConfig(ADDON_NAME) or {}
    return {**_DEFAULT_CONFIG, **config}


class DuplicateChecker:
    """Adds an independent live warning to Anki's note editor."""

    def __init__(self) -> None:
        self._index = DuplicateIndex()
        self._editors: dict[int, tuple[object, QTimer]] = {}
        self._action: QAction | None = None

        action = QAction("Case-Insensitive Duplicate Checker", mw)
        action.setCheckable(True)
        action.setChecked(bool(_config()["enabled"]))
        action.toggled.connect(self.set_enabled)
        mw.form.menuTools.addAction(action)
        self._action = action

        gui_hooks.editor_did_init.append(self._on_editor_init)
        gui_hooks.operation_did_execute.append(self._on_operation)
        self._update_all_editors()

    def set_enabled(self, enabled: bool) -> None:
        config = _config()
        config["enabled"] = bool(enabled)
        mw.addonManager.writeConfig(ADDON_NAME, config)
        if self._action and self._action.isChecked() != bool(enabled):
            self._action.setChecked(bool(enabled))
        self._update_all_editors()
        tooltip("Case-insensitive duplicate checking " + ("on" if enabled else "off"))

    def _on_editor_init(self, editor: object) -> None:
        # NewEditor exposes get_note_info(); old editor implementations are
        # intentionally ignored instead of patching private editor internals.
        if not callable(getattr(editor, "get_note_info", None)):
            return
        web = getattr(editor, "web", None)
        if web is None:
            return

        key = id(editor)
        prior = self._editors.pop(key, None)
        if prior:
            prior[1].stop()
            prior[1].deleteLater()

        timer = QTimer(mw)
        timer.setInterval(max(200, int(_config()["poll_interval_ms"])))
        timer.timeout.connect(lambda ed=editor: self._poll_editor(ed))
        self._editors[key] = (editor, timer)
        widget = getattr(editor, "widget", None)
        destroyed = getattr(widget, "destroyed", None)
        if destroyed is not None:
            destroyed.connect(lambda _obj=None, editor_key=key: self._cleanup_editor(editor_key))
        if _config()["enabled"]:
            self._install_message_ui(editor)
            timer.start()

    def _cleanup_editor(self, key: int) -> None:
        entry = self._editors.pop(key, None)
        if entry:
            entry[1].stop()
            entry[1].deleteLater()

    def _on_operation(self, changes: object, _handler: object) -> None:
        # Any note-changing operation can affect the duplicate index. Clear it
        # lazily; the next check rebuilds only the active note type's entries.
        if getattr(changes, "note", False):
            self._index.clear()

    def _update_all_editors(self) -> None:
        enabled = bool(_config()["enabled"])
        for editor, timer in list(self._editors.values()):
            if enabled:
                self._install_message_ui(editor)
                if not timer.isActive():
                    timer.start()
            else:
                timer.stop()
                self._set_message(editor, "")

    def _install_message_ui(self, editor: object) -> None:
        web = getattr(editor, "web", None)
        if web is None:
            return
        script = """(() => {
          if (window.caseInsensitiveDuplicateCheckerReady) return;
          window.caseInsensitiveDuplicateCheckerReady = true;
          const style = document.createElement('style');
          style.textContent = '#case-insensitive-duplicate-checker{position:fixed;left:8px;right:8px;bottom:8px;z-index:2147483000;padding:7px 10px;border:1px solid #d98200;border-radius:5px;background:#fff4d6;color:#352400;font:13px sans-serif;box-shadow:0 2px 8px #0003;display:none;}';
          document.head.appendChild(style);
          const box = document.createElement('div');
          box.id = 'case-insensitive-duplicate-checker';
          box.setAttribute('role', 'status');
          document.body.appendChild(box);
          window.caseInsensitiveDuplicateCheckerSetMessage = (message) => {
            box.textContent = message;
            box.style.display = message ? 'block' : 'none';
          };
        })();"""
        try:
            web.eval(script)
        except Exception:
            log.debug("Could not install duplicate warning in editor", exc_info=True)

    def _set_message(self, editor: object, message: str) -> None:
        web = getattr(editor, "web", None)
        if web is None:
            return
        try:
            web.eval(
                "window.caseInsensitiveDuplicateCheckerSetMessage && "
                "window.caseInsensitiveDuplicateCheckerSetMessage("
                + json.dumps(message)
                + ");"
            )
        except Exception:
            log.debug("Could not update duplicate warning", exc_info=True)

    def _poll_editor(self, editor: object) -> None:
        if not _config()["enabled"] or not mw.col:
            return
        get_note_info: Callable = getattr(editor, "get_note_info", None)
        if not callable(get_note_info):
            return

        def on_info(note_info: object) -> None:
            try:
                fields = get_note_fields(note_info)
                mid = int(getattr(note_info, "mid"))
                nid = getattr(note_info, "id", None)
                message = self._duplicate_message(mid, fields, nid)
            except Exception:
                log.debug("Duplicate check failed", exc_info=True)
                message = ""
            self._set_message(editor, message)

        try:
            get_note_info(on_info)
        except Exception:
            log.debug("Could not read editor fields", exc_info=True)

    def _duplicate_message(self, mid: int, fields: list[str], current_nid: int | None) -> str:
        if not fields or not fields[0]:
            return ""
        candidate = fields[0]
        key = make_note_key(candidate)
        if not key.strip():
            return ""

        entries = self._index.for_notetype(mid, lambda: self._load_notetype(mid))
        matches = case_variant_matches(entries, key, candidate, current_nid)
        if not matches:
            return ""

        shown = ", ".join(repr(text) for text in matches[:3])
        remainder = len(matches) - min(3, len(matches))
        if remainder:
            shown += f" and {remainder} more"
        return f"Case-insensitive duplicate: {shown}"

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
