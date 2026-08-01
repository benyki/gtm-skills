#!/usr/bin/env node
// Post text to Bluesky (with optional reply or quote).
//
// Usage:
//   node --env-file=~/.agents/.env post.mjs \
//     --account MAIN --text "Hello world"
//
//   # Reply:
//   node ... post.mjs --account MAIN --text "thanks!" \
//     --reply-to at://did:plc:abc/app.bsky.feed.post/xyz --reply-cid bafy...
//
//   # Quote:
//   node ... post.mjs --account MAIN --text "look" \
//     --quote at://did:plc:abc/app.bsky.feed.post/xyz --quote-cid bafy...

import { parseArgs, login, buildPostRecord, die, fmtRef } from './_lib.mjs'

const args = parseArgs(process.argv.slice(2))

if (args.help || !args.account || !args.text) {
  console.log(`usage: post.mjs --account <NAME> --text "<post text>"
              [--reply-to <at-uri> --reply-cid <cid>]
              [--reply-root-uri <at-uri> --reply-root-cid <cid>]
              [--quote <at-uri> --quote-cid <cid>]
              [--lang <code>]`)
  process.exit(args.help ? 0 : 1)
}

try {
  const { agent } = await login(args.account)
  const record = await buildPostRecord(agent, {
    text: args.text,
    replyTo: args['reply-to'],
    replyCid: args['reply-cid'],
    replyRootUri: args['reply-root-uri'],
    replyRootCid: args['reply-root-cid'],
    quote: args.quote,
    quoteCid: args['quote-cid'],
    lang: args.lang,
  })
  const result = await agent.post(record)
  console.log('posted:')
  console.log(fmtRef(result))
} catch (err) {
  die(err.message ?? String(err))
}
