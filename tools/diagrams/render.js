// usage: node render.js in.svg out.png widthPx
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [inp, out, w] = process.argv.slice(2);
  const svg = fs.readFileSync(inp, 'utf8');
  const m = svg.match(/viewBox="([\d.\-\s]+)"/);
  const [, , vw, vh] = m[1].trim().split(/\s+/).map(Number);
  const scale = Number(w) / vw;
  const browser = await chromium.launch({ executablePath: process.env.CHROME || undefined });
  const page = await browser.newPage({ viewport: { width: Math.round(vw), height: Math.round(vh) }, deviceScaleFactor: scale });
  await page.setContent(`<!doctype html><html><head><style>html,body{margin:0;padding:0;background:transparent}svg{display:block}</style></head><body>${svg}</body></html>`);
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(300);
  await page.screenshot({ path: out, omitBackground: true, clip: { x: 0, y: 0, width: vw, height: vh } });
  await browser.close();
})();
