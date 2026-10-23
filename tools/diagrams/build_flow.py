"""Firmware data-flow diagram + pin-connection table."""
import os
from common import svg_doc, save, text, PAL, esc

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "docs", "img")

ARROW_DEFS = """
<marker id="ah" viewBox="0 0 10 10" refX="8.6" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
  <path d="M0,0 L10,5 L0,10 z" fill="#14202B"/>
</marker>
<marker id="ahO" viewBox="0 0 10 10" refX="8.6" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
  <path d="M0,0 L10,5 L0,10 z" fill="#F26B21"/>
</marker>
<marker id="ahT" viewBox="0 0 10 10" refX="8.6" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
  <path d="M0,0 L10,5 L0,10 z" fill="#0E7766"/>
</marker>
"""


def arrow(d, color="#14202B", marker="ah", w=4):
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linejoin="round" marker-end="url(#{marker})"/>'


def box(x, y, w, h, title, sub=None, num=None, fill="#FFFFFF", stroke=PAL["su"], tsize=29, ssize=22,
        sub_cls="t", sub_fill=None):
    s = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="20" fill="{fill}" stroke="{stroke}" stroke-width="3"/>']
    tx = x + (92 if num is not None else 28)
    if num is not None:
        s.append(f'<circle cx="{x+46}" cy="{y+h/2}" r="27" fill="{stroke}"/>')
        s.append(text(x + 46, y + h / 2 + 11, str(num), 30, cls="h", fill="#FFFFFF", anchor="middle"))
    lines = sub if isinstance(sub, (list, tuple)) else ([sub] if sub else [])
    total = tsize + len(lines) * (ssize + 10)
    ty = y + (h - total) / 2 + tsize * 0.85
    s.append(text(tx, ty, title, tsize, weight=600))
    for i, ln in enumerate(lines):
        s.append(text(tx, ty + 14 + (i + 1) * (ssize + 10) - 6, ln, ssize, cls=sub_cls,
                      fill=sub_fill or PAL["gray"]))
    return "".join(s)


def diamond(cx, cy, w, h, label, cls="t", size=26, fill="#FFF4EC", stroke=PAL["orange"]):
    pts = f"{cx},{cy-h/2} {cx+w/2},{cy} {cx},{cy+h/2} {cx-w/2},{cy}"
    return (f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="3" stroke-linejoin="round"/>'
            + text(cx, cy + size * 0.36, label, size, cls=cls, weight=600, anchor="middle", fill=PAL["ink"]))


def lab(x, y, s, color=PAL["orange"], anchor="start", size=23):
    return text(x, y, s, size, weight=700, fill=color, anchor=anchor)


def build_flow():
    W, H = 1420, 1960
    X0, BW = 300, 700
    CX = X0 + BW / 2
    RX, RW = 1060, 270
    b = []
    # start
    b.append(f'<rect x="{CX-230}" y="30" width="460" height="72" rx="36" fill="{PAL["ink"]}"/>')
    b.append(text(CX, 77, "เปิดเครื่อง · ไฟ USB 5 V", 28, weight=600, fill="#FFFFFF", anchor="middle"))
    b.append(arrow(f"M{CX},102 L{CX},150"))
    # 1 self-check
    b.append(box(X0, 150, BW, 140, "ตรวจอุปกรณ์บน I²C (self-check)",
                 ["TSL2591 @0x29 · LCD @0x3F · tsl.begin() · อ่านทดสอบ"], num=1))
    b.append(arrow(f"M{CX},290 L{CX},322"))
    b.append(diamond(CX, 390, 300, 136, "พบครบ?"))
    b.append(arrow(f"M{CX+150},390 L{RX},390", PAL["orange"], "ahO"))
    b.append(lab(CX + 168, 378, "ไม่พบ"))
    b.append(box(RX, 340, RW, 100, "หยุดทำงาน (HALT)", ["แจ้งบน LCD + Serial"], fill="#FDECEC",
                 stroke="#C0392B", tsize=25, ssize=20))
    b.append(arrow(f"M{CX},458 L{CX},500"))
    b.append(lab(CX + 14, 487, "พบ", PAL["teal"]))
    # 2 traceability
    b.append(box(X0, 495, BW, 150, "พิมพ์ข้อมูลสมการชดเชย (traceability)",
                 ["CAL_MODEL_VERSION · CAL_DATE · CAL_REFERENCE", "สัมประสิทธิ์ a (slope), b (offset)"], num=2, ssize=21))
    b.append(arrow(f"M{CX},640 L{CX},700"))
    # loop region background
    b.append(f'<rect x="120" y="676" width="{W-150}" height="{H-676-30}" rx="28" fill="#F3F8FC" stroke="#BBD8EA" stroke-width="2.5" stroke-dasharray="10 8"/>')
    b.append(text(150, 718, "loop() · วนทุก ≈1 วินาที", 24, weight=700, fill=PAL["su"]))
    # re-draw arrow on top of bg
    b.append(arrow(f"M{CX},640 L{CX},740"))
    # 3 read
    b.append(box(X0, 740, BW, 130, "อ่านค่า Full + IR จาก ADC (ค่าดิบ)",
                 ["getFullLuminosity() · ใช้ gain/integration ปัจจุบัน"], num=3))
    b.append(arrow(f"M{CX},870 L{CX},902"))
    # saturation decision
    b.append(diamond(CX, 970, 380, 140, "อิ่มตัว (saturated)?"))
    b.append(text(CX + 24, 1080, "เกณฑ์: 36,863 @100 ms · 65,535 @200–600 ms", 21,
                  fill=PAL["gray"], anchor="start"))
    b.append(arrow(f"M{CX+190},970 L{RX},970", PAL["orange"], "ahO"))
    b.append(lab(CX + 205, 958, "ใช่"))
    b.append(box(RX, 920, RW, 100, "แสดง SATURATED", ["ไม่คำนวณ lux รอบนี้"], fill="#FFF4EC",
                 stroke=PAL["orange"], tsize=25, ssize=20))
    b.append(arrow(f"M{RX+RW},970 L{RX+RW+40},970 L{RX+RW+40},1600 L{X0+BW},1600", PAL["orange"], "ahO"))
    b.append(arrow(f"M{CX},1040 L{CX},1110"))
    b.append(lab(CX - 14, 1082, "ไม่", PAL["teal"], anchor="end"))
    # 4 raw lux
    b.append(box(X0, 1110, BW, 130, "คำนวณ Raw Lux",
                 ["calculateLux(full, ir) — เก็บค่าดิบไว้เสมอเพื่อ audit"], num=4))
    b.append(arrow(f"M{CX},1240 L{CX},1270"))
    b.append(diamond(CX, 1345, 460, 150, "CALIBRATION_ENABLED ?", cls="m", size=23))
    b.append(arrow(f"M{CX+230},1345 L{RX},1345", PAL["teal"], "ahT"))
    b.append(lab(CX + 245, 1333, "true", PAL["teal"]))
    b.append(box(RX, 1290, RW, 110, "E = a·E_raw + b", ["ค่าหลังชดเชย (CLux)"], fill=PAL["teal_tint"],
                 stroke=PAL["teal"], tsize=26, ssize=20))
    b.append(arrow(f"M{RX+RW/2},1400 L{RX+RW/2},1530 L{X0+BW},1530", PAL["teal"], "ahT"))
    b.append(arrow(f"M{CX},1420 L{CX},1490"))
    b.append(lab(CX + 14, 1460, "false → ใช้ Raw (RLux)", PAL["gray"]))
    # 5 output
    b.append(box(X0, 1490, BW, 150, "แสดงผลบน LCD + บันทึกผ่าน Serial",
                 ["LCD: RLux/CLux · Gain · Tint", "Serial: RawLux · CalLux · Gain · Tint · CalMode"], num=5,
                 fill=PAL["teal_tint"], stroke=PAL["teal"]))
    b.append(arrow(f"M{CX},1640 L{CX},1690"))
    # 6 auto-range
    b.append(box(X0, 1690, BW, 170, "Auto-range จากค่า ADC ดิบ (มี hysteresis)",
                 ["ใกล้อิ่มตัว → ลด gain", "สัญญาณต่ำ → เพิ่ม gain เมื่อคาดว่าไม่อิ่มตัว", "ไม่ใช้ค่าหลังชดเชยในการเลือก gain"],
                 num=6, ssize=21))
    # loop back
    b.append(arrow(f"M{X0},1775 L{200},1775 L{200},805 L{X0},805", PAL["su"], "ah", w=4.5))
    return svg_doc(W, H, "".join(b), defs=ARROW_DEFS)


def build_table():
    W = 1800
    cols = [("สัญญาณ", 250), ("Wemos D1 mini", 330), ("TSL2591", 260), ("LCD1602 backpack", 330), ("หมายเหตุ", 630)]
    rows = [
        ("3.3V", PAL["w3v3"], "3V3", "VIN", "—", "ไฟเลี้ยงเซนเซอร์ (บอร์ดรับได้ 3–5 V)"),
        ("5V", PAL["w5v"], "5V · USB", "—", "VCC", "ไฟเลี้ยงจอและ backlight (5 V จาก USB)"),
        ("GND", PAL["wgnd"], "G", "GND", "GND", "กราวด์ร่วมทุกโมดูล"),
        ("SDA", PAL["wsda"], "D2 · GPIO4", "SDA", "SDA", "I²C data — บัสร่วม 2 อุปกรณ์"),
        ("SCL", PAL["wscl"], "D1 · GPIO5", "SCL", "SCL", "I²C clock — บัสร่วม 2 อุปกรณ์"),
    ]
    rh, hh, top = 84, 76, 20
    H = top + hh + rh * len(rows) + 120
    b = [f'<rect x="20" y="{top}" width="{W-40}" height="{hh + rh*len(rows)}" rx="20" fill="#FFFFFF" stroke="{PAL["su"]}" stroke-width="3"/>',
         f'<path d="M20,{top+hh} V{top+20} a20,20 0 0 1 20,-20 H{W-40} a20,20 0 0 1 20,20 V{top+hh} Z" fill="{PAL["su"]}"/>']
    x = 20
    for name, w in cols:
        b.append(text(x + 26, top + 50, name, 28, weight=600, fill="#FFFFFF"))
        x += w
    for i, (sig, c, d1, tsl, lcd, note) in enumerate(rows):
        y = top + hh + i * rh
        if i % 2 == 1:
            b.append(f'<rect x="21.5" y="{y}" width="{W-43}" height="{rh}" fill="#F3F8FC"/>')
        if i > 0:
            b.append(f'<line x1="22" y1="{y}" x2="{W-22}" y2="{y}" stroke="#D5DDE4" stroke-width="1.5"/>')
        cy = y + rh / 2
        b.append(f'<line x1="46" y1="{cy}" x2="106" y2="{cy}" stroke="{c}" stroke-width="12" stroke-linecap="round"/>')
        b.append(text(126, cy + 10, sig, 28, cls="m", fill=PAL["ink"]))
        x = 20 + cols[0][1]
        for val, (nm, w) in zip((d1, tsl, lcd), cols[1:4]):
            b.append(text(x + 26, cy + 10, val, 27, cls="m" if val != "—" else "t",
                          fill=PAL["ink"] if val != "—" else "#9AA6B0"))
            x += w
        b.append(text(x + 26, cy + 9, note, 25))
    fy = top + hh + rh * len(rows) + 50
    b.append(text(28, fy, "ไม่ต่อ: TSL2591 ขา 3Vo และ INT  ·  แอดเดรส I²C: TSL2591 = 0x29 (เปลี่ยนไม่ได้)  ·  LCD = 0x3F (ชิป PCF8574A; ถ้าเป็น PCF8574 จะเป็น 0x27)",
                  23, fill=PAL["gray"]))
    b.append(text(28, fy + 40, "บอร์ด TSL2591 รุ่นเก่า (PCB สีน้ำเงิน) เรียงขาต่างจากรุ่นปัจจุบัน ให้ต่อตามตัวอักษรบนบอร์ดเสมอ",
                  23, fill=PAL["gray"]))
    return svg_doc(W, H, "".join(b))


if __name__ == "__main__":
    save(f"{OUT}/firmware_flow.svg", build_flow())
    save(f"{OUT}/pin_table.svg", build_table())
