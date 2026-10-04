import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawn, execFileSync} from 'node:child_process';
import childProcess from 'node:child_process';
import {syncBuiltinESMExports} from 'node:module';

// Execute the runners' real stopChrome, without their CLI entry point.
const [runner, mode] = process.argv.slice(2);
const source = fs.readFileSync(runner, 'utf8');
const entry = source.lastIndexOf('\nmain(');
if (entry < 0) throw new Error('CLI entry point not found');
const moduleSource = source.slice(0, entry) + `
export { stopChrome, reportInfrastructureError };
export async function probeRetry(error) {
  let calls = 0;
  let launchCalls = 0;
  let auditFailed = false;
  let launchFailed = false;
  // A hypothetical second attempt succeeds: accepting it would hide the leak.
  runAudit = async () => { if (++calls === 1) throw error; return {}; };
  launchChrome = async () => { if (++launchCalls === 1) throw error; return {}; };
  try { await runAuditWithRetries({}); } catch (_) { auditFailed = true; }
  try { await launchChromeWithRetries('fixture', 100); } catch (_) { launchFailed = true; }
  return {calls, launchCalls, auditFailed, launchFailed};
}
`;
const audit = await import('data:text/javascript;base64,' + Buffer.from(moduleSource).toString('base64'));
const root = fs.mkdtempSync(path.join(os.tmpdir(), 'marvel-teardown-fixture-'));
const profile = path.join(root, 'profile');
const heartbeat = path.join(root, 'heartbeat');
const manifest = path.join(root, 'child-pid');
fs.mkdirSync(profile);
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
async function waitFor(check) {
  for (let i = 0; i < 100; i++) { if (check()) return; await sleep(50); }
  throw new Error('fixture readiness timed out');
}
let child;
let grandchildPid;
const originalRm = fs.rmSync;
const originalKill = process.kill;
const originalExec = childProcess.execFileSync;
function running(pid) {
  try {
    process.kill(pid, 0);
    // Linux zombies retain a PID but no executable process or heartbeat.
    if (process.platform === 'linux') {
      const stat = fs.readFileSync(`/proc/${pid}/stat`, 'utf8');
      if (stat.slice(stat.lastIndexOf(')') + 2).startsWith('Z')) return false;
    }
    return true;
  } catch (error) {
    if (error.code === 'ESRCH' || error.code === 'ENOENT') return false;
    throw error;
  }
}
const kill = pid => {
  if (!Number.isInteger(pid) || pid <= 1 || pid === process.pid) throw new Error('unsafe fixture PID');
  try {
    if (process.platform === 'win32') execFileSync('taskkill', ['/PID', String(pid), '/T', '/F'], {stdio:'ignore', timeout:5000, windowsHide:true});
    else process.kill(pid, 'SIGKILL');
  } catch (_) { /* already exited */ }
};
let result;
let failure;
try {
  if (mode === 'profile-error') {
    // A permanent filesystem error cannot be made portable with real locks.
    // Replace only that OS boundary; stopChrome itself remains real.
    fs.rmSync = (target, options) => {
      if (target === profile) throw Object.assign(new Error('fixture profile busy'), {code:'EBUSY'});
      return originalRm(target, options);
    };
    await audit.stopChrome({userDataDir:profile});
    result = {returned:true, retained:fs.existsSync(profile)};
  } else {
    const leaf = `const fs=require('node:fs');setInterval(()=>fs.writeFileSync(${JSON.stringify(heartbeat)},String(Date.now())),30);`;
    const parent = `const fs=require('node:fs');const {spawn}=require('node:child_process');const c=spawn(process.execPath,['-e',${JSON.stringify(leaf)}],{stdio:'ignore'});fs.writeFileSync(${JSON.stringify(manifest)},String(c.pid));${mode === 'parent-exited' ? 'c.unref();setTimeout(()=>process.exit(0),200);' : 'setInterval(()=>{},1000);'}`;
    child = spawn(process.execPath, ['-e', parent], {stdio:'ignore', detached:process.platform !== 'win32', windowsHide:true});
    await waitFor(() => fs.existsSync(heartbeat) && fs.existsSync(manifest));
    grandchildPid = Number(fs.readFileSync(manifest, 'utf8'));
    if (mode === 'parent-exited') await waitFor(() => child.exitCode !== null);
    const liveHeartbeat = fs.readFileSync(heartbeat, 'utf8');
    await sleep(100);
    if (liveHeartbeat === fs.readFileSync(heartbeat, 'utf8')) throw new Error('descendant was not live before teardown');
    const started = Date.now();
    if (mode === 'kill-error' || mode === 'retry-error') {
      // Inject an OS termination failure, not a substitute implementation.
      if (process.platform === 'win32') {
        childProcess.execFileSync = () => { throw new Error('fixture tree kill denied'); };
        syncBuiltinESMExports();
      } else {
        process.kill = () => { throw Object.assign(new Error('fixture tree kill denied'), {code:'EPERM'}); };
      }
    }
    await audit.stopChrome({child, userDataDir:profile});
    await sleep(200);
    const before = fs.readFileSync(heartbeat, 'utf8');
    await sleep(250);
    result = {stopped:before === fs.readFileSync(heartbeat, 'utf8'),
      parentAlive:running(child.pid), descendantAlive:running(grandchildPid),
      profileRemoved:!fs.existsSync(profile), elapsed:Date.now()-started};
  }
} catch (error) {
  failure = error;
} finally {
  fs.rmSync = originalRm;
  process.kill = originalKill;
  childProcess.execFileSync = originalExec;
  syncBuiltinESMExports();
  if (child?.pid) {
    if (process.platform !== 'win32') { try { process.kill(-child.pid, 'SIGKILL'); } catch (_) {} }
    kill(child.pid);
  }
  if (grandchildPid) kill(grandchildPid);
  await sleep(100);
  originalRm(root, {recursive:true, force:true, maxRetries:3, retryDelay:50});
}
if (failure) {
  if (mode === 'retry-error') {
    const probe = await audit.probeRetry(failure);
    process.stdout.write(JSON.stringify(probe)+'\n', () => process.exit(0));
  } else if (mode === 'kill-error') audit.reportInfrastructureError(failure);
  else process.stderr.write(`${failure.message}\n`, () => process.exit(1));
} else {
process.stdout.write(JSON.stringify(result)+'\n', () => process.exit(0));
}
