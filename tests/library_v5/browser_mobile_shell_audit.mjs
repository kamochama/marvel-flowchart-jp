#!/usr/bin/env node

import fs from "node:fs";
import http from "node:http";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import { execFileSync, spawn } from "node:child_process";

const DEFAULT_TIMEOUT_MS = 20_000;
const PROFILE_CLEANUP_RETRIES = 100;

function usage() {
  return [
    "Usage: node browser_mobile_shell_audit.mjs --root <repo> [--chrome <path>]",
    "",
    "Runs real pointer/focus scenarios against the M3 mobile chart surface.",
    "The final line is JSON: {viewport,selection,sheet,rerenders,failures}.",
    "",
    "Options:",
    "  --root <path>      Repository root to serve over HTTP",
    "  --chrome <path>    Chrome/Chromium executable (otherwise auto-detected)",
    "  --timeout-ms <n>   Per-poll timeout (default 20000)",
    "  --help             Show this help",
  ].join("\n");
}

function parseArgs(argv) {
  const args = {};
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--help") { args.help = true; continue; }
    if (!token.startsWith("--")) throw new Error(`unexpected argument: ${token}`);
    const key = token.slice(2).replaceAll("-", "_");
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) throw new Error(`missing value for --${key}`);
    args[key] = value;
    index += 1;
  }
  return args;
}

function locateChrome(configured) {
  const commandNames = ["google-chrome", "chromium", "chromium-browser", "chrome"];
  const commands = commandNames.flatMap((name) => {
    try {
      const command = process.platform === "win32" ? "where.exe" : "which";
      const resolved = execFileSync(command, [name], { encoding: "utf8" }).split(/\r?\n/)[0].trim();
      return resolved ? [resolved] : [];
    } catch (_) { return []; }
  });
  const candidates = [
    configured,
    process.env.MARVEL_CHROME_BIN,
    process.env.CHROME_BIN,
    ...commands,
    "C:/Program Files/Google/Chrome/Application/chrome.exe",
    "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    `${process.env.LOCALAPPDATA || ""}/Google/Chrome/Application/chrome.exe`,
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
  ].filter(Boolean);
  for (const candidate of candidates) {
    if (path.isAbsolute(candidate) && fs.existsSync(candidate)) return candidate;
    if (!path.isAbsolute(candidate) && fs.existsSync(candidate)) return candidate;
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
      server.close((error) => error ? reject(error) : resolve(port));
    });
  });
}

function contentType(filePath) {
  return {
    ".html": "text/html; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".png": "image/png",
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
  const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), "marvel-mobile-shell-cdp-"));
  const child = spawn(chromePath, [
    "--headless=new", "--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox",
    "--no-first-run", "--no-default-browser-check", "--window-size=390,844",
    `--remote-debugging-port=${port}`, `--user-data-dir=${userDataDir}`, "about:blank",
  ], { stdio: ["ignore", "ignore", "pipe"] });
  let launchError = null;
  child.once("error", (error) => { launchError = error; });
  try {
    const target = await poll(async () => {
      if (launchError) throw launchError;
      const response = await fetch(`http://127.0.0.1:${port}/json/list`);
      if (!response.ok) return null;
      return (await response.json()).find((entry) => entry.type === "page" && entry.webSocketDebuggerUrl) || null;
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
  fs.rmSync(processInfo.userDataDir, { recursive: true, force: true, maxRetries: PROFILE_CLEANUP_RETRIES, retryDelay: 100 });
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
      const pending = this.pending.get(message.id);
      if (!pending) return;
      this.pending.delete(message.id);
      if (message.error) pending.reject(new Error(message.error.message || "CDP command failed"));
      else pending.resolve(message.result || {});
    });
    this.socket.addEventListener("close", () => {
      for (const pending of this.pending.values()) pending.reject(new Error("CDP socket closed"));
      this.pending.clear();
    });
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

async function pageEvaluate(cdp, body) { return cdp.evaluate(`(() => { ${body} })()`); }
async function clickPoint(cdp, point) {
  await cdp.send("Input.dispatchMouseEvent", { type: "mouseMoved", x: point.x, y: point.y });
  await cdp.send("Input.dispatchMouseEvent", { type: "mousePressed", x: point.x, y: point.y, button: "left", clickCount: 1 });
  await cdp.send("Input.dispatchMouseEvent", { type: "mouseReleased", x: point.x, y: point.y, button: "left", clickCount: 1 });
}
async function pressTab(cdp) {
  const params = { key: "Tab", code: "Tab", windowsVirtualKeyCode: 9, nativeVirtualKeyCode: 9 };
  await cdp.send("Input.dispatchKeyEvent", { type: "keyDown", ...params });
  await cdp.send("Input.dispatchKeyEvent", { type: "keyUp", ...params });
}
async function focusedElementId(cdp) {
  return pageEvaluate(cdp, "return document.activeElement?.id || null;");
}
async function controlFocusSequence(cdp) {
  const expected = ["mobileChartFit", "mobileChartSelected", "mobileChartDetails", "mobileChartViewButton"];
  await clickPoint(cdp, await pointForSelector(cdp, "#mobileChartFit"));
  const focused = [];
  for (let index = 0; index < expected.length; index += 1) {
    focused.push(await focusedElementId(cdp));
    if (index < expected.length - 1) await pressTab(cdp);
  }
  return { expected, focused };
}
async function drag(cdp, start, end) {
  await cdp.send("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: [{ x: start.x, y: start.y, id: 1 }] });
  for (let step = 1; step <= 6; step += 1) {
    const ratio = step / 6;
    await cdp.send("Input.dispatchTouchEvent", { type: "touchMove", touchPoints: [{ x: start.x + (end.x - start.x) * ratio, y: start.y + (end.y - start.y) * ratio, id: 1 }] });
  }
  await cdp.send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
}
async function pointForSelector(cdp, selector) {
  return pageEvaluate(cdp, `const el=document.querySelector(${JSON.stringify(selector)}); if(!el)return null; const r=el.getBoundingClientRect(); return {x:r.left+r.width/2,y:r.top+r.height/2,width:r.width,height:r.height};`);
}
async function visibleNodePoint(cdp) {
  return pageEvaluate(cdp, `
    const wrap=document.querySelector('#mobileViewHost .mobile-chart-surface .svg-wrap');
    if(!wrap)return null;
    const wr=wrap.getBoundingClientRect();
    for(const node of wrap.querySelectorAll('svg g.node')){
      const r=node.getBoundingClientRect(),x=r.left+r.width/2,y=r.top+r.height/2;
      if(r.width>1&&r.height>1&&x>wr.left+5&&x<wr.right-5&&y>wr.top+5&&y<wr.bottom-5)return {x,y,workId:(node.querySelector(':scope > title')?.textContent||'').trim()};
    }
    return null;
  `);
}
async function blankPoint(cdp) {
  return pageEvaluate(cdp, `
    const wrap=document.querySelector('#mobileViewHost .mobile-chart-surface .svg-wrap');
    if(!wrap)return null;
    const wr=wrap.getBoundingClientRect();
    const nodes=[...wrap.querySelectorAll('svg g.node')].map(node=>node.getBoundingClientRect());
    for(let y=wr.top+12;y<wr.bottom-12;y+=14)for(let x=wr.left+12;x<wr.right-12;x+=14){
      if(nodes.some(r=>x>=r.left-8&&x<=r.right+8&&y>=r.top-8&&y<=r.bottom+8))continue;
      const target=document.elementFromPoint(x,y);
      if(target?.closest?.('.mobile-chart-surface .svg-wrap')===wrap)return {x,y};
    }
    return null;
  `);
}
async function snapshot(cdp) {
  return pageEvaluate(cdp, `
    const store=window.marvelMobileUiStore?.getState?.()||{};
    const selection=window.marvelSelectionAudit?.()||{};
    const surface=document.querySelector('#mobileViewHost [data-mobile-surface="chart"]');
    const legacyPanel=document.querySelector('#left>.panel.active');
    const nav=[...document.querySelectorAll('#mobileBottomNav button')];
    return {
      view:store.view||null,
      chartVisible:!!surface,
      panelId:surface?.querySelector('.panel')?.id||null,
      activePanelId:document.querySelector('.panel.active')?.id||null,
      legacyPanelVisible:!!legacyPanel&&getComputedStyle(legacyPanel).display!=='none',
      selected:[...(selection.selected||[])],
      camera:surface?.dataset.mobileCamera||null,
      sheetHidden:document.getElementById('mobileSheet')?.hidden!==false,
      bottomReachable:nav.length===3&&nav.every(button=>{const r=button.getBoundingClientRect();return r.width>=44&&r.height>=44&&r.bottom<=innerHeight+1;}),
      controlsReachable:surface?[...surface.querySelectorAll('.mobile-chart-controls button')].every(button=>{const r=button.getBoundingClientRect();return r.width>=44&&r.height>=44&&r.bottom<=innerHeight+1;}):false,
      rerenders:window.__mobileShellAuditCounters||{render:0,fit:0,rebuild:0},
    };
  `);
}
async function waitFor(cdp, predicate, timeoutMs, label) { return poll(async () => { const state = await snapshot(cdp); return predicate(state) ? state : null; }, timeoutMs, label); }
async function instrumentRerenders(cdp) {
  await pageEvaluate(cdp, `
    if(!window.__mobileShellAuditInstalled){
      const counters={render:0,fit:0,rebuild:0};
      for(const [name,key] of [['render','render'],['fitView','fit'],['rebuildMobileCanvas','rebuild']]){
        const fn=window[name]; if(typeof fn!=='function')continue;
        window[name]=function(...args){counters[key]+=1;return fn.apply(this,args)};
      }
      window.__mobileShellAuditCounters=counters;window.__mobileShellAuditInstalled=true;
    }
    return true;
  `);
}

async function runAudit(args) {
  const timeoutMs = Number(args.timeout_ms || DEFAULT_TIMEOUT_MS);
  if (!Number.isInteger(timeoutMs) || timeoutMs < 1_000) throw new Error("--timeout-ms must be an integer >= 1000");
  const chrome = locateChrome(args.chrome);
  const staticServer = await startStaticServer(path.resolve(args.root || "."));
  let chromeProcess = null;
  let cdp = null;
  const failures = [];
  const result = {
    viewport: { width: 390, height: 844 },
    selection: { selected: false, reclickClears: false, blankClears: false, dragPreserves: false },
    sheet: { opened: false, closed: false, cameraPreserved: false },
    rerenders: { before: null, afterOpen: null, afterClose: null },
    views: { chartVisible: false, keyboardFocus: false, displayPanel: { selected: false, panelId: null }, nonChartRemovesChart: false, nonChartHidesLegacyPanel: false, nonChartDocumentPanel: false, displayChooser: { selected: false, panelId: null }, charactersPanel: { selected: false, panelId: null }, responsiveSearchSync: false, chartRestoresCamera: false },
    failures,
  };
  try {
    chromeProcess = await launchChrome(chrome, timeoutMs);
    cdp = new CdpClient(chromeProcess.webSocketDebuggerUrl);
    await cdp.connect();
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");
    await cdp.send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
    await cdp.send("Page.navigate", { url: staticServer.url });
    await poll(() => pageEvaluate(cdp, "return document.readyState === 'complete'"), timeoutMs, "page load");
    await poll(() => pageEvaluate(cdp, `return !!document.querySelector('#mobileViewHost [data-mobile-surface="chart"] .svg-wrap svg g.node') && document.querySelectorAll('#mobileViewHost [data-mobile-surface="chart"] .svg-wrap svg g.node').length===131`), timeoutMs, "mobile chart readiness");
    await instrumentRerenders(cdp);
    const initial = await waitFor(cdp, (state) => state.chartVisible && state.bottomReachable && state.controlsReachable, timeoutMs, "mobile chart controls");
    result.views.chartVisible = initial.chartVisible;
    const focus = await controlFocusSequence(cdp);
    result.views.keyboardFocus = focus.expected.every((id, index) => focus.focused[index] === id);
    if (!result.views.keyboardFocus) failures.push(`keyboard focus sequence did not reach compact controls: ${JSON.stringify(focus)}`);

    const node = await poll(() => visibleNodePoint(cdp), timeoutMs, "visible chart node");
    await clickPoint(cdp, node);
    await waitFor(cdp, (state) => state.selected.includes(node.workId), timeoutMs, "one-tap selection");
    result.selection.selected = true;
    await clickPoint(cdp, node);
    await waitFor(cdp, (state) => state.selected.length === 0, timeoutMs, "same-work retap clear");
    result.selection.reclickClears = true;
    await clickPoint(cdp, node);
    await waitFor(cdp, (state) => state.selected.includes(node.workId), timeoutMs, "selection before blank clear");
    const blank = await poll(() => blankPoint(cdp), timeoutMs, "blank chart point");
    await clickPoint(cdp, blank);
    await waitFor(cdp, (state) => state.selected.length === 0, timeoutMs, "blank clear");
    result.selection.blankClears = true;
    await clickPoint(cdp, node);
    await waitFor(cdp, (state) => state.selected.includes(node.workId), timeoutMs, "selection before drag");
    const beforeDrag = (await snapshot(cdp)).camera;
    const dragStart = await poll(() => blankPoint(cdp), timeoutMs, "drag start");
    await drag(cdp, dragStart, { x: Math.min(380, dragStart.x + 90), y: Math.min(730, dragStart.y + 52) });
    const dragged = await snapshot(cdp);
    if (!dragged.selected.includes(node.workId) || !dragged.camera || dragged.camera === beforeDrag) {
      throw new Error(`drag camera and selection failed: before=${beforeDrag} after=${JSON.stringify(dragged)}`);
    }
    result.selection.dragPreserves = true;

    const beforeSheet = await snapshot(cdp);
    result.rerenders.before = { ...beforeSheet.rerenders };
    await clickPoint(cdp, await pointForSelector(cdp, "#mobileChartDetails"));
    await waitFor(cdp, (state) => !state.sheetHidden, timeoutMs, "sheet open");
    const opened = await snapshot(cdp);
    result.sheet.opened = true;
    result.rerenders.afterOpen = { ...opened.rerenders };
    if (opened.camera !== beforeSheet.camera) failures.push("sheet open changed data-mobile-camera");
    if (opened.rerenders.render !== beforeSheet.rerenders.render || opened.rerenders.fit !== beforeSheet.rerenders.fit || opened.rerenders.rebuild !== beforeSheet.rerenders.rebuild) failures.push("sheet open rebuilt chart");
    await clickPoint(cdp, await pointForSelector(cdp, "#mobileSheetClose"));
    await waitFor(cdp, (state) => state.sheetHidden, timeoutMs, "sheet close");
    const closed = await snapshot(cdp);
    result.sheet.closed = true;
    result.rerenders.afterClose = { ...closed.rerenders };
    result.sheet.cameraPreserved = closed.camera === beforeSheet.camera;
    if (!result.sheet.cameraPreserved) failures.push("sheet close changed data-mobile-camera");
    if (closed.rerenders.render !== beforeSheet.rerenders.render || closed.rerenders.fit !== beforeSheet.rerenders.fit || closed.rerenders.rebuild !== beforeSheet.rerenders.rebuild) failures.push("sheet close rebuilt chart");

    await clickPoint(cdp, await pointForSelector(cdp, '#mobileBottomNav [data-mobile-view="search"]'));
    const firstNonChart = await waitFor(cdp, (state) => state.view === "search" && !state.chartVisible, timeoutMs, "non-chart surface removal");
    result.views.nonChartRemovesChart = true;
    result.views.nonChartHidesLegacyPanel = !firstNonChart.legacyPanelVisible;
    if (!result.views.nonChartHidesLegacyPanel) failures.push(`non-chart view exposed legacy panel: ${JSON.stringify(firstNonChart)}`);
    await clickPoint(cdp, await pointForSelector(cdp, '#mobileBottomNav [data-mobile-view="plan"]'));
    const planNonChart = await waitFor(cdp, (state) => state.view === "plan" && !state.chartVisible, timeoutMs, "plan surface removal");
    result.views.nonChartHidesLegacyPanel = result.views.nonChartHidesLegacyPanel && !planNonChart.legacyPanelVisible;
    if (planNonChart.legacyPanelVisible) failures.push(`plan view exposed legacy panel: ${JSON.stringify(planNonChart)}`);
    await clickPoint(cdp, await pointForSelector(cdp, '#mobileBottomNav [data-mobile-view="chart"]'));
    await waitFor(cdp, (state) => state.view === "chart" && state.chartVisible, timeoutMs, "chart surface restore");
    const restored = await snapshot(cdp);
    result.views.chartRestoresCamera = restored.camera === beforeSheet.camera;
    if (!result.views.chartRestoresCamera) failures.push(`chart remount lost camera: before=${beforeSheet.camera} after=${restored.camera}`);

    await clickPoint(cdp, await pointForSelector(cdp, "#mobileChartViewButton"));
    await poll(() => pageEvaluate(cdp, "return !document.getElementById('mobileAreaSheet')?.hidden;"), timeoutMs, "display view chooser");
    await clickPoint(cdp, await pointForSelector(cdp, '#mobileAreaSheet [data-mobile-target="release"]'));
    const releaseView = await waitFor(cdp, (state) => state.view === "chart" && state.chartVisible && state.panelId === "release" && state.activePanelId === "release", timeoutMs, "release display view mount");
    result.views.displayPanel = { selected: releaseView.panelId === "release" && releaseView.activePanelId === "release", panelId: releaseView.panelId };
    if (!result.views.displayPanel.selected) failures.push(`display view did not mount release panel: ${JSON.stringify(releaseView)}`);

    await clickPoint(cdp, await pointForSelector(cdp, '#mobileBottomNav [data-mobile-view="search"]'));
    await waitFor(cdp, (state) => state.view === "search" && !state.chartVisible, timeoutMs, "release non-chart removal");
    const retainedDocumentApis = await pageEvaluate(cdp, `
      const overviewHasIronMan=window.panelHasWork?.("overview","iron-man-2008")===true;
      const preferred=window.preferredPanelForWork?.("iron-man-2008")||null;
      const chooser=!!document.querySelector('#mobileAreaSheet [data-mobile-target="overview"]');
      return {overviewHasIronMan,preferred,chooser,documentPanels:[...document.querySelectorAll('.panel')].map(panel=>panel.id)};
    `);
    result.views.nonChartDocumentPanel = retainedDocumentApis.overviewHasIronMan && ["overview", "release", "chronology"].includes(retainedDocumentApis.preferred) && retainedDocumentApis.chooser;
    if (!result.views.nonChartDocumentPanel) failures.push(`non-chart document panel APIs failed: ${JSON.stringify(retainedDocumentApis)}`);
    await clickPoint(cdp, await pointForSelector(cdp, "#mobileAreaButton"));
    await poll(() => pageEvaluate(cdp, "return !document.getElementById('mobileAreaSheet')?.hidden;"), timeoutMs, "non-chart display view chooser");
    await clickPoint(cdp, await pointForSelector(cdp, '#mobileAreaSheet [data-mobile-target="overview"]'));
    const chooserOverview = await waitFor(cdp, (state) => state.view === "search" && !state.chartVisible && state.activePanelId === "overview", timeoutMs, "non-chart display chooser overview");
    result.views.displayChooser = { selected: chooserOverview.activePanelId === "overview", panelId: chooserOverview.activePanelId };
    if (!result.views.displayChooser.selected) failures.push(`non-chart display chooser did not select overview: ${JSON.stringify(chooserOverview)}`);
    await clickPoint(cdp, await pointForSelector(cdp, '#mobileBottomNav [data-mobile-view="chart"]'));
    await waitFor(cdp, (state) => state.view === "chart" && state.chartVisible && state.panelId === "overview" && state.activePanelId === "overview", timeoutMs, "overview chart return after chooser");
    await clickPoint(cdp, await pointForSelector(cdp, "#mobileChartViewButton"));
    await poll(() => pageEvaluate(cdp, "return !document.getElementById('mobileAreaSheet')?.hidden;"), timeoutMs, "release chooser after overview return");
    await clickPoint(cdp, await pointForSelector(cdp, '#mobileAreaSheet [data-mobile-target="release"]'));
    await waitFor(cdp, (state) => state.view === "chart" && state.chartVisible && state.panelId === "release" && state.activePanelId === "release", timeoutMs, "release chooser reselect");
    await clickPoint(cdp, await pointForSelector(cdp, '#mobileBottomNav [data-mobile-view="search"]'));
    const releaseNonChart = await waitFor(cdp, (state) => state.view === "search" && !state.chartVisible, timeoutMs, "release chooser non-chart removal");
    if (!releaseNonChart.legacyPanelVisible) result.views.nonChartHidesLegacyPanel = true;
    else failures.push(`release non-chart view exposed legacy panel: ${JSON.stringify(releaseNonChart)}`);
    await clickPoint(cdp, await pointForSelector(cdp, '#mobileBottomNav [data-mobile-view="chart"]'));
    const restoredRelease = await waitFor(cdp, (state) => state.view === "chart" && state.chartVisible && state.panelId === "release" && state.activePanelId === "release", timeoutMs, "release chart return");
    if (restoredRelease.panelId !== "release" || restoredRelease.activePanelId !== "release") failures.push(`release display view was not restored: ${JSON.stringify(restoredRelease)}`);

    await clickPoint(cdp, await pointForSelector(cdp, "#mobileChartViewButton"));
    await poll(() => pageEvaluate(cdp, "return !document.getElementById('mobileAreaSheet')?.hidden;"), timeoutMs, "characters chooser");
    await clickPoint(cdp, await pointForSelector(cdp, '#mobileAreaSheet [data-mobile-target="characters"]'));
    const charactersView = await waitFor(cdp, (state) => state.view === "chart" && state.chartVisible && state.panelId === "characters" && state.activePanelId === "characters", timeoutMs, "characters display view mount");
    result.views.charactersPanel = { selected: charactersView.panelId === "characters" && charactersView.activePanelId === "characters", panelId: charactersView.panelId };
    if (!result.views.charactersPanel.selected) failures.push(`characters display view did not mount: ${JSON.stringify(charactersView)}`);
    await clickPoint(cdp, await pointForSelector(cdp, '#mobileBottomNav [data-mobile-view="search"]'));
    await waitFor(cdp, (state) => state.view === "search" && !state.chartVisible, timeoutMs, "characters non-chart removal");
    await clickPoint(cdp, await pointForSelector(cdp, '#mobileBottomNav [data-mobile-view="chart"]'));
    const restoredCharacters = await waitFor(cdp, (state) => state.view === "chart" && state.chartVisible && state.panelId === "characters" && state.activePanelId === "characters", timeoutMs, "characters chart return");
    if (restoredCharacters.panelId !== "characters" || restoredCharacters.activePanelId !== "characters") failures.push(`characters display view was not restored: ${JSON.stringify(restoredCharacters)}`);

    await clickPoint(cdp, await pointForSelector(cdp, '#mobileBottomNav [data-mobile-view="search"]'));
    await waitFor(cdp, (state) => state.view === "search" && !state.chartVisible, timeoutMs, "responsive search setup");
    await cdp.send("Emulation.setDeviceMetricsOverride", { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });
    await poll(() => pageEvaluate(cdp, "return !window.matchMedia('(max-width:760px)').matches;"), timeoutMs, "desktop viewport switch");
    await cdp.send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
    const responsiveSearch = await waitFor(cdp, (state) => state.view === "search" && !state.chartVisible && !state.legacyPanelVisible, timeoutMs, "responsive mobile search sync");
    result.views.responsiveSearchSync = responsiveSearch.view === "search" && !responsiveSearch.chartVisible && !responsiveSearch.legacyPanelVisible;
    if (!result.views.responsiveSearchSync) failures.push(`responsive mobile search exposed legacy panel: ${JSON.stringify(responsiveSearch)}`);
    await clickPoint(cdp, await pointForSelector(cdp, '#mobileBottomNav [data-mobile-view="chart"]'));
    const responsiveChart = await waitFor(cdp, (state) => state.view === "chart" && state.chartVisible && state.panelId === "characters" && state.activePanelId === "characters", timeoutMs, "responsive characters chart return");
    if (responsiveChart.panelId !== "characters" || responsiveChart.activePanelId !== "characters") failures.push(`responsive chart return lost characters panel: ${JSON.stringify(responsiveChart)}`);
  } catch (error) {
    failures.push(String(error?.message || error));
  } finally {
    cdp?.close();
    await new Promise((resolve) => staticServer.server.close(() => resolve()));
    if (chromeProcess) await stopChrome(chromeProcess);
  }
  return result;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) { process.stdout.write(`${usage()}\n`); return; }
  const report = await runAudit(args);
  process.stdout.write(`${JSON.stringify(report)}\n`);
  if (report.failures.length) process.exitCode = 1;
}

main().catch((error) => { process.stderr.write(`${error.stack || error}\n`); process.exitCode = 1; });
