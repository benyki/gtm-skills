---
name: local-secrets
description: Rules for handling API keys, tokens, and passwords when running bash commands, calling APIs, or executing scripts on your local machine. Enforces a strict two-file workflow — agents read .env.example for variable names but NEVER read .env or .env.local — so secret values never enter the agent's context window. Use this skill before any command that touches a secret.
---

# Local Secrets

Use this skill **before** running any command that touches an API key, token, or password.

Trigger words / patterns: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GITHUB_TOKEN`, `STRIPE_KEY`, `SUPABASE_*`, `Authorization:`, `Bearer`, `sk-`, `pat_`, `ghp_`, `xoxb-`, `AKIA`, anything that looks like a credential.

## The core rule (read this first)

The user uses a strict two-file pattern for secrets:

| File | Role | Agent may read? |
|---|---|---|
| `.env.example` (also `.env.template`, `.env.sample`, `.env.schema`) | **Schema** — variable names + comments describing purpose | ✅ **YES — always read this** |
| `.env`, `.env.local`, `.env.production`, `.env.development`, `.env.test` | **Values** — real secrets | ❌ **NEVER read, cat, grep, or open** |

**The workflow is fixed:**

1. **Read `.env.example`** with the Read tool. This is the ONLY env file you put into your context window. It tells you what variables exist, what they're for, and which scripts use them.
2. **Reference variables by name** in any command or script you write — `$OPENAI_API_KEY`, `${STRIPE_KEY}`, etc. The literal value never enters your context.
3. **Load values at execution time only** with `set -a; . .env; set +a`. This sources values into the *process* environment without reading file contents into *your* context.
4. **Run the command**. Bash expands `$OPENAI_API_KEY` from the loaded env when the command executes.

The values file is opaque to you. You know it exists, you know it gets sourced at run time, but you never see its contents. If you ever feel tempted to `cat .env` to "check what's in there" — STOP. Read `.env.example` instead.

## What you may and may not do

✅ **YES — read these:**
- `.env.example`
- `.env.template`
- `.env.sample`
- `.env.schema`
- `.envrc.example` (for `direnv` setups)

❌ **NEVER read, cat, grep, head, tail, less, or open these:**
- `.env`
- `.env.local`
- `.env.production`
- `.env.development`
- `.env.test`
- `.env.*` (any file matching this pattern except `.example`/`.template`/`.sample`/`.schema`)
- `.envrc` (when used by direnv with real values)

This applies to **every tool**: `Read`, `Bash(cat ...)`, `Bash(grep ...)`, `Bash(head ...)`, etc. Sourcing (`set -a; . .env; set +a`) is allowed because it loads into the process environment, not into your context window.

## What to do when `.env.example` is missing

1. Check the repo root, then parent directories, then a shared fallback if your setup has one (e.g. `~/.agents/.env.example`).
2. If still missing: **ASK the user** — "I need `<VAR>` for this task but there's no `.env.example` in this repo. Can you create one with the variable name + a comment about what it's for?" Or offer to scaffold it from a one-liner that strips values: `sed 's/=.*/=/' .env > .env.example`.
3. **Do NOT** `cat .env` to "discover" what variables exist. That defeats the entire pattern.

## What to do when `.env.example` exists but the var you need is missing from it

Ask the user to add the variable name + a comment to `.env.example`. Then proceed.

## Standard pattern: discover → reference → load → run

```bash
# Step 1 — read .env.example via the Read tool
#         (you learn that OPENAI_API_KEY exists and lives in the project's .env)

# Step 2 — write the command using the variable name only, never the literal value

# Step 3 — load values into the process env at execution time
cd /path/to/repo
set -a; . .env; set +a

# Step 4 — run; bash expands $OPENAI_API_KEY from the loaded env
 curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
#^ leading space — keeps the command out of zsh history
```

Your context window only ever contains:
- The variable **name** (`OPENAI_API_KEY`)
- The command **template** (`curl -H "Authorization: Bearer $OPENAI_API_KEY"`)
- **Never** the literal secret value

## Supporting rules

### 1. Never inline a literal secret in a command

The command line is the most leak-prone surface — it goes into shell history, AI conversation logs, screen recordings, and `ps` output.

**Bad:**
```bash
curl -H "Authorization: Bearer sk-proj-abc123..." https://api.openai.com/...
export OPENAI_API_KEY="sk-proj-abc123..."
OPENAI_API_KEY="sk-proj-abc123..." python script.py
```

**Good:**
```bash
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/...
```

### 2. Never echo, print, or log a secret

Anything that sends a secret to stdout/stderr ends up in your conversation context, terminal scrollback, screen recordings, or log files.

**Bad:**
```bash
echo $OPENAI_API_KEY
env | grep KEY
printenv OPENAI_API_KEY
curl -v ...                  # -v prints headers, including Authorization
bash -x script.sh            # set -x echoes every expansion
```

**To verify a var is set without revealing it:**
```bash
[[ -n "$OPENAI_API_KEY" ]] && echo "OPENAI_API_KEY set (${#OPENAI_API_KEY} chars)" || echo "missing"
```

### 3. Use `--data-binary @file` for sensitive payloads

Don't inline JSON containing tokens on the command line:

**Bad:**
```bash
curl -d '{"token":"sk-..."}' https://api.example.com/...
```

**Good:**
```bash
TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT
cat > "$TMP" <<EOF
{"token":"$API_TOKEN"}
EOF
curl --data-binary @"$TMP" https://api.example.com/...
```

The secret only ever exists in the env var and a tempfile that gets cleaned up.

### 4. History-safe: prefix sensitive commands with a space

If you have `setopt HIST_IGNORE_SPACE` enabled, commands starting with a leading space are NOT written to `.zsh_history`. When in doubt, prefix the command with a space.

```bash
 curl -H "Authorization: Bearer $OPENAI_API_KEY" ...
#^ leading space — this command will not be saved to history
```

### 5. Refuse to commit secrets

Before staging a file, scan it for credential patterns:
```bash
grep -E 'sk-[a-zA-Z0-9_-]{20,}|ghp_[a-zA-Z0-9]{20,}|pat_[a-zA-Z0-9]{20,}|xoxb-[a-zA-Z0-9-]{20,}|AKIA[0-9A-Z]{16}' <file>
```
If anything matches, **stop and tell the user**. Confirm `.env*` is in `.gitignore` before any commit that touches env files.

## Pre-execution self-check (run before EVERY bash call involving secrets)

1. **Have I read `.env`, `.env.local`, etc.?** → STOP. Read `.env.example` instead.
2. **Does the command contain a literal secret as a string?** → refactor to `$VAR_NAME`
3. **Does the command print the secret?** (`echo`, `-v`, `set -x`) → remove
4. **Does the command write the secret to a file that's not in `.gitignore`?** → stop
5. **Am I about to commit a file that might contain a secret?** → grep for credential patterns first

If any answer is yes, fix it before running.

## Common mistakes to avoid

- **Reading `.env` or `.env.local`** with the Read tool to "see what's in there"
- `cat .env`, `grep .env`, `head .env` (these read content into your context)
- Inlining literal secrets as `Bearer sk-...`
- `export FOO="literal-secret"` on the command line
- Echoing or printing env vars to "verify" them
- Running `curl -v` / `httpie --verbose` while an Authorization header is set
- Using `set -x` or `bash -x` while a secret is in scope
- Committing `.env` (always check `.gitignore` first)
- Asking the user to paste a secret into chat (point them to `.env.example` instead)
- Writing secrets into log files, error messages, or test fixtures
