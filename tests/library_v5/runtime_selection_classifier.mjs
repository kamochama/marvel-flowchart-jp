import fs from "node:fs";
import vm from "node:vm";

const ROOT = new URL("../../", import.meta.url);
const source = fs.readFileSync(new URL("index.html", ROOT), "utf8");

function functionSource(name) {
  const match = source.match(new RegExp(`function\\s+${name}\\s*\\([^)]*\\)\\s*\\{`));
  if (!match) throw new Error(`function ${name} was not found`);
  const declarationStart = match.index;
  const start = match.index + match[0].length - 1;
  let depth = 0;
  let quote = null;
  let escaped = false;
  for (let index = start; index < source.length; index += 1) {
    const char = source[index];
    if (quote) {
      if (escaped) escaped = false;
      else if (char === "\\") escaped = true;
      else if (char === quote) quote = null;
      continue;
    }
    if (char === "'" || char === '"' || char === "`") quote = char;
    else if (char === "{") depth += 1;
    else if (char === "}") {
      depth -= 1;
      if (depth === 0) return source.slice(declarationStart, index + 1);
    }
  }
  throw new Error(`function ${name} has unbalanced braces`);
}

function loadFunction(name, context = {}) {
  const sandbox = {...context};
  vm.runInNewContext(`this.__fn = ${functionSource(name)}`, sandbox, {filename: "index.html"});
  return sandbox.__fn;
}

const classifyChronologySelection = loadFunction("classifyChronologySelection");
const edgeKey = loadFunction("edgeKey");
const edgeRecordFromSvgGroup = loadFunction("edgeRecordFromSvgGroup", {
  EDGES: [{edge_id: "edge-a-b", source: "a", target: "b"}],
  edgeKey,
});
const renderChronologySelectionState = loadFunction("renderChronologySelectionState", {
  classifyChronologySelection,
});
const mobileOverlayChronologyEdgeClassMap = loadFunction("mobileOverlayChronologyEdgeClassMap", {
  classifyChronologySelection,
});
const hasExplicitWorkRelationReason = loadFunction("hasExplicitWorkRelationReason", {
  reasonsById: {"reason-explicit": {reason_kind: "explicit_relation"}},
});

function classify(records, state) {
  return Object.fromEntries(
    [...classifyChronologySelection(records, state).entries()].sort(([a], [b]) => a.localeCompare(b)),
  );
}

function edgeKeyFromGroup(group) {
  const edge = edgeRecordFromSvgGroup(group);
  if (edge) return edgeKey(edge);
  return group?.dataset?.edgeKey || "";
}

const duplicateEdges = [
  { edge_id: "a-goal-sequence", source: "a", target: "goal", traversable: true, display_only: false },
  { edge_id: "a-goal-branch", source: "a", target: "goal", traversable: true, display_only: false },
  { edge_id: "goal-display", source: "goal", target: "next", traversable: false, display_only: true },
];
const duplicateResult = classifyChronologySelection(duplicateEdges, {
  selectedIds: ["goal"], tier: "complete", combineMode: "or",
});

function fakeClassList(initial = []) {
  const values = new Set(initial);
  return {
    add(...names) { for (const name of names) values.add(name); },
    remove(...names) { for (const name of names) values.delete(name); },
    values() { return [...values].sort(); },
  };
}

const tierRecords = [
  {key: "q->a", source: "q", target: "a", traversable: true},
  {key: "a->goal", source: "a", target: "goal", traversable: true},
  {key: "goal->next", source: "goal", target: "next", traversable: true},
];

const report = {
  non_traversable: {
    "site-proposal": classify(
      [{key: "a->goal", source: "a", target: "goal", traversable: false}],
      {selectedIds: ["goal"], tier: "site-proposal", tierNodeIds: new Set(["a", "goal"])},
    ),
    complete: classify(
      [{key: "a->goal", source: "a", target: "goal", traversable: false}],
      {selectedIds: ["goal"], tier: "complete", tierNodeIds: new Set(["a", "goal"])},
    ),
  },
  tier_gate: {
    "site-proposal": classify(tierRecords, {
      selectedIds: ["goal"],
      tier: "site-proposal",
      tierNodeIds: new Set(["a", "goal", "next"]),
    }),
    complete: classify(tierRecords, {
      selectedIds: ["goal"],
      tier: "complete",
      tierNodeIds: new Set(["a", "goal", "next"]),
    }),
  },
  scope_and_path: {
    previous1: classify(tierRecords, {
      selectedIds: ["goal"],
      scopeMode: "previous1",
      tier: "complete",
    }),
    and: classify(
      [{key: "c->d", source: "c", target: "d", traversable: true}],
      {selectedIds: ["d", "c"], combineMode: "and", tier: "complete"},
    ),
    path: classify(tierRecords, {
      selectedIds: ["goal"],
      pathMode: true,
      pathEdges: new Set(["a->goal"]),
      tier: "complete",
    }),
  },
  edge_key: {
    edge_id: edgeKeyFromGroup({dataset: {edgeKey: "edge-a-b"}, querySelector: () => null}),
    title_fallback: edgeKeyFromGroup({dataset: {}, querySelector: () => ({textContent: "a->b"})}),
  },
  duplicate_edges: Object.fromEntries(
    [...duplicateResult.entries()].sort(([a], [b]) => a.localeCompare(b)),
  ),
};

const chronologyGroups = [
  {
    dataset: {
      chronologyEdgeKey: "a->goal",
      chronologySource: "a",
      chronologyTarget: "goal",
      chronologyTraversable: "true",
    },
    classList: fakeClassList(["forwardhl"]),
  },
  {
    dataset: {
      chronologyEdgeKey: "false->goal",
      chronologySource: "false",
      chronologyTarget: "goal",
      chronologyTraversable: "false",
    },
    classList: fakeClassList(["hl", "backhl"]),
  },
];
renderChronologySelectionState(
  {querySelectorAll: selector => selector === "g.chronology-edge" ? chronologyGroups : []},
  {selectedIds: ["goal"], tier: "complete"},
);
report.svg = Object.fromEntries(
  chronologyGroups.map(group => [group.dataset.chronologyEdgeKey, group.classList.values()]),
);

const canvasClasses = mobileOverlayChronologyEdgeClassMap(
  {
    overlayChronologyEdgePrimitives: new Map([
      ["a->goal", [{overlayChronologySource: "a", overlayChronologyTarget: "goal", overlayChronologyTraversable: true}]],
      ["false->goal", [{overlayChronologySource: "false", overlayChronologyTarget: "goal", overlayChronologyTraversable: false}]],
    ]),
  },
  {selectedIds: ["goal"], tier: "complete"},
);
report.canvas = Object.fromEntries(canvasClasses.entries());

report.reason_provenance = {
  transition_with_explicit_reason: hasExplicitWorkRelationReason({
    type_en: "multiverse transition",
    reason_ids: ["reason-explicit"],
  }),
  transition_without_explicit_reason: hasExplicitWorkRelationReason({
    type_en: "multiverse transition",
    reason_ids: ["reason-other"],
  }),
};

process.stdout.write(`${JSON.stringify(report)}\n`);
