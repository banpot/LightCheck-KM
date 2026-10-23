// usage: node render.js [pngScale]   -> poster_RGB.pdf, poster_preview.png, layout report
const path = require('path');
const { chromium } = require('playwright');
(async () => {
  const scale = Number(process.argv[2] || 0.5);
  const browser = await chromium.launch();
  const W = 3024, H = 3780;  // CSS px for 2268 x 2835 pt
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: scale });
  await page.goto('file://' + path.resolve(__dirname, 'poster.html'));
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(800);
  console.log(JSON.stringify(await page.evaluate(() => window.layoutReport())));
  const out = process.argv[3] || 'poster_preview.png';
  await page.screenshot({ path: out, fullPage: false, clip: { x: 0, y: 0, width: W, height: H } });
  if (!process.argv[4]) await page.pdf({ path: 'poster_RGB.pdf', width: '31.5in', height: '39.375in', printBackground: true, preferCSSPageSize: true });
  await browser.close();
})();
