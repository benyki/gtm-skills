#!/usr/bin/env node
// Delete any record on Bluesky (post / like / repost / follow / etc.)
// by its at:// URI. The URI is expected to belong to the supplied --account.
//
// Usage:
//   node --env-file=~/.agents/.env delete-record.mjs \
//     --account MAIN --uri at://did:plc:abc/app.bsky.feed.post/xyz

import { parseArgs, login, die } from './_lib.mjs'

const args = parseArgs(process.argv.slice(2))

if (args.help || !args.account || !args.uri) {
  console.log(`usage: delete-record.mjs --account <NAME> --uri <at-uri>`)
  process.exit(args.help ? 0 : 1)
}

// at://did/collection/rkey
const m = args.uri.match(/^at:\/\/([^/]+)\/([^/]+)\/([^/]+)$/)
if (!m) die(`invalid at:// URI: ${args.uri}`)
const [, repo, collection, rkey] = m

try {
  const { agent } = await login(args.account)
  await agent.com.atproto.repo.deleteRecord({ repo, collection, rkey })
  console.log(`deleted ${args.uri}`)
} catch (err) {
  die(err.message ?? String(err))
}
