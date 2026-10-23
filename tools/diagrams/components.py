"""Hand-built vector illustrations of the LightCheck KM modules.
All component groups are drawn in millimetres (local origin = PCB top-left)
and placed with transform="translate(x,y) scale(s)".
"""
from common import esc

DEFS = """
<linearGradient id="gSilver" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#F4F6F8"/><stop offset=".55" stop-color="#C9D0D7"/><stop offset="1" stop-color="#A7B0B9"/>
</linearGradient>
<linearGradient id="gGold" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#F0D58C"/><stop offset="1" stop-color="#B98E35"/>
</linearGradient>
<linearGradient id="gLcd" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#2E63E8"/><stop offset="1" stop-color="#1B43C0"/>
</linearGradient>
<linearGradient id="gBlueBoard" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#2468C4"/><stop offset="1" stop-color="#16509E"/>
</linearGradient>
<linearGradient id="gGreenBoard" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#16884F"/><stop offset="1" stop-color="#0C6B3C"/>
</linearGradient>
<linearGradient id="gBlackBoard" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#2A2D33"/><stop offset="1" stop-color="#15171B"/>
</linearGradient>
<linearGradient id="gAmber" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#F2B640"/><stop offset="1" stop-color="#B9771A"/>
</linearGradient>
<filter id="fShadow" x="-10%" y="-10%" width="130%" height="140%">
  <feDropShadow dx="0" dy="0.5" stdDeviation="0.6" flood-color="#0B1520" flood-opacity="0.28"/>
</filter>
"""


def pad(x, y, r=0.85, hole=0.45):
    return (f'<circle cx="{x:.3f}" cy="{y:.3f}" r="{r}" fill="url(#gGold)" stroke="#9C7A2E" stroke-width="0.12"/>'
            f'<circle cx="{x:.3f}" cy="{y:.3f}" r="{hole}" fill="#1A1D21"/>')


def smd(x, y, w, h, body="#D9C29A", ends="#C8CDD2", rot=0):
    e = w * 0.22
    g = (f'<g transform="translate({x},{y}) rotate({rot})">'
         f'<rect x="{-w/2}" y="{-h/2}" width="{w}" height="{h}" fill="{body}" rx="0.1"/>'
         f'<rect x="{-w/2}" y="{-h/2}" width="{e}" height="{h}" fill="{ends}"/>'
         f'<rect x="{w/2-e}" y="{-h/2}" width="{e}" height="{h}" fill="{ends}"/></g>')
    return g


def ic(x, y, w, h, legs_each_side, leg_len=0.55, body="#1E2126", label=None, lsize=0.9):
    s = [f'<rect x="{x-w/2}" y="{y-h/2}" width="{w}" height="{h}" rx="0.18" fill="{body}"/>']
    if legs_each_side:
        pitch = w / (legs_each_side + 0.2)
        for i in range(legs_each_side):
            lx = x - w/2 + pitch * (i + 0.6) - 0.18
            s.append(f'<rect x="{lx:.3f}" y="{y-h/2-leg_len:.3f}" width="0.36" height="{leg_len}" fill="#C8CDD2"/>')
            s.append(f'<rect x="{lx:.3f}" y="{y+h/2:.3f}" width="0.36" height="{leg_len}" fill="#C8CDD2"/>')
    if label:
        s.append(f'<text x="{x}" y="{y+lsize*0.35}" text-anchor="middle" class="silk" '
                 f'style="font-size:{lsize}px;fill:#9AA3AD;font-weight:500">{esc(label)}</text>')
    return "".join(s)


# ---------------------------------------------------------------- Wemos D1 mini
D1_W, D1_H = 25.6, 34.2
D1_ROW_X = (1.37, 24.23)
D1_PIN_Y0, PITCH = 11.2, 2.54
D1_LEFT = ["RST", "A0", "D0", "D5", "D6", "D7", "D8", "3V3"]
D1_RIGHT = ["TX", "RX", "D1", "D2", "D3", "D4", "G", "5V"]


def d1_pin(name):
    """Local mm coordinate of a D1 mini header pin."""
    if name in D1_LEFT:
        return D1_ROW_X[0], D1_PIN_Y0 + PITCH * D1_LEFT.index(name)
    return D1_ROW_X[1], D1_PIN_Y0 + PITCH * D1_RIGHT.index(name)


def d1_mini(highlight=()):
    s = ['<g filter="url(#fShadow)">',
         f'<rect x="0" y="0" width="{D1_W}" height="{D1_H}" rx="1.1" fill="url(#gBlueBoard)" stroke="#0F3F7E" stroke-width="0.25"/>',
         '</g>']
    # PCB antenna meander
    pts = []
    x = 3.4
    up = True
    while x < 21.5:
        pts.append(f"{x:.2f},{1.6 if up else 5.6}")
        pts.append(f"{x:.2f},{5.6 if up else 1.6}")
        x += 1.6
        up = not up
    s.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="#D9B65C" stroke-width="0.42" stroke-linejoin="round" opacity="0.9"/>')
    s.append('<line x1="3.4" y1="5.6" x2="3.4" y2="7.4" stroke="#D9B65C" stroke-width="0.42"/>')
    # metal shield (ESP8266 module can)
    s.append('<rect x="5.7" y="8.0" width="14.2" height="13.6" rx="0.6" fill="url(#gSilver)" stroke="#8A949E" stroke-width="0.22"/>')
    s.append('<rect x="6.3" y="8.6" width="13.0" height="12.4" rx="0.4" fill="none" stroke="#FFFFFF" stroke-width="0.15" opacity="0.7"/>')
    s.append('<text x="12.8" y="14.2" text-anchor="middle" class="h" style="font-size:2.1px;fill:#6E7882">WEMOS</text>')
    s.append('<text x="12.8" y="16.6" text-anchor="middle" class="m" style="font-size:1.05px;fill:#7E8892">ESP8266EX · Wi-Fi</text>')
    # small SMD parts below the can
    s.append(ic(12.8, 25.0, 4.6, 2.2, 4, body="#20242A"))
    s.append(smd(8.0, 23.6, 1.6, 0.8))
    s.append(smd(8.0, 25.4, 1.6, 0.8, body="#2B2E33"))
    s.append(smd(17.6, 23.6, 1.6, 0.8))
    s.append(smd(17.6, 25.4, 1.6, 0.8, body="#2B2E33"))
    s.append('<text x="12.8" y="28.8" text-anchor="middle" class="h" style="font-size:1.55px;fill:#FFFFFF">D1 mini</text>')
    # reset button (top side, near USB)
    s.append('<rect x="3.0" y="29.9" width="3.4" height="3.0" rx="0.3" fill="#C9CED4" stroke="#8A949E" stroke-width="0.15"/>')
    s.append('<circle cx="4.7" cy="31.4" r="0.95" fill="#2A2D31"/>')
    # USB-C receptacle (8.94 x 3.26 mm, protrudes from bottom edge)
    s.append(f'<rect x="8.33" y="{D1_H-1.9:.2f}" width="8.94" height="3.26" rx="1.63" fill="url(#gSilver)" stroke="#7D8790" stroke-width="0.2"/>')
    s.append(f'<rect x="9.4" y="{D1_H-0.75:.2f}" width="6.8" height="0.95" rx="0.47" fill="#3A3F45"/>')
    # header pads + silkscreen
    for i, n in enumerate(D1_LEFT):
        x, y = D1_ROW_X[0], D1_PIN_Y0 + PITCH * i
        s.append(pad(x, y))
        s.append(f'<text x="{x+1.25:.2f}" y="{y+0.42:.2f}" class="silk" style="font-size:1.12px">{n}</text>')
    for i, n in enumerate(D1_RIGHT):
        x, y = D1_ROW_X[1], D1_PIN_Y0 + PITCH * i
        s.append(pad(x, y))
        s.append(f'<text x="{x-1.25:.2f}" y="{y+0.42:.2f}" class="silk" text-anchor="end" style="font-size:1.12px">{n}</text>')
    for n in highlight:
        x, y = d1_pin(n)
        s.append(f'<circle cx="{x}" cy="{y}" r="1.25" fill="none" stroke="#FFFFFF" stroke-width="0.25"/>')
    return "".join(s)


# ---------------------------------------------------------------- Adafruit TSL2591 (#1980, STEMMA QT rev.)
TSL_W, TSL_H = 25.4, 17.78
TSL_PIN_Y = 17.78 - 2.54
TSL_PINS = ["VIN", "3Vo", "GND", "SCL", "SDA", "INT"]
TSL_PIN_X = [6.35, 8.89, 11.43, 13.97, 16.51, 19.05]


def tsl_pin(name):
    return TSL_PIN_X[TSL_PINS.index(name)], TSL_PIN_Y


def tsl2591():
    s = ['<g filter="url(#fShadow)">',
         f'<rect x="0" y="0" width="{TSL_W}" height="{TSL_H}" rx="1.6" fill="url(#gBlackBoard)" stroke="#0C0D0F" stroke-width="0.2"/>',
         '</g>']
    for (x, y) in [(2.54, 2.54), (22.86, 2.54), (2.54, 15.24), (22.86, 15.24)]:
        s.append(f'<circle cx="{x}" cy="{y}" r="1.95" fill="url(#gGold)" stroke="#8E6E2A" stroke-width="0.12"/>')
        s.append(f'<circle cx="{x}" cy="{y}" r="1.25" fill="#0B0C0E"/>')
    # STEMMA QT (JST-SH 4) connectors at both edges
    for cx, outer in [(2.2, -1), (23.2, 1)]:
        s.append(f'<rect x="{cx-2.0}" y="{8.89-3.05}" width="4.0" height="6.1" rx="0.25" fill="#DADDE1" stroke="#AEB4BA" stroke-width="0.12"/>')
        ox = cx + outer * 1.2 - 0.55
        s.append(f'<rect x="{ox}" y="{8.89-2.3}" width="1.1" height="4.6" fill="#7D848B"/>')
        for k in range(4):
            yy = 8.89 - 1.5 + k * 1.0
            lx = cx - outer * 2.0 - (0.6 if outer > 0 else 0)
            s.append(f'<rect x="{lx:.2f}" y="{yy-0.17:.2f}" width="0.6" height="0.34" fill="#C8CDD2"/>')
    # sensor die (DFN-6, 2 x 2.4 mm)
    s.append('<rect x="11.7" y="7.69" width="2.0" height="2.4" rx="0.12" fill="url(#gAmber)" stroke="#8C5A10" stroke-width="0.1"/>')
    s.append('<rect x="12.15" y="8.2" width="1.1" height="1.38" fill="#E8A733" stroke="#7A4C0C" stroke-width="0.06"/>')
    s.append('<circle cx="12.7" cy="8.89" r="3.0" fill="none" stroke="#F2B640" stroke-width="0.08" stroke-dasharray="0.3 0.3" opacity="0.55"/>')
    # regulator, caps, level shifter, resistor pack, LED
    s.append(ic(8.1, 9.0, 2.9, 1.6, 3, leg_len=0.45))
    s.append(smd(7.9, 12.05, 2.0, 1.25, body="#CDB48A"))
    s.append(smd(8.1, 5.6, 2.0, 1.25, body="#CDB48A"))
    s.append(smd(11.8, 12.1, 1.6, 0.8, body="#CDB48A"))
    s.append(ic(16.9, 10.3, 2.0, 1.25, 3, leg_len=0.35))
    s.append(ic(17.15, 6.35, 3.2, 1.6, 4, leg_len=0.3))
    s.append('<rect x="3.15" y="4.85" width="0.9" height="0.55" fill="#38D46A"/>')
    s.append('<text x="0.55" y="5.55" class="silk" style="font-size:0.95px">on</text>')
    # silkscreen
    s.append('<text x="13.6" y="2.75" text-anchor="middle" class="h" style="font-size:2.15px;fill:#FFFFFF">TSL2591</text>')
    s.append('<text x="13.6" y="4.45" text-anchor="middle" class="t" style="font-size:1.2px;fill:#FFFFFF;font-weight:600">Light Sensor</text>')
    for n, x in zip(TSL_PINS, TSL_PIN_X):
        s.append(pad(x, TSL_PIN_Y))
        below = n in ("VIN", "GND", "SDA")
        yy = TSL_PIN_Y + 1.95 if below else TSL_PIN_Y - 1.2
        s.append(f'<text x="{x}" y="{yy:.2f}" text-anchor="middle" class="silk" style="font-size:1.08px">{n}</text>')
    return "".join(s)


# ---------------------------------------------------------------- LCD1602 (HD44780) + PCF8574A backpack
LCD_W, LCD_H = 80.0, 36.0
I2C_ORDER = ["GND", "VCC", "SDA", "SCL"]

FONT5x7 = {
    " ": ["00000"] * 7,
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "u": ["00000", "00000", "10001", "10001", "10001", "10011", "01101"],
    "x": ["00000", "00000", "10001", "01010", "00100", "01010", "10001"],
    ":": ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "m": ["00000", "00000", "11010", "10101", "10101", "10001", "10001"],
    "s": ["00000", "00000", "01110", "10000", "01110", "00001", "11110"],
}


def lcd_text(lines, x0=12.45, y0=12.55, on="#F3F6FF"):
    cw, ch, px, py = 2.95, 5.55, 3.55, 5.95
    dw, dh = cw / 5, ch / 8
    s = []
    for r in range(2):
        line = (lines[r] if r < len(lines) else "").ljust(16)[:16]
        for c, chv in enumerate(line):
            gx, gy = x0 + c * px, y0 + r * py
            s.append(f'<rect x="{gx:.3f}" y="{gy:.3f}" width="{cw}" height="{ch}" fill="#FFFFFF" opacity="0.07"/>')
            glyph = FONT5x7.get(chv, FONT5x7[" "])
            for gr, bits in enumerate(glyph):
                for gc, b in enumerate(bits):
                    if b == "1":
                        s.append(f'<rect x="{gx+gc*dw+0.03:.3f}" y="{gy+gr*dh+0.03:.3f}" width="{dw-0.07:.3f}" '
                                 f'height="{dh-0.07:.3f}" fill="{on}"/>')
    return "".join(s)


def lcd_front(lines=("RLux: 452.31", "R G:25x 300ms"), show_i2c=True):
    s = []
    if show_i2c:  # backpack header peeking out on the left (Wokwi/real layout: pin-1 end)
        s.append('<rect x="-3.4" y="7.2" width="3.8" height="10.8" rx="0.3" fill="#1B1E24"/>')
        for k, n in enumerate(I2C_ORDER):
            y = 8.82 + k * 2.54
            s.append(f'<rect x="-6.2" y="{y-0.32:.2f}" width="3.0" height="0.64" fill="url(#gGold)"/>')
            s.append(f'<rect x="-3.2" y="{y-1.0:.2f}" width="2.3" height="2.0" fill="#0E0F12"/>')
    s.append('<g filter="url(#fShadow)">')
    s.append(f'<rect x="0" y="0" width="{LCD_W}" height="{LCD_H}" rx="0.8" fill="url(#gGreenBoard)" stroke="#0A5430" stroke-width="0.25"/>')
    s.append('</g>')
    for (x, y) in [(2.5, 2.5), (77.5, 2.5), (2.5, 33.5), (77.5, 33.5)]:
        s.append(f'<circle cx="{x}" cy="{y}" r="1.9" fill="url(#gGold)" stroke="#8E6E2A" stroke-width="0.12"/>')
        s.append(f'<circle cx="{x}" cy="{y}" r="1.45" fill="#0B0C0E"/>')
    for k in range(16):  # 16-pin header holes along the top edge (pin 1 on the left)
        s.append(pad(8.4 + k * 2.54, 2.3, r=0.75, hole=0.38))
    s.append('<text x="7.0" y="4.75" class="silk" style="font-size:0.9px">1</text>')
    s.append('<text x="46.9" y="4.75" class="silk" style="font-size:0.9px">16</text>')
    # metal bezel and display window
    s.append('<rect x="4.4" y="5.4" width="71.2" height="25.6" rx="0.6" fill="#1C1F24" stroke="#0A0B0D" stroke-width="0.2"/>')
    s.append('<rect x="4.9" y="5.9" width="70.2" height="24.6" rx="0.45" fill="none" stroke="#4A5058" stroke-width="0.15"/>')
    s.append('<rect x="7.55" y="10.3" width="66.0" height="16.0" rx="1.5" fill="url(#gLcd)"/>')
    s.append('<rect x="7.55" y="10.3" width="66.0" height="5.0" rx="1.5" fill="#FFFFFF" opacity="0.06"/>')
    s.append(lcd_text(lines))
    return "".join(s)


def i2c_pin_back(name):
    """Header pin (end-on) of the backpack in the LCD back view, local mm."""
    return 81.0, 6.19 + 2.54 * I2C_ORDER.index(name)


def lcd_back(addr="0x3F"):
    s = ['<g filter="url(#fShadow)">',
         f'<rect x="0" y="0" width="{LCD_W}" height="{LCD_H}" rx="0.8" fill="url(#gGreenBoard)" stroke="#0A5430" stroke-width="0.25"/>',
         '</g>']
    for (x, y) in [(2.5, 2.5), (77.5, 2.5), (2.5, 33.5), (77.5, 33.5)]:
        s.append(f'<circle cx="{x}" cy="{y}" r="1.9" fill="url(#gGold)" stroke="#8E6E2A" stroke-width="0.12"/>')
        s.append(f'<circle cx="{x}" cy="{y}" r="1.45" fill="#0B0C0E"/>')
    # faint traces and the two COB controller blobs
    for k in range(9):
        y = 22.5 + k * 1.1
        s.append(f'<line x1="6" y1="{y:.2f}" x2="74" y2="{y:.2f}" stroke="#2AA066" stroke-width="0.18" opacity="0.35"/>')
    s.append('<ellipse cx="22" cy="27.0" rx="5.2" ry="4.6" fill="#111215"/>')
    s.append('<ellipse cx="40" cy="27.0" rx="5.2" ry="4.6" fill="#111215"/>')
    s.append('<text x="60" y="29.2" text-anchor="middle" class="silk" style="font-size:1.5px;fill:#BFE6CF">LCD1602A</text>')
    # backpack (PCF8574A) soldered on the 16-pin row (pin 1 = right in back view)
    bx0, by0, bw, bh = 41.0, 0.6, 41.5, 19.0
    s.append('<g filter="url(#fShadow)">')
    s.append(f'<rect x="{bx0}" y="{by0}" width="{bw}" height="{bh}" rx="0.6" fill="url(#gBlackBoard)" stroke="#08090A" stroke-width="0.2"/>')
    s.append('</g>')
    for k in range(16):  # solder joints of the 16-pin row on the backpack
        x = (80 - 8.4) - k * 2.54
        s.append(f'<circle cx="{x:.2f}" cy="2.3" r="0.72" fill="#D4D9DE" stroke="#8A9199" stroke-width="0.1"/>')
    s.append(ic(60.5, 10.4, 10.2, 4.0, 8, leg_len=0.7, body="#3A3F47", label="PCF8574AT", lsize=1.05))
    # contrast trimpot (blue) + backlight jumper + address pads
    s.append('<rect x="43.0" y="6.4" width="6.6" height="6.6" rx="0.5" fill="#2F6FD8" stroke="#1C4C9F" stroke-width="0.15"/>')
    s.append('<circle cx="46.3" cy="9.7" r="2.2" fill="#F2F5FA"/>')
    s.append('<path d="M45.1 9.7 H47.5 M46.3 8.5 V10.9" stroke="#8E99A6" stroke-width="0.45"/>')
    s.append('<text x="46.3" y="14.8" text-anchor="middle" class="silk" style="font-size:0.9px">contrast</text>')
    s.append('<rect x="69.6" y="13.6" width="4.6" height="2.6" rx="0.3" fill="#0E0F12"/>')
    s.append('<text x="71.9" y="17.6" text-anchor="middle" class="silk" style="font-size:0.85px">LED</text>')
    for k, a in enumerate(["A0", "A1", "A2"]):
        x = 54.0 + k * 2.4
        s.append(f'<rect x="{x}" y="15.0" width="0.8" height="1.1" fill="#C8CDD2"/><rect x="{x+1.0}" y="15.0" width="0.8" height="1.1" fill="#C8CDD2"/>')
        s.append(f'<text x="{x+0.9}" y="17.6" text-anchor="middle" class="silk" style="font-size:0.8px">{a}</text>')
    # 4-pin I2C header at the overhanging end, pins pointing at the viewer
    s.append('<rect x="79.7" y="4.9" width="2.6" height="10.2" rx="0.2" fill="#0E0F12"/>')
    for n in I2C_ORDER:
        x, y = i2c_pin_back(n)
        s.append(f'<rect x="{x-0.45}" y="{y-0.45}" width="0.9" height="0.9" fill="url(#gGold)" stroke="#8E6E2A" stroke-width="0.08"/>')
        s.append(f'<text x="{x-1.1}" y="{y+0.55}" text-anchor="end" class="silk" style="font-size:1.55px">{n}</text>')
    s.append(f'<text x="{bx0+2.0}" y="{by0+4.2}" class="silk" style="font-size:0.95px;fill:#9AA3AD">I2C {addr}</text>')
    return "".join(s)
