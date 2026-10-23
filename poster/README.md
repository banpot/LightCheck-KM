# Poster · Silpakorn KM Day 2569 (80 × 100 ซม.)

![poster](LightCheck-KM_poster_preview.png)

| ไฟล์ | ใช้ทำอะไร |
|---|---|
| `LightCheck-KM_poster_80x100_editable.pptx` | **ไฟล์ต้นฉบับที่แก้ไขได้** ใน PowerPoint: ข้อความ กรอบ ตัวเลข และวงจร KM เป็นวัตถุจริงทั้งหมด ขนาดสไลด์ 80 × 100 ซม. |
| `LightCheck-KM_poster_RGB.pdf` | ไฟล์เวกเตอร์ (RGB) สำหรับดูบนจอ / KM Portal |
| `pdf_to_cmyk.py` | แปลง PDF ที่ export จาก PowerPoint เป็นไฟล์ส่งพิมพ์ (CMYK, 200 ppi, 800 × 1000 มม.) |
| `build_poster.py`, `render.js`, `to_cmyk.py` | สร้างโปสเตอร์ใหม่ทั้งหมดจากผลใน repository |
| `pptx/extract.js`, `pptx/build_pptx.js` | แปลงโปสเตอร์ HTML เป็นไฟล์ PowerPoint ที่แก้ไขได้ |

## แก้ไขใน PowerPoint แล้วส่งพิมพ์

1. ติดตั้งฟอนต์ใน `tools/fonts/` (Kanit, IBM Plex Sans Thai; สัญญาอนุญาต OFL) แล้วเปิดไฟล์ `.pptx`
2. ใส่/เปลี่ยนรูป: คลิกขวาที่รูป > **Change Picture** (เช่นกรอบ "ภาพที่ 5" สำหรับรูปเครื่องที่ประกอบเสร็จ) ถ้าสัดส่วนไม่ตรงใช้ Crop > Fill
3. แก้ข้อความได้โดยตรง ชื่อวัตถุทุกชิ้นดูได้ที่ Home > Arrange > Selection Pane
   (ผังวงจร กราฟ render กล่อง โลโก้ QR และสมการเป็นรูปภาพ แก้ต้นทางที่ `tools/diagrams/`, `calibration/`, `build_poster.py`)
4. File > Export > Create PDF/XPS (เฉพาะสไลด์ 1)
5. แปลงเป็น CMYK ตามข้อกำหนดการส่ง

```bash
pip install pymupdf pillow img2pdf
python poster/pdf_to_cmyk.py poster.pdf poster_CMYK.pdf 200            # Windows ใช้ RSWOP.icm ที่มากับระบบ
python poster/pdf_to_cmyk.py poster.pdf poster_CMYK.pdf 200 FOGRA39.icc  # หรือ profile ที่โรงพิมพ์กำหนด
```

## สร้างใหม่จากผลใน repository

```bash
python poster/build_poster.py                # poster.html จากผลใน calibration/sim และ tools/survey
cd poster && npm i playwright && node render.js 2.0833 poster_200ppi.png   # PNG 200 ppi + RGB PDF
python to_cmyk.py poster_200ppi.png poster_CMYK_200ppi.pdf 200 <CMYK.icc>  # แปลงเป็น CMYK
npm i pptxgenjs sharp jszip && node pptx/extract.js && node pptx/build_pptx.js  # ไฟล์ต้นฉบับ PowerPoint
```

ตัวเลขทั้งหมดในโปสเตอร์ดึงจาก `calibration/sim/montecarlo_summary.json` และ `tools/survey/office_twin_result.json`
ตัวเลขที่ติดป้าย "ผลจำลอง" มาจากแบบจำลองเชิงอัลกอริทึม ไม่ใช่ข้อมูลวัดจริง
