#!/usr/bin/env python3
"""
upload-post — post videos to TikTok (and other platforms) via the Upload-Post API.

Docs: https://docs.upload-post.com/

Auth: reads UPLOADPOST_API_KEY from the environment. Source the env file first
(absolute path), never read it directly:

    set -a; . ~/.agents/.env; set +a

Subcommands:
    profiles                       list the connected Upload-Post profiles (accounts)
    post --file <v> --user <name>  upload/publish a video
    status --request-id <id>       check an async upload's status

Examples:
    python3 upload_post.py profiles
    python3 upload_post.py post --file clip.mp4 --user account_one \
        --caption "POV: ... #fyp" --when now --wait
    python3 upload_post.py post --file clip.mp4 --user account_two \
        --when 2026-06-21T15:00:00 --timezone Europe/Paris
"""
import argparse
import json
import mimetypes
import os
import sys
import time
import uuid
import urllib.request
import urllib.error
import urllib.parse

BASE = os.environ.get("UPLOADPOST_BASE", "https://api.upload-post.com")
UPLOAD_URL = f"{BASE}/api/upload"
USERS_URL = f"{BASE}/api/uploadposts/users"
STATUS_URL = f"{BASE}/api/uploadposts/status"

RETRIES = 4
RETRY_SLEEP = 3  # seconds, backs off linearly

# Canonical platform keys used in the posts ledger and platform-status.json.
# Upload-Post's API calls X "twitter" — we accept/record "x" and translate on
# the wire (_wire_platform).
ALL_PLATFORMS = ["tiktok", "youtube", "instagram", "x", "bluesky", "facebook", "threads"]
_PLATFORM_IN = {"twitter": "x"}       # incoming/API name → canonical
_PLATFORM_OUT = {"x": "twitter"}      # canonical → what the API expects
PLATFORM_STATUS_FILE = "platform-status.json"


def _canon_platform(p):
    p = (p or "").strip().lower()
    return _PLATFORM_IN.get(p, p)


def _wire_platform(p):
    return _PLATFORM_OUT.get(_canon_platform(p), _canon_platform(p))


def die(msg, code=1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def api_key():
    k = os.environ.get("UPLOADPOST_API_KEY")
    if not k:
        die(
            "UPLOADPOST_API_KEY not set. Source the env first:\n"
            "    set -a; . ~/.agents/.env; set +a"
        )
    return k


def auth_header():
    return {"Authorization": f"Apikey {api_key()}"}


def _request(req, parse_json=True):
    """Send a urllib request with retries on 5xx / network errors."""
    last = None
    for attempt in range(1, RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                raw = resp.read().decode("utf-8", "replace")
                if not parse_json:
                    return resp.status, raw
                try:
                    return resp.status, json.loads(raw) if raw else {}
                except json.JSONDecodeError:
                    return resp.status, {"_raw": raw}
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            if e.code >= 500 and attempt < RETRIES:
                last = f"HTTP {e.code}: {body}"
                time.sleep(RETRY_SLEEP * attempt)
                continue
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = {"_raw": body}
            return e.code, parsed
        except (urllib.error.URLError, TimeoutError) as e:
            last = str(e)
            if attempt < RETRIES:
                time.sleep(RETRY_SLEEP * attempt)
                continue
            die(f"network error after {RETRIES} attempts: {last}")
    die(f"request failed: {last}")


def _get(url, params=None):
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=auth_header(), method="GET")
    return _request(req)


def _multipart(fields, file_field=None):
    """Build a multipart/form-data body. `fields` is a list of (name, value)
    tuples (value may repeat the same name). `file_field` is (name, path)."""
    boundary = "----uploadpost" + uuid.uuid4().hex
    crlf = b"\r\n"
    body = bytearray()
    for name, value in fields:
        body += b"--" + boundary.encode() + crlf
        body += f'Content-Disposition: form-data; name="{name}"'.encode() + crlf + crlf
        body += str(value).encode("utf-8") + crlf
    if file_field:
        name, path = file_field
        fname = os.path.basename(path)
        ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
        with open(path, "rb") as f:
            data = f.read()
        body += b"--" + boundary.encode() + crlf
        body += (
            f'Content-Disposition: form-data; name="{name}"; filename="{fname}"'.encode()
            + crlf
        )
        body += f"Content-Type: {ctype}".encode() + crlf + crlf
        body += data + crlf
    body += b"--" + boundary.encode() + b"--" + crlf
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    headers.update(auth_header())
    return bytes(body), headers


# ---------------------------------------------------------------- commands


def cmd_profiles(args):
    status, data = _get(USERS_URL)
    if status >= 400:
        die(f"HTTP {status}: {json.dumps(data)}")
    # Response shape may vary; try to surface a clean list.
    profiles = data
    if isinstance(data, dict):
        for key in ("profiles", "users", "data", "results"):
            if key in data:
                profiles = data[key]
                break
    if args.json:
        print(json.dumps(profiles, indent=2))
        return
    if not profiles:
        print("No profiles connected yet.")
        print("Add one in the Upload-Post dashboard, then connect its TikTok account.")
        return
    print("Connected profiles:")
    for p in profiles if isinstance(profiles, list) else [profiles]:
        if isinstance(p, dict):
            name = p.get("username") or p.get("user") or p.get("name") or "?"
            socials = p.get("social_accounts") or p.get("platforms") or p.get("accounts")
            extra = f"  [{socials}]" if socials else ""
            print(f"  - {name}{extra}")
        else:
            print(f"  - {p}")


def cmd_post(args):
    if not os.path.isfile(args.file):
        die(f"file not found: {args.file}")

    request_id = args.request_id or ("up_" + uuid.uuid4().hex[:16])
    args.platform = [_canon_platform(p) for p in args.platform]
    fields = [
        ("user", args.user),
        ("request_id", request_id),
    ]
    for plat in args.platform:
        fields.append(("platform[]", _wire_platform(plat)))
    if args.caption:
        fields.append(("title", args.caption))
    if args.description:
        fields.append(("description", args.description))
    if args.first_comment:
        fields.append(("first_comment", args.first_comment))

    # Per-platform metadata (only sent when that platform is targeted; every
    # platform falls back to `title` = --caption when its own title is unset).
    plats = args.platform
    if "youtube" in plats:
        if args.youtube_title:
            fields.append(("youtube_title", args.youtube_title))
        fields.append(("privacyStatus", args.youtube_privacy))
        for t in args.youtube_tags or []:
            fields.append(("tags[]", t))
    if "instagram" in plats:
        if args.ig_title:
            fields.append(("instagram_title", args.ig_title))
        fields.append(("media_type", args.ig_media_type))
    if "x" in plats:
        if args.x_title:
            fields.append(("x_title", args.x_title))
        if args.x_long_text:
            fields.append(("x_long_text_as_post", "true"))
    if "threads" in plats:
        if args.threads_title:
            fields.append(("threads_title", args.threads_title))
        if args.threads_topic:
            fields.append(("threads_topic_tag", args.threads_topic))
    if "facebook" in plats:
        page_id = args.facebook_page_id or os.environ.get("FACEBOOK_PAGE_ID")
        if not page_id:
            die("posting to facebook requires --facebook-page-id (or $FACEBOOK_PAGE_ID)")
        fields.append(("facebook_page_id", page_id))
        if args.facebook_title:
            fields.append(("facebook_title", args.facebook_title))
        fields.append(("facebook_media_type", args.facebook_media_type))
    if "bluesky" in plats:
        if args.bluesky_title:
            fields.append(("bluesky_title", args.bluesky_title))

    # Scheduling
    scheduled = None
    if args.when and args.when.lower() not in ("now", "publish"):
        scheduled = args.when
        fields.append(("scheduled_date", scheduled))
        fields.append(("timezone", args.timezone))

    # Async: force it for scheduled posts and large files; otherwise honor flag.
    use_async = args.async_upload or scheduled is not None
    fields.append(("async_upload", "true" if use_async else "false"))

    # TikTok-specific options (only meaningful when tiktok is a target).
    # Field names are the un-prefixed ones the Upload-Post API actually accepts
    # (privacy_level / disable_* / post_mode / is_aigc), per the live OpenAPI spec —
    # NOT the tiktok_-prefixed names; those are silently ignored.
    if "tiktok" in [p.lower() for p in args.platform]:
        post_mode = "MEDIA_UPLOAD" if args.inbox else args.post_mode
        fields.append(("post_mode", post_mode))
        if post_mode == "DIRECT_POST":
            # TikTok's Direct Post REQUIRES a privacy level; if it's missing the
            # API falls back to inbox/draft delivery (the "Video sent to Inbox"
            # behavior). MEDIA_UPLOAD ignores all metadata (TikTok sets it in-app).
            fields.append(("privacy_level", args.privacy))
            if args.disable_comment:
                fields.append(("disable_comment", "true"))
            if args.disable_duet:
                fields.append(("disable_duet", "true"))
            if args.disable_stitch:
                fields.append(("disable_stitch", "true"))
        if args.aigc:
            # Disclose AI-generated content (TikTok policy). Only honored in DIRECT_POST.
            fields.append(("is_aigc", "true"))

    body, headers = _multipart(fields, file_field=("video", args.file))
    req = urllib.request.Request(UPLOAD_URL, data=body, headers=headers, method="POST")
    print(
        f"posting {os.path.basename(args.file)} → user='{args.user}' "
        f"platforms={args.platform}"
        + (f" scheduled={scheduled} ({args.timezone})" if scheduled else " (now)")
        + (" [async]" if use_async else "")
    )
    status, data = _request(req)

    ok = status in (200, 201, 202) and not (
        isinstance(data, dict) and data.get("success") is False
    )
    print(json.dumps(data, indent=2))
    if not ok:
        die(f"upload failed (HTTP {status})")

    # Resolve request_id the server actually used (fallback to ours).
    rid = request_id
    if isinstance(data, dict):
        rid = data.get("request_id") or data.get("requestId") or rid

    archived = False
    if not args.no_archive and scheduled is None:
        archived = _archive(args.file, args.published_dir)

    final = None
    if args.wait and use_async:
        final = _poll_status(rid, args.timeout)

    inboxed = bool(final and _detect_inbox(final))
    if inboxed:
        print(
            "\n⚠️  DELIVERED TO TIKTOK INBOX, NOT THE PUBLIC FEED.\n"
            "    DIRECT_POST fell back to inbox/drafts — this happens when Upload-Post's\n"
            "    TikTok app has hit its shared daily active-user cap (resets ~every 24h).\n"
            "    Finish publishing in the TikTok app, or retry the direct post later.",
            file=sys.stderr,
        )

    print(
        f"done. request_id={rid}"
        + ("  delivery=INBOX" if inboxed else "")
        + (f"  archived → {archived}" if archived else "")
    )

    # Record per-platform statuses in the published folder's platform-status.json
    # so the next run (and viralwatch) knows exactly where this clip is live.
    if archived:
        updates = _platform_updates(args.platform, args.user, rid, final, inboxed)
        wrote = _update_platform_status(archived, updates)
        if wrote:
            pending = [p for p, e in updates.items() if e.get("status") == "pending"]
            if pending:
                print(
                    f"platform-status: {', '.join(pending)} recorded as PENDING — confirm with\n"
                    f"    upload_post.py status --request-id {rid} --wait --file '{archived}'",
                )

    # Best-effort telemetry — never affects the post (see _log_post_ledger).
    _log_post_ledger({
        "posted_at": _iso_now(),
        "pipeline": "upload-post",
        "skill": "upload-post",
        "account": args.user,
        "platforms": args.platform,
        "status": "scheduled" if scheduled else ("inbox" if inboxed else "feed"),
        "delivery": "inbox" if inboxed else ("scheduled" if scheduled else "feed"),
        "scheduled_for": scheduled,
        "request_id": rid,
        "post_id": _result_field(final, "platform_post_id") if final else None,
        "post_url": _result_field(final, "post_url") if final else None,
        "post_urls": _post_urls(args.platform, final) if final else None,
        "caption": args.caption,
        "aigc": True if args.aigc else None,
        "file_src": os.path.abspath(args.file) if not archived else None,
        "file_archived": archived or None,
        "tag": args.tag or os.environ.get("POST_SOURCE"),
    })


def cmd_status(args):
    rid = args.request_id
    if args.wait:
        data = _poll_status(rid, args.timeout)
    else:
        status, data = _get(STATUS_URL, {"request_id": rid})
        if status >= 400:
            die(f"HTTP {status}: {json.dumps(data)}")
        print(json.dumps(data, indent=2))
    # --file: confirm the outcome into the clip's platform-status.json (the
    # "second step" of the posting workflow — see the upload-post skill).
    if args.file and data:
        if not os.path.isfile(args.file):
            die(f"--file not found: {args.file}")
        inboxed = _detect_inbox(data)
        byplat = _results_by_platform(data)
        updates = {}
        for p, r in byplat.items():
            if p not in ALL_PLATFORMS:
                continue
            e = {"source": "upload-post", "request_id": rid, "posted_at": _iso_now()}
            url = _platform_url(p, r)
            if p == "tiktok" and inboxed:
                e.update(status="inbox", confirmed=False)
            elif url:
                e.update(status="posted", confirmed=True, url=url)
            else:
                e.update(status="posted", confirmed=True)
            pid = r.get("platform_post_id") or r.get("post_id") or r.get("video_id")
            if pid:
                e["post_id"] = str(pid)
            updates[p] = e
        if updates:
            wrote = _update_platform_status(args.file, updates)
            if wrote:
                marks = ", ".join(f"{p}={e['status']}" for p, e in updates.items())
                print(f"platform-status confirmed ({marks}) → {wrote}")
        else:
            print("warning: no per-platform results in the response; nothing confirmed",
                  file=sys.stderr)


def _poll_status(rid, timeout):
    print(f"polling status for {rid} (timeout {timeout}s) ...")
    deadline = time.time() + timeout
    terminal = {"success", "completed", "done", "sent", "published", "failed", "error"}
    while time.time() < deadline:
        status, data = _get(STATUS_URL, {"request_id": rid})
        state = ""
        if isinstance(data, dict):
            state = str(
                data.get("status") or data.get("state") or data.get("result") or ""
            ).lower()
        print(f"  status={state or '(unknown)'}")
        if state in terminal:
            print(json.dumps(data, indent=2))
            if state in ("failed", "error"):
                die("upload reported failure")
            return data
        time.sleep(5)
    print("warning: timed out waiting for terminal status (the post may still complete)")
    return None


def _detect_inbox(data):
    """True if TikTok delivered to the inbox/drafts instead of the public feed.
    Happens when Upload-Post's TikTok app has hit its shared daily active-user cap:
    DIRECT_POST then silently falls back to MEDIA_UPLOAD (inbox)."""
    results = data.get("results") if isinstance(data, dict) else None
    for r in results if isinstance(results, list) else []:
        if not isinstance(r, dict):
            continue
        pid = str(r.get("platform_post_id") or "")
        purl = str(r.get("post_url") or "")
        if pid.startswith("v_inbox") or "inbox" in purl.lower():
            return True
    return False


def _iso_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _result_field(data, key):
    """Pull the first non-empty `key` from a status response's results list."""
    results = data.get("results") if isinstance(data, dict) else None
    for r in results if isinstance(results, list) else []:
        if isinstance(r, dict) and r.get(key):
            return r.get(key)
    return None


def _http_url(u):
    u = str(u or "").strip()
    return u if u.lower().startswith(("http://", "https://")) else None


def _platform_url(p, r):
    """The live post URL from a result row; YouTube only returns a video_id,
    so derive the canonical watch URL from it."""
    url = _http_url((r or {}).get("post_url") or (r or {}).get("url"))
    if not url and p == "youtube":
        vid = (r or {}).get("video_id") or (r or {}).get("platform_post_id")
        if vid:
            url = f"https://www.youtube.com/watch?v={vid}"
    return url


def _results_by_platform(data):
    """Map canonical platform → its result object from an upload/status response.
    Tolerates both a dict keyed by platform and a list of {platform, ...} rows."""
    out = {}
    results = data.get("results") if isinstance(data, dict) else None
    if isinstance(results, dict):
        for k, v in results.items():
            if isinstance(v, dict):
                out[_canon_platform(k)] = v
    elif isinstance(results, list):
        for r in results:
            if isinstance(r, dict):
                out[_canon_platform(r.get("platform") or r.get("name") or "")] = r
    return out


def _post_urls(platforms, final):
    """Per-platform live URLs from a terminal status response, or None."""
    byplat = _results_by_platform(final)
    urls = {}
    for p, r in byplat.items():
        url = _platform_url(p, r)
        if url and (p in ALL_PLATFORMS):
            urls[p] = url
    # Single-platform post whose result row didn't name the platform.
    if not urls and len(platforms) == 1 and byplat:
        url = _http_url(next(iter(byplat.values())).get("post_url"))
        if url:
            urls[platforms[0]] = url
    return urls or None


def _platform_updates(platforms, user, rid, final, inboxed):
    """Build the platform-status entries for a just-posted clip."""
    byplat = _results_by_platform(final) if final else {}
    updates = {}
    for p in platforms:
        if p not in ALL_PLATFORMS:
            continue
        r = byplat.get(p)
        if r is None and len(platforms) == 1 and byplat:
            r = next(iter(byplat.values()))  # unnamed single-platform result row
        url = _platform_url(p, r)
        e = {"source": "upload-post", "account": user,
             "request_id": rid, "posted_at": _iso_now()}
        if p == "tiktok" and inboxed:
            e.update(status="inbox", confirmed=False)
        elif url:
            e.update(status="posted", confirmed=True, url=url)
        elif final is not None:
            e.update(status="posted", confirmed=True)  # terminal success, no URL surfaced
        else:
            e.update(status="pending", confirmed=False)  # accepted; confirm via `status --file`
        pid = (r or {}).get("platform_post_id") or (r or {}).get("post_id") or (r or {}).get("video_id")
        if pid:
            e["post_id"] = str(pid)
        updates[p] = e
    return updates


def _update_platform_status(mp4_path, updates):
    """Best-effort merge of per-platform entries into the sibling
    platform-status.json (the cross-platform publish record viralwatch reads —
    see the viralwatch-friendly skill). Never affects the post itself."""
    if not updates:
        return None
    try:
        mp4_path = os.path.abspath(mp4_path)
        path = os.path.join(os.path.dirname(mp4_path), PLATFORM_STATUS_FILE)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data.get("files"), dict):
                raise ValueError("bad shape")
        except Exception:
            data = {"version": 1, "files": {}}
        entry = data["files"].setdefault(
            os.path.basename(mp4_path),
            {"platforms": {p: {"status": "not_posted"} for p in ALL_PLATFORMS}},
        )
        entry.setdefault("platforms", {}).update(updates)
        data["version"] = 1
        data["updated_at"] = _iso_now()
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, path)
        return path
    except Exception as e:
        print(f"warning: could not update {PLATFORM_STATUS_FILE}: {e}", file=sys.stderr)
        return None


def _log_post_ledger(record):
    """Best-effort append of one JSON line to the shared posts ledger.

    Purely additive telemetry — wrapped so a logging failure can NEVER affect a
    post. Location overridable via $POSTS_LEDGER (default ~/.agents/runs/posts.jsonl).
    """
    try:
        path = os.path.expanduser(
            os.environ.get("POSTS_LEDGER", "~/.agents/runs/posts.jsonl")
        )
        os.makedirs(os.path.dirname(path), exist_ok=True)
        rec = {k: v for k, v in record.items() if v is not None}
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _archive(path, published_dir):
    """Move a successfully-posted local file into a sibling published/ folder so
    the same clip isn't posted twice. Returns the new path or None."""
    src = os.path.abspath(path)
    dst_dir = os.path.join(os.path.dirname(src), published_dir)
    os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, os.path.basename(src))
    try:
        os.replace(src, dst)
    except OSError as e:
        print(f"warning: could not archive source: {e}", file=sys.stderr)
        return None
    # Carry the inputs sidecar (<stem>.json) alongside the clip so downstream
    # viewers find it next to the published mp4 (one lookup rule). Best-effort:
    # a missing or unmovable sidecar never fails the archive.
    sidecar = os.path.splitext(src)[0] + ".json"
    if os.path.exists(sidecar):
        try:
            os.replace(sidecar, os.path.join(dst_dir, os.path.basename(sidecar)))
        except OSError as e:
            print(f"warning: could not archive sidecar: {e}", file=sys.stderr)
    return dst


# ---------------------------------------------------------------- cli


def build_parser():
    p = argparse.ArgumentParser(description="Post videos via the Upload-Post API.")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("profiles", help="list connected Upload-Post profiles")
    sp.add_argument("--json", action="store_true", help="raw JSON output")
    sp.set_defaults(func=cmd_profiles)

    po = sub.add_parser("post", help="upload/publish a video")
    po.add_argument("--file", required=True, help="local video file")
    po.add_argument("--user", required=True, help="Upload-Post profile username")
    po.add_argument(
        "--platform",
        action="append",
        default=None,
        help="target platform (repeatable). default: tiktok",
    )
    po.add_argument("--caption", help="post caption / title (hashtags go here)")
    po.add_argument("--description", help="extended description")
    po.add_argument("--first-comment", dest="first_comment", help="auto first comment")
    po.add_argument(
        "--when",
        default="now",
        help="'now' (default) or an ISO-8601 datetime to schedule, e.g. 2026-06-21T15:00:00",
    )
    po.add_argument(
        "--timezone",
        default=os.environ.get("TZ", "UTC"),
        help="IANA timezone for --when (default $TZ or UTC)",
    )
    po.add_argument(
        "--post-mode",
        dest="post_mode",
        choices=["DIRECT_POST", "MEDIA_UPLOAD"],
        default="DIRECT_POST",
        help="TikTok delivery: DIRECT_POST publishes to the public feed (default); "
        "MEDIA_UPLOAD sends to the inbox/drafts to finish in-app",
    )
    po.add_argument(
        "--inbox", "--draft", action="store_true", dest="inbox",
        help="alias for --post-mode MEDIA_UPLOAD (TikTok inbox/draft, finish in-app)",
    )
    po.add_argument(
        "--privacy",
        default="PUBLIC_TO_EVERYONE",
        choices=[
            "PUBLIC_TO_EVERYONE",
            "MUTUAL_FOLLOW_FRIENDS",
            "FOLLOWER_OF_CREATOR",
            "SELF_ONLY",
        ],
        help="TikTok privacy level for DIRECT_POST (default PUBLIC_TO_EVERYONE)",
    )
    po.add_argument(
        "--aigc", action="store_true",
        help="disclose the video as AI-generated content (TikTok is_aigc)",
    )
    po.add_argument("--disable-comment", action="store_true", dest="disable_comment")
    po.add_argument("--disable-duet", action="store_true", dest="disable_duet")
    po.add_argument("--disable-stitch", action="store_true", dest="disable_stitch")
    # Per-platform metadata (all optional; `--caption` is the universal fallback title)
    yt = po.add_argument_group("youtube")
    yt.add_argument("--youtube-title", dest="youtube_title", help="YouTube title (≤100 chars)")
    yt.add_argument(
        "--youtube-privacy", dest="youtube_privacy", default="public",
        choices=["public", "unlisted", "private"], help="YouTube privacyStatus (default public)",
    )
    yt.add_argument("--youtube-tag", dest="youtube_tags", action="append", help="YouTube tag (repeatable)")
    ig = po.add_argument_group("instagram")
    ig.add_argument("--ig-title", dest="ig_title", help="Instagram caption override")
    ig.add_argument(
        "--ig-media-type", dest="ig_media_type", default="REELS",
        choices=["REELS", "STORIES"], help="Instagram media type (default REELS)",
    )
    xg = po.add_argument_group("x (twitter)")
    xg.add_argument("--x-title", dest="x_title", help="X post text override")
    xg.add_argument(
        "--x-long-text", dest="x_long_text", action="store_true",
        help="post caption >280 chars as a long-form post (Premium accounts)",
    )
    th = po.add_argument_group("threads")
    th.add_argument("--threads-title", dest="threads_title", help="Threads post text override")
    th.add_argument("--threads-topic", dest="threads_topic", help="Threads topic tag")
    fb = po.add_argument_group("facebook")
    fb.add_argument(
        "--facebook-page-id", dest="facebook_page_id",
        help="Facebook Page id (REQUIRED for facebook; or $FACEBOOK_PAGE_ID)",
    )
    fb.add_argument("--facebook-title", dest="facebook_title", help="Facebook title override")
    fb.add_argument(
        "--facebook-media-type", dest="facebook_media_type", default="REELS",
        choices=["REELS", "STORIES", "VIDEO"], help="Facebook media type (default REELS)",
    )
    bs = po.add_argument_group("bluesky")
    bs.add_argument("--bluesky-title", dest="bluesky_title", help="Bluesky post text override (≤300 chars)")
    po.add_argument(
        "--async", action="store_true", dest="async_upload",
        help="process in background (auto-on for scheduled posts)",
    )
    po.add_argument("--wait", action="store_true", help="poll status until terminal (async only)")
    po.add_argument("--timeout", type=int, default=300, help="seconds to wait with --wait")
    po.add_argument("--request-id", dest="request_id", help="client-provided id")
    po.add_argument("--no-archive", action="store_true", help="don't move source to published/")
    po.add_argument("--published-dir", default="published", help="archive folder name")
    po.add_argument(
        "--tag", default=None,
        help="optional source label recorded in the posts ledger (e.g. the cron name); "
        "falls back to $POST_SOURCE",
    )
    po.set_defaults(func=cmd_post)

    st = sub.add_parser("status", help="check an async upload's status")
    st.add_argument("--request-id", dest="request_id", required=True)
    st.add_argument("--wait", action="store_true")
    st.add_argument("--timeout", type=int, default=300)
    st.add_argument(
        "--file",
        help="the published .mp4 this request posted: on success, confirm each "
        "platform (status/url) into its sibling platform-status.json",
    )
    st.set_defaults(func=cmd_status)
    return p


def main():
    args = build_parser().parse_args()
    if getattr(args, "platform", None) is None and args.cmd == "post":
        args.platform = ["tiktok"]
    args.func(args)


if __name__ == "__main__":
    main()
