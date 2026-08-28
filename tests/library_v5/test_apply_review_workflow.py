import unittest
from pathlib import Path


class ApplyReviewWorkflowTests(unittest.TestCase):
    def test_apply_review_workflow_targets_current_forward_branch(self):
        root = Path(__file__).resolve().parents[2]
        workflow = (root / ".github/workflows/library-v5-apply-review-patch.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("      - library-v5-phase2-db6", workflow)
        self.assertIn("          ref: library-v5-phase2-db6", workflow)
        self.assertIn("git push origin HEAD:library-v5-phase2-db6", workflow)
        self.assertNotIn("library-v5-canonical-freeze", workflow)


if __name__ == "__main__":
    unittest.main()
