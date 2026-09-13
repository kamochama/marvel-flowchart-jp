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
  await new Promise((resolve, reject) => { server.once("error", reject); server.listen(0, "127.0.0.1", resolve); });
  return { server, url: `http://127.0.0.1:${server.address().port}/index.html` };
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
  const child = spawn(chrome, ["--headless=new", "--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox", "--no-first-run", "--no-default-browser-check", `--remote-debugging-port=${port}`, `--user-data-dir=${userDataDir}`, "about:blank"], { stdio: ["ignore", "ignore", "ignore"] });
  const target = await poll(async () => {
    const entries = await fetchJsonWithTimeout(`http://127.0.0.1:${port}/json/list`, Math.min(timeoutMs, 1_000));
    return entries?.find((entry) => entry.type === "page" && entry.webSocketDebuggerUrl) || null;
  }, timeoutMs, "Chrome DevTools page target");
  return { child, userDataDir, url: target.webSocketDebuggerUrl };
}

async function stopChrome(processInfo) {
  const child = processInfo?.child;
  if (child && child.exitCode === null && !child.killed) {
    const exited = new Promise((resolve) => child.once("exit", resolve));
    child.kill();
    await Promise.race([exited, new Promise((resolve) => setTimeout(resolve, 5_000))]);
  }
  fs.rmSync(processInfo.userDataDir, { recursive: true, force: true, maxRetries: 100, retryDelay: 100 });
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

async function setViewport(cdp, width, height, mobile = false, coarse = false) {
  await cdp.send("Emulation.setTouchEmulationEnabled", coarse ? { enabled: true, maxTouchPoints: 5 } : { enabled: false });
  await cdp.send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile });
  return poll(() => evaluate(cdp, `return innerWidth===${width}&&innerHeight===${height};`), 10_000, `viewport ${width}x${height}`);
}

async function snapshot(cdp) {
  return evaluate(cdp, `
    const store=window.marvelMobileUiStore?.getState?.()||{};
    const audit=window.marvelSelectionAudit?.()||{};
    const right=document.getElementById('right'), rs=right&&getComputedStyle(right), host=document.getElementById('sheetHost');
    const visible=(node)=>{if(!node)return false;const s=getComputedStyle(node),r=node.getBoundingClientRect();return !node.hidden&&s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0;};
    const shell=document.documentElement.dataset.shell||null;
    const roots={mobile:shell==='mobile'&&visible(document.getElementById('mobileAppShell')),compact:shell==='compact'&&visible(document.querySelector('main')),desktop:shell==='desktop'&&visible(document.querySelector('main'))};
    roots.count=Object.values(roots).filter(Boolean).length;
    const hostVisible=visible(host);
    const detail=document.getElementById('detail');
    const visibleCount=(selector)=>[...document.querySelectorAll(selector)].filter(visible).length;
    return {activeRoots:roots,shell,sheetHost:{count:document.querySelectorAll('#sheetHost').length,parent:host?.parentElement?.id||host?.parentElement?.tagName?.toLowerCase()||null,owner:host?.dataset?.owner||'none',presentation:host?.dataset?.presentation||null,hidden:!hostVisible,overlay:visibleCount('.mobile-sheet-backdrop,[data-mobile-overlay]'),backdrop:visibleCount('#sheetHostBackdrop,.mobile-sheet-backdrop'),focus:document.activeElement?.id||null,inert:document.body.inert===true,scrollLocked:document.documentElement.classList.contains('mobile-sheet-open')||document.body.classList.contains('mobile-sheet-open')},selectedIds:[...(audit.selected||[])],goalOrder:[...(store.goalIds||[])],currentGoal:store.selectedId||window.marvelDetailFocusId||null,preparationTier:window.connectionTier||store.connectionTier||null,activePanel:store.view||document.querySelector('.panel.active')?.id||null,camera:document.querySelector('.svg-wrap')?.getAttribute('data-mobile-camera')||null,rightMutations:window.__phase6Mutations?.right||0,detailMutations:window.__phase6Mutations?.detail||0,sheetHostMutations:window.__phase6Mutations?.sheetHost||0,historyDelta:{push:window.__phase6History?.push||0,replace:window.__phase6History?.replace||0,length:history.length},chartRebuilds:window.__mobileShellAuditCounters?.rebuild||0,fitView:window.__mobileShellAuditCounters?.fit||0};
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
  const chrome = await launchChrome(locateChrome(args.chrome), timeoutMs);
  const cdp = new CdpClient(chrome.url, timeoutMs);
  const failures = [];
  const checkpoints = [];
  try {
    await cdp.connect(); await cdp.send("Page.enable"); await cdp.send("Runtime.enable");
    await cdp.send("Page.navigate", { url: server.url });
    await poll(() => evaluate(cdp, "return document.readyState==='complete';"), timeoutMs, "page load");
    await poll(() => evaluate(cdp, "return document.querySelectorAll('svg g.node').length>=131;"), timeoutMs, "chart readiness");
    await instrument(cdp);
    await setViewport(cdp, 981, 900, false, false);
    checkpoints.push({ name: "desktop-mobile-desktop", state: await snapshot(cdp) });
    await evaluate(cdp, "window.marvelFocusWork?.('iron-man-2008',{center:false}); return true;");
    await poll(() => evaluate(cdp, "return document.getElementById('sheetHost')&&!document.getElementById('sheetHost').hidden;"), timeoutMs, "inspection sheet");
    checkpoints.push({ name: "reason-settings", state: await snapshot(cdp) });
    await evaluate(cdp, "window.openMobileSheet?.('settings','display'); return true;");
    await evaluate(cdp, "window.closeMobileSheet?.(); return true;");
    await evaluate(cdp, "window.setMobileView?.('search',{pushHistory:true}); return true;");
    await evaluate(cdp, "window.setMobileView?.('plan',{pushHistory:true}); return true;");
    checkpoints.push({ name: "chart-search-plan", state: await snapshot(cdp) });
    await evaluate(cdp, "window.setMobileView?.('chart',{pushHistory:true}); return true;");
    checkpoints.push({ name: "plan-chart", state: await snapshot(cdp) });
    await evaluate(cdp, "history.back(); return true;");
    await poll(() => evaluate(cdp, "return window.marvelMobileUiStore?.getState?.().view==='plan';"), timeoutMs, "history back to plan");
    await evaluate(cdp, "history.forward(); return true;");
    await poll(() => evaluate(cdp, "return window.marvelMobileUiStore?.getState?.().view==='chart';"), timeoutMs, "history forward to chart");
    checkpoints.push({ name: "back-forward", state: await snapshot(cdp) });
    await setViewport(cdp, 980, 900, false, false); checkpoints.push({ name: "980", state: await snapshot(cdp) });
    await setViewport(cdp, 761, 900, false, false); checkpoints.push({ name: "761", state: await snapshot(cdp) });
    await setViewport(cdp, 760, 900, true, true); checkpoints.push({ name: "760", state: await snapshot(cdp) });
    await setViewport(cdp, 390, 844, true, true); checkpoints.push({ name: "390", state: await snapshot(cdp) });
    await setViewport(cdp, 981, 900, false, false); checkpoints.push({ name: "981", state: await snapshot(cdp) });
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
      if(s.selectedIds.length!==0||s.goalOrder.length!==0)failures.push(`${row.name}: unexpected selection/goal mutation ${JSON.stringify({selectedIds:s.selectedIds,goalOrder:s.goalOrder})}`);
    }
    const finalState=checkpoints.at(-1).state;
    if(finalState.selectedIds.length!==0) failures.push(`final selection not cleared: ${JSON.stringify(finalState.selectedIds)}`);
  } catch(error) { failures.push(String(error?.stack||error)); }
  finally { cdp.close(); await stopChrome(chrome); await new Promise((resolve)=>server.server.close(resolve)); }
  const report={summary:{cases:1,failures:failures.length},cases:[{name:"phase6-ownership",checkpoints,contract:CONTRACT}],failures};
  console.log(JSON.stringify(report));
  if(failures.length) process.exitCode=1;
}

const args=parseArgs(process.argv.slice(2));
if(args.help){console.log(usage());process.exit(0);}
run(args).catch((error)=>{console.log(JSON.stringify({summary:{cases:1,failures:1},cases:[],failures:[String(error?.stack||error)]}));process.exitCode=1;});
