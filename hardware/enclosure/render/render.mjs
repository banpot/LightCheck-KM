import { chromium } from 'playwright';   // npm i playwright three@0.169.0
const views = process.argv.slice(2).length ? process.argv.slice(2) : ['hero', 'exploded', 'print'];
const out = new URL('../renders/', import.meta.url).pathname;
const names = { hero: 'enclosure_hero.png', exploded: 'enclosure_exploded.png', print: 'enclosure_printbed.png' };
const sizes = { hero: [1500, 1000], exploded: [1200, 1250], print: [1400, 1050] };
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
for (const v of views) {
  const [w, h] = sizes[v];
  const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 3 });
  page.on('console', m => console.log(v, 'console:', m.text()));
  page.on('pageerror', e => console.log(v, 'ERR:', e.message));
  await page.goto(`http://127.0.0.1:8765/render/render.html?view=${v}`);
  await page.waitForFunction(() => window.__done === true, null, { timeout: 120000 });
  await page.screenshot({ path: out + names[v], omitBackground: true });
  console.log('saved', out + names[v]);
  await page.close();
}
await browser.close();
