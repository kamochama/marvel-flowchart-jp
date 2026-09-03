from __future__ import annotations

import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"
AUDIT = ROOT / "data" / "content_audit"
DERIVED = ROOT / "data" / "derived"

RELATIONS = {
    "work-relation-doctor-strange-2016-doctor-strange-in-the-multiverse-of-madness-2022-sequel": (
        "doctor-strange-2016", "doctor-strange-in-the-multiverse-of-madness-2022",
        "disney-doctor-strange-second-film-2019", "evidence-doctor-strange-multiverse-sequel-disney-2019",
        "review-2026-09-03-doctor-strange-multiverse-sequel", "sequel", "story", "direct", "same_or_intended", "confirmed",
    ),
    "work-relation-black-panther-wakanda-forever-2022-ironheart-2025-spinoff": (
        "black-panther-wakanda-forever-2022", "ironheart-2025",
        "disney-ironheart-wakanda-forever-followup-2022", "evidence-wakanda-forever-ironheart-followup-disney-2022",
        "review-2026-09-03-ironheart-wakanda-forever-spinoff", "spinoff", "story", "strong", "same_or_intended", "probable",
    ),
    "work-relation-what-if-s1-2021-marvel-zombies-s1-2025-spinoff": (
        "what-if-s1-2021", "marvel-zombies-s1-2025",
        "disney-what-if-s1-marvel-zombies-spinoff-2025", "evidence-what-if-s1-marvel-zombies-spinoff-disney-2025",
        "review-2026-09-03-what-if-s1-marvel-zombies-spinoff", "spinoff", "story", "strong", "same_or_intended", "probable",
    ),
    "work-relation-i-am-groot-s1-2022-i-am-groot-s2-2023-sequel": (
        "i-am-groot-s1-2022", "i-am-groot-s2-2023",
        "marvel-i-am-groot-s1-s2-continuation-2023", "evidence-i-am-groot-s1-s2-continuation-marvel-2023",
        "review-2026-09-03-i-am-groot-s1-s2-sequel", "sequel", "story", "strong", "same_or_intended", "probable",
    ),
}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class RelationEvidencePromotionWave008Tests(unittest.TestCase):
    def test_four_relations_have_source_verified_evidence_and_reviews(self) -> None:
        relations = {r["work_relation_id"]: r for r in rows(LIB / "work_relations.csv")}
        sources = {r["source_id"]: r for r in rows(LIB / "sources.csv")}
        evidence = rows(LIB / "evidence.csv")
        reviews = rows(AUDIT / "reviews.csv")
        urls = {
            "disney-doctor-strange-second-film-2019": "https://thewaltdisneycompany.com/news/marvel-studios-reveals-plans-for-phase-four-at-san-diego-comic-con/",
            "disney-ironheart-wakanda-forever-followup-2022": "https://thewaltdisneycompany.com/news/lucasfilm-marvel-studios-and-20th-century-studios-showcase-electrifying-new-slate-at-d23-expo-2022/",
            "disney-what-if-s1-marvel-zombies-spinoff-2025": "https://thewaltdisneycompany.com/news/marvel-animation-2025-sneak-peek/",
            "marvel-i-am-groot-s1-s2-continuation-2023": "https://www.marvel.com/tv-shows/i-am-groot/1?mobile-app=true&theme=falseCampfire",
        }
        for source_id, url in urls.items():
            self.assertEqual(sources[source_id]["url"], url)
        for rid, (src, dst, sid, eid, review_id, relation_kind, relation_scope, directness, continuity_scope, certainty) in RELATIONS.items():
            row = relations[rid]
            self.assertEqual(row["verification_status"], "source_verified")
            self.assertEqual(
                (row["source_work_id"], row["target_work_id"], row["relation_kind"], row["relation_scope"], row["directness"], row["continuity_scope"], row["certainty"]),
                (src, dst, relation_kind, relation_scope, directness, continuity_scope, certainty),
            )
            ev = [r for r in evidence if r["evidence_id"] == eid]
            self.assertEqual(len(ev), 1)
            self.assertEqual((ev[0]["fact_table"], ev[0]["fact_id"], ev[0]["source_id"], ev[0]["evidence_role"]), ("work_relations.csv", rid, sid, "primary"))
            rv = [r for r in reviews if r["review_id"] == review_id]
            self.assertEqual(len(rv), 1)
            self.assertEqual((rv[0]["fact_table"], rv[0]["fact_id"], rv[0]["previous_verification_status"], rv[0]["new_verification_status"], rv[0]["review_action"], rv[0]["evidence_ids"]), ("work_relations.csv", rid, "legacy_seed", "source_verified", "verified_source", eid))

    def test_existing_pairs_and_reason_ids_are_preserved(self) -> None:
        edges = rows(DERIVED / "work_edges_all.csv")
        reasons = rows(DERIVED / "work_pair_reasons.csv")
        self.assertEqual((len(edges), len(reasons)), (355, 562))
        for rid, (src, dst, *_rest) in RELATIONS.items():
            edge = next(r for r in edges if r["source_work_id"] == src and r["target_work_id"] == dst)
            expected = f"reason-{src}-{dst}-explicit-relation-{rid}"
            self.assertIn(expected, edge["reason_ids"])
            reason = [r for r in reasons if r["reason_kind"] == "explicit_relation" and r["relation_id"] == rid]
            self.assertEqual(len(reason), 1)
            self.assertEqual((reason[0]["verification_statuses"], reason[0]["source_work_id"], reason[0]["target_work_id"]), ("source_verified", src, dst))


if __name__ == "__main__":
    unittest.main()
