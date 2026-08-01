#!/usr/bin/env node
// Post text plus 1–4 images to Bluesky.
//
// Usage:
//   node --env-file=~/.agents/.env post-image.mjs \
//     --account MAIN --text "two pics" \
//     --image ./a.jpg --alt "first photo" \
//     --image ./b.jpg --alt "second photo"
//
// Limits: max 4 images, max 1,000,000 bytes (~1 MB) each, 2,000,000 bytes total.

import { readFileSync, statSync } from 'node:fs'
import { extname } from 'node:path'
import { parseArgs, login, buildPostRecord, die, fmtRef } from './_lib.mjs'

const args = parseArgs(process.argv.slice(2))

if (args.help || !args.account || args.text === undefined || !args.image) {
  console.log(`usage: post-image.mjs --account <NAME> --text "<text>" \\
              --image <path> --alt "<alt text>" [--image ... --alt ...]`)
  process.exit(args.help ? 0 : 1)
}

const images = Array.isArray(args.image) ? args.image : [args.image]
const alts   = Array.isArray(args.alt)   ? args.alt   : (args.alt ? [args.alt] : [])
if (images.length > 4) die('max 4 images per post')
if (alts.length !== images.length) die('--alt count must equal --image count (alt text is required for accessibility)')

const MIME = {
  '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
  '.png': 'image/png',  '.gif': 'image/gif',
  '.webp': 'image/webp',
}

const PER_IMAGE_MAX = 1_000_000
const TOTAL_MAX = 2_000_000
let total = 0
for (const p of images) {
  const sz = statSync(p).size
  if (sz > PER_IMAGE_MAX) die(`${p} is ${sz} bytes; max ${PER_IMAGE_MAX} per image`)
  total += sz
}
if (total > TOTAL_MAX) die(`total ${total} bytes; max ${TOTAL_MAX} per post`)

try {
  const { agent } = await login(args.account)

  const embedImages = []
  for (let i = 0; i < images.length; i++) {
    const path = images[i]
    const ext = extname(path).toLowerCase()
    const mime = MIME[ext]
    if (!mime) die(`unsupported image extension: ${ext}`)
    const bytes = readFileSync(path)
    const { data } = await agent.uploadBlob(bytes, { encoding: mime })
    embedImages.push({ image: data.blob, alt: alts[i] })
  }

  // Build text record then attach embed
  const record = await buildPostRecord(agent, { text: args.text })
  record.embed = { $type: 'app.bsky.embed.images', images: embedImages }

  const result = await agent.post(record)
  console.log('posted:')
  console.log(fmtRef(result))
} catch (err) {
  die(err.message ?? String(err))
}
