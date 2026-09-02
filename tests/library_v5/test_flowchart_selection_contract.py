from __future__ import annotations

import csv
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "index.html"


def function_body(source: str, name: str) -> str:
    """Return a balanced-brace JavaScript function body for source assertions."""
    match = re.search(rf"function\s+{re.escape(name)}\s*\([^)]*\)\s*\{{", source)
    if not match:
        raise AssertionError(f"function {name} was not found")
    start = match.end() - 1
    depth = 0
    quote = None
    escaped = False
    for index in range(start, len(source)):
        char = source[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in "'\"`":
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise AssertionError(f"function {name} has unbalanced braces")


class FlowchartSelectionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = INDEX.read_text(encoding="utf-8")

    def test_overview_materializes_every_exported_edge_once_with_stable_edge_key(self) -> None:
        body = function_body(self.source, "materializeMissingMasterEdges")
        self.assertIn("#overview", body)
        self.assertIn("for(const edge of EDGES)", body)
        self.assertIn("edge.edge_id", body)
        self.assertRegex(body, r"dataset\.edgeKey\s*=\s*edge\.edge_id")
        self.assertRegex(body, r"(?:has|querySelector).*edge\.edge_id")
        self.assertIn("data-master-edge-materialized", body)

    def test_default_all_reference_policy_keeps_reference_edges_visible(self) -> None:
        self.assertIn("policy.default_edge_visibility!=='all'", self.source)
        self.assertIn("policy.default_importance_mode", self.source)
        self.assertIn(
            "window.marvelSetImportanceMode(policy.default_importance_mode)",
            function_body(self.source, "applyFlowchartPolicy"),
        )
        self.assertNotIn("window.marvelSetConnectionTier(defaultTier)", function_body(self.source, "applyFlowchartPolicy"))
        self.assertIn("marvelApplyFlowchartPolicy", self.source)
        self.assertRegex(
            self.source,
            r"default_importance_mode[\s\S]{0,240}marvelSetImportanceMode",
        )

    def test_public_tier_highlighting_is_derived_without_importance_visibility_filter(self) -> None:
        """The public tier must share preparation semantics without hiding master edges."""
        self.assertIn("function buildTierHighlightState", self.source)
        body = function_body(self.source, "buildTierHighlightState")
        self.assertIn("tierRoutePartForGoal", body)
        self.assertIn("buildMultiGoalPlan", function_body(self.source, "tierRoutePartForGoal"))
        self.assertIn("tierBackEdges", body)
        self.assertIn("tierNodeIds", body)
        self.assertRegex(body, r"forwardEdges\s*:\s*new Set\(baseState\.forwardEdges")

    def test_chart_story_predecessors_use_reason_provenance(self) -> None:
        """An explicit relation remains a predecessor when another reason wins the display label."""
        helper = function_body(self.source, "hasExplicitWorkRelationReason")
        self.assertIn("reason_ids", helper)
        self.assertIn("reason_kind", helper)
        body = function_body(self.source, "buildTierHighlightState")
        self.assertIn("hasExplicitWorkRelationReason", body)
        self.assertIn("routeBackNodeIds", body)
        self.assertIn("goals.includes(edgeByKey.get(key)?.source)", body)
        tagger = function_body(self.source, "tagEdgeImportance")
        self.assertNotIn("importance-hidden", tagger)

    def test_multigoal_context_keeps_context_edges_from_every_goal(self) -> None:
        body = function_body(self.source, "buildTierHighlightState")
        self.assertIn("goals.includes(edgeByKey.get(key)?.source)", body)
        self.assertIn("goals.includes(edge.source)?edge.target:edge.source", body)

    def test_chart_tier_uses_the_shared_connection_tier_setter(self) -> None:
        self.assertIn('id="chartConnectionTier"', self.source)
        selector = re.search(r'<select id="chartConnectionTier".*?</select>', self.source, re.DOTALL)
        self.assertIsNotNone(selector)
        self.assertEqual(
            re.findall(r'<option value="([^"]+)"', selector.group(0)),
            ["site-proposal", "complete"],
        )
        self.assertRegex(
            self.source,
            r"chart-tier-select[\s\S]{0,600}marvelSetConnectionTier\(sel\.value\)",
        )

    def test_desktop_focus_uses_the_shared_connection_tier_state(self) -> None:
        """PC inspection and watch-plan goals must render the same tier semantics."""
        body = function_body(self.source, "focusPart")
        self.assertIn("marvelBuildTierHighlightState", body)
        self.assertIn("marvelGetConnectionTier", body)

    def test_background_click_clear_is_guarded_against_drag_and_non_background_targets(self) -> None:
        self.assertIn("startTarget", self.source)
        self.assertIn("backgroundClickCandidate", self.source)
        self.assertRegex(self.source, r"backgroundClickCandidate[\s\S]{0,500}clearAllGoalsWithUndo")
        self.assertRegex(self.source, r"if\(st\?\.(?:didDrag|moved)[\s\S]{0,180}stopImmediatePropagation")

    def test_pointercancel_clears_gesture_click_guard(self) -> None:
        """A cancelled pointer gesture must not swallow the next real click."""
        match = re.search(r"const endPointer=e=>\{(?P<body>[\s\S]*?)\n\s*\};", self.source)
        self.assertIsNotNone(match)
        body = match.group("body") if match else ""
        self.assertIn("e.type==='pointercancel'", body)
        self.assertRegex(body, r"pointercancel[\s\S]{0,260}backgroundClickCandidate=false")
        self.assertRegex(body, r"pointercancel[\s\S]{0,320}didDrag=false")

    def test_desktop_reclick_and_blank_click_clear_focus(self) -> None:
        """Desktop inspection must be dismissible without leaving a stale focus paint."""
        self.assertRegex(
            self.source,
            r"window\.marvelFocusWork=function\(id,\{center=true\}=\{\}\)\{[\s\S]{0,1200}detailFocusId===id",
        )
        self.assertRegex(
            self.source,
            r"window\.marvelReturnToGoalView\?\.\(\);\s*clearAllGoalsWithUndo\(\)",
        )

    def test_selection_and_deselection_only_restyle_existing_edge_groups(self) -> None:
        body = function_body(self.source, "renderSelectionState")
        self.assertIn("classList.add('hl'", body)
        self.assertIn("classList.add('pathhl'", body)
        self.assertNotIn("addMissingDirectedEdges(svg,state)", body)
        self.assertNotIn("drawDynamicEdge(", body)
        self.assertNotIn("createElementNS(NS,'g')", body)
        self.assertNotIn("remove()", body)
        self.assertIn("reason_ids", self.source)

    def test_overlapping_backward_and_forward_edges_use_explicit_both_style(self) -> None:
        """A converging route must not let CSS class order decide the highlight color."""
        for name in ("renderSelectionState", "renderFocusHighlight"):
            body = function_body(self.source, name)
            self.assertRegex(body, r"if\(b&&f\).*classList\.add\('hl','bothhl'\)")

    def test_reason_panel_resolves_reason_ids_without_mutating_edges(self) -> None:
        self.assertIn("reasonsById", self.source)
        self.assertRegex(self.source, r"reason_ids\.map\(id=>reasonsById\[id\]")
        self.assertRegex(self.source, r"reason_ids[\s\S]{0,700}(reason explanation|reasonExplain|根拠)")
        self.assertRegex(self.source, r"edge\.edge_id[\s\S]{0,220}reason_ids")

    def test_multiselect_and_directed_path_style_existing_ids(self) -> None:
        self.assertIn("combineMode==='path' && selectedIds.size>1", self.source)
        state_body = function_body(self.source, "pathSelectionState")
        self.assertIn("shortestDirectedPath", self.source)
        self.assertIn("pathEdges", state_body)
        self.assertIn("selectedIds", self.source)
        self.assertRegex(state_body, r"pathEdges\.add\(k\)")
        render_body = function_body(self.source, "renderSelectionState")
        self.assertRegex(render_body, r"state\.pathEdges\.has\(k\)")

    def test_path_mode_applies_connection_tier_to_candidate_edges(self) -> None:
        """PATH must recompute its directed candidates when the public tier changes."""
        self.assertIn("function pathEdgeAllowed", self.source)
        path_body = function_body(self.source, "pathSelectionState")
        self.assertIn("pathEdgeAllowed", path_body)
        self.assertIn("tierPathEdges", path_body)
        self.assertNotIn("if(baseState.pathMode) return {...baseState,tier:mode,tierNodeIds, tierBackEdges", self.source)
        self.assertRegex(self.source, r"function mobileSelectionWorldKey\(state\)[\s\S]{0,500}state\?\.tier\|\|state\?\.prepTier")

    def test_path_explanation_uses_the_same_connection_tier_filter(self) -> None:
        """The textual route explanation must not show a route hidden from the chart."""
        explanation = function_body(self.source, "updatePathExplanation")
        self.assertIn("pathTierContext", explanation)
        self.assertIn("pathEdgeAllowed", explanation)
        self.assertRegex(explanation, r"bestDirectedPairPath\(a,b,'main',[^)]+\)")
        self.assertRegex(explanation, r"bestDirectedPairPath\(a,b,'shortest',[^)]+\)")

    def test_backward_highlight_prefers_chain_over_transitive_shortcut(self) -> None:
        body = function_body(self.source, "directedPartAll")
        self.assertIn("filterBackwardShortcutEdges", body)
        helper = function_body(self.source, "filterBackwardShortcutEdges")
        self.assertIn("backEdges", helper)
        self.assertIn("hasAlternatePath", helper)
        self.assertIn("targetId", helper)
        self.assertIn("type_en", helper)
        self.assertIn("shared character/entity", helper)
        self.assertRegex(helper, r"skipKey")
        self.assertRegex(helper, r"queue|stack")
        self.assertIn("const filteredBackwardEdges=filterBackwardShortcutEdges(", body)
        self.assertIn("const visibleIncomingEdges", body)
        self.assertIn("const omittedBackEdges", body)
        self.assertIn("!omittedBackEdges.has(edgeKey(e))", body)

    def test_forward_highlight_does_not_use_backward_shortcut_filter(self) -> None:
        body = function_body(self.source, "directedPartAll")
        self.assertRegex(body, r"filteredBackwardEdges=filterBackwardShortcutEdges\(")
        self.assertNotRegex(body, r"forwardEdges=filterBackwardShortcutEdges\(forwardEdges\)")

    def test_complete_tier_expands_backward_history_without_expanding_forward_scope(self) -> None:
        body = function_body(self.source, "directedPartAll")
        self.assertRegex(
            body,
            r"backPropagates=e=>importanceAllowed\(e\) && \(edgeRank\(e\)>=3 \|\| e\.type_en==='explicit work relation'\)",
        )
        self.assertRegex(body, r"if\(!backPropagates\(e\)\) continue")
        self.assertRegex(body, r"if\(!propagates\(e\)\) continue")
        self.assertNotRegex(body, r"prepTier==='complete' \|\| edgeRank\(e\)>=3")

    def test_chart_history_keeps_explicit_story_chain_in_site_proposal(self) -> None:
        """Selecting Spider-Man 3 must keep the explicit Spider-Man 2 predecessor lit."""
        body = function_body(self.source, "directedPartAll")
        self.assertRegex(
            body,
            r"backPropagates=e=>importanceAllowed\(e\) && \(edgeRank\(e\)>=3 \|\| e\.type_en==='explicit work relation'\)",
        )
        tier_body = function_body(self.source, "buildTierHighlightState")
        self.assertIn("baseState.backEdges", tier_body)
        self.assertIn("hasExplicitWorkRelationReason", tier_body)
        self.assertIn("tierNodeIds.add(edge.source)", tier_body)
        self.assertIn("tierNodeIds.add(edge.target)", tier_body)

    def test_known_sequel_predecessors_remain_in_the_exported_chart_contract(self) -> None:
        """Both reported Spider-Man chains must remain available to the chart renderer."""
        payload = json.loads((ROOT / "data" / "derived" / "flowchart.json").read_text(encoding="utf-8"))
        edges = {
            (edge["source_work_id"], edge["target_work_id"]): edge
            for edge in payload["edges"]
        }
        for source, target in (
            ("the-amazing-spider-man-2012", "the-amazing-spider-man-2-2014"),
            ("spider-man-2-2004", "spider-man-3-2007"),
        ):
            edge = edges.get((source, target))
            self.assertIsNotNone(edge, f"missing exported edge: {source}->{target}")
            self.assertEqual(edge["type_en"], "explicit work relation")
        body = function_body(self.source, "directedPartAll")
        self.assertRegex(
            body,
            r"backPropagates=e=>importanceAllowed\(e\) && \(edgeRank\(e\)>=3 \|\| e\.type_en==='explicit work relation'\)",
        )

    def test_every_active_work_relation_has_an_exported_chart_edge(self) -> None:
        """The renderer must retain every non-superseded canonical relationship pair."""
        with (ROOT / "data" / "library" / "work_relations.csv").open(
            encoding="utf-8-sig", newline=""
        ) as handle:
            relations = list(csv.DictReader(handle))
        expected = {
            (row["source_work_id"], row["target_work_id"])
            for row in relations
            if row["verification_status"] != "superseded"
        }
        payload = json.loads((ROOT / "data" / "derived" / "flowchart.json").read_text(encoding="utf-8"))
        exported = {
            (edge["source_work_id"], edge["target_work_id"])
            for edge in payload["edges"]
        }
        self.assertTrue(expected <= exported, f"missing exported relationship pairs: {sorted(expected - exported)}")

    def test_character_filter_is_visual_only_and_does_not_replace_exported_edges(self) -> None:
        body = function_body(self.source, "applyCharacterHighlight")
        self.assertIn("charhl", body)
        self.assertNotIn("EDGES=", body)
        self.assertNotIn("EDGES =", body)
        self.assertIn("const ids=charWorks[cf.value]||new Set()", body)
        self.assertIn(
            "EDGES.length",
            self.source,
            "the visual-only filter contract should observe the exported edge collection",
        )

    def test_mobile_canvas_preserves_stable_chronology_edge_ids(self) -> None:
        body = function_body(self.source, "canvasPrimitive")
        self.assertIn("rawEdgeKey=overlayGroup.dataset?.edgeKey", body)
        self.assertIn("window.marvelEdgeKeyFromGroup(overlayGroup)", body)
        self.assertIn("overlayEdgeKey=typeof window.marvelEdgeKeyFromGroup", body)
        self.assertIn("overlayChronologyEdgeId", body)
        rebuild = function_body(self.source, "prepareMobileSelectionWorldResources")
        self.assertIn("overlayChronologyEdgeId", rebuild)
        self.assertIn("chronologyEdgeMap", rebuild)
        self.assertIn("const edgeId=p.overlayChronologyEdgeId||", rebuild)
        self.assertIn("chronologyEdgeMap.has(edgeId)", rebuild)

    def test_chronology_sequence_edges_are_explicit_and_selection_aware(self) -> None:
        """Chronology lines must be their own sequence layer, not graph shortcuts."""
        chronology = function_body(self.source, "buildChronologyView")
        self.assertIn("chronologyEdgeGroup", chronology)
        self.assertIn("data-chronology-source", self.source)
        self.assertIn("data-chronology-target", self.source)
        self.assertIn("renderChronologySelectionState", self.source)
        selection_renderer = function_body(self.source, "renderSelectionState")
        self.assertIn("renderChronologySelectionState(svg,state)", selection_renderer)
        renderer = function_body(self.source, "renderChronologySelectionState")
        self.assertIn("state", renderer)
        self.assertIn("chronology-edge", renderer)
        self.assertNotIn("EDGES", renderer)
        focus_renderer = function_body(self.source, "renderFocusHighlight")
        self.assertIn("renderChronologySelectionState", focus_renderer)

    def test_release_order_keeps_work_relationship_edges_disabled(self) -> None:
        """Publication order remains a date axis, not a fabricated work chain."""
        release = function_body(self.source, "buildReleaseView")
        self.assertIn('data-relationship-edges="off"', release)
        self.assertNotIn("chronology-edge", release)

    def test_mobile_canvas_preserves_chronology_selection_overlay_metadata(self) -> None:
        """Canvas mode must highlight chronology paths without mixing them into graph edges."""
        primitive = function_body(self.source, "canvasPrimitive")
        self.assertIn("overlayChronologySource", primitive)
        self.assertIn("overlayChronologyTarget", primitive)
        self.assertIn("overlayChronologyEdge", primitive)
        self.assertIn("g.chronology-edge", primitive)

        rebuild = function_body(self.source, "prepareMobileSelectionWorldResources")
        self.assertIn("overlayChronologyEdgePrimitives", rebuild)
        self.assertIn("overlayChronologySource", rebuild)

        overlay = function_body(self.source, "drawMobileSelectionOverlay")
        self.assertIn("mobileOverlayChronologyEdgeClass", overlay)
        self.assertIn("overlayChronologyEdgePrimitives", overlay)

    def test_chronology_highlight_uses_shared_state_aware_classifier(self) -> None:
        """SVG and Canvas chronology lines must share selection-mode semantics."""
        self.assertIn("classifyChronologySelection", self.source)
        renderer = function_body(self.source, "renderChronologySelectionState")
        self.assertIn("classifyChronologySelection", renderer)
        mobile = function_body(self.source, "mobileOverlayChronologyEdgeClassMap")
        self.assertIn("classifyChronologySelection", mobile)
        self.assertNotIn("const walk=(starts,adjacent)=>", renderer)
        self.assertNotIn("const walk=(starts,adjacent)=>", mobile)
        classifier = function_body(self.source, "classifyChronologySelection")
        for token in ("previous1", "combineMode==='and'", "pathMode", "traversable===false"):
            self.assertIn(token, classifier)
        self.assertIn("state?.combineMode==='path'&&ids.length>1", classifier)
        self.assertIn("const rawTier=state?.tier||state?.prepTier||'complete'", classifier)
        self.assertIn("const tier=rawTier==='complete'?'complete':'site-proposal'", classifier)
        self.assertNotIn("normalizePreparationTier", classifier)
        self.assertIn("tierNodeIds", classifier)
        self.assertIn("state?.pathEdges", classifier)
        self.assertRegex(classifier, r"adjacent===incoming[\s\S]{0,260}tierNodeIds")
        self.assertRegex(classifier, r"pathIds\.has|pathEdges?\.has")

    def test_selection_state_exposes_scope_and_combine_mode_to_chronology_layer(self) -> None:
        """The pure classifier must not read hidden module globals for mode semantics."""
        state_body = function_body(self.source, "computeSelectionState")
        path_body = function_body(self.source, "pathSelectionState")
        self.assertRegex(state_body, r"scopeMode")
        self.assertRegex(state_body, r"combineMode")
        self.assertRegex(path_body, r"scopeMode")
        self.assertRegex(path_body, r"combineMode")
        self.assertIn("selectedIds", state_body)

    def test_desktop_focus_passes_its_tier_state_to_chronology(self) -> None:
        """Detail inspection must not render chronology from a stale goal state."""
        focus = function_body(self.source, "renderFocusHighlight")
        self.assertIn("renderChronologySelectionState?.(svg,part)", focus)
        self.assertIn("marvelApplyOfficialRouteSvgOverlay?.(svg,part)", focus)

    def test_panel_switch_restores_desktop_detail_focus(self) -> None:
        """Returning to a chart view must repaint an existing desktop inspection."""
        start = self.source.index("window.activatePanel=function")
        end = self.source.index("\n  };\n\n  document.querySelectorAll('.tab').forEach", start)
        activate = self.source[start:end]
        self.assertIn("window.marvelDetailFocusId", activate)
        self.assertIn("window.marvelRenderDetailFocus(window.marvelDetailFocusId)", activate)

    def test_chronology_groups_carry_traversability_and_fox_branch_endpoints(self) -> None:
        """Structural branches are selectable; display-only sequences are not traversed."""
        chronology = function_body(self.source, "buildChronologyView")
        edge_group = function_body(self.source, "chronologyEdgeGroup")
        sequence = function_body(self.source, "drawSequence")
        branch = function_body(self.source, "branchBetweenRows")
        self.assertIn("data-chronology-traversable", edge_group)
        self.assertIn("traversable", sequence)
        self.assertIn("chronologyEdgeGroup", branch)
        self.assertIn("source,target", self.source)
        self.assertIn("chronologyEdgeGroup(edgeId,source,target", branch)
        self.assertRegex(
            chronology,
            r"drawSequence\(\['morbius-2022','madame-web-2024','kraven-the-hunter-2024'\][\s\S]{0,260}traversable:false",
        )

    def test_chronology_edges_have_stable_identity_and_display_invariant(self) -> None:
        edge_group = function_body(self.source, "chronologyEdgeGroup")
        self.assertIn("data-chronology-edge-id", edge_group)
        self.assertIn("data-chronology-kind", edge_group)
        self.assertIn("data-chronology-display-only", edge_group)
        self.assertIn("displayOnly", edge_group)
        self.assertIn("displayOnly&&!traversable", edge_group)

    def test_chronology_canvas_materialization_uses_edge_id(self) -> None:
        primitive = function_body(self.source, "canvasPrimitive")
        mapper = function_body(self.source, "mobileOverlayChronologyEdgeClassMap")
        self.assertIn("overlayChronologyEdgeId", primitive)
        self.assertIn("edgeId", mapper)

    def test_chronology_svg_materialization_uses_edge_id(self) -> None:
        renderer = function_body(self.source, "renderChronologySelectionState")
        self.assertRegex(renderer, r"dataset(?:\?\.)?chronologyEdgeId")
        self.assertIn("edgeId", renderer)
        self.assertIn("recordsById.get(edgeId)", renderer)


if __name__ == "__main__":
    unittest.main()
