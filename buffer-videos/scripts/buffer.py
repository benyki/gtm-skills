#!/usr/bin/env python3
"""
Buffer GraphQL API helper for posting TikToks (and other channels).

Auth: reads BUFFER_API_KEY from the environment. Source it first, never inline it,
and ALWAYS use the absolute path (the shell cwd can reset between calls):

    set -a; . ~/.agents/.env; set +a

Endpoint: https://api.buffer.com  (GraphQL, Bearer auth)

Subcommands:
    whoami                     Show account + organizations
    channels                   List all channels (id, name, service)
    post                       Create a post (queue / now / next / scheduled / draft)
    status --id <postId>       Show a post's status (add --wait to poll to a terminal state)

Posting a local video (Buffer has NO upload endpoint — it fetches a public URL):
    # Let the script upload the file to a public GCS bucket and post it:
    python3 buffer.py post --channel your-account-en \
        --file ~/clip.mp4 --caption "..." --title "..." --when now --wait

    # Or pass an already-public URL directly:
    python3 buffer.py post --channel your-account-en \
        --video https://.../clip.mp4 --caption "..." --when queue
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import urllib.error

API_URL = "https://api.buffer.com"
DEFAULT_BUCKET = "gs://your-bucket/buffer"   # public bucket used for media hand-off
TERMINAL = {"sent", "error", "errored", "failed"}


def gql(query, variables=None, retries=3):
    token = os.environ.get("BUFFER_API_KEY")
    if not token:
        sys.exit("BUFFER_API_KEY not set. Run: set -a; . ~/.agents/.env; set +a")
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    last = None
    for attempt in range(retries):
        req = urllib.request.Request(
            API_URL, data=body,
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                payload = json.load(r)
            if payload.get("errors"):
                # GraphQL validation/logic errors are not transient — fail fast.
                sys.exit("GraphQL error:\n" + json.dumps(payload["errors"], indent=2))
            return payload["data"]
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")
            if e.code >= 500 and attempt < retries - 1:
                last = f"HTTP {e.code}: {detail}"
                time.sleep(2 * (attempt + 1))
                continue
            sys.exit(f"HTTP {e.code}: {detail}")
        except urllib.error.URLError as e:
            last = f"Network error: {e.reason}"
            if attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
                continue
            sys.exit(last)
    sys.exit(last or "Request failed")


# ---------------------------------------------------------------------------- #
# Account / channels
# ---------------------------------------------------------------------------- #
def get_org_id(explicit=None):
    orgs = gql("query { account { organizations { id name } } }")["account"]["organizations"]
    if explicit:
        for o in orgs:
            if o["id"] == explicit or o["name"].lower() == explicit.lower():
                return o["id"]
        sys.exit(f"No organization '{explicit}'. Have: " +
                 ", ".join(f"{o['name']} ({o['id']})" for o in orgs))
    if len(orgs) > 1:
        sys.exit("Multiple organizations — pass --org <name|id>:\n  " +
                 "\n  ".join(f"{o['name']} ({o['id']})" for o in orgs))
    return orgs[0]["id"]


def cmd_whoami(_):
    acct = gql("query { account { id email organizations { id name } } }")["account"]
    print(f"account: {acct['email']}  ({acct['id']})")
    for o in acct["organizations"]:
        print(f"  org: {o['name']}  ({o['id']})")


def get_channels(org_id):
    q = ("query($i: ChannelsInput!){ channels(input:$i){ "
         "id name displayName service type isDisconnected timezone } }")
    return gql(q, {"i": {"organizationId": org_id}})["channels"]


def cmd_channels(a):
    for c in get_channels(get_org_id(a.org)):
        flag = "  [DISCONNECTED]" if c["isDisconnected"] else ""
        print(f"{c['id']}  {c['service']:10} {c['name']}{flag}")


def resolve_channel(name_or_id, org_id):
    chans = get_channels(org_id)
    for c in chans:
        if c["id"] == name_or_id:
            return c
    matches = [c for c in chans
               if name_or_id.lower() in (c["name"].lower(), c["displayName"].lower())]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        sys.exit(f"No channel '{name_or_id}'. Available: " +
                 ", ".join(c["name"] for c in chans))
    sys.exit(f"Ambiguous channel '{name_or_id}'. Use the channel id instead.")


# ---------------------------------------------------------------------------- #
# Media upload (local file -> public URL)
# ---------------------------------------------------------------------------- #
def upload_to_bucket(local_path, bucket):
    local_path = os.path.expanduser(local_path)
    if not os.path.isfile(local_path):
        sys.exit(f"File not found: {local_path}")
    if not bucket.startswith("gs://"):
        sys.exit(f"--bucket must be a gs:// URI, got: {bucket}")
    name = os.path.basename(local_path)
    gs_uri = f"{bucket.rstrip('/')}/{name}"
    ctype = "video/mp4" if name.lower().endswith((".mp4", ".m4v")) else "application/octet-stream"
    print(f"uploading {name} -> {gs_uri} ...", file=sys.stderr)
    r = subprocess.run(["gsutil", "-h", f"Content-Type:{ctype}", "cp", local_path, gs_uri],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("gsutil upload failed:\n" + (r.stderr or r.stdout))
    # gs://bucket/path  ->  https://storage.googleapis.com/bucket/path
    https_url = "https://storage.googleapis.com/" + gs_uri[len("gs://"):]
    return https_url, gs_uri


def delete_from_bucket(gs_uri):
    subprocess.run(["gsutil", "rm", gs_uri], capture_output=True, text=True)


def archive_published(local_path, dirname="published"):
    """Move a just-published local video into a sibling `published/` folder."""
    local_path = os.path.expanduser(local_path)
    if not os.path.isfile(local_path):
        return None
    dest_dir = os.path.join(os.path.dirname(os.path.abspath(local_path)), dirname)
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, os.path.basename(local_path))
    if os.path.abspath(local_path) == os.path.abspath(dest):
        return dest  # already there
    shutil.move(local_path, dest)
    return dest


def _iso_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


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


# ---------------------------------------------------------------------------- #
# Post
# ---------------------------------------------------------------------------- #
CREATE_POST = """
mutation($input: CreatePostInput!) {
  createPost(input: $input) {
    __typename
    ... on PostActionSuccess { post { id text dueAt status } }
    ... on MutationError { message }
  }
}
"""

POST_STATUS = """
query($id: PostId!){ post(input:{id:$id}){ id status text dueAt error { message } } }
"""


def poll_status(post_id, timeout=300, interval=30):
    deadline = time.time() + timeout
    while True:
        p = gql(POST_STATUS, {"id": post_id})["post"]
        st = p["status"]
        err = (p.get("error") or {}).get("message")
        print(f"  status={st}" + (f"  error={err}" if err else ""), file=sys.stderr)
        if st in TERMINAL or err:
            return p
        if time.time() >= deadline:
            print("  (still pending — stopped waiting)", file=sys.stderr)
            return p
        time.sleep(interval)


def cmd_status(a):
    if a.wait:
        p = poll_status(a.id, timeout=a.timeout)
    else:
        p = gql(POST_STATUS, {"id": a.id})["post"]
    print(json.dumps(p, indent=2))


def cmd_post(a):
    if not a.video and not a.file:
        sys.exit("Provide either --video <public URL> or --file <local path>.")
    if a.video and a.file:
        sys.exit("Use only one of --video / --file.")

    # Fast path: if --channel is already a channel id (hex, 20+ chars), skip the
    # account+channels lookups entirely. Saves 2 API requests per post — important
    # because Buffer's API allows only 100 requests / 24h (see SKILL.md).
    if len(a.channel) >= 20 and all(c in "0123456789abcdefABCDEF" for c in a.channel):
        chan = {"id": a.channel, "name": a.channel}
    else:
        org_id = get_org_id(a.org)
        chan = resolve_channel(a.channel, org_id)

    # Local file -> upload -> public URL
    uploaded_gs = None
    video_url = a.video
    if a.file:
        video_url, uploaded_gs = upload_to_bucket(a.file, a.bucket)

    # Scheduling
    when, due_at = a.when, None
    mode = {"queue": "addToQueue", "now": "shareNow", "next": "shareNext"}.get(when)
    if mode is None:
        mode, due_at = "customScheduled", when   # treat as ISO datetime
    if a.draft:
        mode = "addToQueue"

    # automatic = Buffer publishes directly; notification = phone reminder flow
    scheduling_type = "notification" if a.notify else "automatic"

    video = {"url": video_url}
    if a.thumbnail:
        video["thumbnailUrl"] = a.thumbnail
    if a.title:
        video["metadata"] = {"title": a.title}

    inp = {
        "channelId": chan["id"],
        "schedulingType": scheduling_type,
        "mode": mode,
        "text": a.caption,
        "assets": [{"video": video}],
    }
    if due_at:
        inp["dueAt"] = due_at
    if a.title:
        inp["metadata"] = {"tiktok": {"title": a.title}}
    if a.draft:
        inp["saveToDraft"] = True

    res = gql(CREATE_POST, {"input": inp})["createPost"]
    if res["__typename"] != "PostActionSuccess":
        if uploaded_gs and not a.keep:
            delete_from_bucket(uploaded_gs)
        hint = ""
        if not a.notify:
            hint = ("\nIf this is a TikTok direct-publish/permission error, retry with "
                    "--notify (reminder flow).")
        sys.exit("Post failed: " + res.get("message", json.dumps(res)) + hint)

    p = res["post"]
    print(f"OK  channel={chan['name']}  post={p['id']}  "
          f"status={p.get('status')}  dueAt={p.get('dueAt')}")

    archived_dest = None
    final_status = p.get("status")

    # Archive the local source video once it's been pushed out (any non-draft post).
    if a.file and not a.draft and not a.no_archive:
        dest = archive_published(a.file, a.published_dir)
        archived_dest = dest
        if dest:
            print(f"archived source -> {dest}")

    if a.wait:
        final = poll_status(p["id"], timeout=a.timeout)
        st = final["status"]
        final_status = st
        err = (final.get("error") or {}).get("message")
        print(f"FINAL  post={p['id']}  status={st}" + (f"  error={err}" if err else ""))
        if st == "sent" and uploaded_gs and not a.keep:
            delete_from_bucket(uploaded_gs)
            print(f"cleaned up {uploaded_gs}")
        elif uploaded_gs:
            print(f"kept media at {uploaded_gs} (status={st})")
    elif uploaded_gs:
        print(f"media at {video_url}\n"
              f"(not deleted — Buffer still needs to fetch it; "
              f"run with --wait to auto-clean after 'sent', or remove later: "
              f"gsutil rm {uploaded_gs})")

    # Best-effort telemetry — never affects the post (see _log_post_ledger).
    src_abs = os.path.abspath(os.path.expanduser(a.file)) if a.file else None
    _log_post_ledger({
        "posted_at": _iso_now(),
        "pipeline": "buffer",
        "skill": "buffer-videos",
        "account": chan.get("name"),
        "channel_id": chan.get("id"),
        "channel_service": chan.get("service"),
        "status": "draft" if a.draft else final_status,
        "when": a.when,
        "due_at": p.get("dueAt"),
        "post_id": p.get("id"),
        "caption": a.caption,
        "title": a.title,
        "video_url": video_url,
        "file_src": src_abs if (a.file and not archived_dest) else None,
        "file_archived": archived_dest,
        "tag": a.tag or os.environ.get("POST_SOURCE"),
    })


def main():
    ap = argparse.ArgumentParser(description="Buffer API helper")
    ap.add_argument("--org", help="Organization name or id (only needed if you have several)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("whoami").set_defaults(func=cmd_whoami)
    sub.add_parser("channels").set_defaults(func=cmd_channels)

    s = sub.add_parser("status", help="Show a post's status")
    s.add_argument("--id", required=True)
    s.add_argument("--wait", action="store_true", help="Poll until sent/error")
    s.add_argument("--timeout", type=int, default=300)
    s.set_defaults(func=cmd_status)

    p = sub.add_parser("post", help="Create a video post")
    p.add_argument("--channel", required=True, help="Channel name or id")
    src = p.add_argument_group("media (exactly one)")
    src.add_argument("--video", help="Already-public URL of the video file")
    src.add_argument("--file", help="Local video path; uploaded to --bucket automatically")
    p.add_argument("--bucket", default=DEFAULT_BUCKET,
                   help=f"gs:// bucket for --file uploads (default {DEFAULT_BUCKET})")
    p.add_argument("--caption", required=True, help="Post caption/text")
    p.add_argument("--title", help="TikTok title / video title")
    p.add_argument("--thumbnail", help="Public URL for a custom thumbnail")
    p.add_argument("--when", default="queue",
                   help="queue | now | next | ISO datetime (e.g. 2026-06-20T15:00:00Z)")
    p.add_argument("--notify", action="store_true",
                   help="Notification (reminder) publishing instead of direct publish")
    p.add_argument("--draft", action="store_true", help="Save as draft instead of scheduling")
    p.add_argument("--wait", action="store_true",
                   help="Poll until the post reaches a terminal state; clean up uploaded media on 'sent'")
    p.add_argument("--keep", action="store_true", help="Keep uploaded media even after 'sent'")
    p.add_argument("--timeout", type=int, default=300, help="Max seconds to --wait")
    p.add_argument("--published-dir", default="published",
                   help="Sibling folder a --file source is moved into after publishing (default: published)")
    p.add_argument("--no-archive", action="store_true",
                   help="Don't move the --file source into the published/ folder")
    p.add_argument("--tag", default=None,
                   help="Optional source label recorded in the posts ledger (e.g. the cron "
                        "name); falls back to $POST_SOURCE")
    p.set_defaults(func=cmd_post)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
