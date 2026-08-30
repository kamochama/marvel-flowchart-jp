from pathlib import Path
import csv
import hashlib
import json
import re
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX_HTML = REPO_ROOT / "index.html"
PREWATCH_POLICY = REPO_ROOT / "data" / "prewatch_policy.json"
OFFICIAL_PREWATCH_ROUTES = REPO_ROOT / "data" / "prewatch_official_routes.json"
PREWATCH_RULES = REPO_ROOT / "data" / "rules.csv"
DATA_README = REPO_ROOT / "data" / "README.md"
DATA_MANIFEST = REPO_ROOT / "data" / "manifest.json"
FLOWCHART_EXPORT = REPO_ROOT / "data" / "derived" / "flowchart.json"


class WatchScrollNavigationContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = INDEX_HTML.read_text(encoding="utf-8")

    def test_watch_view_keeps_chart_in_document_flow(self) -> None:
        """Opening the plan must not hide the chart needed for upward scrolling."""
        self.assertNotRegex(
            self.html,
            re.compile(
                r"body\.public-watch-view\s+main\s*\{\s*display\s*:\s*none",
                re.IGNORECASE,
            ),
        )
        self.assertRegex(
            self.html,
            re.compile(
                r"body\.public-watch-view\s+main\s*\{\s*display\s*:\s*grid",
                re.IGNORECASE,
            ),
        )

    def test_watch_and_chart_have_scroll_navigation_hooks(self) -> None:
        self.assertIn("watchWorkspace.scrollIntoView", self.html)
        self.assertIn("window.returnToGraphFromWatch", self.html)

    def test_chart_scope_exposes_full_and_previous1_only(self) -> None:
        """The chart viewer has one full view and one direct-predecessor view."""
        scope = re.search(
            r'<div class="control-group control-scope">.*?</div>',
            self.html,
            re.DOTALL,
        )
        self.assertIsNotNone(scope)
        scope_text = scope.group(0)
        self.assertIn('data-scope="all"', scope_text)
        self.assertIn('data-scope="previous1"', scope_text)
        self.assertIn("1つ前のみ", scope_text)
        self.assertNotIn('data-scope="two"', scope_text)
        self.assertNotIn("2段階", scope_text)

    def test_previous1_scope_follows_incoming_edges_only(self) -> None:
        """The one-step chart mode must not light outgoing neighbours."""
        self.assertIn("function directPredecessorPart(id)", self.html)
        previous = re.search(
            r"function directPredecessorPart\(id\)\{.*?\n\s*\}",
            self.html,
            re.DOTALL,
        )
        self.assertIsNotNone(previous)
        self.assertIn("inc[id]", previous.group(0))
        self.assertNotIn("out[id]", previous.group(0))

    def test_user_facing_plan_uses_site_proposal_route(self) -> None:
        """Curated fallback wording should describe the site's proposal, not editing work."""
        self.assertIn("サイト提案ルート", self.html)
        self.assertNotIn("監査済み編集ルート", self.html)

    def test_html_hides_minimum_and_two_stage_choices(self) -> None:
        """Legacy minimum/two-stage values stay internal, but are not offered in HTML controls."""
        tier_select = re.search(
            r'<select id="watchConnectionTier".*?</select>',
            self.html,
            re.DOTALL,
        )
        self.assertIsNotNone(tier_select)
        self.assertNotIn('value="minimum"', tier_select.group(0))
        self.assertNotIn("最低限", tier_select.group(0))
        self.assertNotIn("2段階", self.html)

    def test_preparation_selector_exposes_official_site_and_complete_modes(self) -> None:
        """The watch planner exposes the three user-facing route choices."""
        tier_select = re.search(
            r'<select id="watchConnectionTier".*?</select>',
            self.html,
            re.DOTALL,
        )
        self.assertIsNotNone(tier_select)
        self.assertEqual(
            re.findall(r'<option value="([^"]+)"', tier_select.group(0)),
            ["official", "site-proposal", "complete"],
        )
        self.assertIn("公式予習ルート", tier_select.group(0))
        self.assertIn("サイト提案ルート", tier_select.group(0))
        self.assertIn("完全版", tier_select.group(0))

    def test_mobile_overlay_restoration_uses_public_selection_state(self) -> None:
        """Global mobile helpers must not reach into the core module's local cache."""
        restore = re.search(
            r"function restoreMobileSelectionOverlayIfNeeded\(.*?\n\}",
            self.html,
            re.DOTALL,
        )
        self.assertIsNotNone(restore)
        self.assertNotIn("selectionStateCache", restore.group(0))
        self.assertIn("window.__marvelLastSelectionState", restore.group(0))

    def test_minimum_plan_is_direct_core_only(self) -> None:
        """The provisional minimum tier must not fall back to a recursive plan."""
        minimum = re.search(
            r"if\(prepTier==='minimum'\)\{.*?return \{ids,source:",
            self.html,
            re.DOTALL,
        )
        self.assertIsNotNone(minimum)
        self.assertIn("directCore", minimum.group(0))
        self.assertNotIn("recIds", minimum.group(0))

    def test_path_mode_exposes_both_route_preferences(self) -> None:
        """The PATH explanation must have the controls it tells users to use."""
        self.assertRegex(
            self.html,
            re.compile(
                r'class="path-pref-btn active"[^>]+data-path-pref="main"',
                re.IGNORECASE,
            ),
        )
        self.assertRegex(
            self.html,
            re.compile(
                r'class="path-pref-btn"[^>]+data-path-pref="shortest"',
                re.IGNORECASE,
            ),
        )

    def test_recommended_plan_exposes_official_provenance_boundary(self) -> None:
        """Curated routes must not be presented as an official prewatch list."""
        self.assertIn("PUBLIC v5.20.7", self.html)
        self.assertIn("OFFICIAL_PREWATCH_ROUTES_V57", self.html)
        self.assertIn("chooseOfficialPrewatchRoute", self.html)
        self.assertIn("provenance:'official'", self.html)
        self.assertIn("provenance:'curated'", self.html)
        self.assertIn("公式予習リスト未登録", self.html)
        self.assertNotIn("監査済み推奨ルート上", self.html)
        self.assertIn("data-prep-provenance", self.html)

    def test_official_route_registry_contains_audited_thunderbolts_route(self) -> None:
        registry = json.loads(OFFICIAL_PREWATCH_ROUTES.read_text(encoding="utf-8"))
        self.assertEqual(registry["schema_version"], "1")
        route = next(
            row
            for row in registry["routes"]
            if row["route_id"] == "official-disneyplus-thunderbolts-2025"
        )
        self.assertEqual(route["target_work_id"], "thunderbolts-new-avengers-2025")
        self.assertEqual(
            route["ids"],
            [
                "black-widow-2021",
                "the-falcon-and-the-winter-soldier-2021",
                "hawkeye-2021",
                "thunderbolts-new-avengers-2025",
            ],
        )
        self.assertEqual(
            route["source_url"],
            "https://www.disneyplus.com/explore/articles/thunderbolts-movie",
        )
        self.assertEqual(route["verification_status"], "source_verified")
        self.assertIn("official_prewatch_routes", self.html)

    def test_official_plan_has_distinct_provenance_badge_and_source_link(self) -> None:
        self.assertIn("prep-provenance-badge", self.html)
        self.assertIn('data-prep-provenance="official"', self.html)
        self.assertIn("sourceUrlByGoal", self.html)
        self.assertIn("公式出典", self.html)

    def test_official_route_order_is_preserved_before_graph_expansion(self) -> None:
        self.assertIn("officialRouteIds", self.html)
        self.assertIn("routeOrdered", self.html)

    def test_official_route_can_highlight_existing_chart_edges(self) -> None:
        self.assertIn("official-route-highlight", self.html)
        self.assertIn("toggleOfficialRouteHighlight", self.html)
        self.assertIn("officialRouteEdges", self.html)
        self.assertIn("公式予習ルートをチャートで光らせる", self.html)
        self.assertIn("data-official-route-toggle", self.html)

    def test_detail_focus_redraw_preserves_official_route_highlight(self) -> None:
        self.assertIn(
            "window.marvelApplyOfficialRouteSvgOverlay?.(svg,window.__marvelLastSelectionState)",
            self.html,
        )

    def test_static_export_carries_the_official_route_in_view_policy(self) -> None:
        payload = json.loads(FLOWCHART_EXPORT.read_text(encoding="utf-8"))
        routes = payload["view_policy"]["official_prewatch_routes"]
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0]["route_id"], "official-disneyplus-thunderbolts-2025")
        self.assertEqual(routes[0]["ids"][-1], routes[0]["target_work_id"])

    def test_data_policy_matches_provisional_tiered_ui_semantics(self) -> None:
        """The documented policy must match the current provisional UI contract."""
        policy = json.loads(PREWATCH_POLICY.read_text(encoding="utf-8"))
        minimum = policy["modes"]["minimum"]
        recommended = policy["modes"]["recommended"]

        self.assertEqual(minimum["algorithm"], "direct_core_edges")
        self.assertEqual(minimum.get("recursive_tiers", []), [])
        self.assertIn("再帰", minimum["description"])
        self.assertIn("行わない", minimum["description"])

        self.assertEqual(
            recommended["algorithm"],
            "official_route_or_curated_fallback_plus_core",
        )
        self.assertIn("official", recommended["provenance"])
        self.assertIn("curated", recommended["provenance"])
        self.assertEqual(recommended["expansion_waves"], 0)

        with PREWATCH_RULES.open(encoding="utf-8-sig", newline="") as handle:
            rules = list(csv.DictReader(handle))
        by_no = {row["rule_no"]: row for row in rules}
        self.assertEqual(by_no["14"]["management_value"], "minimum-direct-core")
        self.assertEqual(
            by_no["15"]["management_value"],
            "official-route-or-curated-fallback-plus-core",
        )
        self.assertIn("再帰探索しない", by_no["14"]["meaning"])

        readme = DATA_README.read_text(encoding="utf-8")
        self.assertIn("最低限: ゴールへ直接入る中核接続のみ（再帰なし）", readme)
        self.assertIn("公式予習リストが未登録なら監査済み編集ルートを代替表示", readme)

        manifest = json.loads(DATA_MANIFEST.read_text(encoding="utf-8"))
        for manifest_name, path in (
            ("README.md", DATA_README),
            ("prewatch_policy.json", PREWATCH_POLICY),
            ("prewatch_official_routes.json", OFFICIAL_PREWATCH_ROUTES),
            ("rules.csv", PREWATCH_RULES),
        ):
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(manifest["files"][manifest_name], digest)


if __name__ == "__main__":
    unittest.main()
