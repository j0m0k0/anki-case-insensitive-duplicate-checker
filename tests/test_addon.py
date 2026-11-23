"""Integration-style tests for the native duplicate-state hooks."""
from __future__ import annotations

import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class Hook(list):
    pass


class FakeAction:
    def __init__(self, _text, _parent):
        self._checked = False
        self.toggled = types.SimpleNamespace(connect=lambda callback: setattr(self, "_toggle", callback))

    def setCheckable(self, _value):
        pass

    def setChecked(self, value):
        self._checked = value

    def isChecked(self):
        return self._checked


class FakeDatabase:
    def __init__(self):
        self.rows = [(12, "agony\x1fdefinition")]

    def all(self, _query, mid):
        return self.rows if mid == 7 else []


class FakeAddonManager:
    def __init__(self):
        self.config = {"enabled": True}

    def getConfig(self, _name):
        return self.config

    def writeConfig(self, _name, config):
        self.config = config


class FakeMenu:
    def addAction(self, _action):
        pass


class FakeMainWindow:
    def __init__(self):
        self.addonManager = FakeAddonManager()
        self.form = types.SimpleNamespace(menuTools=FakeMenu())
        self.col = types.SimpleNamespace(db=FakeDatabase())


class FakeNote:
    def __init__(self, col=None, *, mid=7, fields=None, id=0):
        self.col = col
        self.mid = mid
        self.fields = list(fields or [])
        self.id = id

    def fields_check(self):
        return 0


class FakeProtoNote:
    def __init__(self):
        self.notetype_id = 0
        self.fields = []
        self.id = 0

    def ParseFromString(self, payload):
        parsed = json.loads(payload.decode())
        self.notetype_id = parsed["notetype_id"]
        self.fields = parsed["fields"]
        self.id = parsed["id"]


class FakeProtoResponse:
    NORMAL = 0
    DUPLICATE = 2

    def __init__(self):
        self.state = 0

    def ParseFromString(self, payload):
        self.state = json.loads(payload.decode())["state"]

    def SerializeToString(self):
        return json.dumps({"state": self.state}).encode()


class FakeHttpResponse:
    status_code = 200

    def __init__(self, data=b'{"state": 0}'):
        self.data = data

    def get_data(self):
        return self.data

    def set_data(self, data):
        self.data = data


class AddonIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        anki = types.ModuleType("anki")
        anki.__path__ = []
        note_result = types.SimpleNamespace(NORMAL=0, DUPLICATE=2)
        anki_notes = types.ModuleType("anki.notes")
        anki_notes.Note = FakeNote
        anki_notes.NoteFieldsCheckResult = note_result
        anki.notes = anki_notes
        anki.notes_pb2 = types.SimpleNamespace(
            Note=FakeProtoNote, NoteFieldsCheckResponse=FakeProtoResponse
        )

        aqt = types.ModuleType("aqt")
        aqt.mw = FakeMainWindow()
        aqt.gui_hooks = types.SimpleNamespace(operation_did_execute=Hook())
        aqt.mediasrv = types.SimpleNamespace(
            post_handlers={"noteFieldsCheck": lambda: FakeHttpResponse()}
        )
        qt = types.ModuleType("aqt.qt")
        qt.QAction = FakeAction
        utils = types.ModuleType("aqt.utils")
        utils.tooltip = lambda _message: None
        flask = types.ModuleType("flask")
        flask.Response = FakeHttpResponse
        flask.request = types.SimpleNamespace(get_data=lambda: b"")
        aqt.qt = qt
        aqt.utils = utils
        package_name = "_case_dupchecker_test"
        spec = importlib.util.spec_from_file_location(
            package_name,
            ROOT / "__init__.py",
            submodule_search_locations=[str(ROOT)],
        )
        module = importlib.util.module_from_spec(spec)
        modules = {
            "anki": anki,
            "anki.notes": anki_notes,
            "aqt": aqt,
            "aqt.qt": qt,
            "aqt.utils": utils,
            "flask": flask,
            package_name: module,
        }
        cls._module_patcher = patch.dict(sys.modules, modules)
        cls._module_patcher.start()
        spec.loader.exec_module(module)
        cls.addon = module
        cls.aqt = aqt

    @classmethod
    def tearDownClass(cls):
        cls._module_patcher.stop()

    def setUp(self):
        self.addon.checker._index.clear()
        self.addon.mw.col.db.rows = [(12, "agony\x1fdefinition")]
        self.addon.mw.addonManager.config["enabled"] = True

    def test_case_variant_promotes_to_native_duplicate_state(self):
        self.assertTrue(self.addon.checker.has_case_variant(7, "Agony", None))

    def test_same_case_is_left_to_native_checker(self):
        self.assertFalse(self.addon.checker.has_case_variant(7, "agony", None))

    def test_other_note_types_do_not_match(self):
        self.assertFalse(self.addon.checker.has_case_variant(99, "Agony", None))

    def test_current_note_is_excluded(self):
        self.assertFalse(self.addon.checker.has_case_variant(7, "Agony", 12))

    def test_legacy_note_check_returns_anki_duplicate_state(self):
        note = FakeNote(mid=7, fields=["Agony"], id=0)
        result = note.fields_check()
        self.assertEqual(result, 2)

    def test_modern_endpoint_returns_anki_duplicate_state(self):
        request_data = json.dumps(
            {"notetype_id": 7, "fields": ["Agony"], "id": 0}
        ).encode()
        self.aqt.mediasrv.post_handlers["noteFieldsCheck"] = lambda: FakeHttpResponse()
        import flask
        flask.request.get_data = lambda: request_data
        self.addon.checker._patch_modern_editor_check()
        response = self.aqt.mediasrv.post_handlers["noteFieldsCheck"]()
        result = FakeProtoResponse()
        result.ParseFromString(response.get_data())
        self.assertEqual(result.state, FakeProtoResponse.DUPLICATE)

    def test_toggle_persists_and_disables_extra_check(self):
        self.addon.checker.set_enabled(False)
        self.assertFalse(self.addon.mw.addonManager.config["enabled"])
        self.assertFalse(self.addon.checker.has_case_variant(7, "Agony", None))
        self.addon.checker.set_enabled(True)
        self.assertTrue(self.addon.mw.addonManager.config["enabled"])


if __name__ == "__main__":
    unittest.main()
