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
    "Runs real pointer/focus scenarios against the M3/M4/M5 mobile shell surfaces.",
    "The final line is JSON: {viewport,views,selection,history,sheet,rerenders,search,plan,failures}.",
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
  let lastValue = null;
  while (Date.now() < deadline) {
    try { const value = await task(); lastValue = value; if (value) return value; }
    catch (error) { lastError = error; }
    await new Promise((resolve) => setTimeout(resolve, 50));
  }
  const diagnosticValue = lastValue && typeof lastValue === "object" ? lastValue : lastError?.state;
  const state = diagnosticValue && typeof diagnosticValue === "object" ? `: state=${JSON.stringify(diagnosticValue)}` : "";
  throw new Error(`${label} timed out${lastError ? `: ${lastError.message}` : ""}${state}`);
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
  constructor(url) {
    this.url = url;
    this.nextId = 1;
    this.pending = new Map();
    this.commandTimeoutMs = Number(process.env.MARVEL_CDP_COMMAND_TIMEOUT_MS || 30_000);
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
      clearTimeout(pending.timer);
      if (message.error) pending.reject(new Error(message.error.message || "CDP command failed"));
      else pending.resolve(message.result || {});
    });
    this.socket.addEventListener("close", () => {
      for (const pending of this.pending.values()) {
        clearTimeout(pending.timer);
        pending.reject(new Error("CDP socket closed"));
      }
      this.pending.clear();
    });
  }
  send(method, params = {}) {
    const id = this.nextId++;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`CDP command timed out: ${method}`));
      }, this.commandTimeoutMs);
      this.pending.set(id, { resolve, reject, timer });
      this.socket.send(JSON.stringify({ id, method, params }));
    });
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
async function mobileSearchSnapshot(cdp) {
  return pageEvaluate(cdp, `
    const store=window.marvelMobileUiStore?.getState?.()||{};
    const surface=document.querySelector('#mobileViewHost [data-mobile-surface="search"]');
    const input=surface?.querySelector('[data-mobile-search-query]');
    const cards=[...(surface?.querySelectorAll('[data-mobile-search-work]')||[])];
    const empty=surface?.querySelector('[data-mobile-search-empty]');
    const audit=window.marvelSelectionAudit?.()||{};
    const actions=cards.flatMap(card=>[...card.querySelectorAll('.mobile-search-result-action')]);
    return {
      view:store.view||null,query:store.query||input?.value||'',filter:store.filter||'',
      url:location.href,historyLength:history.length,
      historyLog:window.__mobileHistoryLog||[],
      storeViewLog:window.__mobileStoreViewLog||[],
      searchSurface:!!surface,inputValue:input?.value||'',resultCount:cards.length,
      firstId:cards[0]?.dataset.mobileSearchWork||null,selected:[...(audit.selected||[])],back:[...(audit.back||[])],
      emptyText:empty?.textContent||'',emptyVisible:!!empty&&!empty.hidden,
      firstCardInViewport:!!cards[0]&&(()=>{const r=cards[0].getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight;})(),
      actionsReachable:actions.length>0&&actions.every(button=>{const r=button.getBoundingClientRect();return r.width>=44&&r.height>=44;}),
    };
  `);
}
async function waitForSearch(cdp, predicate, timeoutMs, label) {
  return poll(async () => { const state=await mobileSearchSnapshot(cdp); if(predicate(state))return state; const error=new Error("condition not met");error.state=state;throw error; }, timeoutMs, label);
}
async function mobilePlanSnapshot(cdp) {
  return pageEvaluate(cdp, `
    const store=window.marvelMobileUiStore?.getState?.()||{};
    const surface=document.querySelector('#mobileViewHost [data-mobile-surface="plan"]');
    const items=[...(surface?.querySelectorAll('[data-mobile-plan-item]')||[])];
    const tier=surface?.querySelector('[data-mobile-plan-tier]');
    const progress=surface?.querySelector('[data-mobile-plan-progress]');
    const watched=[...(window.marvelWatchProgress?.watched||[])];
    const selection=window.marvelSelectionAudit?.()||{};
    return {
      view:store.view||null,planSurface:!!surface,goalIds:[...(store.goalIds||[])],selectedId:store.selectedId||null,
      summaryText:surface?.querySelector('[data-mobile-plan-summary]')?.textContent||'',
      tierOptions:tier?[...tier.options].map(option=>option.value):[],tierValue:tier?.value||null,
      officialControl:!!surface&&[...surface.querySelectorAll('select,button,[role="option"]')].some(el=>/公式予習ルート/.test(el.textContent||'')),
      ordered:items.map(item=>item.dataset.mobilePlanWork||null),watched,
      watchedIds:items.filter(item=>item.querySelector('[data-mobile-plan-watched]')?.checked).map(item=>item.dataset.mobilePlanWork||null),
      resultCount:items.length,progressText:progress?.textContent||'',progressValue:progress?.querySelector('[role="progressbar"]')?.getAttribute('aria-valuenow')||null,
      remainingVisible:/残り時間/.test(progress?.textContent||''),detailReachable:items.length>0&&items.every(item=>{const button=item.querySelector('[data-mobile-plan-detail]');const r=button?.getBoundingClientRect();return !!r&&r.width>=44&&r.height>=44;}),
      goalRemoveCount:surface?.querySelectorAll('[data-mobile-plan-remove-goal]').length||0,
      layout:surface?(()=>{const r=surface.getBoundingClientRect();return {left:r.left,right:r.right,width:r.width,viewportWidth:innerWidth,scrollY:scrollY};})():null,
      chartAction:!!surface?.querySelector('[data-mobile-plan-chart]'),selected:[...(selection.selected||[])],
      rerenders:window.__mobileShellAuditCounters||{render:0,fit:0,rebuild:0},
    };
  `);
}
async function mobilePlanLayoutSnapshot(cdp) {
  return pageEvaluate(cdp, `
    const surface=document.querySelector('#mobileViewHost [data-mobile-surface="plan"]');
    const focus=document.getElementById('mobileFocusShell'),watch=document.getElementById('watchWorkspace');
    const r=surface?.getBoundingClientRect();
    return {left:r?.left??null,right:r?.right??null,width:r?.width??null,viewportWidth:innerWidth,focusVisible:!!focus&&getComputedStyle(focus).display!=='none',watchVisible:!!watch&&getComputedStyle(watch).display!=='none',scrollY};
  `);
}
async function waitForPlan(cdp, predicate, timeoutMs, label) {
  return poll(async () => { const state=await mobilePlanSnapshot(cdp); if(predicate(state))return state; const error=new Error("condition not met");error.state=state;throw error; }, timeoutMs, label);
}
async function selectAllAndBackspace(cdp) {
  const params={key:"a",code:"KeyA",windowsVirtualKeyCode:65,nativeVirtualKeyCode:65,modifiers:2};
  await cdp.send("Input.dispatchKeyEvent", { type:"keyDown", ...params });
  await cdp.send("Input.dispatchKeyEvent", { type:"keyUp", ...params });
  const backspace={key:"Backspace",code:"Backspace",windowsVirtualKeyCode:8,nativeVirtualKeyCode:8};
  await cdp.send("Input.dispatchKeyEvent", { type:"keyDown", ...backspace });
  await cdp.send("Input.dispatchKeyEvent", { type:"keyUp", ...backspace });
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
      back:[...(selection.back||[])],
      camera:surface?.dataset.mobileCamera||null,
      sheetHidden:document.getElementById('mobileSheet')?.hidden!==false,
      sheetWork:store.sheetWork||null,
      sheetBodyText:document.getElementById('mobileSheetBody')?.textContent?.trim()||'',
      planVisible:!!document.querySelector('#mobileViewHost [data-mobile-surface="plan"]'),
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
    if(!window.__mobileHistoryInstalled){
      const log=[];
      for(const name of ["pushState","replaceState"]){
        const original=history[name];
        history[name]=function(...args){log.push({name,url:String(args[2]||location.href),view:window.marvelMobileUiStore?.getState?.().view||null});return original.apply(this,args);};
      }
      window.__mobileHistoryLog=log;window.__mobileHistoryInstalled=true;
    }
    if(!window.__mobileStoreViewInstalled){
      const store=window.marvelMobileUiStore;
      const original=store?.setView;
      if(store&&typeof original==='function')store.setView=function(view){window.__mobileStoreViewLog=window.__mobileStoreViewLog||[];window.__mobileStoreViewLog.push({requested:view,before:store.getState().view});return original.call(store,view);};
      window.__mobileStoreViewInstalled=true;
    }
    return true;
  `);
}

async function runAudit(args) {
  const timeoutMs = Number(args.timeout_ms || DEFAULT_TIMEOUT_MS);
  if (!Number.isInteger(timeoutMs) || timeoutMs < 1_000) throw new Error("--timeout-ms must be an integer >= 1000");
  const chrome = locateChrome(args.chrome);
  const trace = (label) => console.error(`MOBILE_AUDIT_TRACE ${label}`);
  const staticServer = await startStaticServer(path.resolve(args.root || "."));
  let chromeProcess = null;
  let cdp = null;
  const failures = [];
  const result = {
    viewport: { width: 390, height: 844 },
    views: { chartVisible: false, keyboardFocus: false, displayPanel: { selected: false, panelId: null }, nonChartRemovesChart: false, nonChartHidesLegacyPanel: false, nonChartDocumentPanel: false, displayChooser: { selected: false, panelId: null }, charactersPanel: { selected: false, panelId: null }, responsiveSearchSync: false, chartRestoresCamera: false, legacyPrepJump: false },
    selection: { selected: false, reclickClears: false, blankClears: false, dragPreserves: false },
    history: { queryOnViewSwitch: false, queryOnPopstate: false, planClick: null, urlAfterBack: null },
    sheet: { opened: false, closed: false, cameraPreserved: false },
    rerenders: { before: null, afterOpen: null, afterClose: null },
    search: { queried: false, resultCount: 0, selected: false, chartNavigation: false, predecessorHighlight: false, emptyAnnounced: false, actionsReachable: false, firstCardInViewport: false, legacyQuerySync: false },
    plan: { surface: false, tiers: false, noOfficialControl: false, summary: false, ordered: false, remaining: false, detailOpened: false, detailContent: false, detailClosed: false, goalRemoval: false, layout: false, switchMs: null, watchedToggle: false, multiGoalSummary: false, chartNavigation: false, chartPlanDomAbsent: false, cameraPreserved: false },
    failures,
  };
  try {
    trace("launch");
    chromeProcess = await launchChrome(chrome, timeoutMs);
    cdp = new CdpClient(chromeProcess.webSocketDebuggerUrl);
    await cdp.connect();
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");
    await cdp.send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
    await cdp.send("Page.navigate", { url: staticServer.url });
    await poll(() => pageEvaluate(cdp, "return document.readyState === 'complete'"), timeoutMs, "page load");
    await poll(() => pageEvaluate(cdp, `return !!document.querySelector('#mobileViewHost [data-mobile-surface="chart"] .svg-wrap svg g.node') && document.querySelectorAll('#mobileViewHost [data-mobile-surface="chart"] .svg-wrap svg g.node').length===131`), timeoutMs, "mobile chart readiness");
    trace("chart-ready");
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
    trace("m3-selection-done");

    const legacyPrepJump=await pointForSelector(cdp, '#mobilePrepJump');
    if(legacyPrepJump){
      await pageEvaluate(cdp, "document.querySelector('#mobilePrepJump')?.scrollIntoView({block:'center'}); return true;");
      const visibleLegacyPrepJump=await pointForSelector(cdp, '#mobilePrepJump');
      const visiblePoint=visibleLegacyPrepJump||legacyPrepJump;
      const visiblePointJson=JSON.stringify(visiblePoint||null);
      const legacyPrepBefore=await pageEvaluate(cdp, `const b=document.querySelector('#mobilePrepJump'); const r=b?.getBoundingClientRect(); return {point:${visiblePointJson},rect:r?{left:r.left,top:r.top,width:r.width,height:r.height}:null,display:b?getComputedStyle(b).display:null,hit:(${visiblePointJson}?document.elementFromPoint(${visiblePointJson}.x,${visiblePointJson}.y)?.outerHTML?.slice(0,180)||null:null),setMobileView:typeof window.setMobileView};`);
      await clickPoint(cdp, visiblePoint);
      let jumpedPlan;
      try { jumpedPlan=await waitForPlan(cdp, (state) => state.view === "plan" && state.planSurface, timeoutMs, "legacy mobile prep jump"); }
      catch(error){ failures.push(`legacy prep jump diagnostics: ${JSON.stringify(legacyPrepBefore)} after=${JSON.stringify(await snapshot(cdp))}`); throw error; }
      const jumpedLayout=await mobilePlanLayoutSnapshot(cdp);
      result.views.legacyPrepJump=jumpedPlan.planSurface&&!jumpedLayout.focusVisible&&!jumpedLayout.watchVisible;
      if(!result.views.legacyPrepJump)failures.push(`legacy prep jump did not use the mobile plan surface: ${JSON.stringify(jumpedPlan)}`);
      await clickPoint(cdp, await pointForSelector(cdp, '#mobileBottomNav [data-mobile-view="chart"]'));
      await waitFor(cdp, (state) => state.view === "chart" && state.selected.includes(node.workId), timeoutMs, "chart restore after legacy prep jump");
      await pageEvaluate(cdp, "window.scrollTo(0,0); return true;");
    } else {
      failures.push("legacy mobile prep jump control was not reachable");
    }

    trace("legacy-jump-done");
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
    trace("sheet-done");
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
    trace("view-switch-done");
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

    // M4: search -> select -> chart must preserve the shared goal and its
    // predecessor highlight.  Query/filter updates are DOM-only while typing.
    await clickPoint(cdp, await pointForSelector(cdp, '#mobileBottomNav [data-mobile-view="search"]'));
    await waitForSearch(cdp, (state) => state.view === "search" && state.searchSurface, timeoutMs, "mobile search surface");
    const searchInput=await pointForSelector(cdp, '#mobileViewHost [data-mobile-search-query]');
    if(!searchInput)throw new Error("mobile search input is not mounted");
    await clickPoint(cdp, searchInput);
    await cdp.send("Input.insertText", { text: "Spider-Man 3" });
    const spider=await waitForSearch(cdp, (state) => state.view === "search" && state.query === "Spider-Man 3" && state.resultCount > 0 && state.firstId === "spider-man-3-2007", timeoutMs, "Spider-Man 3 search results");
    result.search.queried=true;
    result.search.resultCount=spider.resultCount;
    result.search.actionsReachable=spider.actionsReachable;
    result.search.firstCardInViewport=spider.firstCardInViewport;
    if(!result.search.firstCardInViewport)failures.push(`mobile search first result is outside the viewport: ${JSON.stringify(spider)}`);
    if(!result.search.actionsReachable)failures.push(`mobile search actions are below the 44px contract: ${JSON.stringify(spider)}`);
    await pageEvaluate(cdp, "document.getElementById('q')?.scrollIntoView({block:'center'}); return true;");
    await clickPoint(cdp, await pointForSelector(cdp, '#q'));
    await selectAllAndBackspace(cdp);
    await cdp.send("Input.insertText", { text: "Spider-Man" });
    const legacySearch=await waitForSearch(cdp, (state) => state.view === "search" && state.query === "Spider-Man" && state.inputValue === "Spider-Man" && state.resultCount > 0, timeoutMs, "legacy search input synchronization");
    result.search.legacyQuerySync=legacySearch.inputValue === "Spider-Man" && legacySearch.query === "Spider-Man";
    if(!result.search.legacyQuerySync)failures.push(`legacy search input did not sync the M4 surface: ${JSON.stringify(legacySearch)}`);
    await pageEvaluate(cdp, "document.querySelector('#mobileViewHost [data-mobile-search-query]')?.scrollIntoView({block:'center'}); return true;");
    await clickPoint(cdp, await pointForSelector(cdp, '#mobileViewHost [data-mobile-search-query]'));
    await selectAllAndBackspace(cdp);
    await cdp.send("Input.insertText", { text: "Spider-Man 3" });
    await waitForSearch(cdp, (state) => state.query === "Spider-Man 3" && state.inputValue === "Spider-Man 3" && state.firstId === "spider-man-3-2007", timeoutMs, "Spider-Man 3 search reset");
    await pageEvaluate(cdp, "document.querySelector('#mobileViewHost [data-mobile-search-work=\\\"spider-man-3-2007\\\"]')?.scrollIntoView({block:'center'}); return true;");
    const firstSearchSelect=await pointForSelector(cdp, '#mobileViewHost [data-mobile-search-work="spider-man-3-2007"] [data-mobile-search-select]');
    if(!firstSearchSelect)throw new Error("Spider-Man 3 selection action is not mounted");
    await clickPoint(cdp, firstSearchSelect);
    const selectedSearch=await waitForSearch(cdp, (state) => state.selected.includes("spider-man-3-2007"), timeoutMs, "mobile search selection");
    result.search.selected=true;
    result.search.predecessorHighlight=selectedSearch.back.includes("spider-man-2-2004");
    if(!result.search.predecessorHighlight)failures.push(`mobile search selection lost predecessor chain: ${JSON.stringify(selectedSearch)}`);
    await pageEvaluate(cdp, "document.querySelector('#mobileViewHost [data-mobile-search-work=\\\"spider-man-3-2007\\\"]')?.scrollIntoView({block:'center'}); return true;");
    await clickPoint(cdp, await pointForSelector(cdp, '#mobileViewHost [data-mobile-search-work="spider-man-3-2007"] [data-mobile-search-chart]'));
    const searchChart=await waitFor(cdp, (state) => state.view === "chart" && state.chartVisible && state.selected.includes("spider-man-3-2007"), timeoutMs, "mobile search chart navigation");
    result.search.chartNavigation=true;
    result.search.predecessorHighlight=result.search.predecessorHighlight && searchChart.back.includes("spider-man-2-2004");
    if(!result.search.predecessorHighlight)failures.push(`mobile chart return lost predecessor chain: ${JSON.stringify(searchChart)}`);

    // The query is kept in the shared URL state across a view switch and a
    // browser back/popstate transition.
    await clickPoint(cdp, await pointForSelector(cdp, '#mobileBottomNav [data-mobile-view="search"]'));
    const searchAgain=await waitForSearch(cdp, (state) => state.view === "search" && state.inputValue === "Spider-Man 3", timeoutMs, "search query after view switch");
    result.history.queryOnViewSwitch=searchAgain.inputValue === "Spider-Man 3";
    if(!result.history.queryOnViewSwitch)failures.push(`query was not restored on search view switch: ${JSON.stringify(searchAgain)}`);
    await clickPoint(cdp, await pointForSelector(cdp, '#mobileBottomNav [data-mobile-view="plan"]'));
    const planClickState=await pageEvaluate(cdp, "return {href:location.href,view:window.marvelMobileUiStore?.getState?.().view||null};");
    result.history.planClick=planClickState;
    if(planClickState.view!=="plan")failures.push(`plan navigation did not settle on plan: ${JSON.stringify(planClickState)}`);
    await waitFor(cdp, (state) => state.view === "plan" && !state.chartVisible, timeoutMs, "plan view after search");
    await pageEvaluate(cdp, "history.back(); return true;");
    result.history.urlAfterBack=await pageEvaluate(cdp, "return {href:location.href,view:window.marvelMobileUiStore?.getState?.().view||null};");
    const searchPop=await waitForSearch(cdp, (state) => state.view === "search" && state.inputValue === "Spider-Man 3", timeoutMs, "search query after popstate");
    result.history.queryOnPopstate=searchPop.inputValue === "Spider-Man 3";
    if(!result.history.queryOnPopstate)failures.push(`query was not restored after popstate: ${JSON.stringify(searchPop)}`);
    await pageEvaluate(cdp, "document.querySelector('#mobileViewHost [data-mobile-search-query]')?.scrollIntoView({block:'center'}); return true;");
    await clickPoint(cdp, await pointForSelector(cdp, '#mobileViewHost [data-mobile-search-query]'));
    await selectAllAndBackspace(cdp);
    await cdp.send("Input.insertText", { text: "No Such Marvel Work" });
    const emptySearch=await waitForSearch(cdp, (state) => state.emptyVisible && state.emptyText === "該当なし", timeoutMs, "empty mobile search announcement");
    result.search.emptyAnnounced=emptySearch.emptyVisible && emptySearch.emptyText === "該当なし";
    if(!result.search.emptyAnnounced)failures.push(`empty search was not announced through aria-live: ${JSON.stringify(emptySearch)}`);
    trace("m4-done");

    // M5: the preparation surface is the only plan presentation.  It reuses
    // the shared goals, ordered plan, and watched persistence without mounting
    // the legacy chart panels.
    await clickPoint(cdp, await pointForSelector(cdp, '#mobileBottomNav [data-mobile-view="plan"]'));
    const initialPlan=await waitForPlan(cdp, (state) => state.view === "plan" && state.planSurface && state.resultCount > 0, timeoutMs, "mobile plan surface");
    result.plan.surface=initialPlan.planSurface;
    result.plan.tiers=JSON.stringify(initialPlan.tierOptions)===JSON.stringify(["site-proposal","complete"]);
    result.plan.noOfficialControl=!initialPlan.officialControl;
    result.plan.summary=initialPlan.summaryText.includes(`${initialPlan.goalIds.length}作品をゴール中`);
    result.plan.ordered=initialPlan.ordered.length===initialPlan.resultCount && initialPlan.ordered.every(Boolean);
    result.plan.remaining=initialPlan.remainingVisible && initialPlan.progressValue!==null;
    const initialLayout=await mobilePlanLayoutSnapshot(cdp);
    initialPlan.layout=initialLayout;
    result.plan.layout=!!initialLayout && !initialLayout.focusVisible && !initialLayout.watchVisible && initialLayout.left>=0 && initialLayout.width>=initialLayout.viewportWidth-24;
    if(!result.plan.tiers)failures.push(`mobile plan exposed unexpected tiers: ${JSON.stringify(initialPlan)}`);
    if(!result.plan.noOfficialControl)failures.push(`mobile plan exposed an official route control: ${JSON.stringify(initialPlan)}`);
    if(!result.plan.summary)failures.push(`mobile plan goal summary is missing: ${JSON.stringify(initialPlan)}`);
    if(!result.plan.ordered)failures.push(`mobile plan checklist order is missing: ${JSON.stringify(initialPlan)}`);
    if(!result.plan.remaining)failures.push(`mobile plan remaining time/progress is missing: ${JSON.stringify(initialPlan)}`);
    if(!result.plan.layout)failures.push(`mobile plan exposed a narrow or legacy surface: ${JSON.stringify(initialLayout)}`);
    trace("plan-initial-done");

    const firstPlanId=initialPlan.ordered[0];
    const removalBefore=initialPlan.rerenders;
    if(initialPlan.goalRemoveCount<1)failures.push(`mobile plan did not expose per-goal removal: ${JSON.stringify(initialPlan)}`);
    const removalSelector=initialPlan.goalIds.length>1?`#mobileViewHost [data-mobile-plan-remove-goal]:not([data-mobile-plan-remove-goal="${firstPlanId}"])`:'#mobileViewHost [data-mobile-plan-remove-goal]';
    const expectedGoalCount=Math.max(0,initialPlan.goalIds.length-1);
    const removalPoint=await pointForSelector(cdp, removalSelector);
    const removalBeforeClick=await pageEvaluate(cdp, `const b=document.querySelector(${JSON.stringify(removalSelector)}); const r=b?.getBoundingClientRect(); return {point:${JSON.stringify(removalPoint)},tag:b?.tagName||null,rect:r?{left:r.left,top:r.top,width:r.width,height:r.height}:null,hit:(${JSON.stringify(removalPoint)}?document.elementFromPoint(${JSON.stringify(removalPoint)}.x,${JSON.stringify(removalPoint)}.y)?.outerHTML?.slice(0,180):null)};`);
    await clickPoint(cdp, removalPoint);
    const removalImmediate=await mobilePlanSnapshot(cdp);
    let removedPlan;
    try {
      removedPlan=await waitForPlan(cdp, (state) => state.view === "plan" && state.goalIds.length === expectedGoalCount, timeoutMs, "mobile plan goal removal");
    } catch(error) {
      const removalAfterTimeout=await mobilePlanSnapshot(cdp);
      failures.push(`mobile plan goal removal diagnostics: before=${JSON.stringify(removalBeforeClick)} immediate=${JSON.stringify(removalImmediate)} after=${JSON.stringify(removalAfterTimeout)}`);
      throw error;
    }
    result.plan.goalRemoval=removedPlan.goalIds.length===expectedGoalCount && (expectedGoalCount===0?removedPlan.resultCount===0:removedPlan.resultCount>0) && JSON.stringify(removedPlan.rerenders)===JSON.stringify(removalBefore);
    if(!result.plan.goalRemoval)failures.push(`mobile plan goal removal did not update only plan state: before=${JSON.stringify(removalBeforeClick)} immediate=${JSON.stringify(removalImmediate)} current=${JSON.stringify(removedPlan)}`);
    trace("plan-removal-done");
    if(expectedGoalCount===0){
      await clickPoint(cdp, await pointForSelector(cdp, '#mobileBottomNav [data-mobile-view="search"]'));
      await waitForSearch(cdp, (state) => state.searchSurface, timeoutMs, "search after mobile plan goal removal");
      await pageEvaluate(cdp, "document.querySelector('#mobileViewHost [data-mobile-search-query]')?.scrollIntoView({block:'center'}); return true;");
      await clickPoint(cdp, await pointForSelector(cdp, '#mobileViewHost [data-mobile-search-query]'));
      await selectAllAndBackspace(cdp);
      await cdp.send("Input.insertText", { text: "Spider-Man 3" });
      await waitForSearch(cdp, (state) => state.resultCount>0 && state.firstId === "spider-man-3-2007", timeoutMs, "restore goal after mobile plan removal");
      await clickPoint(cdp, await pointForSelector(cdp, '#mobileViewHost [data-mobile-search-work="spider-man-3-2007"] [data-mobile-search-select]'));
      await waitForSearch(cdp, (state) => state.selected.includes("spider-man-3-2007"), timeoutMs, "restored mobile plan goal");
      await clickPoint(cdp, await pointForSelector(cdp, '#mobileBottomNav [data-mobile-view="plan"]'));
      await waitForPlan(cdp, (state) => state.view === "plan" && state.resultCount > 0, timeoutMs, "mobile plan after goal removal restore");
    }

    await clickPoint(cdp, await pointForSelector(cdp, `#mobileViewHost [data-mobile-plan-work="${firstPlanId}"] [data-mobile-plan-detail]`));
    const planDetail=await waitFor(cdp, (state) => !state.sheetHidden, timeoutMs, "plan detail sheet");
    result.plan.detailOpened=planDetail.sheetWork===firstPlanId;
    result.plan.detailContent=/あらすじ/.test(planDetail.sheetBodyText)&&/相関図では/.test(planDetail.sheetBodyText);
    if(!result.plan.detailOpened)failures.push(`plan detail sheet target mismatch: ${JSON.stringify(planDetail)}`);
    if(!result.plan.detailContent)failures.push(`plan detail sheet did not render work metadata: ${JSON.stringify(planDetail)}`);
    await clickPoint(cdp, await pointForSelector(cdp, "#mobileSheetClose"));
    await waitFor(cdp, (state) => state.sheetHidden, timeoutMs, "plan detail sheet close");
    result.plan.detailClosed=true;
    trace("plan-detail-done");

    await clickPoint(cdp, await pointForSelector(cdp, '#mobileBottomNav [data-mobile-view="chart"]'));
    const chartBeforePlan=await waitFor(cdp, (state) => state.view === "chart" && state.chartVisible, timeoutMs, "chart before plan watch toggle");
    const cameraBeforePlan=chartBeforePlan.camera;
    const planSwitchStart=Date.now();
    await clickPoint(cdp, await pointForSelector(cdp, '#mobileBottomNav [data-mobile-view="plan"]'));
    const planForWatch=await waitForPlan(cdp, (state) => state.planSurface && state.ordered.includes(firstPlanId), timeoutMs, "plan watch toggle surface");
    result.plan.switchMs=Date.now()-planSwitchStart;
    if(result.plan.switchMs>1500)failures.push(`mobile plan switch was too slow: ${result.plan.switchMs}ms`);
    const watchedBefore=planForWatch.watchedIds.includes(firstPlanId);
    const planRerendersBefore=planForWatch.rerenders;
    await clickPoint(cdp, await pointForSelector(cdp, `#mobileViewHost [data-mobile-plan-work="${firstPlanId}"] [data-mobile-plan-watched]`));
    const toggled=await waitForPlan(cdp, (state) => state.watchedIds.includes(firstPlanId)===!watchedBefore, timeoutMs, "watched persistence toggle");
    const planRerendersUnchanged=JSON.stringify(toggled.rerenders)===JSON.stringify(planRerendersBefore);
    result.plan.watchedToggle=toggled.watchedIds.includes(firstPlanId)===!watchedBefore && planRerendersUnchanged;
    if(!result.plan.watchedToggle)failures.push(`watched toggle did not persist: ${JSON.stringify(toggled)}`);
    if(!planRerendersUnchanged)failures.push(`watched toggle rebuilt chart: before=${JSON.stringify(planRerendersBefore)} after=${JSON.stringify(toggled.rerenders)}`);
    await clickPoint(cdp, await pointForSelector(cdp, '#mobileBottomNav [data-mobile-view="chart"]'));
    const chartAfterPlan=await waitFor(cdp, (state) => state.view === "chart" && state.chartVisible, timeoutMs, "chart after plan watch toggle");
    result.plan.cameraPreserved=chartAfterPlan.camera===cameraBeforePlan;
    if(!result.plan.cameraPreserved)failures.push(`plan watch toggle changed chart camera: before=${cameraBeforePlan} after=${chartAfterPlan.camera}`);
    trace("plan-watch-done");

    // Exercise the multi-goal contract from a clean single-goal state.  The
    // public search action is a toggle: selecting an already-selected work
    // removes it, so clear the existing chart goals through the real goal-bar
    // control before adding Spider-Man 3 and Iron Man in sequence.
    await clickPoint(cdp, await pointForSelector(cdp, '#mobileBottomNav [data-mobile-view="chart"]'));
    await waitFor(cdp, (state) => state.view === "chart" && state.chartVisible, timeoutMs, "chart before multi-goal reset");
    await pageEvaluate(cdp, "document.getElementById('mobileClearGoals')?.scrollIntoView({block:'center'}); return true;");
    await clickPoint(cdp, await pointForSelector(cdp, '#mobileClearGoals'));
    const clearedGoals=await waitFor(cdp, (state) => state.selected.length===0, timeoutMs, "clear goals before multi-goal selection");
    if(clearedGoals.selected.length)failures.push(`multi-goal reset left selected goals: ${JSON.stringify(clearedGoals)}`);
    await clickPoint(cdp, await pointForSelector(cdp, '#mobileBottomNav [data-mobile-view="search"]'));
    await waitForSearch(cdp, (state) => state.searchSurface, timeoutMs, "search for first multi-goal goal");
    await pageEvaluate(cdp, "document.querySelector('#mobileViewHost [data-mobile-search-query]')?.scrollIntoView({block:'center'}); return true;");
    const secondSearchInput=await pointForSelector(cdp, '#mobileViewHost [data-mobile-search-query]');
    await clickPoint(cdp, secondSearchInput);
    await selectAllAndBackspace(cdp);
    await cdp.send("Input.insertText", { text: "Spider-Man 3" });
    await waitForSearch(cdp, (state) => state.resultCount>0 && state.firstId === "spider-man-3-2007", timeoutMs, "first multi-goal search");
    await clickPoint(cdp, await pointForSelector(cdp, '#mobileViewHost [data-mobile-search-work="spider-man-3-2007"] [data-mobile-search-select]'));
    const firstMultiGoal=await waitForSearch(cdp, (state) => state.selected.length===1 && state.selected.includes("spider-man-3-2007"), timeoutMs, "first multi-goal selection");
    if(firstMultiGoal.selected.length!==1)failures.push(`first multi-goal selection was not singular: ${JSON.stringify(firstMultiGoal)}`);
    await pageEvaluate(cdp, "document.querySelector('#mobileViewHost [data-mobile-search-query]')?.scrollIntoView({block:'center'}); return true;");
    await clickPoint(cdp, await pointForSelector(cdp, '#mobileViewHost [data-mobile-search-query]'));
    await selectAllAndBackspace(cdp);
    await cdp.send("Input.insertText", { text: "Iron Man" });
    await waitForSearch(cdp, (state) => state.resultCount>0 && state.firstId === "iron-man-2008", timeoutMs, "second multi-goal search");
    await clickPoint(cdp, await pointForSelector(cdp, '#mobileViewHost [data-mobile-search-work="iron-man-2008"] [data-mobile-search-select]'));
    const secondMultiGoal=await waitForSearch(cdp, (state) => state.selected.length===2 && state.selected.includes("spider-man-3-2007") && state.selected.includes("iron-man-2008"), timeoutMs, "second multi-goal selection");
    if(secondMultiGoal.selected.length!==2)failures.push(`second multi-goal selection replaced the first goal: ${JSON.stringify(secondMultiGoal)}`);
    await clickPoint(cdp, await pointForSelector(cdp, '#mobileBottomNav [data-mobile-view="plan"]'));
    const multiPlan=await waitForPlan(cdp, (state) => state.planSurface && state.goalIds.length===2 && state.goalIds.includes("spider-man-3-2007") && state.goalIds.includes("iron-man-2008"), timeoutMs, "multi-goal mobile plan");
    // The title text is the user-facing assertion; goal IDs and ordered IDs
    // are the machine-readable ordering assertion.
    result.plan.multiGoalSummary=multiPlan.goalIds.length>=2 && multiPlan.ordered.length===multiPlan.resultCount && multiPlan.summaryText.includes("ゴール中");
    if(!result.plan.multiGoalSummary)failures.push(`multi-goal plan summary/order failed: ${JSON.stringify(multiPlan)}`);
    await clickPoint(cdp, await pointForSelector(cdp, '#mobileBottomNav [data-mobile-view="chart"]'));
    const chartFinal=await waitFor(cdp, (state) => state.view === "chart" && state.chartVisible, timeoutMs, "final chart after plan");
    result.plan.chartNavigation=chartFinal.chartVisible;
    result.plan.chartPlanDomAbsent=!chartFinal.planVisible;
    if(!result.plan.chartPlanDomAbsent)failures.push(`plan DOM remained mounted on chart: ${JSON.stringify(chartFinal)}`);
    trace("audit-done");
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
