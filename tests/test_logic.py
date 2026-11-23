import unittest
from types import SimpleNamespace

from logic import (
    DuplicateIndex,
    case_variant_matches,
    get_note_fields,
    make_note_key,
    split_note_fields,
    visible_text,
)


class DuplicateLogicTests(unittest.TestCase):
    def test_english_case_variants_match(self):
        expected = "agony"
        for value in ("agony", "Agony", "aGony", "AGONY"):
            with self.subTest(value=value):
                self.assertEqual(make_note_key(value), expected)

    def test_unicode_casefold(self):
        self.assertEqual(make_note_key("Straße"), make_note_key("STRASSE"))

    def test_canonical_unicode_normalization(self):
        self.assertEqual(make_note_key("é"), make_note_key("e\u0301"))

    def test_html_is_removed_and_entities_decoded(self):
        self.assertEqual(make_note_key("<b>Agony</b> &amp; fear"), "agony & fear")
        self.assertEqual(visible_text("&amp;lt;"), "&lt;")

    def test_whitespace_remains_significant(self):
        self.assertNotEqual(make_note_key(" agony"), make_note_key("agony"))
        self.assertEqual(make_note_key("   "), "   ")

    def test_html_text_extractor(self):
        self.assertEqual(visible_text("one<br>two<div>three</div>"), "one\ntwothree")
        self.assertEqual(visible_text('<img src="cat.png">cat'), "cat.pngcat")

    def test_database_fields_split(self):
        self.assertEqual(split_note_fields("front\x1fback"), ["front", "back"])

    def test_editor_note_info_object_and_dict(self):
        self.assertEqual(get_note_fields(SimpleNamespace(fields=["a", "b"])), ["a", "b"])
        self.assertEqual(get_note_fields({"fields": ["x"]}), ["x"])

    def test_index_loads_once_and_clears(self):
        index = DuplicateIndex()
        calls = []
        loader = lambda: calls.append(True) or {"agony": [(1, "agony", "agony")]}
        index.for_notetype(10, loader)
        index.for_notetype(10, loader)
        self.assertEqual(len(calls), 1)
        index.clear()
        index.for_notetype(10, loader)
        self.assertEqual(len(calls), 2)

    def test_case_variants_report_but_exact_matches_do_not(self):
        entries = {"agony": [(1, "agony", "agony"), (2, "agony", "AGONY")]}
        self.assertEqual(case_variant_matches(entries, "agony", "Agony"), ["agony", "AGONY"])
        self.assertEqual(case_variant_matches(entries, "agony", "agony"), ["AGONY"])

    def test_current_note_is_excluded(self):
        entries = {"agony": [(4, "agony", "Agony")]}
        self.assertEqual(case_variant_matches(entries, "agony", "agony", 4), [])

    def test_markup_only_difference_is_not_a_case_variant(self):
        entries = {"agony": [(4, "agony", "<b>agony</b>")]}
        self.assertEqual(case_variant_matches(entries, "agony", "agony", None), [])


if __name__ == "__main__":
    unittest.main()
