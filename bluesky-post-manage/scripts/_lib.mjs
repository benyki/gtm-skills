// Shared helpers for all bluesky-post-manage scripts.
// Zero external dependencies beyond @atproto/api.
//
// Env loading: scripts assume process.env is already populated (via
// `node --env-file=<path>` or any other dotenv loader the agent prefers).

import { AtpAgent, RichText } from '@atproto/api'

/**
 * Parse argv like `--key value --flag --key2 value2`.
 * Boolean flags become `true`. Repeated keys become arrays.
 *   parseArgs(['--account','MAIN','--image','a.jpg','--image','b.jpg','--mark-seen'])
 *   → { account: 'MAIN', image: ['a.jpg','b.jpg'], 'mark-seen': true }
 */
export function parseArgs(argv) {
  const out = {}
  for (let i = 0; i < argv.length; i++) {
    const tok = argv[i]
    if (!tok.startsWith('--')) continue
    const key = tok.slice(2)
    const next = argv[i + 1]
    if (next === undefined || next.startsWith('--')) {
      out[key] = true
    } else {
      if (out[key] === undefined) out[key] = next
      else if (Array.isArray(out[key])) out[key].push(next)
      else out[key] = [out[key], next]
      i++
    }
  }
  return out
}

/** Read env vars for an account NAME. Throws on missing required vars. */
export function accountEnv(name) {
  const prefix = `BSKY_ACCOUNT_${name.toUpperCase()}_`
  const handle = process.env[prefix + 'HANDLE']
  const password = process.env[prefix + 'APP_PASSWORD']
  const did = process.env[prefix + 'DID']
  const pdsUrl = process.env[prefix + 'PDS_URL'] ?? 'https://bsky.social'
  if (!handle || !password) {
    throw new Error(
      `Missing env vars ${prefix}HANDLE and/or ${prefix}APP_PASSWORD. ` +
      `Add them to ~/.agents/.env and re-run with --env-file.`
    )
  }
  return { name: name.toUpperCase(), handle, password, did, pdsUrl }
}

/** Enumerate every account configured in env (any BSKY_ACCOUNT_*_HANDLE). */
export function listConfiguredAccounts() {
  const names = new Set()
  for (const k of Object.keys(process.env)) {
    const m = k.match(/^BSKY_ACCOUNT_(.+)_HANDLE$/)
    if (m) names.add(m[1])
  }
  return [...names]
}

/** Login and return an AtpAgent for a given account NAME. */
export async function login(name) {
  const env = accountEnv(name)
  const agent = new AtpAgent({ service: env.pdsUrl })
  await agent.login({ identifier: env.handle, password: env.password })
  return { agent, env }
}

/**
 * Build a rich-text post record. Handles facet detection automatically.
 * Returns the record object ready for agent.post(record).
 */
export async function buildPostRecord(agent, { text, replyTo, replyCid, replyRootUri, replyRootCid, quote, quoteCid, lang = 'en' }) {
  const rt = new RichText({ text })
  await rt.detectFacets(agent)
  const record = {
    $type: 'app.bsky.feed.post',
    text: rt.text,
    facets: rt.facets,
    langs: [lang],
    createdAt: new Date().toISOString(),
  }
  if (replyTo) {
    if (!replyCid) throw new Error('--reply-to requires --reply-cid')
    record.reply = {
      root:   { uri: replyRootUri ?? replyTo, cid: replyRootCid ?? replyCid },
      parent: { uri: replyTo, cid: replyCid },
    }
  }
  if (quote) {
    if (!quoteCid) throw new Error('--quote requires --quote-cid')
    record.embed = {
      $type: 'app.bsky.embed.record',
      record: { uri: quote, cid: quoteCid },
    }
  }
  return record
}

/** Print and exit on usage error. */
export function die(msg) {
  console.error(`error: ${msg}`)
  process.exit(1)
}

/** Pretty-print a strong ref (uri+cid). */
export function fmtRef(r) {
  return `${r.uri}\n  cid: ${r.cid}`
}

export { AtpAgent, RichText }
