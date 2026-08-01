---
name: social-video-downloader
description: Download short-form videos from Instagram Reels, TikTok, and Pinterest to ~/videos/{folder} with platform-specific handling and robust file naming.
---

# Social Video Downloader

Download videos from Instagram Reels, TikTok, and Pinterest into structured `~/videos/` subdirectories.

## Usage

**Standard call:**
```
Download this to clips/{destination_folder}: {url}
```

Or with custom naming:
```
Save as clips/{folder}/{name}.mp4: {url}
```

## Platform-Specific Behavior

### Instagram Reels
- **Extractor**: `yt-dlp` — handles `/reel/` and `/reels/` URLs
- **Auth**: No login needed for public reels; CSRF warnings are safe to ignore
- **Output template**: Always use absolute path with fixed rename on download:
  ```
  -o '~/videos/{folder}/{safe_name}.%(ext)s'
  ```
- **Common issue**: Instagram may serve multiple DASH streams (video+audio separate); merger handles this automatically

### TikTok
- **Extractor**: `yt-dlp`
- **Watermark**: By default TikTok videos include a watermark. Add `--remove-banner` if available, otherwise accept it or crop it in post
- **Output template**: Same absolute path pattern as Instagram
- **Common issue**: Some TikToks are region-locked or require a session cookie; public videos usually work fine

### Pinterest
- **Extractor**: `yt-dlp`
- **Format**: Pinterest pins often have video embedded — download best quality available with `-f best`
- **Output template**: Same absolute path pattern

## Robust Download Pattern

```bash
# 1. Ensure destination exists (absolute path, no ~ in mkdir)
mkdir -p ~/videos/{folder}

# 2. Download directly to final location (no cd, no intermediate move)
yt-dlp "{url}" \
  -o '~/videos/{folder}/{safe_name}.%(ext)s' \
  --no-playlist \
  --merge-output-format mp4

# 3. If file lands somewhere unexpected anyway, find it:
find ~ -name "*.mp4" -mmin -5 2>/dev/null
```

## Fallback: Apify scraper

Use when yt-dlp fails for Instagram (e.g. "empty media response"). Requires `APIFY_API_KEY` in `~/.agents/.env`.

**Key fallback:** if the primary `APIFY_API_KEY` fails (auth error, non-2xx, quota exhausted, or no items returned), automatically retry with `APIFY_FALLBACK_API_KEY` from `~/.agents/.env`. The script below tries the keys in order and only fails if *both* are rejected.

**Default actor: `elis/instagram-downloader-api`** — returns a direct download URL only ($0.0021/request). We then download the file ourselves with `curl`. This is ~100–200x cheaper than actors that pipe video through Apify's bandwidth ($0.06/10MB ≈ $0.20–0.40/video).

**Actor quirks (verified Jun 2026):**
- Input `url` **must be an array**: `{"url": ["https://..."]}` — a string gives `HTTP 400: Field input.url must be array`.
- Output is nested: each dataset item has `result: [...]`, an array of `{url, type, thumb}`.
- **`type` is unreliable** — for a reel it returns *both* the cover JPEG and the MP4, **both labeled `type:"video"`**. Don't trust `type`. Instead download each `result[].url` and keep the one whose bytes are actually a video (MP4 magic / `file` says ISO Media), or just pick the largest. The snippet below does this.

```bash
set -a; . ~/.agents/.env; set +a
mkdir -p ~/videos/{folder}

node -e "
const https = require('https');
const { execSync } = require('child_process');
const instagramUrl = 'INSTAGRAM_URL';
const dest = '~/videos/{folder}/{name}.mp4';

// Try primary key first, then fall back to the secondary key.
const TOKENS = [
  ['APIFY_API_KEY', process.env.APIFY_API_KEY || process.env.APIFY_TOKEN],
  ['APIFY_FALLBACK_API_KEY', process.env.APIFY_FALLBACK_API_KEY],
].filter(([, t]) => t);

function attempt(token) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({ url: [instagramUrl] });  // url MUST be an array
    const options = {
      hostname: 'api.apify.com',
      path: '/v2/acts/elis~instagram-downloader-api/run-sync-get-dataset-items?token=' + token + '&timeout=90',
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) }
    };
    const req = https.request(options, res => {
      let data = ''; res.on('data', c => data += c);
      res.on('end', () => {
        // Non-2xx (401/402/403 = bad/exhausted key) -> let caller try next key
        if (res.statusCode < 200 || res.statusCode >= 300) return reject(new Error('HTTP ' + res.statusCode + ': ' + data.slice(0, 200)));
        let items; try { items = JSON.parse(data); } catch (e) { return reject(new Error('Bad JSON: ' + data.slice(0, 200))); }
        const item = items && items[0];
        // Collect candidate URLs: nested result[] first (current schema), then legacy flat keys.
        let urls = [];
        if (Array.isArray(item?.result)) urls = item.result.map(r => r && r.url).filter(Boolean);
        const flat = item?.videoUrl || item?.video_url || item?.downloadUrl || item?.media_url;
        if (flat) urls.push(flat);
        if (!urls.length) return reject(new Error('No candidate URLs. Item keys: ' + Object.keys(item || {})));
        resolve(urls);
      });
    });
    req.on('error', reject);
    req.write(body); req.end();
  });
}

// Download each candidate; keep the one that is actually a video (MP4/ISO Media), else largest.
function pickAndSaveVideo(urls) {
  const tmp = dest + '.cand';
  let best = null, bestSize = 0;
  for (let i = 0; i < urls.length; i++) {
    try {
      execSync('curl -L -s -A Mozilla/5.0 -o ' + JSON.stringify(tmp) + ' ' + JSON.stringify(urls[i]));
      const kind = execSync('file -b ' + JSON.stringify(tmp)).toString();
      const size = require('fs').statSync(tmp).size;
      const isVideo = /ISO Media|MP4|Matroska|WebM/i.test(kind);
      if (isVideo) { require('fs').renameSync(tmp, dest); return true; }      // definitive
      if (size > bestSize) { bestSize = size; best = urls[i]; }               // fallback = largest
    } catch (e) { /* try next */ }
  }
  if (best) { execSync('curl -L -s -A Mozilla/5.0 -o ' + JSON.stringify(dest) + ' ' + JSON.stringify(best)); return true; }
  return false;
}

(async () => {
  if (!TOKENS.length) { console.error('No Apify key set (APIFY_API_KEY / APIFY_FALLBACK_API_KEY)'); process.exit(1); }
  for (const [name, token] of TOKENS) {
    try {
      const urls = await attempt(token);
      console.log('Got ' + urls.length + ' candidate URL(s) via ' + name + ', selecting video...');
      if (pickAndSaveVideo(urls)) { console.log('Done:', dest); return; }
      console.error(name + ': no candidate was a video');
    } catch (e) {
      console.error(name + ' failed: ' + e.message);
    }
  }
  console.error('All Apify keys failed.');
  process.exit(1);
})();
" 2>&1
```

**Avoid** `shouldDownloadMedia: true` or bandwidth-based actors — they route video bytes through Apify and cost $0.20–0.40/video.

## Filename Rules

- **Use `safe_name`** — something descriptive with dashes, not the platform's raw title
- Raw titles often contain brackets `[...]`, spaces, and unicode that break shell commands
- If a name has special characters: quote it or use `--restrict-filenames` to sanitize automatically
- Never rely on post-download rename; write to the right place from the start

## Credit / Attribution Log

After every download, append a credit line to `~/videos/{folder}/CREDITS.md` (create if missing):
```markdown
- [{safe_name}]({url}) — @{handle}, downloaded {date}
```

Use `read` to check existing credits before appending.

## Error Handling

| Problem | Fix |
|---|---|
| `zsh: no matches found` on destination path | Use full absolute path, not `~`, in `-o` template |
| File landed in workspace instead of target folder | `find ~ -name "*.mp4" -mmin -5` then move manually |
| Bracket characters break rename | Quote the source path fully: `"filename [with] brackets.mp4"` |
| Instagram CSRF warning (no csrf token) | Safe to ignore, download still works |
| Instagram "empty media response" | Use Apify fallback above |
| Apify `HTTP 401/402/403` or "monthly usage exceeded" | Primary key is bad/exhausted — the script auto-retries with `APIFY_FALLBACK_API_KEY`. If both fail, both keys are exhausted/invalid |

## What Not To Do

- ❌ `cd ~/videos/animals && yt-dlp URL` — cwd is unreliable in exec context
- ❌ `-o '%(title)s.%(ext)s'` without an absolute prefix — file lands wherever the shell happens to be
- ❌ Downloading then moving as a two-step — write to the right path from the start
