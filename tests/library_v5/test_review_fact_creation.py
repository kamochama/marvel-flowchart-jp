import unittest


class ReviewFactCreationTests(unittest.TestCase):
    def test_created_verified_fact_is_valid_with_qualifying_evidence(self):
        from scripts.library_v5.content_audit import validate_reviews

        tables = {
            "entity_relations.csv": [{
                "entity_relation_id": "er-new",
                "verification_status": "source_verified",
            }],
        }
        evidence = [{
            "evidence_id": "ev-new",
            "fact_table": "entity_relations.csv",
            "fact_id": "er-new",
            "evidence_role": "supporting",
        }]
        reviews = [{
            "review_id": "review-new",
            "fact_table": "entity_relations.csv",
            "fact_id": "er-new",
            "previous_verification_status": "",
            "new_verification_status": "source_verified",
            "review_action": "created_verified",
            "evidence_ids": "ev-new",
        }]
        self.assertEqual(validate_reviews(tables, evidence, reviews), [])

    def test_created_verified_fact_requires_evidence_reference(self):
        from scripts.library_v5.content_audit import validate_reviews

        tables = {
            "entity_relations.csv": [{
                "entity_relation_id": "er-new",
                "verification_status": "source_verified",
            }],
        }
        reviews = [{
            "review_id": "review-new",
            "fact_table": "entity_relations.csv",
            "fact_id": "er-new",
            "previous_verification_status": "",
            "new_verification_status": "source_verified",
            "review_action": "created_verified",
            "evidence_ids": "",
        }]
        issues = validate_reviews(tables, [], reviews)
        self.assertTrue(any(issue["code"] == "created_verified_without_evidence" for issue in issues))


if __name__ == "__main__":
    unittest.main()
