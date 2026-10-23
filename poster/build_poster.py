"""Build poster.html (80 x 100 cm, Silpakorn KM Day 2569 template) from repo results."""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
S = json.load(open(f"{REPO}/calibration/sim/montecarlo_summary.json", encoding="utf-8"))
T = json.load(open(f"{REPO}/tools/survey/office_twin_result.json", encoding="utf-8"))
STATS = json.load(open(f"{REPO}/tools/repo_stats.json"))

u95 = S["guard_band_pct"]
mape_raw = S["m_raw_ref"]["mape"]["p50"]
mape_cor = S["m_cor_ref"]["mape"]["p50"]
mape_cor95 = S["m_cor_ref"]["mape"]["p95"]
d300 = S["decision_analysis"]["300"]
a_ex, b_ex = S["representative"]["a"], S["representative"]["b"]
raw_ex = 250.0
cor_ex = a_ex * raw_ex + b_ex
tb, ta = T["scenarios"]["before"], T["scenarios"]["after"]


def km_cycle_svg():
    """Six-step KM loop drawn as a two-row cycle (fits one 630 pt column)."""
    W, H, w, h = 630, 300, 178, 84
    top = [(97, 64), (315, 64), (533, 64)]
    bot = [(533, 236), (315, 236), (97, 236)]
    nodes = [("วางแผน", "P · เกณฑ์ + จุดวัด"), ("ตรวจวัด", "D · pre-survey"), ("ตรวจสอบ", "C · ยืนยันผล"),
             ("ปรับปรุง", "A · แก้ + ตรวจซ้ำ"), ("ถอดบทเรียน", "KM · บทเรียน"), ("ใช้ซ้ำ", "KM · public repo")]
    pos = top + bot
    o = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" class="kmcycle">',
         '<defs><marker id="ah" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">'
         '<path d="M0 0L10 5L0 10z" fill="#2163A1"/></marker></defs>']
    def arrow(x1, y1, x2, y2):
        o.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#2163A1" stroke-width="5" marker-end="url(#ah)"/>')
    arrow(97 + w/2 + 3, 64, 315 - w/2 - 9, 64); arrow(315 + w/2 + 3, 64, 533 - w/2 - 9, 64)
    arrow(533, 64 + h/2 + 3, 533, 236 - h/2 - 9)
    arrow(533 - w/2 - 3, 236, 315 + w/2 + 9, 236); arrow(315 - w/2 - 3, 236, 97 + w/2 + 9, 236)
    arrow(97, 236 - h/2 - 3, 97, 64 + h/2 + 9)
    for k, ((x, y), (lab, sub)) in enumerate(zip(pos, nodes)):
        col = "#00766A" if k % 2 == 0 else "#2163A1"
        o.append(f'<g transform="translate({x},{y})"><rect x="{-w/2}" y="{-h/2}" width="{w}" height="{h}" rx="18" fill="#fff" '
                 f'stroke="{col}" stroke-width="4"/><circle cx="{-w/2 + 6}" cy="{-h/2 + 6}" r="19" fill="{col}" stroke="#fff" stroke-width="3"/>'
                 f'<text x="{-w/2 + 6}" y="{-h/2 + 14}" text-anchor="middle" class="kn">{k + 1}</text>'
                 f'<text x="6" y="0" text-anchor="middle" class="kl">{lab}</text><text x="6" y="26" text-anchor="middle" class="ks">{sub}</text></g>')
    o.append('<text x="315" y="146" text-anchor="middle" class="kc1">LightCheck KM</text>'
             '<text x="315" y="176" text-anchor="middle" class="kc2">PDCA + Tacit → Explicit</text>')
    o.append('</svg>')
    return "".join(o)


ICONS = json.load(open(os.path.join(HERE, "assets", "icons.json"), encoding="utf-8"))


def icon(name, cls="ico"):
    svg = ICONS[name].replace(' height="64" width="64"', "")
    return svg.replace("<svg ", f'<svg class="{cls}" ', 1)


CAMERA = ('<svg viewBox="0 0 64 64" class="cam"><rect x="6" y="18" width="52" height="36" rx="6" fill="none" '
          'stroke="currentColor" stroke-width="4"/><path d="M22 18l4-7h12l4 7" fill="none" stroke="currentColor" '
          'stroke-width="4" stroke-linejoin="round"/><circle cx="32" cy="36" r="10" fill="none" stroke="currentColor" '
          'stroke-width="4"/></svg>')

html = f"""<!doctype html>
<html lang="th"><head><meta charset="utf-8"><title>LightCheck KM poster</title>
<style>
@font-face{{font-family:Plex;src:url(../tools/fonts/IBMPlexSansThai-Regular.ttf);font-weight:400}}
@font-face{{font-family:Plex;src:url(../tools/fonts/IBMPlexSansThai-Medium.ttf);font-weight:500}}
@font-face{{font-family:Plex;src:url(../tools/fonts/IBMPlexSansThai-SemiBold.ttf);font-weight:600}}
@font-face{{font-family:Plex;src:url(../tools/fonts/IBMPlexSansThai-Bold.ttf);font-weight:700}}
@font-face{{font-family:Kanit;src:url(../tools/fonts/Kanit-Medium.ttf);font-weight:500}}
@font-face{{font-family:Kanit;src:url(../tools/fonts/Kanit-SemiBold.ttf);font-weight:600}}
@font-face{{font-family:Kanit;src:url(../tools/fonts/Kanit-Bold.ttf);font-weight:700}}
@page{{size:2268pt 2835pt;margin:0}}
:root{{--blue:#2163A1;--light:#B4D5E5;--tint:#E3EFF6;--teal:#00766A;--tealtint:#DFF0EC;--orange:#E0601A;
--orangetint:#FDEBDF;--ink:#14202B;--ink2:#4A5866;--rule:#2163A1}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:2268pt;height:2835pt;background:#fff;color:var(--ink);font-family:Plex,sans-serif;
-webkit-print-color-adjust:exact;print-color-adjust:exact}}
body{{position:relative;overflow:hidden;font-size:23pt;line-height:1.4}}
.abs{{position:absolute}}
/* ---------- header (template) ---------- */
.seal{{left:74pt;top:53pt;width:299pt;height:299pt}}
.title{{left:420pt;width:1428pt;top:30pt;text-align:center}}
.t1{{font-family:Kanit;font-weight:600;font-size:104pt;line-height:1.05;letter-spacing:-0.5pt}}
.t1 .km{{color:var(--teal)}}
.t2{{font-family:Kanit;font-weight:500;font-size:47pt;line-height:1.22;margin-top:4pt}}
.t3{{font-family:Plex;font-weight:600;font-size:36pt;margin-top:14pt;color:#2b2b2b}}
.t4{{font-family:Plex;font-weight:500;font-size:28pt;color:#3d3d3d;margin-top:0pt}}
.logo{{left:1870pt;top:70pt;width:345pt}}
.tag{{left:1862pt;top:322pt;width:360pt;text-align:center}}
.pill{{display:inline-block;background:var(--blue);color:#fff;border-radius:40pt;padding:5pt 16pt;font-weight:600;
font-size:17pt;line-height:1.3;white-space:nowrap}}
.pill.t{{background:var(--teal)}}
.bar{{left:0;width:2268pt;top:379pt;height:31pt;background:var(--blue)}}
.fbar{{left:0;width:2268pt;top:2650pt;height:12pt;background:var(--blue)}}
.foot{{font-family:Arial,Helvetica,sans-serif;font-weight:700;font-style:italic;font-size:30pt;line-height:1}}
.vdiv{{top:455pt;height:2160pt;width:3pt;background:var(--light)}}
/* ---------- columns ---------- */
.col{{top:438pt;width:630pt;height:2195pt;display:flex;flex-direction:column}}
.c1{{left:63pt}}.c2{{left:819pt}}.c3{{left:1579pt}}
.col>*{{flex-shrink:0}}
h2{{font-family:Kanit;font-weight:600;font-size:56pt;line-height:1.0;text-align:center;letter-spacing:1pt}}
h2 small{{display:block;font-family:Plex;font-weight:500;font-size:23pt;letter-spacing:0;color:var(--ink2);margin-top:6pt}}
.rule{{height:7pt;background:var(--rule);margin:12pt 0 18pt}}
h3{{font-family:Kanit;font-weight:600;font-size:29pt;line-height:1.15;color:var(--blue);margin:12pt 0 6pt}}
h3 .n{{display:inline-block;background:var(--blue);color:#fff;border-radius:50%;width:40pt;height:40pt;text-align:center;
line-height:40pt;font-size:24pt;margin-right:10pt;vertical-align:2pt}}
p{{margin:0 0 10pt}}
.hook{{font-family:Kanit;font-weight:600;font-size:40pt;line-height:1.2;color:var(--teal);margin:2pt 0 10pt}}
.box{{background:var(--light);border-radius:14pt;padding:18pt 22pt;margin:8pt 0 10pt}}
.box.tint{{background:var(--tint)}}
.box.teal{{background:var(--tealtint)}}
.box.orange{{background:var(--orangetint);border-left:10pt solid var(--orange)}}
.crit{{display:grid;grid-template-columns:0.9fr 0.9fr 1.45fr;gap:8pt;text-align:center}}
.big{{font-family:Kanit;font-weight:600;font-size:66pt;line-height:1;color:var(--blue)}}
.big.t{{color:var(--teal)}}.big.o{{color:var(--orange)}}
.unit{{font-family:Kanit;font-weight:500;font-size:26pt;color:var(--ink2)}}
.lbl{{font-size:19.5pt;line-height:1.3;color:var(--ink)}}
.src{{font-size:17pt;color:var(--ink2);line-height:1.35;margin-top:10pt}}
ol.obj{{list-style:none;counter-reset:o}}
ol.obj li{{counter-increment:o;position:relative;padding-left:52pt;margin-bottom:6pt;font-size:22pt;line-height:1.36}}
ol.obj .num{{position:absolute;left:0;top:2pt;width:38pt;height:38pt;border-radius:50%;
background:var(--teal);color:#fff;font-family:Kanit;font-weight:600;font-size:23pt;text-align:center;line-height:38pt}}
.cap{{font-size:17pt;line-height:1.33;color:var(--ink2);margin:4pt 0 4pt}}
.cap b{{color:var(--ink)}}
.kmcycle{{width:567pt;height:270pt;display:block;margin:2pt auto}}
.kmcycle .kl{{font-family:Kanit;font-weight:600;font-size:23pt;fill:var(--ink)}}
.kmcycle .ks{{font-family:Plex;font-weight:500;font-size:15pt;fill:var(--ink2)}}
.kmcycle .kn{{font-family:Kanit;font-weight:600;font-size:22pt;fill:#fff}}
.kmcycle .kc1{{font-family:Kanit;font-weight:600;font-size:30pt;fill:var(--teal)}}
.kmcycle .kc2{{font-family:Plex;font-weight:600;font-size:17pt;fill:var(--ink)}}
.kmcycle .kc3{{font-family:Plex;font-weight:500;font-size:14.5pt;fill:var(--ink2)}}
.comps{{display:grid;grid-template-columns:1fr 0.82fr 1.35fr;gap:12pt;align-items:end;text-align:center}}
.comps img{{width:100%;display:block;margin:0 auto 6pt}}
.comps img.ph2{{border-radius:10pt;height:150pt;object-fit:cover}}
.credit{{font-size:13pt;color:var(--ink2);margin-top:4pt;text-align:right}}
.comps .nm{{font-family:Kanit;font-weight:600;font-size:21pt;line-height:1.15}}
.comps .pr{{font-size:19pt;color:var(--ink2)}}
.cost{{margin-top:12pt}}
.cost .row{{display:flex;align-items:center;gap:12pt;margin:6pt 0}}
.cost .nm{{width:170pt;font-size:19pt;font-weight:600;line-height:1.2}}
.cost .tr{{flex:1;height:30pt;position:relative}}
.cost .b{{height:30pt;border-radius:0 6pt 6pt 0}}
.cost .v{{font-size:19pt;font-weight:600;white-space:nowrap}}
.wide{{width:630pt;display:block}}
.ph{{border:4pt dashed #8FB2C9;border-radius:14pt;background:#F4F8FB;display:flex;flex-direction:column;align-items:center;
justify-content:center;text-align:center;color:#56708A;font-size:20pt;line-height:1.3;padding:14pt}}
.ph .cam{{width:70pt;height:70pt;color:#7E9DB6;margin-bottom:8pt}}
.ph b{{font-family:Kanit;font-weight:600;font-size:23pt;color:#3E5C77}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:20pt}}
ul.alg{{list-style:none}}
ul.alg li{{display:flex;gap:12pt;margin-bottom:5pt;font-size:20pt;line-height:1.3}}
ul.alg li .k{{flex:0 0 36pt;height:36pt;border-radius:9pt;background:var(--blue);color:#fff;font-family:Kanit;
font-weight:600;font-size:21pt;text-align:center;line-height:36pt;margin-top:2pt}}
ul.alg li .k.t{{background:var(--teal)}}
.eq{{font-family:Plex;font-size:23pt}}
.eqmain{{background:#fff;border:4pt solid var(--teal);border-radius:12pt;padding:8pt 10pt;text-align:center;
font-family:Kanit;font-weight:500;font-size:44pt;line-height:1.1;color:var(--ink);margin:4pt 0 8pt}}
.eqmain .v{{color:var(--teal);font-weight:600}}
.frac{{display:inline-flex;flex-direction:column;vertical-align:middle;text-align:center;margin:0 4pt}}
.frac>span:first-child{{border-bottom:2.4pt solid currentColor;padding:0 6pt 2pt}}
.frac>span:last-child{{padding:2pt 6pt 0}}
.eqrow{{display:flex;align-items:center;gap:8pt;margin:6pt 0;font-size:22pt;line-height:1.25;flex-wrap:wrap}}
.eqrow .lhs{{font-weight:600;white-space:nowrap}}
.mi{{font-style:italic;font-family:'Times New Roman',serif;font-size:1.12em}}
sub{{font-size:0.62em;vertical-align:-0.25em;font-style:normal}}
.chain{{display:flex;align-items:center;justify-content:space-between;gap:4pt;font-size:17pt;text-align:center;line-height:1.2;
margin:2pt 0 6pt}}
.chain .s{{background:#fff;border:2pt solid var(--blue);border-radius:9pt;padding:6pt 8pt;flex:1}}
.chain .ar{{color:var(--blue);font-weight:700;font-size:22pt}}
.ex{{font-size:19.5pt;line-height:1.35;color:var(--ink);margin-top:6pt}}
.kpis{{display:grid;grid-template-columns:1fr 1fr;gap:14pt;margin:6pt 0 8pt}}
.kpi{{background:var(--tint);border-radius:14pt;padding:10pt 14pt 10pt;border-top:8pt solid var(--blue)}}
.kpi.t{{border-top-color:var(--teal)}}.kpi.o{{border-top-color:var(--orange)}}
.kpi .big{{font-size:54pt}}
.kpi .arrow{{font-size:34pt;color:var(--ink2);font-family:Kanit;font-weight:500}}
.kpi .from{{font-family:Kanit;font-weight:600;font-size:40pt;color:var(--ink2)}}
.kpi .lbl{{font-size:17pt;margin-top:2pt;line-height:1.28}}
.lead{{font-size:20.5pt;line-height:1.36}}
.sim{{display:inline-block;background:#FFF2C4;color:#6B5200;border-radius:8pt;padding:1pt 10pt;font-size:17pt;font-weight:600}}
ol.conc{{list-style:none;counter-reset:c}}
ol.conc li{{counter-increment:c;position:relative;padding-left:46pt;margin-bottom:6pt;font-size:21pt;line-height:1.34}}
ol.conc .num{{position:absolute;left:0;top:-4pt;font-family:Kanit;font-weight:600;font-size:30pt;line-height:1.34;
color:var(--blue)}}
.diss{{display:grid;grid-template-columns:236pt 1fr;gap:16pt;align-items:center}}
.diss img{{width:236pt;height:236pt;display:block;border-radius:6pt}}
ol.steps{{list-style:none;counter-reset:st}}
ol.steps li{{counter-increment:st;position:relative;padding-left:40pt;margin:0 0 7pt;font-size:18.5pt;line-height:1.28}}
ol.steps .num{{position:absolute;left:0;top:1pt;width:30pt;height:30pt;border-radius:50%;
background:var(--teal);color:#fff;font-family:Kanit;font-weight:600;font-size:18pt;text-align:center;line-height:30pt}}
.url{{font-family:Kanit;font-weight:600;font-size:27pt;color:var(--blue);line-height:1.2}}
.diss ul{{list-style:none;font-size:19pt;line-height:1.36;margin-top:6pt}}
.stats{{display:flex;justify-content:space-between;text-align:center;margin-top:10pt;padding-top:10pt;border-top:2pt solid #fff}}
.stats .big{{font-size:40pt}}
.stats .lbl{{font-size:16pt}}
.refs{{display:grid;grid-template-columns:1fr 1fr;gap:3pt 18pt;font-size:14.5pt;line-height:1.28;color:var(--ink)}}
.refs div{{padding-left:24pt;text-indent:-24pt}}
.cta{{background:var(--teal);color:#fff;border-radius:12pt;padding:10pt 16pt;font-size:20pt;font-weight:600;line-height:1.3;
margin-top:10pt;text-align:center}}
.grow{{flex:1}}
.harms{{display:grid;grid-template-columns:repeat(4,1fr);gap:10pt;margin:2pt 0 9pt}}
.harm{{background:var(--orangetint);border-radius:12pt;padding:8pt 8pt;display:flex;align-items:center;gap:6pt}}
.harm .ico{{width:28pt;height:28pt;color:var(--orange);flex:0 0 28pt}}
.harm div{{font-family:Kanit;font-weight:500;font-size:16.5pt;line-height:1.2;color:var(--ink)}}
.lesson{{display:grid;grid-template-columns:40pt 1fr;gap:10pt;align-items:center}}
.lesson .ico{{width:40pt;height:40pt;color:var(--teal)}}
.open{{background:var(--tealtint);border-radius:14pt;padding:12pt 18pt;margin-top:10pt}}
.open h4{{font-family:Kanit;font-weight:600;font-size:23pt;line-height:1.2;color:var(--teal)}}
.open ul{{list-style:none;display:grid;grid-template-columns:1fr 1fr;gap:2pt 16pt;font-size:17.5pt;line-height:1.3;margin-top:4pt}}
.open li::before{{content:none}}
.fx{{display:grid;grid-template-columns:150pt 1fr;gap:12pt;align-items:center;background:#fff;border-radius:10pt;padding:8pt 12pt;margin-top:8pt}}
.fxh{{font-family:Kanit;font-weight:600;font-size:18pt;line-height:1.2;color:var(--orange)}}
.fxe{{font-size:24pt;line-height:1.2}}
.fxx{{font-size:16.5pt;color:var(--ink2);margin-top:4pt}}
</style></head><body>

<img class="abs seal" src="assets/su_seal.png" alt="">
<div class="abs title">
  <div class="t1">LightCheck <span class="km">KM</span></div>
  <div class="t2">จากเครื่องวัดแสงต้นทุนต่ำ สู่ระบบความรู้<br>เพื่อยกระดับสภาพแวดล้อมสำนักงานสีเขียว</div>
  <div class="t3">ว่าที่ ร.ต. ดร. บรรพต ดลวิทยากุล</div>
  <div class="t4">ฝ่ายบริหารและพัฒนาดิจิทัลเทคโนโลยี สำนักดิจิทัลเทคโนโลยี มหาวิทยาลัยศิลปากร</div>
</div>
<img class="abs logo" src="assets/bdt_logo_stacked.svg" alt="" style="width:236pt;left:1924pt;top:90pt">
<div class="abs tag"><span class="pill">KM · ด้านการบริหารจัดการและสร้างนวัตกรรม</span></div>
<div class="abs bar"></div>
<div class="abs vdiv" style="left:755pt"></div><div class="abs vdiv" style="left:1511pt"></div>

<!-- ================= COLUMN 1 ================= -->
<div class="abs col c1">
  <h2>INTRODUCTION<small>ที่มาและความสำคัญ</small></h2><div class="rule"></div>
  <div class="hook">“รู้สึกว่าพอ” อาจไม่พอ<br>สำหรับสายตาคนทำงานทั้งวัน</div>
  <p>สายตาปรับตัวกับแสงสลัวจนเราไม่ทันสังเกต แต่ต้องเพ่งอยู่ตลอดวัน ผลเสียจึงสะสมกับคนทำงาน [8,&nbsp;9]</p>
  <div class="harms">
    <div class="harm">{icon("FaEyeLowVision")}<div>ตาล้า<br>ปวดตา</div></div>
    <div class="harm">{icon("FaFaceTired")}<div>ปวดศีรษะ<br>ไมเกรน</div></div>
    <div class="harm">{icon("FaBrain")}<div>ซึม<br>สมาธิลด</div></div>
    <div class="harm">{icon("FaPersonFalling")}<div>เสี่ยง<br>อุบัติเหตุ</div></div>
  </div>
  <p>ตัวชี้วัดจึงมีที่มา: Green Office 2569 ข้อ 5.2.1 ให้<b>วัดเป็นตัวเลข</b>ทุกปีด้วยเครื่องที่สอบเทียบ
  ห้ามใช้แอปมือถือ [1] แต่เครื่องมาตรฐานที่ถูกสุด (HIOKI FT3424) ราคา 28,184&nbsp;฿ จึงมีได้ไม่กี่เครื่อง</p>
  <div class="box">
    <div class="crit">
      <div><div class="big">300<span class="unit"> lx</span></div><div class="lbl">ค่าเฉลี่ย<br>พื้นที่สำนักงาน</div></div>
      <div><div class="big">150<span class="unit"> lx</span></div><div class="lbl">จุดต่ำสุด<br>ของพื้นที่</div></div>
      <div><div class="big t" style="font-size:56pt;line-height:1.18">400–500</div><div class="lbl">lux ณ จุดทำงาน<br>(งานเขียน พิมพ์ อ่าน)</div></div>
    </div>
    <div class="src">เกณฑ์ขั้นต่ำเพื่อสายตาคนทำงาน [2] · วัดที่ระนาบ 75 ซม. ทุกช่อง 2×2 ม. และ ณ จุดทำงาน
    ในสภาพทำงานปกติ ช่วงแสงธรรมชาติน้อยที่สุด [3]</div>
  </div>
  <h3>วัตถุประสงค์</h3>
  <ol class="obj">
    <li>ให้คนทำงาน<b>ได้แสงที่เหมาะกับงานจริง</b> ด้วยเครื่องคัดกรอง (pre‑survey) ต้นทุนต่ำที่ตรวจสอบย้อนกลับได้</li>
    <li>เปลี่ยนความรู้ที่อยู่กับผู้พัฒนา ให้เป็น<b>ความรู้ขององค์กร</b>: โค้ด SOP คู่มือ ไฟล์ STL ในคลังสาธารณะ</li>
    <li>ปรับปรุงแสงด้วยข้อมูลเชิงประจักษ์ตามวงจร <b>PDCA</b> (<span style="white-space:nowrap">ตรวจ → แก้ → ตรวจซ้ำ</span>) ของ Green Office 5.2.1</li>
  </ol>
  <h3>วงจรการจัดการความรู้ (PDCA + KM)</h3>
  {km_cycle_svg()}
  <div class="cap"><b>ภาพที่ 1</b> PDCA ของการดูแลแสง + ชั้น KM ทำให้ทุกรอบกลายเป็นความรู้ขององค์กร</div>
  <h3>อุปกรณ์และต้นทุน</h3>
  <div class="comps">
    <div><img class="ph2" src="assets/photos/tsl2591_crop.jpg" alt="" data-name="รูป TSL2591"><div class="nm">TSL2591</div><div class="pr">หัวรับแสง · 200 ฿</div></div>
    <div><img class="ph2" src="assets/photos/wemos_d1_mini_front_crop.jpg" alt="" data-name="รูป Wemos D1 mini"><div class="nm">Wemos D1 mini</div><div class="pr">ESP8266 · 89 ฿</div></div>
    <div><img src="assets/component_lcd1602_front.svg" alt=""><div class="nm">LCD1602 + I²C</div><div class="pr">จอแสดงผล · 70 ฿</div></div>
  </div>
  <div class="credit">ภาพ: Adafruit Industries (CC BY-SA) · Tpkull / Wikimedia Commons (CC BY-SA 4.0)</div>
  <div class="cost">
    <div class="row"><div class="nm">LightCheck KM<br><span style="font-weight:400;color:var(--ink2)">ต้นทุนจริง</span></div>
      <div class="tr"><div class="b" style="width:1.4%;background:var(--teal)"></div></div><div class="v" style="position:absolute;left:250pt">≈ 385 ฿ <span style="font-weight:400;color:var(--ink2);font-size:16pt">(89 + 200 + 70 + PLA+ 54 g ≈ 26)</span></div></div>
    <div class="row"><div class="nm">HIOKI FT3424<br><span style="font-weight:400;color:var(--ink2)">ถูกที่สุดที่สำรวจได้</span></div>
      <div class="tr"><div class="b" style="width:100%;background:var(--blue)"></div></div><div class="v">28,184 ฿</div></div>
    <div style="font-size:14.5pt;color:var(--ink2);text-align:right;margin-top:-2pt">HIOKI FT3424 (ญี่ปุ่น, JIS C 1609-1 AA / DIN 5032-7 B) 26,340 ฿ + VAT 7% = 28,183.80 ฿ [7]</div>
  </div>
  <div class="box teal" style="margin-top:12pt">
    <div style="display:flex;align-items:center;gap:18pt"><div class="big t" style="font-size:72pt">~73×</div>
    <div style="font-size:20pt;line-height:1.33">ถูกกว่า แต่<b>ไม่ได้เทียบเท่า</b>: ต้นแบบหลายเครื่อง = คัดกรองให้ทั่ว ·
    เครื่องมาตรฐาน = ยืนยันผลทางการ</div></div>
  </div>
  <h3>ใครใช้ประโยชน์ได้อย่างไร</h3>
  <div class="two" style="gap:14pt">
    <div class="box tint" style="margin:0;padding:12pt 16pt"><div style="font-family:Kanit;font-weight:600;font-size:21pt;color:var(--teal)">คณะ / ส่วนงาน</div>
      <div style="font-size:17pt;line-height:1.33">ไม่ต้องมีพื้นฐาน: ยืมเครื่อง → จดค่าเมื่อจอขึ้น * → ส่งจุดเสี่ยงยืนยัน</div></div>
    <div class="box tint" style="margin:0;padding:12pt 16pt"><div style="font-family:Kanit;font-weight:600;font-size:21pt;color:var(--blue)">เจ้าหน้าที่เทคนิค / นักวิจัย</div>
      <div style="font-size:17pt;line-height:1.33">ต่อยอด: Wi-Fi + dashboard, เชื่อม SU Green Office, เพิ่ม CO₂/อุณหภูมิ/เสียง</div></div>
  </div>
  <div class="grow"></div>
  <h2 style="margin-top:10pt;font-size:40pt">REFERENCES</h2><div class="rule" style="margin:10pt 0 10pt"></div>
  <div class="refs">
    <div>1. ทส. (2569). เกณฑ์ Green Office ปี 2569</div>
    <div>6. Lorenzo et al. (2022). Sensors 22(19), 7107</div>
    <div>2. กสร. (2561). มาตรฐานความเข้มแสงสว่าง</div>
    <div>7. HIOKI. FT3424 Lux meter specifications</div>
    <div>3. กสร. (2561). หลักเกณฑ์การตรวจวัดแสง</div>
    <div>8. HSE (1997). Lighting at work, HSG38</div>
    <div>4. Adafruit. TSL2591 sensor guide</div>
    <div>9. CCOHS (2025). Lighting Ergonomics</div>
    <div>5. ams (2018). TSL2591 datasheet</div>
    <div>10. DOE/PNNL (2016). Photometric Flicker</div>
  </div>
</div>

<!-- ================= COLUMN 2 ================= -->
<div class="abs col c2">
  <h2>METHODS<small>แนวคิดและกระบวนการดำเนินงาน</small></h2><div class="rule"></div>
  <img class="wide" src="assets/wiring_diagram.svg" alt="" style="width:596pt;margin:0 auto">
  <div class="cap"><b>ภาพที่ 2</b> ผังวงจร: I²C ร่วม 2 สาย (SDA = D2, SCL = D1) · TSL2591 0x29 · LCD 0x3F · ไฟเลี้ยง USB-C 5 V จาก power bank</div>
  <h3>กล่องพิมพ์ 3 มิติ (ไฟล์ STL เปิดให้ดาวน์โหลด)</h3>
  <img class="wide" src="assets/enclosure_hero.png" alt="" style="width:530pt;margin:-4pt auto 0">
  <div class="cap"><b>ภาพที่ 3</b> Render จากไฟล์ STL · 108×63×26 มม. · หัวรับแสงเสมอผิวฝา ไม่มีขอบบังแสง ·
  ช่องนอต 1/4" ใต้กล่องสำหรับขาตั้งกล้องที่ระดับ 75 ซม.</div>
  <div class="two" style="margin-top:6pt">
    <div><img src="assets/photos/print_ender6.jpg" alt="" data-name="ภาพที่ 4 พิมพ์กล่อง Ender-6" style="width:100%;height:225pt;object-fit:cover;border-radius:14pt;display:block">
      <div class="cap"><b>ภาพที่ 4</b> พิมพ์ด้วย Creality Ender-6</div></div>
    <div><div class="ph" style="height:225pt" data-pptx="img" data-photo="1" data-name="ภาพที่ 5 (คลิกขวา > Change Picture เพื่อใส่รูปเครื่องจริง)">{CAMERA}<b>ใส่รูป: เครื่องต้นแบบ<br>ที่ประกอบเสร็จ</b></div>
      <div class="cap"><b>ภาพที่ 5</b> เครื่องที่ประกอบเสร็จ พร้อมใช้</div></div>
  </div>
  <h3>อัลกอริทึมใน firmware v1.1</h3>
  <ul class="alg">
    <li><span class="k">1</span><span><b>Self-check I²C</b> ก่อนวัด ป้องกันการบันทึกค่าจากระบบที่ต่อผิด</span></li>
    <li><span class="k">2</span><span><b>ตรวจ saturation</b> ตาม datasheet (36,863 / 65,535 counts)</span></li>
    <li><span class="k">3</span><span><b>Auto-range มี hysteresis</b>: 100–2,900 lx อ่านที่ gain 25× เสมอ</span></li>
    <li><span class="k t">4</span><span><b>เฉลี่ย 5 รอบ</b> ลดผล LED กะพริบ · จอแสดง <b>*</b> เมื่อค่านิ่ง (CV&nbsp;&lt;&nbsp;2%)</span></li>
    <li><span class="k t">5</span><span><b>ชดเชย + traceability</b>: บันทึก Raw/Corrected, gain และรุ่นสมการ</span></li>
  </ul>
  <div class="box teal" style="margin-top:10pt;padding:12pt 18pt">
    <div class="lesson">{icon("FaWaveSquare")}<div style="font-size:18pt;line-height:1.34"><b>บทเรียนหน้างาน:</b> LED สว่างตามขนาดกระแส
    วูบ 100 ครั้ง/วินาทีจากไฟ 50&nbsp;Hz [10] → integration 300&nbsp;ms (30 รอบพอดี) + เฉลี่ย 5 ค่า</div></div>
  </div>
  <div class="box tint grow" style="margin-top:8pt">
    <h3 style="margin-top:0">สมการชดเชยความคลาดเคลื่อน</h3>
    <div class="chain"><div class="s">ADC<br>CH<sub>0</sub>, CH<sub>1</sub></div><div class="ar">→</div>
      <div class="s">Raw Lux<br><span class="mi">E</span><sub>raw</sub></div><div class="ar">→</div>
      <div class="s">เฉลี่ย 5 ค่า<br><span class="mi">Ē</span><sub>raw</sub></div><div class="ar">→</div>
      <div class="s" style="border-color:var(--teal)">ค่าหลังชดเชย<br><span class="mi">E</span><sub>corr</sub></div></div>
    <div class="eqmain" data-pptx="img" data-name="สมการชดเชย (หลัก)"><span class="mi">E</span><sub>corrected</sub> = <span class="v mi">a</span> · <span class="mi">Ē</span><sub>raw</sub> + <span class="v mi">b</span></div>
    <div class="eqrow" data-pptx="img" data-name="สมการ Raw lux และ CPL"><span class="lhs"><span class="mi">E</span><sub>raw</sub> =</span>
      <span class="frac"><span>(CH<sub>0</sub> − CH<sub>1</sub>)(1 − CH<sub>1</sub>/CH<sub>0</sub>)</span><span>CPL</span></span>
      <span>, &nbsp;CPL = <span class="frac"><span><span class="mi">t</span><sub>int</sub> · <span class="mi">G</span></span><span>408</span></span></span></div>
    <div class="eqrow" data-pptx="img" data-name="สมการ a และ b (least squares)"><span class="lhs"><span class="mi">a</span> =</span>
      <span class="frac"><span>Σ(<span class="mi">x<sub>i</sub></span> − <span class="mi">x̄</span>)(<span class="mi">y<sub>i</sub></span> − <span class="mi">ȳ</span>)</span><span>Σ(<span class="mi">x<sub>i</sub></span> − <span class="mi">x̄</span>)²</span></span>
      <span>, &nbsp;<span class="mi">b</span> = <span class="mi">ȳ</span> − <span class="mi">a</span><span class="mi">x̄</span></span></div>
    <div class="ex"><span class="mi">x</span> = Raw ของต้นแบบ, <span class="mi">y</span> = ค่าเครื่องอ้างอิงที่มีใบสอบเทียบ (fit ด้วย least squares,
    ทดสอบบนชุด validation) · <span class="mi">t</span><sub>int</sub>&nbsp;=&nbsp;300&nbsp;ms · <span class="mi">G</span>&nbsp;=&nbsp;25</div>
    <div class="ex" style="margin-top:8pt"><span class="sim">ตัวอย่างผลจำลอง</span> <span class="mi">a</span> = {a_ex:.3f},
    <span class="mi">b</span> = {'−' if b_ex < 0 else ''}{abs(b_ex):.1f} lx: Raw {raw_ex:.0f} lx ⇒ <span class="mi">E</span><sub>corr</sub> = {a_ex:.3f}×{raw_ex:.0f} {'−' if b_ex < 0 else '+'} {abs(b_ex):.1f}
    = <b>{cor_ex:.1f} lx</b> อยู่ในช่วงยืนยันของเกณฑ์ 400 lx ({400*(1-u95/100):.0f}–{400*(1+u95/100):.0f} lx) → วัดซ้ำด้วยเครื่องมาตรฐาน</div>
  </div>
</div>

<!-- ================= COLUMN 3 ================= -->
<div class="abs col c3">
  <h2>RESULTS<small>ผลลัพธ์จากการจัดการความรู้</small></h2><div class="rule"></div>
  <div class="lead">ยังไม่มีข้อมูลวัดคู่จริง จึงประเมินด้วย<b>วิธีเชิงอัลกอริทึม</b>: Monte Carlo {S['n_campaigns']:,} รอบ
  จาก datasheet TSL2591 + สเปก Hioki FT3424 (±2% rdg.) <span class="sim">ผลจำลอง</span></div>
  <div class="kpis">
    <div class="kpi t"><div class="big t">±{u95:.1f}%</div><div class="lbl">ความคลาดเคลื่อน (95%) หลังชดเชย เทียบกับค่าจริง</div></div>
    <div class="kpi"><div><span class="from">{mape_raw:.0f}%</span><span class="arrow"> → </span><span class="big">{mape_cor:.1f}%</span></div>
      <div class="lbl">MAPE ก่อน → หลังชดเชย (P95 หลังชดเชย {mape_cor95:.1f}%)</div></div>
    <div class="kpi o"><div><span class="from">{d300['wrong_raw_pct']:.0f}%</span><span class="arrow"> → </span><span class="big o">{d300['wrong_decisions_after_guard_band_pct']:.2f}%</span></div>
      <div class="lbl">ตัดสินผ่าน/ไม่ผ่านผิดที่เกณฑ์ 300 lx (guard band: ส่งยืนยัน {d300['to_verify_with_reference_pct']:.0f}% ของจุด)</div></div>
    <div class="kpi"><div><span class="from">41</span><span class="arrow"> → </span><span class="big">0</span></div>
      <div class="lbl">ระดับแสงที่ auto-range แกว่งจน SATURATED (v1.0 → v1.1, 521 ระดับ)</div></div>
  </div>
  <img class="wide" src="assets/fig_cal_scatter_poster.svg" alt="" style="width:470pt;margin:2pt auto 0">
  <div class="cap"><b>ภาพที่ 6</b> ต้นแบบเทียบเครื่องอ้างอิง: ก่อนชดเชยอ่านต่ำกว่าจริงราว 1/3 (ประมาณจาก datasheet) หลังชดเชยเข้าใกล้ y = x</div>
  <div class="box orange" style="margin-top:8pt;padding:14pt 18pt">
    <div style="display:flex;align-items:center;gap:16pt">
      <div><span class="pill t" style="font-size:18pt">ผลการใช้งานจริง</span>
        <div class="big o" style="font-size:56pt;line-height:1.05;margin-top:4pt;white-space:nowrap">10–30%</div></div>
      <div style="font-size:20.5pt;line-height:1.36">ห้องทำงาน<b>เกือบทุกห้อง</b>ของสำนักดิจิทัลเทคโนโลยี (ยกเว้นห้องประชุม)
      มีแสง<b>ต่ำกว่าระดับมาตรฐาน</b> → ผู้บริหารวางแผนปรับปรุง</div>
    </div>
    <div class="fx"><div class="fxh">ขาดเล็กน้อย<br>เปลี่ยนหลอด LED<br>วัตต์สูงขึ้น</div>
      <div class="fxe"><span data-pptx="img" data-name="สูตรเปลี่ยนวัตต์หลอด" style="display:inline-block"><span class="mi">P</span><sub>ใหม่</sub> = <span class="mi">P</span><sub>เดิม</sub> × <span class="frac"><span><span class="mi">E</span><sub>เป้าหมาย</sub></span><span><span class="mi">E</span><sub>วัดได้</sub></span></span></span>
      <div class="fxx">เช่น วัดได้ 270 lx: 18 W → 22 W</div></div></div>
    <div class="fx"><div class="fxh">ขาดมาก<br>ติดหลอดไฟเพิ่ม</div>
      <div class="fxe"><span data-pptx="img" data-name="สูตรเพิ่มจำนวนหลอด" style="display:inline-block"><span class="mi">N</span><sub>ใหม่</sub> = ⌈<span class="mi">N</span><sub>เดิม</sub> × <span class="frac"><span><span class="mi">E</span><sub>เป้าหมาย</sub></span><span><span class="mi">E</span><sub>วัดได้</sub></span></span>⌉</span>
      <div class="fxx">เช่น วัดได้ 220 lx, 6 ดวง → 9 ดวง</div></div></div>
    <div class="src" style="margin-top:6pt">Lumen method: E = NΦ·UF·MF/A ⇒ E ∝ NΦ · เป้าหมาย = เกณฑ์ × (1 + U<sub>95</sub>) ·
    ยืนยันด้วยเครื่องมาตรฐานก่อนจัดซื้อ</div>
  </div>
  <h2 style="margin-top:10pt">CONCLUSIONS<small>สรุปและบทเรียน</small></h2><div class="rule"></div>
  <ol class="conc">
    <li><b>ใช้ได้จริง</b>: เครื่องละ ~385&nbsp;฿ พบห้องแสงไม่พอ → แผนปรับปรุงทันที</li>
    <li><b>บทเรียนหน้างาน</b>: LED วูบ 100 ครั้ง/วินาทีตามไฟ 50 Hz → เฉลี่ย 5 ค่า ค่านิ่งขึ้น ~2.3&nbsp;เท่า</li>
    <li>ความรู้เป็นโค้ด SOP คู่มือ STL ที่ทำซ้ำได้โดยไม่ต้องพึ่งผู้พัฒนา</li>
  </ol>
  <div class="open"><h4>เปิดให้ร่วมพัฒนาต่อบน GitHub</h4>
    <ul><li>· วัดคู่จริงกับเครื่องมาตรฐาน</li><li>· สมการแยกตามชนิดหลอด</li>
    <li>· Wi-Fi logging + dashboard</li><li>· ฝากระจายแสง (cosine)</li>
    <li>· แผนที่ความสว่างจากกริด</li><li>· เซนเซอร์ CO₂/อุณหภูมิ/เสียง</li></ul></div>
  <div class="box" style="padding:16pt 20pt">
    <div style="font-family:Kanit;font-weight:600;font-size:30pt;line-height:1.15;color:var(--ink)">เผยแพร่แล้ว · สแกนเพื่อนำไปใช้</div>
    <div class="url" style="margin:2pt 0 10pt" data-link="https://github.com/banpot/LightCheck-KM">github.com/banpot/LightCheck-KM</div>
    <div class="diss"><img src="assets/qr_repo.svg" alt="" data-name="QR GitHub" data-link="https://github.com/banpot/LightCheck-KM">
      <ol class="steps">
        <li>สแกน QR → คู่มือ, firmware, STL</li>
        <li>ซื้ออุปกรณ์ 359&nbsp;฿ + พิมพ์กล่อง 54&nbsp;g</li>
        <li>ต่อสายตามผัง + อัปโหลด firmware</li>
        <li>สอบเทียบกับเครื่องมาตรฐาน 1 ครั้ง</li>
        <li>วัดตาม SOP: จดค่าเมื่อจอขึ้น * จุดใกล้เกณฑ์ส่งยืนยัน</li>
        <li>ขอรับการถ่ายทอด: เปิด Issue ใน repo</li>
      </ol></div>
    <div class="stats">
      <div><div class="big">{STATS['markdown_docs']}</div><div class="lbl">เอกสาร/คู่มือ</div></div>
      <div><div class="big">{STATS['stl_files']}</div><div class="lbl">ไฟล์ STL</div></div>
      <div><div class="big">{STATS['python_tools']}</div><div class="lbl">เครื่องมือ Python</div></div>
      <div><div class="big" style="font-size:30pt;line-height:1.33">Public</div><div class="lbl">MIT / CC BY 4.0</div></div>
    </div>
  </div>
</div>

<div class="abs fbar"></div>
<div class="abs foot" style="left:70pt;top:2686pt">Silpakorn KM Day 2569</div>
<div class="abs foot" style="left:70pt;top:2765pt">18 Dec 2026</div>
<div class="abs foot" style="left:1429pt;top:2694pt;font-size:29.5pt">OFFICE THE PRESIDENT SILPAKORN UNIVERSITY</div>
<div class="abs foot" style="left:1429pt;top:2774pt;font-size:29.5pt">22, Borommarachachonani Rd., Talingchan, Bangkok</div>
<div class="abs" style="left:530pt;top:2700pt;width:880pt;text-align:center;font-size:17pt;color:var(--ink2);line-height:1.35">
ตัวเลขที่ติดป้าย <span class="sim">ผลจำลอง</span> มาจากแบบจำลองเชิงอัลกอริทึม ไม่ใช่ข้อมูลวัดจริง<br>สร้างซ้ำได้ด้วยคำสั่ง <b>make all</b> ใน repository</div>
<script>
// overflow report for layout tuning
window.layoutReport = () => [...document.querySelectorAll('.col')].map(c => {{
  const last = [...c.children].reduce((m, e) => Math.max(m, e.getBoundingClientRect().bottom), 0);
  return {{col: c.className, bottom_pt: Math.round(last * 0.75), limit_pt: Math.round(c.getBoundingClientRect().bottom * 0.75)}};
}});
</script>
</body></html>
"""
import re


def number_lists(doc):
    """Write list numbers as real spans (editable in PowerPoint) instead of CSS counters."""
    def fix(m):
        cls, body = m.group(1), m.group(2)
        k = [0]
        def li(_):
            k[0] += 1
            return f'<li><span class="num">{k[0]}{"." if cls == "conc" else ""}</span>'
        return f'<ol class="{cls}">' + re.sub(r"<li>", li, body) + "</ol>"
    return re.sub(r'<ol class="(obj|conc|steps)">(.*?)</ol>', fix, doc, flags=re.S)


html = number_lists(html)
open(os.path.join(HERE, "poster.html"), "w", encoding="utf-8").write(html)
print("poster.html written", len(html))
