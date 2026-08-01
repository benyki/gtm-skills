# Buffer GraphQL API — Reference

Endpoint: `POST https://api.buffer.com` · Auth: `Authorization: Bearer $BUFFER_API_KEY`
All types below were confirmed by live introspection (2026-06-18). Re-introspect after
any API change — see SKILL.md "Discovering the schema".

## Queries

| Query | Notes |
|---|---|
| `account { id email organizations { id name } }` | current account + orgs |
| `channels(input: { organizationId })` | channels in an org (see fields below) |
| `channel(input: { id })` | single channel |
| `posts(...)` | posts for channels (queue / sent / etc.) |
| `post(input: { id })` | single post — incl. `status`, `error { message }` |
| `dailyPostingLimits(...)` | per-channel posting limits |
| `aggregatedPostMetrics(...)` | analytics |

### Channel fields
`id, name, displayName, service, serviceId, type, isDisconnected, isLocked, isNew,
isQueuePaused, timezone, avatar, descriptor, externalLink, organizationId, scopes,
products, allowedActions, postingGoal, postingSchedule, linkShortening, metadata,
showTrendingTopicSuggestions, hasActiveMemberDevice, createdAt, updatedAt`

> Fields that do **not** exist (common wrong guesses): `serviceType`, `serviceUsername`,
> `locked`. Use `service`, `serviceId`, `isLocked`.

### Post status
`status` flows `sending → sent` (or an error state). `error` is a `PostPublishingError`
object — query `error { message }`.

## Mutations

| Mutation | Returns |
|---|---|
| `createPost(input: CreatePostInput!)` | `PostActionSuccess` \| `MutationError` |
| `editPost(input: ...)` | edit an existing post |
| `deletePost(input: ...)` | remove a post |
| `createIdea(input: ...)` | create a draft idea |

There is **no** media-upload mutation — see the public-URL gotcha.

### Return union
```graphql
... on PostActionSuccess { post { id text dueAt status } }
... on MutationError { message }
```

## CreatePostInput

| Field | Type | Notes |
|---|---|---|
| `channelId` | `ChannelId!` | required |
| `schedulingType` | `SchedulingType!` | `automatic` \| `notification` |
| `mode` | `ShareMode!` | `addToQueue` \| `shareNow` \| `shareNext` \| `customScheduled` |
| `assets` | `[AssetInput!]!` | required; media + links |
| `text` | `String` | caption / post body |
| `dueAt` | `DateTime` | **required** when `mode: customScheduled` (ISO 8601 UTC) |
| `metadata` | `PostInputMetaData` | per-network options |
| `tagIds` | `[TagId!]` | |
| `saveToDraft` | `Boolean` | create as draft |
| `ideaId` / `draftId` | | create from an existing idea/draft |
| `source` / `aiAssisted` | `String` / `Boolean` | |

### Enums
- `SchedulingType`: `automatic` (Buffer publishes directly), `notification` (phone
  reminder; you finish in the app).
- `ShareMode`: `addToQueue`, `shareNow`, `shareNext`, `customScheduled`.

### AssetInput (one of)
`image: ImageAssetInput` · `video: VideoAssetInput` · `document: DocumentAssetInput` ·
`link: LinkAssetInput`

- `VideoAssetInput`: `url!`, `thumbnailUrl`, `metadata { thumbnailOffset, title }`
- `ImageAssetInput`: `url!`, `thumbnailUrl`, `metadata { altText!, animatedThumbnail, userTags, dimensions }`

### PostInputMetaData (per-network)
`instagram, facebook, linkedin, twitter, pinterest, google, youtube, mastodon, threads,
bluesky, tiktok`

- `TikTokPostMetadataInput`: `{ title: String, isAiGenerated: Boolean }`

## Example: create a scheduled video post

```graphql
mutation($input: CreatePostInput!) {
  createPost(input: $input) {
    __typename
    ... on PostActionSuccess { post { id text dueAt status } }
    ... on MutationError { message }
  }
}
```
Variables:
```json
{ "input": {
  "channelId": "<channel id>",
  "schedulingType": "automatic",
  "mode": "customScheduled",
  "dueAt": "2026-06-20T15:00:00Z",
  "text": "caption #hashtags",
  "assets": [ { "video": { "url": "https://.../clip.mp4",
                            "metadata": { "title": "my title" } } } ],
  "metadata": { "tiktok": { "title": "my title" } }
} }
```

## Known account (snapshot)
- Account `you@example.com` · org **Your Organization** `YOUR_BUFFER_ORG_ID`.
- Channels are listed in `buffer-videos/references/accounts.md`.
