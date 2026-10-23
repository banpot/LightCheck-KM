// Dump the rendered poster.html into a flat list of native PowerPoint-able items
// (text boxes with runs, shapes, lines, pictures) + rasterise the few parts that
// stay pictures (equations, diagrams, logos, QR).   usage: node extract.js
const path = require('path');
const fs = require('fs');
let chromium;
try { ({ chromium } = require('playwright')); } catch (e) { ({ chromium } = require('/home/claude/work/diagram/node_modules/playwright')); }
const LAUNCH = process.env.CHROME ? { executablePath: process.env.CHROME } : (fs.existsSync('/opt/pw-browsers/chromium') ? { executablePath: '/opt/pw-browsers/chromium' } : {});

const HERE = __dirname;
const MEDIA = path.join(HERE, 'media');
const DSF = 3.125; // 300 ppi at placed size (1 CSS px = 1/96 in)

function inPage() {
  const items = [];
  let shotN = 0;
  const S = e => getComputedStyle(e);
  const col = c => {
    const m = /rgba?\(([^)]+)\)/.exec(c || '');
    if (!m) return null;
    const p = m[1].split(/[\s,/]+/).filter(Boolean).map(Number);
    if (p.length > 3 && p[3] === 0) return null;
    return p.slice(0, 3).map(v => Math.round(v).toString(16).padStart(2, '0')).join('').toUpperCase();
  };
  const rect = e => { const r = e.getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height }; };
  const isImgNode = e => e.tagName === 'IMG' || e.dataset.pptx === 'img' || e.tagName.toLowerCase() === 'svg';
  const inlineDisp = d => d === 'inline' || d === 'contents';

  // ---- 1. inline-blocks inside running text become runs (highlight); lone ones stay shapes
  const blockUp = (n, stopAtIB) => {
    let p = n.nodeType === 3 ? n.parentElement : n.parentElement;
    while (p) {
      const d = S(p).display;
      if (inlineDisp(d)) { p = p.parentElement; continue; }
      if (d === 'inline-block' && !stopAtIB && p.dataset.run === '1') { p = p.parentElement; continue; }
      return p;
    }
    return null;
  };
  for (const ib of document.querySelectorAll('body *')) {
    if (S(ib).display !== 'inline-block' || isImgNode(ib) || ib.closest('[data-pptx="img"]')) continue;
    const cb = blockUp(ib, true);
    const tw = document.createTreeWalker(cb, NodeFilter.SHOW_TEXT);
    let mixed = false;
    for (let t = tw.nextNode(); t; t = tw.nextNode()) {
      if (!t.nodeValue.trim() || ib.contains(t)) continue;
      if (blockUp(t, true) === cb) { mixed = true; break; }
    }
    if (mixed) ib.dataset.run = '1';
  }
  const isInlineEl = e => inlineDisp(S(e).display) || e.dataset.run === '1';

  // ---- 2. text runs of one block container
  function runsOf(el) {
    const paras = [[]];
    const nodes = [];
    const lineHeights = [];
    const sizes = [];
    const visit = (n, ctx) => {
      if (n.nodeType === 3) {
        if (!n.nodeValue) return;
        const p = n.parentElement, st = S(p);
        let txt = n.nodeValue;
        const ws = st.whiteSpace;
        if (!/pre/.test(ws)) txt = txt.replace(/[ \t\n\r\f]+/g, ' ');
        if (ws === 'nowrap' || ctx.nowrap) txt = txt.replace(/ /g, ' ');
        const fam = st.fontFamily.split(',')[0].replace(/["']/g, '').trim();
        let size = parseFloat(st.fontSize) * 0.75;
        if (ctx.sub || ctx.sup) size = ctx.baseSize;
        const run = { text: txt, fam, weight: parseInt(st.fontWeight, 10), italic: st.fontStyle === 'italic',
          size: +size.toFixed(2), color: col(st.color) || '000000', sub: !!ctx.sub, sup: !!ctx.sup,
          highlight: ctx.highlight || null, link: ctx.link || null,
          spacing: st.letterSpacing === 'normal' ? 0 : +(parseFloat(st.letterSpacing) * 0.75).toFixed(2) };
        paras[paras.length - 1].push(run);
        if (txt.trim()) {
          nodes.push(n);
          const lh = st.lineHeight === 'normal' ? parseFloat(st.fontSize) * 1.25 : parseFloat(st.lineHeight);
          if (!ctx.sub && !ctx.sup) { lineHeights.push(lh); sizes.push(size); }
        }
        return;
      }
      if (n.nodeType !== 1) return;
      if (n.tagName === 'BR') { paras.push([]); return; }
      if (n !== el && (!isInlineEl(n) || isImgNode(n))) return; // separate box
      const st = S(n);
      const c2 = Object.assign({}, ctx);
      if (n !== el) {
        if (n.tagName === 'SUB') { c2.sub = true; c2.baseSize = parseFloat(S(n.parentElement).fontSize) * 0.75; }
        if (n.tagName === 'SUP') { c2.sup = true; c2.baseSize = parseFloat(S(n.parentElement).fontSize) * 0.75; }
        if (n.dataset.run === '1' && col(st.backgroundColor)) c2.highlight = col(st.backgroundColor);
        if (st.whiteSpace === 'nowrap') c2.nowrap = true;
      }
      if (n.dataset.link) c2.link = n.dataset.link;
      for (const k of n.childNodes) visit(k, c2);
    };
    visit(el, { link: el.dataset.link || null });
    // collapse whitespace across run boundaries, trim paragraph ends
    for (const p of paras) {
      let prevSpace = true;
      for (const r of p) {
        if (prevSpace) r.text = r.text.replace(/^ +/, '');
        if (r.text.length) prevSpace = / $/.test(r.text);
      }
      for (let i = p.length - 1; i >= 0; i--) {
        p[i].text = p[i].text.replace(/ +$/, '');
        if (p[i].text.length) break;
      }
    }
    const clean = paras.map(p => p.filter(r => r.text.length));
    while (clean.length && !clean[clean.length - 1].length) clean.pop();
    while (clean.length && !clean[0].length) clean.shift();
    if (!nodes.length) return null;
    // geometry of the rendered lines
    const frags = [];
    for (const n of nodes) {
      const rg = document.createRange(); rg.selectNodeContents(n);
      for (const r of rg.getClientRects()) if (r.width >= 0.5) frags.push({ top: r.top, bottom: r.bottom, h: r.height });
    }
    const st = S(el);
    const elLH = st.lineHeight === 'normal' ? parseFloat(st.fontSize) * 1.25 : parseFloat(st.lineHeight);
    const X = Math.max(Math.max(...lineHeights, 0), elLH);           // line pitch (px)
    const minTop = Math.min(...frags.map(f => f.top));
    const first = frags.filter(f => f.top < minTop + 0.6 * X);
    const tall = first.reduce((a, b) => (b.h > a.h ? b : a));
    const C = tall.h;                                                   // content height of first line
    const centers = frags.map(f => (f.top + f.bottom) / 2).sort((a, b) => a - b);
    let lines = 0, last = -1e9;
    for (const c of centers) { if (c - last > X * 0.5) { lines++; last = c; } }
    const forced = lines <= clean.length;                              // every line ends at a <br>
    return { paras: clean, lines, X, C, forced,
      boxTop: tall.top - (X - C),                                       // y of a PowerPoint box with exact spacing X
      contentTop: Math.min(...first.map(f => f.top)), contentBottom: Math.max(...frags.map(f => f.bottom)),
      align: ({ start: 'left', end: 'right', '-webkit-center': 'center' })[st.textAlign] || st.textAlign,
      nowrap: st.whiteSpace === 'nowrap', indent: parseFloat(st.textIndent) || 0 };
  }

  // ---- 3. backgrounds / borders -> shapes
  function shapeOf(el) {
    const st = S(el), r = rect(el);
    const bg = col(st.backgroundColor);
    const side = s => ({ w: parseFloat(st[`border${s}Width`]) || 0, c: col(st[`border${s}Color`]), style: st[`border${s}Style`] });
    const b = { T: side('Top'), R: side('Right'), B: side('Bottom'), L: side('Left') };
    const on = k => b[k].w > 0 && b[k].style !== 'none' && b[k].c;
    const rad = parseFloat(st.borderTopLeftRadius) || 0;
    const radR = parseFloat(st.borderTopRightRadius) || 0;
    const uniformR = rad === radR && rad === (parseFloat(st.borderBottomRightRadius) || 0);
    const radius = uniformR ? Math.min(rad, r.h / 2, r.w / 2) : 0;
    const round = st.borderRadius === '50%' || (radius >= r.h / 2 - 0.5 && radius >= r.w / 2 - 0.5 && Math.abs(r.w - r.h) < 1);
    const sides = ['T', 'R', 'B', 'L'].filter(on);
    const out = [];
    if (sides.length === 4 && b.T.w === b.L.w && b.T.c === b.L.c) {
      const w = b.T.w;
      out.push({ type: 'shape', x: r.x + w / 2, y: r.y + w / 2, w: r.w - w, h: r.h - w, fill: bg, radius: Math.max(0, radius - w / 2),
        ellipse: round, line: { color: b.T.c, width: w * 0.75, dash: b.T.style === 'dashed' ? 'dash' : (b.T.style === 'dotted' ? 'sysDot' : null) } });
    } else if (sides.length === 1) {
      const k = sides[0], w = b[k].w;
      if (bg) {
        out.push({ type: 'shape', x: r.x, y: r.y, w: r.w, h: r.h, fill: b[k].c, radius, ellipse: false });
        const ins = { x: r.x + (k === 'L' ? w : 0), y: r.y + (k === 'T' ? w : 0), w: r.w - (k === 'L' || k === 'R' ? w : 0), h: r.h - (k === 'T' || k === 'B' ? w : 0) };
        out.push(Object.assign({ type: 'shape', fill: bg, radius, ellipse: false }, ins));
      } else {
        const strip = { T: { x: r.x, y: r.y, w: r.w, h: w }, B: { x: r.x, y: r.y + r.h - w, w: r.w, h: w },
          L: { x: r.x, y: r.y, w, h: r.h }, R: { x: r.x + r.w - w, y: r.y, w, h: r.h } }[k];
        out.push(Object.assign({ type: 'shape', fill: b[k].c, radius: 0 }, strip));
      }
    } else if (bg) {
      out.push({ type: 'shape', x: r.x, y: r.y, w: r.w, h: r.h, fill: bg, radius, ellipse: round });
    }
    return out;
  }

  const contentBox = el => {
    const st = S(el), r = rect(el);
    const g = k => parseFloat(st[k]) || 0;
    const l = g('borderLeftWidth') + g('paddingLeft'), rr = g('borderRightWidth') + g('paddingRight');
    const t = g('borderTopWidth') + g('paddingTop'), bb = g('borderBottomWidth') + g('paddingBottom');
    return { x: r.x + l, y: r.y + t, w: r.w - l - rr, h: r.h - t - bb, ins: { l, r: rr, t, b: bb } };
  };

  function nameOf(el, fallback) {
    if (el.dataset.name) return el.dataset.name;
    const cls = (el.className && el.className.baseVal === undefined ? el.className : '') || '';
    return fallback + (cls ? ' .' + cls.trim().split(/\s+/).join('.') : '');
  }

  // ---- 4. pictures
  function emitImage(el) {
    const r = rect(el), st = S(el);
    const radius = parseFloat(st.borderTopLeftRadius) || 0;
    const it = { type: 'image', x: r.x, y: r.y, w: r.w, h: r.h, radius, name: nameOf(el, 'ภาพ'), link: el.dataset.link || null };
    const src = el.tagName === 'IMG' ? decodeURIComponent(new URL(el.src).pathname) : null;
    if (src && /\.(jpe?g|png)$/i.test(src) && !el.dataset.pptx) {
      it.src = src; it.fit = st.objectFit; it.nat = [el.naturalWidth, el.naturalHeight];
      if (!el.dataset.name) it.name = 'ภาพ ' + src.split('/').pop();
    } else {
      it.shotId = String(++shotN); el.setAttribute('data-shot-id', it.shotId);
      if (src && !el.dataset.name) it.name = 'ภาพ ' + src.split('/').pop();
    }
    if (el.dataset.photo) it.photo = true;
    items.push(it);
  }

  // ---- 5. the KM cycle SVG as native shapes
  function emitKm(svg) {
    const pt = (el, x, y) => new DOMPoint(x, y).matrixTransform(el.getScreenCTM());
    const sc = svg.getScreenCTM().a;
    for (const ln of svg.querySelectorAll('line')) {
      const a = pt(ln, +ln.getAttribute('x1'), +ln.getAttribute('y1'));
      const b = pt(ln, +ln.getAttribute('x2'), +ln.getAttribute('y2'));
      const len = Math.hypot(b.x - a.x, b.y - a.y), ext = 7.5 * sc; // marker refX offset
      const bx = b.x + (b.x - a.x) / len * ext, by = b.y + (b.y - a.y) / len * ext;
      items.push({ type: 'line', x1: a.x, y1: a.y, x2: bx, y2: by, color: ln.getAttribute('stroke').replace('#', '').toUpperCase(),
        width: +ln.getAttribute('stroke-width') * sc * 0.75, arrow: !!ln.getAttribute('marker-end'), name: 'ลูกศรวงจร KM' });
    }
    const txt = (t, name) => {
      const r = rect(t), st = S(t);
      const anchor = pt(t, +t.getAttribute('x'), +t.getAttribute('y'));
      const W = r.w + 80;
      return { type: 'text', x: anchor.x - W / 2, y: r.y, w: W, h: r.h, valign: 'middle', wrap: false, name,
        paras: [[{ text: t.textContent, fam: st.fontFamily.split(',')[0].replace(/["']/g, '').trim(), weight: parseInt(st.fontWeight, 10),
          italic: false, size: +(parseFloat(st.fontSize) * sc * 0.75).toFixed(2), color: col(st.fill) || '000000', spacing: 0 }]],
        align: 'center', single: true };
    };
    for (const g of svg.querySelectorAll('g')) {
      const rc = g.querySelector('rect'), ci = g.querySelector('circle');
      const r = rect(rc);
      const sw = +rc.getAttribute('stroke-width') * sc;
      const lab = g.querySelector('.kl').textContent;
      items.push({ type: 'shape', x: r.x, y: r.y, w: r.w, h: r.h, fill: 'FFFFFF', radius: +rc.getAttribute('rx') * sc,
        line: { color: rc.getAttribute('stroke').replace('#', '').toUpperCase(), width: sw * 0.75 }, name: 'วงจร KM: กรอบ ' + lab });
      const cr = rect(ci), kn = g.querySelector('.kn'), st = S(kn);
      items.push({ type: 'text', x: cr.x, y: cr.y, w: cr.w, h: cr.h, valign: 'middle', wrap: false, align: 'center', single: true,
        shape: { fill: ci.getAttribute('fill').replace('#', '').toUpperCase(), ellipse: true,
          line: { color: 'FFFFFF', width: +ci.getAttribute('stroke-width') * sc * 0.75 } }, ins: { l: 0, r: 0, t: 0, b: 0 },
        name: 'วงจร KM: เลข ' + kn.textContent,
        paras: [[{ text: kn.textContent, fam: st.fontFamily.split(',')[0].replace(/["']/g, '').trim(), weight: parseInt(st.fontWeight, 10),
          size: +(parseFloat(st.fontSize) * sc * 0.75).toFixed(2), color: 'FFFFFF', spacing: 0 }]] });
      items.push(txt(g.querySelector('.kl'), 'วงจร KM: ' + lab));
      items.push(txt(g.querySelector('.ks'), 'วงจร KM: ' + lab + ' (คำอธิบาย)'));
    }
    for (const t of svg.querySelectorAll(':scope > text')) items.push(txt(t, 'วงจร KM: ' + t.textContent));
  }

  // ---- 6. walk the document
  function walk(el) {
    const st = S(el);
    if (st.display === 'none' || st.visibility === 'hidden' || ['SCRIPT', 'STYLE'].includes(el.tagName)) return;
    if (el.tagName.toLowerCase() === 'svg') { if (el.classList.contains('kmcycle')) emitKm(el); else emitImage(el); return; }
    if (el.tagName === 'IMG' || el.dataset.pptx === 'img') { emitImage(el); return; }
    if (el !== document.body && !isInlineEl(el)) {
      const shapes = shapeOf(el);
      const g = runsOf(el);
      const hasBlockKids = [...el.children].some(c => !isInlineEl(c) && S(c).display !== 'none' && S(c).position !== 'absolute');
      const name = nameOf(el, el.tagName.toLowerCase());
      if (g && shapes.length === 1 && !hasBlockKids && (g.lines <= 2)) {
        const sh = shapes[0], cb = contentBox(el), r = rect(el);
        const ins = Object.assign({}, cb.ins);
        if (g.lines > 1) { const h = (g.X - g.C) / 2; ins.t = Math.max(0, ins.t - h); ins.b = Math.max(0, ins.b + h); }
        items.push({ type: 'text', x: r.x, y: r.y, w: r.w, h: r.h, paras: g.paras, align: g.align, valign: 'middle',
          wrap: !(g.nowrap || g.lines === 1 || g.forced), single: g.lines === 1, lineHeight: g.lines > 1 ? g.X : null, name,
          shape: { fill: sh.fill, radius: sh.radius + (sh.line ? sh.line.width / 1.5 : 0), ellipse: sh.ellipse, line: sh.line || null },
          ins });
      } else {
        shapes.forEach((s, i) => items.push(Object.assign(s, { name: name + (shapes.length > 1 ? ` (${i + 1})` : '') })));
        if (g) {
          const cb = contentBox(el);
          if (g.lines === 1 || g.nowrap) {
            items.push({ type: 'text', x: cb.x, y: g.contentTop, w: cb.w, h: g.contentBottom - g.contentTop, paras: g.paras,
              align: g.align, valign: 'middle', wrap: false, single: true, name, indent: g.indent });
          } else {
            items.push({ type: 'text', x: cb.x, y: g.boxTop, w: cb.w, h: g.lines * g.X, paras: g.paras, align: g.align,
              valign: 'top', wrap: !g.forced, single: false, lineHeight: g.X, name, indent: g.indent });
          }
        }
      }
    }
    for (const c of el.children) walk(c);
  }
  walk(document.body);
  return { W: document.documentElement.clientWidth, H: document.documentElement.clientHeight, items };
}

(async () => {
  fs.rmSync(MEDIA, { recursive: true, force: true });
  fs.mkdirSync(MEDIA, { recursive: true });
  const browser = await chromium.launch(LAUNCH);
  const page = await browser.newPage({ viewport: { width: 3024, height: 3780 }, deviceScaleFactor: DSF });
  await page.goto('file://' + path.resolve(HERE, '..', 'poster.html'));
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(800);
  const dump = await page.evaluate(inPage);
  // rasterise picture-parts with nothing else visible (transparent background)
  await page.addStyleTag({ content: 'html.shot *{visibility:hidden!important} html.shot [data-shot-on], html.shot [data-shot-on] *{visibility:visible!important} html.shot,html.shot body{background:transparent!important}' });
  await page.evaluate(() => document.documentElement.classList.add('shot'));
  for (const it of dump.items) {
    if (!it.shotId) continue;
    const sel = `[data-shot-id="${it.shotId}"]`;
    await page.evaluate(s => document.querySelector(s).setAttribute('data-shot-on', ''), sel);
    it.file = path.join(MEDIA, `shot_${it.shotId.padStart(2, '0')}.png`);
    await page.screenshot({ path: it.file, omitBackground: true, clip: { x: it.x, y: it.y, width: it.w, height: it.h } });
    await page.evaluate(s => document.querySelector(s).removeAttribute('data-shot-on'), sel);
  }
  fs.writeFileSync(path.join(HERE, 'dump.json'), JSON.stringify(dump, null, 1));
  const n = t => dump.items.filter(i => i.type === t).length;
  console.log(`items ${dump.items.length}: text ${n('text')}, shape ${n('shape')}, image ${n('image')}, line ${n('line')}`);
  await browser.close();
})();
