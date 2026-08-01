#!/usr/bin/env node
// Mark a thread done on one or more PLATFORMS in thread-inputs.json.
// Status is per-platform: status = { x, bluesky, threads }.
//
//   mark-done.mjs <label> --platform bluesky [--url <post-url>]
//   mark-done.mjs <label> --platform x,threads          # comma list, same call
//
// Sets status[platform]="done" and (if --url) posted[platform]=url.

import { readFileSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';

const BACKLOG = join(homedir(), 'code/<project>/world/threads/inputs/thread-inputs.json');
const PLATFORMS = ['x', 'bluesky', 'threads'];

const args = process.argv.slice(2);
const label = args.find((a) => !a.startsWith('--'));
const get = (f) => { const i = args.indexOf(f); return i !== -1 ? args[i + 1] : undefined; };
const platforms = (get('--platform') || '').split(',').map((s) => s.trim()).filter(Boolean);
const url = get('--url');

if (!label || !platforms.length) {
  console.error('usage: mark-done.mjs <label> --platform <x|bluesky|threads[,...]> [--url <post-url>]');
  process.exit(1);
}
for (const p of platforms) if (!PLATFORMS.includes(p)) { console.error(`bad platform: ${p}`); process.exit(1); }

const data = JSON.parse(readFileSync(BACKLOG, 'utf8'));
const entry = data.find((e) => e.label === label);
if (!entry) { console.error(`no entry with label "${label}"`); process.exit(1); }
if (!entry.status || typeof entry.status !== 'object') entry.status = { x: 'todo', bluesky: 'todo', threads: 'todo' };

for (const p of platforms) {
  entry.status[p] = 'done';
  if (url) { entry.posted = { ...(entry.posted || {}), [p]: url }; }
}
writeFileSync(BACKLOG, JSON.stringify(data, null, 2) + '\n');

console.log(`marked done: ${label} on ${platforms.join(', ')}`);
console.log(`  status now: ${PLATFORMS.map((p) => `${p}=${entry.status[p]}`).join('  ')}`);
for (const p of PLATFORMS) {
  const n = data.filter((e) => (e.status?.[p] || 'todo') === 'todo').length;
  process.stderr.write(`  ${p}: ${n} todo\n`);
}
