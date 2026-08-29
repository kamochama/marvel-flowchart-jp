import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = ROOT / "data" / "derived" / "flowchart.json"


class PublicFlowchartArtifactTests(unittest.TestCase):
    def test_public_pages_artifact_is_versioned_and_loadable(self) -> None:
        self.assertTrue(
            ARTIFACT.is_file(),
            "GitHub Pages must receive the static flowchart JSON artifact",
        )
        payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], "1")
        self.assertTrue(payload["nodes"])
        self.assertTrue(payload["edges"])
        self.assertTrue(payload["reasons"])
        self.assertEqual(payload["view_policy"]["default_edge_visibility"], "all")


if __name__ == "__main__":
    unittest.main()
