"""Wiring diagram: Wemos D1 mini + TSL2591 + LCD1602 (PCF8574A backpack) on one I2C bus."""
import os
from common import svg_doc, save, text, PAL, esc
import components as C

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "docs", "img")
S = 9.0  # px per mm
W, H = 1800, 1290

LCD_O = (70, 150)
TSL_O = (1290, 190)
D1_O = (520, 640)


def P(origin, local):
    return origin[0] + local[0] * S, origin[1] + local[1] * S


def cable(d, color, w=8.0):
    return (f'<path d="{d}" fill="none" stroke="#FFFFFF" stroke-width="{w+5}" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="#FFFFFF" stroke-opacity="0.28" stroke-width="{w*0.28:.2f}" '
            f'stroke-linecap="round" transform="translate(-1.2,-1.6)"/>')


def end_dot(x, y, color):
    return (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7.5" fill="{color}" stroke="#FFFFFF" stroke-width="2.5"/>'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" fill="#FFFFFF" opacity="0.85"/>')


def junction(x, y, color):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="{color}" stroke="#14202B" stroke-width="2.4"/>'


def bez(p0, p1, p2, p3):
    return f"M{p0[0]:.1f},{p0[1]:.1f} C{p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f} {p3[0]:.1f},{p3[1]:.1f}"


def bez_pt(p0, p1, p2, p3, t):
    u = 1 - t
    return tuple(u**3 * a + 3 * u * u * t * b + 3 * u * t * t * c + t**3 * d for a, b, c, d in zip(p0, p1, p2, p3))


def pill(x, y, label, color, txt="#FFFFFF", size=25, padx=13):
    w = len(label) * size * 0.62 + 2 * padx
    h = size * 1.45
    return (f'<rect x="{x-w/2:.1f}" y="{y-h/2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{h/2:.1f}" fill="{color}" stroke="#FFFFFF" stroke-width="3"/>'
            + text(x, y + size * 0.36, label, size, cls="m", fill=txt, anchor="middle"))


def title(x, y, main, sub=None, addr=None, anchor="start"):
    s = text(x, y, main, 34, cls="h", anchor=anchor)
    if sub:
        s += text(x, y + 36, sub, 24, fill=PAL["gray"], anchor=anchor)
    if addr:
        aw = 128
        ax = x + (len(main) * 34 * 0.53 + 20 if anchor == "start" else 20)
        s += (f'<rect x="{ax:.1f}" y="{y-32}" width="{aw}" height="42" rx="21" fill="{PAL["teal"]}"/>'
              + text(ax + aw / 2, y - 3, addr, 25, cls="m", fill="#FFFFFF", anchor="middle"))
    return s


def build(embed_fonts=True):
    body = []
    # --- components
    body.append(f'<g transform="translate({LCD_O[0]},{LCD_O[1]}) scale({S})">{C.lcd_back()}</g>')
    body.append(f'<g transform="translate({TSL_O[0]},{TSL_O[1]}) scale({S})">{C.tsl2591()}</g>')
    body.append(f'<g transform="translate({D1_O[0]},{D1_O[1]}) scale({S})">{C.d1_mini()}</g>')

    # --- titles
    body.append(title(LCD_O[0], LCD_O[1] - 62, "LCD1602 + I²C backpack", "มุมมองด้านหลัง · ชิป PCF8574A · ไฟเลี้ยง 5 V", "0x3F"))
    body.append(title(TSL_O[0], TSL_O[1] - 62, "TSL2591", "Adafruit #1980 · ไฟเลี้ยง 3.3 V", "0x29"))
    body.append(title(D1_O[0] + 115, D1_O[1] - 52, "Wemos D1 mini", "ESP8266 · ไฟเลี้ยง USB-C 5 V", anchor="middle"))

    # --- pin coordinates
    d1 = {n: P(D1_O, C.d1_pin(n)) for n in ["D1", "D2", "G", "5V", "3V3"]}
    lcd = {n: P(LCD_O, C.i2c_pin_back(n)) for n in C.I2C_ORDER}
    tsl = {n: P(TSL_O, C.tsl_pin(n)) for n in ["VIN", "GND", "SCL", "SDA"]}

    col = dict(SCL=PAL["wscl"], SDA=PAL["wsda"], GND=PAL["wgnd"], V5=PAL["w5v"], V33=PAL["w3v3"])
    jx = {"SCL": 800, "SDA": 830, "GND": 860}
    J = {"SCL": (jx["SCL"], d1["D1"][1]), "SDA": (jx["SDA"], d1["D2"][1]), "GND": (jx["GND"], d1["G"][1])}
    wires, dots, tags = [], [], []

    # stubs from D1 pads to splice junctions
    for sig, pin in [("SCL", "D1"), ("SDA", "D2"), ("GND", "G")]:
        x0, y0 = d1[pin]
        wires.append((f"M{x0:.1f},{y0:.1f} L{J[sig][0]:.1f},{J[sig][1]:.1f}", col[sig]))

    # cables to the LCD backpack header (arrive from the right, horizontally)
    lcd_routes = {
        "GND": (J["GND"], (1060, J["GND"][1] - 40), (1080, lcd["GND"][1]), "GND", col["GND"]),
        "SDA": (J["SDA"], (1000, J["SDA"][1] - 60), (1040, lcd["SDA"][1]), "SDA", col["SDA"]),
        "SCL": (J["SCL"], (960, J["SCL"][1] - 80), (1000, lcd["SCL"][1]), "SCL", col["SCL"]),
    }
    for sig, (p0, p1, p2, pin, c) in lcd_routes.items():
        p3 = (lcd[pin][0] + 2, lcd[pin][1])
        wires.append((bez(p0, p1, p2, p3), c))
        dots.append(end_dot(*p3, c))
    # 5 V straight from the D1 5V pad
    p0 = d1["5V"]
    p3 = (lcd["VCC"][0] + 2, lcd["VCC"][1])
    v5 = (p0, (1150, p0[1]), (1120, lcd["VCC"][1]), p3)
    wires.append((bez(*v5), col["V5"]))
    dots.append(end_dot(*p3, col["V5"]))

    # cables to the TSL2591 header (arrive from below, vertically)
    tsl_routes = {
        "GND": (J["GND"], (1000, J["GND"][1] + 10), tsl["GND"], col["GND"]),
        "SCL": (J["SCL"], (1000, J["SCL"][1] + 10), tsl["SCL"], col["SCL"]),
        "SDA": (J["SDA"], (1000, J["SDA"][1] + 10), tsl["SDA"], col["SDA"]),
    }
    for sig, (p0, p1, pin, c) in tsl_routes.items():
        p3 = (pin[0], pin[1] + 2)
        p2 = (pin[0], pin[1] + 260)
        wires.append((bez(p0, p1, p2, p3), c))
        dots.append(end_dot(*p3, c))
    # 3V3: around the bottom of the D1 mini to TSL VIN
    x0, y0 = d1["3V3"]
    vin = tsl["VIN"]
    yb = 1035
    d33 = (f"M{x0:.1f},{y0:.1f} C{x0-80:.1f},{y0:.1f} {x0-80:.1f},{yb:.1f} {x0+20:.1f},{yb:.1f} "
           f"L{vin[0]-120:.1f},{yb:.1f} C{vin[0]:.1f},{yb:.1f} {vin[0]:.1f},{yb-120:.1f} {vin[0]:.1f},{vin[1]+240:.1f} "
           f"L{vin[0]:.1f},{vin[1]+2:.1f}")
    wires.insert(0, (d33, col["V33"]))
    dots.append(end_dot(vin[0], vin[1] + 2, col["V33"]))
    # D1 pad dots
    for sig, pin, c in [("SCL", "D1", col["SCL"]), ("SDA", "D2", col["SDA"]), ("GND", "G", col["GND"]),
                        ("5V", "5V", col["V5"]), ("3V3", "3V3", col["V33"])]:
        dots.append(end_dot(*d1[pin], c))
    for sig in ("SCL", "SDA", "GND"):
        dots.append(junction(*J[sig], col[sig]))

    for d, c in wires:
        body.append(cable(d, c))
    body += dots

    # --- tags placed on the cables themselves
    for (p0, p1, p2, pin, c), t, lab, tc in [
        (lcd_routes["SCL"], 0.58, "SCL", "#14202B"), (lcd_routes["SDA"], 0.47, "SDA", "#FFFFFF"),
        (lcd_routes["GND"], 0.37, "GND", "#FFFFFF")]:
        p3 = (lcd[pin][0] + 2, lcd[pin][1])
        x, y = bez_pt(p0, p1, p2, p3, t)
        body.append(pill(x, y, lab, c, txt=tc, size=22, padx=10))
    x, y = bez_pt(*v5, 0.30)
    body.append(pill(x, y, "5V", col["V5"], size=22, padx=10))
    for sig, t, lab, tc in [("GND", 0.66, "GND", "#FFFFFF"), ("SCL", 0.44, "SCL", "#14202B"), ("SDA", 0.36, "SDA", "#FFFFFF")]:
        p0, p1, pin, c = tsl_routes[sig]
        p3 = (pin[0], pin[1] + 2); p2 = (pin[0], pin[1] + 260)
        x, y = bez_pt(p0, p1, p2, p3, t)
        body.append(pill(x, y, lab, c, txt=tc, size=22, padx=10))
    body.append(pill(vin[0], 1035 - 150, "3.3V", col["V33"], txt="#14202B", size=22, padx=10))
    body.append(pill(900, 1035, "3.3V", col["V33"], txt="#14202B", size=22, padx=10))

    # --- power source: USB-C cable from the D1 mini to a power bank (left, below the I2C box)
    ux = D1_O[0] + 12.8 * S                      # USB-C receptacle centre
    uy = D1_O[1] + (C.D1_H + 1.36) * S           # receptacle outer edge
    pb_x, pb_y, pb_w, pb_h = 95, 968, 250, 86
    port = (pb_x + pb_w, pb_y + pb_h / 2)
    usb = (f"M{ux:.1f},{uy+40:.1f} L{ux:.1f},{uy+70:.1f} C{ux:.1f},{1066:.1f} {ux-30:.1f},{1066:.1f} {ux-60:.1f},{1066:.1f} "
           f"L{port[0]+110:.1f},{1066:.1f} C{port[0]+70:.1f},{1066:.1f} {port[0]+80:.1f},{port[1]:.1f} {port[0]+42:.1f},{port[1]:.1f}")
    body.append(cable(usb, "#3A3F45", w=13))
    # plug overmoulds (board end + power bank end)
    body.append(f'<rect x="{ux-34:.1f}" y="{uy+2:.1f}" width="68" height="40" rx="11" fill="#2F3438" stroke="#14202B" stroke-width="2"/>'
                f'<rect x="{ux-22:.1f}" y="{uy+8:.1f}" width="44" height="6" rx="3" fill="#FFFFFF" opacity="0.25"/>')
    body.append(f'<rect x="{port[0]+2:.1f}" y="{port[1]-17:.1f}" width="42" height="34" rx="10" fill="#2F3438" stroke="#14202B" stroke-width="2"/>')
    # power bank body
    body.append(f'<g filter="url(#fShadow)"><rect x="{pb_x}" y="{pb_y}" width="{pb_w}" height="{pb_h}" rx="18" fill="#3B4650" stroke="#1E262D" stroke-width="2.5"/></g>'
                f'<rect x="{pb_x+10}" y="{pb_y+8}" width="{pb_w-20}" height="14" rx="7" fill="#FFFFFF" opacity="0.10"/>')
    for i in range(4):
        body.append(f'<circle cx="{pb_x+30+i*20}" cy="{pb_y+pb_h-24}" r="5.5" fill="{"#4CD07D" if i < 3 else "#5B6670"}"/>')
    body.append(text(pb_x + 26, pb_y + 44, "POWER BANK", 21, cls="silk"))
    body.append(text(pb_x, pb_y - 46, "แหล่งจ่ายไฟ USB-C 5 V", 29, cls="h"))
    body.append(text(pb_x, pb_y - 14, "power bank หรืออะแดปเตอร์มือถือ", 22, fill=PAL["gray"]))
    body.append(pill(ux - 140, 1066, "USB-C", "#3A3F45", size=22, padx=10))

    # --- I2C summary box (left)
    bx, by = 70, 525
    body.append(f'<rect x="{bx}" y="{by}" width="385" height="330" rx="18" fill="{PAL["teal_tint"]}" stroke="{PAL["teal"]}" stroke-width="2.5"/>')
    body.append(text(bx + 24, by + 50, "I²C bus ร่วม 2 สาย", 30, cls="h", fill=PAL["teal"]))
    rows = [("SDA", "D2 (GPIO4)", col["SDA"]), ("SCL", "D1 (GPIO5)", col["SCL"])]
    for i, (sig, pin, c) in enumerate(rows):
        yy = by + 105 + i * 58
        body.append(f'<line x1="{bx+24}" y1="{yy-9}" x2="{bx+84}" y2="{yy-9}" stroke="{c}" stroke-width="10" stroke-linecap="round"/>')
        body.append(text(bx + 100, yy, f"{sig} → {pin}", 24, cls="m", fill=PAL["ink"]))
    body.append(text(bx + 24, by + 240, "TSL2591 = 0x29", 24, cls="m", fill=PAL["ink"]))
    body.append(text(bx + 24, by + 285, "LCD1602 = 0x3F", 24, cls="m", fill=PAL["ink"]))

    # --- legend + note band
    ly = 1110
    body.append(f'<line x1="70" y1="{ly-20}" x2="{W-70}" y2="{ly-20}" stroke="#D5DDE4" stroke-width="2"/>')
    leg = [("5V (USB-C)", col["V5"]), ("3.3V", col["V33"]), ("GND ร่วม", col["GND"]),
           ("SDA", col["SDA"]), ("SCL", col["SCL"])]
    x = 70
    for i, (lab, c) in enumerate(leg):
        yy = ly + 30 + (i // 3) * 52
        xx = 70 + (i % 3) * 230
        body.append(f'<line x1="{xx}" y1="{yy-9}" x2="{xx+56}" y2="{yy-9}" stroke="#FFFFFF" stroke-width="15" stroke-linecap="round"/>')
        body.append(f'<line x1="{xx}" y1="{yy-9}" x2="{xx+56}" y2="{yy-9}" stroke="{c}" stroke-width="10" stroke-linecap="round"/>')
        body.append(text(xx + 72, yy, lab, 25))
    body.append(junction(70 + 2 * 230 + 8, ly + 30 + 52 - 9, "#FFFFFF"))
    body.append(text(70 + 2 * 230 + 30, ly + 30 + 52, "จุดต่อแยกสาย", 25))

    nx = 780
    body.append(f'<rect x="{nx}" y="{ly-2}" width="{W-70-nx}" height="150" rx="16" fill="#FFF4EC" stroke="{PAL["orange"]}" stroke-width="2.5"/>')
    note = [
        "ข้อควรระวัง: backpack PCF8574 หลายรุ่นมี pull-up ≈4.7 kΩ ต่อขึ้น 5 V ทำให้สาย SDA/SCL",
        "ลอยที่ ≈4.5 V เกินพิกัดขา ESP8266 (VIH สูงสุด 3.6 V) ใช้งานทดลองได้ แต่ถ้าสร้างหลายเครื่อง",
        "หรือใช้งานระยะยาว ควรใส่ I²C level shifter (เช่น BSS138) คั่นระหว่างบัส 3.3 V กับ LCD",
    ]
    for i, ln in enumerate(note):
        body.append(text(nx + 22, ly + 40 + i * 40, ln, 22.5))

    return svg_doc(W, H, "".join(body), defs=C.DEFS, embed_fonts=embed_fonts)


if __name__ == "__main__":
    save(f"{OUT}/wiring_diagram.svg", build())
