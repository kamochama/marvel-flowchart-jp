import unittest


class LegacyExtractionTests(unittest.TestCase):
    def test_extract_char_links_preserves_order_and_deduplicates_exact_rows(self):
        from scripts.library_v5.extract_legacy import extract_char_links

        html = '''<script>const CHAR_LINKS=[
          {"character":"トニー・スターク／アイアンマン","work_id":"iron-man-2008","title_ja":"アイアンマン","title_en":"Iron Man"},
          {"character":"トニー・スターク／アイアンマン","work_id":"the-avengers-2012","title_ja":"アベンジャーズ","title_en":"The Avengers"},
          {"character":"トニー・スターク／アイアンマン","work_id":"iron-man-2008","title_ja":"アイアンマン","title_en":"Iron Man"}
        ]; const X=1;</script>'''
        rows = extract_char_links(html)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["work_id"], "iron-man-2008")
        self.assertEqual(rows[1]["work_id"], "the-avengers-2012")
        self.assertEqual(rows[0]["verification_status"], "legacy_seed")
        self.assertEqual(rows[0]["legacy_source"], "index.html:CHAR_LINKS")

    def test_extract_char_links_rejects_missing_or_wrong_shape(self):
        from scripts.library_v5.extract_legacy import LegacyExtractionError, extract_char_links

        with self.assertRaises(LegacyExtractionError):
            extract_char_links("<script>const OTHER=[];</script>")
        with self.assertRaises(LegacyExtractionError):
            extract_char_links('<script>const CHAR_LINKS={"character":"x"};</script>')
        with self.assertRaises(LegacyExtractionError):
            extract_char_links('<script>const CHAR_LINKS=[{"character":"x"}];</script>')

    def test_extract_entity_returns_preserves_all_legacy_fields(self):
        from scripts.library_v5.extract_legacy import extract_entity_returns

        csv_text = """target_work_id,entity,representative_prior_work_id,evidence,continuity_certainty,source_url\navengers-doomsday-2026-12-18,ソー,thor-love-and-thunder-2022,official return teaser / cast,same_or_intended,https://example.test/doomsday\n"""
        rows = extract_entity_returns(csv_text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["entity"], "ソー")
        self.assertEqual(rows[0]["representative_prior_work_id"], "thor-love-and-thunder-2022")
        self.assertEqual(rows[0]["verification_status"], "legacy_seed")
        self.assertEqual(rows[0]["legacy_source"], "data/entity_returns.csv")


if __name__ == "__main__":
    unittest.main()
