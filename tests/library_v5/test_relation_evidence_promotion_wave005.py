from __future__ import annotations

import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"
AUDIT = ROOT / "data" / "content_audit"
DERIVED = ROOT / "data" / "derived"

RELATIONS = {
    "work-relation-iron-man-2008-iron-man-2-2010-sequel": (
        "iron-man-2008", "iron-man-2-2010", "paramount-iron-man-2-sequel-2010",
        "evidence-iron-man-iron-man-2-sequel-paramount-2010", "review-2026-09-03-iron-man-iron-man-2-sequel", "confirmed", "direct", "sequel",
    ),
    "work-relation-avengers-infinity-war-2018-avengers-endgame-2019-sequel": (
        "avengers-infinity-war-2018", "avengers-endgame-2019", "disney-infinity-war-endgame-sequel-2019",
        "evidence-infinity-war-endgame-sequel-disney-2019", "review-2026-09-03-infinity-war-endgame-sequel", "probable", "direct", "sequel",
    ),
    "work-relation-daredevil-s1-2015-daredevil-s2-2016-sequel": (
        "daredevil-s1-2015", "daredevil-s2-2016", "disney-daredevil-s1-s2-renewal-2015",
        "evidence-daredevil-s1-s2-sequel-disney-2015", "review-2026-09-03-daredevil-s1-s2-sequel", "confirmed", "direct", "sequel",
    ),
    "work-relation-what-if-s1-2021-what-if-s2-2023-sequel": (
        "what-if-s1-2021", "what-if-s2-2023", "marvel-what-if-s1-s2-continuation-2023",
        "evidence-what-if-s1-s2-sequel-marvel-2023", "review-2026-09-03-what-if-s1-s2-sequel", "probable", "strong", "sequel",
    ),
    "work-relation-loki-s1-2021-loki-s2-2023-sequel": (
        "loki-s1-2021", "loki-s2-2023", "marvel-loki-s1-s2-continuation-2023",
        "evidence-loki-s1-s2-sequel-marvel-2023", "review-2026-09-03-loki-s1-s2-sequel", "confirmed", "direct", "sequel",
    ),
}

def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))

class RelationEvidencePromotionWave005Tests(unittest.TestCase):
    def test_five_relations_have_source_verified_evidence_and_reviews(self) -> None:
        relations = {r["work_relation_id"]: r for r in rows(LIB / "work_relations.csv")}
        sources = {r["source_id"]: r for r in rows(LIB / "sources.csv")}
        evidence = rows(LIB / "evidence.csv")
        reviews = rows(AUDIT / "reviews.csv")
        urls = {
            "paramount-iron-man-2-sequel-2010": "https://ir.paramount.com/news-releases/news-release-details/marvel-entertainment-and-paramount-pictures-iron-man-2-be",
            "disney-infinity-war-endgame-sequel-2019": "https://thewaltdisneycompany.com/app/uploads/2019/03/Disney_Investor_Day_2019_transcript.pdf",
            "disney-daredevil-s1-s2-renewal-2015": "https://investors.thewaltdisneycompany.com/files/doc_events/2015/05/q2-fy15-earnings-transcript.pdf",
            "marvel-what-if-s1-s2-continuation-2023": "https://www.marvel.com/articles/tv-shows/marvel-studios-animation-what-if-season-2",
            "marvel-loki-s1-s2-continuation-2023": "https://www.marvel.com/articles/tv-shows/loki-tom-hiddleston-tva-family?cid=EML_Newsletter_2023106_WeeklyPulse_Story1",
        }
        for source_id, url in urls.items(): self.assertEqual(sources[source_id]["url"], url)
        for rid, (src, dst, sid, eid, review_id, certainty, directness, kind) in RELATIONS.items():
            row = relations[rid]
            self.assertEqual(row["verification_status"], "source_verified")
            self.assertEqual((row["source_work_id"], row["target_work_id"], row["relation_kind"], row["certainty"], row["directness"]), (src, dst, kind, certainty, directness))
            ev = [r for r in evidence if r["evidence_id"] == eid]
            self.assertEqual(len(ev), 1); self.assertEqual((ev[0]["fact_table"], ev[0]["fact_id"], ev[0]["source_id"], ev[0]["evidence_role"]), ("work_relations.csv", rid, sid, "primary"))
            rv = [r for r in reviews if r["review_id"] == review_id]
            self.assertEqual(len(rv), 1); self.assertEqual((rv[0]["fact_table"], rv[0]["fact_id"], rv[0]["previous_verification_status"], rv[0]["new_verification_status"], rv[0]["review_action"], rv[0]["evidence_ids"]), ("work_relations.csv", rid, "legacy_seed", "source_verified", "verified_source", eid))

    def test_existing_pairs_and_reason_ids_are_preserved(self) -> None:
        edges = rows(DERIVED / "work_edges_all.csv"); reasons = rows(DERIVED / "work_pair_reasons.csv")
        self.assertEqual((len(edges), len(reasons)), (355, 562))
        for rid, (src, dst, *_rest) in RELATIONS.items():
            edge = next(r for r in edges if r["source_work_id"] == src and r["target_work_id"] == dst)
            expected = f"reason-{src}-{dst}-explicit-relation-{rid}"
            self.assertIn(expected, edge["reason_ids"])
            reason = [r for r in reasons if r["reason_kind"] == "explicit_relation" and r["relation_id"] == rid]
            self.assertEqual(len(reason), 1); self.assertEqual((reason[0]["verification_statuses"], reason[0]["source_work_id"], reason[0]["target_work_id"]), ("source_verified", src, dst))

if __name__ == "__main__": unittest.main()
