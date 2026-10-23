"""Orphan check on the LibreOffice render of the PPTX: last line of each wrapped text box vs its width."""
import json, re, sys, zipfile
import pymupdf as fitz
pptx, pdf = sys.argv[1], sys.argv[2]
xml = zipfile.ZipFile(pptx).read('ppt/slides/slide1.xml').decode()
EMU = 914400
boxes = []
for sp in re.findall(r'<p:sp>.*?</p:sp>', xml, flags=re.S):
    if 'wrap="square"' not in sp: continue
    nm = re.search(r'name="([^"]*)"', sp).group(1)
    off = re.search(r'<a:off x="(\d+)" y="(\d+)"/><a:ext cx="(\d+)" cy="(\d+)"', sp)
    x, y, w, h = [int(v) / EMU * 72 for v in off.groups()]
    boxes.append(dict(name=nm, x=x, y=y, w=w, h=h, lines=[]))
page = fitz.open(pdf)[0]
for b in page.get_text('dict')['blocks']:
    for ln in b.get('lines', []):
        x0, y0, x1, y1 = ln['bbox']; cy = (y0 + y1) / 2
        for bx in boxes:
            if bx['x'] - 2 <= x0 and x1 <= bx['x'] + bx['w'] + 4 and bx['y'] - 6 <= cy <= bx['y'] + bx['h'] + 30:
                bx['lines'].append((round(cy), x0, x1)); break
bad = 0
for bx in boxes:
    rows = {}
    for cy, x0, x1 in bx['lines']:
        k = next((r for r in rows if abs(r - cy) < 6), cy)
        a, c = rows.get(k, (1e9, -1e9)); rows[k] = (min(a, x0), max(c, x1))
    if len(rows) < 2: continue
    ks = sorted(rows); last = rows[ks[-1]]
    fill = (last[1] - last[0]) / bx['w']
    if fill < 0.3:
        bad += 1; print(f"ORPHAN fill={fill:.2f} lines={len(ks)} {bx['name']}")
print(len(boxes), 'wrapped boxes,', bad, 'orphans in LibreOffice render')
