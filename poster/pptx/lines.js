// Line-fill report for every wrapped text block in poster.html: flags orphans (a short last line)
// and lines that are nearly full (risky when PowerPoint re-wraps).   usage: node lines.js [all]
const path = require('path');
const fs = require('fs');
let chromium;
try { ({ chromium } = require('playwright')); } catch (e) { ({ chromium } = require('/home/claude/work/diagram/node_modules/playwright')); }
const LAUNCH = fs.existsSync('/opt/pw-browsers/chromium') ? { executablePath: '/opt/pw-browsers/chromium' } : {};

(async () => {
  const browser = await chromium.launch(LAUNCH);
  const page = await browser.newPage({ viewport: { width: 3024, height: 3780 } });
  await page.goto('file://' + path.resolve(__dirname, '..', 'poster.html'));
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(500);
  const rows = await page.evaluate(() => {
    const S = e => getComputedStyle(e);
    const inl = e => ['inline', 'contents'].includes(S(e).display);
    const out = [];
    for (const el of document.querySelectorAll('body *')) {
      if (inl(el) || el.closest('[data-pptx="img"]') || el.closest('svg')) continue;
      const st = S(el);
      if (st.whiteSpace === 'nowrap') continue;
      const chars = [];
      const tw = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
      for (let t = tw.nextNode(); t; t = tw.nextNode()) {
        let p = t.parentElement; while (p !== el && inl(p)) p = p.parentElement;
        if (p !== el) continue;
        for (let i = 0; i < t.length; i++) {
          const r = document.createRange(); r.setStart(t, i); r.setEnd(t, i + 1);
          const b = r.getBoundingClientRect();
          if (b.width > 0) chars.push({ c: t.nodeValue[i], top: b.top + b.height / 2, l: b.left, r: b.right, h: b.height });
        }
      }
      if (chars.length < 2) continue;
      const lines = [];
      for (const ch of chars) {
        const L = lines.find(x => Math.abs(x.mid - ch.top) < ch.h * 0.45);
        if (L) { L.l = Math.min(L.l, ch.l); L.r = Math.max(L.r, ch.r); L.t += ch.c; }
        else lines.push({ mid: ch.top, l: ch.l, r: ch.r, t: ch.c });
      }
      if (lines.length < 2) continue;
      lines.sort((a, b) => a.mid - b.mid);
      const r = el.getBoundingClientRect();
      const g = k => parseFloat(st[k]) || 0;
      const x0 = r.left + g('paddingLeft') + g('borderLeftWidth'), x1 = r.right - g('paddingRight') - g('borderRightWidth');
      const W = x1 - x0;
      const fill = lines.map(L => (L.r - L.l) / W);
      out.push({ sel: el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).split(' ').join('.') : ''),
        y: Math.round(r.top * 0.75), x: Math.round(r.left * 0.75), n: lines.length,
        fill: fill.map(f => +f.toFixed(2)), last: lines[lines.length - 1].t.trim(), first: lines[0].t.trim().slice(0, 40) });
    }
    return out;
  });
  const all = process.argv[2] === 'all';
  let bad = 0;
  for (const r of rows) {
    const last = r.fill[r.fill.length - 1];
    const full = Math.max(...r.fill.slice(0, -1));
    const flag = last < 0.3 ? 'ORPHAN' : full > 0.985 ? 'TIGHT' : '';
    if (flag) bad++;
    if (flag || all) console.log(`${flag.padEnd(6)} @${r.x},${r.y} ${r.sel.slice(0, 18).padEnd(18)} n=${r.n} fill=${r.fill.join('/')} | ${r.first} … «${r.last}»`);
  }
  console.log(`${rows.length} wrapped blocks, ${bad} flagged`);
  await browser.close();
})();
