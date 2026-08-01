#!/usr/bin/env node
// Print notifications for an account, optionally marking them as seen.
//
// Usage:
//   node --env-file=~/.agents/.env read-notifications.mjs --account MAIN
//   node --env-file=~/.agents/.env read-notifications.mjs --account MAIN --mark-seen

import { parseArgs, login, die } from './_lib.mjs'

const args = parseArgs(process.argv.slice(2))

if (args.help || !args.account) {
  console.log(`usage: read-notifications.mjs --account <NAME> [--limit <n>] [--mark-seen]`)
  process.exit(args.help ? 0 : 1)
}

const limit = parseInt(args.limit ?? '30', 10)

try {
  const { agent } = await login(args.account)
  const { data } = await agent.listNotifications({ limit })
  for (const n of data.notifications) {
    const mark = n.isRead ? ' ' : '*'
    console.log(`${mark} [${n.reason}] @${n.author.handle}  ${n.uri}`)
    if (n.record?.text) console.log(`    ${n.record.text.replace(/\n/g, ' ')}`)
  }
  if (args['mark-seen']) {
    await agent.updateSeenNotifications(new Date().toISOString())
    console.log('— marked all as seen')
  }
} catch (err) {
  die(err.message ?? String(err))
}
