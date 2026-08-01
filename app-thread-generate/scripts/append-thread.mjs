#!/usr/bin/env node
// Validate a new thread entry and append it to the thread backlog.
//
// usage:
//   append-thread.mjs --file entry.json        # read entry from a JSON file
//   cat entry.json | append-thread.mjs --stdin # read entry from stdin
//   append-thread.mjs --check --file entry.json # validate only, do not write
//
// Entry shape (see config.md):
//   { label, word, template, daily_users_millions, opener, posts:[...], cta_reply, lang }
// Enforces: required fields, valid template, unique word/label, every post <= 280 chars.

import { readFileSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';

const BACKLOG = join(homedir(), 'code/<project>/world/threads/inputs/thread-inputs.json');
const TEMPLATES = ['default-1', 'default-2', 'surprising', 'weird'];
const MAX = 280;

const args = process.argv.slice(2);
const check = args.includes('--check');
let raw;
if (args.includes('--stdin')) {
  raw = readFileSync(0, 'utf8');
} else {
  const fi = args.indexOf('--file');
  if (fi === -1) { console.error('need --file <path> or --stdin'); process.exit(1); }
  raw = readFileSync(args[fi + 1], 'utf8');
}

let e;
try { e = JSON.parse(raw); } catch (err) { console.error('invalid JSON:', err.message); process.exit(1); }

const errs = [];
for (const f of ['label', 'word', 'template', 'opener', 'cta_reply']) {
  if (!e[f] || typeof e[f] !== 'string') errs.push(`missing/!string: ${f}`);
}
if (!Array.isArray(e.posts) || e.posts.length < 1) errs.push('posts must be a non-empty array');
if (e.template && !TEMPLATES.includes(e.template)) errs.push(`template must be one of ${TEMPLATES.join(', ')}`);
if (typeof e.daily_users_millions !== 'number') errs.push('daily_users_millions must be a number');

// char limits (strip *italic* markers for the count — they may be removed at post time)
const len = (s) => [...s.replace(/\*(.+?)\*/g, '$1')].length;
const allPosts = [e.opener, ...(e.posts || []), e.cta_reply].filter((x) => typeof x === 'string');
allPosts.forEach((p, i) => { if (len(p) > MAX) errs.push(`post ${i + 1} is ${len(p)} > ${MAX} chars`); });

// house style: no em dashes (rewrite with comma/colon/period/parentheses)
allPosts.forEach((p, i) => { if (p.includes('—')) errs.push(`post ${i + 1} contains an em dash (—) — not allowed`); });

// recommended shape: opener + 2-3 body + reply (4-5 total)
const total = allPosts.length;
if (total < 3) errs.push('thread too short (need opener + >=1 body + reply)');
if (e.posts && e.posts.length > 4) errs.push(`too many body posts (${e.posts.length}); aim for 2-3 longer ones`);

const data = JSON.parse(readFileSync(BACKLOG, 'utf8'));
if (data.some((x) => x.label === e.label)) errs.push(`duplicate label already in backlog: ${e.label}`);
if (data.some((x) => x.word?.toLowerCase() === e.word?.toLowerCase())) errs.push(`word already in backlog: ${e.word}`);

if (errs.length) {
  console.error('REJECTED:\n  - ' + errs.join('\n  - '));
  process.exit(1);
}

const entry = {
  label: e.label, word: e.word,
  status: { x: 'todo', bluesky: 'todo', threads: 'todo' },
  template: e.template, daily_users_millions: e.daily_users_millions,
  opener: e.opener, posts: e.posts, cta_reply: e.cta_reply, lang: e.lang || 'en',
};

if (check) {
  console.log(`OK (validated, not written): ${entry.word} — ${total} posts, template ${entry.template}`);
  process.exit(0);
}

data.push(entry);
writeFileSync(BACKLOG, JSON.stringify(data, null, 2) + '\n');
console.log(`appended: ${entry.word} (${entry.template}, ${total} posts)`);
const counts = ['x', 'bluesky', 'threads'].map((p) => `${p}=${data.filter((x) => (x.status?.[p] || 'todo') === 'todo').length}`);
console.log(`backlog now ${data.length} threads; todo: ${counts.join(' ')}`);
