#!/usr/bin/env node

import fs from "node:fs";
import http from "node:http";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";

const WORK_COUNT = 131;
const WAIT_TIMEOUT_MS = 20_000;
const CHROME_PROFILE_CLEANUP_RETRIES = 100;
const PC_CASES = [
  { name: "exact-day", precision: "day", id: "iron-man-2008" },
  { name: "month-only", precision: "month", id: null },
  { name: "year-only", precision: "year", id: null },
  { name: "tbd", precision: "none", id: null },
];

function usage() {
  return [
    "Usage: node browser_publication_order_audit.mjs --root <repo> --chrome <path> [--timeout-ms <n>]",
    "Audits the publication-order SVG and mobile Canvas with real Chrome CDP events.",
    "geometry: card paths, viewBox, year axis, era/lane frames remain invariant after selection.",
    "synthetic: mobile publication-order selections, re-tap, background tap, and drag-end keep synthetic edges at zero.",
    "Options: --root, --chrome, --timeout-ms, --help",
  ].join("\n");
}

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--help" || arg === "-h") args.help = true;
    else if (arg.startsWith("--")) {
      const key = arg.slice(2).replaceAll("-", "_");
      const next = argv[i + 1];
      if (!next || next.startsWith("--")) throw new Error(`${arg} requires a value`);
      args[key] = next;
      i += 1;
    } else throw new Error(`unknown argument: ${arg}`);
  }
  return args;
}

function locateChrome(configured) {
  const candidates = [
    configured,
    process.env.MARVEL_CHROME_BIN,
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "chrome",
    "C:/Program Files/Google/Chrome/Application/chrome.exe",
    "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    path.join(process.env.LOCALAPPDATA || "", "Google/Chrome/Application/chrome.exe"),
  ].filter(Boolean);
  for (const candidate of candidates) {
    if (path.isAbsolute(candidate) && fs.existsSync(candidate)) return candidate;
    if (!path.isAbsolute(candidate)) {
      const resolved = process.env.PATH?.split(path.delimiter).map((entry) => path.join(entry, candidate)).find((entry) => fs.existsSync(entry));
      if (resolved) return resolved;
    }
  }
  throw new Error("Chrome/Chromium executable not found; pass --chrome or MARVEL_CHROME_BIN");
}

function loadExpected(root) {
  const file = path.join(root, "data", "derived", "flowchart.json");
  const payload = JSON.parse(fs.readFileSync(file, "utf8"));
  const nodes = payload.nodes || [];
  if (nodes.length !== WORK_COUNT) throw new Error(`flowchart expected ${WORK_COUNT} works, got ${nodes.length}`);
  const ids = nodes.map((node) => node.work_id);
  if (new Set(ids).size !== WORK_COUNT) throw new Error("flowchart contains duplicate work IDs");
  return {
    ids,
    indexById: new Map(ids.map((id, index) => [id, index])),
    byId: new Map(nodes.map((node) => [node.work_id, node])),
  };
}

function freePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      const port = typeof address === "object" && address ? address.port : 0;
      server.close((error) => (error ? reject(error) : resolve(port)));
    });
  });
}

function contentType(filePath) {
  return {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".json": "application/json",
    ".css": "text/css; charset=utf-8",
    ".png": "image/png",
    ".svg": "image/svg+xml",
  }[path.extname(filePath).toLowerCase()] || "application/octet-stream";
}

async function startStaticServer(root) {
  const resolvedRoot = fs.realpathSync(root);
  const server = http.createServer((request, response) => {
    try {
      const pathname = decodeURIComponent(new URL(request.url || "/", "http://localhost").pathname);
      const relative = pathname === "/" ? "index.html" : pathname.replace(/^\/+/, "");
      const filePath = path.resolve(resolvedRoot, relative);
      const relativeCheck = path.relative(resolvedRoot, filePath);
      if (relativeCheck.startsWith("..") || path.isAbsolute(relativeCheck)) {
        response.writeHead(403);
        response.end("forbidden");
        return;
      }
      if (!fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
        response.writeHead(404);
        response.end("not found");
        return;
      }
      response.writeHead(200, { "Content-Type": contentType(filePath), "Cache-Control": "no-store" });
      fs.createReadStream(filePath).pipe(response);
    } catch (error) {
      response.writeHead(400);
      response.end(String(error?.message || error));
    }
  });
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  const address = server.address();
  if (typeof address !== "object" || !address) throw new Error("static server address unavailable");
  return { server, url: `http://127.0.0.1:${address.port}/index.html` };
}

async function poll(task, timeoutMs, label) {
  const deadline = Date.now() + timeoutMs;
  let lastError = null;
  while (Date.now() < deadline) {
    try {
      const value = await task();
      if (value) return value;
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolve) => setTimeout(resolve, 50));
  }
  throw new Error(`${label} timed out${lastError ? `: ${lastError.message}` : ""}`);
}

async function launchChrome(chromePath, timeoutMs) {
  const port = await freePort();
  const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), "marvel-flowchart-publication-cdp-"));
  const child = spawn(chromePath, [
    "--headless=new", "--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox",
    "--no-first-run", "--no-default-browser-check", "--window-size=1600,1200",
    `--remote-debugging-port=${port}`, `--user-data-dir=${userDataDir}`, "about:blank",
  ], { stdio: ["ignore", "ignore", "pipe"] });
  let launchError = null;
  child.once("error", (error) => { launchError = error; });
  try {
    const target = await poll(async () => {
      if (launchError) throw launchError;
      const response = await fetch(`http://127.0.0.1:${port}/json/list`);
      if (!response.ok) return null;
      const targets = await response.json();
      return targets.find((entry) => entry.type === "page" && entry.webSocketDebuggerUrl) || null;
    }, timeoutMs, "Chrome DevTools page target");
    return { child, userDataDir, webSocketDebuggerUrl: target.webSocketDebuggerUrl };
  } catch (error) {
    await stopChrome({ child, userDataDir });
    throw error;
  }
}

async function stopChrome(processInfo) {
  const child = processInfo?.child;
  if (child && child.exitCode === null && !child.killed) {
    const exited = new Promise((resolve) => child.once("exit", resolve));
    child.kill();
    await Promise.race([exited, new Promise((resolve) => setTimeout(resolve, 5_000))]);
  }
  if (processInfo?.userDataDir) {
    fs.rmSync(processInfo.userDataDir, {
      recursive: true,
      force: true,
      maxRetries: CHROME_PROFILE_CLEANUP_RETRIES,
      retryDelay: 100,
    });
  }
}

class CdpClient {
  constructor(url) {
    this.url = url;
    this.nextId = 1;
    this.pending = new Map();
  }

  async connect() {
    this.socket = new WebSocket(this.url);
    await new Promise((resolve, reject) => {
      this.socket.addEventListener("open", resolve, { once: true });
      this.socket.addEventListener("error", () => reject(new Error("CDP WebSocket error")), { once: true });
    });
    this.socket.addEventListener("message", (event) => {
      const message = JSON.parse(String(event.data));
      if (!message.id) return;
      const pending = this.pending.get(message.id);
      if (!pending) return;
      this.pending.delete(message.id);
      if (message.error) pending.reject(new Error(message.error.message || "CDP command failed"));
      else pending.resolve(message.result || {});
    });
    this.socket.addEventListener("close", () => {
      for (const { reject } of this.pending.values()) reject(new Error("CDP socket closed"));
      this.pending.clear();
    });
  }

  send(method, params = {}) {
    const id = this.nextId++;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.socket.send(JSON.stringify({ id, method, params }));
    });
  }

  async evaluate(expression) {
    const result = await this.send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
    if (result.exceptionDetails) throw new Error(result.exceptionDetails.exception?.description || "page evaluation failed");
    return result.result?.value;
  }

  close() {
    try { this.socket?.close(); } catch (_) { /* best effort */ }
  }
}

async function pageEvaluate(cdp, body) {
  return cdp.evaluate(`(() => { ${body} })()`);
}

async function loadPage(cdp, url, timeoutMs) {
  await cdp.send("Page.navigate", { url });
  await poll(() => pageEvaluate(cdp, "return document.readyState === 'complete'"), timeoutMs, "page load");
  await poll(() => pageEvaluate(cdp, `
    return document.querySelectorAll('#overview .svg-wrap svg g.node').length===${WORK_COUNT} &&
      !!document.querySelector('#chartConnectionTier');
  `), timeoutMs, "flowchart DOM readiness");
}

async function clickPoint(cdp, point) {
  await cdp.send("Input.dispatchMouseEvent", { type: "mouseMoved", x: point.x, y: point.y });
  await cdp.send("Input.dispatchMouseEvent", { type: "mousePressed", x: point.x, y: point.y, button: "left", clickCount: 1 });
  await cdp.send("Input.dispatchMouseEvent", { type: "mouseReleased", x: point.x, y: point.y, button: "left", clickCount: 1 });
}

async function dragMouse(cdp, start, end) {
  await cdp.send("Input.dispatchMouseEvent", { type: "mouseMoved", x: start.x, y: start.y });
  await cdp.send("Input.dispatchMouseEvent", { type: "mousePressed", x: start.x, y: start.y, button: "left", clickCount: 1 });
  for (let step = 1; step <= 8; step += 1) {
    const ratio = step / 8;
    await cdp.send("Input.dispatchMouseEvent", {
      type: "mouseMoved", x: start.x + (end.x - start.x) * ratio, y: start.y + (end.y - start.y) * ratio, button: "left", buttons: 1,
    });
  }
  await cdp.send("Input.dispatchMouseEvent", { type: "mouseReleased", x: end.x, y: end.y, button: "left", clickCount: 1 });
}

async function touchTap(cdp, point) {
  await cdp.send("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: [{ x: point.x, y: point.y, radiusX: 1, radiusY: 1, force: 1 }] });
  await cdp.send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
}

async function touchDrag(cdp, start, end) {
  await cdp.send("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: [{ x: start.x, y: start.y, radiusX: 1, radiusY: 1, force: 1 }] });
  for (let step = 1; step <= 8; step += 1) {
    const ratio = step / 8;
    await cdp.send("Input.dispatchTouchEvent", {
      type: "touchMove", touchPoints: [{ x: start.x + (end.x - start.x) * ratio, y: start.y + (end.y - start.y) * ratio, radiusX: 1, radiusY: 1, force: 1 }],
    });
  }
  await cdp.send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
}

async function pointForSelector(cdp, selector) {
  return pageEvaluate(cdp, `
    const element=document.querySelector(${JSON.stringify(selector)});if(!element)return null;
    const rect=element.getBoundingClientRect();return {x:rect.left+rect.width/2,y:rect.top+rect.height/2,width:rect.width,height:rect.height};
  `);
}

async function clickSelector(cdp, selector, timeoutMs) {
  const point = await poll(() => pointForSelector(cdp, selector), timeoutMs, `selector ${selector}`);
  await clickPoint(cdp, point);
}

async function releaseCardRect(cdp, id) {
  return pageEvaluate(cdp, `
    const card=[...document.querySelectorAll('#release g.release-node[data-release-work-id]')].find(g=>g.dataset.releaseWorkId===${JSON.stringify(id)});
    const wrap=document.querySelector('#release .release-view-wrap');if(!card||!wrap)return null;
    const r=card.getBoundingClientRect(),w=wrap.getBoundingClientRect(),x=r.left+r.width/2,y=r.top+r.height/2,hit=document.elementFromPoint(x,y);
    return {x,y,left:r.left,right:r.right,top:r.top,bottom:r.bottom,hit:hit?{tag:hit.tagName,class:hit.getAttribute('class'),work:hit.closest?.('g.release-node')?.dataset?.releaseWorkId||null}:null,stack:[...(document.elementsFromPoint?.(x,y)||[])].slice(0,4).map(el=>({tag:el.tagName,class:el.getAttribute?.('class')||''})),viewport:{width:innerWidth,height:innerHeight,scrollX,scrollY},svg:document.querySelector('#release .release-view-wrap svg')?.getBoundingClientRect?.().toJSON?.()||null,wrap:{left:w.left,right:w.right,top:w.top,bottom:w.bottom}};
  `);
}

async function centerReleaseCard(cdp, id, timeoutMs) {
  let lastRect = null;
  const attempts = [];
  for (let attempt = 0; attempt < 24; attempt += 1) {
    const rect = await poll(() => releaseCardRect(cdp, id), timeoutMs, `release card ${id}`);
    lastRect = rect;
    const visibleBottom = Math.min(rect.wrap.bottom, rect.viewport?.height ?? rect.wrap.bottom);
    const inside = rect.x >= rect.wrap.left + 2 && rect.x <= Math.min(rect.wrap.right, rect.viewport?.width ?? rect.wrap.right) - 2 && rect.y >= rect.wrap.top + 2 && rect.y <= visibleBottom - 2;
    if (inside) return rect;
    const start = await blankReleasePoint(cdp);
    // Keep every drag endpoint inside the viewport. CDP does not reliably
    // deliver pointer moves whose endpoint is several screen-heights away.
    const dx = rect.wrap.left + (rect.wrap.right - rect.wrap.left) / 2 - rect.x;
    const targetY = rect.wrap.top + Math.max(20, (visibleBottom - rect.wrap.top) / 2);
    const dy = targetY - rect.y;
    const end = { x: Math.max(rect.wrap.left + 10, Math.min(Math.min(rect.wrap.right, rect.viewport?.width ?? rect.wrap.right) - 10, start.x + Math.max(-500, Math.min(500, dx)))), y: Math.max(rect.wrap.top + 10, Math.min(visibleBottom - 10, start.y + Math.max(-400, Math.min(400, dy)))) };
    attempts.push({ rect: { x: rect.x, y: rect.y }, start, end });
    await dragMouse(cdp, start, end);
  }
  throw new Error(`could not bring release card ${id} into viewport: ${JSON.stringify({ lastRect, attempts })}`);
}

async function blankReleasePoint(cdp) {
  return pageEvaluate(cdp, `
    const wrap=document.querySelector('#release .release-view-wrap'),svg=wrap?.querySelector('svg');if(!wrap||!svg)return null;const r=wrap.getBoundingClientRect(),cx=(r.left+r.right)/2,cy=(r.top+r.bottom)/2;let best=null,bestDistance=Infinity;
    for(let y=r.top+8;y<r.bottom-8;y+=12)for(let x=r.left+8;x<r.right-8;x+=12){
      const target=document.elementFromPoint(x,y);
      if(target&&target.closest?.('.svg-wrap svg')===svg&&!target.closest?.('g.node,g.edge,canvas,.zoom-hint,.chart-watch-tools,.chronology-nav-popover,[data-chronology-nav-group]')){const distance=(x-cx)**2+(y-cy)**2;if(distance<bestDistance){bestDistance=distance;best={x,y};}}
    }return best||{x:r.left+8,y:r.top+8};
  `);
}

async function releaseSnapshot(cdp) {
  return pageEvaluate(cdp, `
    const panel=document.querySelector('.panel.active'),svg=document.querySelector('#release .release-view-wrap svg');
    const cards=[...(svg?.querySelectorAll('g.release-node[data-release-work-id]')||[])];
    const attr=(el,name)=>el?.getAttribute(name)||'';
    const signature=(el)=>({class:attr(el,'class'),era:attr(el,'data-release-era'),x:attr(el,'x'),y:attr(el,'y'),width:attr(el,'width'),height:attr(el,'height'),rx:attr(el,'rx'),text:(el.textContent||'').trim()});
    // Capture each card path d and layout metadata as rendered by the browser.
    const paths=Object.fromEntries(cards.map(g=>[g.dataset.releaseWorkId,attr(g.querySelector('path'),'d')]));
    const metadata=Object.fromEntries(cards.map(g=>{const date=g.querySelector('.release-date');const label=[...(date?.childNodes||[])].filter(node=>node.nodeType===Node.TEXT_NODE).map(node=>node.textContent).join('').trim();return [g.dataset.releaseWorkId,{precision:attr(g,'data-release-precision'),sortKey:attr(g,'data-release-sort-key'),tbd:attr(g,'data-release-tbd'),isTbd:attr(g,'data-release-tbd')==='true',lane:attr(g,'data-release-lane'),label}]}));
    const audit=window.marvelSelectionAudit?.()||{};
    return {panel:panel?.id||null,viewBox:attr(svg,'viewBox'),cards:cards.map(g=>g.dataset.releaseWorkId),paths,metadata,
      yearAxis:[...svg?.querySelectorAll('.release-history-year,.release-history-year-label')||[]].map(signature),
      frames:[...svg?.querySelectorAll('.release-history-era,.release-lane-row')||[]].map(signature),
      lineCount:svg?.querySelectorAll('line').length||0,edgeCount:svg?.querySelectorAll('g.edge').length||0,chronologyEdgeCount:svg?.querySelectorAll('g.chronology-edge').length||0,
      focus:[...svg?.querySelectorAll('g.release-node.focus,g.release-node.detail-focus')||[]].map(g=>g.dataset.releaseWorkId).sort(),
      selected:[...(audit.selected||[])].sort(),detailFocus:window.marvelDetailFocusId||null,detailText:document.querySelector('#detail')?.textContent||'',
      relationHighlights:svg?.querySelectorAll('g.edge.hl,g.chronology-edge.hl').length||0};
  `);
}

function same(a, b) {
  return JSON.stringify(a) === JSON.stringify(b);
}

function tieBreakReport(snapshot, expected) {
  const expectedOrder = new Map(expected.ids.map((id, index) => [id, index]));
  const bySortAndLane = new Map();
  for (const id of snapshot.cards) {
    const metadata = snapshot.metadata[id] || {};
    if (!metadata.sortKey) continue;
    const groupKey = `${metadata.sortKey}\u0000${metadata.lane || ""}`;
    if (!bySortAndLane.has(groupKey)) bySortAndLane.set(groupKey, []);
    bySortAndLane.get(groupKey).push(id);
  }
  const groups = [];
  const failures = [];
  for (const [groupKey, actual] of bySortAndLane) {
    if (actual.length < 2) continue;
    const [sortKey, lane] = groupKey.split("\u0000");
    const expectedIds = [...actual].sort((a, b) =>
      (expectedOrder.get(a) ?? Number.MAX_SAFE_INTEGER) - (expectedOrder.get(b) ?? Number.MAX_SAFE_INTEGER) || a.localeCompare(b)
    );
    const ok = same(actual, expectedIds);
    groups.push({ sortKey, lane, actual, expected: expectedIds, ok });
    if (!ok) failures.push(`unstable tie-break for sort key ${sortKey} in lane ${lane}`);
  }
  return { groups, failures, ok: failures.length === 0 };
}

function inspectReleaseSnapshot(snapshot, expected) {
  const failures = [];
  if (snapshot.panel !== "release") failures.push(`release panel inactive: ${snapshot.panel}`);
  if (snapshot.cards.length !== WORK_COUNT) failures.push(`card count ${snapshot.cards.length}, expected ${WORK_COUNT}`);
  const cardSet = new Set(snapshot.cards);
  if (cardSet.size !== WORK_COUNT) failures.push("duplicate release card IDs");
  if (!same([...cardSet].sort(), [...expected.ids].sort())) failures.push("release card set differs from expected 131-work set");
  if (snapshot.edgeCount !== 0) failures.push(`release g.edge count ${snapshot.edgeCount}`);
  if (snapshot.chronologyEdgeCount !== 0) failures.push(`release g.chronology-edge count ${snapshot.chronologyEdgeCount}`);
  if (snapshot.lineCount < 1) failures.push("release year/marker line signature is empty");
  for (const id of expected.ids) {
    const meta = expected.byId.get(id) || {};
    const card = snapshot.metadata[id];
    if (!card) { failures.push(`missing metadata for ${id}`); continue; }
    const precision = meta.release_precision || "unknown";
    const tbd = !meta.release_sort_date || ["none", "undated", "tbd"].includes(precision);
    const sortKey = tbd ? "9999-99-99" : meta.release_sort_date;
    if (card.precision !== precision) failures.push(`${id} precision ${card.precision} != ${precision}`);
    if (card.sortKey !== sortKey) failures.push(`${id} sort key ${card.sortKey} != ${sortKey}`);
    if (card.tbd !== String(tbd) || card.isTbd !== tbd) failures.push(`${id} TBD marker ${card.tbd} != ${tbd}`);
    if (!card.label) failures.push(`${id} has empty release label`);
    // Month/year labels must not invent a day from a partial date; invented day values are failures.
    if (precision === "month" && /^\d{4}\.\d{2}\.\d{2}/.test(card.label)) failures.push(`${id} month label invents a day: ${card.label}`);
    if (precision === "year" && /\.\d{2}\.\d{2}/.test(card.label)) failures.push(`${id} year label invents a day: ${card.label}`);
  }
  failures.push(...tieBreakReport(snapshot, expected).failures);
  return failures;
}

async function waitReleaseState(cdp, id, timeoutMs) {
  let last = null;
  try {
    return await poll(async () => {
      const snapshot = await releaseSnapshot(cdp);
      last = snapshot;
      // Desktop left-click is the public detail-inspection action; goal
      // selection remains a right-click/mobile concern. Both focus and the
      // shared detail ID must nevertheless target the clicked work.
      return snapshot.panel === "release" && same(snapshot.focus, [id]) && same(snapshot.selected, []) && snapshot.detailFocus === id ? snapshot : null;
    }, timeoutMs, `release selection ${id}`);
  } catch (error) {
    throw new Error(`${error.message}; last=${JSON.stringify(last)}`);
  }
}

async function selectReleaseCard(cdp, id, timeoutMs) {
  await centerReleaseCard(cdp, id, timeoutMs);
  const rect = await releaseCardRect(cdp, id);
  await clickPoint(cdp, rect);
  try {
    return await waitReleaseState(cdp, id, timeoutMs);
  } catch (error) {
    throw new Error(`${error.message}; clicked=${JSON.stringify(rect)}`);
  }
}

async function installSyntheticYearPrecisionFixture(cdp, id, year, timeoutMs) {
  const installed = await pageEvaluate(cdp, `
    const meta=RELEASE_META[${JSON.stringify(id)}],panel=document.getElementById('release');
    if(!meta||!panel)return false;
    meta.sortDate=${JSON.stringify(year)};meta.displayDate=${JSON.stringify(year)};meta.precision='year';
    panel.innerHTML='';panel.dataset.lazyInitialized='0';
    return window.ensureStageAViewInitialized?.('release')===true;
  `);
  if (!installed) throw new Error(`could not install synthetic year-only fixture for ${id}`);
  return poll(async () => {
    const snapshot = await releaseSnapshot(cdp);
    const metadata = snapshot.metadata[id];
    return snapshot.panel === "release" && snapshot.cards.length === WORK_COUNT && metadata?.precision === "year" && metadata?.label === year ? snapshot : null;
  }, timeoutMs, `synthetic year-only fixture ${id}`);
}

async function clearReleaseSelection(cdp, timeoutMs) {
  const point = await poll(() => blankReleasePoint(cdp), timeoutMs, "release background point");
  await clickPoint(cdp, point);
  let last = null;
  try {
    return await poll(async () => {
      const snapshot = await releaseSnapshot(cdp);
      last = snapshot;
      return snapshot.selected.length === 0 && snapshot.detailFocus === null ? snapshot : null;
    }, timeoutMs, "release selection clear");
  } catch (error) {
    throw new Error(`${error.message}; last=${JSON.stringify(last)}; point=${JSON.stringify(point)}`);
  }
}

async function runDesktopAudit(cdp, url, expected, timeoutMs) {
  await loadPage(cdp, url, timeoutMs);
  await clickSelector(cdp, '.tab[data-target="release"]', timeoutMs);
  await poll(async () => {
    const snapshot = await releaseSnapshot(cdp);
    return snapshot.panel === "release" && snapshot.cards.length === WORK_COUNT ? snapshot : null;
  }, timeoutMs, "release view readiness");
  const baseline = await releaseSnapshot(cdp);
  const failures = inspectReleaseSnapshot(baseline, expected);
  const available = (precision) => expected.ids.find((id) => {
    const node = expected.byId.get(id) || {};
    return (node.release_precision || "unknown") === precision;
  });
  PC_CASES[1].id = available("month");
  PC_CASES[2].id = available("year");
  PC_CASES[3].id = expected.ids.find((id) => {
    const node = expected.byId.get(id) || {};
    return !node.release_sort_date || ["none", "undated", "tbd"].includes(node.release_precision);
  });
  const caseReports = [];
  const roundTrip = {
    release_to_overview: false,
    overview_to_release: false,
    release_to_chronology: false,
    chronology_to_release: false,
    chronology: null,
  };
  for (const testCase of PC_CASES) {
    let syntheticFixture = null;
    if (testCase.name === "year-only" && !testCase.id) {
      const candidate = expected.ids.find((id) => (expected.byId.get(id)?.release_precision || "unknown") === "month") || available("day");
      if (!candidate) throw new Error("no dated work available for the synthetic year-only browser fixture");
      const year = String(expected.byId.get(candidate)?.release_sort_date || "2026").slice(0, 4);
      await installSyntheticYearPrecisionFixture(cdp, candidate, year, timeoutMs);
      testCase.id = candidate;
      syntheticFixture = { kind: "runtime-year-precision", year };
    }
    if (!testCase.id) {
      caseReports.push({ name: testCase.name, skipped: true, reason: `no ${testCase.precision} fixture in exported metadata` });
      continue;
    }
    const before = await releaseSnapshot(cdp);
    const after = await selectReleaseCard(cdp, testCase.id, timeoutMs);
    const invariant = ["cards", "paths", "viewBox", "yearAxis", "frames", "lineCount", "edgeCount", "chronologyEdgeCount"];
    const invariantFailures = invariant.filter((field) => !same(before[field], after[field])).map((field) => `${testCase.name} changed ${field}`);
    const selectedMeta = after.metadata[testCase.id];
    if (selectedMeta?.precision !== testCase.precision) invariantFailures.push(`${testCase.name} selected precision mismatch`);
    if (after.relationHighlights !== 0) invariantFailures.push(`${testCase.name} release relation highlights ${after.relationHighlights}`);
    failures.push(...invariantFailures);
    const releaseFocus = same(after.focus, [testCase.id]) && same(after.selected, []) && after.detailFocus === testCase.id;
    if (!releaseFocus) failures.push(`${testCase.name} release focus/shared selection/detail was not exclusive to ${testCase.id}`);
    if (testCase.name === "exact-day") {
      await clickSelector(cdp, '.tab[data-target="overview"]', timeoutMs);
      const overview = await poll(() => pageEvaluate(cdp, `
        const p=document.querySelector('.panel.active'),s=document.querySelector('.panel.active .svg-wrap svg'),a=window.marvelSelectionAudit?.()||{};
        const focus=[...s?.querySelectorAll('g.node.focus')||[]].map(g=>(g.querySelector(':scope > title')?.textContent||'').trim()),edges=s?.querySelectorAll('g.edge.hl,g.chronology-edge.hl').length||0;
        focus.sort();const selected=[...(a.selected||[])].sort();
        return p?.id==='overview'&&window.marvelDetailFocusId===${JSON.stringify(testCase.id)}&&JSON.stringify(focus)===JSON.stringify([${JSON.stringify(testCase.id)}])&&selected.length===0&&edges>0?{panel:p.id,selected,edges,focus,detailAudit:window.marvelDetailFocusAudit?.()||null,renderType:typeof window.marvelRenderDetailFocus,nodeIds:[...s?.querySelectorAll('g.node')||[]].slice(0,3).map(g=>({id:g.dataset?.releaseWorkId||'',title:(g.querySelector(':scope > title')?.textContent||'').trim()})),hasNode:[...s?.querySelectorAll('g.node')||[]].some(g=>(g.querySelector(':scope > title')?.textContent||'').trim()===${JSON.stringify(testCase.id)})}:null;
      `), timeoutMs, "overview selection round-trip");
      if (!same(overview.focus, [testCase.id]) || !same(overview.selected, [])) failures.push(`overview did not restore exclusive detail focus: ${JSON.stringify(overview)}`);
      if (overview.edges <= 0) failures.push(`overview relation highlights did not return there: ${JSON.stringify(overview)}`);
      roundTrip.release_to_overview = true;
      await clickSelector(cdp, '.tab[data-target="release"]', timeoutMs);
      const returned = await poll(async () => {
        const s = await releaseSnapshot(cdp);
        return s.panel === "release" && same(s.focus, [testCase.id]) && same(s.selected, []) && s.detailFocus === testCase.id ? s : null;
      }, timeoutMs, "overview to release round-trip");
      if (returned.relationHighlights !== 0) failures.push("release relation highlights leaked after round-trip");
      for (const field of invariant) if (!same(before[field], returned[field])) failures.push(`round-trip changed ${field}`);
      roundTrip.overview_to_release = true;

      await clickSelector(cdp, '.tab[data-target="chronology"]', timeoutMs);
      const chronology = await poll(() => pageEvaluate(cdp, `
        const panel=document.querySelector('.panel.active'),svg=panel?.querySelector('.svg-wrap svg'),audit=window.marvelSelectionAudit?.()||{};
        const chronologyEdges=svg?.querySelectorAll('g.chronology-edge').length||0;
        const chronologyHighlights=svg?.querySelectorAll('g.chronology-edge.hl').length||0;
        const focus=[...svg?.querySelectorAll('g.node.focus')||[]].map(g=>(g.querySelector(':scope > title')?.textContent||'').trim()).sort(),selected=[...(audit.selected||[])].sort();
        const ready=panel?.id==='chronology'&&panel.dataset.lazyInitialized==='1'&&chronologyEdges > 0;
        return ready&&window.marvelDetailFocusId===${JSON.stringify(testCase.id)}&&JSON.stringify(focus)===JSON.stringify([${JSON.stringify(testCase.id)}])&&selected.length===0?{panel:panel.id,ready,chronologyEdges,chronologyHighlights,focus,selected,detailFocus:window.marvelDetailFocusId}:null;
      `), timeoutMs, "chronology panel readiness");
      roundTrip.release_to_chronology = true;
      roundTrip.chronology = chronology;
      await clickSelector(cdp, '.tab[data-target="release"]', timeoutMs);
      const chronologyReturned = await poll(async () => {
        const snapshot = await releaseSnapshot(cdp);
        return snapshot.panel === "release" && same(snapshot.focus, [testCase.id]) && same(snapshot.selected, []) && snapshot.detailFocus === testCase.id ? snapshot : null;
      }, timeoutMs, "chronology to release round-trip");
      const chronologyFailures = [];
      if (chronologyReturned.relationHighlights !== 0) chronologyFailures.push("chronology round-trip leaked release relation highlights");
      if (chronologyReturned.edgeCount !== 0) chronologyFailures.push(`chronology round-trip release g.edge count ${chronologyReturned.edgeCount}`);
      if (chronologyReturned.chronologyEdgeCount !== 0) chronologyFailures.push(`chronology round-trip release g.chronology-edge count ${chronologyReturned.chronologyEdgeCount}`);
      for (const field of invariant) if (!same(before[field], chronologyReturned[field])) chronologyFailures.push(`chronology round-trip changed ${field}`);
      failures.push(...chronologyFailures);
      roundTrip.chronology_to_release = true;
      caseReports.push({ name: "chronology-middle-round-trip", id: testCase.id, chronology, after: chronologyReturned, failures: chronologyFailures, ok: chronologyFailures.length === 0 });
    }
    caseReports.push({ name: testCase.name, id: testCase.id, precision: testCase.precision, syntheticFixture, before, after, ok: invariantFailures.length === 0 && releaseFocus });
    await clearReleaseSelection(cdp, timeoutMs);
    if (syntheticFixture) {
      await loadPage(cdp, url, timeoutMs);
      await clickSelector(cdp, '.tab[data-target="release"]', timeoutMs);
      await poll(async () => {
        const snapshot = await releaseSnapshot(cdp);
        return snapshot.panel === "release" && snapshot.cards.length === WORK_COUNT ? snapshot : null;
      }, timeoutMs, "release view restoration after synthetic year fixture");
    }
  }
  return { baseline, failures, cases: caseReports, roundTrip };
}

async function setMobileViewport(cdp, timeoutMs) {
  await cdp.send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
  await poll(() => pageEvaluate(cdp, "return window.matchMedia('(max-width:760px)').matches"), timeoutMs, "mobile viewport readiness");
}

async function clearMobileViewport(cdp, timeoutMs) {
  await cdp.send("Emulation.clearDeviceMetricsOverride");
  await poll(() => pageEvaluate(cdp, "return !window.matchMedia('(max-width:760px)').matches"), timeoutMs, "desktop viewport restoration");
}

async function mobileSnapshot(cdp) {
  return pageEvaluate(cdp, `
    const audit=window.marvelCanvasAudit?.()||{},selection=window.marvelSelectionAudit?.()||{},detail=window.marvelDetailFocusAudit?.()||{};
    const wrap=document.querySelector('#release .release-view-wrap');
    return {panel:audit.panel,active:audit.active,nodeBoxes:audit.nodeBoxes||0,selected:[...(selection.selected||[])].sort(),goals:[...(detail.goals||selection.selected||[])].sort(),detailFocus:detail.focus||null,overlaySyntheticDrawn:audit.overlaySyntheticDrawn||0,camera:audit.camera||null,wrapRect:(()=>{const r=wrap?.getBoundingClientRect();return r?{left:r.left,right:r.right,top:r.top,bottom:r.bottom}:null;})()};
  `);
}

async function mobilePointForWork(cdp, id, timeoutMs) {
  return poll(() => pageEvaluate(cdp, `
    const wrap=document.querySelector('#release .release-view-wrap'),audit=window.marvelCanvasAudit?.()||{};
    wrap?.scrollIntoView({block:'center',inline:'center'});
    const state=wrap&&mobileCanvasStates.get(wrap),view=wrap&&ensureMobileViewBoxState(wrap),node=state?.nodeBoxes?.find(item=>item.id===${JSON.stringify(id)});
    if(audit.active!==true||audit.panel!=="release"||!state||!view||!node)return null;
    const aspect=mobileViewportAspect(wrap,view),nw=Math.min(view.vbW,Math.max(node.box.w*8,node.box.h*8*aspect)),nh=nw/aspect;
    setMobileViewBox(wrap,view,node.box.x+node.box.w/2-nw/2,node.box.y+node.box.h/2-nh/2,nw,nh);applyView(wrap);
    const r=wrap.getBoundingClientRect(),m=mobileViewBoxMetrics(wrap,view),x=r.left+m.offsetX+(node.box.x+node.box.w/2-view.vbX)*m.pxPerWorld,y=r.top+m.offsetY+(node.box.y+node.box.h/2-view.vbY)*m.pxPerWorld;
    const hit=document.elementFromPoint(x,y);return x>=r.left&&x<=r.right&&y>=r.top&&y<=r.bottom?{x,y,world:{x:node.box.x+node.box.w/2,y:node.box.y+node.box.h/2},box:node.box,rect:{left:r.left,right:r.right,top:r.top,bottom:r.bottom},camera:{x:view.vbX,y:view.vbY,w:view.vbW,h:view.vbH},hit:hit?{tag:hit.tagName,class:hit.getAttribute?.('class')||'',canvas:!!hit.closest?.('canvas[data-marvel-mobile-canvas]')}:null,hitTest:mobileCanvasHitTest(wrap,x,y)}:null;
  `), timeoutMs, `mobile release card ${id}`);
}

async function mobileBlankPoint(cdp, timeoutMs) {
  return poll(() => pageEvaluate(cdp, `
    const wrap=document.querySelector('#release .release-view-wrap'),audit=window.marvelCanvasAudit?.(),r=wrap?.getBoundingClientRect(),state=wrap&&mobileCanvasStates.get(wrap),view=wrap&&ensureMobileViewBoxState(wrap);
    if(!wrap||!r||!state||!view)return null;const m=mobileViewBoxMetrics(wrap,view),boxes=state.nodeBoxes||[],right=Math.min(r.right,innerWidth),bottom=Math.min(r.bottom,innerHeight);
    for(let y=r.top+18;y<bottom-18;y+=16)for(let x=r.left+8;x<right-8;x+=16){const w=mobileClientToWorld(wrap,view,x,y,r);if(boxes.every(n=>w.x<n.box.x||w.x>n.box.x2||w.y<n.box.y||w.y>n.box.y2))return{x,y};}return{x:r.left+8,y:Math.min(bottom-8,r.top+8)};
  `), timeoutMs, "mobile release background point");
}

async function waitMobile(cdp, predicate, timeoutMs, label) {
  return poll(async () => {
    const state = await mobileSnapshot(cdp);
    return predicate(state) ? state : null;
  }, timeoutMs, label);
}

async function activateMobileRelease(cdp, timeoutMs) {
  await clickSelector(cdp, "#mobileAreaButton", timeoutMs);
  await clickSelector(cdp, '.mobile-area-sheet [data-mobile-target="release"]', timeoutMs);
  await waitMobile(cdp, (s) => s.active === true && s.panel === "release" && s.nodeBoxes === WORK_COUNT, timeoutMs, "mobile release Canvas readiness");
}

async function selectMobile(cdp, id, timeoutMs) {
  const point = await mobilePointForWork(cdp, id, timeoutMs);
  await touchTap(cdp, point);
  try {
    return await waitMobile(cdp, (s) => same(s.selected, [id]) && same(s.goals, [id]) && s.nodeBoxes === WORK_COUNT && s.overlaySyntheticDrawn === 0, timeoutMs, `mobile selection ${id}`);
  } catch (error) {
    throw new Error(`${error.message}; point=${JSON.stringify(point)}; state=${JSON.stringify(await mobileSnapshot(cdp))}`);
  }
}

async function installSyntheticMobileYearPrecisionFixture(cdp, id, year, timeoutMs) {
  const installed = await pageEvaluate(cdp, `
    const meta=RELEASE_META[${JSON.stringify(id)}],panel=document.getElementById('release');
    if(!meta||!panel)return false;
    meta.sortDate=${JSON.stringify(year)};meta.displayDate=${JSON.stringify(year)};meta.precision='year';
    panel.innerHTML='';panel.dataset.lazyInitialized='0';panel.removeAttribute('data-release-camera-ready');
    const initialized=window.ensureStageAViewInitialized?.('release')===true;
    if(initialized)window.activatePanel?.('release',{fit:true,restoreSelection:false,exitFeatured:false});
    return initialized;
  `);
  if (!installed) throw new Error(`could not install synthetic mobile year-only fixture for ${id}`);
  return poll(() => pageEvaluate(cdp, `
    const panel=document.querySelector('.panel.active'),wrap=panel?.querySelector('.release-view-wrap'),audit=window.marvelCanvasAudit?.()||{};
    const card=[...(wrap?.querySelectorAll('g.release-node[data-release-work-id]')||[])].find(g=>g.dataset.releaseWorkId===${JSON.stringify(id)});
    const date=card?.querySelector('.release-date'),label=[...(date?.childNodes||[])].filter(node=>node.nodeType===Node.TEXT_NODE).map(node=>node.textContent).join('').trim();
    return panel?.id==='release'&&audit.active===true&&audit.panel==='release'&&audit.nodeBoxes===${WORK_COUNT}&&card?.dataset.releasePrecision==='year'&&label===${JSON.stringify(year)}?{id:${JSON.stringify(id)},year:${JSON.stringify(year)},precision:card.dataset.releasePrecision,label,nodeBoxes:audit.nodeBoxes}:null;
  `), timeoutMs, `synthetic mobile year-only fixture ${id}`);
}

async function runMobileAudit(cdp, url, expected, timeoutMs) {
  await loadPage(cdp, url, timeoutMs);
  await setMobileViewport(cdp, timeoutMs);
  const failures = [];
  const cases = [];
  try {
    await activateMobileRelease(cdp, timeoutMs);
    const available = (precision) => expected.ids.find((id) => (expected.byId.get(id)?.release_precision || "unknown") === precision);
    const exactDayId = available("day");
    const monthId = available("month");
    const yearId = available("year");
    const tbdId = expected.ids.find((id) => !expected.byId.get(id)?.release_sort_date || ["none", "undated", "tbd"].includes(expected.byId.get(id)?.release_precision)) || expected.ids.at(-1);
    const mobileCases = [
      { name: "exact-day-touch", precision: "day", id: exactDayId },
      { name: "month-only-touch", precision: "month", id: monthId },
      { name: "year-only-touch", precision: "year", id: yearId },
      { name: "tbd-touch", precision: "none", id: tbdId },
    ];
    for (let caseIndex = 0; caseIndex < mobileCases.length; caseIndex += 1) {
      const testCase = mobileCases[caseIndex];
      if (caseIndex > 0) {
        await loadPage(cdp, url, timeoutMs);
        await activateMobileRelease(cdp, timeoutMs);
      }
      let syntheticFixture = null;
      if (testCase.name === "year-only-touch" && !testCase.id) {
        const candidate = available("month") || available("day");
        if (!candidate) throw new Error("no dated work available for the synthetic mobile year-only browser fixture");
        const year = String(expected.byId.get(candidate)?.release_sort_date || "2026").slice(0, 4);
        const rendered = await installSyntheticMobileYearPrecisionFixture(cdp, candidate, year, timeoutMs);
        testCase.id = candidate;
        syntheticFixture = { kind: "runtime-year-precision", year, rendered };
      }
      const { name, id, precision } = testCase;
      if (!id) throw new Error(`no ${precision} work available for mobile publication-order audit`);
      let state = await selectMobile(cdp, id, timeoutMs);
      if (state.nodeBoxes !== WORK_COUNT) failures.push(`${name} nodeBoxes ${state.nodeBoxes} != ${WORK_COUNT}`);
      if (!same(state.selected, [id]) || !same(state.goals, [id])) failures.push(`${name} shared mobile selection/goal was not exclusive to ${id}`);
      if (state.overlaySyntheticDrawn > 0) failures.push(`${name} synthetic overlay drawn: ${state.overlaySyntheticDrawn}`);
      cases.push({ name: `${name}-select`, id, precision, syntheticFixture, state });
      const selectedPoint = await mobilePointForWork(cdp, id, timeoutMs);
      await touchTap(cdp, selectedPoint);
      state = await waitMobile(cdp, (s) => same(s.selected, []) && same(s.goals, []) && s.nodeBoxes === WORK_COUNT && s.overlaySyntheticDrawn === 0, timeoutMs, `${name} re-tap clear`);
      if (state.overlaySyntheticDrawn > 0) failures.push(`${name} re-tap synthetic overlay drawn: ${state.overlaySyntheticDrawn}`);
      cases.push({ name: `${name}-re-tap`, id, precision, syntheticFixture, state });
      await selectMobile(cdp, id, timeoutMs);
      const background = await mobileBlankPoint(cdp, timeoutMs);
      await touchTap(cdp, background);
      state = await waitMobile(cdp, (s) => same(s.selected, []) && same(s.goals, []) && s.nodeBoxes === WORK_COUNT && s.overlaySyntheticDrawn === 0, timeoutMs, `${name} background clear`);
      if (state.overlaySyntheticDrawn > 0) failures.push(`${name} background synthetic overlay drawn: ${state.overlaySyntheticDrawn}`);
      cases.push({ name: `${name}-background`, id, precision, syntheticFixture, state });
      state = await selectMobile(cdp, id, timeoutMs);
      const dragStart = await mobilePointForWork(cdp, id, timeoutMs);
      const dragEnd = { x: Math.min(370, dragStart.x + 70), y: Math.min(830, dragStart.y + 80) };
      const cameraBeforeDrag = state.camera;
      await touchDrag(cdp, dragStart, dragEnd);
      try {
        state = await waitMobile(cdp, (s) => same(s.selected, [id]) && same(s.goals, [id]) && s.nodeBoxes === WORK_COUNT && s.overlaySyntheticDrawn === 0 && !same(s.camera, cameraBeforeDrag), timeoutMs, `${name} drag-end selection preservation`);
      } catch (error) {
        throw new Error(`${error.message}; start=${JSON.stringify(dragStart)}; end=${JSON.stringify(dragEnd)}; before=${JSON.stringify(cameraBeforeDrag)}; after=${JSON.stringify(await mobileSnapshot(cdp))}`);
      }
      cases.push({ name: `${name}-drag-end`, id, precision, syntheticFixture, state });
    }
  } finally {
    await clearMobileViewport(cdp, timeoutMs);
  }
  return { failures, cases };
}

async function runAudit(args) {
  const root = path.resolve(args.root || ".");
  const timeoutMs = Number(args.timeout_ms || WAIT_TIMEOUT_MS);
  if (!Number.isInteger(timeoutMs) || timeoutMs < 1_000) throw new Error("--timeout-ms must be an integer >= 1000");
  const expected = loadExpected(root);
  const chrome = locateChrome(args.chrome);
  const staticServer = await startStaticServer(root);
  let chromeProcess = null;
  let cdp = null;
  let desktop = null;
  let mobile = null;
  try {
    chromeProcess = await launchChrome(chrome, timeoutMs);
    cdp = new CdpClient(chromeProcess.webSocketDebuggerUrl);
    await cdp.connect();
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");
    desktop = await runDesktopAudit(cdp, staticServer.url, expected, timeoutMs);
    mobile = await runMobileAudit(cdp, staticServer.url, expected, timeoutMs);
  } finally {
    cdp?.close();
    if (chromeProcess) await stopChrome(chromeProcess);
    // Close the browser before the fixture server. Chrome may retain an idle
    // keep-alive request, which otherwise prevents server.close's callback
    // from firing and leaves the wrapper waiting after a successful audit.
    await new Promise((resolve) => staticServer.server.close(() => resolve()));
  }
  const cases = [...(desktop?.cases || []), ...(mobile?.cases || [])];
  const failures = [...(desktop?.failures || []), ...(mobile?.failures || [])];
  const syntheticEdges = Math.max(0, ...cases.map((item) => item.state?.overlaySyntheticDrawn || 0));
  const desktopCases = desktop?.cases?.filter((item) => !item.skipped) || [];
  const precisionNames = new Set(PC_CASES.map((item) => item.name));
  const precision = Object.fromEntries(desktopCases.filter((item) => precisionNames.has(item.name)).map((item) => [item.name, {
    id: item.id,
    precision: item.after?.metadata?.[item.id]?.precision || null,
    sortKey: item.after?.metadata?.[item.id]?.sortKey || null,
    label: item.after?.metadata?.[item.id]?.label || null,
    syntheticFixture: item.syntheticFixture || null,
  }]));
  const tbdCase = desktopCases.find((item) => item.name === "tbd");
  const ties = desktop?.baseline ? tieBreakReport(desktop.baseline, expected) : { groups: [], failures: ["baseline unavailable"], ok: false };
  const report = {
    summary: { cards: desktop?.baseline?.cards?.length || 0, cases: cases.length, failures: failures.length, syntheticEdges },
    structural: { cards: desktop?.baseline?.cards?.length || 0, duplicate_ids: desktop?.baseline ? [...new Set(desktop.baseline.cards)].length !== desktop.baseline.cards.length : true, edge_count: desktop?.baseline?.edgeCount || 0, chronology_edge_count: desktop?.baseline?.chronologyEdgeCount || 0 },
    focus: {
      desktop: desktopCases.map((item) => ({ id: item.id, focused: same(item.after?.focus || [], [item.id]), focusIds: item.after?.focus || [], selected: item.after?.selected || [], detailWorkId: item.after?.detailFocus || null })),
      mobile: (mobile?.cases || []).filter((item) => item.name.endsWith("-select")).map((item) => ({ id: item.id, goals: item.state?.goals || [], detailWorkId: item.state?.detailFocus || null })),
    },
    geometry: { viewBox: desktop?.baseline?.viewBox || null, lineCount: desktop?.baseline?.lineCount || 0, failures: failures.filter((failure) => /changed|geometry|viewBox|path|axis|frame|lineCount/.test(failure)) },
    line_free: { svgEdges: desktop?.baseline?.edgeCount || 0, svgChronologyEdges: desktop?.baseline?.chronologyEdgeCount || 0, canvasSyntheticEdges: syntheticEdges, ok: (desktop?.baseline?.edgeCount || 0) === 0 && (desktop?.baseline?.chronologyEdgeCount || 0) === 0 && syntheticEdges === 0 },
    precision,
    tbd: tbdCase ? { id: tbdCase.id, metadata: tbdCase.after?.metadata?.[tbdCase.id] || null } : null,
    tie_break: ties,
    round_trip: desktop?.roundTrip || { release_to_overview: false, overview_to_release: false, release_to_chronology: false, chronology_to_release: false, chronology: null },
    mobile: { viewport: [390, 844], nodeBoxes: mobile?.cases?.map((item) => item.state?.nodeBoxes || 0) || [], syntheticEdges, cases: mobile?.cases || [] },
    cases,
    failures,
  };
  return report;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    process.stdout.write(`${usage()}\n`);
    return;
  }
  try {
    const report = await runAudit(args);
    process.stdout.write(`${JSON.stringify(report)}\n`);
    if (report.summary.failures || report.summary.syntheticEdges) process.exitCode = 1;
  } catch (error) {
    process.stderr.write(`${error.stack || error}\n`);
    process.exitCode = 1;
  }
}

main();
