"""Shared visual system for LightCheck KM diagrams (fonts, palette, helpers)."""
import base64, os

HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.path.join(HERE, "node_modules", "@fontsource")

PAL = dict(
    su="#1F5F9E", su_light="#BBD8EA", teal="#0E7766", teal_tint="#DCEFEA",
    orange="#F26B21", ink="#14202B", gray="#5B6B78", paper="#FFFFFF",
    w5v="#D62828", w3v3="#F28C28", wgnd="#222222", wsda="#1E6FD9", wscl="#E8B500",
)

R_THAI = "U+02D7,U+0303,U+0331,U+0E01-0E5B,U+200C-200D,U+25CC"
R_LATIN = ("U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,"
           "U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD")

FACES = [
    ("Plex Thai", "ibm-plex-sans-thai", "ibm-plex-sans-thai-thai-{w}-normal.woff2", R_THAI, [400, 500, 600, 700]),
    ("Plex Thai", "ibm-plex-sans-thai", "ibm-plex-sans-thai-latin-{w}-normal.woff2", R_LATIN, [400, 500, 600, 700]),
    ("Kanit", "kanit", "kanit-thai-{w}-normal.woff2", R_THAI, [600]),
    ("Kanit", "kanit", "kanit-latin-{w}-normal.woff2", R_LATIN, [600]),
    ("Plex Mono", "ibm-plex-mono", "ibm-plex-mono-latin-{w}-normal.woff2", R_LATIN, [500, 600]),
]

_font_css = None


def font_css():
    global _font_css
    if _font_css is None:
        out = []
        for fam, pkg, pat, rng, weights in FACES:
            for w in weights:
                p = os.path.join(FD, pkg, "files", pat.format(w=w))
                b64 = base64.b64encode(open(p, "rb").read()).decode()
                out.append(
                    f"@font-face{{font-family:'{fam}';font-weight:{w};font-style:normal;"
                    f"src:url(data:font/woff2;base64,{b64}) format('woff2');unicode-range:{rng};}}")
        _font_css = "\n".join(out)
    return _font_css


BASE_CSS = """
.t{font-family:'Plex Thai','IBM Plex Sans Thai',sans-serif;fill:#14202B}
.h{font-family:'Kanit',sans-serif;font-weight:600;fill:#14202B}
.m{font-family:'Plex Mono','IBM Plex Mono',monospace;font-weight:600}
.silk{font-family:'Plex Mono','IBM Plex Mono',monospace;font-weight:600;fill:#fff}
"""


def svg_doc(w, h, body, defs="", bg=None, embed_fonts=True):
    style = (font_css() if embed_fonts else "") + BASE_CSS
    bgrect = f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
            f'<defs><style>{style}</style>{defs}</defs>{bgrect}{body}</svg>')


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size, cls="t", weight=None, fill=None, anchor="start", extra=""):
    st = f"font-size:{size}px;"
    if weight:
        st += f"font-weight:{weight};"
    if fill:
        st += f"fill:{fill};"
    return f'<text x="{x:.2f}" y="{y:.2f}" class="{cls}" style="{st}" text-anchor="{anchor}" {extra}>{esc(s)}</text>'


def save(path, svg):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
