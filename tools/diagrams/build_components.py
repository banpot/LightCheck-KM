"""Standalone component illustrations (transparent background)."""
import os
from common import svg_doc, save, text, PAL
import components as C

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "docs", "img")


def wrap(body, w_mm, h_mm, s=40, pad_mm=(2, 2, 2, 2)):
    l, t, r, b = pad_mm
    W, H = (w_mm + l + r) * s, (h_mm + t + b) * s
    g = f'<g transform="translate({l*s},{t*s}) scale({s})">{body}</g>'
    return svg_doc(round(W), round(H), g, defs=C.DEFS)


def main():
    save(f"{OUT}/component_d1mini.svg", wrap(C.d1_mini(), C.D1_W, C.D1_H + 1.2, pad_mm=(1.5, 1.5, 1.5, 1.5)))
    save(f"{OUT}/component_tsl2591.svg", wrap(C.tsl2591(), C.TSL_W, C.TSL_H, pad_mm=(1.5, 1.5, 1.5, 1.5)))
    save(f"{OUT}/component_lcd1602_front.svg",
         f'{wrap(C.lcd_front(), C.LCD_W, C.LCD_H, s=24, pad_mm=(7.5, 1.5, 1.5, 1.5))}'.replace(
             'translate(180.0,36.0)', 'translate(180.0,36.0)'))
    save(f"{OUT}/component_lcd1602_back.svg", wrap(C.lcd_back(), C.LCD_W + 2.6, C.LCD_H, s=24, pad_mm=(1.5, 1.5, 1.5, 1.5)))


if __name__ == "__main__":
    main()
