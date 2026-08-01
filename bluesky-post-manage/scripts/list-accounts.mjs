#!/usr/bin/env node
// Enumerate all BSKY_ACCOUNT_<NAME>_* accounts in the loaded environment
// and verify that each one logs in successfully. Prints handle, DID, and
// app-password validity.
//
// Usage:
//   node --env-file=~/.agents/.env list-accounts.mjs

import { listConfiguredAccounts, accountEnv, AtpAgent } from './_lib.mjs'

const names = listConfiguredAccounts()
if (!names.length) {
  console.log('no BSKY_ACCOUNT_*_HANDLE env vars found.')
  console.log('see ~/.agents/skills/bluesky-post-manage/references/accounts.md')
  process.exit(0)
}

console.log(`found ${names.length} account(s):`)
for (const name of names) {
  try {
    const env = accountEnv(name)
    const agent = new AtpAgent({ service: env.pdsUrl })
    await agent.login({ identifier: env.handle, password: env.password })
    const did = agent.session?.did ?? env.did ?? '?'
    const handle = agent.session?.handle ?? env.handle
    console.log(`  ✓ ${name.padEnd(12)} ${handle}  did=${did}  pds=${env.pdsUrl}`)
  } catch (err) {
    console.log(`  ✗ ${name.padEnd(12)} ${err.message ?? err}`)
  }
}
