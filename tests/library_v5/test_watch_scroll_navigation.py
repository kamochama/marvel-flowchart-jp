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

    def test_chart_scope_controls_are_not_public(self) -> None:
        """The public chart no longer exposes a separate lighting-scope selector."""
        self.assertNotIn('class="control-group control-scope"', self.html)
        self.assertNotIn("点灯範囲", self.html)
        self.assertNotIn("関連全体", self.html)
        self.assertNotIn("1つ前のみ", self.html)

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

    def test_readme_describes_the_two_public_modes(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("v5.21.3", readme)
        self.assertIn("サイト提案ルート", readme)
        self.assertIn("完全版", readme)
        self.assertIn("公式予習ルートの登録データ", readme)
        self.assertIn("点灯範囲", readme)

    def test_preparation_selector_exposes_two_public_modes(self) -> None:
        """The watch planner exposes site proposal and complete modes only."""
        tier_select = re.search(
            r'<select id="watchConnectionTier".*?</select>',
            self.html,
            re.DOTALL,
        )
        self.assertIsNotNone(tier_select)
        self.assertEqual(
            re.findall(r'<option value="([^"]+)"', tier_select.group(0)),
            ["site-proposal", "complete"],
        )
        self.assertNotIn("公式予習ルート", tier_select.group(0))
        self.assertIn("サイト提案ルート", tier_select.group(0))
        self.assertIn("完全版", tier_select.group(0))
        self.assertNotIn('value="minimum"', tier_select.group(0))
        self.assertNotIn('value="recommended"', tier_select.group(0))
        self.assertNotIn("2段階", self.html)

    def test_chart_connection_selector_matches_watch_modes(self) -> None:
        """The chart and watch plan expose the same two public tiers."""
        selector = re.search(r'<select id="chartConnectionTier".*?</select>', self.html, re.DOTALL)
        self.assertIsNotNone(selector)
        self.assertEqual(
            re.findall(r'<option value="([^"]+)"', selector.group(0)),
            ["site-proposal", "complete"],
        )
        self.assertIn("document.querySelectorAll('.chart-tier-select')", self.html)
        self.assertIn("window.marvelSetConnectionTier(sel.value)", self.html)
        self.assertNotIn('data-importance-mode="recommended"', selector.group(0))

    def test_official_route_is_not_exposed_by_public_controls(self) -> None:
        """Official provenance stays in data, but route controls are not public UI."""
        self.assertNotIn('<option value="official">公式予習ルート</option>', self.html)
        self.assertNotIn("data-official-route-toggle", self.html)
        self.assertNotIn("公式予習ルートをチャートで光らせる", self.html)

    def test_legacy_official_tier_normalizes_to_site_proposal(self) -> None:
        """Persisted official UI state must not resurrect the removed public mode."""
        normalizer = re.search(
            r"function normalizePreparationTier\(tier\)\{.*?\n\s*\}",
            self.html,
            re.DOTALL,
        )
        self.assertIsNotNone(normalizer)
        self.assertIn("tier==='official'", normalizer.group(0))
        self.assertNotIn("return 'official'", normalizer.group(0))
        self.assertIn("return 'site-proposal'", normalizer.group(0))

    def test_guide_and_tabs_use_a_viewport_sticky_desktop_nav(self) -> None:
        self.assertIn('<div class="public-nav-sticky">', self.html)
        nav_start = self.html.index('<div class="public-nav-sticky">')
        nav_end = self.html.index('<dialog id="publicHelpDialog"', nav_start)
        nav_text = self.html[nav_start:nav_end]
        self.assertIn('class="public-guide"', nav_text)
        self.assertIn('class="tabs"', nav_text)
        header = re.search(r"<header>[\s\S]*?</header>", self.html)
        self.assertIsNotNone(header)
        self.assertNotIn('class="public-guide"', header.group(0))
        self.assertNotIn('class="tabs"', header.group(0))
        main = re.search(r"<main>[\s\S]*?</main>", self.html)
        self.assertIsNotNone(main)
        self.assertNotIn('class="public-guide"', main.group(0))
        self.assertNotIn('class="tabs"', main.group(0))
        self.assertRegex(self.html, r"\.public-nav-sticky\{[^}]*position:sticky[^}]*top:0")
        self.assertIn(".tabs,.public-guide{display:none!important}", self.html)

    def test_flowchart_policy_initializes_chart_importance_without_changing_watch_mode(self) -> None:
        """The exported default importance must not overwrite the watch-plan tier."""
        policy = re.search(
            r"function applyFlowchartPolicy\(policy\)\{.*?\n\s*\}",
            self.html,
            re.DOTALL,
        )
        self.assertIsNotNone(policy)
        policy_text = policy.group(0)
        self.assertIn(
            "window.marvelSetImportanceMode(policy.default_importance_mode)",
            policy_text,
        )
        self.assertNotIn("window.marvelSetConnectionTier(defaultTier)", policy_text)

    def test_complete_mode_has_nonofficial_provenance(self) -> None:
        """Complete mode must not retain an official source URL or official provenance."""
        complete = re.search(
            r"if\(prepTier==='complete'\)\{.*?return \{ids,source:.*?\n\s*\};",
            self.html,
            re.DOTALL,
        )
        self.assertIsNotNone(complete)
        self.assertIn("provenance:'complete'", complete.group(0))
        self.assertIn("sourceUrl:''", complete.group(0))

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

    def test_official_mode_does_not_fallback_to_site_proposal(self) -> None:
        """Official mode must use only a registered official route or show it as unavailable."""
        official = re.search(
            r"function buildOfficialPreparationPlan\(target\)\{.*?return \{\n\s*ids:\[\],",
            self.html,
            re.DOTALL,
        )
        self.assertIsNotNone(official)
        self.assertIn("chooseOfficialPrewatchRoute", official.group(0))
        self.assertIn("公式予習ルートは未登録", self.html)
        self.assertIn("公式予習ルートは未登録", self.html)

    def test_site_proposal_mode_never_uses_official_route(self) -> None:
        """Site proposal mode must be independent from official route registration."""
        site = re.search(
            r"function buildSiteProposalPreparationPlan\(target\)\{.*?\n\}\nfunction buildPreparationPlan",
            self.html,
            re.DOTALL,
        )
        self.assertIsNotNone(site)
        self.assertIn("chooseCuratedRoute", site.group(0))
        self.assertNotIn("chooseOfficialPrewatchRoute", site.group(0))

    def test_complete_mode_uses_graph_recursion_without_route_mixing(self) -> None:
        """Complete mode must not import official/site proposal route IDs as provenance."""
        complete = re.search(
            r"if\(prepTier==='complete'\)\{.*?return \{ids,source:",
            self.html,
            re.DOTALL,
        )
        self.assertIsNotNone(complete)
        self.assertIn("ancestorSetByImportance(target,true)", complete.group(0))
        self.assertNotIn("recIds", complete.group(0))
        self.assertNotIn("buildRecommendedPlan", complete.group(0))

    def test_legacy_plan_values_normalize_to_site_proposal(self) -> None:
        """Old recommended/minimum shared state remains readable as site proposal."""
        self.assertIn(
            "function normalizePreparationTier(tier)",
            self.html,
        )
        self.assertIn("prepTier=normalizePreparationTier(tier)", self.html)
        self.assertIn("Legacy shared-room values map to the explicit site proposal mode", self.html)

    def test_site_proposal_path_filter_excludes_reference_edges(self) -> None:
        """Site proposal explanations stay on core/recommended connections."""
        allowed = re.search(
            r"function prepAllowedEdge\(e\)\{.*?\n\s*\}",
            self.html,
            re.DOTALL,
        )
        self.assertIsNotNone(allowed)
        self.assertIn(
            "prepTier==='site-proposal' || prepTier==='recommended'",
            allowed.group(0),
        )

    def test_official_route_highlight_is_cleared_outside_official_mode(self) -> None:
        """Leaving official mode must remove its chart overlay state."""
        sync = re.search(
            r"function syncOfficialRouteHighlightForGoals\(\)\{.*?\n\s*\}",
            self.html,
            re.DOTALL,
        )
        self.assertIsNotNone(sync)
        self.assertIn("prepTier!=='official'", sync.group(0))
        self.assertIn("officialRouteHighlightEnabled=false", sync.group(0))
        setter = re.search(
            r"window\.marvelSetConnectionTier=function\(tier\)\{.*?\n\s*\};",
            self.html,
            re.DOTALL,
        )
        self.assertIsNotNone(setter)
        self.assertIn("syncOfficialRouteHighlightForGoals();", setter.group(0))

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

    def test_plan_modes_expose_official_and_site_provenance_boundaries(self) -> None:
        """Curated routes must not be presented as an official prewatch list."""
        self.assertIn("PUBLIC v5.21.3", self.html)
        self.assertIn("OFFICIAL_PREWATCH_ROUTES_V57", self.html)
        self.assertIn("chooseOfficialPrewatchRoute", self.html)
        self.assertIn("provenance:'official'", self.html)
        self.assertIn("provenance:'curated'", self.html)
        self.assertIn("公式予習ルートは未登録", self.html)
        self.assertIn("site-proposal", self.html)
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
        self.assertIn("const officialOrder=[]", self.html)
        self.assertIn("const officialRank=new Map(officialOrder", self.html)

    def test_official_route_highlight_implementation_is_internal_only(self) -> None:
        self.assertIn("official-route-highlight", self.html)
        self.assertIn("toggleOfficialRouteHighlight", self.html)
        self.assertIn("officialRouteEdges", self.html)
        self.assertNotIn("data-official-route-toggle", self.html)

    def test_detail_focus_redraw_preserves_official_route_highlight(self) -> None:
        self.assertIn(
            "window.marvelApplyOfficialRouteSvgOverlay?.(svg,part)",
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
        official = policy["modes"]["official"]
        site_proposal = policy["modes"]["site-proposal"]
        complete = policy["modes"]["complete"]

        self.assertEqual(official["algorithm"], "official_route_only")
        self.assertEqual(official["fallback"], "none")
        self.assertEqual(official.get("recursive_tiers", []), [])
        self.assertIn("自動切替", official["description"])

        self.assertEqual(site_proposal["algorithm"], "curated_route_plus_core")
        self.assertIn("curated", site_proposal["provenance"])
        self.assertIn("graph", site_proposal["provenance"])
        self.assertEqual(site_proposal["expansion_waves"], 0)
        self.assertIn("公式予習ルートとは分離", site_proposal["description"])

        self.assertEqual(
            complete["algorithm"],
            "recursive_core_recommended_plus_direct_reference",
        )
        self.assertIn("混ぜず", complete["description"])
        self.assertEqual(policy["legacy_modes"]["recommended"], "旧v5共有状態。現行公開UIではsite-proposalへ正規化する。")

        with PREWATCH_RULES.open(encoding="utf-8-sig", newline="") as handle:
            rules = list(csv.DictReader(handle))
        by_no = {row["rule_no"]: row for row in rules}
        self.assertEqual(by_no["14"]["management_value"], "minimum-direct-core")
        self.assertEqual(
            by_no["15"]["management_value"],
            "site-proposal-plus-core",
        )
        self.assertIn("再帰探索しない", by_no["14"]["meaning"])

        readme = DATA_README.read_text(encoding="utf-8")
        self.assertIn("公式予習ルート", readme)
        self.assertIn("サイト提案ルート", readme)
        self.assertIn("完全版", readme)

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
