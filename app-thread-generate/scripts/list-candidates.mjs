#!/usr/bin/env node
// Print candidate words for new threads that are NOT already in the backlog.
// Seed pool below; extend it freely. Verify etymology before writing (see SKILL.md).

import { readFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';

const BACKLOG = join(homedir(), 'code/<project>/world/threads/inputs/thread-inputs.json');

// well-known, well-attested etymologies (verify each before writing a thread)
const POOL = [
  'trivia', 'panic', 'jovial', 'lunatic', 'berserk', 'goodbye', 'decimate', 'assassin',
  'hazard', 'robot', 'malaria', 'influenza', 'calculate', 'candidate', 'sabotage', 'tragedy',
  'hippopotamus', 'dandelion', 'daisy', 'mortgage', 'galaxy', 'denim', 'magazine', 'sinister',
  'gymnasium', 'cappuccino', 'tuxedo', 'marathon', 'volcano', 'cereal', 'january', 'salary-x',
  'ostracize', 'clinic', 'pupil', 'vaccine', 'manure', 'tantalize', 'narcissist', 'atlas',
];

const data = JSON.parse(readFileSync(BACKLOG, 'utf8'));
const have = new Set(data.map((e) => e.word.toLowerCase()));
const fresh = POOL.filter((w) => !have.has(w.toLowerCase()));

const n = Number(process.argv[2]) || fresh.length;
for (const w of fresh.slice(0, n)) console.log(w);
console.error(`\n${fresh.length} candidates not yet in backlog (${have.size} words already covered)`);
