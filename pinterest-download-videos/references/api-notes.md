# Pinterest search API notes

Pinterest's web search is backed by a public JSON endpoint. No auth required.

## Endpoint

```
GET https://www.pinterest.com/resource/BaseSearchResource/get/
```

## Required query params

- `source_url` — the path of the equivalent browser URL, e.g. `/search/videos/?q=running%20in%20the%20nature`
- `data` — JSON string:

```json
{
  "options": {
    "query": "<keyword>",
    "scope": "videos",
    "page_size": 20
  },
  "context": {}
}
```

Scopes: `pins`, `videos`, `users`, `boards`. Use `videos` to filter out image-only pins.

## Required headers

```
user-agent: Mozilla/5.0
x-pinterest-pws-handler: www/search/[scope].js
accept: application/json
```

Missing the `x-pinterest-pws-handler` header usually yields 404.

## Response shape (trimmed)

```json
{
  "resource_response": {
    "data": {
      "results": [
        {
          "id": "576883033529047994",
          "videos": { "video_list": { "V_720P": { "url": "..." } } },
          "images": { "orig": { "url": "..." } },
          "title": "...",
          "description": "..."
        }
      ]
    }
  }
}
```

Even with `scope=videos`, a few results may lack a `videos` field — defensively filter with `r.get("videos")` before collecting the pin ID.

## yt-dlp handling

`yt-dlp` has a first-party Pinterest extractor. Given `https://www.pinterest.com/pin/<id>/`, it:

- Prefers `V_720P` / `V_EXP7` (direct MP4) when available.
- Falls back to `V_HLSV4-*` / `V_HLSV3_MOBILE-*` HLS manifests and merges fragments.
- Auto-merges separate video + audio streams into a single `.mp4`.

Keep the output template short to avoid filesystem path-length issues:

```
-o "pinterest-%(id)s.%(ext)s"
```

## Rate limits

Pinterest doesn't publish official limits for unauthenticated resource calls. Empirically, a few dozen requests per minute are fine. If you start seeing 429 or 5xx, throttle with `sleep 1` between downloads.
