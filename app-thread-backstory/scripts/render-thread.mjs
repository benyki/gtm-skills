#!/usr/bin/env node
// Render a thread entry into ordered posts for review / posting.
//
// usage: render-thread.mjs <label> [--json] [--strip-md] [--max <n>]
//   <label>      required. The entry's label.
//   --json       emit a JSON array of post strings (post 1 = opener ... last = cta_reply)
//                instead of the human-readable numbered preview.
//   --strip-md   remove *italic* asterisks (post platforms don't render markdown).
//   --max <n>    per-post character limit to validate against (default 280 = X limit).

import { readFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';

const BACKLOG = join(homedir(), 'code/<project>/world/threads/inputs/thread-inputs.json');

const args = process.argv.slice(2);
const label = args.find((a) => !a.startsWith('--'));
const asJson = args.includes('--json');
const stripMd = args.includes('--strip-md');
const maxIdx = args.indexOf('--max');
const max = maxIdx !== -1 ? Number(args[maxIdx + 1]) : 280;

if (!label || args.includes('--help') || args.includes('-h')) {
  console.log('usage: render-thread.mjs <label> [--json] [--strip-md] [--max <n>]');
  process.exit(label ? 0 : 1);
}

const data = JSON.parse(readFileSync(BACKLOG, 'utf8'));
const e = data.find((x) => x.label === label);
if (!e) {
  console.error(`no entry with label "${label}"`);
  process.exit(1);
}

const clean = (s) => (stripMd ? s.replace(/\*(.+?)\*/g, '$1') : s);
const posts = [e.opener, ...e.posts, e.cta_reply].map(clean);

if (asJson) {
  console.log(JSON.stringify(posts, null, 2));
  process.exit(0);
}

const statusStr = e.status && typeof e.status === 'object'
  ? ['x', 'bluesky', 'threads'].map((p) => `${p}=${e.status[p] || 'todo'}`).join(' ')
  : e.status;
console.log(`# ${e.word}  (label: ${e.label}, template: ${e.template})  [${statusStr}]\n`);
let over = 0;
posts.forEach((p, i) => {
  const n = i + 1;
  const tag = i === 0 ? 'OPENER' : i === posts.length - 1 ? 'REPLY ' : `POST ${n} `;
  const len = [...p].length;
  const flag = len > max ? `  ⚠️ ${len}/${max} OVER` : `  (${len}/${max})`;
  if (len > max) over++;
  console.log(`── ${tag} ${flag}`);
  console.log(p);
  console.log('');
});
console.error(over ? `⚠️  ${over} post(s) over ${max} chars — trim before posting.` : `✓ all ${posts.length} posts within ${max} chars`);
