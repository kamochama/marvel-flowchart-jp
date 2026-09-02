#!/usr/bin/env node

import fs from "node:fs";
import http from "node:http";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import { execFileSync, spawn } from "node:child_process";

const DEFAULT_TIMEOUT_MS = 20_000;
const PROFILE_RETRIES = 100;
const CHRONOLOGY_EDGE_COUNT = 74;
const PRIMARY_WORK = "iron-man-2008";
const SECONDARY_WORK = "iron-man-2-2010";
const MOBILE_WORK = "blade-mcu-tba-tba";
const ORACLE_EDGE_IDS = {
  captain_to_iron: "sequence-captain-marvel-2019-iron-man-2008-mcu-main-2",
  iron_to_iron2: "sequence-iron-man-2008-iron-man-2-2010-mcu-main-3",
  iron2_to_hulk: "sequence-iron-man-2-2010-the-incredible-hulk-2008-mcu-main-4",
};
const MODE_ORACLE = {
  complete: {captain_to_iron: "backhl", iron_to_iron2: "forwardhl"},
  "site-proposal": {iron_to_iron2: "forwardhl"},
  or: {captain_to_iron: "backhl", iron_to_iron2: "bothhl"},
  and: {iron_to_iron2: "bothhl"},
  path: {iron_to_iron2: "pathhl"},
};
// The structural contract is intentionally keyed by the exported
// data-chronology-edge-id attribute (not by a release/overview graph edge).

function usage() {
  return [
    "Usage: node browser_chronology_audit.mjs --root <repo> [--chrome <path>]",
    "",
    "Audits the public chronology display with real Chrome CDP pointer events.",
    "Checks stable edge-id metadata, non-traversable/display-only safety, five public modes",
    "plus the internal-unit-only previous1 boundary,",
    "SVG/Canvas chronology materialization parity, and overview/chronology round trips.",
    "",
    "Options:",
    "  --root <path>      Repository root to serve over HTTP",
    "  --chrome <path>    Chrome/Chromium executable (otherwise auto-detected)",
    "  --timeout-ms <n>   Per-condition timeout (default 20000)",
    "  --help             Show this help (includes non-traversable and edge-id contract)",
  ].join("\n");
}

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (token === "--help") { args.help = true; continue; }
    if (!token.startsWith("--")) throw new Error(`unexpected argument: ${token}`);
    const key = token.slice(2).replaceAll("-", "_");
    const value = argv[i + 1];
    if (!value || value.startsWith("--")) throw new Error(`missing value for --${key.replaceAll("_", "-")}`);
    args[key] = value;
    i += 1;
  }
  return args;
}

function locateChrome(configured) {
  const names = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"];
  const commands = names.flatMap((name) => {
    try {
      const command = process.platform === "win32" ? "where.exe" : "which";
      const found = execFileSync(command, [name], { encoding: "utf8" }).split(/\r?\n/)[0].trim();
      return found ? [found] : [];
    } catch (_) { return []; }
  });
  const candidates = [
    configured, process.env.MARVEL_CHROME_BIN, process.env.CHROME_BIN, ...commands,
    "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
    "C:/Program Files/Google/Chrome/Application/chrome.exe",
    "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    `${process.env.LOCALAPPDATA || ""}/Google/Chrome/Application/chrome.exe`,
  ].filter(Boolean);
  for (const candidate of candidates) {
    if (path.isAbsolute(candidate) && fs.existsSync(candidate)) return candidate;
    if (!path.isAbsolute(candidate)) {
      const found = candidate.split(path.delimiter).find((item) => item && fs.existsSync(item));
      if (found) return found;
    }
  }
  throw new Error("Chrome/Chromium executable not found; pass --chrome or MARVEL_CHROME_BIN");
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
    ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
    ".json": "application/json", ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml",
  }[path.extname(filePath).toLowerCase()] || "application/octet-stream";
}

async function startStaticServer(root) {
  const resolvedRoot = fs.realpathSync(root);
  const server = http.createServer((request, response) => {
    try {
      const pathname = decodeURIComponent(new URL(request.url || "/", "http://localhost").pathname);
      const relative = pathname === "/" ? "index.html" : pathname.replace(/^\/+/, "");
      const filePath = path.resolve(resolvedRoot, relative);
      const check = path.relative(resolvedRoot, filePath);
      if (check.startsWith("..") || path.isAbsolute(check)) { response.writeHead(403); response.end("forbidden"); return; }
      if (!fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) { response.writeHead(404); response.end("not found"); return; }
      response.writeHead(200, { "Content-Type": contentType(filePath), "Cache-Control": "no-store" });
      fs.createReadStream(filePath).pipe(response);
    } catch (error) { response.writeHead(400); response.end(String(error?.message || error)); }
  });
  await new Promise((resolve, reject) => { server.once("error", reject); server.listen(0, "127.0.0.1", resolve); });
  const address = server.address();
  if (typeof address !== "object" || !address) throw new Error("static server address unavailable");
  return { server, url: `http://127.0.0.1:${address.port}/index.html` };
}

async function poll(task, timeoutMs, label) {
  const deadline = Date.now() + timeoutMs;
  let lastError = null;
  while (Date.now() < deadline) {
    try { const value = await task(); if (value) return value; }
    catch (error) { lastError = error; }
    await new Promise((resolve) => setTimeout(resolve, 50));
  }
  throw new Error(`${label} timed out${lastError ? `: ${lastError.message}` : ""}`);
}

async function launchChrome(chromePath, timeoutMs) {
  const port = await freePort();
  const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), "marvel-flowchart-chronology-cdp-"));
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
  } catch (error) { await stopChrome({ child, userDataDir }); throw error; }
}

async function stopChrome(processInfo) {
  const child = processInfo?.child;
  if (child && child.exitCode === null && !child.killed) {
    const exited = new Promise((resolve) => child.once("exit", resolve));
    child.kill();
    await Promise.race([exited, new Promise((resolve) => setTimeout(resolve, 5_000))]);
  }
  if (processInfo?.userDataDir) fs.rmSync(processInfo.userDataDir, { recursive: true, force: true, maxRetries: PROFILE_RETRIES, retryDelay: 100 });
}

class CdpClient {
  constructor(url) { this.url = url; this.nextId = 1; this.pending = new Map(); }
  async connect() {
    this.socket = new WebSocket(this.url);
    await new Promise((resolve, reject) => {
      this.socket.addEventListener("open", resolve, { once: true });
      this.socket.addEventListener("error", () => reject(new Error("CDP WebSocket error")), { once: true });
    });
    this.socket.addEventListener("message", (event) => {
      const message = JSON.parse(String(event.data));
      if (!message.id) return;
      const pending = this.pending.get(message.id); if (!pending) return;
      this.pending.delete(message.id);
      if (message.error) pending.reject(new Error(message.error.message || "CDP command failed"));
      else pending.resolve(message.result || {});
    });
    this.socket.addEventListener("close", () => { for (const { reject } of this.pending.values()) reject(new Error("CDP socket closed")); this.pending.clear(); });
  }
  send(method, params = {}) {
    const id = this.nextId++;
    return new Promise((resolve, reject) => { this.pending.set(id, { resolve, reject }); this.socket.send(JSON.stringify({ id, method, params })); });
  }
  async evaluate(expression) {
    const result = await this.send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
    if (result.exceptionDetails) throw new Error(result.exceptionDetails.exception?.description || "page evaluation failed");
    return result.result?.value;
  }
  close() { try { this.socket?.close(); } catch (_) { /* best effort */ } }
}

const evaluate = (cdp, body) => cdp.evaluate(`(() => { ${body} })()`);
const clickPoint = async (cdp, point, button = "left") => {
  await cdp.send("Input.dispatchMouseEvent", { type: "mouseMoved", x: point.x, y: point.y });
  await cdp.send("Input.dispatchMouseEvent", { type: "mousePressed", x: point.x, y: point.y, button, clickCount: 1 });
  await cdp.send("Input.dispatchMouseEvent", { type: "mouseReleased", x: point.x, y: point.y, button, clickCount: 1 });
};

async function loadPage(cdp, url, timeoutMs) {
  await cdp.send("Page.navigate", { url });
  await poll(() => evaluate(cdp, "return document.readyState === 'complete'"), timeoutMs, "page load");
  // Chronology is lazily materialized when its public tab is opened.
  await clickSelector(cdp, '.tab[data-target="chronology"]', timeoutMs);
  try { await poll(() => evaluate(cdp, `
    const svg=document.querySelector('#chronology .svg-wrap svg');
    return !!svg && svg.querySelectorAll('g.node').length >= 100 &&
      svg.querySelectorAll('g.chronology-edge').length === ${CHRONOLOGY_EDGE_COUNT} &&
      !!document.querySelector('#chartConnectionTier');
  `), timeoutMs, "chronology DOM readiness"); } catch (error) {
    const state=await evaluate(cdp, `const s=document.querySelector('#chronology .svg-wrap svg'); return {ready:document.documentElement.dataset.flowchartState||'',svg:!!s,nodes:s?.querySelectorAll('g.node').length||0,edges:s?.querySelectorAll('g.chronology-edge').length||0,body:document.body.innerText.slice(0,200)};`);
    throw new Error(`${error.message}: ${JSON.stringify(state)}`);
  }
}

function pointForWork(cdp, workId, panel = "chronology") {
  return evaluate(cdp, `
    const svg=document.querySelector(${JSON.stringify(`#${panel} .svg-wrap svg`)});
    const node=[...(svg?.querySelectorAll('g.node')||[])].find(g=>(g.querySelector(':scope > title')?.textContent||'').trim()===${JSON.stringify(workId)});
    if(!node)return null; node.scrollIntoView({block:'center',inline:'center'}); const r=node.getBoundingClientRect();
    if(r.width<=0||r.height<=0)return null;
    return {x:r.left+r.width/2,y:r.top+r.height/2};
  `);
}

function pointForSelector(cdp, selector) {
  return evaluate(cdp, `
    const el=document.querySelector(${JSON.stringify(selector)}); if(!el)return null;
    el.scrollIntoView({block:'center',inline:'center'});
    const r=el.getBoundingClientRect(); if(r.width<=0||r.height<=0)return null;
    return {x:r.left+r.width/2,y:r.top+r.height/2};
  `);
}

async function clickWork(cdp, workId, timeoutMs, button = "left", panel = "chronology") {
  const point = await poll(() => pointForWork(cdp, workId, panel), timeoutMs, `${panel} work ${workId}`);
  await clickPoint(cdp, point, button);
}

async function clickSelector(cdp, selector, timeoutMs) {
  const point = await poll(() => pointForSelector(cdp, selector), timeoutMs, `selector ${selector}`);
  await clickPoint(cdp, point);
}

async function clearSelection(cdp, timeoutMs) {
  const mobile = await evaluate(cdp, "return matchMedia('(max-width:760px)').matches");
  if (mobile) {
    const controlsOpen = await evaluate(cdp, "return document.querySelector('#mobileControlsButton')?.getAttribute('aria-expanded') === 'true'");
    if (!controlsOpen) await clickSelector(cdp, "#mobileControlsButton", timeoutMs);
    await poll(() => evaluate(cdp, "return document.querySelector('#flowchartControls')?.classList.contains('controls-open') || document.querySelector('#mobileControlsButton')?.getAttribute('aria-expanded') === 'true'"), timeoutMs, "mobile controls readiness");
    const clearVisible = await evaluate(cdp, "const r=document.querySelector('#clear')?.getBoundingClientRect(); return !!r && r.width>0 && r.height>0");
    if (!clearVisible) {
      const clearCovered = await evaluate(cdp, "const b=document.querySelector('#mobileClearGoals'),r=b?.getBoundingClientRect(); return !!r && !!document.elementFromPoint(r.left+r.width/2,r.top+r.height/2) && !document.elementFromPoint(r.left+r.width/2,r.top+r.height/2)?.closest('#mobileClearGoals')");
      if (clearCovered) await clickSelector(cdp, "#mobileControlsButton", timeoutMs);
      await poll(() => pointForSelector(cdp, "#mobileClearGoals"), timeoutMs, "mobile goal clear control");
      await clickSelector(cdp, "#mobileClearGoals", timeoutMs);
      try { await poll(() => evaluate(cdp, "return (window.marvelSelectionAudit?.().selected || []).length===0"), timeoutMs, "mobile goal clear"); }
      catch (error) {
        const state=await evaluate(cdp,"const b=document.querySelector('#mobileClearGoals'),r=b?.getBoundingClientRect(); return {selected:window.marvelSelectionAudit?.().selected||null,rect:r?{x:r.x,y:r.y,w:r.width,h:r.height}:null,top:r?document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)?.id:null}");
        throw new Error(`${error.message}: ${JSON.stringify(state)}`);
      }
      return;
    }
  }
  await clickSelector(cdp, "#clear", timeoutMs);
  await poll(() => evaluate(cdp, "const audit=window.marvelSelectionAudit?.(); return audit ? audit.selected.length===0 : !document.querySelector('#chronology .svg-wrap svg')?.classList.contains('dim')"), timeoutMs, "clear selection");
}

function chronologySnapshot(cdp) {
  return evaluate(cdp, `
    const chronologySvg=document.querySelector('#chronology .svg-wrap svg');
    const svg=document.querySelector('.panel.active .svg-wrap svg');
    const title=g=>(g.querySelector(':scope > title')?.textContent||'').trim();
    const groups=[...(chronologySvg?.querySelectorAll('g.chronology-edge')||[])];
    const classes=g=>[...g.classList].filter(x=>['hl','backhl','forwardhl','bothhl','pathhl','contexthl'].includes(x)).sort();
    const records=groups.map(g=>({id:g.dataset.chronologyEdgeId||'',source:g.dataset.chronologySource||'',target:g.dataset.chronologyTarget||'',kind:g.dataset.chronologyKind||'',displayOnly:g.dataset.chronologyDisplayOnly==='true',traversable:g.dataset.chronologyTraversable!=='false',classes:classes(g)}));
    const ids=records.map(x=>x.id), seen=new Set(), duplicateIds=[];
    for(const id of ids){if(seen.has(id)&&!duplicateIds.includes(id))duplicateIds.push(id);seen.add(id)}
    return {records,ids,duplicateIds,displayOnlyHighlighted:records.filter(x=>x.displayOnly&&x.classes.includes('hl')).map(x=>x.id),
      highlighted:records.filter(x=>x.classes.includes('hl')).map(x=>x.id),focus:[...((svg&&svg.querySelectorAll('g.node.focus,g.node.current-goal'))||[])].map(title),
      dim:!!svg?.classList.contains('dim'),panel:document.querySelector('.panel.active')?.id||null};
  `);
}

async function waitChronologyState(cdp, predicate, timeoutMs, label) {
  return poll(async () => predicate(await chronologySnapshot(cdp)), timeoutMs, label);
}

function validateModeOracle(snapshot, mode) {
  const expected = MODE_ORACLE[mode] || {};
  const byId = new Map(snapshot.records.map(record => [record.id, record.classes.filter(x => x !== "hl")]));
  const failures = [];
  for (const [name, category] of Object.entries(expected)) {
    const id = ORACLE_EDGE_IDS[name];
    if (!byId.has(id) || !byId.get(id).includes(category)) failures.push(`${mode}: expected ${id}=${category}`);
  }
  // Independent directed reachability oracle for the single-goal public cases;
  // OR/AND/PATH additionally require the explicit fixture IDs above.
  const allowed = new Set();
  const starts = mode === "or" || mode === "and" || mode === "path" ? [PRIMARY_WORK, SECONDARY_WORK] : [PRIMARY_WORK];
  const incoming = new Map(), outgoing = new Map();
  for (const record of snapshot.records) if (record.traversable) {
    if (!outgoing.has(record.source)) outgoing.set(record.source, []); outgoing.get(record.source).push(record);
    if (!incoming.has(record.target)) incoming.set(record.target, []); incoming.get(record.target).push(record);
  }
  for (const start of starts) for (const adjacency of [incoming, outgoing]) {
    const seen = new Set([start]), queue = [start];
    while (queue.length) for (const edge of (adjacency.get(queue.shift()) || [])) { allowed.add(edge.id); const next = adjacency === incoming ? edge.source : edge.target; if (!seen.has(next)) { seen.add(next); queue.push(next); } }
  }
  if (mode === "path") { allowed.clear(); allowed.add(ORACLE_EDGE_IDS.iron_to_iron2); }
  const actual = new Set(snapshot.highlighted);
  for (const id of actual) if (!allowed.has(id)) failures.push(`${mode}: unexpected highlighted ${id}`);
  for (const id of actual) {
    const names = Object.entries(ORACLE_EDGE_IDS).filter(([, value]) => value === id).map(([name]) => name);
    const wanted = names.map(name => expected[name]).filter(Boolean);
    if (wanted.length && !wanted.some(category => byId.get(id)?.includes(category))) failures.push(`${mode}: category mismatch ${id}`);
  }
  if (snapshot.displayOnlyHighlighted.length) failures.push(`${mode}: display-only highlighted`);
  if (failures.length) throw new Error(failures.join("; "));
}

async function setTier(cdp, tier, timeoutMs) {
  await evaluate(cdp, `
    const select=document.querySelector('#chartConnectionTier');
    if(!select)throw new Error('public tier control missing'); select.value=${JSON.stringify(tier)};
    select.dispatchEvent(new Event('change',{bubbles:true})); return true;
  `);
  await poll(() => evaluate(cdp, `return document.querySelector('#chartConnectionTier')?.value===${JSON.stringify(tier)}`), timeoutMs, `tier ${tier}`);
}

async function setCombine(cdp, mode, timeoutMs) {
  const advancedOpen=await evaluate(cdp, "return !!document.querySelector('.advanced-controls')?.open");
  if(!advancedOpen) await clickSelector(cdp, '.advanced-controls > summary', timeoutMs);
  await clickSelector(cdp, `.combine-btn[data-combine="${mode}"]`, timeoutMs);
  await poll(() => evaluate(cdp, `return !!document.querySelector('.combine-btn[data-combine="${mode}"]')?.classList.contains('active')`), timeoutMs, `combine ${mode}`);
}

async function activateChronologyOnCurrentViewport(cdp, timeoutMs) {
  const mobile=await evaluate(cdp, "return matchMedia('(max-width:760px)').matches");
  if(mobile){
    const open=await evaluate(cdp, "return !!document.querySelector('#mobileAreaSheet')&&!document.querySelector('#mobileAreaSheet').hidden");
    if(!open)await clickSelector(cdp,"#mobileAreaButton",timeoutMs);
    await clickSelector(cdp,'.mobile-area-sheet [data-mobile-target="chronology"]',timeoutMs);
  }else await clickSelector(cdp,'.tab[data-target="chronology"]',timeoutMs);
  await poll(()=>evaluate(cdp,"return document.querySelector('.panel.active')?.id==='chronology'"),timeoutMs,"chronology panel activation");
}

async function canvasChronologySnapshot(cdp) {
  return evaluate(cdp, `
    const svg=document.querySelector('#chronology .svg-wrap svg');
    const svgRecords=[...(svg?.querySelectorAll('g.chronology-edge')||[])].map(g=>({id:g.dataset.chronologyEdgeId||'',classes:[...g.classList].filter(x=>['hl','backhl','forwardhl','bothhl','pathhl','contexthl'].includes(x)).sort()}));
    let records=[];
    try {
      const wrap=document.querySelector('#chronology .svg-wrap'), cs=mobileCanvasStates.get(wrap);
      const classified=cs?.overlayWorldChronologyClasses||new Map();
      for(const [key,primitives] of (cs?.overlayChronologyEdgePrimitives||new Map())){
        const p=primitives?.[0]; if(p?.overlayChronologyEdgeId){
          const category=classified.get(p.overlayChronologyEdgeId);
          records.push({id:p.overlayChronologyEdgeId,classes:category?[category]:[]});
        }
      }
    } catch (_) { records=[]; }
    return {records,svgRecords,canvasAvailable:records.length>0};
  `);
}

async function inspectParity(cdp, timeoutMs) {
  const initial = await chronologySnapshot(cdp);
  const canvas = await canvasChronologySnapshot(cdp);
  if (!canvas.canvasAvailable) {
    return {svg_ids: initial.ids, canvas_ids: [], canvas_available: false,
      failures: ["Canvas chronology materialization unavailable"]};
  }
  const source = canvas.records;
  // `hl` is the shared visibility marker; category parity concerns only the
  // directional/path category represented by the SVG and Canvas renderers.
  const category = (classes) => classes.filter((item) => item !== "hl").join("|");
  const svgById = new Map(initial.records.map(x => [x.id, category(x.classes)]));
  const canvasById = new Map(source.map(x => [x.id, category(x.classes)]));
  const failures=[];
  for(const id of initial.ids){if(!canvasById.has(id))failures.push(`missing canvas edge-id: ${id}`); else if(svgById.get(id)!==canvasById.get(id))failures.push(`category mismatch: ${id} (svg=${svgById.get(id)||"none"}, canvas=${canvasById.get(id)||"none"})`);}
  for(const id of canvasById.keys())if(!svgById.has(id))failures.push(`extra canvas edge-id: ${id}`);
  // A real mobile canvas may be initialized lazily; the semantic SVG remains the
  // conservative fallback, but both paths still compare the same stable IDs.
  return {svg_ids:initial.ids,canvas_ids:[...canvasById.keys()],canvas_available:canvas.canvasAvailable,failures};
}

async function runCase(cdp, url, timeoutMs, name, action) {
  try { await loadPage(cdp, url, timeoutMs); const details=await action(); return {name,ok:true,...(details||{})}; }
  catch (error) { return {name,ok:false,error:String(error?.message||error),state:await chronologySnapshot(cdp).catch(() => null)}; }
}

async function runAudit(args) {
  const root=path.resolve(args.root||"."), timeoutMs=Number(args.timeout_ms||DEFAULT_TIMEOUT_MS);
  if(!Number.isInteger(timeoutMs)||timeoutMs<1000)throw new Error("--timeout-ms must be an integer >= 1000");
  const chrome=locateChrome(args.chrome), server=await startStaticServer(root);
  let chromeProcess=null, cdp=null; const cases=[]; let structural=null, parity=null, roundTrip={overview_to_chronology:false,chronology_to_overview:false};
  try {
    chromeProcess=await launchChrome(chrome,timeoutMs); cdp=new CdpClient(chromeProcess.webSocketDebuggerUrl); await cdp.connect();
    await cdp.send("Page.enable"); await cdp.send("Runtime.enable");
    await loadPage(cdp,server.url,timeoutMs);
    structural=await chronologySnapshot(cdp);
    const structuralFailures=[];
    if(structural.ids.length!==CHRONOLOGY_EDGE_COUNT)structuralFailures.push(`expected ${CHRONOLOGY_EDGE_COUNT} chronology edges, got ${structural.ids.length}`);
    if(structural.duplicateIds.length)structuralFailures.push(`duplicate edge-id: ${structural.duplicateIds.join(',')}`);
    if(structural.displayOnlyHighlighted.length)structuralFailures.push(`display-only highlighted: ${structural.displayOnlyHighlighted.join(',')}`);
    structural={edge_count:structural.ids.length,edge_ids:structural.ids,duplicate_ids:structural.duplicateIds,display_only_highlighted:structural.displayOnlyHighlighted,non_traversable:structural.records.filter(x=>!x.traversable).map(x=>x.id),failures:structuralFailures};

    cases.push(await runCase(cdp,server.url,timeoutMs,"complete",async()=>{
      await clearSelection(cdp,timeoutMs); await setTier(cdp,"complete",timeoutMs); await clickWork(cdp,PRIMARY_WORK,timeoutMs);
      await waitChronologyState(cdp,s=>s.dim&&s.focus.length>0&&s.highlighted.length>0,timeoutMs,"complete chronology selection");
      validateModeOracle(await chronologySnapshot(cdp), "complete");
    }));
    cases.push(await runCase(cdp,server.url,timeoutMs,"site-proposal",async()=>{
      await clearSelection(cdp,timeoutMs); await setTier(cdp,"site-proposal",timeoutMs); await clickWork(cdp,PRIMARY_WORK,timeoutMs);
      await waitChronologyState(cdp,s=>s.dim&&s.focus.length>0&&s.highlighted.length>0,timeoutMs,"site-proposal chronology selection");
      validateModeOracle(await chronologySnapshot(cdp), "site-proposal");
    }));
    cases.push(await runCase(cdp,server.url,timeoutMs,"previous1",async()=>{
      const available=await evaluate(cdp,"return !!document.querySelector('.scope-btn[data-scope=\"previous1\"]')");
      if(!available)return {ok:null,available:false,skipped:true,coverage:"internal-unit-only",reason:"previous1 is not a public mode in this export; no internal scope state was invoked"};
      await clearSelection(cdp,timeoutMs); await clickSelector(cdp,'.scope-btn[data-scope="previous1"]',timeoutMs); await clickWork(cdp,PRIMARY_WORK,timeoutMs);
      await waitChronologyState(cdp,s=>s.dim&&s.focus.length>0,timeoutMs,"previous1 public selection");
      return {available:true};
    }));
    for(const mode of ["or","and","path"]){
      cases.push(await runCase(cdp,server.url,timeoutMs,mode,async()=>{
        await clearSelection(cdp,timeoutMs); await setTier(cdp,"complete",timeoutMs); await setCombine(cdp,mode,timeoutMs);
        await clickWork(cdp,PRIMARY_WORK,timeoutMs,"right"); await clickWork(cdp,SECONDARY_WORK,timeoutMs,"right");
        await waitChronologyState(cdp,s=>s.dim&&s.highlighted.length>0,timeoutMs,`${mode} chronology selection`);
        const state=await chronologySnapshot(cdp); if(state.displayOnlyHighlighted.length)throw new Error(`${mode} highlighted display-only edge`);
        validateModeOracle(state, mode);
      }));
    }
    await clearSelection(cdp,timeoutMs); await setCombine(cdp,"or",timeoutMs); await setTier(cdp,"complete",timeoutMs);
    await clickSelector(cdp,'.tab[data-target="overview"]',timeoutMs); await clickWork(cdp,PRIMARY_WORK,timeoutMs,"left","overview");
    await waitChronologyState(cdp,s=>s.panel==="overview"&&s.focus.length>0,timeoutMs,"overview selection");
    await clickSelector(cdp,'.tab[data-target="chronology"]',timeoutMs);
    await waitChronologyState(cdp,s=>s.panel==="chronology"&&s.focus.length>0&&s.highlighted.length>0,timeoutMs,"overview to chronology repaint");
    roundTrip.overview_to_chronology=true;
    await clickSelector(cdp,'.tab[data-target="overview"]',timeoutMs);
    await waitChronologyState(cdp,s=>s.panel==="overview"&&s.focus.length>0,timeoutMs,"chronology to overview repaint");
    roundTrip.chronology_to_overview=true;
    // Exercise the mobile Canvas path as well.  This is a viewport change only;
    // the tab itself is still activated through the public mobile navigation.
    await clickSelector(cdp,'.tab[data-target="chronology"]',timeoutMs);
    await clickWork(cdp,PRIMARY_WORK,timeoutMs,"right","chronology");
    await waitChronologyState(cdp,s=>s.dim&&s.focus.length>0,timeoutMs,"desktop chronology goal before Canvas parity");
    await poll(()=>evaluate(cdp,`return !!window.marvelSelectionAudit?.().selected?.includes(${JSON.stringify(PRIMARY_WORK)})`),timeoutMs,"desktop chronology public goal selection");
    await cdp.send("Emulation.setDeviceMetricsOverride", {width:390,height:844,deviceScaleFactor:1,mobile:true});
    await activateChronologyOnCurrentViewport(cdp,timeoutMs);
    await poll(()=>evaluate(cdp,"return !!document.querySelector('#chronology canvas[data-marvel-mobile-canvas]')"),timeoutMs,"mobile chronology canvas readiness");
    // Add an unselected goal through the mobile Canvas hit target so its world
    // cache records a fresh public selection without re-click deselection.
    await clickWork(cdp,MOBILE_WORK,timeoutMs,"left","chronology");
    await poll(()=>evaluate(cdp,`return !!window.marvelSelectionAudit?.().selected?.includes(${JSON.stringify(MOBILE_WORK)})`),timeoutMs,"mobile chronology public goal selection");
    await poll(()=>evaluate(cdp,"const cs=mobileCanvasStates.get(document.querySelector('#chronology .svg-wrap')); return !!cs?.overlayWorldChronologyClasses"),timeoutMs,"mobile chronology category readiness");
    parity=await inspectParity(cdp,timeoutMs);
  } finally {
    cdp?.close(); await new Promise((resolve)=>server.server.close(()=>resolve())); if(chromeProcess)await stopChrome(chromeProcess);
  }
  const failures=[...(structural?.failures||[]),...(parity?.failures||[]),...cases.filter(x=>x.ok===false).map(x=>`${x.name}: ${x.error}`)];
  const coverage_gaps=cases.filter(x=>x.skipped).map(x=>({name:x.name,available:x.available===true,coverage:x.coverage||"environment",reason:x.reason||"not exercised"}));
  if(!roundTrip.overview_to_chronology)failures.push("overview_to_chronology round trip failed");
  if(!roundTrip.chronology_to_overview)failures.push("chronology_to_overview round trip failed");
  return {summary:{cases:cases.length,failures:failures.length,coverage_gaps:coverage_gaps.length},coverage_gaps,structural,modes:cases,svg_canvas_parity:parity||{failures:["parity not collected"]},round_trip:roundTrip,failures};
}

async function main(){
  const args=parseArgs(process.argv.slice(2)); if(args.help){process.stdout.write(`${usage()}\n`);return;}
  const report=await runAudit(args); process.stdout.write(`${JSON.stringify(report)}\n`); if(report.failures.length)process.exitCode=1;
}
main().catch((error)=>{process.stderr.write(`${error.stack||error}\n`);process.exitCode=1;});
