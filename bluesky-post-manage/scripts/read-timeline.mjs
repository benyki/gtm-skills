#!/usr/bin/env node
// Print the home timeline for an account.
//
// Usage:
//   node --env-file=~/.agents/.env read-timeline.mjs --account MAIN --limit 20

import { parseArgs, login, die } from './_lib.mjs'

const args = parseArgs(process.argv.slice(2))

if (args.help || !args.account) {
  console.log(`usage: read-timeline.mjs --account <NAME> [--limit <n>]`)
  process.exit(args.help ? 0 : 1)
}

const limit = Math.min(parseInt(args.limit ?? '30', 10), 100)

try {
  const { agent } = await login(args.account)
  const { data } = await agent.getTimeline({ limit })
  for (const item of data.feed) {
    const p = item.post
    const handle = p.author.handle
    const text = (p.record?.text ?? '').replace(/\n/g, ' ')
    console.log(`@${handle}  ${p.uri}`)
    console.log(`  ${text}`)
  }
} catch (err) {
  die(err.message ?? String(err))
}
