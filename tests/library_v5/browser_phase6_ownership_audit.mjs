#!/usr/bin/env node

/*
 * Phase 6 ownership audit.  This runner deliberately reuses the same static
 * fixture and Chrome/CDP lifecycle as the existing browser audits, but keeps
 * one compact scenario whose output is a state-delta record rather than a
 * string-presence check.
 */
import fs from "node:fs";
import http from "node:http";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import { execFileSync, spawn } from "node:child_process";

const CONTRACT = [
  "MutationObserver", "pushState", "replaceState", "historyDelta", "activeRoots",
  "sheetHost", "overlay", "backdrop", "detailMutations", "rightMutations",
  "chartRebuilds", "fitView", "selectedIds", "goalOrder", "currentGoal",
  "preparationTier", "activePanel", "camera", "chart-search-plan", "plan-chart",
  "reason-settings", "back-forward", "desktop-mobile-desktop", "761", "980", "981",
];

function usage() {
  return [
    "Usage: node browser_phase6_ownership_audit.mjs --root <repo> [--chrome <path>] [--timeout-ms <n>]",
    "Runs one bounded Chrome/CDP ownership scenario and emits JSON.",
    `Records ${CONTRACT.join(", ")} and emits a JSON report with failures.`,
    "Options: --root <path> --chrome <path> --timeout-ms <n> --help",
  ].join("\n");
}

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (token === "--help") { args.help = true; continue; }
    if (!token.startsWith("--")) throw new Error(`unexpected argument: ${token}`);
    const key = token.slice(2).replaceAll("-", "_");
    const value = argv[++i];
    if (!value || value.startsWith("--")) throw new Error(`missing value for --${key}`);
    args[key] = value;
  }
  return args;
}

function locateChrome(configured) {
  const candidates = [configured, process.env.MARVEL_CHROME_BIN, process.env.CHROME_BIN];
  for (const name of ["google-chrome", "chromium", "chromium-browser", "chrome"]) {
    try {
      const command = process.platform === "win32" ? "where.exe" : "which";
      candidates.push(execFileSync(command, [name], { encoding: "utf8" }).split(/\r?\n/)[0].trim());
    } catch (_) { /* keep searching */ }
  }
  candidates.push(
    "C:/Program Files/Google/Chrome/Application/chrome.exe",
    "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    `${process.env.LOCALAPPDATA || ""}/Google/Chrome/Application/chrome.exe`,
    "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
  );
  for (const candidate of candidates.filter(Boolean)) if (fs.existsSync(candidate)) return candidate;
  throw new Error("Chrome/Chromium executable not found; pass --chrome or MARVEL_CHROME_BIN");
}

function freePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      server.close(() => resolve(address.port));
    });
  });
}

async function fetchJsonWithTimeout(url, timeoutMs) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), Math.max(250, timeoutMs));
  try {
    const response = await fetch(url, { signal: controller.signal });
    if (!response.ok) return null;
    return await response.json();
  } finally {
    clearTimeout(timer);
  }
}

function contentType(file) {
  return { ".html": "text/html; charset=utf-8", ".json": "application/json", ".js": "text/javascript" }[path.extname(file)] || "application/octet-stream";
}

async function startServer(root) {
  const resolved = fs.realpathSync(root);
  const sockets = new Set();
  const server = http.createServer((request, response) => {
    try {
      const pathname = decodeURIComponent(new URL(request.url || "/", "http://localhost").pathname);
      const relative = pathname === "/" ? "index.html" : pathname.replace(/^\/+/, "");
      const file = path.resolve(resolved, relative);
      const check = path.relative(resolved, file);
      if (check.startsWith("..") || path.isAbsolute(check) || !fs.existsSync(file) || !fs.statSync(file).isFile()) {
        response.writeHead(404); response.end("not found"); return;
      }
      response.writeHead(200, { "Content-Type": contentType(file), "Cache-Control": "no-store" });
      fs.createReadStream(file).pipe(response);
    } catch (error) { response.writeHead(400); response.end(String(error)); }
  });
  server.on("connection", (socket) => {
    sockets.add(socket);
    socket.once("close", () => sockets.delete(socket));
  });
  await new Promise((resolve, reject) => { server.once("error", reject); server.listen(0, "127.0.0.1", resolve); });
  return { server, sockets, url: `http://127.0.0.1:${server.address().port}/index.html` };
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

async function launchChrome(chrome, timeoutMs) {
  const port = await freePort();
  const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), "marvel-phase6-cdp-"));
  let child = null;
  try {
    child = spawn(chrome, ["--headless=new", "--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox", "--no-first-run", "--no-default-browser-check", `--remote-debugging-port=${port}`, `--user-data-dir=${userDataDir}`, "about:blank"], { stdio: ["ignore", "ignore", "ignore"], detached: process.platform !== "win32" });
    const target = await poll(async () => {
      const entries = await fetchJsonWithTimeout(`http://127.0.0.1:${port}/json/list`, Math.min(timeoutMs, 1_000));
      return entries?.find((entry) => entry.type === "page" && entry.webSocketDebuggerUrl) || null;
    }, timeoutMs, "Chrome DevTools page target");
    return { child, userDataDir, url: target.webSocketDebuggerUrl };
  } catch (error) {
    killProcessTree(child);
    try { fs.rmSync(userDataDir, { recursive: true, force: true, maxRetries: 3, retryDelay: 50 }); } catch (_) { /* temporary profile cleanup is best effort */ }
    throw error;
  }
}

async function launchChromeWithRetries(chrome, timeoutMs, attempts = 3) {
  let lastError = null;
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    try {
      return await launchChrome(chrome, timeoutMs);
    } catch (error) {
      lastError = error;
      if (attempt + 1 < attempts) await new Promise((resolve) => setTimeout(resolve, 250));
    }
  }
  throw lastError || new Error("Chrome launch failed");
}

function killProcessTree(child) {
  if (!child || child.exitCode !== null || child.killed) return;
  if (process.platform === "win32") {
    try { execFileSync("taskkill", ["/PID", String(child.pid), "/T", "/F"], { stdio: "ignore" }); } catch (_) { /* best effort */ }
    return;
  }
  try { process.kill(-child.pid, "SIGKILL"); }
  catch (_) { try { child.kill("SIGKILL"); } catch (_) { /* best effort */ } }
}

async function stopChrome(processInfo) {
  const child = processInfo?.child;
  if (child && child.exitCode === null && !child.killed) {
    const exited = new Promise((resolve) => child.once("exit", resolve));
    killProcessTree(child);
    await Promise.race([exited, new Promise((resolve) => setTimeout(resolve, 5_000))]);
  }
  try { fs.rmSync(processInfo.userDataDir, { recursive: true, force: true, maxRetries: 3, retryDelay: 50 }); } catch (_) { /* temporary profile cleanup is best effort */ }
}

async function stopServer(serverInfo) {
  const server = serverInfo?.server;
  if (!server) return;
  const destroySockets = () => {
    for (const socket of serverInfo.sockets || []) socket.destroy();
  };
  await new Promise((resolve) => {
    let settled = false;
    let timer = null;
    const finish = () => {
      if (!settled) {
        settled = true;
        if (timer) clearTimeout(timer);
        resolve();
      }
    };
    try {
      server.close(finish);
      // Chrome may leave an HTTP keep-alive socket open after CDP closes.  The
      // audit must have a bounded shutdown even when that socket is not idle.
      server.closeAllConnections?.();
      server.closeIdleConnections?.();
      destroySockets();
    } catch (_) { finish(); }
    timer = setTimeout(finish, 2_000);
    timer.unref?.();
  });
  destroySockets();
}

class CdpClient {
  constructor(url, timeoutMs) { this.url = url; this.timeoutMs = timeoutMs; this.nextId = 1; this.pending = new Map(); }
  async connect() {
    this.socket = new WebSocket(this.url);
    await new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error("CDP connection timeout")), this.timeoutMs);
      this.socket.addEventListener("open", () => { clearTimeout(timer); resolve(); }, { once: true });
      this.socket.addEventListener("error", () => { clearTimeout(timer); reject(new Error("CDP websocket error")); }, { once: true });
    });
    this.socket.addEventListener("message", (event) => {
      const message = JSON.parse(String(event.data));
      const pending = this.pending.get(message.id);
      if (!pending) return;
      this.pending.delete(message.id); clearTimeout(pending.timer);
      message.error ? pending.reject(new Error(message.error.message || "CDP command failed")) : pending.resolve(message.result || {});
    });
  }
  send(method, params = {}) {
    const id = this.nextId++;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => { this.pending.delete(id); reject(new Error(`CDP command timeout: ${method}`)); }, this.timeoutMs);
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

const evaluate = (cdp, body) => cdp.evaluate(`(() => { ${body} })()`);

async function setViewport(cdp, width, height, mobile = false, coarse = false, expectedShell = null) {
  await cdp.send("Emulation.setTouchEmulationEnabled", coarse ? { enabled: true, maxTouchPoints: 5 } : { enabled: false });
  await cdp.send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile });
  await poll(() => evaluate(cdp, `return innerWidth===${width}&&innerHeight===${height};`), 10_000, `viewport ${width}x${height}`);
  if (expectedShell) await poll(() => evaluate(cdp, `return document.documentElement.dataset.shell===${JSON.stringify(expectedShell)};`), 10_000, `shell ${expectedShell}`);
  return true;
}

async function snapshot(cdp) {
  return evaluate(cdp, `
    const store=window.marvelMobileUiStore?.getState?.()||{};
    const audit=window.marvelSelectionAudit?.()||{};
    const right=document.getElementById('right'), rs=right&&getComputedStyle(right), host=document.getElementById('sheetHost');
    const visible=(node)=>{if(!node)return false;const s=getComputedStyle(node),r=node.getBoundingClientRect();return !node.hidden&&s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0&&r.bottom>0&&r.right>0&&r.top<innerHeight&&r.left<innerWidth;};
    const shell=document.documentElement.dataset.shell||null;
    const mobileVisible=visible(document.getElementById('mobileAppShell'));
    const mainVisible=visible(document.querySelector('main'));
    const roots={mobile:shell==='mobile'&&mobileVisible,compact:shell==='compact'&&mainVisible,desktop:shell==='desktop'&&mainVisible};
    roots.count=Object.values(roots).filter(Boolean).length;
    const hostVisible=visible(host);
    const detail=document.getElementById('detail');
    const visibleCount=(selector)=>[...document.querySelectorAll(selector)].filter(visible).length;
    return {activeRoots:roots,presentationVisibility:{mobile:mobileVisible,main:mainVisible},shell,sheetHost:{count:document.querySelectorAll('#sheetHost').length,parent:host?.parentElement?.id||host?.parentElement?.tagName?.toLowerCase()||null,owner:host?.dataset?.owner||'none',presentation:host?.dataset?.presentation||null,hidden:!hostVisible,overlay:visibleCount('.mobile-sheet-backdrop,[data-mobile-overlay]'),backdrop:visibleCount('#sheetHostBackdrop,.mobile-sheet-backdrop'),focus:document.activeElement?.id||null,inert:document.body.inert===true,scrollLocked:document.documentElement.classList.contains('mobile-sheet-open')||document.body.classList.contains('mobile-sheet-open')},selectedIds:[...(audit.selected||[])],goalOrder:[...(store.goalIds||[])],currentGoal:store.selectedId||window.marvelDetailFocusId||null,preparationTier:window.marvelGetConnectionTier?.()||null,activePanel:store.view||document.querySelector('.panel.active')?.id||null,camera:document.querySelector('.svg-wrap')?.getAttribute('data-mobile-camera')||null,rightMutations:window.__phase6Mutations?.right||0,detailMutations:window.__phase6Mutations?.detail||0,sheetHostMutations:window.__phase6Mutations?.sheetHost||0,historyDelta:{push:window.__phase6History?.push||0,replace:window.__phase6History?.replace||0,length:history.length},chartRebuilds:window.__mobileShellAuditCounters?.rebuild||0,fitView:window.__mobileShellAuditCounters?.fit||0};
  `);
}

async function instrument(cdp) {
  await evaluate(cdp, `
    window.__phase6Mutations={right:0,detail:0,sheetHost:0};
    for(const [key,id] of [['right','right'],['detail','detail'],['sheetHost','sheetHost']]){const node=document.getElementById(id);if(node)new MutationObserver(()=>window.__phase6Mutations[key]++).observe(node,{subtree:true,childList:true,attributes:true,characterData:true});}
    window.__phase6History={push:0,replace:0};
    for(const name of ['pushState','replaceState']){const original=history[name];history[name]=function(...args){window.__phase6History[name==='pushState'?'push':'replace']++;return original.apply(this,args);};}
    window.__mobileShellAuditCounters={render:0,fit:0,rebuild:0};
    for(const [name,key] of [['render','render'],['fitView','fit'],['rebuildMobileCanvas','rebuild']]){const original=window[name];if(typeof original==='function')window[name]=function(...args){window.__mobileShellAuditCounters[key]++;return original.apply(this,args);};}
    return true;
  `);
}

async function run(args) {
  const timeoutMs = Number(args.timeout_ms || 8_000);
  const server = await startServer(path.resolve(args.root || "."));
  let chrome = null;
  let cdp = null;
  const failures = [];
  const checkpoints = [];
  try {
    chrome = await launchChromeWithRetries(locateChrome(args.chrome), timeoutMs);
    cdp = new CdpClient(chrome.url, timeoutMs);
    await cdp.connect(); await cdp.send("Page.enable"); await cdp.send("Runtime.enable");
    await cdp.send("Page.navigate", { url: server.url });
    await poll(() => evaluate(cdp, "return document.readyState==='complete';"), timeoutMs, "page load");
    await poll(() => evaluate(cdp, "return document.querySelectorAll('svg g.node').length>=131;"), timeoutMs, "chart readiness");
    await instrument(cdp);
    await setViewport(cdp, 981, 900, false, false, "desktop");
    const emptyStart = await snapshot(cdp);
    checkpoints.push({ name: "desktop-mobile-desktop", state: emptyStart });
    await evaluate(cdp, "window.marvelFocusWork?.('iron-man-2008',{center:false}); return true;");
    await poll(() => evaluate(cdp, "return document.getElementById('sheetHost')&&!document.getElementById('sheetHost').hidden;"), timeoutMs, "inspection sheet");
    const inspectionBaseline = await snapshot(cdp);
    await evaluate(cdp, "window.openMobileSheet?.('reason','relation-audit'); return true;");
    await poll(() => evaluate(cdp, "return document.getElementById('sheetHost')?.dataset?.owner==='explicit'&&!document.getElementById('sheetHost')?.hidden;"), timeoutMs, "reason sheet");
    await evaluate(cdp, "window.closeMobileSheet?.(); return true;");
    await poll(() => evaluate(cdp, "return !!document.getElementById('sheetHost')?.hidden;"), timeoutMs, "reason sheet close");
    await evaluate(cdp, "window.openMobileSheet?.('settings','display'); return true;");
    await poll(() => evaluate(cdp, "return document.getElementById('sheetHost')?.dataset?.owner==='explicit'&&!document.getElementById('sheetHost')?.hidden;"), timeoutMs, "settings sheet");
    await evaluate(cdp, "window.closeMobileSheet?.(); return true;");
    await poll(() => evaluate(cdp, "return !!document.getElementById('sheetHost')?.hidden;"), timeoutMs, "settings sheet close");
    const inspectionAfter = await snapshot(cdp);
    if (inspectionAfter.detailMutations !== inspectionBaseline.detailMutations) failures.push(`inspection: #detail mutated during reason/settings (${inspectionBaseline.detailMutations}->${inspectionAfter.detailMutations})`);
    if (inspectionAfter.chartRebuilds !== inspectionBaseline.chartRebuilds || inspectionAfter.fitView !== inspectionBaseline.fitView) failures.push(`inspection: chart changed during reason/settings ${JSON.stringify({before:[inspectionBaseline.chartRebuilds,inspectionBaseline.fitView],after:[inspectionAfter.chartRebuilds,inspectionAfter.fitView]})}`);
    if (JSON.stringify(inspectionAfter.selectedIds) !== JSON.stringify(inspectionBaseline.selectedIds) || JSON.stringify(inspectionAfter.goalOrder) !== JSON.stringify(inspectionBaseline.goalOrder)) failures.push("inspection: selection/goals changed during reason/settings");
    checkpoints.push({ name: "reason-settings", state: inspectionAfter });

    await evaluate(cdp, "window.marvelReturnToGoalView?.(); window.marvelToggleGoal?.('iron-man-2008'); window.marvelSetConnectionTier?.('complete'); return true;");
    await poll(() => evaluate(cdp, "return (window.marvelSelectionAudit?.().selected||[]).includes('iron-man-2008') && window.marvelMobileUiStore?.getState?.().goalIds?.includes('iron-man-2008');"), timeoutMs, "seed goal");
    const roundTripStart = await snapshot(cdp);
    if (!roundTripStart.goalOrder.length || roundTripStart.preparationTier !== "complete") failures.push(`seed: goal/tier not established ${JSON.stringify({goals:roundTripStart.goalOrder,tier:roundTripStart.preparationTier})}`);
    await evaluate(cdp, "window.setMobileView?.('search',{pushHistory:true}); return true;");
    await evaluate(cdp, "window.setMobileView?.('plan',{pushHistory:true}); return true;");
    const chartSearchPlan = await snapshot(cdp);
    checkpoints.push({ name: "chart-search-plan", state: chartSearchPlan });
    if (chartSearchPlan.historyDelta.push !== roundTripStart.historyDelta.push + 2) failures.push(`chart-search-plan: expected two surface history pushes ${JSON.stringify({before:roundTripStart.historyDelta,after:chartSearchPlan.historyDelta})}`);
    await evaluate(cdp, "window.setMobileView?.('chart',{pushHistory:true}); return true;");
    const planChart = await snapshot(cdp);
    checkpoints.push({ name: "plan-chart", state: planChart });
    if (planChart.historyDelta.push !== chartSearchPlan.historyDelta.push + 1) failures.push(`plan-chart: expected one surface history push ${JSON.stringify({before:chartSearchPlan.historyDelta,after:planChart.historyDelta})}`);
    await evaluate(cdp, "history.back(); return true;");
    await poll(() => evaluate(cdp, "return window.marvelMobileUiStore?.getState?.().view==='plan';"), timeoutMs, "history back to plan");
    await evaluate(cdp, "history.forward(); return true;");
    await poll(() => evaluate(cdp, "return window.marvelMobileUiStore?.getState?.().view==='chart';"), timeoutMs, "history forward to chart");
    const backForward = await snapshot(cdp);
    checkpoints.push({ name: "back-forward", state: backForward });
    if (backForward.historyDelta.push !== planChart.historyDelta.push || backForward.historyDelta.replace !== planChart.historyDelta.replace || backForward.historyDelta.length !== planChart.historyDelta.length) failures.push(`back-forward: history writes changed during traversal ${JSON.stringify({before:planChart.historyDelta,after:backForward.historyDelta})}`);
    for (const field of ["selectedIds","goalOrder","currentGoal","preparationTier","activePanel","camera"]) {
      if (JSON.stringify(backForward[field]) !== JSON.stringify(roundTripStart[field])) failures.push(`back-forward: ${field} did not round-trip`);
    }
    await setViewport(cdp, 980, 900, false, false, "compact"); checkpoints.push({ name: "980", state: await snapshot(cdp) });
    await setViewport(cdp, 761, 900, false, false, "compact"); checkpoints.push({ name: "761", state: await snapshot(cdp) });
    await setViewport(cdp, 760, 900, true, true, "mobile"); checkpoints.push({ name: "760", state: await snapshot(cdp) });
    await setViewport(cdp, 390, 844, true, true, "mobile"); checkpoints.push({ name: "390", state: await snapshot(cdp) });
    await setViewport(cdp, 981, 900, false, false, "desktop"); checkpoints.push({ name: "981", state: await snapshot(cdp) });
    for(const row of checkpoints){
      const s=row.state;
      if(s.activeRoots.count!==1)failures.push(`${row.name}: active root count ${s.activeRoots.count}`);
      if(s.sheetHost.count!==1)failures.push(`${row.name}: sheetHost count ${s.sheetHost.count}`);
      if(s.sheetHost.overlay>1||s.sheetHost.backdrop>1)failures.push(`${row.name}: duplicate overlay/backdrop`);
      if(!s.shell)failures.push(`${row.name}: missing data-shell`);
      const expectedMobile=["760","390"].includes(row.name);
      const expectedShell=expectedMobile?"mobile":["980","761"].includes(row.name)?"compact":"desktop";
      const expectedParent=expectedMobile?"body":"right";
      if(s.shell!==expectedShell||s.sheetHost.parent!==expectedParent)failures.push(`${row.name}: ownership mismatch ${JSON.stringify({shell:s.shell,parent:s.sheetHost.parent})}`);
      if(s.presentationVisibility.mobile!==expectedMobile || s.presentationVisibility.main===expectedMobile) failures.push(`${row.name}: independent presentation visibility mismatch ${JSON.stringify(s.presentationVisibility)}`);
      if(!s.sheetHost.hidden || s.sheetHost.overlay!==0 || s.sheetHost.backdrop!==0 || s.inert || s.scrollLocked) failures.push(`${row.name}: closed sheet modal state leaked ${JSON.stringify({hidden:s.sheetHost.hidden,overlay:s.sheetHost.overlay,backdrop:s.sheetHost.backdrop,inert:s.inert,scrollLocked:s.scrollLocked})}`);
    }
    const finalState=checkpoints.at(-1).state;
    for (const field of ["selectedIds","goalOrder","currentGoal","preparationTier","activePanel","camera"]) {
      if (JSON.stringify(finalState[field]) !== JSON.stringify(roundTripStart[field])) failures.push(`final desktop round-trip: ${field} changed`);
    }
  } catch(error) { failures.push(String(error?.stack||error)); }
  finally { cdp?.close(); if (chrome) await stopChrome(chrome); await stopServer(server); }
  const report={summary:{cases:1,failures:failures.length},cases:[{name:"phase6-ownership",checkpoints,contract:CONTRACT}],failures};
  const exitCode = failures.length ? 1 : 0;
  process.stdout.write(`${JSON.stringify(report)}\n`, () => process.exit(exitCode));
}

const args=parseArgs(process.argv.slice(2));
if(args.help){console.log(usage());process.exit(0);}
run(args).catch((error)=>{
  const report={summary:{cases:1,failures:1},cases:[],failures:[String(error?.stack||error)]};
  process.stdout.write(`${JSON.stringify(report)}\n`, () => process.exit(1));
});
