#!/usr/bin/env node
// Usage: node download-instagram-audio.js <instagram-reel-url> <output.mp3>

const https = require('https');
const { execSync } = require('child_process');
const path = require('path');
const os = require('os');

const [, , reelUrl, outputPath] = process.argv;
if (!reelUrl || !outputPath) {
  console.error('Usage: node download-instagram-audio.js <reel-url> <output.mp3>');
  process.exit(1);
}

const APIFY_TOKEN = process.env.APIFY_FALLBACK_API_KEY || process.env.APIFY_API_KEY;
if (!APIFY_TOKEN) {
  console.error('APIFY_FALLBACK_API_KEY not set. Source ~/.agents/.env first.');
  process.exit(1);
}

const tmpVideo = path.join(os.tmpdir(), `reel-${Date.now()}.mp4`);
const body = JSON.stringify({ url: [reelUrl] });

const options = {
  hostname: 'api.apify.com',
  path: `/v2/acts/elis~instagram-downloader-api/run-sync-get-dataset-items?token=${APIFY_TOKEN}&timeout=60`,
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) },
};

console.log('Fetching video URL via Apify...');
const req = https.request(options, res => {
  let data = '';
  res.on('data', c => (data += c));
  res.on('end', () => {
    let items;
    try { items = JSON.parse(data); } catch (e) { console.error('Parse error:', data.slice(0, 300)); process.exit(1); }

    const result = items[0]?.result;
    if (!result?.length) {
      console.error('No result array. Response:', JSON.stringify(items).slice(0, 400));
      process.exit(1);
    }

    // Last item in result[] is the actual mp4; earlier items are thumbnails
    const videoUrl = result[result.length - 1]?.url;
    if (!videoUrl) { console.error('No video URL in result'); process.exit(1); }

    console.log(`Downloading reel to ${tmpVideo}...`);
    execSync(`curl -L -s -o ${JSON.stringify(tmpVideo)} ${JSON.stringify(videoUrl)}`, { stdio: 'inherit' });

    const fileType = execSync(`file ${JSON.stringify(tmpVideo)}`, { encoding: 'utf8' });
    if (fileType.includes('HTML')) {
      console.error('Downloaded file is HTML, not a video. The reel may be private or the URL expired.');
      execSync(`rm -f ${JSON.stringify(tmpVideo)}`);
      process.exit(1);
    }

    console.log(`Extracting audio → ${outputPath}...`);
    execSync(
      `ffmpeg -y -i ${JSON.stringify(tmpVideo)} -vn -acodec libmp3lame -q:a 2 ${JSON.stringify(outputPath)} 2>&1 | tail -2`,
      { stdio: 'inherit', shell: true }
    );
    execSync(`rm -f ${JSON.stringify(tmpVideo)}`);
    console.log('Done:', outputPath);
  });
});

req.on('error', e => { console.error(e.message); process.exit(1); });
req.write(body);
req.end();
