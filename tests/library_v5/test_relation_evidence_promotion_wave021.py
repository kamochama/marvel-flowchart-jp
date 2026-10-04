from __future__ import annotations

import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def rows(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class RelationEvidencePromotionWave021Tests(unittest.TestCase):
    def test_story_continuations_have_exact_primary_provenance_and_unchanged_meaning(self) -> None:
        cases = (
            ("avengers-endgame-2019", "the-falcon-and-the-winter-soldier-2021", "direct",
             "サムが盾を託された『エンドゲーム』を直接受けるシリーズ。", "endgame-fatws",
             (("disney-fatws-production-brief-2021", "https://lumiere-a.akamaihd.net/v1/documents/the_falcon_and_the_winter_soldier_production_brief_fina_875edcc9.pdf", "production-brief"),)),
            ("captain-america-civil-war-2016", "spider-man-homecoming-2017", "direct",
             "ピーターのアベンジャーズ参加経験を受けて『ホームカミング』が始まる。", "civil-war-homecoming",
             (("sony-homecoming-civil-war-story-2017", "https://www.sonypictures.com/movies/spidermanhomecoming", "synopsis"),)),
            ("the-falcon-and-the-winter-soldier-2021", "captain-america-brave-new-world-2025", "strong",
             "Sam Wilson's Captain America arc.", "fatws-brave-new-world",
             (("disney-brave-new-world-sam-mantle-2024", "https://thewaltdisneycompany.com/news/captain-america-brave-new-world-teaser-trailer/", "teaser"),
              ("disney-brave-new-world-story-continuation-2025", "https://thewaltdisneycompany.com/news/captain-america-brave-new-world-producer-interview/", "producer"))),
        )
        relations = rows("data/library/work_relations.csv")
        sources = rows("data/library/sources.csv")
        evidences = rows("data/library/evidence.csv")
        reviews = rows("data/content_audit/reviews.csv")
        for source_work, target_work, directness, note, token, source_cases in cases:
            fact = f"work-relation-{source_work}-{target_work}-story-link"
            with self.subTest(fact=fact):
                matches = [r for r in relations if r["work_relation_id"] == fact]
                self.assertEqual(len(matches), 1)
                self.assertEqual(tuple(matches[0][k] for k in (
                    "source_work_id", "target_work_id", "relation_kind", "relation_scope",
                    "directness", "continuity_scope", "certainty", "verification_status", "notes")),
                    (source_work, target_work, "story_link", "story", directness,
                     "same_or_intended", "probable", "source_verified", note))
                evidence_ids = []
                for source_id, url, suffix in source_cases:
                    source_rows = [r for r in sources if r["source_id"] == source_id]
                    self.assertEqual(len(source_rows), 1)
                    self.assertEqual(source_rows[0]["url"], url)
                    evidence_id = f"evidence-{token}-{suffix}-wave021"
                    evidence_ids.append(evidence_id)
                    evidence_rows = [r for r in evidences if r["evidence_id"] == evidence_id]
                    self.assertEqual(len(evidence_rows), 1)
                    self.assertEqual(tuple(evidence_rows[0][k] for k in (
                        "fact_table", "fact_id", "source_id", "evidence_role")),
                        ("work_relations.csv", fact, source_id, "primary"))
                review_rows = [r for r in reviews if r["review_id"] == f"review-2026-10-04-{token}-wave021"]
                self.assertEqual(len(review_rows), 1)
                self.assertEqual(tuple(review_rows[0][k] for k in (
                    "fact_table", "fact_id", "previous_verification_status", "new_verification_status", "review_action")),
                    ("work_relations.csv", fact, "legacy_seed", "source_verified", "verified_source"))
                self.assertEqual(set(review_rows[0]["evidence_ids"].split("|")), set(evidence_ids))


if __name__ == "__main__":
    unittest.main()
