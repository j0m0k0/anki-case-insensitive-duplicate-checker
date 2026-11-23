"""Integration-style tests for add-on wiring using small Anki GUI stubs."""
from __future__ import annotations

import importlib.util
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


class FakeTimer:
    def __init__(self, _parent):
        self.timeout = types.SimpleNamespace(connect=lambda _callback: None)
        self.active = False

    def setInterval(self, _value):
        pass

    def start(self):
        self.active = True

    def stop(self):
        self.active = False

    def isActive(self):
        return self.active

    def deleteLater(self):
        pass


class FakeDatabase:
    def __init__(self):
        self.rows = [(12, "agony\x1fdefinition"), (13, "AGONY\x1fother")]

    def all(self, _query, mid):
        return self.rows if mid == 7 else []


class FakeAddonManager:
    def __init__(self):
        self.config = {"enabled": True, "poll_interval_ms": 500}

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


class AddonIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        anki = types.ModuleType("anki")
        anki.gui_hooks = types.SimpleNamespace(
            editor_did_init=Hook(), operation_did_execute=Hook()
        )
        aqt = types.ModuleType("aqt")
        aqt.mw = FakeMainWindow()
        qt = types.ModuleType("aqt.qt")
        qt.QAction = FakeAction
        qt.QTimer = FakeTimer
        utils = types.ModuleType("aqt.utils")
        utils.tooltip = lambda _message: None
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
            "aqt": aqt,
            "aqt.qt": qt,
            "aqt.utils": utils,
            package_name: module,
        }
        cls._module_patcher = patch.dict(sys.modules, modules)
        cls._module_patcher.start()
        spec.loader.exec_module(module)
        cls.addon = module

    @classmethod
    def tearDownClass(cls):
        cls._module_patcher.stop()

    def setUp(self):
        self.addon.checker._index.clear()
        self.addon.mw.col.db.rows = [(12, "agony\x1fdefinition"), (13, "AGONY\x1fother")]

    def test_warns_on_capitalization_variants(self):
        message = self.addon.checker._duplicate_message(7, ["Agony", "gloss"], None)
        self.assertEqual(message, "Case-insensitive duplicate: 'agony', 'AGONY'")

    def test_other_note_types_do_not_match(self):
        message = self.addon.checker._duplicate_message(99, ["Agony"], None)
        self.assertEqual(message, "")

    def test_exact_case_is_left_to_native_checker(self):
        message = self.addon.checker._duplicate_message(7, ["agony"], None)
        self.assertEqual(message, "Case-insensitive duplicate: 'AGONY'")

    def test_current_note_is_excluded(self):
        message = self.addon.checker._duplicate_message(7, ["Agony"], 12)
        self.assertEqual(message, "Case-insensitive duplicate: 'AGONY'")

    def test_toggle_persists_setting(self):
        self.addon.checker.set_enabled(False)
        self.assertFalse(self.addon.mw.addonManager.config["enabled"])
        self.addon.checker.set_enabled(True)
        self.assertTrue(self.addon.mw.addonManager.config["enabled"])


if __name__ == "__main__":
    unittest.main()
