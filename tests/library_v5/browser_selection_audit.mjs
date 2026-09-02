#!/usr/bin/env node

import fs from "node:fs";
import http from "node:http";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import { execFileSync, spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const TIERS = ["site-proposal", "complete"];
const EDGE_CLASSES = ["backhl", "forwardhl", "bothhl", "contexthl"];
const WAIT_TIMEOUT_MS = 20_000;
const CHROME_PROFILE_CLEANUP_RETRIES = 100;

function usage() {
  return [
    "Usage: node browser_selection_audit.mjs --root <repo> --expected <json> [--chrome <path>]",
    "",
    "Runs the real desktop SVG click audit for every exported work in both public tiers.",
    "The expected JSON is produced by the independent Python selection oracle.",
    "",
    "Options:",
    "  --root <path>      Repository root to serve over HTTP",
    "  --expected <path>  JSON file with tier/work expected edge classes",
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
  const commandNames = ["google-chrome", "chromium", "chromium-browser", "chrome"];
  const commandCandidates = commandNames.flatMap((name) => {
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
    ".json": "application/json; charset=utf-8",
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
  const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), "marvel-flowchart-cdp-"));
  const child = spawn(
    chromePath,
    [
      "--headless=new",
      "--disable-gpu",
      "--disable-dev-shm-usage",
      "--no-sandbox",
      "--no-first-run",
      "--no-default-browser-check",
      "--window-size=1600,1200",
      `--remote-debugging-port=${port}`,
      `--user-data-dir=${userDataDir}`,
      "about:blank",
    ],
    { stdio: ["ignore", "ignore", "pipe"] },
  );
  let launchError = null;
  child.once("error", (error) => { launchError = error; });
  try {
    const target = await poll(
      async () => {
        if (launchError) throw launchError;
        const response = await fetch(`http://127.0.0.1:${port}/json/list`);
        if (!response.ok) return null;
        const targets = await response.json();
        return targets.find((entry) => entry.type === "page" && entry.webSocketDebuggerUrl) || null;
      },
      timeoutMs,
      "Chrome DevTools page target",
    );
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
  // Chrome's child processes can briefly leave the profile non-empty after the
  // browser process exits. Node's recursive remover handles ENOTEMPTY/EBUSY/
  // EPERM with bounded retries; use a longer window for hosted CI runners.
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
    this.eventWaiters = new Map();
  }

  async connect() {
    this.socket = new WebSocket(this.url);
    await new Promise((resolve, reject) => {
      this.socket.addEventListener("open", resolve, { once: true });
      this.socket.addEventListener("error", (event) => reject(new Error(`CDP WebSocket error: ${event.message || "unknown"}`)), { once: true });
    });
    this.socket.addEventListener("message", (event) => this.#onMessage(event.data));
    this.socket.addEventListener("close", () => {
      for (const { reject } of this.pending.values()) reject(new Error("CDP socket closed"));
      this.pending.clear();
    });
  }

  #onMessage(raw) {
    const message = JSON.parse(String(raw));
    if (message.id) {
      const pending = this.pending.get(message.id);
      if (!pending) return;
      this.pending.delete(message.id);
      if (message.error) pending.reject(new Error(message.error.message || "CDP command failed"));
      else pending.resolve(message.result || {});
      return;
    }
    const waiters = this.eventWaiters.get(message.method);
    if (waiters?.length) waiters.shift()(message.params || {});
  }

  send(method, params = {}) {
    const id = this.nextId++;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.socket.send(JSON.stringify({ id, method, params }));
    });
  }

  waitForEvent(method, timeoutMs) {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        const waiters = this.eventWaiters.get(method) || [];
        const index = waiters.indexOf(onEvent);
        if (index >= 0) waiters.splice(index, 1);
        reject(new Error(`${method} timed out`));
      }, timeoutMs);
      const onEvent = (params) => {
        clearTimeout(timer);
        resolve(params);
      };
      const waiters = this.eventWaiters.get(method) || [];
      waiters.push(onEvent);
      this.eventWaiters.set(method, waiters);
    });
  }

  async evaluate(expression) {
    const result = await this.send("Runtime.evaluate", {
      expression,
      awaitPromise: true,
      returnByValue: true,
    });
    if (result.exceptionDetails) {
      throw new Error(result.exceptionDetails.exception?.description || "page evaluation failed");
    }
    return result.result?.value;
  }

  close() {
    try {
      this.socket?.close();
    } catch (_) {
      // Best effort cleanup.
    }
  }
}

function normalizeExpected(raw) {
  if (!raw || typeof raw !== "object") throw new Error("expected JSON must be an object");
  const result = {};
  for (const tier of TIERS) {
    if (!raw[tier] || typeof raw[tier] !== "object") throw new Error(`expected JSON missing tier: ${tier}`);
    result[tier] = {};
    for (const [workId, value] of Object.entries(raw[tier])) {
      if (!value || typeof value !== "object") throw new Error(`expected entry must be an object: ${tier}/${workId}`);
      result[tier][workId] = {};
      for (const category of ["back", "forward", "context"]) {
        if (!Array.isArray(value[category])) throw new Error(`expected entry missing ${category}: ${tier}/${workId}`);
        result[tier][workId][category] = new Set(value[category].map(String));
      }
    }
  }
  return result;
}

async function pageEvaluate(cdp, expression) {
  return cdp.evaluate(`(() => { ${expression} })()`);
}

async function waitForReady(cdp, timeoutMs) {
  return poll(
    async () => pageEvaluate(cdp, `
      const svg=document.querySelector('.panel.active .svg-wrap svg');
      const nodes=svg?.querySelectorAll('g.node').length||0;
      const edges=svg?.querySelectorAll('g.edge').length||0;
      return nodes===131 && edges>=361 && !!document.querySelector('#chartConnectionTier');
    `),
    timeoutMs,
    "flowchart DOM readiness",
  );
}

async function setTier(cdp, tier, timeoutMs) {
  const actual = await pageEvaluate(cdp, `
    const select=document.querySelector('#chartConnectionTier');
    if(!select) throw new Error('chart tier selector missing');
    select.value=${JSON.stringify(tier)};
    select.dispatchEvent(new Event('change',{bubbles:true}));
    return select.value;
  `);
  if (actual !== tier) throw new Error(`chart tier did not accept ${tier}: ${actual}`);
  await poll(
    async () => pageEvaluate(cdp, `return (() => {
      const select=document.querySelector('#chartConnectionTier');
      return !!select && select.value===${JSON.stringify(tier)} && (window.marvelGetConnectionTier?.()||'')===${JSON.stringify(tier)};
    })()`),
    timeoutMs,
    `chart tier update for ${tier}`,
  );
}

async function clearSelection(cdp, timeoutMs) {
  await pageEvaluate(cdp, `
    window.marvelReturnToGoalView?.();
    window.clearAllGoalsWithUndo?.();
    return true;
  `);
  await poll(
    async () => pageEvaluate(cdp, `return document.querySelectorAll('.panel.active .svg-wrap svg g.node.focus').length===0`),
    timeoutMs,
    "selection clear",
  );
}

async function clickWork(cdp, workId) {
  const clicked = await pageEvaluate(cdp, `
    const svg=document.querySelector('.panel.active .svg-wrap svg');
    const node=[...(svg?.querySelectorAll('g.node')||[])].find(g=>(g.querySelector(':scope > title')?.textContent||'').trim()===${JSON.stringify(workId)});
    if(!node) return false;
    node.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,view:window}));
    return true;
  `);
  if (!clicked) throw new Error(`SVG node not found: ${workId}`);
}

async function snapshot(cdp, workId) {
  return pageEvaluate(cdp, `
    const svg=document.querySelector('.panel.active .svg-wrap svg');
    const nodes=[...(svg?.querySelectorAll('g.node.focus')||[])].map(g=>(g.querySelector(':scope > title')?.textContent||'').trim());
    const edges={back:new Set(),forward:new Set(),context:new Set()};
    for(const g of (svg?.querySelectorAll('g.edge')||[])){
      const key=window.marvelEdgeKeyFromGroup?.(g)||'';
      if(!key) continue;
      if(g.classList.contains('bothhl')){edges.back.add(key);edges.forward.add(key);}
      else if(g.classList.contains('backhl'))edges.back.add(key);
      else if(g.classList.contains('forwardhl'))edges.forward.add(key);
      else if(g.classList.contains('contexthl'))edges.context.add(key);
    }
    return {work_id:${JSON.stringify(workId)},focus:nodes,back:[...edges.back].sort(),forward:[...edges.forward].sort(),context:[...edges.context].sort()};
  `);
}

function stableSnapshot(cdp, workId, timeoutMs) {
  let previous = "";
  let repeats = 0;
  return poll(
    async () => {
      const value = await snapshot(cdp, workId);
      if (!value.focus.includes(workId)) {
        repeats = 0;
        return null;
      }
      const signature = JSON.stringify(value);
      repeats = signature === previous ? repeats + 1 : 0;
      previous = signature;
      return repeats >= 2 ? value : null;
    },
    timeoutMs,
    `selection render for ${workId}`,
  );
}

function difference(expected, actual) {
  const missing = {};
  const extra = {};
  for (const category of ["back", "forward", "context"]) {
    const expectedSet = expected?.[category] || new Set();
    const actualSet = new Set(actual?.[category] || []);
    missing[category] = [...expectedSet].filter((key) => !actualSet.has(key)).sort();
    extra[category] = [...actualSet].filter((key) => !expectedSet.has(key)).sort();
  }
  return {
    missing,
    extra,
    hasDifference: Object.values(missing).some((values) => values.length) || Object.values(extra).some((values) => values.length),
  };
}

async function runAudit(args, expected) {
  const root = path.resolve(args.root || path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../.."));
  const timeoutMs = Number(args.timeout_ms || WAIT_TIMEOUT_MS);
  if (!Number.isInteger(timeoutMs) || timeoutMs < 1_000) throw new Error("--timeout-ms must be an integer >= 1000");
  const chrome = locateChrome(args.chrome);
  const staticServer = await startStaticServer(root);
  let chromeProcess = null;
  let cdp = null;
  const mismatches = [];
  try {
    chromeProcess = await launchChrome(chrome, timeoutMs);
    cdp = new CdpClient(chromeProcess.webSocketDebuggerUrl);
    await cdp.connect();
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");
    const loaded = cdp.waitForEvent("Page.loadEventFired", timeoutMs);
    await cdp.send("Page.navigate", { url: staticServer.url });
    await loaded;
    await waitForReady(cdp, timeoutMs);
    for (const tier of TIERS) {
      const workIds = Object.keys(expected[tier]).sort();
      await clearSelection(cdp, timeoutMs);
      await setTier(cdp, tier, timeoutMs);
      for (const workId of workIds) {
        await clearSelection(cdp, timeoutMs);
        await clickWork(cdp, workId);
        const actual = await stableSnapshot(cdp, workId, timeoutMs);
        const diff = difference(expected[tier][workId], actual);
        if (diff.hasDifference) mismatches.push({ tier, work_id: workId, ...diff });
      }
    }
  } finally {
    cdp?.close();
    await new Promise((resolve) => staticServer.server.close(() => resolve()));
    if (chromeProcess) await stopChrome(chromeProcess);
  }
  const summary = Object.fromEntries(TIERS.map((tier) => {
    const tierMismatches = mismatches.filter((item) => item.tier === tier);
    return [tier, { works: Object.keys(expected[tier]).length, mismatches: tierMismatches.length }];
  }));
  return { summary, mismatches };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    process.stdout.write(`${usage()}\n`);
    return;
  }
  if (!args.expected) throw new Error("--expected is required");
  const expected = normalizeExpected(JSON.parse(fs.readFileSync(path.resolve(args.expected), "utf8")));
  const report = await runAudit(args, expected);
  process.stdout.write(`${JSON.stringify(report)}\n`);
  if (report.mismatches.length) process.exitCode = 1;
}

main().catch((error) => {
  process.stderr.write(`${error.stack || error}\n`);
  process.exitCode = 1;
});
