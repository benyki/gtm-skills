#!/usr/bin/env node
// Pick a thread from ~/code/<project>/world/threads/inputs/thread-inputs.json
// Status is now PER-PLATFORM: status = { x, bluesky, threads } each "todo"|"done".
//
//   pick-todo.mjs --platform bluesky        # random entry still todo on bluesky
//   pick-todo.mjs --platform x --label clue # a specific entry (any status)
//   pick-todo.mjs --list-todos              # full status matrix for all entries
//   pick-todo.mjs --list-todos --platform x # just labels still todo on x

import { readFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';

const BACKLOG = join(homedir(), 'code/<project>/world/threads/inputs/thread-inputs.json');
const PLATFORMS = ['x', 'bluesky', 'threads'];

const args = process.argv.slice(2);
let label = null, platform = null, showAll = false;
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--label') label = args[++i];
  else if (args[i] === '--platform') platform = args[++i];
  else if (args[i] === '--list-todos') showAll = true;
  else if (args[i] === '--help' || args[i] === '-h') {
    console.log(`usage: pick-todo.mjs [--platform <x|bluesky|threads>] [--label <name>] [--list-todos]

Default pick uses --platform bluesky (the headless-postable channel).
--list-todos with no --platform prints the full per-platform status matrix.`);
    process.exit(0);
  }
}
if (platform && !PLATFORMS.includes(platform)) {
  console.error(`--platform must be one of ${PLATFORMS.join(', ')}`); process.exit(1);
}

const data = JSON.parse(readFileSync(BACKLOG, 'utf8'));
const st = (e, p) => (e.status && e.status[p]) || 'todo';

if (label) {
  const e = data.find((x) => x.label === label);
  if (!e) { console.error(`no entry with label "${label}"`); process.exit(1); }
  console.log(JSON.stringify(e, null, 2));
  process.exit(0);
}

if (showAll) {
  if (platform) {
    const todos = data.filter((e) => st(e, platform) === 'todo');
    for (const e of todos) console.log(e.label);
    console.error(`\n${todos.length} todo on ${platform} / ${data.length} total`);
  } else {
    console.log(`${'word'.padEnd(12)}${PLATFORMS.map((p) => p.padStart(9)).join('')}`);
    for (const e of data) {
      console.log(`${e.word.padEnd(12)}${PLATFORMS.map((p) => st(e, p).padStart(9)).join('')}`);
    }
  }
  process.exit(0);
}

const p = platform || 'bluesky';
const todos = data.filter((e) => st(e, p) === 'todo');
if (!todos.length) { console.error(`no threads still todo on ${p}`); process.exit(1); }
const pick = todos[Math.floor(Math.random() * todos.length)];
console.error(`(random todo on ${p})`);
console.log(JSON.stringify(pick, null, 2));
