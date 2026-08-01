#!/usr/bin/env bash
# phash-check.sh — measure perceptual-hash similarity of dupe variants
# against the source video and against each other.
#
# Samples multiple frames (default: t=1, 5, 10s) and reports the WORST
# (most-similar) similarity across all samples. Single-frame pHash is
# unreliable — a frame with uniform content can hash identically across
# very different variants. Multi-frame worst-case is the conservative
# measure that matches what a platform would actually compute over the
# whole video.
#
# Reports for each variant:
#   - worst pHash, dHash, aHash, wHash similarity vs source across samples
#   - verdict at <80% and <85% thresholds
# Then a pairwise pHash matrix showing the worst (most-similar) pair
# across all sampled frames.
#
# Usage:
#   bash phash-check.sh /abs/path/source.mp4 /abs/path/dup-dir/
#   bash phash-check.sh /abs/path/source.mp4 /abs/path/dup-dir/*.mp4
#   bash phash-check.sh --frames 1,3,7,12 /abs/path/source.mp4 /abs/path/dup-dir/
#
# Flags (before the source):
#   --frames LIST   comma-separated timestamps in seconds (default "1,5,10")
#
# Requires Python 3 + imagehash + Pillow.
#   pip3 install --break-system-packages imagehash Pillow
set -euo pipefail

FF="${FFMPEG_BIN:-/opt/homebrew/bin/ffmpeg}"

FRAMES="1,5,10"
while [[ $# -gt 0 && "$1" == --* ]]; do
  case "$1" in
    --frames) FRAMES="$2"; shift 2 ;;
    *) echo "unknown flag: $1" >&2; exit 1 ;;
  esac
done

SRC="${1:?usage: phash-check.sh [--frames LIST] /abs/path/source.mp4 /abs/path/dup-dir|files...}"
shift

VARIANTS=()
if [[ $# -eq 1 && -d "$1" ]]; then
  while IFS= read -r f; do VARIANTS+=("$f"); done < <(find "$1" -maxdepth 1 -name '*.mp4' | sort)
else
  VARIANTS=("$@")
fi

if [[ ${#VARIANTS[@]} -eq 0 ]]; then
  echo "no variants found" >&2
  exit 1
fi

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

IFS=',' read -ra FRAME_ARR <<< "$FRAMES"
for t in "${FRAME_ARR[@]}"; do
  "$FF" -ss "$t" -i "$SRC" -frames:v 1 "$TMP/_source.t${t}.png" -loglevel error
  for v in "${VARIANTS[@]}"; do
    name="$(basename "${v%.*}")"
    "$FF" -ss "$t" -i "$v" -frames:v 1 "$TMP/${name}.t${t}.png" -loglevel error
  done
done

VARS_JOINED="$(printf "%s\n" "${VARIANTS[@]}")"
SOURCE="$SRC" TMPDIR="$TMP" VARIANTS_LIST="$VARS_JOINED" FRAMES="$FRAMES" python3 - <<'PY'
import os, sys
from pathlib import Path
try:
    import imagehash
    from PIL import Image
except ImportError:
    print("missing deps: pip3 install --break-system-packages imagehash Pillow", file=sys.stderr)
    sys.exit(1)

tmp     = Path(os.environ["TMPDIR"])
src     = Path(os.environ["SOURCE"])
frames  = [t.strip() for t in os.environ["FRAMES"].split(",") if t.strip()]
variants = [Path(p) for p in os.environ["VARIANTS_LIST"].splitlines() if p]

def sim(d, bits=64): return (1 - d/bits) * 100

print(f"\nSource: {src}")
print(f"Variants: {len(variants)}  Frames sampled: t={','.join(frames)}s\n")

# For each variant, compute worst (highest) similarity to source across frames.
print("─ vs source (worst across sampled frames) ───────────────────────")
print(f"  {'variant':<26} {'pHash':>7} {'dHash':>7} {'aHash':>7} {'wHash':>7}  verdict")
worst_phash_per_var = []
fails_80, fails_85 = 0, 0
for v in variants:
    sims = {"p":[], "d":[], "a":[], "w":[]}
    for t in frames:
        s_img = Image.open(tmp / f"_source.t{t}.png")
        v_img = Image.open(tmp / f"{v.stem}.t{t}.png")
        sims["p"].append(sim(imagehash.phash(s_img)       - imagehash.phash(v_img)))
        sims["d"].append(sim(imagehash.dhash(s_img)       - imagehash.dhash(v_img)))
        sims["a"].append(sim(imagehash.average_hash(s_img) - imagehash.average_hash(v_img)))
        sims["w"].append(sim(imagehash.whash(s_img)       - imagehash.whash(v_img)))
    wp, wd, wa, ww = max(sims["p"]), max(sims["d"]), max(sims["a"]), max(sims["w"])
    worst_phash_per_var.append(wp)
    if wp >= 80: fails_80 += 1
    if wp >= 85: fails_85 += 1
    flag80 = "✓" if wp < 80 else "⚠"
    flag85 = "✓" if wp < 85 else "❌"
    print(f"  {v.stem:<26} {wp:>6.1f}% {wd:>6.1f}% {wa:>6.1f}% {ww:>6.1f}%  {flag85} <85%  {flag80} <80%")

print(f"\n  pHash spread: min={min(worst_phash_per_var):.1f}%  max={max(worst_phash_per_var):.1f}%  range={max(worst_phash_per_var)-min(worst_phash_per_var):.1f}pp")
print(f"  pHash fails:  {fails_85}/{len(variants)} variants ≥85%   {fails_80}/{len(variants)} variants ≥80%")

if len(variants) < 2:
    sys.exit(0)

# Pairwise: for each pair across all frames, take MAX similarity (worst case).
print("\n─ pairwise pHash similarity (worst across sampled frames) ────────")

# Cache hashes per (variant, frame)
hashes = {}
for v in variants:
    for t in frames:
        hashes[(v.stem, t)] = imagehash.phash(Image.open(tmp / f"{v.stem}.t{t}.png"))

short = [v.stem[-4:] if len(v.stem) > 4 else v.stem for v in variants]
worst_pair_sim, worst_pair = 0, ""
worst_pair_frame = ""
pairwise = {}
for i, a in enumerate(variants):
    for j, b in enumerate(variants):
        if i == j: continue
        max_s, max_t = 0, ""
        for t in frames:
            s = sim(hashes[(a.stem, t)] - hashes[(b.stem, t)])
            if s > max_s: max_s, max_t = s, t
        pairwise[(i, j)] = (max_s, max_t)
        if i < j and max_s > worst_pair_sim:
            worst_pair_sim, worst_pair, worst_pair_frame = max_s, f"{short[i]}↔{short[j]}", max_t

header = "          " + "  ".join(f"{s:>5}" for s in short)
print(header)
for i, a in enumerate(variants):
    row = f"  {short[i]:>7}  "
    for j, b in enumerate(variants):
        if i == j:
            row += f"  {'-':>5}"
        else:
            s, _ = pairwise[(i, j)]
            row += f"  {s:>4.0f}%"
    print(row)

verdict = "✓ unique" if worst_pair_sim < 85 else ("⚠ marginal" if worst_pair_sim < 95 else "❌ collision")
print(f"\n  worst pair: {worst_pair} at {worst_pair_sim:.1f}% (at t={worst_pair_frame}s)  {verdict}")

print("\n─ summary ────────────────────────────────────────────────────────")
if fails_85 == 0 and worst_pair_sim < 85:
    print("  ✓ all variants pass <85% vs source AND pairwise distinct across all frames")
elif fails_85 == 0:
    print("  ⚠ all variants pass vs source but worst pair too similar — tighten the spread")
elif worst_pair_sim < 85:
    print("  ⚠ pairwise unique but some variants too close to source — widen perturbation")
else:
    print("  ❌ both vs-source AND pairwise issues — review the stack and parameter envelopes")
PY
