// Build the editable 80 x 100 cm PowerPoint source of the poster from dump.json.
// usage: node build_pptx.js [out.pptx]
const path = require('path');
const fs = require('fs');
const pptxgen = require('pptxgenjs');
const sharp = require('sharp');
const JSZip = require(require.resolve('jszip', { paths: [path.dirname(require.resolve('pptxgenjs')), '/opt/npm-tools/node_modules'] }));

const HERE = __dirname;
const OUT = process.argv[2] || path.join(HERE, 'LightCheck-KM_poster_80x100_editable.pptx');
const dump = JSON.parse(fs.readFileSync(path.join(HERE, 'dump.json'), 'utf8'));
const SLIDE_W = 80 / 2.54, SLIDE_H = 100 / 2.54;          // exactly 80 x 100 cm
const SC = SLIDE_W / (dump.W / 96);                       // CSS px -> in (2268 pt page -> 80 cm)
const I = px => +(px / 96 * SC).toFixed(4);
const PT = px => px * 0.75;

function face(fam, weight) {
  const f = (fam || '').toLowerCase();
  if (f === 'kanit') return weight >= 700 ? ['Kanit', true] : weight >= 600 ? ['Kanit SemiBold', false] : ['Kanit Medium', false];
  if (f.includes('times')) return ['Times New Roman', weight >= 600];
  if (f.includes('arial') || f.includes('helvetica')) return ['Arial', weight >= 600];
  // Plex (IBM Plex Sans Thai)
  return weight >= 700 ? ['IBM Plex Sans Thai', true] : weight >= 600 ? ['IBM Plex Sans Thai SemiBold', false]
    : weight >= 500 ? ['IBM Plex Sans Thai Medium', false] : ['IBM Plex Sans Thai', false];
}

function runs(paras) {
  const out = [];
  paras.forEach((p, pi) => {
    const last = pi === paras.length - 1;
    if (!p.length) { out.push({ text: '', options: { breakLine: !last } }); return; }
    p.forEach((r, ri) => {
      const [ff, bold] = face(r.fam, r.weight);
      const o = { fontFace: ff, fontSize: r.size, bold, italic: !!r.italic, color: r.color };
      if (r.sub) o.subscript = true;
      if (r.sup) o.superscript = true;
      if (r.highlight) o.highlight = r.highlight;
      if (r.spacing) o.charSpacing = r.spacing;
      if (r.link) { o.hyperlink = { url: r.link, tooltip: r.link }; o.underline = { style: 'none' }; }
      o.lang = /[฀-๿]/.test(r.text) ? 'th-TH' : 'en-US';
      if (ri === p.length - 1 && !last) o.breakLine = true;
      out.push({ text: r.text, options: o });
    });
  });
  return out;
}

const NOTES = `ไฟล์ต้นฉบับโปสเตอร์ LightCheck KM (Silpakorn KM Day 2569) ขนาด 80 × 100 ซม.

ก่อนแก้ไข: ติดตั้งฟอนต์ Kanit และ IBM Plex Sans Thai ทุกไฟล์ในโฟลเดอร์ fonts (คลิกขวา > Install for all users) แล้วเปิดไฟล์นี้ใหม่
ถ้าไม่ติดตั้ง PowerPoint จะใช้ฟอนต์อื่นแทนและข้อความอาจล้นกรอบ

ใส่/เปลี่ยนรูป: คลิกขวาที่รูป > Change Picture > From a File (เช่น "ภาพที่ 5 ..." กรอบประ) แล้วใช้ Crop > Fill ถ้าสัดส่วนไม่ตรง
แก้ข้อความ: คลิกที่ข้อความแล้วพิมพ์ทับได้เลย ทุกกล่องเป็น text box จริง (ดูชื่อวัตถุทั้งหมดที่ Home > Arrange > Selection Pane)
ส่วนที่เป็นรูปภาพ: ผังวงจร กราฟ กล่องพิมพ์ 3 มิติ โลโก้ QR และสมการ (แก้สมการที่ poster/build_poster.py ใน repository)

ส่งออก PDF: File > Export > Create PDF/XPS > Options: เลือกเฉพาะสไลด์นี้, Optimize for: Standard
ถ้าต้องส่งเป็น CMYK: python poster/pdf_to_cmyk.py โปสเตอร์.pdf โปสเตอร์_CMYK.pdf 200 (ดู poster/README.md)
ส่งให้เพื่อนแก้ต่อ: File > Options > Save > Embed fonts in the file (ฟอนต์ทั้งสองเป็น OFL ฝังได้)`;

(async () => {
  const pres = new pptxgen();
  pres.defineLayout({ name: 'POSTER_80x100', width: SLIDE_W, height: SLIDE_H });
  pres.layout = 'POSTER_80x100';
  pres.title = 'LightCheck KM poster 80x100 cm (Silpakorn KM Day 2569)';
  pres.author = 'ว่าที่ ร.ต. ดร. บรรพต ดลวิทยากุล';
  pres.company = 'สำนักดิจิทัลเทคโนโลยี มหาวิทยาลัยศิลปากร';
  pres.subject = 'Editable poster source';
  pres.theme = { headFontFace: 'Kanit SemiBold', bodyFontFace: 'IBM Plex Sans Thai' };
  const slide = pres.addSlide();
  slide.background = { color: 'FFFFFF' };
  slide.addNotes(NOTES);

  const hang = {};       // text box name -> hanging indent (EMU)
  const round = {};      // picture name -> corner radius (EMU ratio applied in post-processing)
  const usedNames = {};
  const uniq = n => { usedNames[n] = (usedNames[n] || 0) + 1; return usedNames[n] > 1 ? `${n} #${usedNames[n]}` : n; };
  const cropDir = path.join(HERE, 'media');

  for (const it of dump.items) {
    let base = it.name || it.type;
    if (it.type === 'text' && !/^วงจร KM/.test(base)) {
      const t = it.paras.map(p => p.map(r => r.text).join('')).join(' ').replace(/\s+/g, ' ').trim();
      base = 'ข้อความ: ' + (t.length > 34 ? t.slice(0, 34) + '…' : t);
    } else if (it.type === 'shape' && !/^วงจร KM/.test(base)) {
      const LABEL = { bar: 'แถบสีหัวโปสเตอร์', fbar: 'แถบสีท้ายโปสเตอร์', vdiv: 'เส้นแบ่งคอลัมน์', rule: 'เส้นใต้หัวข้อ', kpi: 'กล่อง KPI',
        box: 'กล่องพื้นหลัง', fx: 'กล่องสูตร', b: 'แท่งเทียบราคา', stats: 'เส้นคั่นสถิติ', s: 'กล่องขั้นตอน' };
      const cls = (base.split(' .')[1] || '').split('.');
      const key = ['fbar', 'bar', 'vdiv', 'rule', 'kpi', 'fx', 'stats', 'box', 'b', 's'].find(k => cls.includes(k));
      base = (key ? LABEL[key] : 'กรอบ') + (/\(\d\)$/.test(base) ? ' ' + base.match(/\(\d\)$/)[0] : '');
    }
    const name = uniq(base);
    if (it.type === 'shape') {
      const shape = it.ellipse ? pres.shapes.OVAL : it.radius > 0.5 ? pres.shapes.ROUNDED_RECTANGLE : pres.shapes.RECTANGLE;
      const o = { x: I(it.x), y: I(it.y), w: I(it.w), h: I(it.h), objectName: name,
        fill: it.fill ? { color: it.fill } : { type: 'none' },
        line: it.line ? { color: it.line.color, width: it.line.width, dashType: it.line.dash || 'solid' } : { type: 'none' } };
      if (shape === pres.shapes.ROUNDED_RECTANGLE) o.rectRadius = I(Math.min(it.radius, it.w / 2, it.h / 2));
      slide.addShape(shape, o);
    } else if (it.type === 'line') {
      const x = Math.min(it.x1, it.x2), y = Math.min(it.y1, it.y2);
      slide.addShape(pres.shapes.LINE, { x: I(x), y: I(y), w: I(Math.abs(it.x2 - it.x1)), h: I(Math.abs(it.y2 - it.y1)),
        flipH: it.x2 < it.x1, flipV: it.y2 < it.y1, objectName: name,
        line: { color: it.color, width: it.width, endArrowType: it.arrow ? 'triangle' : undefined } });
    } else if (it.type === 'image') {
      let file = it.file || it.src;
      if (it.src && it.fit === 'cover') {          // pre-crop like CSS object-fit: cover (centre)
        const [nw, nh] = it.nat, ar = it.w / it.h;
        let cw = nw, ch = Math.round(nw / ar);
        if (ch > nh) { ch = nh; cw = Math.round(nh * ar); }
        file = path.join(cropDir, 'photo_' + path.basename(it.src).replace(/\.\w+$/, '.jpg'));
        await sharp(it.src).extract({ left: Math.round((nw - cw) / 2), top: Math.round((nh - ch) / 2), width: cw, height: ch })
          .jpeg({ quality: 92 }).toFile(file);
      }
      const o = { path: file, x: I(it.x), y: I(it.y), w: I(it.w), h: I(it.h), objectName: name, altText: name };
      if (it.link) o.hyperlink = { url: it.link, tooltip: it.link };
      slide.addImage(o);
      if (it.radius > 0.5) round[name] = Math.min(it.radius / Math.min(it.w, it.h), 0.5);
    } else if (it.type === 'text') {
      const pad = it.wrap ? it.w * 0.02 : 0;          // a little slack for PowerPoint's own Thai line breaking
      let x = it.x, w = it.w;
      if (it.indent < 0) { x += it.indent; w -= it.indent; hang[name] = Math.round(-it.indent / 96 * SC * 914400); }
      if (pad && !it.shape) { if (it.align === 'center') { x -= pad / 2; w += pad; } else if (it.align === 'right') { x -= pad; w += pad; } else w += pad; }
      const o = { x: I(x), y: I(it.y), w: I(w), h: I(Math.max(it.h, 4)), objectName: name, isTextBox: true,
        align: ['left', 'center', 'right', 'justify'].includes(it.align) ? it.align : 'left', valign: it.valign || 'top',
        wrap: !!it.wrap, fit: 'none', margin: 0 };
      if (it.lineHeight) o.lineSpacing = +PT(it.lineHeight).toFixed(2);
      if (it.shape) {
        o.shape = it.shape.ellipse ? pres.shapes.OVAL : it.shape.radius > 0.5 ? pres.shapes.ROUNDED_RECTANGLE : pres.shapes.RECTANGLE;
        if (o.shape === pres.shapes.ROUNDED_RECTANGLE) o.rectRadius = I(Math.min(it.shape.radius, it.w / 2, it.h / 2));
        o.fill = it.shape.fill ? { color: it.shape.fill } : { type: 'none' };
        o.line = it.shape.line ? { color: it.shape.line.color, width: it.shape.line.width, dashType: it.shape.line.dash || 'solid' } : { type: 'none' };
        const ins = it.ins || { l: 0, r: 0, t: 0, b: 0 };
        o.margin = [PT(ins.l), PT(ins.r), PT(ins.b), PT(ins.t)].map(v => +v.toFixed(2));
        delete o.isTextBox;
      }
      slide.addText(runs(it.paras), o);
    }
  }
  await pres.writeFile({ fileName: OUT });

  // ---- post-process the package
  const zip = await JSZip.loadAsync(fs.readFileSync(OUT));
  const sp = 'ppt/slides/slide1.xml';
  let xml = await zip.file(sp).async('string');
  xml = xml.replace(/baseline="-40000"/g, 'baseline="-25000"').replace(/baseline="30000"/g, 'baseline="30000"');
  xml = xml.replace(/<a:tailEnd type="triangle"\/>/g, '<a:tailEnd type="triangle" w="med" len="med"/>');
  // rounded picture frames (keep the shape when the user does Change Picture)
  xml = xml.replace(/<p:pic>[\s\S]*?<\/p:pic>/g, pic => {
    const m = /<p:cNvPr [^>]*name="([^"]*)"/.exec(pic);
    if (!m) return pic;
    const nm = m[1].replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
    if (!(nm in round)) return pic;
    const adj = Math.round(round[nm] * 100000);
    return pic.replace(/<a:prstGeom prst="rect">\s*<a:avLst\s*\/>\s*<\/a:prstGeom>/, `<a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val ${adj}"/></a:avLst></a:prstGeom>`);
  });
  xml = xml.replace(/<p:sp>[\s\S]*?<\/p:sp>/g, shp => {
    const m = /<p:cNvPr [^>]*name="([^"]*)"/.exec(shp);
    const nm = m && m[1].replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
    if (!nm || !(nm in hang)) return shp;
    return shp.replace(/indent="0" marL="0"/g, `indent="-${hang[nm]}" marL="${hang[nm]}"`);
  });
  zip.file(sp, xml);
  // theme: Thai script fonts for new text boxes the user adds
  const tp = Object.keys(zip.files).find(f => /^ppt\/theme\/theme\d+\.xml$/.test(f));
  let th = await zip.file(tp).async('string');
  th = th.replace(/(<a:majorFont>[\s\S]*?)<a:cs typeface="[^"]*"\/>/, '$1<a:cs typeface="Kanit SemiBold"/>')
    .replace(/(<a:minorFont>[\s\S]*?)<a:cs typeface="[^"]*"\/>/, '$1<a:cs typeface="IBM Plex Sans Thai"/>')
    .replace(/(<a:majorFont>[\s\S]*?)<a:font script="Thai" typeface="[^"]*"\/>/, '$1<a:font script="Thai" typeface="Kanit SemiBold"/>')
    .replace(/(<a:minorFont>[\s\S]*?)<a:font script="Thai" typeface="[^"]*"\/>/, '$1<a:font script="Thai" typeface="IBM Plex Sans Thai"/>')
    .replace(/<a:hlink>[\s\S]*?<\/a:hlink>/, '<a:hlink><a:srgbClr val="2163A1"/></a:hlink>')
    .replace(/<a:folHlink>[\s\S]*?<\/a:folHlink>/, '<a:folHlink><a:srgbClr val="2163A1"/></a:folHlink>');
  zip.file(tp, th);
  fs.writeFileSync(OUT, await zip.generateAsync({ type: 'nodebuffer', compression: 'DEFLATE' }));
  console.log('wrote', OUT, (fs.statSync(OUT).size / 1e6).toFixed(1), 'MB; rounded pictures:', Object.keys(round).length);
})();
