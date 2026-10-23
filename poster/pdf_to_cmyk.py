"""Convert the poster PDF exported from PowerPoint into the print-submission file:
CMYK, >= 100 ppi (default 200 ppi), exactly 800 x 1000 mm.

    pip install pymupdf pillow img2pdf
    python pdf_to_cmyk.py poster_from_powerpoint.pdf poster_CMYK.pdf [ppi] [cmyk_profile.icc]

CMYK profile: pass any .icc/.icm (ask the print shop which one they want). If none is given the script
uses Windows' built-in RSWOP.icm (US SWOP) or default_cmyk.icc in the current folder.
"""
import io
import os
import sys

try:
    import pymupdf as fitz  # PyMuPDF >= 1.24
except ImportError:
    import fitz
import img2pdf
from PIL import Image, ImageCms

Image.MAX_IMAGE_PIXELS = None


def find_profile(arg):
    cands = [arg] if arg else []
    windir = os.environ.get("WINDIR", r"C:\Windows")
    cands += [os.path.join(windir, "System32", "spool", "drivers", "color", "RSWOP.icm"), "default_cmyk.icc",
              os.path.join(os.path.dirname(os.path.abspath(__file__)), "default_cmyk.icc")]
    for c in cands:
        if c and os.path.exists(c):
            return c
    sys.exit("no CMYK profile found: pass one as the 4th argument (e.g. the print shop's .icc)")


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    src, out_pdf = sys.argv[1], sys.argv[2]
    ppi = int(sys.argv[3]) if len(sys.argv) > 3 else 200
    prof_path = find_profile(sys.argv[4] if len(sys.argv) > 4 else None)
    doc = fitz.open(src)
    page = doc[0]                                    # the poster is slide 1
    w_in, h_in = page.rect.width / 72, page.rect.height / 72
    pix = page.get_pixmap(dpi=ppi, alpha=False)
    rgb = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    cmyk_prof = ImageCms.getOpenProfile(prof_path)
    tr = ImageCms.buildTransform(ImageCms.createProfile("sRGB"), cmyk_prof, "RGB", "CMYK",
                                 renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC,
                                 flags=ImageCms.Flags.BLACKPOINTCOMPENSATION)
    cmyk = ImageCms.applyTransform(rgb, tr)
    buf = io.BytesIO()
    cmyk.save(buf, "JPEG", quality=94, dpi=(ppi, ppi), icc_profile=cmyk_prof.tobytes(), subsampling=0)
    layout = img2pdf.get_layout_fun((img2pdf.mm_to_pt(800), img2pdf.mm_to_pt(1000)))
    with open(out_pdf, "wb") as fh:
        fh.write(img2pdf.convert(buf.getvalue(), layout_fun=layout))
    print(f"{src}: page {w_in * 25.4:.0f} x {h_in * 25.4:.0f} mm -> {rgb.size[0]} x {rgb.size[1]} px "
          f"({ppi} ppi) CMYK [{os.path.basename(prof_path)}] -> {out_pdf} (800 x 1000 mm)")


if __name__ == "__main__":
    main()
