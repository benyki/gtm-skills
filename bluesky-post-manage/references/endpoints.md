# XRPC Endpoints & Rate Limits

## Routing rules

| Operation | Base URL |
|-----------|----------|
| Authenticated writes | `https://bsky.social` (or user's PDS) |
| Authenticated reads | `https://bsky.social` (proxied to AppView) |
| Public unauthenticated reads | `https://public.api.bsky.app` (CDN-cached) |
| Direct AppView | `https://api.bsky.app` |

---

## Rate limits

### Per-account write points (rolling)

| Op | Cost |
|----|------|
| CREATE | 3 |
| UPDATE | 2 |
| DELETE | 1 |

- 5,000 pts/hour (~1,666 creates/hour)
- 35,000 pts/day

### IP-based global

- 3,000 requests / 5 minutes per IP

### Per-endpoint

| Endpoint | Limit |
|----------|-------|
| `createSession` | 30 / 5 min · 300 / day per account |
| `createAccount` | 100 / 5 min per IP |
| `updateHandle` | 10 / 5 min · 50 / day per account |

HTTP **429** on breach; rate-limit headers in response.

---

## Auth & session

| Endpoint | Method | Notes |
|----------|--------|-------|
| `com.atproto.server.createSession` | POST | Login (handle + app password) |
| `com.atproto.server.refreshSession` | POST | Auth: `Bearer <refreshJwt>` |
| `com.atproto.server.deleteSession` | POST | Auth: `Bearer <refreshJwt>` |
| `com.atproto.server.getSession` | GET | Returns current session info |
| `com.atproto.server.createAppPassword` | POST | `{ name, privileged? }` |
| `com.atproto.server.listAppPasswords` | GET | |
| `com.atproto.server.revokeAppPassword` | POST | `{ name }` |

---

## Repository (writes → PDS)

| Endpoint | Method | Notes |
|----------|--------|-------|
| `com.atproto.repo.createRecord` | POST | Create any record |
| `com.atproto.repo.putRecord` | POST | Upsert |
| `com.atproto.repo.deleteRecord` | POST | Delete by `{repo, collection, rkey}` |
| `com.atproto.repo.uploadBlob` | POST | Raw bytes; `Content-Type: <mime>`; 50 MB cap |
| `com.atproto.repo.listRecords` | GET | Paginate a collection |
| `com.atproto.repo.getRecord` | GET | Single record |
| `com.atproto.repo.describeRepo` | GET | Repo info |
| `com.atproto.repo.applyWrites` | POST | Batch create/update/delete |

`createRecord` body:
```json
{
  "repo": "did:plc:yourDID",
  "collection": "app.bsky.feed.post",
  "record": {
    "$type": "app.bsky.feed.post",
    "text": "Hello!",
    "createdAt": "2026-01-01T00:00:00.000Z"
  }
}
```

---

## Identity

| Endpoint | Notes |
|----------|-------|
| `com.atproto.identity.resolveHandle` | `?handle=alice.bsky.social` → `{ did }` |
| `com.atproto.identity.updateHandle` | Change handle |

---

## Bluesky AppView (`app.bsky.*`)

Proxied through PDS, or called directly on `https://public.api.bsky.app` (no auth, public data only).

### Feed
| Endpoint | SDK |
|----------|-----|
| `app.bsky.feed.getTimeline` | `agent.getTimeline()` |
| `app.bsky.feed.getAuthorFeed` | `agent.getAuthorFeed()` |
| `app.bsky.feed.getPostThread` | `agent.getPostThread()` |
| `app.bsky.feed.getLikes` | `agent.getLikes()` |
| `app.bsky.feed.getRepostedBy` | `agent.getRepostedBy()` |
| `app.bsky.feed.getFeed` | `agent.getFeed()` (custom feed generators) |
| `app.bsky.feed.searchPosts` | `agent.app.bsky.feed.searchPosts()` |

### Actor
| Endpoint | SDK |
|----------|-----|
| `app.bsky.actor.getProfile` | `agent.getProfile()` |
| `app.bsky.actor.getProfiles` | `agent.getProfiles()` |
| `app.bsky.actor.searchActors` | `agent.searchActors()` |
| `app.bsky.actor.getSuggestions` | `agent.getSuggestions()` |

### Graph
| Endpoint | SDK |
|----------|-----|
| `app.bsky.graph.getFollows` | `agent.getFollows()` |
| `app.bsky.graph.getFollowers` | `agent.getFollowers()` |
| `app.bsky.graph.getBlocks` | `agent.getBlocks()` |
| `app.bsky.graph.getMutes` | `agent.getMutes()` |

### Notifications
| Endpoint | SDK |
|----------|-----|
| `app.bsky.notification.listNotifications` | `agent.listNotifications()` |
| `app.bsky.notification.updateSeen` | `agent.updateSeenNotifications(seenAtISO)` — body requires `seenAt` |
| `app.bsky.notification.getUnreadCount` | `agent.countUnreadNotifications()` |

---

## Sync / Firehose

| Endpoint | Notes |
|----------|-------|
| `com.atproto.sync.subscribeRepos` | WS firehose. Canonical: `wss://bsky.network/xrpc/com.atproto.sync.subscribeRepos`. Resume via `?cursor=<seq>`. |
| `com.atproto.sync.getRepo` | Full repo as CAR file |
| `com.atproto.sync.listReposByCollection` | Backfill by collection (Sync 1.1) |

JetStream (JSON, simpler):
```
wss://jetstream2.us-east.bsky.network/subscribe
  ?wantedCollections=app.bsky.feed.post
  &wantedDids=did:plc:abc123
```
Also: `jetstream1.us-east`, `jetstream1.us-west`, `jetstream2.us-west`.

---

## Record collections (common)

| Collection | Purpose |
|------------|---------|
| `app.bsky.feed.post` | Post |
| `app.bsky.feed.like` | Like |
| `app.bsky.feed.repost` | Repost |
| `app.bsky.feed.generator` | Custom feed generator record |
| `app.bsky.graph.follow` | Follow |
| `app.bsky.graph.block` | Block |
| `app.bsky.graph.mute` | Mute |
| `app.bsky.graph.list` | List |
| `app.bsky.actor.profile` | Profile (one per repo, rkey = `self`) |
| `app.bsky.labeler.service` | Labeler service record |
| `chat.bsky.convo.*` | DMs (privileged app password required) |
