from __future__ import annotations

import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def rows(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class RelationEvidencePromotionWave022Tests(unittest.TestCase):
    def test_three_continuations_have_exact_primary_provenance_and_unchanged_meaning(self) -> None:
        cases = (
            ("captain-america-the-first-avenger-2011", "agent-carter-one-shot-2013", "story_link", "indirect",
             "Peggy Carter continuation.", "first-avenger-agent-carter", "disneyplus-agent-carter-after-first-avenger",
             "https://www.disneyplus.com/ja-jp/browse/entity-5e7f5aa1-b3ea-4cd3-983f-c5cda970fb0a"),
            ("captain-america-civil-war-2016", "black-widow-2021", "aftermath", "direct",
             "『ブラック・ウィドウ』本編は『シビル・ウォー』直後のナターシャを描く。", "civil-war-black-widow",
             "disney-black-widow-after-civil-war-2021",
             "https://lumiere-a.akamaihd.net/v1/documents/black_widow_advance_updated_final_04-29-21_e1222ad3.pdf"),
            ("avengers-endgame-2019", "hawkeye-2021", "aftermath", "indirect",
             "ローニン期とナターシャ喪失を抱えるクリントの後日談。", "endgame-hawkeye",
             "disney-hawkeye-endgame-aftermath-2021",
             "https://lumiere-a.akamaihd.net/v1/documents/hawkeye_production_brief_final_11-04-21_b8718e9c.pdf"),
        )
        relations = rows("data/library/work_relations.csv")
        sources = rows("data/library/sources.csv")
        evidences = rows("data/library/evidence.csv")
        reviews = rows("data/content_audit/reviews.csv")
        for source_work, target_work, kind, directness, note, token, source_id, url in cases:
            fact = f"work-relation-{source_work}-{target_work}-{kind.replace('_', '-')}"
            with self.subTest(fact=fact):
                matches = [r for r in relations if r["work_relation_id"] == fact]
                self.assertEqual(len(matches), 1)
                self.assertEqual(tuple(matches[0][k] for k in (
                    "source_work_id", "target_work_id", "relation_kind", "relation_scope",
                    "directness", "continuity_scope", "certainty", "verification_status", "notes")),
                    (source_work, target_work, kind, "story", directness,
                     "same_or_intended", "probable", "source_verified", note))
                source_rows = [r for r in sources if r["source_id"] == source_id]
                self.assertEqual(len(source_rows), 1)
                self.assertEqual(source_rows[0]["url"], url)
                evidence_id = f"evidence-{token}-primary-wave022"
                evidence_rows = [r for r in evidences if r["evidence_id"] == evidence_id]
                self.assertEqual(len(evidence_rows), 1)
                self.assertEqual(tuple(evidence_rows[0][k] for k in (
                    "fact_table", "fact_id", "source_id", "evidence_role")),
                    ("work_relations.csv", fact, source_id, "primary"))
                review_rows = [r for r in reviews if r["review_id"] == f"review-2026-10-04-{token}-wave022"]
                self.assertEqual(len(review_rows), 1)
                self.assertEqual(tuple(review_rows[0][k] for k in (
                    "fact_table", "fact_id", "previous_verification_status", "new_verification_status", "review_action")),
                    ("work_relations.csv", fact, "legacy_seed", "source_verified", "verified_source"))
                self.assertEqual(review_rows[0]["evidence_ids"], evidence_id)


if __name__ == "__main__":
    unittest.main()
