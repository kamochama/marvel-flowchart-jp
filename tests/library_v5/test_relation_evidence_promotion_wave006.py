from __future__ import annotations

import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "library"
AUDIT = ROOT / "data" / "content_audit"
DERIVED = ROOT / "data" / "derived"

RELATIONS = {
    "work-relation-spider-man-across-the-spider-verse-2023-spider-man-beyond-the-spider-verse-tba-sequel": (
        "spider-man-across-the-spider-verse-2023", "spider-man-beyond-the-spider-verse-tba", "sony-spider-verse-trilogy-beyond-2026", "evidence-spider-man-across-beyond-trilogy-sony-2026", "review-2026-09-03-spider-man-across-beyond-trilogy", "confirmed", "strong", "sequel",
    ),
    "work-relation-spider-man-into-the-spider-verse-2018-spider-man-across-the-spider-verse-2023-sequel": (
        "spider-man-into-the-spider-verse-2018", "spider-man-across-the-spider-verse-2023", "sony-spider-man-across-sequel-2024", "evidence-spider-man-into-across-sequel-sony-2024", "review-2026-09-03-spider-man-into-across-sequel", "probable", "direct", "sequel",
    ),
    "work-relation-x-men-the-animated-series-19921997-x-men-97-s1-2024-sequel": (
        "x-men-the-animated-series-19921997", "x-men-97-s1-2024", "marvel-xmen97-original-series-timeline-2022", "evidence-x-men-animated-series-x-men97-s1-timeline-marvel-2022", "review-2026-09-03-x-men-animated-series-xmen97-s1", "probable", "direct", "sequel",
    ),
    "work-relation-spider-man-homecoming-2017-spider-man-far-from-home-2019-sequel": (
        "spider-man-homecoming-2017", "spider-man-far-from-home-2019", "marvel-spider-man-far-from-home-homecoming-series-2019", "evidence-spider-man-homecoming-far-from-home-next-chapter-marvel-2019", "review-2026-09-03-spider-man-homecoming-far-from-home-sequel", "confirmed", "direct", "sequel",
    ),
}

def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))

class RelationEvidencePromotionWave006Tests(unittest.TestCase):
    def test_four_relations_have_source_verified_evidence_and_reviews(self) -> None:
        relations = {r["work_relation_id"]: r for r in rows(LIB / "work_relations.csv")}
        sources = {r["source_id"]: r for r in rows(LIB / "sources.csv")}
        evidence = rows(LIB / "evidence.csv")
        reviews = rows(AUDIT / "reviews.csv")
        urls = {
            "sony-spider-verse-trilogy-beyond-2026": "https://www.sonypicturesanimation.com/about",
            "sony-spider-man-across-sequel-2024": "https://www.sonypictures.com/corp/press_releases/2024/0321",
            "marvel-xmen97-original-series-timeline-2022": "https://www.marvel.com/articles/tv-shows/sdcc-2022-marvel-studios-animation-panel?mobile-app=true&theme=dark",
            "marvel-spider-man-far-from-home-homecoming-series-2019": "https://www.marvel.com/amp/articles/movies/jake-gyllenhaal-on-the-mcu-mysterio",
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
