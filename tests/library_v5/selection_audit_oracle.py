"""Small, independent oracle for the flowchart selection contract.

This module intentionally does not import or execute ``index.html``.  It models
the documented edge-direction rules from the exported edge attributes so that
the contract tests can catch a shared regression in both traversal and
rendering code.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Iterable, Mapping


_STRENGTH_RANK = {
    "very strong": 4,
    "strong": 3,
    "medium": 2,
    "weak": 1,
}


@dataclass(frozen=True)
class SelectionExpectation:
    back_edges: frozenset[str]
    forward_edges: frozenset[str]
    context_edges: frozenset[str]

    @property
    def all_edges(self) -> frozenset[str]:
        return self.back_edges | self.forward_edges | self.context_edges


class SelectionAuditOracle:
    """Independent expected-set calculator for one exported flowchart payload."""

    def __init__(self, payload: Mapping[str, object]) -> None:
        raw_nodes = payload.get("nodes")
        raw_edges = payload.get("edges")
        if not isinstance(raw_nodes, list) or not isinstance(raw_edges, list):
            raise ValueError("flowchart payload must contain nodes and edges lists")
        self.work_ids = tuple(sorted(str(row["work_id"]) for row in raw_nodes))
        self.edges = tuple(self._normalize_edge(row) for row in raw_edges)
        self._incoming: dict[str, list[dict[str, str]]] = defaultdict(list)
        self._outgoing: dict[str, list[dict[str, str]]] = defaultdict(list)
        self._edge_by_key: dict[str, dict[str, str]] = {}
        for edge in self.edges:
            key = self.edge_key(edge)
            if key in self._edge_by_key:
                raise ValueError(f"duplicate directed edge pair: {key}")
            self._edge_by_key[key] = edge
            self._incoming[edge["target_work_id"]].append(edge)
            self._outgoing[edge["source_work_id"]].append(edge)

    @staticmethod
    def edge_key(edge: Mapping[str, str]) -> str:
        """Return the key used by the HTML renderer for a directed edge."""
        return f"{edge['source_work_id']}->{edge['target_work_id']}"

    @staticmethod
    def _normalize_edge(raw: object) -> dict[str, str]:
        if not isinstance(raw, Mapping):
            raise ValueError("flowchart edge must be an object")
        required = ("edge_id", "source_work_id", "target_work_id", "type_en", "strength")
        missing = [name for name in required if not raw.get(name)]
        if missing:
            raise ValueError(f"flowchart edge missing fields: {missing}")
        return {name: str(raw[name]) for name in required}

    @staticmethod
    def _rank(edge: Mapping[str, str]) -> int:
        return _STRENGTH_RANK.get(edge.get("strength", ""), 1)

    @classmethod
    def _back_propagates(cls, edge: Mapping[str, str]) -> bool:
        return cls._rank(edge) >= 3 or edge["type_en"] == "explicit work relation"

    @classmethod
    def _forward_propagates(cls, edge: Mapping[str, str]) -> bool:
        return cls._rank(edge) >= 3

    def _backward_edges(self, target_id: str) -> tuple[set[str], set[str]]:
        """Return complete backward edges and the direct links omitted as shortcuts."""
        all_back: set[str] = set()
        stack = [target_id]
        while stack:
            current = stack.pop()
            for edge in self._incoming.get(current, ()):
                if not self._back_propagates(edge):
                    continue
                key = self.edge_key(edge)
                if key in all_back:
                    continue
                all_back.add(key)
                stack.append(edge["source_work_id"])

        visible_incoming = {
            self.edge_key(edge) for edge in self._incoming.get(target_id, ())
        }
        candidates = all_back | visible_incoming
        adjacency: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for key in candidates:
            edge = self._edge_by_key[key]
            adjacency[edge["source_work_id"]].append((key, edge["target_work_id"]))

        def has_alternate_path(source: str, destination: str, skip_key: str) -> bool:
            seen = {source}
            queue = deque([source])
            while queue:
                current = queue.popleft()
                for key, next_id in adjacency.get(current, ()):
                    if key == skip_key:
                        continue
                    if next_id == destination:
                        return True
                    if next_id not in seen:
                        seen.add(next_id)
                        queue.append(next_id)
            return False

        filtered = set(candidates)
        for key in candidates:
            edge = self._edge_by_key[key]
            if (
                edge["target_work_id"] == target_id
                and edge["type_en"] == "shared character/entity"
                and has_alternate_path(edge["source_work_id"], target_id, key)
            ):
                filtered.remove(key)
        return all_back & filtered, visible_incoming - filtered

    def expected_main_selection(self, target_id: str, *, tier: str) -> SelectionExpectation:
        """Calculate main-graph edge classes for one target.

        The two public tiers intentionally share the chart's explicit
        predecessor contract.  Tier-specific preparation filtering is a view
        concern layered on top of this main-graph predecessor set.
        """
        if target_id not in self.work_ids:
            raise KeyError(target_id)
        if tier not in {"site-proposal", "complete"}:
            raise ValueError(f"unsupported public tier: {tier}")

        back_edges, omitted_shortcuts = self._backward_edges(target_id)
        forward_edges: set[str] = set()
        stack = [target_id]
        seen_nodes = {target_id}
        while stack:
            current = stack.pop()
            for edge in self._outgoing.get(current, ()):
                if not self._forward_propagates(edge):
                    continue
                key = self.edge_key(edge)
                forward_edges.add(key)
                next_id = edge["target_work_id"]
                if next_id not in seen_nodes:
                    seen_nodes.add(next_id)
                    stack.append(next_id)

        # Site proposal is intentionally asymmetric: direct weak context after
        # the selected work stays visible, while weak incoming fan-in is kept
        # out of the curated route. Complete mode retains both direct sides.
        context_edges = set()
        if tier == "complete":
            context_edges.update(
                self.edge_key(edge)
                for edge in self._incoming.get(target_id, ())
                if not self._back_propagates(edge)
                and self.edge_key(edge) not in omitted_shortcuts
            )
        context_edges.update(
            self.edge_key(edge)
            for edge in self._outgoing.get(target_id, ())
            if not self._forward_propagates(edge)
        )
        return SelectionExpectation(
            back_edges=frozenset(back_edges),
            forward_edges=frozenset(forward_edges),
            context_edges=frozenset(context_edges),
        )

    @staticmethod
    def expected_chronology(
        records: Iterable[Mapping[str, object]],
        target_id: str,
        *,
        tier: str,
        tier_node_ids: Iterable[str] | None = None,
    ) -> dict[str, str]:
        """Return expected chronology classes without traversing display-only rows."""
        if tier not in {"site-proposal", "complete"}:
            raise ValueError(f"unsupported public tier: {tier}")
        normalized: list[dict[str, object]] = []
        seen: set[str] = set()
        for raw in records:
            source = str(raw.get("source") or raw.get("chronologySource") or "")
            target = str(raw.get("target") or raw.get("chronologyTarget") or "")
            key = str(raw.get("key") or f"{source}->{target}")
            if not source or not target or not key or key in seen:
                continue
            if raw.get("traversable") is False:
                continue
            seen.add(key)
            normalized.append({"key": key, "source": source, "target": target})

        incoming: dict[str, list[dict[str, object]]] = defaultdict(list)
        outgoing: dict[str, list[dict[str, object]]] = defaultdict(list)
        for edge in normalized:
            incoming[str(edge["target"])].append(edge)
            outgoing[str(edge["source"])].append(edge)

        tier_nodes = set(tier_node_ids or ())

        def walk(adjacency: Mapping[str, list[dict[str, object]]], *, backward: bool) -> set[str]:
            found: set[str] = set()
            seen_nodes = {target_id}
            queue = deque([target_id])
            while queue:
                current = queue.popleft()
                for edge in adjacency.get(current, ()):
                    if backward and tier == "site-proposal" and tier_nodes:
                        if edge["source"] not in tier_nodes or edge["target"] not in tier_nodes:
                            continue
                    key = str(edge["key"])
                    found.add(key)
                    next_id = str(edge["source"] if backward else edge["target"])
                    if next_id not in seen_nodes:
                        seen_nodes.add(next_id)
                        queue.append(next_id)
            return found

        classes: dict[str, str] = {}
        for key in walk(incoming, backward=True):
            classes[key] = "backhl"
        for key in walk(outgoing, backward=False):
            classes[key] = "bothhl" if key in classes else "forwardhl"
        return classes
