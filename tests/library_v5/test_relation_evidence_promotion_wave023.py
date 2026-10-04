from __future__ import annotations

import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def rows(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        result = []
        for line_number, row in enumerate(reader, 2):
            if len(row) != len(header):
                raise AssertionError(f"{path}:{line_number}: malformed CSV row")
            result.append(dict(zip(header, row)))
        return result


class RelationEvidencePromotionWave023Tests(unittest.TestCase):
    # Mutations caught: lost review/evidence provenance or accidental strengthening
    # of an existing relation, including its variant and indirect-lore boundaries.
    def assert_promoted(self, source_work, target_work, kind, scope, directness,
                        note, token, provenance):
        fact = f"work-relation-{source_work}-{target_work}-{kind.replace('_', '-')}"
        matches = [r for r in rows("data/library/work_relations.csv")
                   if r["work_relation_id"] == fact]
        self.assertEqual(len(matches), 1)
        self.assertEqual(tuple(matches[0][key] for key in (
            "source_work_id", "target_work_id", "relation_kind", "relation_scope",
            "directness", "continuity_scope", "certainty", "verification_status", "notes")),
            (source_work, target_work, kind, scope, directness, "same_or_intended",
             "probable", "source_verified", note))
        sources = rows("data/library/sources.csv")
        evidence = rows("data/library/evidence.csv")
        evidence_ids = []
        for evidence_id, source_id, url in provenance:
            source_matches = [r for r in sources if r["source_id"] == source_id]
            self.assertEqual(len(source_matches), 1)
            self.assertEqual(source_matches[0]["url"], url)
            self.assertEqual(sum(r["url"] == url for r in sources), 1)
            evidence_matches = [r for r in evidence if r["evidence_id"] == evidence_id]
            self.assertEqual(len(evidence_matches), 1)
            self.assertEqual(tuple(evidence_matches[0][key] for key in (
                "fact_table", "fact_id", "source_id", "evidence_role", "verified_at")),
                ("work_relations.csv", fact, source_id, "primary", "2026-10-05"))
            evidence_ids.append(evidence_id)
        reviews = [r for r in rows("data/content_audit/reviews.csv")
                   if r["review_id"] == f"review-2026-10-05-{token}-wave023"]
        self.assertEqual(len(reviews), 1)
        self.assertEqual(tuple(reviews[0][key] for key in (
            "fact_table", "fact_id", "previous_verification_status",
            "new_verification_status", "review_action", "evidence_ids", "reviewed_at")),
            ("work_relations.csv", fact, "legacy_seed", "source_verified",
             "verified_source", "|".join(evidence_ids), "2026-10-05"))

    def test_carol_endgame_crossover_has_two_exact_primary_sources(self):
        self.assert_promoted(
            "captain-marvel-2019", "avengers-endgame-2019", "crossover", "story", "direct",
            "キャロルが『エンドゲーム』でアベンジャーズ側へ合流。", "captain-marvel-endgame",
            (("evidence-captain-marvel-endgame-appearance-wave023",
              "disney-captain-marvel-endgame-appearance-2019",
              "https://thewaltdisneycompany.com/news/captain-marvel-crosses-1-billion-worldwide/"),
             ("evidence-captain-marvel-endgame-avengers-thanos-wave023",
              "disneyplus-carol-danvers-avengers-thanos-2023",
              "https://press.disneyplus.com/news/next-on-disney-plus-november-2023")))

    def test_loki_starting_branch_is_verified_without_identity_rewrite(self):
        self.assert_promoted(
            "avengers-endgame-2019", "loki-s1-2021", "story_link", "story", "direct",
            "『エンドゲーム』の2012年タイム強奪でロキがテッセラクトを奪った分岐から始まる。",
            "endgame-loki",
            (("evidence-endgame-loki-2012-tesseract-wave023",
              "disney-loki-production-brief-2021",
              "https://lumiere-a.akamaihd.net/v1/documents/loki_production_brief_6-1-21_e2911727.pdf"),))

    def test_secret_invasion_retains_indirect_lore_not_a_direct_sequel(self):
        self.assert_promoted(
            "captain-marvel-2019", "secret-invasion-2023", "world_lore", "world_lore", "indirect",
            "フューリー、タロス、スクラル問題を『キャプテン・マーベル』から引き継ぐ。",
            "captain-marvel-secret-invasion",
            (("evidence-captain-marvel-secret-invasion-production-brief-wave023",
              "disney-secret-invasion-production-brief-2023",
              "https://lumiere-a.akamaihd.net/v1/documents/secret_invasion_production_brief_final_6-08-23_66_367af151.pdf"),))


if __name__ == "__main__":
    unittest.main()
