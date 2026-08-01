# Authentication

## App Passwords (recommended for bots and server-side scripts)

The default path for bots. No OAuth setup. Created in Bluesky:
**Settings → Privacy and Security → App Passwords**.

- Format: `xxxx-xxxx-xxxx-xxxx`
- Cannot delete/migrate the account or create more app passwords
- Set `privileged: true` (UI checkbox) to grant DM access (`chat.bsky.*`)

### Create via API
```http
POST /xrpc/com.atproto.server.createAppPassword
Authorization: Bearer <accessJwt>
Content-Type: application/json

{ "name": "my-bot", "privileged": false }
```

### Login (createSession)
```typescript
import { AtpAgent } from '@atproto/api'

const agent = new AtpAgent({ service: 'https://bsky.social' })
await agent.login({
  identifier: 'you.bsky.social',           // handle or DID
  password: 'xxxx-xxxx-xxxx-xxxx',
})
// agent.session: { accessJwt, refreshJwt, did, handle, email?, emailConfirmed? }
```

### Session lifetime
- `accessJwt` — ~2 hours
- `refreshJwt` — ~60 days, rotated on each use (effectively single-use)

The SDK automatically refreshes `accessJwt` using `refreshJwt` on 401.

### Persist session across restarts
```typescript
import { writeFileSync, readFileSync, existsSync } from 'node:fs'

const STORE = '/tmp/bsky-session.json'
const agent = new AtpAgent({
  service: 'https://bsky.social',
  persistSession: (_evt, sess) => sess && writeFileSync(STORE, JSON.stringify(sess)),
})

if (existsSync(STORE)) {
  await agent.resumeSession(JSON.parse(readFileSync(STORE, 'utf8')))
} else {
  await agent.login({ identifier, password })
}
```

### Manual refresh
```http
POST /xrpc/com.atproto.server.refreshSession
Authorization: Bearer <refreshJwt>
```

### Logout
```http
POST /xrpc/com.atproto.server.deleteSession
Authorization: Bearer <refreshJwt>
```
(`deleteSession` is **POST**, not DELETE.)

### App password management
```typescript
await agent.api.com.atproto.server.listAppPasswords()
await agent.api.com.atproto.server.revokeAppPassword({ name: 'my-bot' })
```

---

## OAuth 2.0 + DPoP (recommended for user-facing apps)

Use when your code handles **other people's** Bluesky accounts. App-password auth is officially deprecated for new user-facing apps.

Required extensions: **DPoP** (ES256 JWT proof of possession), **PAR** (Pushed Authorization Requests), **PKCE-S256**.

**Discovery flow:**
1. `com.atproto.identity.resolveHandle` → DID
2. Fetch DID doc → PDS URL
3. `{pds}/.well-known/oauth-protected-resource` → `authorization_servers[]`
4. `{auth_server}/.well-known/oauth-authorization-server` → endpoints

**Client metadata** (hosted at a public HTTPS URL = your `client_id`):
```json
{
  "application_type": "web",
  "grant_types": ["authorization_code", "refresh_token"],
  "scope": "atproto transition:generic",
  "response_types": ["code"],
  "redirect_uris": ["https://your-app.example.com/callback"],
  "dpop_bound_access_tokens": true
}
```

**Scopes:**
| Scope | Access |
|-------|--------|
| `atproto` | Required for all sessions |
| `transition:generic` | Create/update/delete records, upload blobs |
| `transition:chat.bsky` | DM access (needs `transition:generic`) |
| `transition:email` | Read account email |

**TS packages:**
- `@atproto/oauth-client-node` (server)
- `@atproto/oauth-client-browser` (browser)

```typescript
// Server-side
import { NodeOAuthClient } from '@atproto/oauth-client-node'
import { Agent } from '@atproto/api'

const client = await NodeOAuthClient.fromClientMetadata({
  clientId: 'https://your-app.example.com/client-metadata.json',
  handleResolver: 'https://bsky.social',
})
const session = await client.restore(did)
const agent = new Agent(session)
```

Use the `Agent` class (not `AtpAgent`) for OAuth-based sessions.

---

## Multi-account pattern

Each account = its own `AtpAgent`. Key them by name in a map:

```typescript
import { AtpAgent } from '@atproto/api'

const ACCOUNT_NAMES = ['MAIN', 'BOT', 'BRAND']
const agents = new Map()
for (const name of ACCOUNT_NAMES) {
  const prefix = `BSKY_ACCOUNT_${name}_`
  const agent = new AtpAgent({
    service: process.env[prefix + 'PDS_URL'] ?? 'https://bsky.social',
  })
  await agent.login({
    identifier: process.env[prefix + 'HANDLE'],
    password:   process.env[prefix + 'APP_PASSWORD'],
  })
  agents.set(name, agent)
}
```

The skill's `scripts/_lib.mjs` provides `accountEnv()`, `listConfiguredAccounts()`, and `login()` that implement exactly this pattern. See `accounts.md` for the env naming convention.
