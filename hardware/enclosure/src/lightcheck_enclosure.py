#!/usr/bin/env python3
"""
LightCheck KM - parametric 3D-printable enclosure
=================================================

Generates a two-part handheld/tripod enclosure for:
  * Adafruit TSL2591 #1980 (STEMMA QT version) - flush in a pocket on the TOP face
  * LCD1602 + PCF8574 I2C backpack              - under the lid, bezel in a window
  * WEMOS D1 mini (ESP8266)                     - on the base floor, USB out the right wall

Output (relative to this file):
  ../stl/lightcheck_base.stl
  ../stl/lightcheck_lid.stl
  ../stl/proxies/*.stl          (simple module stand-ins, used only for renders/checks)
  ../stl/scene.json             (colours/positions for the three.js renderer)

Run:   python3 lightcheck_enclosure.py            # build + validate
Needs: pip install manifold3d trimesh numpy matplotlib

Coordinate system (assembled):  X -> right, Y -> away from the user (far end),
Z -> up, origin = centre of the footprint at the bottom of the base.
The user holds the meter with the LCD near them; the sensor sits at the far end.

Every dimension marked  [VERIFY]  depends on the exact module you bought -
measure it with calipers and edit the value before printing.
Changing the enclosure, the sensor pocket/aperture or the sensor position
REQUIRES re-verification of the calibration model (KM doc section 9.1.12).
"""
import json
import math
import os
import sys

import numpy as np
from manifold3d import CrossSection, FillRule, JoinType, Manifold, set_circular_segments

set_circular_segments(72)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "stl"))

# =============================================================================
# PARAMETERS (mm)
# =============================================================================
# ---- general / printing ------------------------------------------------------
WALL = 2.2            # side wall thickness (>= 2 mm)
FLOOR = 2.0           # base floor thickness
LID_T = 2.4           # lid plate thickness
CORNER_R = 6.0        # outer corner radius (plan view)
CLR = 0.3             # general fit clearance per side
LIP_H = 2.0           # lid locating lip height (goes inside the base walls)
LIP_T = 1.2           # lid lip thickness
EDGE_MARGIN = 2.5     # min solid lid around the sensor pocket
CHAMFER = 0.6         # 45 deg chamfer on the bed-side outer edges (hides elephant foot)

# ---- LCD1602 (HD44780, 80x36 PCB) + PCF8574 I2C backpack ----------------------
LCD_PCB_W = 80.0      # [VERIFY] PCB length
LCD_PCB_D = 36.0      # [VERIFY] PCB width
LCD_PCB_T = 1.6       # [VERIFY] PCB thickness
LCD_HOLE_DX = 75.0    # [VERIFY] mounting-hole spacing (X)  (holes 2.5 mm from edges)
LCD_HOLE_DY = 31.0    # [VERIFY] mounting-hole spacing (Y)
LCD_SCREW_PILOT = 2.1 # pilot for M2.5 self-tapping screws (LCD holes are 2.5-3.0 mm)
LCD_STANDOFF_D = 5.6  # standoff outer diameter (must clear the bezel corner)
LCD_BEZEL_W = 71.2    # [VERIFY] metal bezel outer length
LCD_BEZEL_D = 24.2    # [VERIFY] metal bezel outer width
LCD_BEZEL_H = 7.0     # [VERIFY] bezel top above PCB top (typ. 6.5-9.5 mm) -> sets standoff length
LCD_BEZEL_OFF_X = 0.0 # [VERIFY] bezel centre offset from PCB centre (X)
LCD_BEZEL_OFF_Y = 0.0 # [VERIFY] bezel centre offset from PCB centre (Y)
LCD_VIEW_W = 64.5     # viewing area (render only)
LCD_VIEW_D = 16.0
LCD_WINDOW_CLR = 0.4  # window clearance around bezel, per side
LCD_BEZEL_RECESS = 0.3  # bezel top sits this far below the lid top surface
LCD_BACK_DEPTH = 12.0 # [VERIFY] backpack + trimpot depth below the LCD PCB bottom
LCD_HEADER_CLEAR = 16.0  # free space left of the LCD for the backpack's 4-pin I2C header
                         # (solder wires or bend pins 90 deg down; straight Dupont needs ~25)
LCD_BACKPACK_X0 = 6.0    # [VERIFY] backpack extent along LCD, from LCD left edge
LCD_BACKPACK_X1 = 48.0
LCD_BACKPACK_D = 20.0    # [VERIFY] backpack extent from the LCD's far (header) edge
LCD_NEAR_GAP = 0.5       # gap LCD PCB <-> near inner wall

# ---- WEMOS D1 mini --------------------------------------------------------------
D1_L = 34.2           # [VERIFY] PCB length (USB end -> antenna end)
D1_W = 25.6           # [VERIFY] PCB width
D1_T = 1.0            # [VERIFY] PCB thickness
D1_TOP_H = 3.4        # [VERIFY] tallest top-side part (ESP8266 shield)
D1_BOT_H = 3.0        # [VERIFY] tallest bottom-side part (CH340 / USB / LDO)
D1_STANDOFF = 5.5     # PCB bottom above floor top (clears bottom parts + pin stubs)
D1_USB_W = 12.5       # USB opening width  (fits micro-USB and USB-C overmolds)
D1_USB_H = 9.5        # USB opening height (covers a top- or bottom-mounted connector)
D1_POST_T = 1.6       # locating post bar thickness
D1_POST_L = 5.0       # locating post bar length
D1_PAD = 3.0          # corner support pad size

# ---- Adafruit TSL2591 #1980 STEMMA QT (from Adafruit EAGLE file "Adafruit TSL2591.brd") --
TSL_W = 25.4          # board X  (1.0")
TSL_D = 17.78         # board Y  (0.7")
TSL_T = 1.6           # [VERIFY] PCB thickness
TSL_HOLE_DX = 20.32   # M2.5 hole spacing X (holes 2.54 from edges)
TSL_HOLE_DY = 12.70   # M2.5 hole spacing Y
TSL_HOLE_PILOT = 2.1  # optional M2.5 screw pilot
TSL_HDR_Y = -6.35     # 6-pin header row centre, relative to board centre (toward the user)
TSL_HDR_SLOT = (16.4, 3.4)   # slot for header plastic + pins
TSL_POCKET_CLR = 0.3
TSL_TAPE = 0.0        # add thickness of foam tape if you mount the board on tape
TSL_PAD_T = 2.0       # lid thickening under the pocket
TSL_X = 20.0          # sensor centre X (right side of the far end; text goes on the left)
TSL_WINDOW_GAP = 6.0  # min lid between LCD window and sensor pocket
SENSOR_PKG = (2.0, 2.4, 0.65)    # TSL2591 DFN-6 package (on board centre)
JST_SH = (4.25, 6.0, 2.95)       # STEMMA QT connectors at x = +-10.03 (board-relative)

# ---- screws -------------------------------------------------------------------
BOSS_D = 7.0          # corner boss diameter
BOSS_INSET = 5.2      # boss centre from the outer edges
LID_BOSS_H = 3.0      # boss under the lid (gives depth for the counterbore)
M3_PILOT = 2.5        # base boss pilot for M3 self-tapping (M3 x 12)
M3_PILOT_DEPTH = 12.0
M3_CLEAR = 3.4
M3_CB_D = 6.4         # counterbore for M3 pan/socket head
M3_CB_DEPTH = 3.0     # head sits below the lid top -> nothing rises above the sensor plane

# ---- tripod (1/4"-20 hex nut, captured from inside) --------------------------------
NUT_AF = 11.11 + 0.35 # across flats (7/16") + clearance  [VERIFY your nut]
NUT_T = 5.56          # nut thickness (7/32")
TRIPOD_HOLE = 6.8     # clearance for the 1/4" tripod screw
TRIPOD_SHOULDER = 1.6 # floor under the nut (thin = more thread engagement)
TRIPOD_BOSS_D = 18.0

# ---- lid lettering --------------------------------------------------------------
TEXT_DEPTH = 0.6
TEXT_1 = "LightCheck KM"
TEXT_2 = "BDT · Silpakorn"
TEXT_1_SIZE = 5.6     # font size (cap height ~0.73x)
TEXT_2_SIZE = 3.6

# =============================================================================
# DERIVED LAYOUT
# =============================================================================
_boss_reach = BOSS_INSET + BOSS_D / 2          # boss edge from outer edge
W = math.ceil(WALL + LCD_HEADER_CLEAR + LCD_PCB_W + 0.5 + _boss_reach)
# Y layout measured from the NEAR outer edge
_lcd_near = WALL + LCD_NEAR_GAP
_lcd_far = _lcd_near + LCD_PCB_D
_win_far = _lcd_near + LCD_PCB_D / 2 + LCD_BEZEL_OFF_Y + LCD_BEZEL_D / 2 + LCD_WINDOW_CLR
_pocket_near = _win_far + TSL_WINDOW_GAP
_pocket_far = _pocket_near + TSL_D + 2 * TSL_POCKET_CLR
D = math.ceil(_pocket_far + EDGE_MARGIN + WALL + CLR)
# Z
_lcd_stack = LCD_BEZEL_RECESS + LCD_BEZEL_H + LCD_PCB_T + LCD_BACK_DEPTH
H = math.ceil(FLOOR + 1.0 + 2.0 + _lcd_stack)   # 1 mm clearance + 2 mm margin
Z_LID_BOT = H - LID_T          # top of base walls / underside of lid plate
Z_BOSS_TOP = Z_LID_BOT - LID_BOSS_H


def ynear(v):
    """convert 'distance from near outer edge' to centred Y."""
    return v - D / 2


LCD_CX = -W / 2 + WALL + LCD_HEADER_CLEAR + LCD_PCB_W / 2
LCD_CY = ynear(_lcd_near + LCD_PCB_D / 2)
LCD_PCB_TOP = H - LCD_BEZEL_RECESS - LCD_BEZEL_H
TSL_Y = ynear(_pocket_near + TSL_POCKET_CLR + TSL_D / 2)
TSL_BOARD_BOT = H - TSL_T - TSL_TAPE

# D1 mini: long axis along X, USB edge at the right inner wall, under the LCD's
# right half (clear of the backpack), clear of the near-right boss.
D1_X1 = W / 2 - WALL - CLR                 # USB edge
D1_X0 = D1_X1 - D1_L
D1_Y0 = ynear(BOSS_INSET + BOSS_D / 2 + 0.5 + CLR + D1_POST_T)
D1_Y1 = D1_Y0 + D1_W
D1_CY = (D1_Y0 + D1_Y1) / 2
D1_PCB_BOT = FLOOR + D1_STANDOFF

CORNERS = [(sx * (W / 2 - BOSS_INSET), sy * (D / 2 - BOSS_INSET)) for sx in (-1, 1) for sy in (-1, 1)]


# =============================================================================
# HELPERS
# =============================================================================
def rrect(w, d, r):
    r = max(0.01, min(r, w / 2 - 0.01, d / 2 - 0.01))
    return CrossSection.square([w - 2 * r, d - 2 * r], center=True).offset(r, JoinType.Round, circular_segments=48)


def prism(cs, z0, z1):
    return cs.extrude(z1 - z0).translate([0, 0, z0])


def chamfered_slab(w, d, r, z0, z1, c_bot=0.0, c_top=0.0):
    """Rounded-rect slab with optional 45-degree chamfers on the bottom/top outer edge."""
    pieces = [prism(rrect(w, d, r), z0 + c_bot, z1 - c_top)]
    if c_bot:
        pieces.append(prism(rrect(w - 2 * c_bot, d - 2 * c_bot, r - c_bot), z0, z0 + c_bot))
    if c_top:
        pieces.append(prism(rrect(w - 2 * c_top, d - 2 * c_top, r - c_top), z1 - c_top, z1))
    return Manifold.batch_hull(pieces) if len(pieces) > 1 else pieces[0]


def box(x0, y0, z0, x1, y1, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def cbox(cx, cy, w, d, z0, z1):
    return box(cx - w / 2, cy - d / 2, z0, cx + w / 2, cy + d / 2, z1)


def cyl(cx, cy, d, z0, z1, seg=48):
    return Manifold.cylinder(z1 - z0, d / 2, circular_segments=seg).translate([cx, cy, z0])


def hexagon(cx, cy, af, z0, z1):
    r = af / math.sqrt(3)  # circumradius from across-flats
    pts = [(cx + r * math.cos(math.radians(30 + 60 * i)), cy + r * math.sin(math.radians(30 + 60 * i))) for i in range(6)]
    return prism(CrossSection([pts]), z0, z1)


def _bounds(cs):
    b = cs.bounds()
    b = [float(v) for v in (b if len(b) == 4 else (*b[0], *b[1]))]
    return b


def text_cs(txt, size, cx, cy, max_w=None):
    """Text outline -> CrossSection (DejaVu Sans Bold), centred at (cx, cy), shrunk to max_w."""
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextPath

    tp = TextPath((0, 0), txt, size=size, prop=FontProperties(family="DejaVu Sans", weight="bold"))
    polys = [p for p in tp.to_polygons(closed_only=True) if len(p) >= 3]
    cs = CrossSection([[(float(x), float(y)) for x, y in p[:-1]] for p in polys], FillRule.EvenOdd)
    x0, y0, x1, y1 = _bounds(cs)
    if max_w and (x1 - x0) > max_w:
        k = max_w / (x1 - x0)
        cs = cs.scale([k, k])
        x0, y0, x1, y1 = _bounds(cs)
    return cs.translate([cx - (x0 + x1) / 2, cy - (y0 + y1) / 2])


# =============================================================================
# PARTS
# =============================================================================
def build_base():
    outer = rrect(W, D, CORNER_R)
    inner = rrect(W - 2 * WALL, D - 2 * WALL, CORNER_R - WALL)
    outer_solid = chamfered_slab(W, D, CORNER_R, 0, Z_LID_BOT, c_bot=CHAMFER)
    shell = outer_solid - prism(inner, FLOOR, H)

    # corner bosses (merge into the walls), M3 pilots
    for (x, y) in CORNERS:
        shell += cyl(x, y, BOSS_D, 0, Z_BOSS_TOP) ^ outer_solid
    for (x, y) in CORNERS:
        shell -= cyl(x, y, M3_PILOT, Z_BOSS_TOP - M3_PILOT_DEPTH, Z_BOSS_TOP + 0.1)

    # D1 mini cradle: corner pads + locating bars
    zt = D1_PCB_BOT
    zpost = D1_PCB_BOT + D1_T + 1.2
    for x in (D1_X0, D1_X1 - D1_PAD):
        for y in (D1_Y0, D1_Y1 - D1_PAD):
            shell += box(x, y, FLOOR - 0.01, x + D1_PAD, y + D1_PAD, zt)
    t, L, c = D1_POST_T, D1_POST_L, CLR
    # antenna end (x0): L-shaped posts at both corners
    for y_edge, s in ((D1_Y0, -1), (D1_Y1, 1)):
        yb0, yb1 = (y_edge - c - t, y_edge - c) if s < 0 else (y_edge + c, y_edge + c + t)
        shell += box(D1_X0 - c - t, yb0, FLOOR - 0.01, D1_X0 - c + L, yb1, zpost)
        ys0, ys1 = (y_edge - c - t, y_edge - c + L) if s < 0 else (y_edge + c - L, y_edge + c + t)
        shell += box(D1_X0 - c - t, ys0, FLOOR - 0.01, D1_X0 - c, ys1, zpost)
    # USB end (x1): side bars only (the wall is the end stop)
    for y_edge, s in ((D1_Y0, -1), (D1_Y1, 1)):
        yb0, yb1 = (y_edge - c - t, y_edge - c) if s < 0 else (y_edge + c, y_edge + c + t)
        shell += box(D1_X1 - L, yb0, FLOOR - 0.01, W / 2 - WALL + 0.01, yb1, zpost)
    # USB opening through the right wall
    zc = D1_PCB_BOT + D1_T / 2
    usb = box(W / 2 - WALL - 1, D1_CY - D1_USB_W / 2, zc - D1_USB_H / 2, W / 2 + 1, D1_CY + D1_USB_W / 2, zc + D1_USB_H / 2)
    shell -= usb

    # tripod boss with captured 1/4"-20 nut (nut inserted from inside, pulled against the shoulder)
    ztop = TRIPOD_SHOULDER + NUT_T + 0.4
    shell += cyl(TSL_X, TSL_Y, TRIPOD_BOSS_D, FLOOR - 0.01, ztop)
    shell -= hexagon(TSL_X, TSL_Y, NUT_AF, TRIPOD_SHOULDER, ztop + 0.1)
    shell -= cyl(TSL_X, TSL_Y, TRIPOD_HOLE, -0.1, TRIPOD_SHOULDER + 0.1)
    # chamfer-ish lead-in on the tripod hole (cone)
    shell -= Manifold.cylinder(0.8, TRIPOD_HOLE / 2 + 0.8, TRIPOD_HOLE / 2, circular_segments=48).translate([TSL_X, TSL_Y, -0.001])
    return shell


def build_lid():
    outer = rrect(W, D, CORNER_R)
    inner_fit = rrect(W - 2 * WALL - 2 * CLR, D - 2 * WALL - 2 * CLR, CORNER_R - WALL - CLR)
    lid = chamfered_slab(W, D, CORNER_R, Z_LID_BOT, H, c_top=CHAMFER)

    # locating lip
    lip_in = rrect(W - 2 * WALL - 2 * CLR - 2 * LIP_T, D - 2 * WALL - 2 * CLR - 2 * LIP_T, max(0.5, CORNER_R - WALL - CLR - LIP_T))
    lid += prism(inner_fit, Z_LID_BOT - LIP_H, Z_LID_BOT + 0.01) - prism(lip_in, Z_LID_BOT - LIP_H - 1, Z_LID_BOT + 1)

    # lid bosses (only inside the walls)
    for (x, y) in CORNERS:
        lid += cyl(x, y, BOSS_D, Z_BOSS_TOP, Z_LID_BOT + 0.01) ^ prism(inner_fit, Z_BOSS_TOP - 1, H)

    # LCD standoffs
    lcd_holes = [(LCD_CX + sx * LCD_HOLE_DX / 2, LCD_CY + sy * LCD_HOLE_DY / 2) for sx in (-1, 1) for sy in (-1, 1)]
    for (x, y) in lcd_holes:
        lid += cyl(x, y, LCD_STANDOFF_D, LCD_PCB_TOP, Z_LID_BOT + 0.01)

    # sensor pad under the pocket
    pw, pd = TSL_W + 2 * TSL_POCKET_CLR, TSL_D + 2 * TSL_POCKET_CLR
    lid += prism(rrect(pw + 2 * EDGE_MARGIN, pd + 2 * EDGE_MARGIN, 2.0).translate([TSL_X, TSL_Y]), Z_LID_BOT - TSL_PAD_T, Z_LID_BOT + 0.01)

    # ---- cuts ----
    # LCD window
    ww, wd = LCD_BEZEL_W + 2 * LCD_WINDOW_CLR, LCD_BEZEL_D + 2 * LCD_WINDOW_CLR
    lid -= prism(rrect(ww, wd, LCD_WINDOW_CLR + 0.2).translate([LCD_CX + LCD_BEZEL_OFF_X, LCD_CY + LCD_BEZEL_OFF_Y]), Z_LID_BOT - 5, H + 1)
    # LCD screw pilots
    for (x, y) in lcd_holes:
        lid -= cyl(x, y, LCD_SCREW_PILOT, LCD_PCB_TOP - 0.1, Z_LID_BOT + 1.0)
    # sensor pocket (board top flush with lid top)
    lid -= prism(rrect(pw, pd, 1.0).translate([TSL_X, TSL_Y]), TSL_BOARD_BOT, H + 1)
    # header slot
    lid -= cbox(TSL_X, TSL_Y + TSL_HDR_Y, TSL_HDR_SLOT[0], TSL_HDR_SLOT[1], Z_LID_BOT - TSL_PAD_T - 1, H + 1)
    # optional M2.5 pilots
    for sx in (-1, 1):
        for sy in (-1, 1):
            lid -= cyl(TSL_X + sx * TSL_HOLE_DX / 2, TSL_Y + sy * TSL_HOLE_DY / 2, TSL_HOLE_PILOT, Z_LID_BOT - TSL_PAD_T - 1, H + 1)
    # corner screws: clearance + counterbore
    for (x, y) in CORNERS:
        lid -= cyl(x, y, M3_CLEAR, Z_BOSS_TOP - 1, H + 1)
        lid -= cyl(x, y, M3_CB_D, H - M3_CB_DEPTH, H + 1)
    # debossed lettering (left of the sensor, in the far zone)
    tx0 = -W / 2 + BOSS_INSET + M3_CB_D / 2 + 2.0
    tx1 = TSL_X - pw / 2 - 3.0
    tcx = (tx0 + tx1) / 2
    t1 = text_cs(TEXT_1, TEXT_1_SIZE, tcx, TSL_Y + 3.0, max_w=tx1 - tx0)
    t2 = text_cs(TEXT_2, TEXT_2_SIZE, tcx, TSL_Y - 4.6, max_w=tx1 - tx0)
    for t in (t1, t2):
        lid -= prism(t, H - TEXT_DEPTH, H + 1)
    return lid, (tx0, tx1)


# =============================================================================
# MODULE PROXIES (assembled positions) - for renders and interference checks
# =============================================================================
def build_proxies():
    P = {}
    # LCD
    pcb_bot = LCD_PCB_TOP - LCD_PCB_T
    P["lcd_pcb"] = cbox(LCD_CX, LCD_CY, LCD_PCB_W, LCD_PCB_D, pcb_bot, LCD_PCB_TOP) - sum(
        (cyl(LCD_CX + sx * LCD_HOLE_DX / 2, LCD_CY + sy * LCD_HOLE_DY / 2, 2.6, pcb_bot - 1, LCD_PCB_TOP + 1) for sx in (-1, 1) for sy in (-1, 1)),
        Manifold())
    bx, by = LCD_CX + LCD_BEZEL_OFF_X, LCD_CY + LCD_BEZEL_OFF_Y
    btop = H - LCD_BEZEL_RECESS
    P["lcd_bezel"] = cbox(bx, by, LCD_BEZEL_W, LCD_BEZEL_D, LCD_PCB_TOP, btop) - cbox(bx, by, LCD_VIEW_W, LCD_VIEW_D, btop - 1.2, btop + 1)
    P["lcd_glass"] = cbox(bx, by, LCD_VIEW_W, LCD_VIEW_D, btop - 1.2, btop - 0.7)
    lx0 = LCD_CX - LCD_PCB_W / 2
    yf = LCD_CY + LCD_PCB_D / 2
    P["lcd_backpack"] = box(lx0 + LCD_BACKPACK_X0, yf - LCD_BACKPACK_D, pcb_bot - LCD_BACK_DEPTH, lx0 + LCD_BACKPACK_X1, yf - 1.0, pcb_bot - 2.5)
    P["lcd_trimpot"] = cbox(lx0 + LCD_BACKPACK_X0 + 7, yf - 12, 7, 7, pcb_bot - LCD_BACK_DEPTH, pcb_bot - 4.0)
    P["lcd_header"] = box(lx0 + 8, yf - 4.0, pcb_bot - 2.5, lx0 + 8 + 40.6, yf - 1.5, pcb_bot)
    # backpack I2C pins bent down at the left end
    P["lcd_i2c_pins"] = box(lx0 - 8.0, yf - 16, pcb_bot - LCD_BACK_DEPTH - 0.5, lx0 + LCD_BACKPACK_X0, yf - 5, pcb_bot - 9.0)
    # D1 mini
    P["d1_pcb"] = box(D1_X0, D1_Y0, D1_PCB_BOT, D1_X1, D1_Y1, D1_PCB_BOT + D1_T)
    P["d1_shield"] = box(D1_X0 + 1.5, D1_Y0 + 4.5, D1_PCB_BOT + D1_T, D1_X0 + 17.5, D1_Y1 - 4.5, D1_PCB_BOT + D1_T + D1_TOP_H)
    P["d1_bottom"] = box(D1_X0 + 12, D1_Y0 + 5, D1_PCB_BOT - D1_BOT_H, D1_X1 - 0.6, D1_Y1 - 5, D1_PCB_BOT)
    P["d1_usb"] = cbox(D1_X1 - 2.6, D1_CY, 5.4, 7.6, D1_PCB_BOT - 2.6, D1_PCB_BOT)
    # TSL2591
    P["tsl_pcb"] = cbox(TSL_X, TSL_Y, TSL_W, TSL_D, TSL_BOARD_BOT, H) - sum(
        (cyl(TSL_X + sx * TSL_HOLE_DX / 2, TSL_Y + sy * TSL_HOLE_DY / 2, 2.5, TSL_BOARD_BOT - 1, H + 1) for sx in (-1, 1) for sy in (-1, 1)),
        Manifold())
    P["tsl_sensor"] = cbox(TSL_X, TSL_Y, SENSOR_PKG[0], SENSOR_PKG[1], H, H + SENSOR_PKG[2])
    P["tsl_jst"] = sum((cbox(TSL_X + s * 10.03, TSL_Y, JST_SH[0], JST_SH[1], H, H + JST_SH[2]) for s in (-1, 1)), Manifold())
    P["tsl_header"] = cbox(TSL_X, TSL_Y + TSL_HDR_Y, 15.24, 2.5, TSL_BOARD_BOT - 2.5, TSL_BOARD_BOT)
    P["tsl_pins"] = cbox(TSL_X, TSL_Y + TSL_HDR_Y, 14.0, 0.64, TSL_BOARD_BOT - 8.5, TSL_BOARD_BOT - 2.5)
    return P


PROXY_COLORS = {
    "lcd_pcb": "#1f7a3a", "lcd_bezel": "#2b2f33", "lcd_glass": "#1f5fd6", "lcd_backpack": "#121417",
    "lcd_trimpot": "#2a5bd7", "lcd_header": "#151515", "lcd_i2c_pins": "#c9a646",
    "d1_pcb": "#1d63c9", "d1_shield": "#c8ccd2", "d1_bottom": "#222222", "d1_usb": "#b8bcc2",
    "tsl_pcb": "#141414", "tsl_sensor": "#d9d4c4", "tsl_jst": "#f2f2ee", "tsl_header": "#151515", "tsl_pins": "#d4af37",
}


# =============================================================================
# EXPORT + VALIDATION
# =============================================================================
def to_trimesh(m):
    import trimesh
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    f = np.asarray(mesh.tri_verts)
    return trimesh.Trimesh(vertices=v, faces=f, process=True)


def export(m, path):
    tm = to_trimesh(m)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tm.export(path)
    return tm


def main():
    base = build_base()
    lid, text_band = build_lid()
    prox = build_proxies()

    os.makedirs(OUT, exist_ok=True)
    report = {"outer_mm": [W, D, H], "parts": {}}
    ok = True

    # print orientation: base as-is (floor on bed); lid flipped (top face on bed)
    lid_print = lid.rotate([180, 0, 0]).translate([0, 0, H])
    parts = {"lightcheck_base": base, "lightcheck_lid": lid_print}
    for name, m in parts.items():
        tm = export(m, os.path.join(OUT, name + ".stl"))
        bb = tm.bounds
        info = {
            "watertight": bool(tm.is_watertight), "volume_cm3": round(tm.volume / 1000, 2),
            "bbox_mm": [round(float(x), 2) for x in (bb[1] - bb[0])], "min_z": round(float(bb[0][2]), 3),
            "triangles": int(len(tm.faces)), "genus": m.genus(),
        }
        report["parts"][name] = info
        ok &= info["watertight"] and info["volume_cm3"] > 0 and abs(info["min_z"]) < 1e-6

    # assembled lid (for checks / renders)
    export(lid, os.path.join(OUT, "proxies", "_lid_assembled.stl"))
    pdir = os.path.join(OUT, "proxies")
    for k, m in prox.items():
        export(m, os.path.join(pdir, k + ".stl"))

    # interference: every proxy vs base and lid (volume of intersection)
    inter = {}
    for k, m in prox.items():
        vb = (m ^ base).volume()
        vl = (m ^ lid).volume()
        inter[k] = round(vb + vl, 4)
    report["interference_mm3"] = inter
    bad = {k: v for k, v in inter.items() if v > 0.01}
    ok &= not bad
    # lid vs base overlap
    report["lid_base_overlap_mm3"] = round((lid ^ base).volume(), 4)
    ok &= report["lid_base_overlap_mm3"] < 0.01
    # min gaps of the tight spots
    report["min_gap_mm"] = {
        "lcd_bezel-lid": round(prox["lcd_bezel"].min_gap(lid, 3.0), 3),
        "d1_pcb-base": round(prox["d1_pcb"].min_gap(base, 3.0), 3),
        "lcd_backpack-base(floor)": round(prox["lcd_backpack"].min_gap(base, 5.0), 3),
        "d1_shield-lcd_pcb": round(prox["d1_shield"].min_gap(prox["lcd_pcb"], 10.0), 3),
        "d1-lcd_backpack": round(prox["d1_pcb"].min_gap(prox["lcd_backpack"], 10.0), 3),
        "tsl_pins-base": round(prox["tsl_pins"].min_gap(base, 10.0), 3),
    }
    # sensor plane: board top flush, sensor above lid top, nothing of the enclosure above H
    lid_top = lid.bounding_box()[5]
    report["sensor"] = {
        "lid_top_z": round(lid_top, 3), "tsl_pcb_top_z": round(prox["tsl_pcb"].bounding_box()[5], 3),
        "sensor_top_z": round(prox["tsl_sensor"].bounding_box()[5], 3),
        "enclosure_max_z": round(max(lid_top, base.bounding_box()[5]), 3),
        "sensor_xy": [TSL_X, round(TSL_Y, 2)],
    }
    ok &= report["sensor"]["sensor_top_z"] >= lid_top and report["sensor"]["enclosure_max_z"] <= H + 1e-6
    report["layout"] = {
        "lcd_centre": [round(LCD_CX, 2), round(LCD_CY, 2)], "d1_x": [round(D1_X0, 2), round(D1_X1, 2)],
        "d1_y": [round(D1_Y0, 2), round(D1_Y1, 2)], "text_band_x": [round(text_band[0], 1), round(text_band[1], 1)],
        "lcd_standoff_len": round(Z_LID_BOT - LCD_PCB_TOP, 2), "usb_centre_z": round(D1_PCB_BOT + D1_T / 2, 2),
    }

    # scene manifest for the renderer
    scene = {
        "outer": [W, D, H], "z_lid_bot": Z_LID_BOT,
        "lcd_view": {"cx": LCD_CX + LCD_BEZEL_OFF_X, "cy": LCD_CY + LCD_BEZEL_OFF_Y, "w": LCD_VIEW_W, "d": LCD_VIEW_D,
                     "z": H - LCD_BEZEL_RECESS - 0.7},
        "parts": [
            {"file": "../stl/lightcheck_base.stl", "name": "base", "role": "base", "color": "#0E7766"},
            {"file": "../stl/proxies/_lid_assembled.stl", "name": "lid", "role": "lid", "color": "#F4F4F0"},
        ] + [{"file": f"../stl/proxies/{k}.stl", "name": k, "role": k.split('_')[0], "color": PROXY_COLORS[k]} for k in prox],
        "print": [
            {"file": "../stl/lightcheck_base.stl", "color": "#0E7766"},
            {"file": "../stl/lightcheck_lid.stl", "color": "#F4F4F0"},
        ],
    }
    with open(os.path.join(OUT, "scene.json"), "w") as fh:
        json.dump(scene, fh, indent=1)

    report["PASS"] = bool(ok)
    print(json.dumps(report, indent=1))
    if bad:
        print("INTERFERENCE:", bad, file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
