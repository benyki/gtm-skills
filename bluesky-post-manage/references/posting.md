# Posting

All write operations go to the user's PDS (`https://bsky.social` for default accounts).

## Hard limits

| Item | Limit |
|------|-------|
| Text | 300 graphemes max |
| Images | 4 max per post, 1,000,000 bytes each, 2,000,000 bytes total |
| Video | 100 MB max, 3 minutes max |
| Tags (post `tags` field) | 8 max, 64 graphemes / 640 bytes each |
| Blob upload | 50 MB hard cap |

---

## Plain text post

```typescript
const result = await agent.post({
  text: 'Hello world!',
  langs: ['en'],
  createdAt: new Date().toISOString(),
})
// result.uri  = "at://did:plc:.../app.bsky.feed.post/rkey"
// result.cid  = "bafy..."   ← save both for reply/quote chains
```

---

## Rich text (mentions, links, hashtags)

Facets index into **UTF-8 bytes** (inclusive start, exclusive end).
Never use `string.length` (UTF-16). Always use `RichText` or `TextEncoder`.

### Auto-detect (recommended)
```typescript
import { RichText } from '@atproto/api'

const rt = new RichText({
  text: 'Hello @alice.bsky.social! Check #atproto https://atproto.com',
})
await rt.detectFacets(agent)   // resolves @handles → DIDs

await agent.post({
  text: rt.text,
  facets: rt.facets,
  createdAt: new Date().toISOString(),
})
```

### Manual facets
```typescript
const text = 'Visit our site'
await agent.post({
  text,
  facets: [{
    index: { byteStart: 6, byteEnd: 14 },   // "our site" in UTF-8 bytes
    features: [{ $type: 'app.bsky.richtext.facet#link', uri: 'https://example.com' }],
  }],
  createdAt: new Date().toISOString(),
})
```

### Facet feature types
| Type | `$type` | Extra field |
|------|---------|-------------|
| Link | `app.bsky.richtext.facet#link` | `uri` |
| Mention | `app.bsky.richtext.facet#mention` | `did` |
| Hashtag | `app.bsky.richtext.facet#tag` | `tag` (no `#`) |

Facets **cannot overlap**.

### Extra hashtags (not in text)
```typescript
await agent.post({
  text: 'Hello!',
  tags: ['atproto', 'bluesky'],   // up to 8
  createdAt: new Date().toISOString(),
})
```

---

## Reply (thread)

Both `root` and `parent` are required. They're the same for a direct reply to a root post; they diverge deeper in a thread.

```typescript
await agent.post({
  text: 'Replying here!',
  reply: {
    root:   { uri: threadRootUri, cid: threadRootCid },
    parent: { uri: parentPostUri, cid: parentPostCid },
  },
  createdAt: new Date().toISOString(),
})
```

Threading recipe:
1. Post root → save `uri` + `cid` from response
2. Each subsequent reply: `root` = post 1, `parent` = immediate predecessor

---

## Quote post

```typescript
await agent.post({
  text: 'Look at this:',
  embed: {
    $type: 'app.bsky.embed.record',
    record: { uri: quotedUri, cid: quotedCid },
  },
  createdAt: new Date().toISOString(),
})
```

---

## Images

```typescript
import fs from 'node:fs'

const bytes = fs.readFileSync('./photo.jpg')
const { data } = await agent.uploadBlob(bytes, { encoding: 'image/jpeg' })

await agent.post({
  text: 'My photo',
  embed: {
    $type: 'app.bsky.embed.images',
    images: [{
      image: data.blob,
      alt: 'Descriptive alt text',                     // accessibility, required by convention
      aspectRatio: { width: 1920, height: 1080 },      // optional but recommended
    }],
  },
  createdAt: new Date().toISOString(),
})
```

Supported mime types: `image/jpeg`, `image/png`, `image/gif`, `image/webp`.
Blob refs are short-lived; create the post record promptly after upload.
Endpoint: `POST /xrpc/com.atproto.repo.uploadBlob` with raw bytes and `Content-Type: <mime>`.

---

## Link card (external embed)

You fetch OG tags yourself; the SDK does not.

```typescript
const thumb = fs.readFileSync('./thumb.jpg')
const { data: thumbBlob } = await agent.uploadBlob(thumb, { encoding: 'image/jpeg' })

await agent.post({
  text: 'Check this out',
  embed: {
    $type: 'app.bsky.embed.external',
    external: {
      uri: 'https://example.com/article',
      title: 'Article Title',
      description: 'Short description',
      thumb: thumbBlob.blob,
    },
  },
  createdAt: new Date().toISOString(),
})
```

---

## Video

```typescript
const bytes = fs.readFileSync('./clip.mp4')
const { data } = await agent.uploadBlob(bytes, { encoding: 'video/mp4' })

await agent.post({
  text: '',
  embed: {
    $type: 'app.bsky.embed.video',
    video: data.blob,
    alt: 'Video description',
    aspectRatio: { width: 1920, height: 1080 },
  },
  createdAt: new Date().toISOString(),
})
```
100 MB / 3 minutes hard limit.

---

## Quote + media (combined)

```typescript
embed: {
  $type: 'app.bsky.embed.recordWithMedia',
  record: { $type: 'app.bsky.embed.record', record: { uri, cid } },
  media:  { $type: 'app.bsky.embed.images', images: [...] },
}
```

---

## Deleting

```typescript
await agent.deletePost('at://did:plc:abc/app.bsky.feed.post/rkey')
await agent.deleteLike('at://did:plc:abc/app.bsky.feed.like/rkey')
await agent.deleteRepost('at://did:plc:abc/app.bsky.feed.repost/rkey')
await agent.deleteFollow('at://did:plc:abc/app.bsky.graph.follow/rkey')
```

Raw XRPC (any collection):
```http
POST /xrpc/com.atproto.repo.deleteRecord
Authorization: Bearer <accessJwt>

{ "repo": "did:plc:yourDID", "collection": "app.bsky.feed.post", "rkey": "3k44..." }
```
`rkey` = last path segment of the at:// URI.

---

## Reading

```typescript
await agent.getTimeline({ limit: 50 })                            // home feed
await agent.getAuthorFeed({ actor: 'alice.bsky.social', limit: 20 })
await agent.getPostThread({ uri: 'at://...', depth: 10 })
await agent.getProfile({ actor: 'alice.bsky.social' })

const { data } = await agent.listNotifications({ limit: 20 })
// data.notifications[].reason: 'like'|'repost'|'follow'|'mention'|'reply'|'quote'
await agent.updateSeenNotifications(new Date().toISOString())
```

---

## Firehose

**Canonical relay** (Sync 1.1, JSON commit framing over WS + CBOR payload):
```
wss://bsky.network/xrpc/com.atproto.sync.subscribeRepos
```
Resume with `?cursor=<seq>`. Each `#commit` has `ops[]` with `action`
(`create`|`update`|`delete`), `path` (collection/rkey), and `cid`.

**JetStream** (plain JSON, far simpler, recommended for most use cases):
```
wss://jetstream2.us-east.bsky.network/subscribe
  ?wantedCollections=app.bsky.feed.post
  &wantedDids=did:plc:abc123
```
Other Jetstream hosts: `jetstream1.us-east`, `jetstream1.us-west`, `jetstream2.us-west`.
