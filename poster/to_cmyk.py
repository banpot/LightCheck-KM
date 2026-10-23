"""RGB render (PNG) -> CMYK JPEG -> single-page PDF 800 x 1000 mm (print submission)."""
import sys
import img2pdf
from PIL import Image, ImageCms
Image.MAX_IMAGE_PIXELS = None
src, out_pdf, ppi = sys.argv[1], sys.argv[2], int(sys.argv[3])
rgb = Image.open(src).convert("RGB")
srgb = ImageCms.createProfile("sRGB")
cmyk_prof = ImageCms.getOpenProfile(sys.argv[4] if len(sys.argv) > 4 else "default_cmyk.icc")
tr = ImageCms.buildTransform(srgb, cmyk_prof, "RGB", "CMYK", renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC,
                             flags=ImageCms.Flags.BLACKPOINTCOMPENSATION)
cmyk = ImageCms.applyTransform(rgb, tr)
jpg = out_pdf.replace(".pdf", ".jpg")
cmyk.save(jpg, "JPEG", quality=94, dpi=(ppi, ppi), icc_profile=cmyk_prof.tobytes(), subsampling=0)
layout = img2pdf.get_layout_fun((img2pdf.mm_to_pt(800), img2pdf.mm_to_pt(1000)))
with open(out_pdf, "wb") as fh:
    fh.write(img2pdf.convert(jpg, layout_fun=layout))
print(rgb.size, "->", out_pdf)
