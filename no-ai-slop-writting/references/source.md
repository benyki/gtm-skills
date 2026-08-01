# Source

These rules are adapted from **no-ai-slop** by Peter Yang.

- Repo: https://github.com/petergyang/no-ai-slop
- License: MIT
- Adapted: 2026-07-23

Local changes vs upstream:

- Widened the `description` frontmatter so the skill also triggers before writing user-facing copy in a repo (landing pages, App Store text, changelogs, emails), not only when a draft is pasted in.
- Added a "When to use this skill" section naming the sibling skills whose output should be run through these rules (`write-changelog-app`, `aso-appstore-screenshots`, `domain-finder`).
- Moved `eval.md` into `references/` to match the local skill layout.

If upstream updates, re-diff against `SKILL.md` and `eval.md` at the repo root rather than overwriting the local edits above.
