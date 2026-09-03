#!/usr/bin/env node

import fs from "node:fs";
import http from "node:http";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import { execFileSync, spawn } from "node:child_process";

const WAIT_TIMEOUT_MS = 20_000;
const CHROME_PROFILE_CLEANUP_RETRIES = 100;
const REPRESENTATIVE_WORK = "spider-man-3-2007";
const CHRONOLOGY_WORK = "iron-man-2008";

function usage() {
  return [
    "Usage: node browser_interaction_audit.mjs --root <repo> [--chrome <path>]",
    "",
    "Runs six real desktop interaction cases against the exported SVG chart:",
    "re-click deselection, background clear, drag preservation, two panel round-trips, and side-tab preservation.",
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
    if (token === "--help") {
      args.help = true;
      continue;
    }
    if (!token.startsWith("--")) throw new Error(`unexpected argument: ${token}`);
    const key = token.slice(2).replaceAll("-", "_");
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) throw new Error(`missing value for --${key.replaceAll("_", "-")}`);
    args[key] = value;
    index += 1;
  }
  return args;
}

function locateChrome(configured) {
  const names = ["google-chrome", "chromium", "chromium-browser", "chrome"];
  const commandCandidates = names.flatMap((name) => {
    try {
      const command = process.platform === "win32" ? "where.exe" : "which";
      const resolved = execFileSync(command, [name], { encoding: "utf8" }).split(/\r?\n/)[0].trim();
      return resolved ? [resolved] : [];
    } catch (_) {
      return [];
    }
  });
  const candidates = [
    configured,
    process.env.MARVEL_CHROME_BIN,
    process.env.CHROME_BIN,
    ...commandCandidates,
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "C:/Program Files/Google/Chrome/Application/chrome.exe",
    "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    `${process.env.LOCALAPPDATA || ""}/Google/Chrome/Application/chrome.exe`,
  ].filter(Boolean);
  for (const candidate of candidates) {
    if (path.isAbsolute(candidate) && fs.existsSync(candidate)) return candidate;
    if (!path.isAbsolute(candidate)) {
      const resolved = candidate.split(path.delimiter).find((entry) => entry && fs.existsSync(entry));
      if (resolved) return resolved;
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
  const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), "marvel-flowchart-interaction-cdp-"));
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
  fs.rmSync(processInfo.userDataDir, {
    recursive: true,
    force: true,
    maxRetries: CHROME_PROFILE_CLEANUP_RETRIES,
    retryDelay: 100,
  });
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
    const result = await this.send("Runtime.evaluate", {
      expression, awaitPromise: true, returnByValue: true,
    });
    if (result.exceptionDetails) throw new Error(result.exceptionDetails.exception?.description || "page evaluation failed");
    return result.result?.value;
  }

  close() {
    try { this.socket?.close(); } catch (_) { /* best effort */ }
  }
}

async function pageEvaluate(cdp, expression) {
  return cdp.evaluate(`(() => { ${expression} })()`);
}

async function loadPage(cdp, url, timeoutMs) {
  await cdp.send("Page.navigate", { url });
  await poll(
    () => pageEvaluate(cdp, "return document.readyState === 'complete'"),
    timeoutMs,
    "page load",
  );
  await poll(() => pageEvaluate(cdp, `
    const svg=document.querySelector('#overview .svg-wrap svg');
    return (svg?.querySelectorAll('g.node').length||0)===131 &&
      (svg?.querySelectorAll('g.edge').length||0)>=361 && !!document.querySelector('#chartConnectionTier');
  `), timeoutMs, "flowchart DOM readiness");
}

async function clickPoint(cdp, point) {
  await cdp.send("Input.dispatchMouseEvent", { type: "mouseMoved", x: point.x, y: point.y });
  await cdp.send("Input.dispatchMouseEvent", { type: "mousePressed", x: point.x, y: point.y, button: "left", clickCount: 1 });
  await cdp.send("Input.dispatchMouseEvent", { type: "mouseReleased", x: point.x, y: point.y, button: "left", clickCount: 1 });
}

async function drag(cdp, start, end) {
  await cdp.send("Input.dispatchMouseEvent", { type: "mouseMoved", x: start.x, y: start.y });
  await cdp.send("Input.dispatchMouseEvent", { type: "mousePressed", x: start.x, y: start.y, button: "left", clickCount: 1 });
  const steps = 5;
  for (let step = 1; step <= steps; step += 1) {
    const ratio = step / steps;
    await cdp.send("Input.dispatchMouseEvent", {
      type: "mouseMoved", x: start.x + (end.x - start.x) * ratio, y: start.y + (end.y - start.y) * ratio,
      button: "left", buttons: 1,
    });
  }
  await cdp.send("Input.dispatchMouseEvent", { type: "mouseReleased", x: end.x, y: end.y, button: "left", clickCount: 1 });
}

async function pointForSelector(cdp, selector) {
  return pageEvaluate(cdp, `
    const element=document.querySelector(${JSON.stringify(selector)});
    if(!element) return null;
    const rect=element.getBoundingClientRect();
    return {x:rect.left+rect.width/2,y:rect.top+rect.height/2,width:rect.width,height:rect.height};
  `);
}

async function pointForWork(cdp, workId) {
  return pageEvaluate(cdp, `
    const svg=document.querySelector('#overview .svg-wrap svg');
    const node=[...(svg?.querySelectorAll('g.node')||[])].find(g=>(g.querySelector(':scope > title')?.textContent||'').trim()===${JSON.stringify(workId)});
    if(!node) return null;
    const rect=node.getBoundingClientRect();
    return {x:rect.left+rect.width/2,y:rect.top+rect.height/2,width:rect.width,height:rect.height};
  `);
}

async function blankPoint(cdp) {
  return pageEvaluate(cdp, `
    const svg=document.querySelector('#overview .svg-wrap svg');
    if(!svg) return null;
    const rect=svg.getBoundingClientRect();
    for(let y=rect.top+8;y<rect.bottom-8;y+=16){
      for(let x=rect.left+8;x<rect.right-8;x+=16){
        const target=document.elementFromPoint(x,y);
        if(target && target.closest?.('.svg-wrap svg')===svg &&
          !target.closest?.('g.node,g.edge,canvas,.zoom-hint,.chart-watch-tools,.chronology-nav-popover,[data-chronology-nav-group]'))
          return {x,y};
      }
    }
    return null;
  `);
}

async function snapshot(cdp) {
  return pageEvaluate(cdp, `
    const active=document.querySelector('.panel.active');
    const svg=active?.querySelector('.svg-wrap svg');
    const canvasAudit=window.marvelCanvasAudit?.()||{};
    const title=g=>(g.querySelector(':scope > title')?.textContent||'').trim();
    return {
      panel:active?.id||null,
      focus:[...(svg?.querySelectorAll('g.node.focus')||[])].map(title).sort(),
      dim:!!svg?.classList.contains('dim'),
      chronologyHighlighted:svg?.querySelectorAll('g.chronology-edge.hl').length||0,
      goalNodes:svg?.querySelectorAll('g.node.goal-node,g.node.current-goal').length||0,
      overlaySyntheticDrawn:canvasAudit.overlaySyntheticDrawn||0,
      selectedText:document.querySelector('#detail')?.textContent?.trim()||'',
      sideTab:document.querySelector('.side-tab-btn.active')?.dataset.sideTab||null,
    };
  `);
}

async function waitFor(cdp, predicate, timeoutMs, label) {
  return poll(async () => predicate(await snapshot(cdp)), timeoutMs, label);
}

async function clickSelector(cdp, selector, timeoutMs) {
  const point = await poll(() => pointForSelector(cdp, selector), timeoutMs, `selector ${selector}`);
  await clickPoint(cdp, point);
}

async function selectRepresentative(cdp, timeoutMs) {
  const point = await poll(() => pointForWork(cdp, REPRESENTATIVE_WORK), timeoutMs, `work ${REPRESENTATIVE_WORK}`);
  await clickPoint(cdp, point);
  return waitFor(cdp, (state) => state.panel === "overview" && state.focus.includes(REPRESENTATIVE_WORK), timeoutMs, "representative selection");
}

async function runCase(cdp, url, timeoutMs, name, action) {
  try {
    await loadPage(cdp, url, timeoutMs);
    await action();
    return { name, ok: true };
  } catch (error) {
    return { name, ok: false, error: String(error?.message || error), state: await snapshot(cdp).catch(() => null) };
  }
}

async function runAudit(args) {
  const root = path.resolve(args.root || ".");
  const timeoutMs = Number(args.timeout_ms || WAIT_TIMEOUT_MS);
  if (!Number.isInteger(timeoutMs) || timeoutMs < 1_000) throw new Error("--timeout-ms must be an integer >= 1000");
  const chrome = locateChrome(args.chrome);
  const staticServer = await startStaticServer(root);
  let chromeProcess = null;
  let cdp = null;
  const cases = [];
  try {
    chromeProcess = await launchChrome(chrome, timeoutMs);
    cdp = new CdpClient(chromeProcess.webSocketDebuggerUrl);
    await cdp.connect();
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");
    cases.push(await runCase(cdp, staticServer.url, timeoutMs, "reclick-deselect", async () => {
      await selectRepresentative(cdp, timeoutMs);
      const point = await pointForWork(cdp, REPRESENTATIVE_WORK);
      await clickPoint(cdp, point);
      await waitFor(cdp, (state) => state.panel === "overview" && state.focus.length === 0 && !state.dim, timeoutMs, "same-work re-click deselection");
    }));
    cases.push(await runCase(cdp, staticServer.url, timeoutMs, "background-clear", async () => {
      await selectRepresentative(cdp, timeoutMs);
      const point = await poll(() => blankPoint(cdp), timeoutMs, "SVG background point");
      await clickPoint(cdp, point);
      await waitFor(cdp, (state) => state.focus.length === 0 && !state.dim, timeoutMs, "background clear");
    }));
    cases.push(await runCase(cdp, staticServer.url, timeoutMs, "drag-preserves-selection", async () => {
      await selectRepresentative(cdp, timeoutMs);
      const start = await poll(() => blankPoint(cdp), timeoutMs, "SVG drag start point");
      const end = { x: Math.min(1480, start.x + 120), y: Math.min(1120, start.y + 80) };
      const before = await pageEvaluate(cdp, "return document.querySelector('#overview .svg-wrap svg')?.style.transform || ''");
      await drag(cdp, start, end);
      const after = await pageEvaluate(cdp, "return document.querySelector('#overview .svg-wrap svg')?.style.transform || ''");
      if (!before || before === after) throw new Error(`drag did not change SVG transform: ${before} -> ${after}`);
      await waitFor(cdp, (state) => state.focus.includes(REPRESENTATIVE_WORK) && state.dim, timeoutMs, "drag selection preservation");
    }));
    cases.push(await runCase(cdp, staticServer.url, timeoutMs, "chronology-round-trip", async () => {
      const point = await poll(() => pointForWork(cdp, CHRONOLOGY_WORK), timeoutMs, `work ${CHRONOLOGY_WORK}`);
      await clickPoint(cdp, point);
      await waitFor(cdp, (state) => state.panel === "overview" && state.focus.includes(CHRONOLOGY_WORK), timeoutMs, "chronology representative selection");
      await clickSelector(cdp, '.tab[data-target="chronology"]', timeoutMs);
      await waitFor(cdp, (state) => state.panel === "chronology" && state.focus.includes(CHRONOLOGY_WORK) && state.chronologyHighlighted > 0, timeoutMs, "chronology focus repaint");
      await clickSelector(cdp, '.tab[data-target="overview"]', timeoutMs);
      await waitFor(cdp, (state) => state.panel === "overview" && state.focus.includes(CHRONOLOGY_WORK), timeoutMs, "overview focus restore");
    }));
    cases.push(await runCase(cdp, staticServer.url, timeoutMs, "release-round-trip", async () => {
      await selectRepresentative(cdp, timeoutMs);
      await clickSelector(cdp, '.tab[data-target="release"]', timeoutMs);
      await waitFor(cdp, (state) => state.panel === "release" && state.focus.includes(REPRESENTATIVE_WORK) && state.overlaySyntheticDrawn === 0, timeoutMs, "release focus repaint without mobile synthetic edges");
      await clickSelector(cdp, '.tab[data-target="overview"]', timeoutMs);
      await waitFor(cdp, (state) => state.panel === "overview" && state.focus.includes(REPRESENTATIVE_WORK), timeoutMs, "overview focus restore after release");
    }));
    cases.push(await runCase(cdp, staticServer.url, timeoutMs, "side-tab-round-trip", async () => {
      await selectRepresentative(cdp, timeoutMs);
      await clickSelector(cdp, '.side-tab-btn[data-side-tab="links"]', timeoutMs);
      await waitFor(cdp, (state) => state.sideTab === "links" && state.focus.includes(REPRESENTATIVE_WORK), timeoutMs, "links tab focus preservation");
      await clickSelector(cdp, '.side-tab-btn[data-side-tab="works"]', timeoutMs);
      await waitFor(cdp, (state) => state.sideTab === "works" && state.focus.includes(REPRESENTATIVE_WORK), timeoutMs, "works tab focus restoration");
    }));
  } finally {
    cdp?.close();
    await new Promise((resolve) => staticServer.server.close(() => resolve()));
    if (chromeProcess) await stopChrome(chromeProcess);
  }
  const failures = cases.filter((item) => !item.ok);
  return { summary: { cases: cases.length, failures: failures.length }, cases, failures };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    process.stdout.write(`${usage()}\n`);
    return;
  }
  const report = await runAudit(args);
  process.stdout.write(`${JSON.stringify(report)}\n`);
  if (report.failures.length) process.exitCode = 1;
}

main().catch((error) => {
  process.stderr.write(`${error.stack || error}\n`);
  process.exitCode = 1;
});
