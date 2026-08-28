import tempfile
import unittest
from pathlib import Path
from unittest import mock


class BootstrapTests(unittest.TestCase):
    def test_install_safety_accepts_exact_baseline_and_rejects_audited_change(self):
        from scripts.library_v5.bootstrap import assert_install_safe

        baseline = {"data/library/works.csv": "aaa", "data/library/evidence.csv": "bbb"}
        assert_install_safe(baseline, dict(baseline), force_destructive=False)
        changed = dict(baseline)
        changed["data/library/evidence.csv"] = "ccc"
        with self.assertRaisesRegex(RuntimeError, "bootstrap_install_refused"):
            assert_install_safe(baseline, changed, force_destructive=False)
        assert_install_safe(baseline, changed, force_destructive=True)

    def test_default_bootstrap_stages_candidate_without_touching_canonical(self):
        from scripts.library_v5.bootstrap import bootstrap
        from scripts.library_v5.canonical_guard import canonical_hashes

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            library = root / "data/library"
            library.mkdir(parents=True)
            (library / "schema.json").write_text("{}", encoding="utf-8")
            (library / "works.csv").write_text("canonical", encoding="utf-8")
            before = canonical_hashes(root)

            def fake_reconstruct(repo_root, stage_root):
                out = stage_root / "library"
                out.mkdir(parents=True, exist_ok=True)
                (out / "works.csv").write_text("candidate", encoding="utf-8")
                (out / "schema.json").write_text("{}", encoding="utf-8")
                return {"works": 1}

            with mock.patch("scripts.library_v5.bootstrap._reconstruct_to", side_effect=fake_reconstruct):
                result = bootstrap(root)

            self.assertEqual(before, canonical_hashes(root))
            self.assertEqual((root / "data/migration/bootstrap/library/works.csv").read_text(), "candidate")
            self.assertFalse(result["installed_canonical"])

    def test_bootstrap_repeated_candidate_manifest_is_deterministic(self):
        from scripts.library_v5.bootstrap import candidate_manifest

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = root / "data/migration/bootstrap/library"
            stage.mkdir(parents=True)
            (stage / "a.csv").write_text("x\n", encoding="utf-8")
            first = candidate_manifest(root)
            second = candidate_manifest(root)
            self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
