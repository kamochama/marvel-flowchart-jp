from __future__ import annotations

import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"
AUDIT = ROOT / "data" / "content_audit"
DERIVED = ROOT / "data" / "derived"

RELATIONS = {
    "work-relation-the-amazing-spider-man-2012-the-amazing-spider-man-2-2014-sequel": (
        "the-amazing-spider-man-2012", "the-amazing-spider-man-2-2014", "sony-amazing-spider-man-1-2-sequel-2013", "evidence-amazing-spider-man-1-2-sequel-sony-2013", "review-2026-09-03-amazing-spider-man-1-2-sequel", "confirmed",
    ),
    "work-relation-spider-man-far-from-home-2019-spider-man-no-way-home-2021-sequel": (
        "spider-man-far-from-home-2019", "spider-man-no-way-home-2021", "sony-spider-man-homecoming-third-film-2020", "evidence-spider-man-far-from-home-no-way-home-sequel-sony-2020", "review-2026-09-03-spider-man-far-from-home-no-way-home-sequel", "confirmed",
    ),
    "work-relation-deadpool-2016-deadpool-2-2018-sequel": (
        "deadpool-2016", "deadpool-2-2018", "twentieth-deadpool2-sequel-2018", "evidence-deadpool-deadpool2-sequel-twentieth-2018", "review-2026-09-03-deadpool-deadpool2-sequel", "confirmed",
    ),
    "work-relation-captain-marvel-2019-the-marvels-2023-sequel": (
        "captain-marvel-2019", "the-marvels-2023", "disney-the-marvels-captain-marvel-sequel-2023", "evidence-captain-marvel-the-marvels-sequel-disney-2023", "review-2026-09-03-captain-marvel-the-marvels-sequel", "probable",
    ),
}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class RelationEvidencePromotionWave007Tests(unittest.TestCase):
    def test_four_relations_have_source_verified_evidence_and_reviews(self) -> None:
        relations = {r["work_relation_id"]: r for r in rows(LIB / "work_relations.csv")}
        sources = {r["source_id"]: r for r in rows(LIB / "sources.csv")}
        evidence = rows(LIB / "evidence.csv")
        reviews = rows(AUDIT / "reviews.csv")
        urls = {
            "sony-amazing-spider-man-1-2-sequel-2013": "https://www.sonypictures.com/corp/press_releases/2013/02_13/020513_spiderman2.html",
            "sony-spider-man-homecoming-third-film-2020": "https://www.sonypictures.com/corp/press_releases/2020/0121",
            "twentieth-deadpool2-sequel-2018": "https://www.20thcenturystudios.com/movies/deadpool-2",
            "disney-the-marvels-captain-marvel-sequel-2023": "https://thewaltdisneycompany.com/news/the-marvels-director-nia-dacosta-on-crafting-a-cosmic-team-up-of-epic-proportions/",
        }
        for source_id, url in urls.items():
            self.assertEqual(sources[source_id]["url"], url)
        for rid, (src, dst, sid, eid, review_id, certainty) in RELATIONS.items():
            row = relations[rid]
            self.assertEqual(row["verification_status"], "source_verified")
            self.assertEqual((row["source_work_id"], row["target_work_id"], row["relation_kind"], row["relation_scope"], row["directness"], row["continuity_scope"], row["certainty"]), (src, dst, "sequel", "story", "direct", "same_or_intended", certainty))
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
