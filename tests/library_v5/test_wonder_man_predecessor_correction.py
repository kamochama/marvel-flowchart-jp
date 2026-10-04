from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from tests.library_v5.selection_audit_oracle import SelectionAuditOracle

ROOT = Path(__file__).resolve().parents[2]
SOURCE = "shang-chi-and-the-legend-of-the-ten-rings-2021"
TARGET = "wonder-man-s1-2026"
FACT = f"work-relation-{SOURCE}-{TARGET}-story-link"
SOURCE_ID = "disneyplus-wonder-man-trevor-continuation-2026"
EVIDENCE = "evidence-shang-chi-wonder-man-trevor-continuation-2026"
REVIEW = "review-2026-10-05-shang-chi-wonder-man-created"


def rows(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class WonderManPredecessorCorrectionTests(unittest.TestCase):
    def test_exact_new_story_link_has_primary_created_verified_provenance(self) -> None:
        relations = [r for r in rows("data/library/work_relations.csv") if r["work_relation_id"] == FACT]
        self.assertEqual(len(relations), 1)
        self.assertEqual(relations[0], dict(zip((
            "work_relation_id", "source_work_id", "target_work_id", "relation_kind",
            "relation_scope", "directness", "continuity_scope", "certainty", "verification_status", "notes"
        ), (FACT, SOURCE, TARGET, "story_link", "story", "indirect", "same_or_intended", "probable",
            "source_verified", "公式Disney+がトレヴァーのターローでの冒険を経てワンダーマンでハリウッドへ戻る流れを説明。直接続編とは断定しない。"))))
        sources = [r for r in rows("data/library/sources.csv") if r["source_id"] == SOURCE_ID]
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]["url"], "https://www.disneyplus.com/en-sg/explore/articles/marvels-wonder-man")
        evidence = [r for r in rows("data/library/evidence.csv") if r["evidence_id"] == EVIDENCE]
        self.assertEqual(len(evidence), 1)
        self.assertEqual(tuple(evidence[0][k] for k in ("fact_table", "fact_id", "source_id", "evidence_role")),
                         ("work_relations.csv", FACT, SOURCE_ID, "primary"))
        reviews = [r for r in rows("data/content_audit/reviews.csv") if r["review_id"] == REVIEW]
        self.assertEqual(len(reviews), 1)
        self.assertEqual(tuple(reviews[0][k] for k in ("fact_table", "fact_id", "previous_verification_status",
                                                     "new_verification_status", "review_action", "evidence_ids")),
                         ("work_relations.csv", FACT, "", "source_verified", "created_verified", EVIDENCE))

    def test_wonder_man_selection_lights_the_intermediate_trevor_chain(self) -> None:
        payload = json.loads((ROOT / "data/derived/flowchart.json").read_text(encoding="utf-8"))
        oracle = SelectionAuditOracle(payload)
        chain = {
            "iron-man-3-2013->all-hail-the-king-2014",
            f"all-hail-the-king-2014->{SOURCE}",
            f"{SOURCE}->{TARGET}",
        }
        for tier in ("site-proposal", "complete"):
            with self.subTest(tier=tier):
                self.assertTrue(chain <= oracle.expected_main_selection(TARGET, tier=tier).back_edges)
        target_edges = [r for r in payload["edges"] if r["target_work_id"] == TARGET]
        self.assertEqual([(r["source_work_id"], r["target_work_id"]) for r in target_edges], [(SOURCE, TARGET)])
        reasons = [r for r in payload["reasons"] if r["target_work_id"] == TARGET]
        self.assertEqual(len(reasons), 1)
        self.assertEqual(reasons[0]["relation_id"], FACT)
        self.assertEqual(reasons[0]["reason_kind"], "explicit_relation")


if __name__ == "__main__":
    unittest.main()
