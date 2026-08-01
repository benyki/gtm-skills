# Fallback method — Claude-in-Chrome browser plugin

Use ONLY when Apify doesn't fit: no usable results, content needs a logged-in
session, region-locked, or the user wants zero API spend.

## Steps

1. **Pick a browser.** `list_connected_browsers` → if more than one, ask the
   user which to use (list each by display name + deviceId). If they want to
   choose in Chrome, call `switch_browser`.
2. **Open a tab.** `tabs_context_mcp` with `createIfEmpty: true`; note the tabId.
3. **Search.** `navigate` to:
   `https://www.tiktok.com/search?q=<url-encoded query>`
   e.g. `favorite%20word%20in%20the%20language%20i%27m%20learning`
4. **Read captions.** `get_page_text` on the tabId — gives captions + author
   handles + messy inline like-counts (no clean per-post metrics).
5. **Extract real URLs** (the text dump has none) via `javascript_tool`:

   ```js
   JSON.stringify(
     [...document.querySelectorAll('a[href*="/video/"]')]
       .map(a => a.href)
       .filter((v,i,s) => s.indexOf(v) === i)
       .slice(0, 30)
   )
   ```

   Map each `/@handle/video/<id>` URL back to its caption (by handle) from the
   page text to build {url, note} pairs.

## Limits vs Apify

- No reliable likes/engagement → can't rank objectively; judge by caption only.
- DOM-dependent and brittle (lazy loading, layout changes, login walls).
- Slower: several tool round-trips vs one Apify call.

Once you have the posts, curate the top 5 and continue with
`scripts/report_to_discord.sh` exactly as in the Apify path.
